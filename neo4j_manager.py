"""
Neo4j Database Manager Component
Handles all Neo4j graph database operations
"""

import logging
from typing import List, Dict, Optional, Tuple, Any
from datetime import datetime

from neo4j import GraphDatabase, Session, Transaction
from neo4j.exceptions import Neo4jError

from config import config
from models import LatentRelationship, GraphEdgeWeight

logger = logging.getLogger(__name__)


class Neo4jManager:
    """Manages Neo4j database operations"""
    
    def __init__(self):
        """Initialize Neo4j manager"""
        self.cfg = config.neo4j
        
        # Create driver
        self.driver = GraphDatabase.driver(
            self.cfg.uri,
            auth=(self.cfg.username, self.cfg.password)
        )
        
        # Test connection
        try:
            with self.driver.session(database=self.cfg.database) as session:
                result = session.run("RETURN 1")
                logger.info("Successfully connected to Neo4j database")
        except Neo4jError as e:
            logger.error(f"Failed to connect to Neo4j: {e}")
            raise
    
    def close(self):
        """Close database connection"""
        if self.driver:
            self.driver.close()
            logger.info("Closed Neo4j connection")
    
    def create_node(
        self,
        label: str,
        properties: Dict[str, Any]
    ) -> str:
        """
        Create a node in the graph
        
        Args:
            label: Node label
            properties: Node properties
            
        Returns:
            Node ID
        """
        with self.driver.session(database=self.cfg.database) as session:
            query = f"""
                CREATE (n:{label} $props)
                SET n.created_at = datetime()
                RETURN id(n) as node_id
            """
            
            result = session.run(query, props=properties)
            record = result.single()
            
            if record:
                node_id = str(record["node_id"])
                logger.debug(f"Created node {node_id} with label {label}")
                return node_id
        
        return ""
    
    def create_relationship(
        self,
        source_id: str,
        target_id: str,
        relation_type: str,
        properties: Optional[Dict[str, Any]] = None
    ):
        """
        Create a relationship between nodes
        
        Args:
            source_id: Source node ID
            target_id: Target node ID
            relation_type: Relationship type
            properties: Relationship properties
        """
        if properties is None:
            properties = {}
        
        with self.driver.session(database=self.cfg.database) as session:
            query = f"""
                MATCH (s) WHERE id(s) = $source_id
                MATCH (t) WHERE id(t) = $target_id
                CREATE (s)-[r:{relation_type} $props]->(t)
                SET r.created_at = datetime()
                RETURN r
            """
            
            try:
                session.run(
                    query,
                    source_id=int(source_id),
                    target_id=int(target_id),
                    props=properties
                )
                logger.debug(
                    f"Created relationship {relation_type} "
                    f"from {source_id} to {target_id}"
                )
            except Neo4jError as e:
                logger.error(f"Failed to create relationship: {e}")
    
    def add_latent_relationship(
        self,
        relationship: LatentRelationship
    ):
        """
        Add a discovered latent relationship to the graph
        
        Args:
            relationship: LatentRelationship object
        """
        if relationship.status not in ["approved", "active"]:
            logger.debug(
                f"Skipping {relationship.status} relationship: "
                f"{relationship.source_entity}-"
                f"[{relationship.relationship_type}]->"
                f"{relationship.target_entity}"
            )
            return
        
        with self.driver.session(database=self.cfg.database) as session:
            query = """
                MATCH (s:Entity {name: $source})
                MATCH (t:Entity {name: $target})
                CREATE (s)-[r:LATENT_RELATIONSHIP {
                    type: $rel_type,
                    confidence: $confidence,
                    discovered_at: datetime(),
                    status: $status
                }]->(t)
                RETURN r
            """
            
            try:
                session.run(
                    query,
                    source=relationship.source_entity,
                    target=relationship.target_entity,
                    rel_type=relationship.relationship_type,
                    confidence=relationship.confidence_score,
                    status=relationship.status
                )
                logger.info(
                    f"Added latent relationship to Neo4j: "
                    f"{relationship.source_entity}-"
                    f"[{relationship.relationship_type}]->"
                    f"{relationship.target_entity}"
                )
            except Neo4jError as e:
                logger.warning(f"Failed to add latent relationship: {e}")
    
    def update_edge_weight(
        self,
        source_entity: str,
        target_entity: str,
        relation_type: str,
        weight: float
    ):
        """
        Update relationship weight in the graph
        
        Args:
            source_entity: Source entity name
            target_entity: Target entity name
            relation_type: Relationship type
            weight: New weight value
        """
        with self.driver.session(database=self.cfg.database) as session:
            query = f"""
                MATCH (s:Entity {{name: $source}})-
                      [r:{relation_type} {{type: $rel_type}}]->
                      (t:Entity {{name: $target}})
                SET r.weight = $weight, r.updated_at = datetime()
                RETURN r
            """
            
            try:
                result = session.run(
                    query,
                    source=source_entity,
                    target=target_entity,
                    rel_type=relation_type,
                    weight=weight
                )
                
                if result.single():
                    logger.debug(
                        f"Updated weight for {source_entity}-"
                        f"[{relation_type}]->{target_entity} to {weight}"
                    )
            except Neo4jError as e:
                logger.debug(f"Failed to update edge weight: {e}")
    
    def get_entity_neighbors(
        self,
        entity_name: str,
        hops: int = 2
    ) -> List[Dict[str, Any]]:
        """
        Get neighbors of an entity
        
        Args:
            entity_name: Entity name
            hops: Number of hops
            
        Returns:
            List of neighboring entities
        """
        with self.driver.session(database=self.cfg.database) as session:
            query = f"""
                MATCH (e:Entity {{name: $name}})-[*1..{hops}]-(neighbor)
                RETURN DISTINCT neighbor.name as name,
                       labels(neighbor) as labels,
                       neighbor.embedding_id as embedding_id
                LIMIT 100
            """
            
            try:
                result = session.run(query, name=entity_name)
                return [dict(record) for record in result]
            except Neo4jError as e:
                logger.warning(f"Failed to get entity neighbors: {e}")
                return []
    
    def search_by_property(
        self,
        label: str,
        property_name: str,
        property_value: Any
    ) -> List[Dict[str, Any]]:
        """
        Search nodes by property
        
        Args:
            label: Node label
            property_name: Property name
            property_value: Property value
            
        Returns:
            List of matching nodes
        """
        with self.driver.session(database=self.cfg.database) as session:
            query = f"""
                MATCH (n:{label} {{{property_name}: $value}})
                RETURN properties(n) as props, id(n) as node_id
                LIMIT 50
            """
            
            try:
                result = session.run(
                    query,
                    value=property_value
                )
                return [dict(record) for record in result]
            except Neo4jError as e:
                logger.warning(
                    f"Failed to search by property: {e}"
                )
                return []
    
    def get_highest_weighted_paths(
        self,
        source_entity: str,
        target_entity: str,
        limit: int = 5
    ) -> List[List[Dict[str, Any]]]:
        """
        Find highest weighted paths between entities
        
        Args:
            source_entity: Source entity
            target_entity: Target entity
            limit: Max paths to return
            
        Returns:
            List of paths
        """
        with self.driver.session(database=self.cfg.database) as session:
            query = """
                MATCH (s:Entity {name: $source}),
                      (t:Entity {name: $target})
                CALL apoc.algo.dijkstra(s, t, 'weight', 5)
                YIELD path, weight
                RETURN path, weight
                ORDER BY weight DESC
                LIMIT $limit
            """
            
            try:
                result = session.run(
                    query,
                    source=source_entity,
                    target=target_entity,
                    limit=limit
                )
                paths = []
                for record in result:
                    paths.append({
                        "path": str(record["path"]),
                        "weight": record["weight"]
                    })
                return paths
            except Neo4jError as e:
                logger.warning(
                    f"Failed to get weighted paths: {e}"
                )
                return []
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get database statistics"""
        with self.driver.session(database=self.cfg.database) as session:
            # Get node counts
            node_query = "MATCH (n) RETURN count(n) as count"
            node_result = session.run(node_query).single()
            node_count = node_result["count"] if node_result else 0
            
            # Get relationship counts
            rel_query = "MATCH ()-[r]->() RETURN count(r) as count"
            rel_result = session.run(rel_query).single()
            rel_count = rel_result["count"] if rel_result else 0
            
            return {
                "nodes": node_count,
                "relationships": rel_count,
                "database": self.cfg.database,
            }


# Global instance
neo4j_instance: Optional[Neo4jManager] = None


def get_neo4j_manager() -> Neo4jManager:
    """Get or create Neo4j manager instance"""
    global neo4j_instance
    if neo4j_instance is None:
        neo4j_instance = Neo4jManager()
    return neo4j_instance