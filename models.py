"""
Data Models and Structures for AdaptiveGraphRAG
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime
from enum import Enum
import uuid


class RetrievalMethod(str, Enum):
    """Enumeration of retrieval methods"""
    VECTOR_SEARCH = "vector_search"
    GRAPH_TRAVERSAL = "graph_traversal"
    LOGICAL_FILTERING = "logical_filtering"
    HYBRID = "hybrid"


class RelationshipType(str, Enum):
    """Enumeration of relationship types in the graph"""
    EXPLICIT = "explicit"
    IMPLICIT = "implicit"
    INFERRED = "inferred"


@dataclass
class QuerySignature:
    """Represents a query's semantic signature"""
    query_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    query_text: str = ""
    embedding: List[float] = field(default_factory=list)
    query_type: str = ""  # e.g., "semantic", "structured", "multi-hop"
    created_at: datetime = field(default_factory=datetime.now)
    
    def __hash__(self):
        return hash(self.query_id)


@dataclass
class RetrievalOutcome:
    """Records the outcome of a retrieval operation"""
    outcome_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    query_signature: QuerySignature = field(default_factory=QuerySignature)
    retrieval_method: RetrievalMethod = RetrievalMethod.HYBRID
    
    # Success metrics
    success: bool = False
    confidence_score: float = 0.0
    reasoning_validity: float = 0.0
    embedding_coherence: float = 0.0
    
    # Retrieved items
    retrieved_nodes: List[str] = field(default_factory=list)
    retrieved_edges: List[Tuple[str, str, str]] = field(default_factory=list)
    
    # Timing
    execution_time_ms: float = 0.0
    created_at: datetime = field(default_factory=datetime.now)
    
    def composite_success_score(self) -> float:
        """Calculate composite success score"""
        weights = {
            "success": 0.4,
            "confidence": 0.3,
            "reasoning_validity": 0.2,
            "embedding_coherence": 0.1
        }
        
        score = (
            (1.0 if self.success else 0.0) * weights["success"] +
            self.confidence_score * weights["confidence"] +
            self.reasoning_validity * weights["reasoning_validity"] +
            self.embedding_coherence * weights["embedding_coherence"]
        )
        return max(0.0, min(1.0, score))


@dataclass
class GraphEdgeWeight:
    """Represents weighted edges in the adaptive meta-graph"""
    source_id: str = ""
    target_id: str = ""
    relationship_type: str = ""
    
    weight: float = 1.0
    initial_weight: float = 1.0
    
    # Tracking
    successes: int = 0
    failures: int = 0
    last_used: datetime = field(default_factory=datetime.now)
    
    # Statistics
    average_success_score: float = 0.0
    usage_count: int = 0
    
    def update_weight(self, delta: float):
        """Update edge weight with a delta"""
        self.weight = max(0.1, min(10.0, self.weight + delta))
        self.last_used = datetime.now()
    
    def get_effectiveness_ratio(self) -> float:
        """Calculate success/total ratio"""
        total = self.successes + self.failures
        if total == 0:
            return 0.5  # Neutral starting point
        return self.successes / total


@dataclass
class LatentRelationship:
    """Discovered implicit relationship between entities"""
    relation_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    source_entity: str = ""
    target_entity: str = ""
    relationship_type: str = ""
    
    confidence_score: float = 0.0
    reasoning_chain: List[str] = field(default_factory=list)
    
    # Status
    status: str = "pending"  # pending, approved, rejected, active
    discovered_at: datetime = field(default_factory=datetime.now)
    approved_at: Optional[datetime] = None
    
    def is_approved(self) -> bool:
        return self.status == "approved" or self.status == "active"


@dataclass
class MethodEffectiveness:
    """Tracks effectiveness of each retrieval method"""
    method: RetrievalMethod = RetrievalMethod.VECTOR_SEARCH
    query_type_signature: str = ""
    
    success_rate: float = 0.5
    average_execution_time_ms: float = 0.0
    total_uses: int = 0
    successful_uses: int = 0
    
    # Confidence in this metric
    confidence: float = 0.0  # Based on sample size
    
    def update(self, success: bool, execution_time_ms: float):
        """Update effectiveness metrics"""
        self.total_uses += 1
        if success:
            self.successful_uses += 1
        
        # Exponential moving average for time
        if self.average_execution_time_ms == 0:
            self.average_execution_time_ms = execution_time_ms
        else:
            self.average_execution_time_ms = (
                0.8 * self.average_execution_time_ms + 
                0.2 * execution_time_ms
            )
        
        # Update success rate
        self.success_rate = self.successful_uses / self.total_uses
        
        # Update confidence (sigmoid based on sample size)
        self.confidence = 1.0 - (1.0 / (1.0 + self.total_uses * 0.1))
    
    def is_reliable(self, min_samples: int = 5) -> bool:
        """Check if method is reliable enough for routing"""
        return self.total_uses >= min_samples and self.confidence > 0.5


@dataclass
class AdaptiveMetaGraph:
    """Core adaptive meta-graph data structure"""
    graph_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    
    # Query tracking
    query_outcomes: List[RetrievalOutcome] = field(default_factory=list)
    query_signatures: Dict[str, QuerySignature] = field(default_factory=dict)
    
    # Graph adaptation
    edge_weights: Dict[Tuple[str, str, str], GraphEdgeWeight] = field(default_factory=dict)
    
    # Method tracking
    method_effectiveness: Dict[str, MethodEffectiveness] = field(default_factory=dict)
    
    # Relationship discovery
    latent_relations: Dict[str, LatentRelationship] = field(default_factory=dict)
    
    # Embedding cache
    embedding_cache: Dict[str, List[float]] = field(default_factory=dict)
    
    # Metadata
    created_at: datetime = field(default_factory=datetime.now)
    last_updated: datetime = field(default_factory=datetime.now)
    version: int = 1
    
    def get_best_retrieval_method(self, query_type: str) -> RetrievalMethod:
        """Determine best retrieval method for query type"""
        best_method = RetrievalMethod.VECTOR_SEARCH
        best_score = -1.0
        
        for method_name, method_stat in self.method_effectiveness.items():
            if method_stat.query_type_signature == query_type:
                if method_stat.is_reliable() and method_stat.success_rate > best_score:
                    best_method = method_stat.method
                    best_score = method_stat.success_rate
        
        return best_method
    
    def get_routing_weights(self, query_type: str) -> Dict[RetrievalMethod, float]:
        """Get adaptive routing weights for ensemble retrieval"""
        weights = {
            RetrievalMethod.VECTOR_SEARCH: 0.33,
            RetrievalMethod.GRAPH_TRAVERSAL: 0.33,
            RetrievalMethod.LOGICAL_FILTERING: 0.34,
        }
        
        # Override with learned weights if available
        for method_name, method_stat in self.method_effectiveness.items():
            if method_stat.query_type_signature == query_type:
                if method_stat.is_reliable():
                    for method_enum in RetrievalMethod:
                        if method_enum.value == method_name:
                            # Weight by success rate and confidence
                            weights[method_enum] = (
                                method_stat.success_rate * method_stat.confidence
                            )
        
        # Normalize weights
        total = sum(weights.values())
        if total > 0:
            weights = {k: v/total for k, v in weights.items()}
        
        return weights


@dataclass
class RAGResponse:
    """Response structure for RAG queries"""
    query: str = ""
    answer: str = ""
    
    # Source information
    source_nodes: List[str] = field(default_factory=list)
    source_edges: List[Tuple[str, str, str]] = field(default_factory=list)
    reasoning_chain: List[str] = field(default_factory=list)
    
    # Metadata
    retrieval_method_used: RetrievalMethod = RetrievalMethod.HYBRID
    confidence_score: float = 0.0
    execution_time_ms: float = 0.0
    
    # Adaptive metadata
    methods_tried: List[str] = field(default_factory=list)
    adaptive_insights: Dict[str, Any] = field(default_factory=dict)