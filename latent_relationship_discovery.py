"""
Latent Relationship Discovery (LRD) Component
Identifies implicit semantic relationships from successful retrievals
"""

import logging
from typing import List, Dict, Tuple, Optional, Set
from datetime import datetime
import re

from models import (
    LatentRelationship, AdaptiveMetaGraph, RetrievalOutcome
)
from config import config

logger = logging.getLogger(__name__)


class LatentRelationshipDiscovery:
    """Discovers implicit relationships between entities"""
    
    def __init__(self, meta_graph: AdaptiveMetaGraph):
        """
        Initialize LRD
        
        Args:
            meta_graph: The adaptive meta-graph
        """
        self.meta_graph = meta_graph
        self.cfg = config.adaptive_meta
        
        # Common relationship patterns
        self.relationship_patterns = {
            "part_of": r"(?:is part of|comprises|contains|includes)",
            "similar_to": r"(?:similar to|like|analogous to|resembles)",
            "causes": r"(?:causes|leads to|results in|triggers)",
            "related_to": r"(?:related to|associated with|connected to)",
            "parent_of": r"(?:parent|superclass|category of)",
            "child_of": r"(?:child|instance of|subclass of)",
            "collaborates_with": r"(?:works with|collaborates with|partners with)",
            "depends_on": r"(?:depends on|relies on|requires)",
            "influences": r"(?:influences|affects|impacts)",
            "opposite_of": r"(?:opposite of|opposite to|contrary to)",
        }
    
    def discover_from_reasoning_chain(
        self,
        outcome: RetrievalOutcome,
        reasoning_chain: List[str]
    ) -> List[LatentRelationship]:
        """
        Extract latent relationships from reasoning chain
        
        Args:
            outcome: The retrieval outcome
            reasoning_chain: Steps in the reasoning process
            
        Returns:
            List of discovered relationships
        """
        discovered = []
        
        # Only process successful outcomes
        if outcome.composite_success_score() < 0.6:
            return discovered
        
        # Extract entity pairs from reasoning chain
        for step in reasoning_chain:
            relationships = self._extract_relationships_from_text(step)
            discovered.extend(relationships)
        
        # Score and filter relationships
        scored_relationships = []
        for rel in discovered:
            # Score based on outcome success
            rel.confidence_score = (
                outcome.composite_success_score() *
                rel.confidence_score
            )
            
            if rel.confidence_score >= self.cfg.latent_relation_confidence_threshold:
                scored_relationships.append(rel)
                self._add_or_update_relationship(rel)
        
        logger.info(
            f"Discovered {len(scored_relationships)} relationships "
            f"from reasoning chain"
        )
        
        return scored_relationships
    
    def _extract_relationships_from_text(
        self,
        text: str
    ) -> List[LatentRelationship]:
        """Extract relationships from text using patterns"""
        relationships = []
        
        # Simple entity extraction (can be improved)
        entities = self._extract_entities(text)
        
        if len(entities) < 2:
            return relationships
        
        # Check for relationship patterns
        for relation_name, pattern in self.relationship_patterns.items():
            if re.search(pattern, text, re.IGNORECASE):
                # Create relationships between entity pairs
                for i, entity1 in enumerate(entities):
                    for entity2 in entities[i+1:]:
                        rel = LatentRelationship(
                            source_entity=entity1,
                            target_entity=entity2,
                            relationship_type=relation_name,
                            confidence_score=0.7,  # Base confidence
                            reasoning_chain=[text]
                        )
                        relationships.append(rel)
        
        return relationships
    
    def _extract_entities(self, text: str) -> List[str]:
        """Extract potential entities from text"""
        # Simple extraction: capitalized words/phrases
        # In production, use NER models
        words = text.split()
        entities = []
        
        i = 0
        while i < len(words):
            word = words[i]
            
            # Look for capitalized words or phrases
            if word and word[0].isupper() and word not in ['The', 'A', 'An']:
                phrase = word
                
                # Collect consecutive capitalized words
                j = i + 1
                while j < len(words) and words[j] and words[j][0].isupper():
                    phrase += " " + words[j]
                    j += 1
                
                # Clean up
                phrase = re.sub(r'[,.!?;:]$', '', phrase)
                if len(phrase) > 2:
                    entities.append(phrase)
                
                i = j
            else:
                i += 1
        
        return entities
    
    def _add_or_update_relationship(self, relationship: LatentRelationship):
        """Add new or update existing latent relationship"""
        rel_key = (
            relationship.source_entity,
            relationship.target_entity,
            relationship.relationship_type
        )
        
        existing_id = None
        for rel_id, rel in self.meta_graph.latent_relations.items():
            if (rel.source_entity == relationship.source_entity and
                rel.target_entity == relationship.target_entity and
                rel.relationship_type == relationship.relationship_type):
                existing_id = rel_id
                break
        
        if existing_id:
            # Update existing relationship
            existing = self.meta_graph.latent_relations[existing_id]
            
            # Average confidence scores
            total_observations = existing.confidence_score + 1
            existing.confidence_score = (
                (existing.confidence_score * (total_observations - 1) +
                 relationship.confidence_score) / total_observations
            )
            
            # Add to reasoning chain
            existing.reasoning_chain.extend(relationship.reasoning_chain)
            
            logger.debug(
                f"Updated relationship: {existing.source_entity} "
                f"-[{existing.relationship_type}]-> "
                f"{existing.target_entity} | "
                f"Confidence: {existing.confidence_score:.2f}"
            )
        else:
            # Add new relationship
            self.meta_graph.latent_relations[relationship.relation_id] = (
                relationship
            )
            
            logger.info(
                f"Discovered new relationship: {relationship.source_entity} "
                f"-[{relationship.relationship_type}]-> "
                f"{relationship.target_entity} | "
                f"Confidence: {relationship.confidence_score:.2f}"
            )
    
    def approve_relationships(
        self,
        relationship_ids: List[str],
        auto_approve_high_confidence: bool = None
    ):
        """
        Approve discovered relationships for integration
        
        Args:
            relationship_ids: IDs to approve
            auto_approve_high_confidence: Override config if provided
        """
        if auto_approve_high_confidence is None:
            auto_approve_high_confidence = (
                self.cfg.auto_approve_high_confidence
            )
        
        approved_count = 0
        for rel_id in relationship_ids:
            if rel_id in self.meta_graph.latent_relations:
                rel = self.meta_graph.latent_relations[rel_id]
                rel.status = "approved"
                rel.approved_at = datetime.now()
                approved_count += 1
        
        logger.info(f"Approved {approved_count} relationships")
    
    def get_pending_relationships(self) -> List[LatentRelationship]:
        """Get all pending relationship approvals"""
        return [
            rel for rel in self.meta_graph.latent_relations.values()
            if rel.status == "pending"
        ]
    
    def get_high_confidence_relationships(
        self,
        threshold: float = 0.8
    ) -> List[LatentRelationship]:
        """Get high-confidence discovered relationships"""
        return [
            rel for rel in self.meta_graph.latent_relations.values()
            if rel.confidence_score >= threshold
        ]
    
    def auto_activate_high_confidence(
        self,
        threshold: float = None
    ) -> int:
        """
        Automatically activate high-confidence relationships
        
        Args:
            threshold: Confidence threshold
            
        Returns:
            Number of activated relationships
        """
        if threshold is None:
            threshold = self.cfg.latent_relation_confidence_threshold
        
        activated = 0
        for rel in self.meta_graph.latent_relations.values():
            if (rel.status == "pending" and
                rel.confidence_score >= threshold):
                rel.status = "active"
                rel.approved_at = datetime.now()
                activated += 1
        
        logger.info(f"Auto-activated {activated} relationships")
        return activated
    
    def get_statistics(self) -> Dict:
        """Get discovery statistics"""
        relations = self.meta_graph.latent_relations.values()
        
        return {
            "total_discovered": len(relations),
            "pending": sum(1 for r in relations if r.status == "pending"),
            "approved": sum(1 for r in relations if r.status == "approved"),
            "active": sum(1 for r in relations if r.status == "active"),
            "rejected": sum(1 for r in relations if r.status == "rejected"),
            "average_confidence": (
                sum(r.confidence_score for r in relations) / len(relations)
                if relations else 0.0
            ),
        }


# Global instance
lrd_instance: Optional[LatentRelationshipDiscovery] = None


def get_lrd(meta_graph: AdaptiveMetaGraph) -> LatentRelationshipDiscovery:
    """Get or create LRD instance"""
    global lrd_instance
    if lrd_instance is None:
        lrd_instance = LatentRelationshipDiscovery(meta_graph)
    return lrd_instance