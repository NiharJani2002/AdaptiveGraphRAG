"""
AdaptiveGraphRAG Configuration Module
Centralized configuration for all components
"""

import os
from dataclasses import dataclass, field
from typing import Dict, List, Optional
from dotenv import load_dotenv

load_dotenv()


@dataclass
class Neo4jConfig:
    """Neo4j Database Configuration"""
    uri: str = os.getenv("NEO4J_URI", "bolt://localhost:7687")
    username: str = os.getenv("NEO4J_USERNAME", "neo4j")
    password: str = os.getenv("NEO4J_PASSWORD", "password")
    database: str = os.getenv("NEO4J_DATABASE", "neo4j")


@dataclass
class EmbeddingConfig:
    """Embedding Model Configuration"""
    model_name: str = "sentence-transformers/all-MiniLM-L6-v2"
    embedding_dim: int = 384
    device: str = "cpu"  # or "cuda" for GPU
    cache_embeddings: bool = True


@dataclass
class LLMConfig:
    """Large Language Model Configuration"""
    provider: str = "ollama"  # "ollama", "openai", etc.
    model_name: str = "mistral"  # For Ollama
    temperature: float = 0.7
    max_tokens: int = 1024
    top_p: float = 0.9
    streaming: bool = True


@dataclass
class RetrieverConfig:
    """Retriever Configuration"""
    vector_search_top_k: int = 5
    graph_traversal_hops: int = 3
    logical_filter_threshold: float = 0.7
    hybrid_weights: Dict[str, float] = field(default_factory=lambda: {
        "vector": 0.4,
        "graph": 0.3,
        "logical": 0.3
    })


@dataclass
class AdaptiveMetaGraphConfig:
    """Adaptive Meta-Graph Configuration"""
    # Learning rates
    positive_weight_delta: float = 0.15
    negative_weight_delta: float = -0.10
    initial_edge_weight: float = 1.0
    
    # Decay
    recency_decay_factor: float = 0.95
    time_window_days: int = 30
    
    # Relationship discovery
    latent_relation_confidence_threshold: float = 0.7
    auto_approve_high_confidence: bool = True
    
    # Routing
    min_historical_queries: int = 5  # Min queries before routing optimization
    routing_update_frequency: int = 10  # Update routing every N queries
    

@dataclass
class FastAPIConfig:
    """FastAPI Server Configuration"""
    host: str = os.getenv("API_HOST", "0.0.0.0")
    port: int = int(os.getenv("API_PORT", "8000"))
    debug: bool = os.getenv("DEBUG", "False") == "True"
    reload: bool = os.getenv("RELOAD", "False") == "True"


@dataclass
class MonitoringConfig:
    """Monitoring and Logging Configuration"""
    log_level: str = os.getenv("LOG_LEVEL", "INFO")
    prometheus_port: int = int(os.getenv("PROMETHEUS_PORT", "8001"))
    enable_metrics: bool = True
    metrics_update_interval: int = 60  # seconds


class AdaptiveGraphRAGConfig:
    """Master Configuration Class"""
    
    def __init__(self):
        self.neo4j = Neo4jConfig()
        self.embedding = EmbeddingConfig()
        self.llm = LLMConfig()
        self.retriever = RetrieverConfig()
        self.adaptive_meta = AdaptiveMetaGraphConfig()
        self.api = FastAPIConfig()
        self.monitoring = MonitoringConfig()
    
    def to_dict(self) -> Dict:
        """Convert configuration to dictionary"""
        return {
            "neo4j": vars(self.neo4j),
            "embedding": vars(self.embedding),
            "llm": vars(self.llm),
            "retriever": vars(self.retriever),
            "adaptive_meta": vars(self.adaptive_meta),
            "api": vars(self.api),
            "monitoring": vars(self.monitoring),
        }


# Global config instance
config = AdaptiveGraphRAGConfig()