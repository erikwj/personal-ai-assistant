import os
os.environ["LANGCHAIN_DISABLE_TELEMETRY"] = "true"

from pathlib import Path
import uuid
from typing import List, Optional, Dict
import logging
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma
from langchain.schema import Document
from app.models.document import QueryResponse, QueryResult, DocumentMetadata, RelevanceLevel

class DocumentService:
    def __init__(self):
        # Initialize embedding model from local path
        self.embedding_model = HuggingFaceEmbeddings(
            model_name="models/embeddings",  # Local path to model
            model_kwargs={'device': 'cpu'},
            encode_kwargs={'normalize_embeddings': True}
        )
        
        # Initialize ChromaDB
        self.persist_directory = "data/chromadb"
        self.db = self._initialize_db()
        
        logging.info("Vector store initialized")

    def _initialize_db(self) -> Chroma:
        """Initialize or load existing ChromaDB"""
        if os.path.exists(self.persist_directory):
            return self._load_vector_db()
        return Chroma(
            persist_directory=self.persist_directory,
            embedding_function=self.embedding_model
        )

    def _load_vector_db(self) -> Chroma:
        """Load existing vector database"""
        return Chroma(
            persist_directory=self.persist_directory,
            embedding_function=self.embedding_model
        )

    def _chunk_text(self, text: str, chunk_size: int = 500) -> List[str]:
        """Split text into chunks of approximately chunk_size characters"""
        sentences = text.split('.')
        chunks = []
        current_chunk = []
        current_size = 0
        
        for sentence in sentences:
            sentence = sentence.strip() + '.'
            sentence_size = len(sentence)
            
            if current_size + sentence_size > chunk_size and current_chunk:
                chunks.append(' '.join(current_chunk))
                current_chunk = [sentence]
                current_size = sentence_size
            else:
                current_chunk.append(sentence)
                current_size += sentence_size
        
        if current_chunk:
            chunks.append(' '.join(current_chunk))
        
        return chunks

    async def add_document(self, filename: str, content: bytes) -> str:
        try:
            # Check if document with this filename already exists
            existing_docs = self.db._collection.get(
                where={"source": filename}
            )
            if existing_docs['ids']:
                logging.info(f"Document {filename} already exists, skipping")
                return existing_docs['ids'][0]

            text = content.decode('utf-8')
            doc_id = str(uuid.uuid4())
            chunks = self._chunk_text(text)
            
            logging.info(f"Processing document {filename} with {len(chunks)} chunks")
            
            documents = []
            for chunk in chunks:
                documents.append(
                    Document(
                        page_content=chunk,
                        metadata={
                            "source": filename,
                            "full_document": text
                        }
                    )
                )
            
            self.db.add_documents(documents)
            self.db.persist()
            
            logging.info(f"Successfully added document {filename} with ID {doc_id}")
            return doc_id
            
        except Exception as e:
            logging.error(f"Error adding document: {str(e)}")
            logging.exception("Full traceback:")
            raise

    def _get_relevance_level(self, similarity: float) -> RelevanceLevel:
        """Determine relevance level based on similarity score"""
        # Using similarity score directly (higher is better)
        if similarity > 0.5:     # Very high similarity
            return RelevanceLevel.HIGH
        elif similarity > 0.2:   # Good similarity
            return RelevanceLevel.MEDIUM
        elif similarity > 0.1:   # Acceptable similarity
            return RelevanceLevel.LOW
        return RelevanceLevel.NOT_RELEVANT  # Too dissimilar

    def _is_relevant(self, relevance: RelevanceLevel) -> bool:
        """Determine if a result is relevant based on relevance level"""
        # Consider all levels except NOT_RELEVANT as relevant
        return relevance != RelevanceLevel.NOT_RELEVANT

    async def query_documents(
        self, 
        query: str, 
        num_results: int = 3, 
        min_relevance: Optional[RelevanceLevel] = None,
        min_similarity: Optional[float] = None
    ) -> QueryResponse:
        try:
            logging.info(f"Querying documents with: '{query}'")
            
            doc_count = self.db._collection.count()
            logging.info(f"Total documents in collection: {doc_count}")
            
            if doc_count == 0:
                logging.warning("No documents in collection")
                return QueryResponse(results=[], has_results=False)
            
            # Search in ChromaDB
            logging.info(f"Searching for top {num_results * 2} results")
            results = self.db.similarity_search_with_relevance_scores(
                query,
                k=num_results * 2  # Get more results to filter
            )
            
            logging.info(f"Found {len(results)} initial results")
            
            # Use dict to deduplicate by source while keeping highest similarity
            source_results = {}
            for doc, similarity in results:
                source = doc.metadata["source"]
                if source not in source_results or similarity > source_results[source][1]:
                    source_results[source] = (doc, similarity)
            
            # Convert back to list and format results
            formatted_results = []
            for doc, similarity in source_results.values():
                relevance = self._get_relevance_level(similarity)
                
                # Apply filters
                if min_similarity is not None and similarity < min_similarity:
                    logging.info(f"Skipping result due to low similarity: {similarity} < {min_similarity}")
                    continue
                    
                if min_relevance is not None and relevance.value < min_relevance.value:
                    logging.info(f"Skipping result due to low relevance: {relevance} < {min_relevance}")
                    continue
                
                result = QueryResult(
                    text=doc.page_content,
                    metadata=DocumentMetadata(
                        source=doc.metadata["source"],
                        full_document=doc.metadata["full_document"],
                        similarity=float(similarity),
                        relevance=relevance
                    ),
                    is_relevant=self._is_relevant(relevance)
                )
                formatted_results.append(result)
            
            # Sort by similarity
            formatted_results.sort(key=lambda x: x.metadata.similarity, reverse=True)
            
            # Limit to requested number
            formatted_results = formatted_results[:num_results]
            logging.info(f"Returning {len(formatted_results)} final results")
            
            return QueryResponse(
                results=formatted_results,
                has_results=len(formatted_results) > 0
            )
            
        except Exception as e:
            logging.error(f"Error querying documents: {str(e)}")
            logging.exception("Full traceback:")
            raise

    async def get_context_for_prompt(
        self, 
        prompt: str, 
        num_results: int = 3,
        min_similarity: float = 0.1
    ) -> str:
        """Get relevant context from the vector database for a given prompt"""
        try:
            # Search for relevant documents
            results = await self.query_documents(
                query=prompt,
                num_results=num_results,
                min_similarity=min_similarity
            )
            
            if not results:
                logging.info("No relevant context found")
                return ""
            
            # Format context
            context_parts = []
            for i, result in enumerate(results, 1):
                similarity = result["metadata"]["similarity"]
                context_parts.append(
                    f"[Context {i} (similarity: {similarity:.2f})]: {result['text']}"
                )
            
            # Combine all context
            context = "\n\n".join(context_parts)
            logging.info(f"Found {len(results)} relevant context pieces")
            
            return context
            
        except Exception as e:
            logging.error(f"Error getting context: {str(e)}")
            logging.exception("Full traceback:")
            return ""