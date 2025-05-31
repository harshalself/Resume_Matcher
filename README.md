# Resume Matcher Project

This project is a resume matching system that uses AI to match candidate resumes with job descriptions and calculate match percentages.

## Prerequisites

- Python 3.8 or higher
- Node.js 16 or higher
- npm (comes with Node.js)
- Google API Key for Gemini AI
- Supabase account and credentials

## Backend Setup

1. Open terminal and navigate to the backend directory:

```bash
cd backend
```

2. Create and activate virtual environment:

```bash
# Create virtual environment
py -m venv .venv

# For Windows PowerShell, set execution policy
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass

# Activate virtual environment
.\.venv\Scripts\Activate.ps1
```

3. Install required packages:

```bash
# Install base requirements
pip install -r requirements.txt

# Install additional required packages
pip install --upgrade google-generativeai
pip install google-generativeai PyPDF2
pip install watchdog
pip install flask flask-cors python-dotenv supabase
```

4. Create a `.env` file in the backend directory with the following variables:

```env
GOOGLE_API_KEY=your_google_api_key
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_supabase_key
```

5. Run the backend server:

```bash
python app.py
```

The backend server will start running on `http://localhost:5000`

## Frontend Setup

1. Open a new terminal and navigate to the frontend directory:

```bash
cd frontend
```

2. Install dependencies:

```bash
npm install
```

3. Start the development server:

```bash
npm run dev
```

The frontend application will be available at `http://localhost:3000`

## Project Structure

```
├── backend/
│   ├── app.py              # Main Flask application
│   ├── db.py              # Database operations
│   ├── resume_matcher.py  # Resume matching logic
│   ├── requirements.txt   # Python dependencies
│   └── .env              # Environment variables
│
└── frontend/
    ├── src/
    │   ├── components/    # React components
    │   ├── pages/        # Next.js pages
    │   └── ...
    ├── package.json      # Node.js dependencies
    └── .env             # Environment variables
```

## Features

- Resume parsing and analysis
- Job description matching
- Match percentage calculation
- Real-time updates
- User authentication
- Job application tracking

## Troubleshooting

1. If you encounter any issues with the virtual environment:

   - Make sure you're using the correct Python version
   - Try recreating the virtual environment
   - Ensure all dependencies are installed correctly

2. For frontend issues:

   - Clear npm cache: `npm cache clean --force`
   - Delete node_modules and reinstall: `rm -rf node_modules && npm install`

3. Database connection issues:
   - Verify your Supabase credentials
   - Check if the database tables are created correctly
   - Ensure RLS policies are properly configured

## Contributing

1. Fork the repository
2. Create your feature branch
3. Commit your changes
4. Push to the branch
5. Create a new Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.
