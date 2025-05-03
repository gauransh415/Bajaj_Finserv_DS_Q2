# app.py
import os
import uuid
from typing import List
import pytesseract
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from PIL import Image
import io
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Configure Tesseract path from environment variable or use default
TESSERACT_PATH = os.environ.get("TESSERACT_PATH", "/opt/homebrew/bin/tesseract")
pytesseract.pytesseract.tesseract_cmd = TESSERACT_PATH

# Check for Tesseract availability at startup
try:
    tesseract_version = pytesseract.get_tesseract_version()
    logger.info(f"Tesseract OCR available (version: {tesseract_version})")
except Exception as e:
    logger.error(f"Tesseract OCR not available: {str(e)}")
    logger.error(f"Tesseract path is set to: {TESSERACT_PATH}")
    logger.error("Please ensure Tesseract is installed correctly")

# Initialize FastAPI app
app = FastAPI(
    title="OCR Image Processing API",
    description="API for extracting text from images using Tesseract OCR",
    version="1.0.0",
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Modify in production to specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create uploads directory if it doesn't exist
UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)


@app.get("/")
async def root():
    """Health check endpoint that also confirms Tesseract availability"""
    try:
        tesseract_version = pytesseract.get_tesseract_version()
        return {
            "message": "OCR Image Processing API is running",
            "status": "healthy",
            "tesseract_version": str(tesseract_version),
            "docs_url": "/docs"
        }
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return {
            "message": "OCR Image Processing API is running but Tesseract is not available",
            "status": "degraded",
            "error": str(e),
            "docs_url": "/docs"
        }

@app.post("/ocr/", response_model=dict)
async def process_image(file: UploadFile = File(...)):
    """
    Process an uploaded PNG image with OCR and return extracted text as JSON.
    
    Args:
        file: The image file (PNG format expected)
    
    Returns:
        JSON with extracted text and metadata
    """
    logger.info(f"Processing file: {file.filename}")
    
    # Check if the file is a PNG
    if not file.filename.lower().endswith('.png'):
        logger.warning(f"Invalid file format: {file.filename}")
        raise HTTPException(status_code=400, detail="Only PNG files are supported")
    
    try:
        # Read the image
        contents = await file.read()
        image = Image.open(io.BytesIO(contents))
        
        # Generate a unique filename
        unique_filename = f"{uuid.uuid4()}.png"
        file_path = os.path.join(UPLOAD_DIR, unique_filename)
        
        # Save the image
        image.save(file_path)
        logger.info(f"Image saved to {file_path}")
        
        # Process with Tesseract OCR
        extracted_text = pytesseract.image_to_string(image)
        logger.info("OCR processing completed")
        
        # Return the result
        return {
            "filename": file.filename,
            "saved_as": unique_filename,
            "extracted_text": extracted_text,
            "status": "success"
        }
        
    except Exception as e:
        logger.error(f"Error processing image: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error processing image: {str(e)}")

@app.post("/ocr/batch/", response_model=List[dict])
async def process_multiple_images(files: List[UploadFile] = File(...)):
    """
    Process multiple uploaded PNG images with OCR and return extracted text as JSON.
    
    Args:
        files: List of image files (PNG format expected)
    
    Returns:
        JSON array with extracted text and metadata for each image
    """
    logger.info(f"Processing batch of {len(files)} files")
    
    results = []
    for file in files:
        try:
            # Check if the file is a PNG
            if not file.filename.lower().endswith('.png'):
                results.append({
                    "filename": file.filename,
                    "status": "error",
                    "error": "Only PNG files are supported"
                })
                continue
                
            # Read the image
            contents = await file.read()
            image = Image.open(io.BytesIO(contents))
            
            # Generate a unique filename
            unique_filename = f"{uuid.uuid4()}.png"
            file_path = os.path.join(UPLOAD_DIR, unique_filename)
            
            # Save the image
            image.save(file_path)
            
            # Process with Tesseract OCR
            extracted_text = pytesseract.image_to_string(image)
            
            results.append({
                "filename": file.filename,
                "saved_as": unique_filename,
                "extracted_text": extracted_text,
                "status": "success"
            })
            
        except Exception as e:
            logger.error(f"Error processing {file.filename}: {str(e)}")
            results.append({
                "filename": file.filename,
                "status": "error",
                "error": str(e)
            })
    
    return results

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("app:app", host="0.0.0.0", port=port, reload=True)