# app.py
import os
import uuid
from typing import Any, List, Dict, Optional
import pytesseract
from fastapi import FastAPI, File, UploadFile, HTTPException, Body
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from PIL import Image
import io
import logging
import re
from pydantic import BaseModel
import cv2
import numpy as np
from models import ExtractionRequest, LabTest, LabTestResponse

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


def extract_lab_tests_from_image(image: np.ndarray) -> List[Dict[str, Any]]:
    """Extract lab test data from medical report image using OCR"""
    # Convert image to text using pytesseract
    text = pytesseract.image_to_string(image)
    
    # Initialize list to store test results
    tests = []
    
    # Extract tests from the OCR text
    
    # Haemoglobin test
    hb_match = re.search(r"(?:Haemoglobin|Blood\s*-\s*Haemoglobin).*?(\d+\.?\d*)\s*([a-zA-Z]/[a-zA-Z][a-zA-Z])\s*(\d+\.?\d*\s*-\s*\d+\.?\d*)", text, re.DOTALL)
    if hb_match:
        hb_value = hb_match.group(1)
        hb_unit = hb_match.group(2)
        hb_ref = hb_match.group(3)
        
        # Check if out of range
        is_out_of_range = False
        if hb_ref and "-" in hb_ref:
            min_val, max_val = map(float, hb_ref.split("-"))
            if float(hb_value) < min_val or float(hb_value) > max_val:
                is_out_of_range = True
                
        tests.append({
            "test_name": "HB ESTIMATION",
            "test_value": hb_value,
            "bio_reference_range": hb_ref,
            "test_unit": "g/dl",  # Standardize unit
            "lab_test_out_of_range": is_out_of_range
        })
    
    # PCV (Packed Cell Volume)
    pcv_match = re.search(r"PCV.*?(\d+\.?\d*)\s*(%|percent)\s*(\d+\.?\d*\s*-\s*\d+\.?\d*)", text, re.DOTALL)
    if pcv_match:
        pcv_value = pcv_match.group(1)
        pcv_ref = pcv_match.group(3)
        
        # Check if out of range
        is_out_of_range = False
        if pcv_ref and "-" in pcv_ref:
            min_val, max_val = map(float, pcv_ref.split("-"))
            if float(pcv_value) < min_val or float(pcv_value) > max_val:
                is_out_of_range = True
                
        tests.append({
            "test_name": "PCV (PACKED CELL VOLUME)",
            "test_value": pcv_value,
            "bio_reference_range": pcv_ref,
            "test_unit": "%",  # Standardize unit
            "lab_test_out_of_range": is_out_of_range
        })
    
    # Prothrombin Time
    pt_value_match = re.search(r"Prothrombin Time.*?(\d+\.?\d*)\s*Seconds", text, re.DOTALL)
    pt_ref_match = re.search(r"Seconds\s*(\d+\.?\d*\s*-\s*\d+\.?\d*)", text)
    
    if pt_value_match:
        pt_value = pt_value_match.group(1)
        pt_ref = pt_ref_match.group(1) if pt_ref_match else "11-16"  # Default from example
        
        # Check if out of range
        is_out_of_range = False
        if pt_ref and "-" in pt_ref:
            min_val, max_val = map(float, pt_ref.split("-"))
            if float(pt_value) < min_val or float(pt_value) > max_val:
                is_out_of_range = True
        
        tests.append({
            "test_name": "PROTHROMBIN TIME",
            "test_value": pt_value,
            "bio_reference_range": pt_ref,
            "test_unit": "seconds",
            "lab_test_out_of_range": is_out_of_range
        })
    
    # Pattern for other common tests
    # Format: Test Name, Value, Unit, Reference Range
    test_pattern = r"([A-Za-z\s\-\(\)]+)\s*(\d+\.?\d*)\s*([a-zA-Z%/\.]+)\s*(\d+\.?\d*\s*-\s*\d+\.?\d*)"
    
    for match in re.finditer(test_pattern, text):
        test_name = match.group(1).strip().upper()
        test_value = match.group(2)
        unit = match.group(3)
        ref_range = match.group(4)
        
        # Skip tests we've already processed specifically
        if any(test["test_name"].upper() == test_name for test in tests):
            continue
            
        # Check if out of range
        is_out_of_range = False
        if ref_range and "-" in ref_range:
            try:
                min_val, max_val = map(float, ref_range.split("-"))
                if float(test_value) < min_val or float(test_value) > max_val:
                    is_out_of_range = True
            except (ValueError, AttributeError):
                pass
                
        tests.append({
            "test_name": test_name,
            "test_value": test_value,
            "bio_reference_range": ref_range,
            "test_unit": unit,
            "lab_test_out_of_range": is_out_of_range
        })
    
    return tests

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


@app.post("/get-lab-tests", response_model=LabTestResponse)
async def extract_lab_tests(file: UploadFile = File(...)):
    """
    Extract lab test data from uploaded medical report image
    
    This endpoint processes lab test report images to extract key information including:
    - Test names
    - Test values
    - Reference ranges
    - Units
    - Whether values are out of normal range
    
    Returns data in standardized JSON format matching the expected output.
    """
    logger.info(f"Processing lab test file: {file.filename}")
    try:
        # Read file content
        content = await file.read()
        
        # Convert to OpenCV format
        image = cv2.imdecode(np.frombuffer(content, np.uint8), cv2.IMREAD_COLOR)
        if image is None:
            logger.error(f"Invalid image format: {file.filename}")
            return LabTestResponse(is_success=False, data=[], error="Invalid image format")
        
        # Extract lab tests from image
        lab_tests = extract_lab_tests_from_image(image)
        
        if lab_tests:
            logger.info(f"Successfully extracted {len(lab_tests)} lab tests from {file.filename}")
            return LabTestResponse(is_success=True, data=[LabTest(**test) for test in lab_tests])
        else:
            logger.warning(f"No lab tests detected in image: {file.filename}")
            return LabTestResponse(is_success=False, data=[], error="No lab tests detected in image")
            
    except Exception as e:
        logger.error(f"Error processing lab test image: {str(e)}")
        return LabTestResponse(is_success=False, data=[], error=f"Processing error: {str(e)}")

@app.post("/extract/", response_model=dict)
async def extract_specific_info(
    file: UploadFile = File(...),
    extraction_request: ExtractionRequest = Body(...)
):
    """
    Extract specific information from an image based on provided patterns.
    
    Args:
        file: The image file (PNG format expected)
        extraction_request: List of patterns to extract
    
    Returns:
        JSON with extracted information based on patterns
    """
    logger.info(f"Processing file: {file.filename}")
    
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
        
        # Extract information based on patterns
        extracted_info = {}
        for pattern in extraction_request.patterns:
            matches = re.findall(pattern.pattern, extracted_text)
            extracted_info[pattern.name] = matches if matches else []
        
        # Return the result
        return {
            "filename": file.filename,
            "saved_as": unique_filename,
            "extracted_info": extracted_info,
            "status": "success"
        }
        
    except Exception as e:
        logger.error(f"Error processing image: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error processing image: {str(e)}")

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("app:app", host="0.0.0.0", port=port, reload=True)