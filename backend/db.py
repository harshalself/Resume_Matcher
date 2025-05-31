from supabase import create_client
import os
from dotenv import load_dotenv
import time
import json

load_dotenv()

# Initialize Supabase client
supabase = create_client(
    os.getenv("SUPABASE_URL"),
    os.getenv("SUPABASE_KEY")
)

def get_job_application_resume(application_id: str, max_retries=3, retry_delay=2):
    """
    Fetch resume URL from job applications table for a specific application
    with retry mechanism
    """
    for attempt in range(max_retries):
        try:
            # First verify if the application exists
            check_response = supabase.table('job_applications').select('id').eq('id', application_id).execute()
            
            if not check_response.data:
                if attempt < max_retries - 1:
                    time.sleep(retry_delay)
                    continue
                return None
            
            # Get the full application details
            response = supabase.table('job_applications').select('id, resume_url, candidate_id, job_id').eq('id', application_id).execute()
            
            if not response.data:
                if attempt < max_retries - 1:
                    time.sleep(retry_delay)
                    continue
                return None
                
            if len(response.data) == 0:
                if attempt < max_retries - 1:
                    time.sleep(retry_delay)
                    continue
                return None
                
            application = response.data[0]
            
            if not application.get('resume_url'):
                if attempt < max_retries - 1:
                    time.sleep(retry_delay)
                    continue
                return None
                
            return application['resume_url']
            
        except Exception:
            if attempt < max_retries - 1:
                time.sleep(retry_delay)
                continue
            return None

def download_resume_from_storage(resume_url: str, temp_path: str):
    """
    Download resume from Supabase storage bucket
    """
    try:
        if not resume_url:
            return False
            
        # Extract bucket name and file path from URL
        # Assuming URL format: https://<project>.supabase.co/storage/v1/object/public/<bucket>/<path>
        parts = resume_url.split('/')
        if len(parts) < 2:
            return False
            
        bucket_name = parts[-2]
        file_path = parts[-1]
        
        # Download file from storage
        response = supabase.storage.from_(bucket_name).download(file_path)
        
        if not response:
            return False
            
        # Save to temp file
        with open(temp_path, 'wb') as f:
            f.write(response)
            
        return True
        
    except Exception:
        return False

def get_job_description(job_id: str, max_retries=3, retry_delay=2):
    """
    Fetch job description from jobs table for a specific job
    with retry mechanism
    """
    for attempt in range(max_retries):
        try:
            # First verify if the job exists
            check_response = supabase.table('jobs').select('id').eq('id', job_id).execute()
            
            if not check_response.data:
                if attempt < max_retries - 1:
                    time.sleep(retry_delay)
                    continue
                return None
            
            # Get the full job details
            response = supabase.table('jobs').select('description, requirements, company, position').eq('id', job_id).execute()
            
            if not response.data:
                if attempt < max_retries - 1:
                    time.sleep(retry_delay)
                    continue
                return None
                
            if len(response.data) == 0:
                if attempt < max_retries - 1:
                    time.sleep(retry_delay)
                    continue
                return None
                
            job_data = response.data[0]
            
            if not job_data.get('description'):
                if attempt < max_retries - 1:
                    time.sleep(retry_delay)
                    continue
                return None
                
            return job_data
            
        except Exception:
            if attempt < max_retries - 1:
                time.sleep(retry_delay)
                continue
            return None

def update_match_percentage(application_id: str, match_percentage: float) -> bool:
    """
    Update the match percentage for a job application
    """
    try:
        print(f"\n=== Updating match percentage in database ===")
        print(f"Application ID: {application_id}")
        print(f"Match percentage: {match_percentage}")

        print("Executing database update query...")
        response = supabase.table('job_applications').update({
            "match_percentage": match_percentage
        }).eq('id', application_id).execute()

        if not response.data:
            print("No data returned from update operation")
            # Verify if the update actually happened
            verify_response = supabase.table('job_applications').select('match_percentage').eq('id', application_id).execute()
            if verify_response.data and verify_response.data[0].get('match_percentage') == match_percentage:
                print("Update verified - match percentage was updated successfully")
                return True
            print("Update verification failed - match percentage was not updated")
            return False

        print(f"Database update response: {response.data}")
        print("Successfully updated match percentage in database")
        return True

    except Exception as e:
        print(f"Error updating match percentage in database: {str(e)}")
        print(f"Error type: {type(e)}")
        return False

def get_application_id_by_job_id(job_id: str) -> str:
    """
    Get the application ID for a given job ID
    """
    try:
        job_id = str(job_id).strip()
        
        # First verify if the job exists
        check_response = supabase.table('jobs').select('id').eq('id', job_id).execute()
        
        if not check_response.data:
            return None
            
        # Get the application ID
        response = supabase.table('job_applications').select('id, job_id, applied_at').eq('job_id', job_id).execute()
        
        if not response.data:
            return None
            
        if len(response.data) == 0:
            return None
            
        # Get the most recent application
        applications = sorted(response.data, key=lambda x: x.get('applied_at', ''), reverse=True)
        application_id = applications[0]['id']
        
        return application_id
        
    except Exception:
        return None
