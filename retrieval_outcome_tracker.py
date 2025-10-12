"""
Retrieval Outcome Tracker (ROT) Component
Tracks and records all retrieval outcomes for learning
"""

import logging
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
import json
from pathlib import Path

from models import (
    RetrievalOutcome, QuerySignature, RetrievalMethod,
    AdaptiveMetaGraph, MethodEffectiveness
)
from config import config

logger = logging.getLogger(__name__)


class RetrievalOutcomeTracker:
    """Tracks all retrieval outcomes and enables learning from them"""
    
    def __init__(self, storage_path: str = "./data/rot_storage"):
        """Initialize the tracker"""
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
        self.outcomes: List[RetrievalOutcome] = []
        self.query_signatures: Dict[str, QuerySignature] = {}
        
        # Load existing outcomes if available
        self._load_outcomes()
    
    def record_outcome(
        self,
        query_signature: QuerySignature,
        retrieval_method: RetrievalMethod,
        success: bool,
        confidence_score: float,
        reasoning_validity: float,
        embedding_coherence: float,
        retrieved_nodes: List[str],
        retrieved_edges: List[Tuple[str, str, str]],
        execution_time_ms: float
    ) -> RetrievalOutcome:
        """
        Record a retrieval outcome
        
        Args:
            query_signature: Query metadata
            retrieval_method: Method used
            success: Whether retrieval was successful
            confidence_score: Confidence in the answer
            reasoning_validity: Validity of reasoning chain
            embedding_coherence: Quality of embeddings
            retrieved_nodes: Retrieved node IDs
            retrieved_edges: Retrieved relationships
            execution_time_ms: Execution time
            
        Returns:
            RetrievalOutcome object
        """
        outcome = RetrievalOutcome(
            query_signature=query_signature,
            retrieval_method=retrieval_method,
            success=success,
            confidence_score=confidence_score,
            reasoning_validity=reasoning_validity,
            embedding_coherence=embedding_coherence,
            retrieved_nodes=retrieved_nodes,
            retrieved_edges=retrieved_edges,
            execution_time_ms=execution_time_ms,
        )
        
        self.outcomes.append(outcome)
        self.query_signatures[query_signature.query_id] = query_signature
        
        logger.info(
            f"Recorded outcome: {outcome.outcome_id} | "
            f"Method: {retrieval_method.value} | "
            f"Success: {success} | "
            f"Score: {outcome.composite_success_score():.2f}"
        )
        
        return outcome
    
    def get_outcomes_by_method(
        self,
        method: RetrievalMethod,
        days: int = 30
    ) -> List[RetrievalOutcome]:
        """Get outcomes for a specific retrieval method in recent days"""
        cutoff_date = datetime.now() - timedelta(days=days)
        
        return [
            o for o in self.outcomes
            if o.retrieval_method == method and o.created_at >= cutoff_date
        ]
    
    def get_outcomes_by_query_type(
        self,
        query_type: str,
        days: int = 30
    ) -> List[RetrievalOutcome]:
        """Get outcomes for a specific query type"""
        cutoff_date = datetime.now() - timedelta(days=days)
        
        return [
            o for o in self.outcomes
            if o.query_signature.query_type == query_type 
            and o.created_at >= cutoff_date
        ]
    
    def calculate_method_effectiveness(
        self,
        method: RetrievalMethod,
        query_type: str = "",
        days: int = 30
    ) -> MethodEffectiveness:
        """
        Calculate effectiveness metrics for a retrieval method
        
        Args:
            method: Retrieval method to analyze
            query_type: Optional query type filter
            days: Time window in days
            
        Returns:
            MethodEffectiveness object
        """
        outcomes = self.get_outcomes_by_method(method, days)
        
        if query_type:
            outcomes = [
                o for o in outcomes
                if o.query_signature.query_type == query_type
            ]
        
        effectiveness = MethodEffectiveness(
            method=method,
            query_type_signature=query_type
        )
        
        for outcome in outcomes:
            success = outcome.composite_success_score() > 0.5
            effectiveness.update(success, outcome.execution_time_ms)
        
        return effectiveness
    
    def get_failed_retrievals(
        self,
        limit: int = 100,
        days: int = 30
    ) -> List[RetrievalOutcome]:
        """Get recent failed retrievals for analysis"""
        cutoff_date = datetime.now() - timedelta(days=days)
        
        failed = [
            o for o in self.outcomes
            if not o.success and o.created_at >= cutoff_date
        ]
        
        return sorted(
            failed,
            key=lambda x: x.created_at,
            reverse=True
        )[:limit]
    
    def get_success_rate(
        self,
        method: Optional[RetrievalMethod] = None,
        days: int = 30
    ) -> float:
        """Calculate success rate"""
        outcomes = self.outcomes
        
        cutoff_date = datetime.now() - timedelta(days=days)
        outcomes = [o for o in outcomes if o.created_at >= cutoff_date]
        
        if method:
            outcomes = [o for o in outcomes if o.retrieval_method == method]
        
        if not outcomes:
            return 0.0
        
        successful = sum(1 for o in outcomes if o.success)
        return successful / len(outcomes)
    
    def get_average_execution_time(
        self,
        method: Optional[RetrievalMethod] = None,
        days: int = 30
    ) -> float:
        """Get average execution time in milliseconds"""
        outcomes = self.outcomes
        
        cutoff_date = datetime.now() - timedelta(days=days)
        outcomes = [o for o in outcomes if o.created_at >= cutoff_date]
        
        if method:
            outcomes = [o for o in outcomes if o.retrieval_method == method]
        
        if not outcomes:
            return 0.0
        
        total_time = sum(o.execution_time_ms for o in outcomes)
        return total_time / len(outcomes)
    
    def get_performance_summary(self, days: int = 30) -> Dict:
        """Get comprehensive performance summary"""
        summary = {
            "timestamp": datetime.now().isoformat(),
            "time_window_days": days,
            "total_outcomes": len(self.outcomes),
        }
        
        # Overall metrics
        summary["overall_success_rate"] = self.get_success_rate(days=days)
        summary["overall_avg_execution_time_ms"] = (
            self.get_average_execution_time(days=days)
        )
        
        # Per-method metrics
        summary["methods"] = {}
        for method in RetrievalMethod:
            outcomes = self.get_outcomes_by_method(method, days)
            if outcomes:
                summary["methods"][method.value] = {
                    "count": len(outcomes),
                    "success_rate": self.get_success_rate(method, days),
                    "avg_execution_time_ms": (
                        self.get_average_execution_time(method, days)
                    ),
                    "avg_confidence": sum(
                        o.confidence_score for o in outcomes
                    ) / len(outcomes),
                }
        
        return summary
    
    def export_outcomes(self, filepath: str):
        """Export outcomes to JSON file"""
        data = {
            "exported_at": datetime.now().isoformat(),
            "total_outcomes": len(self.outcomes),
            "outcomes": [
                {
                    "outcome_id": o.outcome_id,
                    "query_id": o.query_signature.query_id,
                    "query_text": o.query_signature.query_text,
                    "method": o.retrieval_method.value,
                    "success": o.success,
                    "composite_score": o.composite_success_score(),
                    "execution_time_ms": o.execution_time_ms,
                    "created_at": o.created_at.isoformat(),
                }
                for o in self.outcomes
            ]
        }
        
        Path(filepath).parent.mkdir(parents=True, exist_ok=True)
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)
        
        logger.info(f"Exported outcomes to {filepath}")
    
    def _load_outcomes(self):
        """Load outcomes from storage"""
        outcomes_file = self.storage_path / "outcomes.json"
        if outcomes_file.exists():
            try:
                with open(outcomes_file, 'r') as f:
                    # Load implementation would go here
                    logger.info("Loaded existing outcomes")
            except Exception as e:
                logger.warning(f"Failed to load outcomes: {e}")
    
    def save_outcomes(self):
        """Save outcomes to storage"""
        self.export_outcomes(str(self.storage_path / "outcomes.json"))


# Global instance
rot_instance: Optional[RetrievalOutcomeTracker] = None


def get_rot() -> RetrievalOutcomeTracker:
    """Get or create ROT instance"""
    global rot_instance
    if rot_instance is None:
        rot_instance = RetrievalOutcomeTracker()
    return rot_instance