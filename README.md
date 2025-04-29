# Bajaj Data Science Q2

A FastAPI-based service for processing and extracting data from medical lab reports using OCR technology.

## Features

- Upload lab report images
- Extract text using OCR
- Process and structure lab report data
- Retrieve formatted lab report results

## Setup

### Local Development

1. Create a virtual environment:
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

3. Install Tesseract OCR on your system:
   - For Ubuntu: `sudo apt-get install tesseract-ocr`
   - For macOS: `brew install tesseract`
   - For Windows: Download installer from https://github.com/UB-Mannheim/tesseract/wiki

4. Run the application:
   ```
   uvicorn app.main:app --reload
   ```

5. Access the API documentation at http://127.0.0.1:8000/docs

### Docker

1. Build the Docker image:
   ```
   docker build -t lab-report-api .
   ```

2. Run the container:
   ```
   docker run -p 8000:8000 lab-report-api
   ```

## API Endpoints

- `POST /api/lab-reports/upload`: Upload a lab report image
- `GET /api/lab-reports/{report_id}`: Get processed lab report data
