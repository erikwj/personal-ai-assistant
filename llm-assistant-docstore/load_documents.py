import os
from pathlib import Path
from app.services.document_service import DocumentService
import logging
import asyncio

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DOCUMENTS_DIR = "documents"  # Directory to watch for documents

async def load_documents():
    # Ensure directories exist
    os.makedirs(DOCUMENTS_DIR, exist_ok=True)
    os.makedirs("data/chromadb", exist_ok=True)
    
    try:
        # Initialize document service
        doc_service = DocumentService()
        
        # Process all files in the documents directory
        for file_path in Path(DOCUMENTS_DIR).glob('**/*'):
            if file_path.is_file() and file_path.suffix in ['.txt', '.md', '.pdf']:
                try:
                    logger.info(f"Processing {file_path}")
                    with open(file_path, 'rb') as f:
                        content = f.read()
                    doc_id = await doc_service.add_document(file_path.name, content)
                    logger.info(f"Successfully loaded {file_path.name} with ID: {doc_id}")
                except Exception as e:
                    logger.error(f"Error processing {file_path}: {str(e)}")
        
    except Exception as e:
        logger.error(f"Error in load_documents: {str(e)}")
        raise

if __name__ == "__main__":
    asyncio.run(load_documents()) 