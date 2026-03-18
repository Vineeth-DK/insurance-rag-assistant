from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List
import os

# Import your RAG engine functions
from rag_engine import build_vector_store, get_insurance_answer

app = FastAPI(title="Insurance RAG API")

# --- CORS Setup (Crucial for React Native) ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Global State ---
# Store the vector database in memory so the analyze endpoint can access it
app.state.vectorstore = None

# --- Pydantic Models ---
class ClaimRequest(BaseModel):
    client_name: str
    client_age: int
    claim_factors: str
    api_key: str

# --- Endpoints ---

@app.post("/upload")
async def upload_pdfs(files: List[UploadFile] = File(...)):
    """Receives multiple PDFs, builds the vector database, and cleans up."""
    if not files:
        raise HTTPException(status_code=400, detail="No files provided")

    saved_file_paths = []
    
    try:
        # 1. Save all uploaded files to the local disk temporarily
        for file in files:
            file_location = f"temp_{file.filename}"
            # Use await file.read() for FastAPI async uploads
            with open(file_location, "wb+") as file_object:
                file_object.write(await file.read())
            saved_file_paths.append(file_location)
            
        # 2. Build the FAISS vector store using the list of file paths
        # This calls the updated function in rag_engine.py
        app.state.vectorstore = build_vector_store(saved_file_paths)
        
        # 3. Clean up: Delete the temporary PDF files from your backend folder
        for path in saved_file_paths:
            if os.path.exists(path):
                os.remove(path)
                
        return {"success": True, "message": f"Successfully loaded {len(files)} documents into the AI brain."}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/analyze")
async def analyze_claim(request: ClaimRequest):
    """Processes the claim using the uploaded documents and Llama 3.1."""
    if app.state.vectorstore is None:
        raise HTTPException(status_code=400, detail="Please upload policy documents first.")
        
    try:
        # Call the LLM using the loaded vectorstore
        answer = get_insurance_answer(
            client_name=request.client_name,
            client_age=request.client_age,
            claim_factors=request.claim_factors,
            api_key=request.api_key,
            vectorstore=app.state.vectorstore
        )
        return {"success": True, "answer": answer}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))