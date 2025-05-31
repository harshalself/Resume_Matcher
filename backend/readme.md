# Resume Matcher Backend

This is the backend service for the Resume Matcher application. It provides APIs for matching resumes against job descriptions and updating match percentages in the database.

## Setup

1. Create a virtual environment:

```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Create a `.env` file with the following variables:

```env
# Supabase Configuration
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_supabase_key

# API Keys
OPENAI_API_KEY=your_openai_api_key
CLAUDE_API_KEY=your_claude_api_key

# Model Configuration
ANTHROPIC_MODEL=claude-3-opus-20240229
OPENAI_MODEL=gpt-4-turbo-preview
OPENAI_FAST_MODEL=gpt-3.5-turbo
DEFAULT_MAX_TOKENS=4096
GPT_4O_CONTEXT_WINDOW=128000

# Server Configuration
PORT=5000
DEBUG=True
```

4. Run the server:

```bash
python app.py
```

## API Endpoints

### 1. Health Check

```http
GET /api/health
```

Returns the health status of the backend service.

### 2. Resume Matching

```http
POST /api/resume/match
```

Matches a resume against a job description and updates the match percentage in the database.

Request body:

```json
{
  "application_id": "your_application_id"
}
```

Response:

```json
{
    "status": "success",
    "message": "Resume matching completed",
    "data": {
        "match_percentage": 85,
        "match_reasons": "Strong technical skills | Relevant experience | Good education match",
        "red_flags": ["🚩": ["Location"], "📍": ["Certifications"]]
    }
}
```

### 3. Test Resume Matcher

```http
POST /api/test/resume-matcher
```

Test endpoint to verify resume matcher functionality without database integration.

Request body:

```json
{
  "resume_url": "https://example.com/resume.pdf",
  "job_description": "Job description text here..."
}
```

Response:

```json
{
    "status": "success",
    "message": "Resume matching test completed",
    "data": {
        "match_percentage": 85,
        "match_reasons": "Strong technical skills | Relevant experience | Good education match",
        "red_flags": ["🚩": ["Location"], "📍": ["Certifications"]],
        "extracted_text": "First 500 characters of extracted resume text..."
    }
}
```

## Error Handling

All endpoints return appropriate HTTP status codes and error messages in case of failures:

- 400: Bad Request (missing or invalid parameters)
- 404: Not Found (resource not found)
- 500: Internal Server Error

Error response format:

```json
{
  "error": "Error message description"
}
```

## Dependencies

- Flask: Web framework
- Flask-CORS: CORS support
- Supabase: Database client
- OpenAI/Anthropic: AI models for resume matching
- PyPDF2: PDF processing
- Other dependencies listed in requirements.txt
