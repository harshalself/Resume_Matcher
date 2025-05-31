from flask import Flask, send_file, jsonify, request
from flask_cors import CORS
import os
import tempfile
import requests
from db import get_job_application_resume, download_resume_from_storage, get_job_description
from resume_matcher import ResumeMatcher
import json
import uuid

app = Flask(__name__)
CORS(app)

# Create temp directories if they don't exist
TEMP_DIR = os.path.join(os.path.dirname(__file__), 'temp_resumes')
TEMP_JD_DIR = os.path.join(os.path.dirname(__file__), 'temp_jd')
os.makedirs(TEMP_DIR, exist_ok=True)
os.makedirs(TEMP_JD_DIR, exist_ok=True)

# Initialize ResumeMatcher
resume_matcher = ResumeMatcher()

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

@app.route('/api/job-description/download', methods=['POST'])
def download_and_store_job_description():
    try:
        data = request.json
        job_id = data.get('jobId')
        company_name = data.get('companyName')
        position = data.get('position')

        if not all([job_id, company_name, position]):
            return jsonify({
                "error": "Missing required parameters",
                "status": "error"
            }), 400

        # Get job description from database
        print(f"\nFetching job description for job ID: {job_id}")
        job_data = get_job_description(job_id)
        
        if not job_data:
            print("No job description found in database")
            return jsonify({
                "error": "Job description not found",
                "status": "error"
            }), 404

        print(f"\nFound job data: {job_data}")

        # Sanitize company name and position for filename
        sanitized_company = "".join(c for c in company_name if c.isalnum() or c in (' ', '-', '_')).strip()
        sanitized_company = sanitized_company.replace(' ', '_')
        sanitized_position = "".join(c for c in position if c.isalnum() or c in (' ', '-', '_')).strip()
        sanitized_position = sanitized_position.replace(' ', '_')
        
        # Create unique filename
        filename = f"{sanitized_company}_{sanitized_position}_{job_id}_{uuid.uuid4().hex[:8]}.txt"
        temp_path = os.path.join(TEMP_JD_DIR, filename)

        print(f"\nSaving job description to: {temp_path}")

        # Save job description to file
        with open(temp_path, 'w', encoding='utf-8') as f:
            f.write(f"Company: {company_name}\n")
            f.write(f"Position: {position}\n")
            f.write(f"Job ID: {job_id}\n")
            f.write("\nDescription:\n")
            f.write(job_data.get('description', ''))
            f.write("\n\nRequirements:\n")
            f.write(job_data.get('requirements', 'N/A'))

        storage_key = f"temp_jd_{job_id}_{sanitized_company}"
        
        print(f"\nSuccessfully saved job description")
        
        return jsonify({
            "success": True,
            "message": "Job description downloaded and stored successfully",
            "storageKey": storage_key,
            "filePath": temp_path
        })

    except Exception as e:
        print(f"Error in download_and_store_job_description: {str(e)}")
        print(f"Error type: {type(e)}")
        return jsonify({
            "error": str(e),
            "status": "error"
        }), 500

@app.route('/api/match-resume', methods=['POST'])
def match_resume():
    try:
        data = request.json
        resume_path = data.get('resumePath')
        jd_path = data.get('jdPath')

        if not all([resume_path, jd_path]):
            return jsonify({
                "error": "Missing required parameters",
                "status": "error"
            }), 400

        print(f"\n=== Starting resume matching ===")
        print(f"Resume path: {resume_path}")
        print(f"Job description path: {jd_path}")

        # Match resume against job description
        result = resume_matcher.match_resume_to_job(resume_path, jd_path)

        if not result['success']:
            return jsonify({
                "error": result.get('error', 'Failed to match resume'),
                "status": "error"
            }), 500

        return jsonify({
            "success": True,
            "message": "Resume matched successfully",
            "result": result
        })

    except Exception as e:
        print(f"Error in match_resume: {str(e)}")
        print(f"Error type: {type(e)}")
        return jsonify({
            "error": str(e),
            "status": "error"
        }), 500

if __name__ == '__main__':
    print("\n=== Starting Flask server ===")
    print(f"Debug mode: {app.debug}")
    print(f"Environment: {os.getenv('FLASK_ENV', 'development')}")
    app.run(debug=True, port=5000)
