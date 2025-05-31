import os
import google.generativeai as genai
from typing import Dict, List, Tuple
import PyPDF2
import re
from dotenv import load_dotenv
import time
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import json
import threading
import shutil

# Load environment variables
load_dotenv()

# Configure Gemini API
genai.configure(api_key=os.getenv('GOOGLE_API_KEY'))
# Swap to flash model to reduce load
model = genai.GenerativeModel(model_name="models/gemini-1.5-flash")

class ResumeFileHandler(FileSystemEventHandler):
    def __init__(self, matcher):
        self.matcher = matcher
        self.processing_files = set()
        self.last_processed = {}
        self.last_event_time = {}  # Track last event time for each file
        self.processing_lock = threading.Lock()  # Add lock for thread safety
        self.processing_job_ids = set()  # Track which job IDs are being processed

    def on_created(self, event):
        if event.is_directory:
            return

        file_path = event.src_path
        current_time = time.time()
        
        # Check if we've processed this file recently (within 2 seconds)
        if file_path in self.last_event_time and current_time - self.last_event_time[file_path] < 2:
            return
            
        self.last_event_time[file_path] = current_time
        
        if file_path in self.processing_files:
            return

        # Wait a short time to ensure file is completely written
        time.sleep(1)

        try:
            if file_path.endswith('.pdf') and 'temp_resumes' in file_path:
                self.process_resume(file_path)
            elif file_path.endswith('.txt') and 'temp_jd' in file_path:
                self.process_job_description(file_path)
        except Exception as e:
            pass

    def process_resume(self, resume_path: str):
        """Process a new resume file."""
        self.processing_files.add(resume_path)

        # Wait for corresponding job description
        job_id = self.extract_job_id_from_filename(resume_path)
        if not job_id:
            return

        # Look for matching job description
        jd_path = self.find_matching_jd(job_id)
        if jd_path:
            self.process_matching_files(resume_path, jd_path)
        else:
            # Store resume path for later processing
            self.last_processed[job_id] = {'resume': resume_path}

    def process_job_description(self, jd_path: str):
        """Process a new job description file."""
        self.processing_files.add(jd_path)

        # Extract job ID from filename
        job_id = self.extract_job_id_from_filename(jd_path)
        if not job_id:
            return

        # Look for matching resume
        resume_path = self.find_matching_resume(job_id)
        if resume_path:
            self.process_matching_files(resume_path, jd_path)
        else:
            # Store job description path for later processing
            if job_id in self.last_processed:
                self.last_processed[job_id]['jd'] = jd_path
            else:
                self.last_processed[job_id] = {'jd': jd_path}

    def process_matching_files(self, resume_path: str, jd_path: str):
        """Process matching resume and job description files."""
        job_id = self.extract_job_id_from_filename(resume_path)
        
        # Check if this job ID is already being processed
        if job_id in self.processing_job_ids:
            return
            
        self.processing_job_ids.add(job_id)
        
        with self.processing_lock:  # Use lock to prevent concurrent processing
            try:
                # Match resume against job description
                result = self.matcher.match_resume_to_job(resume_path, jd_path)

                if result['success']:
                    # Get application ID from database using job_id
                    try:
                        from db import get_application_id_by_job_id
                        application_id = get_application_id_by_job_id(job_id)
                        
                        if application_id:
                            match_result = result['matching_result']
                            
                            # Get the data field which contains the JSON string
                            if isinstance(match_result, dict) and 'data' in match_result:
                                json_str = match_result['data']
                                
                                # Clean up the JSON string (remove ```json and ```)
                                json_str = json_str.replace('```json', '').replace('```', '').strip()
                                
                                try:
                                    parsed_result = json.loads(json_str)
                                    match_percentage = float(parsed_result.get("overall_score", 0))
                                    
                                    # Only proceed with update if match percentage is not 0
                                    if match_percentage > 0:
                                        # Update match percentage in database
                                        from db import update_match_percentage
                                        update_match_percentage(application_id, match_percentage)
                                except json.JSONDecodeError:
                                    return
                            else:
                                return
                    except Exception:
                        pass
                    
                    # Clean up files after all processing is done
                    self.cleanup_files(resume_path, jd_path)

            except Exception:
                pass
            finally:
                self.processing_files.remove(resume_path)
                self.processing_files.remove(jd_path)
                if job_id in self.last_processed:
                    del self.last_processed[job_id]
                self.processing_job_ids.remove(job_id)

    def extract_job_id_from_filename(self, file_path: str) -> str:
        """Extract job ID from filename."""
        try:
            filename = os.path.basename(file_path)
            # Assuming filename format: something_jobid_uuid.extension
            parts = filename.split('_')
            if len(parts) >= 2:
                return parts[-2]  # Return the job ID part
        except Exception:
            pass
        return None

    def find_matching_jd(self, job_id: str) -> str:
        """Find matching job description file for a job ID."""
        if job_id in self.last_processed and 'jd' in self.last_processed[job_id]:
            return self.last_processed[job_id]['jd']
        return None

    def find_matching_resume(self, job_id: str) -> str:
        """Find matching resume file for a job ID."""
        if job_id in self.last_processed and 'resume' in self.last_processed[job_id]:
            return self.last_processed[job_id]['resume']
        return None

    def cleanup_files(self, resume_path: str, jd_path: str):
        """Clean up processed files."""
        try:
            if os.path.exists(resume_path):
                os.remove(resume_path)
            if os.path.exists(jd_path):
                os.remove(jd_path)
        except Exception:
            pass

class ResumeMatcher:
    def __init__(self):
        self.temp_resume_dir = os.path.join(os.path.dirname(__file__), 'temp_resumes')
        self.temp_jd_dir = os.path.join(os.path.dirname(__file__), 'temp_jd')
        
        # Create directories if they don't exist
        os.makedirs(self.temp_resume_dir, exist_ok=True)
        os.makedirs(self.temp_jd_dir, exist_ok=True)
        
        # Initialize file watcher
        self.event_handler = ResumeFileHandler(self)
        self.observer = Observer()
        self.observer.schedule(self.event_handler, self.temp_resume_dir, recursive=False)
        self.observer.schedule(self.event_handler, self.temp_jd_dir, recursive=False)
        self.observer.start()

    def __del__(self):
        """Cleanup when the object is destroyed."""
        if hasattr(self, 'observer'):
            self.observer.stop()
            self.observer.join()

    def extract_text_from_pdf(self, pdf_path: str) -> str:
        """Extract text content from PDF file."""
        try:
            with open(pdf_path, 'rb') as file:
                reader = PyPDF2.PdfReader(file)
                text = ""
                for page in reader.pages:
                    text += page.extract_text()
                return text
        except Exception:
            return ""

    def extract_text_from_txt(self, txt_path: str) -> str:
        """Extract text content from TXT file."""
        try:
            with open(txt_path, 'r', encoding='utf-8') as file:
                return file.read()
        except Exception:
            return ""

    def extract_resume_content(self, resume_path: str) -> Dict:
        """Extract structured content from resume using Gemini."""
        try:
            # Extract raw text from PDF
            raw_text = self.extract_text_from_pdf(resume_path)
            
            # Use Gemini to extract structured information
            prompt = f"""
            Extract the following information from this resume:
            1. Skills (list all technical and soft skills)
            2. Experience (years of experience and key roles)
            3. Education
            4. Key achievements
            
            Resume text:
            {raw_text}
            
            Format the response as a JSON with these keys: skills, experience, education, achievements
            """
            
            response = model.generate_content(prompt)
            return response.text
        except Exception:
            return {}

    def extract_job_requirements(self, jd_path: str) -> Dict:
        """Extract structured content from job description using Gemini."""
        try:
            # Extract raw text from TXT
            raw_text = self.extract_text_from_txt(jd_path)
            
            # Use Gemini to extract structured information
            prompt = f"""
            Extract the following information from this job description:
            1. Required skills (technical and soft skills)
            2. Required experience (years and type)
            3. Required education
            4. Key responsibilities
            
            Job description text:
            {raw_text}
            
            Format the response as a JSON with these keys: required_skills, required_experience, required_education, responsibilities
            """
            
            response = model.generate_content(prompt)
            return response.text
        except Exception:
            return {}

    def calculate_matching_score(self, resume_content: Dict, job_requirements: Dict) -> Tuple[float, Dict]:
        """Calculate matching score between resume and job requirements."""
        try:
            # Use Gemini to analyze match
            prompt = f"""
            Analyze the match between this resume and job requirements.
            Calculate a matching score (0-100) and provide detailed analysis.
            
            Resume content:
            {resume_content}
            
            Job requirements:
            {job_requirements}
            
            Format the response as a JSON with these keys:
            - overall_score (number 0-100)
            - skills_match (percentage of required skills present)
            - experience_match (how well experience matches requirements)
            - education_match (how well education matches requirements)
            - detailed_analysis (text explaining the match)
            """
            
            response = model.generate_content(prompt)
            return {
                "success": True,
                "data": response.text
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    def match_resume_to_job(self, resume_path: str, jd_path: str) -> Dict:
        """Main function to match a resume against a job description."""
        try:
            # Extract content from both files
            resume_content = self.extract_resume_content(resume_path)
            job_requirements = self.extract_job_requirements(jd_path)

            # Calculate matching score
            matching_result = self.calculate_matching_score(resume_content, job_requirements)

            return {
                "success": True,
                "resume_content": resume_content,
                "job_requirements": job_requirements,
                "matching_result": matching_result
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

# Example usage
if __name__ == "__main__":
    matcher = ResumeMatcher()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        pass
