"""
Complete Integration Examples for AdaptiveGraphRAG
Shows how to integrate with existing systems
"""

import logging
from typing import List, Dict, Optional, Tuple
from datetime import datetime
import json
from abc import ABC, abstractmethod

from adaptive_orchestrator import get_orchestrator
from models import RetrievalMethod, QuerySignature

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# ==================== EXAMPLE 1: Basic Integration ====================

class BasicRAGIntegration:
    """Simple integration for basic use cases"""
    
    def __init__(self):
        """Initialize"""
        self.orchestrator = get_orchestrator()
    
    def ask(self, question: str) -> str:
        """Ask a question and get answer"""
        response = self.orchestrator.process_query(question)
        return response.answer
    
    def ask_with_metadata(self, question: str) -> Dict:
        """Ask a question and get full metadata"""
        response = self.orchestrator.process_query(question)
        
        return {
            "query": question,
            "answer": response.answer,
            "confidence": response.confidence_score,
            "method": response.retrieval_method_used.value,
            "execution_time_ms": response.execution_time_ms,
            "source_nodes": response.source_nodes,
            "source_edges": response.source_edges,
        }


# ==================== EXAMPLE 2: Batch Processing ====================

class BatchProcessingIntegration:
    """Integration for batch query processing"""
    
    def __init__(self, batch_size: int = 10):
        """Initialize with batch size"""
        self.orchestrator = get_orchestrator()
        self.batch_size = batch_size
    
    def process_queries(
        self,
        queries: List[str],
        user_id: Optional[str] = None
    ) -> List[Dict]:
        """Process multiple queries"""
        results = []
        
        for i, query in enumerate(queries):
            try:
                logger.info(
                    f"Processing query {i+1}/{len(queries)}: {query[:50]}..."
                )
                
                response = self.orchestrator.process_query(
                    query,
                    user_id
                )
                
                results.append({
                    "query": query,
                    "answer": response.answer,
                    "confidence": response.confidence_score,
                    "status": "success",
                    "execution_time_ms": response.execution_time_ms,
                })
            
            except Exception as e:
                logger.error(f"Failed to process query: {e}")
                results.append({
                    "query": query,
                    "answer": None,
                    "confidence": 0.0,
                    "status": "failed",
                    "error": str(e),
                })
        
        return results
    
    def export_results(
        self,
        results: List[Dict],
        filepath: str
    ):
        """Export results to JSON"""
        with open(filepath, 'w') as f:
            json.dump(results, f, indent=2)
        
        logger.info(f"Exported {len(results)} results to {filepath}")


# ==================== EXAMPLE 3: Performance Monitoring ====================

class PerformanceMonitoringIntegration:
    """Integration for monitoring and analytics"""
    
    def __init__(self):
        """Initialize"""
        self.orchestrator = get_orchestrator()
        self.metrics = {
            "total_queries": 0,
            "successful_queries": 0,
            "total_execution_time_ms": 0,
            "method_stats": {},
        }
    
    def process_and_monitor(
        self,
        query: str,
        user_id: Optional[str] = None
    ) -> Dict:
        """Process query and collect metrics"""
        response = self.orchestrator.process_query(query, user_id)
        
        # Update metrics
        self.metrics["total_queries"] += 1
        
        if response.confidence_score > 0.5:
            self.metrics["successful_queries"] += 1
        
        self.metrics["total_execution_time_ms"] += (
            response.execution_time_ms
        )
        
        # Track method stats
        method = response.retrieval_method_used.value
        if method not in self.metrics["method_stats"]:
            self.metrics["method_stats"][method] = {
                "count": 0,
                "success_count": 0,
                "total_time_ms": 0,
            }
        
        method_stats = self.metrics["method_stats"][method]
        method_stats["count"] += 1
        method_stats["total_time_ms"] += response.execution_time_ms
        
        if response.confidence_score > 0.5:
            method_stats["success_count"] += 1
        
        return {
            **self.metrics,
            "current_response": {
                "query": query,
                "answer": response.answer,
                "confidence": response.confidence_score,
                "method": method,
                "execution_time_ms": response.execution_time_ms,
            }
        }
    
    def get_performance_report(self) -> Dict:
        """Generate performance report"""
        total_queries = self.metrics["total_queries"]
        
        if total_queries == 0:
            return {"status": "no_data"}
        
        avg_time = (
            self.metrics["total_execution_time_ms"] / total_queries
        )
        success_rate = (
            self.metrics["successful_queries"] / total_queries
        )
        
        method_reports = {}
        for method, stats in self.metrics["method_stats"].items():
            method_reports[method] = {
                "count": stats["count"],
                "success_rate": (
                    stats["success_count"] / stats["count"]
                    if stats["count"] > 0 else 0
                ),
                "avg_execution_time_ms": (
                    stats["total_time_ms"] / stats["count"]
                    if stats["count"] > 0 else 0
                ),
            }
        
        return {
            "total_queries": total_queries,
            "success_rate": success_rate,
            "avg_execution_time_ms": avg_time,
            "method_reports": method_reports,
            "timestamp": datetime.now().isoformat(),
        }
    
    def print_report(self):
        """Print formatted performance report"""
        report = self.get_performance_report()
        
        if report["status"] == "no_data":
            logger.info("No performance data yet")
            return
        
        print("\n" + "=" * 80)
        print("PERFORMANCE REPORT")
        print("=" * 80)
        print(f"Total queries: {report['total_queries']}")
        print(f"Success rate: {report['success_rate']:.1%}")
        print(f"Avg execution time: {report['avg_execution_time_ms']:.1f}ms")
        
        print("\nMethod Breakdown:")
        print("-" * 80)
        for method, metrics in report["method_reports"].items():
            print(f"\n{method}:")
            print(f"  Count: {metrics['count']}")
            print(f"  Success rate: {metrics['success_rate']:.1%}")
            print(
                f"  Avg time: {metrics['avg_execution_time_ms']:.1f}ms"
            )


# ==================== EXAMPLE 4: Custom Callback Integration ====================

class CallbackIntegration:
    """Integration with custom callbacks for events"""
    
    def __init__(self):
        """Initialize"""
        self.orchestrator = get_orchestrator()
        self.callbacks = {
            "on_query_start": [],
            "on_query_complete": [],
            "on_relationship_discovered": [],
            "on_routing_change": [],
        }
    
    def register_callback(
        self,
        event: str,
        callback
    ):
        """Register callback for event"""
        if event in self.callbacks:
            self.callbacks[event].append(callback)
            logger.info(f"Registered callback for {event}")
    
    def process_with_callbacks(
        self,
        query: str,
        user_id: Optional[str] = None
    ) -> Dict:
        """Process query with callbacks"""
        # Trigger on_query_start
        for callback in self.callbacks["on_query_start"]:
            callback({"query": query, "user_id": user_id})
        
        # Process query
        response = self.orchestrator.process_query(query, user_id)
        
        # Trigger on_query_complete
        for callback in self.callbacks["on_query_complete"]:
            callback({
                "query": query,
                "answer": response.answer,
                "confidence": response.confidence_score,
                "method": response.retrieval_method_used.value,
            })
        
        # Check for new relationships
        pending = self.orchestrator.lrd.get_pending_relationships()
        if pending:
            for callback in self.callbacks["on_relationship_discovered"]:
                callback({
                    "relationships": [
                        {
                            "source": r.source_entity,
                            "target": r.target_entity,
                            "type": r.relationship_type,
                            "confidence": r.confidence_score,
                        }
                        for r in pending
                    ]
                })
        
        return {
            "query": query,
            "answer": response.answer,
            "confidence": response.confidence_score,
            "method": response.retrieval_method_used.value,
        }


# ==================== EXAMPLE 5: Database Integration ====================

class DatabaseIntegration:
    """Integration with external databases"""
    
    def __init__(self):
        """Initialize"""
        self.orchestrator = get_orchestrator()
    
    def store_query_result(
        self,
        db_connection,
        query: str,
        user_id: str,
        result_table: str = "rag_results"
    ):
        """Store query result in database"""
        response = self.orchestrator.process_query(query, user_id)
        
        sql = f"""
            INSERT INTO {result_table}
            (user_id, query, answer, confidence, method, execution_time_ms, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """
        
        try:
            db_connection.execute(
                sql,
                (
                    user_id,
                    query,
                    response.answer,
                    response.confidence_score,
                    response.retrieval_method_used.value,
                    response.execution_time_ms,
                    datetime.now(),
                )
            )
            db_connection.commit()
            
            logger.info(f"Stored result for user {user_id}")
        
        except Exception as e:
            logger.error(f"Failed to store result: {e}")
            db_connection.rollback()
    
    def get_user_query_history(
        self,
        db_connection,
        user_id: str,
        limit: int = 10,
        table: str = "rag_results"
    ) -> List[Dict]:
        """Retrieve user's query history"""
        sql = f"""
            SELECT query, answer, confidence, method, execution_time_ms, created_at
            FROM {table}
            WHERE user_id = ?
            ORDER BY created_at DESC
            LIMIT ?
        """
        
        try:
            cursor = db_connection.execute(sql, (user_id, limit))
            columns = [description[0] for description in cursor.description]
            
            results = []
            for row in cursor.fetchall():
                results.append(dict(zip(columns, row)))
            
            return results
        
        except Exception as e:
            logger.error(f"Failed to retrieve history: {e}")
            return []


# ==================== EXAMPLE 6: FastAPI Middleware Integration ====================

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware


class RAGMetricsMiddleware(BaseHTTPMiddleware):
    """FastAPI middleware for tracking RAG metrics"""
    
    async def dispatch(self, request: Request, call_next) -> Response:
        """Track metrics for each request"""
        if request.url.path == "/query":
            # Track time
            import time
            start_time = time.time()
            
            response = await call_next(request)
            
            process_time = (time.time() - start_time) * 1000
            
            # Add metrics header
            response.headers["X-Process-Time"] = str(process_time)
            
            logger.info(
                f"Query processed in {process_time:.1f}ms"
            )
            
            return response
        
        return await call_next(request)


# ==================== EXAMPLE 7: Chain of Thought Integration ====================

class ChainOfThoughtIntegration:
    """Integration for chain-of-thought reasoning"""
    
    def __init__(self):
        """Initialize"""
        self.orchestrator = get_orchestrator()
    
    def process_with_reasoning(
        self,
        query: str
    ) -> Dict:
        """Process query with detailed reasoning"""
        response = self.orchestrator.process_query(query)
        
        reasoning_steps = [
            f"1. Query Classification: {self.orchestrator.mqr.classify_query(query).value}",
            f"2. Retrieval Method: {response.retrieval_method_used.value}",
            f"3. Source Nodes: {len(response.source_nodes)} entities retrieved",
            f"4. Source Edges: {len(response.source_edges)} relationships found",
            f"5. Confidence Score: {response.confidence_score:.1%}",
            f"6. Execution Time: {response.execution_time_ms:.1f}ms",
        ]
        
        return {
            "query": query,
            "answer": response.answer,
            "confidence": response.confidence_score,
            "reasoning_steps": reasoning_steps,
            "sources": {
                "nodes": response.source_nodes,
                "edges": response.source_edges,
            },
            "metadata": {
                "method": response.retrieval_method_used.value,
                "execution_time_ms": response.execution_time_ms,
                "methods_tried": response.methods_tried,
            }
        }


# ==================== DEMO: Usage Examples ====================

def demo_basic_integration():
    """Demo: Basic integration"""
    logger.info("\n=== BASIC INTEGRATION DEMO ===")
    
    rag = BasicRAGIntegration()
    
    query = "What is machine learning?"
    answer = rag.ask(query)
    print(f"Q: {query}")
    print(f"A: {answer}\n")
    
    result = rag.ask_with_metadata(query)
    print(f"Confidence: {result['confidence']:.1%}")
    print(f"Method: {result['method']}")
    print(f"Time: {result['execution_time_ms']:.1f}ms\n")


def demo_batch_processing():
    """Demo: Batch processing"""
    logger.info("\n=== BATCH PROCESSING DEMO ===")
    
    batch = BatchProcessingIntegration()
    
    queries = [
        "What is deep learning?",
        "Explain neural networks",
        "Tell me about transformers",
    ]
    
    results = batch.process_queries(queries, user_id="user_123")
    
    successful = sum(1 for r in results if r["status"] == "success")
    print(f"Processed {len(results)} queries")
    print(f"Successful: {successful}/{len(results)}")
    
    batch.export_results(results, "batch_results.json")


def demo_performance_monitoring():
    """Demo: Performance monitoring"""
    logger.info("\n=== PERFORMANCE MONITORING DEMO ===")
    
    monitor = PerformanceMonitoringIntegration()
    
    queries = [
        "What is AI?",
        "Explain machine learning",
        "What is deep learning?",
    ]
    
    for query in queries:
        monitor.process_and_monitor(query)
    
    monitor.print_report()


def demo_chain_of_thought():
    """Demo: Chain of thought"""
    logger.info("\n=== CHAIN OF THOUGHT DEMO ===")
    
    cot = ChainOfThoughtIntegration()
    
    result = cot.process_with_reasoning(
        "How does machine learning relate to artificial intelligence?"
    )
    
    print(f"Query: {result['query']}")
    print(f"Answer: {result['answer']}")
    print(f"\nReasoning Steps:")
    for step in result['reasoning_steps']:
        print(f"  {step}")


if __name__ == "__main__":
    # Run all demos
    demo_basic_integration()
    demo_batch_processing()
    demo_performance_monitoring()
    demo_chain_of_thought()
    
    logger.info("\n" + "=" * 80)
    logger.info("All integration examples completed successfully!")
    logger.info("=" * 80)