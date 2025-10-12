"""
Meta-Agent Query Router (MQR) Component
Routes queries to optimal retrieval strategies based on learning
"""

import logging
from typing import Dict, List, Tuple, Optional
from enum import Enum
import hashlib

from models import (
    QuerySignature, RetrievalMethod, AdaptiveMetaGraph,
    MethodEffectiveness
)
from config import config

logger = logging.getLogger(__name__)


class QueryType(str, Enum):
    """Query type classification"""
    SEMANTIC = "semantic"
    STRUCTURED = "structured"
    MULTI_HOP = "multi_hop"
    CONSTRAINT = "constraint"
    HYBRID = "hybrid"


class MetaAgentQueryRouter:
    """Routes queries to optimal retrieval strategies"""
    
    def __init__(self, meta_graph: AdaptiveMetaGraph):
        """
        Initialize MQR
        
        Args:
            meta_graph: The adaptive meta-graph
        """
        self.meta_graph = meta_graph
        self.cfg = config.retriever
        
        # Query type patterns
        self.query_patterns = {
            QueryType.SEMANTIC: [
                "what", "how", "why", "describe", "explain",
                "tell me", "find", "search", "similar"
            ],
            QueryType.STRUCTURED: [
                "who", "where", "when", "list", "count",
                "filter", "select", "by", "with"
            ],
            QueryType.MULTI_HOP: [
                "relationship", "connect", "path", "between",
                "through", "via", "across", "chain"
            ],
            QueryType.CONSTRAINT: [
                "only", "exactly", "must", "should", "cannot",
                "not", "exclude", "restriction", "rule"
            ],
        }
        
        # Statistics
        self.routing_decisions = []
    
    def classify_query(self, query_text: str) -> QueryType:
        """
        Classify query into type
        
        Args:
            query_text: The query text
            
        Returns:
            QueryType classification
        """
        query_lower = query_text.lower()
        scores = {qt: 0.0 for qt in QueryType}
        
        for query_type, patterns in self.query_patterns.items():
            for pattern in patterns:
                if pattern in query_lower:
                    scores[query_type] += 1.0
        
        # Normalize scores
        total = sum(scores.values())
        if total > 0:
            scores = {k: v/total for k, v in scores.items()}
        else:
            scores[QueryType.SEMANTIC] = 1.0
        
        # Return highest score
        return max(scores.keys(), key=lambda x: scores[x])
    
    def get_query_signature_hash(self, query_signature: QuerySignature) -> str:
        """
        Create hash of query signature for routing stats
        
        Args:
            query_signature: Query signature
            
        Returns:
            Hash string
        """
        # Use query type as key
        query_type = self.classify_query(query_signature.query_text)
        return f"{query_type.value}"
    
    def should_optimize_routing(self) -> bool:
        """
        Check if enough data exists for routing optimization
        
        Returns:
            Whether routing should be optimized
        """
        min_queries = self.cfg.min_historical_queries
        
        # Count outcomes by method
        outcomes_by_method = {}
        for method in RetrievalMethod:
            count = sum(
                1 for o in self.meta_graph.query_outcomes
                if o.retrieval_method == method
            )
            outcomes_by_method[method] = count
        
        # Check if we have enough data
        min_count = min(outcomes_by_method.values())
        return min_count >= min_queries
    
    def get_optimal_routing(
        self,
        query_signature: QuerySignature
    ) -> Tuple[RetrievalMethod, Dict[RetrievalMethod, float]]:
        """
        Determine optimal routing for a query
        
        Args:
            query_signature: The query signature
            
        Returns:
            Tuple of (primary method, ensemble weights)
        """
        query_type = self.classify_query(query_signature.query_text)
        query_type_str = query_type.value
        
        # Get best method based on historical data
        if self.should_optimize_routing():
            # Calculate effectiveness for each method
            method_scores = {}
            
            for method in RetrievalMethod:
                effectiveness = self._get_method_effectiveness(
                    method, query_type_str
                )
                
                if effectiveness and effectiveness.is_reliable():
                    score = (
                        effectiveness.success_rate *
                        effectiveness.confidence
                    )
                else:
                    score = 0.5  # Default neutral score
                
                method_scores[method] = score
            
            # Normalize scores for ensemble
            total = sum(method_scores.values())
            ensemble_weights = (
                {k: v/total for k, v in method_scores.items()}
                if total > 0 else {m: 1/3 for m in RetrievalMethod}
            )
            
            # Pick best method
            best_method = max(
                method_scores.keys(),
                key=lambda x: method_scores[x]
            )
        else:
            # Insufficient data - use default routing
            best_method = RetrievalMethod.HYBRID
            ensemble_weights = {
                RetrievalMethod.VECTOR_SEARCH: 0.33,
                RetrievalMethod.GRAPH_TRAVERSAL: 0.33,
                RetrievalMethod.LOGICAL_FILTERING: 0.34,
            }
        
        # Record routing decision
        self.routing_decisions.append({
            "query_type": query_type_str,
            "selected_method": best_method.value,
            "weights": {k.value: v for k, v in ensemble_weights.items()},
        })
        
        return best_method, ensemble_weights
    
    def _get_method_effectiveness(
        self,
        method: RetrievalMethod,
        query_type: str
    ) -> Optional[MethodEffectiveness]:
        """Get effectiveness metric for method/query type combo"""
        method_key = f"{method.value}_{query_type}"
        
        if method_key in self.meta_graph.method_effectiveness:
            return self.meta_graph.method_effectiveness[method_key]
        
        return None
    
    def update_method_effectiveness(
        self,
        method: RetrievalMethod,
        query_type: str,
        success: bool,
        execution_time_ms: float
    ):
        """
        Update effectiveness tracking for a method
        
        Args:
            method: The retrieval method
            query_type: Query type classification
            success: Whether retrieval succeeded
            execution_time_ms: Execution time
        """
        method_key = f"{method.value}_{query_type}"
        
        if method_key not in self.meta_graph.method_effectiveness:
            self.meta_graph.method_effectiveness[method_key] = (
                MethodEffectiveness(
                    method=method,
                    query_type_signature=query_type
                )
            )
        
        effectiveness = self.meta_graph.method_effectiveness[method_key]
        effectiveness.update(success, execution_time_ms)
        
        logger.debug(
            f"Updated {method.value} effectiveness for {query_type}: "
            f"Success rate = {effectiveness.success_rate:.2%}, "
            f"Confidence = {effectiveness.confidence:.2%}"
        )
    
    def get_routing_recommendations(self) -> Dict:
        """Get routing performance recommendations"""
        recommendations = {}
        
        for method_key, effectiveness in (
            self.meta_graph.method_effectiveness.items()
        ):
            if effectiveness.total_uses > 0:
                recommendations[method_key] = {
                    "method": effectiveness.method.value,
                    "query_type": effectiveness.query_type_signature,
                    "success_rate": effectiveness.success_rate,
                    "avg_time_ms": effectiveness.average_execution_time_ms,
                    "reliability": effectiveness.confidence,
                    "is_reliable": effectiveness.is_reliable(),
                }
        
        return recommendations
    
    def get_statistics(self) -> Dict:
        """Get routing statistics"""
        return {
            "total_routing_decisions": len(self.routing_decisions),
            "methods_tracked": len(self.meta_graph.method_effectiveness),
            "recent_decisions": (
                self.routing_decisions[-10:]
                if len(self.routing_decisions) >= 10
                else self.routing_decisions
            ),
        }


# Global instance
mqr_instance: Optional[MetaAgentQueryRouter] = None


def get_mqr(meta_graph: AdaptiveMetaGraph) -> MetaAgentQueryRouter:
    """Get or create MQR instance"""
    global mqr_instance
    if mqr_instance is None:
        mqr_instance = MetaAgentQueryRouter(meta_graph)
    return mqr_instance