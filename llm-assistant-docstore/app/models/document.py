from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from enum import Enum

class RelevanceLevel(str, Enum):
    HIGH = "high"          # Very relevant (similarity > 0.5)
    MEDIUM = "medium"      # Quite relevant (0.2 < similarity ≤ 0.5)
    LOW = "low"           # Somewhat relevant (0.1 < similarity ≤ 0.2)
    NOT_RELEVANT = "not_relevant"  # Not relevant enough (similarity ≤ 0.1)

class DocumentResponse(BaseModel):
    id: str
    filename: str

class QueryRequest(BaseModel):
    text: str
    num_results: int = 3
    min_relevance: Optional[RelevanceLevel] = None
    min_similarity: Optional[float] = None  # Add minimum similarity threshold

class QueryResultMetadata(BaseModel):
    filename: str
    doc_id: str
    chunk: int
    similarity: float
    relevance: RelevanceLevel

class QueryResult(BaseModel):
    text: str
    metadata: QueryResultMetadata
    is_relevant: bool

class QueryResponse(BaseModel):
    results: List[QueryResult]
    query_text: str
    total_results: int
    relevant_results: int