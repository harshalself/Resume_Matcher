from flask import Flask, send_file, jsonify, request
from flask_cors import CORS
import os
import tempfile
import requests
from db import get_job_application_resume, download_resume_from_storage
import json
import uuid

app = Flask(__name__)
CORS(app)

# Create temp directory if it doesn't exist
TEMP_DIR = os.path.join(os.path.dirname(__file__), 'temp_resumes')
os.makedirs(TEMP_DIR, exist_ok=True)

@app.route('/api/resume/download', methods=['POST'])
def download_and_store_resume():
    try:
        data = request.json
        resume_url = data.get('resumeUrl')
        candidate_name = data.get('candidateName')
        job_id = data.get('jobId')

        if not all([resume_url, candidate_name, job_id]):
            return jsonify({
                "error": "Missing required parameters",
                "status": "error"
            }), 400

        # Sanitize candidate name for filename
        sanitized_name = "".join(c for c in candidate_name if c.isalnum() or c in (' ', '-', '_')).strip()
        sanitized_name = sanitized_name.replace(' ', '_')
        
        # Create unique filename
        filename = f"{sanitized_name}_{job_id}_{uuid.uuid4().hex[:8]}.pdf"
        temp_path = os.path.join(TEMP_DIR, filename)

        # Download the resume
        response = requests.get(resume_url)
        if not response.ok:
            return jsonify({
                "error": f"Failed to download resume: {response.status_code}",
                "status": "error"
            }), 500

        # Save to temp file
        with open(temp_path, 'wb') as f:
            f.write(response.content)

        storage_key = f"temp_resume_{job_id}_{sanitized_name}"
        
        return jsonify({
            "success": True,
            "message": "Resume downloaded and stored successfully",
            "storageKey": storage_key,
            "filePath": temp_path
        })

    except Exception as e:
        print(f"Error in download_and_store_resume: {str(e)}")
        return jsonify({
            "error": str(e),
            "status": "error"
        }), 500

@app.route('/api/resume/<application_id>', methods=['GET'])
def download_resume(application_id):
    print(f"\n=== Starting resume download request ===")
    print(f"Application ID: {application_id}")
    
    try:
        # Get resume URL from database
        print("\nFetching resume URL from database...")
        resume_url = get_job_application_resume(application_id)
        
        if not resume_url:
            print("No resume URL found in database")
            return jsonify({
                "error": "Resume not found",
                "application_id": application_id,
                "status": "not_found"
            }), 404

        print(f"\nFound resume URL: {resume_url}")

        # Create temporary directory
        temp_dir = tempfile.mkdtemp()
        temp_file_path = os.path.join(temp_dir, f"resume_{application_id}.pdf")
        print(f"Created temp directory: {temp_dir}")
        print(f"Temp file path: {temp_file_path}")

        # Download resume from storage
        print("\nAttempting to download resume from storage...")
        success = download_resume_from_storage(resume_url, temp_file_path)
        
        if not success:
            print("Failed to download resume from storage")
            return jsonify({
                "error": "Failed to download resume",
                "application_id": application_id,
                "resume_url": resume_url,
                "status": "download_failed"
            }), 500

        print(f"\nSuccessfully downloaded resume to {temp_file_path}")

        # Send file to client
        print("\nSending file to client...")
        return send_file(
            temp_file_path,
            as_attachment=True,
            download_name=f"resume_{application_id}.pdf",
            mimetype='application/pdf'
        )

    except Exception as e:
        print(f"\nError processing resume request: {str(e)}")
        print(f"Error type: {type(e)}")
        return jsonify({
            "error": str(e),
            "application_id": application_id,
            "status": "error"
        }), 500

    finally:
        # Clean up temporary file
        if 'temp_file_path' in locals() and os.path.exists(temp_file_path):
            print(f"\nCleaning up temp file: {temp_file_path}")
            os.remove(temp_file_path)
        if 'temp_dir' in locals() and os.path.exists(temp_dir):
            print(f"Cleaning up temp directory: {temp_dir}")
            os.rmdir(temp_dir)

if __name__ == '__main__':
    print("\n=== Starting Flask server ===")
    print(f"Debug mode: {app.debug}")
    print(f"Environment: {os.getenv('FLASK_ENV', 'development')}")
    app.run(debug=True, port=5000)
