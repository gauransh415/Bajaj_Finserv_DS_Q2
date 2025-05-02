# Medical Reports Text Extraction API

A robust OCR (Optical Character Recognition) API built with FastAPI for extracting text from medical reports and images.

## 🚀 Live Demo

The API is live and can be accessed at:

**Production URL:** [https://medical-reports-text-extraction.onrender.com/docs](https://medical-reports-text-extraction.onrender.com/docs)

## 📋 Overview

This API extracts text from uploaded PNG images using Tesseract OCR. It's designed specifically for medical reports but can be used for any text extraction needs. The service provides both single image and batch processing capabilities, with persistent storage for uploaded images.

## ✨ Features

- **Single Image Processing**: Extract text from individual PNG images
- **Batch Processing**: Process multiple images in one request
- **Health Monitoring**: Built-in health check with Tesseract version information
- **Persistent Storage**: Secure storage for uploaded images
- **Docker Deployment**: Containerized for easy deployment and scaling
- **Comprehensive Logging**: Detailed logging for monitoring and debugging

## 🛠️ Technology Stack

- **FastAPI**: Modern, fast web framework for building APIs with Python
- **Tesseract OCR**: Powerful open-source OCR engine
- **Uvicorn + Gunicorn**: ASGI server implementation for production deployment
- **Docker**: Containerization for consistent environments
- **Render**: Cloud hosting platform for deployment

## 📝 API Documentation

Interactive API documentation is available at:
- Swagger UI: [https://medical-reports-text-extraction.onrender.com/docs](https://medical-reports-text-extraction.onrender.com/docs)
- ReDoc: [https://medical-reports-text-extraction.onrender.com/redoc](https://medical-reports-text-extraction.onrender.com/redoc)

## 🔌 API Endpoints

### Health Check
```
GET /
```
Returns the API status and Tesseract version information.

### Process Single Image
```
POST /ocr/
```
Processes a single PNG image and returns the extracted text.

### Process Multiple Images
```
POST /ocr/batch/
```
Processes multiple PNG images and returns extracted text for each.

## 🚀 Deployment

The project is configured for deployment on Render using Docker. The deployment configuration is defined in `render.yaml`.

### Environment Variables

- `PORT`: The port on which the service runs (default: 8000)
- `TESSERACT_PATH`: Path to the Tesseract binary (default: /usr/bin/tesseract)
- `PYTHONUNBUFFERED`: Ensures Python output is sent straight to the terminal (for logging)

## 💻 Local Development

### Prerequisites

- Python 3.11 or higher
- Tesseract OCR installed on your system
- Docker (optional, for containerized development)

### Setup

1. Clone the repository
   ```bash
   git clone https://github.com/yourusername/medical-reports-text-extraction.git
   cd medical-reports-text-extraction
   ```

2. Create a virtual environment
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies
   ```bash
   pip install -r requirements.txt
   ```

4. Run the development server
   ```bash
   python app.py
   ```

### Using Docker

1. Build the Docker image
   ```bash
   docker build -t ocr-api .
   ```

2. Run the container
   ```bash
   docker run -p 8000:8000 ocr-api
   ```

## 📁 Project Structure

```
├── app.py              # Main application entry point
├── requirements.txt    # Python dependencies
├── Dockerfile          # Docker configuration
├── render.yaml         # Render deployment configuration
├── start.sh            # Startup script for Docker container
└── uploads/            # Directory for storing uploaded images
```


## 👥 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request
