"""
Modern Resume Matching System using Google's Gemini API
"""

import os
import logging
from pathlib import Path
from typing import List, Dict, Tuple, Optional
import google.generativeai as genai
from document_processor import DocumentProcessor

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class GeminiResumeMatcher:
    """
    Modern resume matching system using Google's Gemini API
    """
    
    def __init__(self, api_key: str):
        # Configure Gemini API
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-pro')
        self.document_processor = DocumentProcessor()
        self.resumes_data = {}
        self.job_keywords = None
        
    def load_job_description(self, job_file_path: str) -> Optional[str]:
        """
        Load and preprocess job description
        """
        try:
            with open(job_file_path, 'r', encoding='utf-8') as file:
                job_text = file.read()
                
            # Clean and preprocess
            cleaned_text = self.document_processor.clean_text(job_text)
            processed_text = self.document_processor.preprocess_text(cleaned_text)
            
            # Extract keywords using Gemini
            prompt = f"""
            Extract the top 20 most important technical skills, qualifications, and requirements from this job description.
            Return only the keywords separated by commas:
            
            {processed_text}
            """
            
            response = self.model.generate_content(prompt)
            self.job_keywords = [kw.strip() for kw in response.text.split(',')]
            logger.info(f"Extracted {len(self.job_keywords)} keywords from job description")
            
            return processed_text
            
        except Exception as e:
            logger.error(f"Failed to load job description from {job_file_path}: {e}")
            return None
    
    def load_resumes(self, resume_directory: str) -> bool:
        """
        Load and process all resumes from directory
        """
        try:
            self.resumes_data = self.document_processor.process_directory(resume_directory)
            
            if not self.resumes_data:
                logger.error("No resumes were processed successfully")
                return False
            
            logger.info(f"Successfully loaded {len(self.resumes_data)} resumes")
            return True
            
        except Exception as e:
            logger.error(f"Failed to load resumes: {e}")
            return False
    
    def match_resumes(self, job_description: str, top_k: int = 10) -> List[Tuple[str, float]]:
        """
        Match resumes against job description using Gemini
        """
        try:
            matches = []
            
            for file_path, resume_text in self.resumes_data.items():
                # Create prompt for Gemini
                prompt = f"""
                Analyze how well this resume matches the job description.
                Consider skills, experience, qualifications, and overall fit.
                Return a score between 0 and 1, where 1 is a perfect match.
                Also provide a brief explanation of the match.
                
                Job Description:
                {job_description}
                
                Resume:
                {resume_text}
                
                Format your response as:
                Score: [0-1]
                Explanation: [brief explanation]
                """
                
                response = self.model.generate_content(prompt)
                response_text = response.text
                
                # Extract score from response
                try:
                    score_line = response_text.split('\n')[0]
                    score = float(score_line.split(':')[1].strip())
                    matches.append((file_path, score))
                except:
                    logger.warning(f"Failed to parse score for {file_path}")
                    continue
            
            # Sort by score
            matches.sort(key=lambda x: x[1], reverse=True)
            return matches[:top_k]
            
        except Exception as e:
            logger.error(f"Failed to match resumes: {e}")
            return []
    
    def analyze_match(self, job_description: str, resume_file: str) -> Dict:
        """
        Provide detailed analysis of job-resume match using Gemini
        """
        try:
            if resume_file not in self.resumes_data:
                return {"error": "Resume not found"}
            
            resume_text = self.resumes_data[resume_file]
            
            # Create detailed analysis prompt
            prompt = f"""
            Provide a detailed analysis of how well this resume matches the job description.
            Include:
            1. Overall match score (0-1)
            2. Key skills match
            3. Experience match
            4. Qualifications match
            5. Areas of strength
            6. Areas for improvement
            7. Specific recommendations
            
            Job Description:
            {job_description}
            
            Resume:
            {resume_text}
            
            Format your response as a JSON object with these keys:
            overall_score, skills_match, experience_match, qualifications_match, strengths, improvements, recommendations
            """
            
            response = self.model.generate_content(prompt)
            
            # Parse response into structured format
            try:
                analysis = eval(response.text)  # Convert string to dict
                analysis['resume_file'] = resume_file
                return analysis
            except:
                return {
                    "error": "Failed to parse analysis",
                    "raw_response": response.text
                }
            
        except Exception as e:
            logger.error(f"Match analysis failed: {e}")
            return {"error": str(e)}

class ResultFormatter:
    """
    Format results for display
    """
    
    @staticmethod
    def format_matches(matches: List[Tuple[str, float]], method: str = "gemini") -> List[Dict]:
        """
        Format matches for web display
        """
        formatted_results = []
        
        for rank, (file_path, score) in enumerate(matches, 1):
            # Extract filename from path
            filename = Path(file_path).name
            
            formatted_results.append({
                "rank": rank,
                "filename": filename,
                "filepath": file_path,
                "score": round(score, 4),
                "percentage": round(score * 100, 2),
                "method": method
            })
        
        return formatted_results