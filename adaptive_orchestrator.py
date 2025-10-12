"""
AdaptiveGraphRAG Main Orchestrator
Coordinates all components for end-to-end functionality
"""

import logging
from typing import List, Dict, Optional, Tuple
from datetime import datetime
import time

from models import (
    AdaptiveMetaGraph, QuerySignature, RetrievalOutcome,
    RAGResponse, RetrievalMethod
)
from config import config
from retrieval_outcome_tracker import get_rot
from graph_edge_reweighting import get_gere
from latent_relationship_discovery import get_lrd
from meta_query_router import get_mqr
from embeddings_manager import get_embeddings_manager
from neo4j_manager import get_neo4j_manager

logger = logging.getLogger(__name__)


class AdaptiveGraphRAGOrchestrator:
    """Main orchestrator for AdaptiveGraphRAG system"""
    
    def __init__(self):
        """Initialize orchestrator and all components"""
        self.meta_graph = AdaptiveMetaGraph()
        
        # Initialize all components
        self.rot = get_rot()
        self.gere = get_gere(self.meta_graph)
        self.lrd = get_lrd(self.meta_graph)
        self.mqr = get_mqr(self.meta_graph)
        self.embeddings = get_embeddings_manager(self.meta_graph)
        self.neo4j = get_neo4j_manager()
        
        logger.info("Initialized AdaptiveGraphRAG Orchestrator")
    
    def process_query(
        self,
        query_text: str,
        user_id: Optional[str] = None
    ) -> RAGResponse:
        """
        Process a query end-to-end
        
        Args:
            query_text: User query
            user_id: Optional user ID for tracking
            
        Returns:
            RAGResponse object
        """
        start_time = time.time()
        
        # 1. Create query signature
        query_signature = self._create_query_signature(query_text)
        
        # 2. Classify and route
        best_method, ensemble_weights = self.mqr.get_optimal_routing(
            query_signature
        )
        
        # 3. Execute retrieval
        response = self._execute_retrieval(
            query_signature,
            best_method,
            ensemble_weights
        )
        
        # 4. Update adaptive components
        self._update_adaptive_components(response, query_signature)
        
        # 5. Calculate metrics
        execution_time_ms = (time.time() - start_time) * 1000
        response.execution_time_ms = execution_time_ms
        
        logger.info(
            f"Processed query in {execution_time_ms:.1f}ms | "
            f"Method: {best_method.value} | "
            f"Confidence: {response.confidence_score:.2%}"
        )
        
        return response
    
    def _create_query_signature(self, query_text: str) -> QuerySignature:
        """Create signature for a query"""
        embedding = self.embeddings.embed_text(query_text)
        query_type = self.mqr.classify_query(query_text)
        
        signature = QuerySignature(
            query_text=query_text,
            embedding=embedding,
            query_type=query_type.value
        )
        
        self.meta_graph.query_signatures[signature.query_id] = signature
        
        return signature
    
    def _execute_retrieval(
        self,
        query_signature: QuerySignature,
        primary_method: RetrievalMethod,
        ensemble_weights: Dict[RetrievalMethod, float]
    ) -> RAGResponse:
        """
        Execute retrieval using specified method(s)
        
        Args:
            query_signature: Query signature
            primary_method: Primary retrieval method
            ensemble_weights: Weights for ensemble methods
            
        Returns:
            RAGResponse object
        """
        response = RAGResponse(
            query=query_signature.query_text,
            retrieval_method_used=primary_method
        )
        
        # Execute retrieval based on selected method
        if primary_method == RetrievalMethod.VECTOR_SEARCH:
            response = self._vector_search(query_signature, response)
        elif primary_method == RetrievalMethod.GRAPH_TRAVERSAL:
            response = self._graph_traversal(query_signature, response)
        elif primary_method == RetrievalMethod.LOGICAL_FILTERING:
            response = self._logical_filtering(query_signature, response)
        elif primary_method == RetrievalMethod.HYBRID:
            # Execute multiple methods and ensemble
            vector_response = self._vector_search(
                query_signature,
                RAGResponse(query=query_signature.query_text)
            )
            graph_response = self._graph_traversal(
                query_signature,
                RAGResponse(query=query_signature.query_text)
            )
            
            # Ensemble results
            response = self._ensemble_responses(
                [vector_response, graph_response],
                ensemble_weights
            )
        
        return response
    
    def _vector_search(
        self,
        query_signature: QuerySignature,
        response: RAGResponse
    ) -> RAGResponse:
        """Execute vector similarity search"""
        # Placeholder for actual implementation
        response.answer = "Vector search result placeholder"
        response.confidence_score = 0.8
        response.methods_tried.append("vector_search")
        
        logger.debug("Executed vector search retrieval")
        return response
    
    def _graph_traversal(
        self,
        query_signature: QuerySignature,
        response: RAGResponse
    ) -> RAGResponse:
        """Execute graph traversal retrieval"""
        # Placeholder for actual implementation
        response.answer = "Graph traversal result placeholder"
        response.confidence_score = 0.75
        response.methods_tried.append("graph_traversal")
        
        logger.debug("Executed graph traversal retrieval")
        return response
    
    def _logical_filtering(
        self,
        query_signature: QuerySignature,
        response: RAGResponse
    ) -> RAGResponse:
        """Execute logical filtering retrieval"""
        # Placeholder for actual implementation
        response.answer = "Logical filtering result placeholder"
        response.confidence_score = 0.7
        response.methods_tried.append("logical_filtering")
        
        logger.debug("Executed logical filtering retrieval")
        return response
    
    def _ensemble_responses(
        self,
        responses: List[RAGResponse],
        weights: Dict[RetrievalMethod, float]
    ) -> RAGResponse:
        """Ensemble multiple retrieval responses"""
        ensemble_response = responses[0]
        
        # Average confidence scores
        avg_confidence = sum(
            r.confidence_score * weights.get(r.retrieval_method_used, 0.33)
            for r in responses
        )
        ensemble_response.confidence_score = avg_confidence
        
        # Combine methods tried
        ensemble_response.methods_tried = list(
            set().union(*(r.methods_tried for r in responses))
        )
        
        logger.debug(
            f"Ensembled {len(responses)} responses "
            f"with avg confidence {avg_confidence:.2%}"
        )
        
        return ensemble_response
    
    def _update_adaptive_components(
        self,
        response: RAGResponse,
        query_signature: QuerySignature
    ):
        """Update all adaptive components based on retrieval outcome"""
        # Record outcome
        outcome = self.rot.record_outcome(
            query_signature=query_signature,
            retrieval_method=response.retrieval_method_used,
            success=response.confidence_score > 0.5,
            confidence_score=response.confidence_score,
            reasoning_validity=0.8,  # Would be calculated from reasoning
            embedding_coherence=0.75,  # Would be calculated
            retrieved_nodes=response.source_nodes,
            retrieved_edges=response.source_edges,
            execution_time_ms=response.execution_time_ms
        )
        
        # Update meta-graph
        self.meta_graph.query_outcomes.append(outcome)
        
        # Update routing effectiveness
        query_type = query_signature.query_type
        success = outcome.composite_success_score() > 0.5
        self.mqr.update_method_effectiveness(
            response.retrieval_method_used,
            query_type,
            success,
            response.execution_time_ms
        )
        
        # Update edge weights
        path_edges = response.source_edges
        if path_edges:
            self.gere.update_edges_from_outcome(
                outcome,
                response.source_nodes,
                path_edges
            )
        
        # Discover latent relationships
        if success and response.reasoning_chain:
            self.lrd.discover_from_reasoning_chain(
                outcome,
                response.reasoning_chain
            )
    
    def get_system_status(self) -> Dict:
        """Get system status and statistics"""
        return {
            "timestamp": datetime.now().isoformat(),
            "meta_graph": {
                "query_outcomes": len(self.meta_graph.query_outcomes),
                "query_signatures": len(self.meta_graph.query_signatures),
                "edge_weights": len(self.meta_graph.edge_weights),
                "latent_relations": len(self.meta_graph.latent_relations),
            },
            "rot": self.rot.get_performance_summary(),
            "gere": self.gere.get_statistics(),
            "lrd": self.lrd.get_statistics(),
            "mqr": self.mqr.get_statistics(),
            "embeddings": self.embeddings.get_cache_stats(),
            "neo4j": self.neo4j.get_statistics(),
        }
    
    def save_state(self, filepath: str):
        """Save orchestrator state"""
        self.rot.export_outcomes(filepath)
        logger.info(f"Saved orchestrator state to {filepath}")
    
    def cleanup(self):
        """Cleanup resources"""
        self.neo4j.close()
        logger.info("Cleaned up AdaptiveGraphRAG resources")


# Global instance
orchestrator_instance: Optional[AdaptiveGraphRAGOrchestrator] = None


def get_orchestrator() -> AdaptiveGraphRAGOrchestrator:
    """Get or create orchestrator instance"""
    global orchestrator_instance
    if orchestrator_instance is None:
        orchestrator_instance = AdaptiveGraphRAGOrchestrator()
    return orchestrator_instance