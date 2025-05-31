from supabase import create_client, Client
import os
from dotenv import load_dotenv
import logging
from resume_matcher import extract_text_and_image_from_pdf, match_resume_to_job, choose_api
import tempfile
import requests

load_dotenv()

# Configure logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Create handlers
file_handler = logging.FileHandler('resume_matcher.log')
console_handler = logging.StreamHandler()

# Create formatters and add it to handlers
log_format = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
file_handler.setFormatter(log_format)
console_handler.setFormatter(log_format)

# Add handlers to the logger
logger.addHandler(file_handler)
logger.addHandler(console_handler)

# Initialize Supabase client with specific options
supabase: Client = create_client(
    supabase_url=os.getenv('SUPABASE_URL'),
    supabase_key=os.getenv('SUPABASE_KEY')
)

def get_job_details(job_id):
    """Fetch job details from the database"""
    try:
        response = supabase.table('jobs').select('*').eq('id', job_id).execute()
        if response.data:
            return response.data[0]
        return None
    except Exception as e:
        logging.error(f"Error fetching job details: {str(e)}")
        return None

def get_candidate_profile(candidate_id):
    """Fetch candidate profile from the database"""
    try:
        response = supabase.table('candidate_profiles').select('*').eq('user_id', candidate_id).execute()
        if response.data:
            return response.data[0]
        return None
    except Exception as e:
        logging.error(f"Error fetching candidate profile: {str(e)}")
        return None

def update_match_percentage(application_id, match_percentage):
    """Update the match percentage in job_applications table"""
    try:
        logger.info(f"Attempting to update match percentage for application {application_id} to {match_percentage}%")
        response = supabase.table('job_applications').update({
            'match_percentage': match_percentage
        }).eq('id', application_id).execute()
        
        if response.data:
            logger.info(f"Successfully updated match percentage to {match_percentage}% for application {application_id}")
            return response.data
        else:
            logger.error(f"Failed to update match percentage for application {application_id}. No data returned from database.")
            return None
    except Exception as e:
        logger.error(f"Error updating match percentage for application {application_id}: {str(e)}", exc_info=True)
        return None

def process_new_application(application_id):
    """Process a new job application by matching resume and updating match percentage"""
    try:
        logging.info(f"Processing new application: {application_id}")
        
        # Get application details
        response = supabase.table('job_applications').select('*').eq('id', application_id).execute()
        if not response.data:
            logging.error(f"Application not found: {application_id}")
            return False
        
        application = response.data[0]
        job_id = application['job_id']
        resume_url = application['resume_url']
        
        # Get job details
        job = get_job_details(job_id)
        if not job:
            logging.error(f"Job not found: {job_id}")
            return False
        
        # Download resume from URL
        if not resume_url:
            logging.error(f"Resume URL not found for application: {application_id}")
            return False
            
        # Create a temporary file to store the resume
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as temp_file:
            # Download the resume
            response = requests.get(resume_url)
            if response.status_code != 200:
                logging.error(f"Failed to download resume from URL: {resume_url}")
                return False
                
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
                logging.error(f"Failed to update match percentage for application: {application_id}")
                return False
            
            logging.info(f"Successfully processed application {application_id} with match percentage: {match_percentage}%")
            return True
            
        finally:
            # Clean up temporary file
            if os.path.exists(temp_file_path):
                os.unlink(temp_file_path)
    
    except Exception as e:
        logging.error(f"Error processing application {application_id}: {str(e)}")
        return False

def listen_for_new_applications():
    """Listen for new job applications and process them"""
    try:
        # Subscribe to changes in job_applications table
        subscription = supabase.table('job_applications').on('INSERT').execute()
        
        for change in subscription:
            if change.event_type == 'INSERT':
                application_id = change.new['id']
                logging.info(f"New application detected: {application_id}")
                process_new_application(application_id)
                
    except Exception as e:
        logging.error(f"Error in application listener: {str(e)}")
        return False 