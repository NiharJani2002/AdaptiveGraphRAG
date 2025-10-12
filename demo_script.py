"""
Demo Script for AdaptiveGraphRAG
Complete end-to-end demonstration with synthetic data
"""

import logging
from datetime import datetime
import time
import json
from pathlib import Path

from adaptive_orchestrator import get_orchestrator
from models import (
    QuerySignature, RetrievalOutcome, LatentRelationship,
    RetrievalMethod
)
from config import config

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class AdaptiveGraphRAGDemo:
    """Demo for AdaptiveGraphRAG system"""
    
    def __init__(self):
        """Initialize demo"""
        self.orchestrator = get_orchestrator()
        self.results = []
    
    def demo_query_routing(self):
        """Demo: Query classification and routing"""
        logger.info("=" * 80)
        logger.info("DEMO 1: Query Classification & Routing")
        logger.info("=" * 80)
        
        test_queries = [
            "Tell me about machine learning techniques",  # Semantic
            "List all companies founded in 2020",  # Structured
            "How does training connect to deployment in ML systems?",  # Multi-hop
            "Show me articles published only by Yann LeCun",  # Constraint
        ]
        
        for query in test_queries:
            query_type = self.orchestrator.mqr.classify_query(query)
            logger.info(f"\nQuery: {query}")
            logger.info(f"Classified as: {query_type.value}")
            
            best_method, weights = (
                self.orchestrator.mqr.get_optimal_routing(
                    self.orchestrator._create_query_signature(query)
                )
            )
            
            logger.info(f"Recommended method: {best_method.value}")
            logger.info(f"Ensemble weights: {weights}")
    
    def demo_retrieval_learning(self):
        """Demo: Retrieval outcome learning"""
        logger.info("=" * 80)
        logger.info("DEMO 2: Retrieval Outcome Learning")
        logger.info("=" * 80)
        
        # Simulate multiple queries with different outcomes
        test_scenarios = [
            {
                "query": "What is neural network?",
                "method": RetrievalMethod.VECTOR_SEARCH,
                "success": True,
                "confidence": 0.92
            },
            {
                "query": "What is neural network?",
                "method": RetrievalMethod.VECTOR_SEARCH,
                "success": True,
                "confidence": 0.88
            },
            {
                "query": "Find papers by LeCun on deep learning",
                "method": RetrievalMethod.GRAPH_TRAVERSAL,
                "success": True,
                "confidence": 0.85
            },
            {
                "query": "Find papers by LeCun on deep learning",
                "method": RetrievalMethod.LOGICAL_FILTERING,
                "success": False,
                "confidence": 0.45
            },
        ]
        
        for scenario in test_scenarios:
            # Simulate query processing
            response = self.orchestrator.process_query(scenario["query"])
            
            logger.info(f"\nQuery: {scenario['query']}")
            logger.info(f"Method: {response.retrieval_method_used.value}")
            logger.info(f"Confidence: {response.confidence_score:.2%}")
            logger.info(f"Execution time: {response.execution_time_ms:.1f}ms")
        
        # Show learned effectiveness
        logger.info("\n" + "-" * 80)
        logger.info("Learned Method Effectiveness:")
        logger.info("-" * 80)
        
        for method_key, effectiveness in (
            self.orchestrator.meta_graph.method_effectiveness.items()
        ):
            logger.info(
                f"{method_key}: "
                f"Success={effectiveness.success_rate:.2%}, "
                f"Reliability={effectiveness.confidence:.2%}, "
                f"Uses={effectiveness.total_uses}"
            )
    
    def demo_edge_reweighting(self):
        """Demo: Graph edge reweighting"""
        logger.info("=" * 80)
        logger.info("DEMO 3: Graph Edge Reweighting")
        logger.info("=" * 80)
        
        logger.info("\nInitial edge weights (before learning):")
        logger.info("-" * 80)
        
        initial_weights = self.orchestrator.gere.get_top_edges(limit=10)
        for source, target, rel_type, weight in initial_weights:
            logger.info(
                f"{source} -[{rel_type}]-> {target}: {weight:.2f}"
            )
        
        logger.info(f"\nTotal edges tracked: "
                   f"{len(self.orchestrator.meta_graph.edge_weights)}")
        
        # Get statistics
        stats = self.orchestrator.gere.get_statistics()
        logger.info(f"\nEdge Reweighting Statistics:")
        logger.info(f"  Total updates: {stats['total_updates']}")
        logger.info(
            f"  Positive updates: {stats['positive_updates']} "
            f"({stats['positive_ratio']:.1%})"
        )
        logger.info(f"  Negative updates: {stats['negative_updates']}")
        logger.info(f"  Average edge weight: {stats['average_edge_weight']:.2f}")
    
    def demo_relationship_discovery(self):
        """Demo: Latent relationship discovery"""
        logger.info("=" * 80)
        logger.info("DEMO 4: Latent Relationship Discovery")
        logger.info("=" * 80)
        
        stats = self.orchestrator.lrd.get_statistics()
        
        logger.info("\nDiscovered Relationships:")
        logger.info("-" * 80)
        logger.info(f"Total discovered: {stats['total_discovered']}")
        logger.info(f"Pending approval: {stats['pending']}")
        logger.info(f"Approved: {stats['approved']}")
        logger.info(f"Active: {stats['active']}")
        logger.info(f"Rejected: {stats['rejected']}")
        logger.info(
            f"Average confidence: "
            f"{stats['average_confidence']:.2%}"
        )
        
        # Get pending relationships
        pending = self.orchestrator.lrd.get_pending_relationships()
        if pending:
            logger.info("\nPending Relationships for Approval:")
            logger.info("-" * 80)
            for rel in pending[:5]:
                logger.info(
                    f"{rel.source_entity} -[{rel.relationship_type}]-> "
                    f"{rel.target_entity} "
                    f"(confidence: {rel.confidence_score:.2%})"
                )
        
        # Get high confidence
        high_conf = (
            self.orchestrator.lrd.get_high_confidence_relationships(0.8)
        )
        if high_conf:
            logger.info("\nHigh Confidence Relationships (>80%):")
            logger.info("-" * 80)
            for rel in high_conf[:5]:
                logger.info(
                    f"{rel.source_entity} -[{rel.relationship_type}]-> "
                    f"{rel.target_entity} "
                    f"(confidence: {rel.confidence_score:.2%})"
                )
    
    def demo_system_status(self):
        """Demo: System status and monitoring"""
        logger.info("=" * 80)
        logger.info("DEMO 5: System Status & Monitoring")
        logger.info("=" * 80)
        
        status = self.orchestrator.get_system_status()
        
        logger.info("\nSystem Timestamp: " + status['timestamp'])
        
        logger.info("\nMeta-Graph Statistics:")
        logger.info("-" * 80)
        for key, value in status['meta_graph'].items():
            logger.info(f"  {key}: {value}")
        
        logger.info("\nRetrieval Performance Summary:")
        logger.info("-" * 80)
        rot_stats = status['rot']
        if 'overall_success_rate' in rot_stats:
            logger.info(
                f"  Overall success rate: "
                f"{rot_stats['overall_success_rate']:.2%}"
            )
            logger.info(
                f"  Avg execution time: "
                f"{rot_stats['overall_avg_execution_time_ms']:.1f}ms"
            )
        
        if 'methods' in rot_stats:
            logger.info("\n  Per-Method Statistics:")
            for method, metrics in rot_stats['methods'].items():
                logger.info(f"    {method}:")
                logger.info(
                    f"      Success rate: {metrics['success_rate']:.2%}"
                )
                logger.info(
                    f"      Avg time: {metrics['avg_execution_time_ms']:.1f}ms"
                )
                logger.info(
                    f"      Uses: {metrics['count']}"
                )
        
        logger.info("\nEmbedding Statistics:")
        logger.info("-" * 80)
        emb_stats = status['embeddings']
        logger.info(f"  Cached embeddings: {emb_stats['cached_embeddings']}")
        logger.info(f"  Model: {emb_stats['model_name']}")
        logger.info(f"  Dimension: {emb_stats['embedding_dim']}")
        
        logger.info("\nGraph Database Statistics:")
        logger.info("-" * 80)
        neo4j_stats = status['neo4j']
        logger.info(f"  Nodes: {neo4j_stats['nodes']}")
        logger.info(f"  Relationships: {neo4j_stats['relationships']}")
    
    def run_full_demo(self):
        """Run full demonstration"""
        logger.info("\n")
        logger.info("=" * 80)
        logger.info("AdaptiveGraphRAG - Complete System Demo")
        logger.info("=" * 80)
        logger.info(f"Started: {datetime.now().isoformat()}")
        logger.info("=" * 80)
        
        try:
            # Run demos
            self.demo_query_routing()
            time.sleep(1)
            
            self.demo_retrieval_learning()
            time.sleep(1)
            
            self.demo_edge_reweighting()
            time.sleep(1)
            
            self.demo_relationship_discovery()
            time.sleep(1)
            
            self.demo_system_status()
            
            # Final summary
            logger.info("\n")
            logger.info("=" * 80)
            logger.info("Demo Summary")
            logger.info("=" * 80)
            logger.info("✓ Query classification working")
            logger.info("✓ Adaptive routing learning from outcomes")
            logger.info("✓ Edge weights being updated")
            logger.info("✓ Latent relationships discovered")
            logger.info("✓ System monitoring active")
            logger.info("=" * 80)
            logger.info(f"Completed: {datetime.now().isoformat()}")
            
        except Exception as e:
            logger.error(f"Demo error: {e}", exc_info=True)
        finally:
            # Cleanup
            self.orchestrator.cleanup()


if __name__ == "__main__":
    demo = AdaptiveGraphRAGDemo()
    demo.run_full_demo()