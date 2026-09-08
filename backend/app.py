"""
Main FastAPI Application

Orchestrates the three-layer Q&A system:
1. Rule engine (fast, exact matching)
2. Semantic retrieval (embedding-based)
3. LLM enhancement (when confidence is low)
"""
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, Dict, List
import time
import logging
from datetime import datetime

from config import settings, get_settings
from modules.rule_engine import RuleEngine
from modules.embedding_model import EmbeddingModel
from modules.retrieval import SemanticRetriever
from modules.llm_handler import LLMHandler
from modules.confidence import ConfidenceScorer
from modules.cache import QueryCache, CacheManager

# Setup logging
logging.basicConfig(level=settings.LOG_LEVEL)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Hybrid Q&A System with Rule + Small Model + LLM Layers"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============ Global Components ============
rule_engine: Optional[RuleEngine] = None
retriever: Optional[SemanticRetriever] = None
llm_handler: Optional[LLMHandler] = None
query_cache: Optional[QueryCache] = None
cache_manager: Optional[CacheManager] = None

# Statistics
stats = {
    'rule_layer_hits': 0,
    'small_model_hits': 0,
    'llm_layer_hits': 0,
    'cache_hits': 0,
    'total_queries': 0,
}


# ============ Request/Response Models ============
class QARequest(BaseModel):
    """Q&A request"""
    query: str
    include_confidence: bool = True
    include_sources: bool = True
    force_llm: bool = False


class QAResponse(BaseModel):
    """Q&A response"""
    answer: str
    layer: str  # "rule", "small_model", or "llm"
    confidence: float
    sources: List[str] = []
    processing_time_ms: float
    llm_used: bool = False
    metadata: Dict = {}


class FeedbackRequest(BaseModel):
    """Feedback on answer"""
    query: str
    answer: str
    rating: int  # 1-5
    comment: str = ""
    layer: str = ""


class DocumentRequest(BaseModel):
    """Add document to system"""
    doc_id: str
    content: str
    source: str = "user"


# ============ Initialization ============
@app.on_event("startup")
async def startup_event():
    """Initialize components on startup"""
    global rule_engine, retriever, llm_handler, query_cache, cache_manager
    
    logger.info("Initializing Doc QA Bot...")
    
    # Initialize cache
    cache_manager = CacheManager(settings.CACHE_BACKEND)
    query_cache = QueryCache(cache_manager)
    
    # Initialize Layer 1: Rule Engine
    if settings.RULE_ENABLE:
        rule_engine = RuleEngine()
        logger.info(f"Rule engine initialized: {rule_engine.get_stats()}")
    
    # Initialize Layer 2: Small Model
    if settings.SMALL_MODEL_ENABLE:
        embedding_model = EmbeddingModel()
        retriever = SemanticRetriever(embedding_model)
        logger.info(f"Retriever initialized: {retriever.get_stats()}")
    
    # Initialize Layer 3: LLM
    if settings.LLM_ENABLE:
        try:
            llm_handler = LLMHandler()
            logger.info("LLM handler initialized")
        except Exception as e:
            logger.warning(f"LLM initialization failed: {e}")
    
    logger.info("Doc QA Bot ready!")


# ============ Core Q&A Endpoint ============
@app.post(f"{settings.API_PREFIX}/qa", response_model=QAResponse)
async def answer_question(request: QARequest) -> QAResponse:
    """
    Main Q&A endpoint
    
    Routes query through:
    1. Rule engine (exact matching)
    2. Semantic retrieval (embedding-based)
    3. LLM (if confidence is low)
    """
    stats['total_queries'] += 1
    start_time = time.time()
    
    try:
        # Step 0: Check cache
        cached_answer = query_cache.get_answer(request.query)
        if cached_answer:
            stats['cache_hits'] += 1
            processing_time = (time.time() - start_time) * 1000
            return QAResponse(
                **cached_answer,
                processing_time_ms=processing_time
            )
        
        # Step 1: Rule Engine (Layer 1)
        answer, confidence, sources = None, 0.0, []
        
        if rule_engine:
            result = rule_engine.match(request.query)
            if result:
                answer, confidence, sources = result
                stats['rule_layer_hits'] += 1
                
                response = QAResponse(
                    answer=answer,
                    layer="rule",
                    confidence=confidence,
                    sources=sources if request.include_sources else [],
                    processing_time_ms=(time.time() - start_time) * 1000,
                    llm_used=False
                )
                
                # Cache result
                query_cache.set_answer(request.query, response.dict())
                return response
        
        # Step 2: Semantic Retrieval (Layer 2)
        if retriever:
            retrieved_docs = retriever.retrieve(request.query)
            
            if retrieved_docs:
                top_result = retrieved_docs[0]
                answer = top_result['content']
                confidence = top_result['similarity']
                sources = [top_result['source']] if top_result['source'] else ["document"]
                
                stats['small_model_hits'] += 1
                
                # Step 3: Check if LLM should be used
                use_llm = (
                    not request.force_llm and 
                    llm_handler and 
                    ConfidenceScorer.should_route_to_llm(confidence)
                )
                
                if use_llm:
                    # Use LLM to generate more contextual answer
                    context = "\n".join([doc['content'] for doc in retrieved_docs[:3]])
                    llm_result = llm_handler.generate_answer(
                        request.query,
                        context
                    )
                    
                    if not llm_result.get('error'):
                        answer = llm_result['answer']
                        confidence = 0.95  # LLM provides high confidence
                        stats['llm_layer_hits'] += 1
                        layer = "llm"
                        llm_used = True
                    else:
                        layer = "small_model"
                        llm_used = False
                else:
                    layer = "small_model"
                    llm_used = False
                
                response = QAResponse(
                    answer=answer,
                    layer=layer,
                    confidence=ConfidenceScorer.normalize_confidence(confidence),
                    sources=sources if request.include_sources else [],
                    processing_time_ms=(time.time() - start_time) * 1000,
                    llm_used=llm_used
                )
                
                # Cache result
                query_cache.set_answer(request.query, response.dict())
                return response
        
        # No answer found in any layer
        raise HTTPException(
            status_code=404,
            detail="Could not find answer in knowledge base"
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing query: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# ============ Document Management ============
@app.post(f"{settings.API_PREFIX}/documents")
async def add_document(request: DocumentRequest):
    """Add document to retriever"""
    if not retriever:
        raise HTTPException(status_code=503, detail="Retriever not initialized")
    
    try:
        retriever.add_document_and_index(
            request.doc_id,
            request.content,
            request.source
        )
        
        return {
            "status": "success",
            "message": f"Document '{request.doc_id}' added and indexed",
            "retriever_stats": retriever.get_stats()
        }
    except Exception as e:
        logger.error(f"Error adding document: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============ Feedback ============
@app.post(f"{settings.API_PREFIX}/feedback")
async def submit_feedback(request: FeedbackRequest, background_tasks: BackgroundTasks):
    """Submit feedback on answer"""
    try:
        # Log feedback
        feedback_data = {
            'timestamp': datetime.now().isoformat(),
            'query': request.query,
            'answer': request.answer,
            'rating': request.rating,
            'comment': request.comment,
            'layer': request.layer
        }
        
        logger.info(f"Feedback received: {feedback_data}")
        
        # TODO: Store feedback and use for model improvement
        
        return {
            "status": "success",
            "message": "Feedback recorded"
        }
    except Exception as e:
        logger.error(f"Error processing feedback: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============ Health & Statistics ============
@app.get(f"{settings.API_PREFIX}/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": settings.APP_VERSION
    }


@app.get(f"{settings.API_PREFIX}/stats")
async def get_stats():
    """Get system statistics"""
    return {
        "general": stats,
        "rule_engine": rule_engine.get_stats() if rule_engine else None,
        "retriever": retriever.get_stats() if retriever else None,
        "llm": llm_handler.get_stats() if llm_handler else None,
        "cache": query_cache.get_stats() if query_cache else None,
    }


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "docs": "/docs",
        "health": f"{settings.API_PREFIX}/health"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app,
        host=settings.API_HOST,
        port=settings.API_PORT,
        log_level=settings.LOG_LEVEL.lower()
    )
