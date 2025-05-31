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
    print(f"\n=== Starting resume fetch for application ID: {application_id} ===")
    print(f"Using Supabase URL: {os.getenv('SUPABASE_URL')}")
    
    for attempt in range(max_retries):
        try:
            print(f"\nAttempt {attempt + 1}:")
            print(f"Querying job_applications table for ID: {application_id}")
            
            # First verify if the application exists
            check_response = supabase.table('job_applications').select('id').eq('id', application_id).execute()
            print(f"Check response: {check_response.data}")
            
            if not check_response.data:
                print(f"Application ID {application_id} not found in database")
                if attempt < max_retries - 1:
                    print(f"Waiting {retry_delay} seconds before next attempt...")
                    time.sleep(retry_delay)
                    continue
                return None
            
            # Get the full application details
            response = supabase.table('job_applications').select('id, resume_url, candidate_id, job_id').eq('id', application_id).execute()
            
            # Log the raw response for debugging
            print(f"Raw response type: {type(response)}")
            print(f"Response data: {response.data}")
            
            if not response.data:
                print(f"Response data is empty")
                if attempt < max_retries - 1:
                    print(f"Waiting {retry_delay} seconds before next attempt...")
                    time.sleep(retry_delay)
                    continue
                return None
                
            if len(response.data) == 0:
                print(f"No records found in response data")
                if attempt < max_retries - 1:
                    print(f"Waiting {retry_delay} seconds before next attempt...")
                    time.sleep(retry_delay)
                    continue
                return None
                
            application = response.data[0]
            print(f"Found application data: {application}")
            
            if not application.get('resume_url'):
                print(f"No resume_url field in application data")
                if attempt < max_retries - 1:
                    print(f"Waiting {retry_delay} seconds before next attempt...")
                    time.sleep(retry_delay)
                    continue
                return None
                
            print(f"Successfully found resume URL: {application['resume_url']}")
            return application['resume_url']
            
        except Exception as e:
            print(f"Attempt {attempt + 1} failed with error: {str(e)}")
            print(f"Error type: {type(e)}")
            if attempt < max_retries - 1:
                print(f"Waiting {retry_delay} seconds before next attempt...")
                time.sleep(retry_delay)
                continue
            return None

def download_resume_from_storage(resume_url: str, temp_path: str):
    """
    Download resume from Supabase storage bucket
    """
    try:
        if not resume_url:
            print("No resume URL provided")
            return False
            
        print(f"\n=== Starting resume download ===")
        print(f"Resume URL: {resume_url}")
        print(f"Temp path: {temp_path}")
            
        # Extract bucket name and file path from URL
        # Assuming URL format: https://<project>.supabase.co/storage/v1/object/public/<bucket>/<path>
        parts = resume_url.split('/')
        if len(parts) < 2:
            print(f"Invalid resume URL format: {resume_url}")
            return False
            
        bucket_name = parts[-2]
        file_path = parts[-1]
        
        print(f"Extracted bucket: {bucket_name}")
        print(f"Extracted file path: {file_path}")
        
        # Download file from storage
        print("Attempting to download from storage...")
        response = supabase.storage.from_(bucket_name).download(file_path)
        
        if not response:
            print("No response from storage download")
            return False
            
        # Save to temp file
        print(f"Saving to temp file: {temp_path}")
        with open(temp_path, 'wb') as f:
            f.write(response)
            
        print(f"Successfully downloaded resume to: {temp_path}")
        return True
        
    except Exception as e:
        print(f"Error downloading resume: {str(e)}")
        print(f"Error type: {type(e)}")
        return False
