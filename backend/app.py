from flask import Flask, request, jsonify
from flask_cors import CORS
import os
from dotenv import load_dotenv
from db import get_job_details, get_candidate_profile, update_match_percentage, supabase
from resume_matcher import extract_text_and_image_from_pdf, match_resume_to_job, choose_api
import tempfile
import logging
import requests
import threading
import time

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),  # Output to console
        logging.FileHandler('resume_matcher.log')  # Output to file
    ]
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

def check_new_applications():
    """Poll for new applications that need processing"""
    while True:
        try:
            # Query for applications that haven't been processed yet
            logger.info("Checking for new unprocessed applications...")
            response = supabase.table('job_applications').select('*').is_('match_percentage', 'null').execute()
            
            if response.data:
                logger.info(f"Found {len(response.data)} new applications to process")
                for application in response.data:
                    try:
                        # Process each new application
                        application_id = application['id']
                        job_id = application['job_id']
                        candidate_id = application['candidate_id']
                        resume_url = application['resume_url']
                        
                        logger.info(f"Processing application {application_id} for job {job_id} and candidate {candidate_id}")
                        logger.info(f"Resume URL: {resume_url}")
                        
                        # Get job details
                        logger.info(f"Fetching job details for job {job_id}")
                        job = get_job_details(job_id)
                        if not job:
                            logger.error(f"Job not found for application {application_id}")
                            continue
                        logger.info(f"Successfully fetched job details for job {job_id}")
                        logger.info(f"Job description length: {len(job['description'])} characters")
                        
                        # Download and process resume
                        logger.info(f"Downloading resume from URL: {resume_url}")
                        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as temp_file:
                            response = requests.get(resume_url)
                            if response.status_code != 200:
                                logger.error(f"Failed to download resume for application {application_id}. Status code: {response.status_code}")
                                continue
                            
                            temp_file.write(response.content)
                            temp_file_path = temp_file.name
                            logger.info(f"Resume downloaded and saved to temporary file: {temp_file_path}")
                        
                        try:
                            # Initialize API choice
                            logger.info("Initializing API for resume matching")
                            choose_api()
                            
                            # Extract text and images from PDF
                            logger.info("Extracting text and images from PDF")
                            resume_text, resume_images = extract_text_and_image_from_pdf(temp_file_path)
                            logger.info(f"Successfully extracted {len(resume_text)} characters of text and {len(resume_images)} images from PDF")
                            
                            # Match resume with job description
                            logger.info("Starting resume matching process")
                            match_result = match_resume_to_job(
                                resume_text=resume_text,
                                job_desc=job['description'],
                                file_path=temp_file_path,
                                resume_images=resume_images
                            )
                            
                            # Update match percentage
                            match_percentage = match_result.get('score', 0)
                            logger.info(f"Match percentage calculated: {match_percentage}%")
                            logger.info(f"Match reasons: {match_result.get('match_reasons', 'No reasons provided')}")
                            logger.info(f"Red flags: {match_result.get('red_flags', [])}")
                            
                            logger.info(f"Updating match percentage in database for application {application_id}")
                            update_result = update_match_percentage(application_id, match_percentage)
                            
                            if update_result:
                                logger.info(f"Successfully updated match percentage to {match_percentage}% for application {application_id}")
                            else:
                                logger.error(f"Failed to update match percentage for application {application_id}")
                            
                        finally:
                            # Clean up temporary file
                            if os.path.exists(temp_file_path):
                                os.unlink(temp_file_path)
                                logger.info(f"Cleaned up temporary file: {temp_file_path}")
                                
                    except Exception as e:
                        logger.error(f"Error processing application {application.get('id')}: {str(e)}", exc_info=True)
            else:
                logger.info("No new applications found to process")
            
            # Wait for 30 seconds before checking again
            logger.info("Waiting 30 seconds before next check...")
            time.sleep(30)
            
        except Exception as e:
            logger.error(f"Error in application checker: {str(e)}", exc_info=True)
            logger.info("Waiting 30 seconds before retrying...")
            time.sleep(30)  # Wait before retrying

def start_application_listener():
    """Start the application checker in a separate thread"""
    try:
        logger.info("Starting application checker...")
        checker_thread = threading.Thread(target=check_new_applications, daemon=True)
        checker_thread.start()
        logger.info("Application checker started successfully")
    except Exception as e:
        logger.error(f"Error starting application checker: {str(e)}")

@app.route('/api/health', methods=['GET'])
def health_check():
    return jsonify({"status": "healthy", "message": "Backend is running"})

@app.route('/api/test/resume-matcher', methods=['POST'])
def test_resume_matcher():
    """Test endpoint to verify resume matcher functionality"""
    try:
        # Get test data from request
        data = request.get_json()
        if not data or 'resume_url' not in data or 'job_description' not in data:
            return jsonify({
                "error": "Both resume_url and job_description are required",
                "example": {
                    "resume_url": "https://example.com/resume.pdf",
                    "job_description": "Job description text here..."
                }
            }), 400

        resume_url = data['resume_url']
        job_description = data['job_description']

        # Create a temporary file to store the resume
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as temp_file:
            # Download the resume
            response = requests.get(resume_url)
            if response.status_code != 200:
                return jsonify({"error": "Failed to download resume"}), 400
                
            temp_file.write(response.content)
            temp_file_path = temp_file.name

        try:
            # Initialize API choice
            choose_api()

            # Extract text and images from PDF
            resume_text, resume_images = extract_text_and_image_from_pdf(temp_file_path)
            
            # Match resume with job description
            match_result = match_resume_to_job(
                resume_text=resume_text,
                job_desc=job_description,
                file_path=temp_file_path,
                resume_images=resume_images
            )
            
            return jsonify({
                "status": "success",
                "message": "Resume matching test completed",
                "data": {
                    "match_percentage": match_result.get('score', 0),
                    "match_reasons": match_result.get('match_reasons', ''),
                    "red_flags": match_result.get('red_flags', []),
                    "extracted_text": resume_text[:500] + "..." if len(resume_text) > 500 else resume_text
                }
            })
            
        finally:
            # Clean up temporary file
            if os.path.exists(temp_file_path):
                os.unlink(temp_file_path)
    
    except Exception as e:
        logger.error(f"Error in resume matcher test: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/resume/match', methods=['POST'])
def match_resume():
    try:
        # Get application ID from request
        data = request.get_json()
        if not data or 'application_id' not in data:
            return jsonify({"error": "Application ID is required"}), 400
        
        application_id = data['application_id']
        
        # Get job application details
        response = supabase.table('job_applications').select('*').eq('id', application_id).execute()
        if not response.data:
            return jsonify({"error": "Application not found"}), 404
        
        application = response.data[0]
        job_id = application['job_id']
        candidate_id = application['candidate_id']
        resume_url = application['resume_url']
        
        # Get job details
        job = get_job_details(job_id)
        if not job:
            return jsonify({"error": "Job not found"}), 404
        
        # Get candidate profile
        candidate = get_candidate_profile(candidate_id)
        if not candidate:
            return jsonify({"error": "Candidate profile not found"}), 404
        
        # Download resume from URL
        if not resume_url:
            return jsonify({"error": "Resume URL not found"}), 400
            
        # Create a temporary file to store the resume
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as temp_file:
            # Download the resume
            response = requests.get(resume_url)
            if response.status_code != 200:
                return jsonify({"error": "Failed to download resume"}), 400
                
            temp_file.write(response.content)
            temp_file_path = temp_file.name
        
        try:
            # Initialize API choice
            choose_api()

            # Extract text and images from PDF
            resume_text, resume_images = extract_text_and_image_from_pdf(temp_file_path)
            
            # Match resume with job description
            match_result = match_resume_to_job(
                resume_text=resume_text,
                job_desc=job['description'],
                file_path=temp_file_path,
                resume_images=resume_images
            )
            
            # Extract match percentage
            match_percentage = match_result.get('score', 0)
            
            # Update match percentage in database
            update_result = update_match_percentage(application_id, match_percentage)
            
            if not update_result:
                return jsonify({"error": "Failed to update match percentage"}), 500
            
            return jsonify({
                "status": "success",
                "message": "Resume matching completed",
                "data": {
                    "match_percentage": match_percentage,
                    "match_reasons": match_result.get('match_reasons', ''),
                    "red_flags": match_result.get('red_flags', [])
                }
            })
            
        finally:
            # Clean up temporary file
            if os.path.exists(temp_file_path):
                os.unlink(temp_file_path)
    
    except Exception as e:
        logger.error(f"Error in resume matching: {str(e)}")
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    # Start the application listener
    start_application_listener()
    
    # Start the Flask application
    port = int(os.getenv('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True) 