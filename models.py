from pydantic import BaseModel
from typing import List, Optional

class LabTest(BaseModel):
    test_name: str
    test_value: str
    bio_reference_range: str
    test_unit: str
    lab_test_out_of_range: bool

class LabTestResponse(BaseModel):
    is_success: bool
    data: List[LabTest]
    error: Optional[str] = None

class ExtractionPattern(BaseModel):
    """Model for defining extraction patterns"""
    name: str
    pattern: str
    description: Optional[str] = None

class ExtractionRequest(BaseModel):
    """Model for extraction request"""
    patterns: List[ExtractionPattern]