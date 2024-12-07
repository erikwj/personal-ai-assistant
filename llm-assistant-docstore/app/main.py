from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from app.services.document_service import DocumentService
from app.models.document import DocumentResponse, QueryRequest, QueryResponse
import logging
from pydantic import BaseModel

app = FastAPI(title="LLM Assistant Document Store")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust this in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

try:
    doc_service = DocumentService()
except Exception as e:
    logging.error(f"Error initializing document service: {str(e)}")
    doc_service = None

@app.post("/documents/", response_model=DocumentResponse)
async def upload_document(file: UploadFile = File(...)):
    if doc_service is None:
        raise HTTPException(status_code=503, detail="Document service not initialized")
    
    try:
        content = await file.read()
        doc_id = await doc_service.add_document(file.filename, content)
        return DocumentResponse(id=doc_id, filename=file.filename)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/query", response_model=QueryResponse)
async def query_documents(query: QueryRequest):
    if doc_service is None:
        raise HTTPException(status_code=503, detail="Document service not initialized")
    
    try:
        results = await doc_service.query_documents(
            query.text,
            num_results=query.num_results,
            min_relevance=query.min_relevance,
            min_similarity=query.min_similarity
        )
        
        # Count relevant results
        relevant_results = sum(1 for r in results if r["is_relevant"])
        
        return QueryResponse(
            results=results,
            query_text=query.text,
            total_results=len(results),
            relevant_results=relevant_results
        )
    except Exception as e:
        logging.error(f"Error processing query: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    if doc_service is None:
        return {"status": "unhealthy", "message": "Document service not initialized"}
    return {"status": "healthy"}

@app.get("/stats")
async def get_stats():
    if doc_service is None:
        raise HTTPException(status_code=503, detail="Document service not initialized")
    
    try:
        return {
            "status": "ok",
            "collection_name": doc_service.db._collection.name,
            "document_count": doc_service.db._collection.count(),
            "persist_directory": doc_service.persist_directory
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/documents")
async def list_documents():
    if doc_service is None:
        raise HTTPException(status_code=503, detail="Document service not initialized")
    
    try:
        # Get all documents from ChromaDB
        results = doc_service.db.get()
        
        # Format the response
        documents = []
        if results and results['documents']:
            for i, doc in enumerate(results['documents']):
                documents.append({
                    "id": results['ids'][i],
                    "text": doc[:200] + "..." if len(doc) > 200 else doc,  # First 200 chars
                    "metadata": results['metadatas'][i] if results['metadatas'] else {}
                })
        
        return {
            "total_documents": len(documents),
            "documents": documents
        }
    except Exception as e:
        logging.error(f"Error listing documents: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

class PromptRequest(BaseModel):
    prompt: str
    num_context: int = 3
    min_similarity: float = 0.1

class PromptResponse(BaseModel):
    context: str
    has_context: bool

@app.post("/context", response_model=PromptResponse)
async def get_context(request: PromptRequest):
    """Get relevant context for a prompt"""
    if doc_service is None:
        raise HTTPException(status_code=503, detail="Document service not initialized")
    
    try:
        context = await doc_service.get_context_for_prompt(
            prompt=request.prompt,
            num_results=request.num_context,
            min_similarity=request.min_similarity
        )
        
        return PromptResponse(
            context=context,
            has_context=bool(context)
        )
    except Exception as e:
        logging.error(f"Error getting context: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e)) 