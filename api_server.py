"""
FastAPI Server for AdaptiveGraphRAG
REST API endpoints for the system
"""

import logging
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Optional
import uvicorn

from config import config
from adaptive_orchestrator import get_orchestrator
from models import RetrievalMethod

# Configure logging
logging.basicConfig(
    level=config.monitoring.log_level,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="AdaptiveGraphRAG API",
    description="Self-Evolving Knowledge Graph Intelligence",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize orchestrator
orchestrator = get_orchestrator()


# ==================== Request/Response Models ====================

class QueryRequest(BaseModel):
    """Query request model"""
    query: str
    user_id: Optional[str] = None


class QueryResponse(BaseModel):
    """Query response model"""
    query: str
    answer: str
    confidence_score: float
    retrieval_method: str
    execution_time_ms: float
    source_nodes: List[str]
    methods_tried: List[str]


class SystemStatusResponse(BaseModel):
    """System status response"""
    timestamp: str
    meta_graph: Dict
    rot: Dict
    gere: Dict
    lrd: Dict
    mqr: Dict
    embeddings: Dict
    neo4j: Dict


class HealthResponse(BaseModel):
    """Health check response"""
    status: str
    timestamp: str


class RoutingRecommendation(BaseModel):
    """Routing recommendation"""
    method: str
    query_type: str
    success_rate: float
    avg_time_ms: float
    reliability: float
    is_reliable: bool


class RelationshipResponse(BaseModel):
    """Relationship response"""
    source_entity: str
    target_entity: str
    relationship_type: str
    confidence_score: float
    status: str


# ==================== API Endpoints ====================

@app.post("/query", response_model=QueryResponse)
async def process_query(request: QueryRequest):
    """
    Process a query and get adaptive routing response
    
    Args:
        request: QueryRequest with query text
        
    Returns:
        QueryResponse with answer and metadata
    """
    try:
        if not request.query or len(request.query.strip()) == 0:
            raise HTTPException(
                status_code=400,
                detail="Query cannot be empty"
            )
        
        # Process query
        response = orchestrator.process_query(
            request.query,
            request.user_id
        )
        
        return QueryResponse(
            query=response.query,
            answer=response.answer,
            confidence_score=response.confidence_score,
            retrieval_method=response.retrieval_method_used.value,
            execution_time_ms=response.execution_time_ms,
            source_nodes=response.source_nodes,
            methods_tried=response.methods_tried
        )
    
    except Exception as e:
        logger.error(f"Error processing query: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/status", response_model=SystemStatusResponse)
async def get_status():
    """
    Get system status and statistics
    
    Returns:
        SystemStatusResponse with all metrics
    """
    try:
        status = orchestrator.get_system_status()
        return SystemStatusResponse(**status)
    except Exception as e:
        logger.error(f"Error getting status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    from datetime import datetime
    return HealthResponse(
        status="healthy",
        timestamp=datetime.now().isoformat()
    )


@app.get("/routing/recommendations", response_model=Dict[str, RoutingRecommendation])
async def get_routing_recommendations():
    """Get routing performance recommendations"""
    try:
        recommendations = orchestrator.mqr.get_routing_recommendations()
        return {
            k: RoutingRecommendation(**v)
            for k, v in recommendations.items()
        }
    except Exception as e:
        logger.error(f"Error getting recommendations: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/relationships/pending", response_model=List[RelationshipResponse])
async def get_pending_relationships():
    """Get pending relationship approvals"""
    try:
        pending = orchestrator.lrd.get_pending_relationships()
        return [
            RelationshipResponse(
                source_entity=r.source_entity,
                target_entity=r.target_entity,
                relationship_type=r.relationship_type,
                confidence_score=r.confidence_score,
                status=r.status
            )
            for r in pending
        ]
    except Exception as e:
        logger.error(f"Error getting pending relationships: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/relationships/approve/{relationship_id}")
async def approve_relationship(relationship_id: str):
    """Approve a discovered relationship"""
    try:
        orchestrator.lrd.approve_relationships([relationship_id])
        return {
            "status": "approved",
            "relationship_id": relationship_id
        }
    except Exception as e:
        logger.error(f"Error approving relationship: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/relationships/high-confidence")
async def get_high_confidence_relationships(threshold: float = 0.8):
    """Get high-confidence discovered relationships"""
    try:
        relationships = (
            orchestrator.lrd.get_high_confidence_relationships(threshold)
        )
        return [
            {
                "source": r.source_entity,
                "target": r.target_entity,
                "type": r.relationship_type,
                "confidence": r.confidence_score
            }
            for r in relationships
        ]
    except Exception as e:
        logger.error(f"Error getting relationships: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/relationships/auto-activate")
async def auto_activate_relationships(threshold: float = 0.8):
    """Auto-activate high-confidence relationships"""
    try:
        activated_count = (
            orchestrator.lrd.auto_activate_high_confidence(threshold)
        )
        return {
            "status": "success",
            "activated": activated_count
        }
    except Exception as e:
        logger.error(f"Error activating relationships: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/graph/statistics")
async def get_graph_statistics():
    """Get graph database statistics"""
    try:
        stats = orchestrator.neo4j.get_statistics()
        return stats
    except Exception as e:
        logger.error(f"Error getting graph stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/performance/summary")
async def get_performance_summary(days: int = 30):
    """Get performance summary"""
    try:
        summary = orchestrator.rot.get_performance_summary(days)
        return summary
    except Exception as e:
        logger.error(f"Error getting performance: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/edge-weights/top")
async def get_top_edges(limit: int = 50):
    """Get top weighted edges in the graph"""
    try:
        edges = orchestrator.gere.get_top_edges(limit)
        return [
            {
                "source": source,
                "target": target,
                "type": rel_type,
                "weight": weight
            }
            for source, target, rel_type, weight in edges
        ]
    except Exception as e:
        logger.error(f"Error getting top edges: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/cache/clear")
async def clear_embeddings_cache():
    """Clear embeddings cache"""
    try:
        orchestrator.embeddings.clear_cache()
        return {"status": "success", "message": "Cache cleared"}
    except Exception as e:
        logger.error(f"Error clearing cache: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/save-state/{filepath}")
async def save_state(filepath: str):
    """Save orchestrator state"""
    try:
        orchestrator.save_state(filepath)
        return {"status": "success", "filepath": filepath}
    except Exception as e:
        logger.error(f"Error saving state: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    orchestrator.cleanup()
    logger.info("Server shutdown")


# ==================== Main ====================

if __name__ == "__main__":
    logger.info(
        f"Starting AdaptiveGraphRAG API on "
        f"{config.api.host}:{config.api.port}"
    )
    
    uvicorn.run(
        app,
        host=config.api.host,
        port=config.api.port,
        debug=config.api.debug,
        reload=config.api.reload,
        log_level=config.monitoring.log_level.lower()
    )