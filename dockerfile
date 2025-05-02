# Dockerfile optimized for Render deployment
FROM python:3.10-slim

# Install Tesseract OCR and required dependencies
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    tesseract-ocr-eng \
    # libtesseract-dev \
    # libleptonica-dev \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Verify Tesseract installation
RUN tesseract --version && \
    tesseract --list-langs

WORKDIR /app

# Copy requirements file and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application code
COPY . .

# Create uploads directory
RUN mkdir -p uploads && chmod 777 uploads

# Make build script executable if it exists
RUN if [ -f build.sh ]; then chmod +x build.sh; fi

# Default environment variables
ENV PORT=8000
ENV TESSERACT_PATH=/usr/bin/tesseract
ENV PYTHONUNBUFFERED=1

# Expose port
EXPOSE $PORT

# Command to run the application
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "$PORT"]