import streamlit as st
import requests
import json
from pathlib import Path
import os
import pandas as pd
import plotly.express as px

# Backend API URL
API_URL = "http://localhost:5000"

def display_keywords(keywords, title):
    """Display keywords in a nice format"""
    st.write(f"**{title}**")
    if isinstance(keywords, list):
        st.write(", ".join(keywords))
    else:
        st.write(keywords)

def main():
    st.set_page_config(
        page_title="Resume Matcher - Backend Test",
        page_icon="📄",
        layout="wide"
    )

    st.title("Resume Matcher - Backend Test Interface")
    st.markdown("---")

    # Create tabs for different sections
    tab1, tab2, tab3 = st.tabs(["Upload Files", "View Files", "Match Results"])

    with tab1:
        # Create two columns for job description and resume upload
        col1, col2 = st.columns(2)

        with col1:
            st.subheader("Job Description")
            job_description = st.text_area(
                "Enter Job Description",
                height=300,
                placeholder="Enter the job description here..."
            )
            
            if st.button("Upload Job Description"):
                if job_description:
                    try:
                        # Create a temporary file for the job description
                        job_file = "temp_job.txt"
                        with open(job_file, "w") as f:
                            f.write(job_description)
                        
                        # Upload the file
                        with open(job_file, "rb") as f:
                            files = {"file": f}
                            response = requests.post(f"{API_URL}/upload/job", files=files)
                        
                        if response.status_code == 200:
                            st.success("Job description uploaded successfully!")
                            os.remove(job_file)  # Clean up temp file
                        else:
                            st.error(f"Error: {response.json().get('error', 'Unknown error')}")
                    except Exception as e:
                        st.error(f"Error uploading job description: {str(e)}")
                else:
                    st.warning("Please enter a job description")

        with col2:
            st.subheader("Resume Upload")
            uploaded_file = st.file_uploader(
                "Upload Resume",
                type=["pdf", "doc", "docx", "txt"],
                help="Upload a resume in PDF, DOC, DOCX, or TXT format"
            )
            
            if uploaded_file and st.button("Upload Resume"):
                try:
                    files = {"file": uploaded_file}
                    response = requests.post(f"{API_URL}/upload/resume", files=files)
                    
                    if response.status_code == 200:
                        st.success("Resume uploaded successfully!")
                    else:
                        st.error(f"Error: {response.json().get('error', 'Unknown error')}")
                except Exception as e:
                    st.error(f"Error uploading resume: {str(e)}")

    with tab2:
        st.subheader("Uploaded Files")
        
        # Show job descriptions
        st.write("### Job Descriptions")
        try:
            response = requests.get(f"{API_URL}/jobs")
            if response.status_code == 200:
                jobs = response.json()
                if jobs:
                    for job in jobs:
                        with st.expander(f"Job: {job['title']}"):
                            st.write("**Description:**")
                            st.write(job['description'])
                            if 'keywords' in job:
                                display_keywords(job['keywords'], "Extracted Keywords:")
                else:
                    st.info("No job descriptions uploaded yet.")
        except Exception as e:
            st.error(f"Error fetching job descriptions: {str(e)}")

        # Show uploaded resumes
        st.write("### Uploaded Resumes")
        resume_dir = "Original_Resumes"
        if os.path.exists(resume_dir):
            resumes = os.listdir(resume_dir)
            if resumes:
                for resume in resumes:
                    st.write(f"- {resume}")
            else:
                st.info("No resumes uploaded yet.")
        else:
            st.info("Resume directory not found.")

    with tab3:
        st.subheader("Match Results")
        
        # Get available job descriptions for matching
        try:
            response = requests.get(f"{API_URL}/jobs")
            if response.status_code == 200:
                jobs = response.json()
                
                if jobs:
                    selected_job = st.selectbox(
                        "Select Job Description",
                        options=jobs,
                        format_func=lambda x: x['title']
                    )
                    
                    if st.button("Match Resumes"):
                        try:
                            match_response = requests.get(f"{API_URL}/match/{selected_job['id']}")
                            if match_response.status_code == 200:
                                matches = match_response.json()
                                
                                if matches:
                                    # Convert matches to DataFrame for better display
                                    df = pd.DataFrame(matches)
                                    df = df.sort_values('score', ascending=False)
                                    
                                    # Display overall matching statistics
                                    st.write("### Matching Statistics")
                                    col1, col2, col3 = st.columns(3)
                                    with col1:
                                        st.metric("Total Resumes", len(matches))
                                    with col2:
                                        st.metric("Average Match Score", f"{df['percentage'].mean():.1f}%")
                                    with col3:
                                        st.metric("Best Match", f"{df['percentage'].max():.1f}%")
                                    
                                    # Create a bar chart of match scores
                                    fig = px.bar(df, x='filename', y='percentage',
                                                title='Resume Match Scores',
                                                labels={'filename': 'Resume', 'percentage': 'Match Score (%)'})
                                    st.plotly_chart(fig)
                                    
                                    # Show detailed results
                                    st.write("### Detailed Results")
                                    for match in matches:
                                        with st.expander(f"Resume: {match['filename']} - Score: {match['percentage']}%"):
                                            # Display match details
                                            col1, col2 = st.columns(2)
                                            with col1:
                                                display_keywords(match['job_keywords'], "Job Keywords:")
                                            with col2:
                                                display_keywords(match['resume_keywords'], "Resume Keywords:")
                                            
                                            # Show detailed analysis
                                            try:
                                                analysis_response = requests.get(
                                                    f"{API_URL}/analyze/{selected_job['id']}/{match['resume_file']}"
                                                )
                                                if analysis_response.status_code == 200:
                                                    analysis = analysis_response.json()
                                                    st.write("### Detailed Analysis")
                                                    
                                                    # Display analysis in a structured format
                                                    if 'overall_score' in analysis:
                                                        st.metric("Overall Match Score", f"{float(analysis['overall_score']) * 100:.1f}%")
                                                    
                                                    if 'skills_match' in analysis:
                                                        st.write("**Skills Match:**")
                                                        st.write(analysis['skills_match'])
                                                    
                                                    if 'experience_match' in analysis:
                                                        st.write("**Experience Match:**")
                                                        st.write(analysis['experience_match'])
                                                    
                                                    if 'qualifications_match' in analysis:
                                                        st.write("**Qualifications Match:**")
                                                        st.write(analysis['qualifications_match'])
                                                    
                                                    if 'strengths' in analysis:
                                                        st.write("**Areas of Strength:**")
                                                        st.write(analysis['strengths'])
                                                    
                                                    if 'improvements' in analysis:
                                                        st.write("**Areas for Improvement:**")
                                                        st.write(analysis['improvements'])
                                                    
                                                    if 'recommendations' in analysis:
                                                        st.write("**Recommendations:**")
                                                        st.write(analysis['recommendations'])
                                                else:
                                                    st.error("Failed to get detailed analysis")
                                            except Exception as e:
                                                st.error(f"Error getting analysis: {str(e)}")
                                else:
                                    st.info("No matches found.")
                            else:
                                st.error("Failed to get matches")
                        except Exception as e:
                            st.error(f"Error matching resumes: {str(e)}")
                else:
                    st.info("No job descriptions available. Please upload a job description first.")
            else:
                st.error("Failed to fetch job descriptions")
        except Exception as e:
            st.error(f"Error connecting to backend: {str(e)}")

if __name__ == "__main__":
    main() 