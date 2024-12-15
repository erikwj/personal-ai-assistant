from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import TextLoader, DirectoryLoader
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_core.documents import Document
import os
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def load_documents(directory_path: str, db_directory: str):
    try:
        logger.info(f"Loading documents from {directory_path}")
        
        # Ensure directories exist
        os.makedirs(directory_path, exist_ok=True)
        os.makedirs(db_directory, exist_ok=True)

        # Load all documents from directory
        loader = DirectoryLoader(
            directory_path,
            glob="**/*.txt",
            loader_cls=TextLoader
        )
        documents = loader.load()
        logger.info(f"Loaded {len(documents)} documents")

        if not documents:
            logger.warning("No documents found!")
            return None

        # Store complete documents
        complete_docs = {}
        for doc in documents:
            complete_docs[doc.metadata['source']] = doc.page_content
        logger.info(f"Stored {len(complete_docs)} complete documents")

        # Create chunks for searching
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            length_function=len,
        )
        
        chunks = []
        for doc in documents:
            doc_chunks = text_splitter.split_text(doc.page_content)
            for chunk in doc_chunks:
                chunks.append({
                    'content': chunk,
                    'metadata': {
                        'source': doc.metadata['source'],
                        'full_document': complete_docs[doc.metadata['source']]
                    }
                })
        logger.info(f"Created {len(chunks)} chunks")

        # Convert chunks to documents with metadata
        chunked_documents = [
            Document(
                page_content=chunk['content'],
                metadata=chunk['metadata']
            )
            for chunk in chunks
        ]

        # Initialize embeddings and vector store
        logger.info("Initializing embeddings...")
        embeddings = HuggingFaceEmbeddings()
        
        # Create or load the vector store
        logger.info(f"Creating vector store in {db_directory}")
        db = Chroma.from_documents(
            documents=chunked_documents,
            embedding=embeddings,
            persist_directory=db_directory
        )
        
        db.persist()
        logger.info("Vector store created and persisted successfully")
        return db

    except Exception as e:
        logger.error(f"Error in load_documents: {str(e)}", exc_info=True)
        raise

if __name__ == "__main__":
    # Test the document loading
    DOCUMENTS_DIR = "documents"
    DB_DIR = "data/chromadb"
    
    try:
        db = load_documents(DOCUMENTS_DIR, DB_DIR)
        if db:
            # Test a simple query to verify the database works
            results = db.similarity_search("test query", k=1)
            logger.info(f"Test query returned {len(results)} results")
            logger.info("Database creation and testing successful!")
    except Exception as e:
        logger.error(f"Failed to create database: {str(e)}") 