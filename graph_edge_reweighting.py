"""
Graph Edge Reweighting Engine (GERE) Component
Dynamically adjusts graph edge weights based on retrieval outcomes
"""

import logging
from typing import Dict, List, Tuple, Optional
from datetime import datetime, timedelta
import math

from models import (
    GraphEdgeWeight, RetrievalOutcome, AdaptiveMetaGraph,
    RetrievalMethod
)
from config import config

logger = logging.getLogger(__name__)


class GraphEdgeReweightingEngine:
    """Dynamically learns and optimizes graph edge weights"""
    
    def __init__(self, meta_graph: AdaptiveMetaGraph):
        """
        Initialize GERE
        
        Args:
            meta_graph: The adaptive meta-graph to manage
        """
        self.meta_graph = meta_graph
        self.cfg = config.adaptive_meta
        
        # Statistics for monitoring
        self.total_updates = 0
        self.positive_updates = 0
        self.negative_updates = 0
    
    def update_edges_from_outcome(
        self,
        outcome: RetrievalOutcome,
        path_nodes: List[str],
        path_edges: List[Tuple[str, str, str]]
    ):
        """
        Update edge weights based on a retrieval outcome
        
        Args:
            outcome: The retrieval outcome
            path_nodes: Nodes in the retrieval path
            path_edges: Edges used in the retrieval path
        """
        success_score = outcome.composite_success_score()
        
        if success_score > 0.5:
            # Successful retrieval - increase weights
            self._strengthen_path(path_edges, outcome)
        else:
            # Failed retrieval - decrease weights
            self._weaken_path(path_edges, outcome)
        
        self.meta_graph.last_updated = datetime.now()
    
    def _strengthen_path(
        self,
        path_edges: List[Tuple[str, str, str]],
        outcome: RetrievalOutcome
    ):
        """Increase weights along successful path"""
        success_score = outcome.composite_success_score()
        
        # Multi-hop bonus: deeper paths matter more
        hop_count = len(path_edges)
        hop_bonus = math.log10(hop_count + 1) * 0.05
        
        for source, target, relation_type in path_edges:
            edge_key = (source, target, relation_type)
            
            # Get or create edge weight
            if edge_key not in self.meta_graph.edge_weights:
                self.meta_graph.edge_weights[edge_key] = GraphEdgeWeight(
                    source_id=source,
                    target_id=target,
                    relationship_type=relation_type,
                    weight=self.cfg.initial_edge_weight,
                    initial_weight=self.cfg.initial_edge_weight,
                )
            
            edge = self.meta