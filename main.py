from fastapi import FastAPI, File, UploadFile, HTTPException, Depends, Form
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
import os
import shutil
import uuid
import json
from pathlib import Path

# Database models
class ScanResult(BaseModel):
    id: str
    patient_id: str
    pre_op_path: str
    during_op_path: str
    result_path: str
    created_at: str
    analysis_results: dict

# In-memory storage (replace with a real database in production)
scans_db = []

def save_scan_to_db(scan_data: dict):
    """Save scan data to the database"""
    scans_db.append(scan_data)
    # Save to file for persistence (temporary solution)
    with open('scans_db.json', 'w') as f:
        json.dump(scans_db, f)

def load_scans_from_db():
    """Load scans from the database"""
    if os.path.exists('scans_db.json'):
        with open('scans_db.json', 'r') as f:
            return json.load(f)
    return []

# Initialize FastAPI app
app = FastAPI(
    title="Occlusmart Backend",
    description="Backend API for Occlusmart - AI-Powered Dental Restoration Optimizer",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
from fastapi.staticfiles import StaticFiles
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

# Load existing scans on startup
scans_db = load_scans_from_db()

# Create uploads directory if it doesn't exist
UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)

@app.get("/api/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "ok", "timestamp": datetime.utcnow().isoformat()}

@app.get("/api/scans", response_model=List[dict])
async def get_scans(patient_id: Optional[str] = None):
    """
    Get all scans or filter by patient_id
    """
    if patient_id:
        return [scan for scan in scans_db if scan.get('patient_id') == patient_id]
    return scans_db

@app.get("/api/scans/{scan_id}", response_model=dict)
async def get_scan(scan_id: str):
    """
    Get a specific scan by ID
    """
    for scan in scans_db:
        if scan.get('id') == scan_id:
            # Create a copy of the scan data to avoid modifying the original
            scan_data = scan.copy()
            
            # Convert relative paths to absolute paths for serving files
            base_url = "http://your-server-ip:8000"  # Replace with your actual server URL
            
            # Add full URLs for the image files
            scan_data['pre_op_url'] = f"{base_url}/uploads/{scan_data['pre_op_path']}"
            scan_data['during_op_url'] = f"{base_url}/uploads/{scan_data['during_op_path']}"
            
            # If there's a result image, add its URL as well
            if 'result_path' in scan_data:
                scan_data['result_url'] = f"{base_url}/uploads/{scan_data['result_path']}"
            
            return scan_data
    raise HTTPException(status_code=404, detail="Scan not found")

@app.delete("/api/scans/{scan_id}")
async def delete_scan(scan_id: str):
    """
    Delete a scan by ID
    """
    global scans_db
    initial_length = len(scans_db)
    scans_db = [scan for scan in scans_db if scan.get('id') != scan_id]
    
    if len(scans_db) == initial_length:
        raise HTTPException(status_code=404, detail="Scan not found")
    
    # Save the updated database
    with open('scans_db.json', 'w') as f:
        json.dump(scans_db, f)
    
    return {"status": "success", "message": "Scan deleted"}

@app.post("/api/analyze-occlusion")
async def analyze_occlusion(
    pre_op_image: UploadFile = File(..., alias="pre_op_image"),
    during_op_image: UploadFile = File(..., alias="during_op_image"),
    patient_id: str = Form(...),
):
    """
    Upload pre-op and during-op images for analysis
    """
    try:
        # Generate unique ID for this scan
        scan_id = str(uuid.uuid4())
        
        # Create a directory for this scan
        scan_dir = UPLOAD_DIR / scan_id
        scan_dir.mkdir(exist_ok=True)
        
        # Save uploaded files with proper extensions
        pre_op_ext = os.path.splitext(pre_op_image.filename)[1] if pre_op_image.filename else '.jpg'
        during_op_ext = os.path.splitext(during_op_image.filename)[1] if during_op_image.filename else '.jpg'
        
        pre_op_filename = f"pre_op{pre_op_ext}"
        during_op_filename = f"during_op{during_op_ext}"
        
        pre_op_path = scan_dir / pre_op_filename
        during_op_path = scan_dir / during_op_filename
        
        # Save the uploaded files
        with open(pre_op_path, "wb") as buffer:
            shutil.copyfileobj(pre_op_image.file, buffer)
            
        with open(during_op_path, "wb") as buffer:
            shutil.copyfileobj(during_op_image.file, buffer)
        
        # Here you would typically call your ML model for analysis
        # For now, we'll return mock data
        analysis_results = {
            "status": "success",
            "scan_id": scan_id,
            "analysis": {
                "occlusion_score": 0.85,
                "alignment_score": 0.92,
                "findings": [
                    "Good overall occlusion",
                    "Slight misalignment on lower right molars"
                ],
                "recommendations": [
                    "Consider minor adjustment to lower right molars",
                    "Schedule follow-up in 2 weeks"
                ]
            }
        }
        
        # Save the analysis results
        result_path = scan_dir / "analysis_results.json"
        with open(result_path, 'w') as f:
            json.dump(analysis_results, f)
        
        # Create scan record with the provided patient_id
        from datetime import timezone
        scan_data = {
            "id": scan_id,
            "patient_id": patient_id,
            "pre_op_path": str(pre_op_path.relative_to(UPLOAD_DIR)),
            "during_op_path": str(during_op_path.relative_to(UPLOAD_DIR)),
            "result_path": str(result_path.relative_to(UPLOAD_DIR)),
            "created_at": datetime.now(timezone.utc).isoformat(),  # Include timezone info
            "analysis_results": analysis_results
        }
        
        # Save to database
        save_scan_to_db(scan_data)
            
        return analysis_results
        
    except Exception as e:
        # Clean up files if there was an error
        if 'pre_op_path' in locals() and pre_op_path.exists():
            pre_op_path.unlink()
        if 'during_op_path' in locals() and during_op_path.exists():
            during_op_path.unlink()
            
        raise HTTPException(
            status_code=500,
            detail=f"An error occurred during analysis: {str(e)}"
        )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)