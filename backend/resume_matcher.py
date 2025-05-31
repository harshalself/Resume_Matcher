import json, json5, PyPDF2, anthropic, openai
from openai import OpenAI
import logging
import requests, base64, os
from bs4 import BeautifulSoup
from PIL import Image
import io
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
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

# Model configuration
ANTHROPIC_MODEL = os.getenv('ANTHROPIC_MODEL')
OPENAI_MODEL = os.getenv('OPENAI_MODEL')
OPENAI_FAST_MODEL = os.getenv('OPENAI_FAST_MODEL')
DEFAULT_MAX_TOKENS = int(os.getenv('DEFAULT_MAX_TOKENS'))
GPT_4O_CONTEXT_WINDOW = int(os.getenv('GPT_4O_CONTEXT_WINDOW'))

# Initialize API clients
clients = {
    "anthropic": anthropic.Anthropic(api_key=os.getenv("CLAUDE_API_KEY")),
    "openai": openai.OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
}

# Global variable to store the chosen API
chosen_api = "anthropic"

def choose_api():
    """Choose between Anthropic and OpenAI APIs"""
    global chosen_api
    # Default to Anthropic for better performance
    chosen_api = "anthropic"
    logger.info(f"Selected API: {chosen_api.capitalize()}")

def talk_to_ai(prompt, max_tokens=DEFAULT_MAX_TOKENS, image_data=None, client=None):
    """Communicate with AI model"""
    try:
        if chosen_api == "anthropic":
            response = talk_to_anthropic(prompt, max_tokens, image_data, client)
        else:
            response = talk_to_openai(prompt, max_tokens, image_data, client)
        return response.strip() if response else ""
    except Exception as e:
        logger.error(f"Error in talk_to_ai: {str(e)}")
        return ""

def talk_to_anthropic(prompt, max_tokens=DEFAULT_MAX_TOKENS, image_data=None, client=None):
    """Communicate with Anthropic's Claude model"""
    if client is None:
        client = clients['anthropic']

    messages = [{"role": "user", "content": [{"type": "text", "text": prompt}]}]

    if image_data:
        for img in image_data:
            base64_image = base64.b64encode(img).decode('utf-8')
            messages[0]["content"].append({
                "type": "image",
                "source": {
                    "type": "base64",
                    "media_type": "image/jpeg",
                    "data": base64_image
                }
            })

    try:
        response = client.messages.create(
            model=ANTHROPIC_MODEL,
            max_tokens=max_tokens,
            messages=messages
        )
        return response.content[0].text.strip()
    except Exception as e:
        logger.error(f"Error in Anthropic AI communication: {str(e)}")
        return ""

def talk_to_openai(prompt, max_tokens=DEFAULT_MAX_TOKENS, image_data=None, client=None):
    """Communicate with OpenAI's GPT model"""
    if client is None:
        client = clients['openai']

    content = [{"type": "text", "text": prompt}]
    if image_data:
        for img in image_data:
            base64_image = base64.b64encode(img).decode('utf-8')
            content.append({
                "type": "image_url",
                "image_url": {
                    "url": f"data:image/jpeg;base64,{base64_image}"
                }
            })

    try:
        response = client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=[{"role": "user", "content": content}],
            max_tokens=max_tokens
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        logger.error(f"Error in OpenAI communication: {str(e)}")
        return ""

def extract_text_and_image_from_pdf(file_path):
    """Extract text and images from PDF file"""
    try:
        text = ""
        resume_images = []

        # Extract text from all pages of the PDF using PyPDF2
        reader = PyPDF2.PdfReader(file_path)
        for page in reader.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"

        # Convert PDF pages to images
        from pdf2image import convert_from_path
        images = convert_from_path(file_path)
        for i, img in enumerate(images):
            # Convert to grayscale and compress image
            img_gray = img.convert('L')
            img_buffer = io.BytesIO()
            img_gray.save(img_buffer, format='JPEG', quality=51)
            img_buffer.seek(0)

            # Add image data to resume_images list
            resume_images.append(img_buffer.getvalue())

            # If text extraction is insufficient, perform OCR
            if not text or len(text.strip()) < 500:
                import pytesseract
                ocr_text = pytesseract.image_to_string(Image.open(img_buffer))
                text += ocr_text + "\n"

        if not images:
            logger.error(f"No images found in PDF {file_path}")

        return text.strip(), resume_images

    except Exception as e:
        logger.error(f"Error extracting text and image from PDF {file_path}: {str(e)}")
        return "", []

def match_resume_to_job(resume_text, job_desc, file_path, resume_images, client=None):
    """Match resume against job description and calculate match percentage"""
    try:
        logger.info("Starting resume matching process")
        logger.info(f"Resume text length: {len(resume_text)} characters")
        logger.info(f"Job description length: {len(job_desc)} characters")
        
        # Extract job requirements
        logger.info("Extracting job requirements from job description")
        job_requirements = extract_job_requirements(job_desc, client)
        if not job_requirements:
            logger.error("Failed to extract job requirements")
            return {'score': 0, 'match_reasons': "Error: Failed to extract job requirements", 'red_flags': []}
        logger.info(f"Successfully extracted job requirements: {json.dumps(job_requirements, indent=2)}")

        # Initialize scoring criteria
        criteria = [
            {
                'name': 'Technical Skills',
                'key': 'technical_skills',
                'weight': job_requirements['emphasis'].get('technical_skills_weight', 50),
                'description': 'Evaluate technical skills match',
                'factors': ['Required skills', 'Optional skills', 'Proficiency level']
            },
            {
                'name': 'Experience',
                'key': 'experience',
                'weight': job_requirements['emphasis'].get('experience_weight', 20),
                'description': 'Evaluate experience match',
                'factors': ['Years of experience', 'Relevant experience', 'Achievements']
            },
            {
                'name': 'Education',
                'key': 'education',
                'weight': job_requirements['emphasis'].get('education_weight', 10),
                'description': 'Evaluate education match',
                'factors': ['Degree level', 'Field of study', 'Relevance to job']
            },
            {
                'name': 'Soft Skills',
                'key': 'soft_skills',
                'weight': job_requirements['emphasis'].get('soft_skills_weight', 20),
                'description': 'Evaluate soft skills match',
                'factors': ['Communication', 'Teamwork', 'Leadership']
            }
        ]

        # Calculate scores
        scores = {}
        total_weight = sum(criterion['weight'] for criterion in criteria)
        total_score = 0
        red_flags = {'🚩': [], '📍': []}

        logger.info("Starting evaluation of each criterion")
        logger.info(f"Total weight of all criteria: {total_weight}%")
        
        for criterion in criteria:
            logger.info(f"Evaluating {criterion['name']} (Weight: {criterion['weight']}%)")
            prompt = f"""
            Evaluate the candidate's resume based on the criterion: "{criterion['name']}".

            Criterion Description:
            {criterion['description']}

            Factors to consider:
            {', '.join(criterion['factors'])}

            Job Requirements:
            {json.dumps(job_requirements, indent=2)}

            Resume:
            {resume_text}

            Provide your evaluation as an integer score from 0 to 100.
            Only return the integer score, nothing else.
            """

            logger.info(f"Sending evaluation request to AI for {criterion['name']}")
            response = talk_to_ai(prompt, client=client)
            logger.info(f"Received AI response for {criterion['name']}: {response}")
            
            try:
                score = int(str(response).strip())
                if 0 <= score <= 100:
                    criterion['score'] = score
                    logger.info(f"{criterion['name']} raw score: {score}/100")
                    if score < 10:
                        if criterion['weight'] >= 30:
                            red_flags['🚩'].append(criterion['name'])
                            logger.warning(f"🚩 Critical red flag in {criterion['name']} (score: {score})")
                        else:
                            red_flags['📍'].append(criterion['name'])
                            logger.warning(f"📍 Minor red flag in {criterion['name']} (score: {score})")
                else:
                    raise ValueError(f"Score out of range: {score}")
            except Exception as e:
                logger.error(f"Error parsing score for criterion {criterion['name']}: {str(e)}")
                criterion['score'] = 0

            scores[criterion['key']] = criterion['score']
            weighted_score = (criterion['score'] * criterion['weight']) / 100
            total_score += weighted_score
            logger.info(f"{criterion['name']} weighted score: {weighted_score:.2f} (raw score: {criterion['score']} * weight: {criterion['weight']}%)")

        # Calculate final score
        final_score = int((total_score / total_weight) * 100)
        logger.info(f"Total weighted score: {total_score:.2f}")
        logger.info(f"Final match percentage calculated: {final_score}%")

        # Generate match reasons
        logger.info("Generating match reasons")
        reasons_prompt = f"""
        Based on the evaluation, provide 3-4 key reasons for the match between the candidate's resume and the job requirements.

        Resume:
        {resume_text}

        Job Requirements:
        {json.dumps(job_requirements, indent=2)}

        Provide the reasons in telegraphic English, max 10 words per reason, separated by ' | '.
        """
        match_reasons = talk_to_ai(reasons_prompt, max_tokens=100, client=client)
        logger.info(f"Match reasons generated: {match_reasons}")

        result = {
            'score': final_score,
            'match_reasons': match_reasons,
            'red_flags': red_flags
        }
        logger.info(f"Resume matching completed. Final score: {final_score}%")
        return result

    except Exception as e:
        logger.error(f"Error in resume matching: {str(e)}", exc_info=True)
        return {'score': 0, 'match_reasons': f"Error: {str(e)}", 'red_flags': []}

def extract_job_requirements(job_desc, client=None):
    """Extract requirements from job description"""
    prompt = f"""
    Extract the key requirements from the following job description.

    Job Description:
    {job_desc}

    Provide the output in the following JSON format:
    {{
      "required_skills": [list of strings],
      "optional_skills": [list of strings],
      "experience_years": integer,
      "education_level": string,
      "soft_skills": [list of strings],
      "emphasis": {{
        "technical_skills_weight": integer,
        "soft_skills_weight": integer,
        "experience_weight": integer,
        "education_weight": integer
      }}
    }}
    """
    response = talk_to_ai(prompt, max_tokens=2000, client=client)
    try:
        if isinstance(response, dict):
            return response
        return json5.loads(response)
    except Exception as e:
        logger.error(f"Error parsing job requirements: {str(e)}")
        return None