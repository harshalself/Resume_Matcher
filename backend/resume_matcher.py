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

    def on_created(self, event):
        if event.is_directory:
            return

        file_path = event.src_path
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
            print(f"Error processing file {file_path}: {str(e)}")

    def process_resume(self, resume_path: str):
        """Process a new resume file."""
        print(f"\n=== New resume detected: {resume_path} ===")
        self.processing_files.add(resume_path)

        # Wait for corresponding job description
        job_id = self.extract_job_id_from_filename(resume_path)
        if not job_id:
            print("Could not extract job ID from resume filename")
            return

        # Look for matching job description
        jd_path = self.find_matching_jd(job_id)
        if jd_path:
            print(f"Found matching job description: {jd_path}")
            self.process_matching_files(resume_path, jd_path)
        else:
            print(f"Waiting for job description for job ID: {job_id}")
            # Store resume path for later processing
            self.last_processed[job_id] = {'resume': resume_path}

    def process_job_description(self, jd_path: str):
        """Process a new job description file."""
        print(f"\n=== New job description detected: {jd_path} ===")
        self.processing_files.add(jd_path)

        # Extract job ID from filename
        job_id = self.extract_job_id_from_filename(jd_path)
        if not job_id:
            print("Could not extract job ID from job description filename")
            return

        # Look for matching resume
        resume_path = self.find_matching_resume(job_id)
        if resume_path:
            print(f"Found matching resume: {resume_path}")
            self.process_matching_files(resume_path, jd_path)
        else:
            print(f"Waiting for resume for job ID: {job_id}")
            # Store job description path for later processing
            if job_id in self.last_processed:
                self.last_processed[job_id]['jd'] = jd_path
            else:
                self.last_processed[job_id] = {'jd': jd_path}

    def process_matching_files(self, resume_path: str, jd_path: str):
        """Process matching resume and job description files."""
        try:
            print("\n=== Processing matching files ===")
            print(f"Resume: {resume_path}")
            print(f"Job Description: {jd_path}")

            # Match resume against job description
            result = self.matcher.match_resume_to_job(resume_path, jd_path)

            if result['success']:
                print("\n=== Matching Results ===")
                print(json.dumps(result['matching_result'], indent=2))
                
                # Clean up files
                self.cleanup_files(resume_path, jd_path)
            else:
                print(f"Error in matching: {result.get('error')}")

        except Exception as e:
            print(f"Error processing matching files: {str(e)}")
        finally:
            self.processing_files.remove(resume_path)
            self.processing_files.remove(jd_path)
            job_id = self.extract_job_id_from_filename(resume_path)
            if job_id in self.last_processed:
                del self.last_processed[job_id]

    def extract_job_id_from_filename(self, file_path: str) -> str:
        """Extract job ID from filename."""
        try:
            filename = os.path.basename(file_path)
            # Assuming filename format: something_jobid_uuid.extension
            parts = filename.split('_')
            if len(parts) >= 2:
                return parts[-2]  # Return the job ID part
        except Exception as e:
            print(f"Error extracting job ID: {str(e)}")
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
            print("\n=== Cleaning up files ===")
            if os.path.exists(resume_path):
                os.remove(resume_path)
                print(f"Removed resume: {resume_path}")
            if os.path.exists(jd_path):
                os.remove(jd_path)
                print(f"Removed job description: {jd_path}")
        except Exception as e:
            print(f"Error cleaning up files: {str(e)}")

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
        
        print("\n=== Resume Matcher Initialized ===")
        print(f"Watching directories:")
        print(f"- Resumes: {self.temp_resume_dir}")
        print(f"- Job Descriptions: {self.temp_jd_dir}")

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
        except Exception as e:
            print(f"Error extracting text from PDF: {str(e)}")
            return ""

    def extract_text_from_txt(self, txt_path: str) -> str:
        """Extract text content from TXT file."""
        try:
            with open(txt_path, 'r', encoding='utf-8') as file:
                return file.read()
        except Exception as e:
            print(f"Error extracting text from TXT: {str(e)}")
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
        except Exception as e:
            print(f"Error extracting resume content: {str(e)}")
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
        except Exception as e:
            print(f"Error extracting job requirements: {str(e)}")
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
            print(f"Error calculating matching score: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }


    def match_resume_to_job(self, resume_path: str, jd_path: str) -> Dict:
        """Main function to match a resume against a job description."""
        try:
            print(f"\n=== Starting resume matching process ===")
            print(f"Resume path: {resume_path}")
            print(f"Job description path: {jd_path}")

            # Extract content from both files
            print("\nExtracting resume content...")
            resume_content = self.extract_resume_content(resume_path)
            print("Resume content extracted successfully")

            print("\nExtracting job requirements...")
            job_requirements = self.extract_job_requirements(jd_path)
            print("Job requirements extracted successfully")

            # Calculate matching score
            print("\nCalculating matching score...")
            matching_result = self.calculate_matching_score(resume_content, job_requirements)
            print("Matching score calculated successfully")

            return {
                "success": True,
                "resume_content": resume_content,
                "job_requirements": job_requirements,
                "matching_result": matching_result
            }

        except Exception as e:
            print(f"Error in match_resume_to_job: {str(e)}")
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
        print("\nStopping resume matcher...")
