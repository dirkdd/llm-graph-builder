# Task 10: Chunk Relationships Implementation
# Comprehensive relationship management system for hierarchical chunks

from typing import List, Dict, Any, Optional, Tuple, Set, Union
from dataclasses import dataclass, field
from datetime import datetime
import logging
import re
import hashlib
from collections import defaultdict, Counter
from pathlib import Path

# Import models from previous tasks
from .entities.navigation_models import (
    ChunkRelationship,
    RelationshipType,
    DecisionOutcome,
    HierarchicalChunk,
    EnhancedNavigationNode,
    DecisionTreeNode,
    NavigationContext,
    DatabaseMetadata,
    validate_chunk_relationships
)
from .semantic_chunker import ChunkingResult, SemanticChunk, ChunkType
from .navigation_extractor import NavigationStructure, NavigationNode


@dataclass
class RelationshipEvidence:
    """Evidence supporting a chunk relationship"""
    evidence_type: str                      # keyword, structural, semantic, positional
    evidence_text: List[str]               # Supporting text/keywords
    confidence: float                      # Evidence confidence (0-1)
    source_location: str                   # Where evidence was found
    detection_method: str                  # How evidence was detected
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            'evidence_type': self.evidence_type,
            'evidence_text': self.evidence_text,
            'confidence': self.confidence,
            'source_location': self.source_location,
            'detection_method': self.detection_method,
            'metadata': self.metadata
        }


@dataclass
class RelationshipDetectionResult:
    """Result of relationship detection analysis"""
    detected_relationships: List[ChunkRelationship]
    relationship_evidence: Dict[str, List[RelationshipEvidence]]  # relationship_id -> evidence
    detection_metrics: Dict[str, Any]
    quality_assessment: Dict[str, float]
    validation_errors: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            'detected_relationships': [rel.to_dict() for rel in self.detected_relationships],
            'relationship_evidence': {
                rel_id: [ev.to_dict() for ev in evidence_list] 
                for rel_id, evidence_list in self.relationship_evidence.items()
            },
            'detection_metrics': self.detection_metrics,
            'quality_assessment': self.quality_assessment,
            'validation_errors': self.validation_errors
        }


class ChunkRelationshipManager:
    """Comprehensive relationship management system for hierarchical chunks"""
    
    def __init__(self, 
                 min_relationship_strength: float = 0.3,
                 min_evidence_confidence: float = 0.5,
                 max_relationships_per_chunk: int = 20,
                 enable_quality_filtering: bool = True):
        """Initialize ChunkRelationshipManager
        
        Args:
            min_relationship_strength: Minimum strength for relationship creation
            min_evidence_confidence: Minimum confidence for evidence acceptance
            max_relationships_per_chunk: Maximum relationships per chunk to prevent overconnection
            enable_quality_filtering: Whether to filter low-quality relationships
        """
        self.min_relationship_strength = min_relationship_strength
        self.min_evidence_confidence = min_evidence_confidence
        self.max_relationships_per_chunk = max_relationships_per_chunk
        self.enable_quality_filtering = enable_quality_filtering
        self.logger = logging.getLogger(__name__)
        
        # Relationship pattern dictionaries
        self._init_relationship_patterns()
    
    def _init_relationship_patterns(self):
        """Initialize relationship detection patterns"""
        # Decision reference patterns
        self.decision_patterns = {
            'conditional': [
                r'\bif\s+(.+?)\s+then\b',
                r'\bwhen\s+(.+?)\s*,\s*then\b',
                r'\bunless\s+(.+?)\s*,\s*otherwise\b',
                r'\bprovided\s+that\s+(.+?)\s*,\b'
            ],
            'outcome': [
                r'\b(approve|decline|refer)\b',
                r'\b(approved|declined|referred)\b',
                r'\b(accept|reject|review)\b'
            ],
            'criteria': [
                r'\bcredit\s+score\s*[>=<]+\s*\d+\b',
                r'\bfico\s*[>=<]+\s*\d+\b',
                r'\bltv\s*[>=<]+\s*\d+%?\b',
                r'\bdti\s*[>=<]+\s*\d+%?\b'
            ]
        }
        
        # Cross-reference patterns
        self.reference_patterns = {
            'section_ref': [
                r'\bsection\s+(\d+\.?\d*\.?\d*)\b',
                r'\bsee\s+section\s+(\d+\.?\d*\.?\d*)\b',
                r'\bas\s+defined\s+in\s+section\s+(\d+\.?\d*\.?\d*)\b'
            ],
            'page_ref': [
                r'\bpage\s+(\d+)\b',
                r'\bon\s+page\s+(\d+)\b',
                r'\bsee\s+page\s+(\d+)\b'
            ],
            'document_ref': [
                r'\bin\s+the\s+(.+?)\s+matrix\b',
                r'\baccording\s+to\s+the\s+(.+?)\s+guidelines\b',
                r'\bas\s+outlined\s+in\s+(.+?)\b'
            ]
        }
        
        # Matrix-specific patterns
        self.matrix_patterns = {
            'eligibility': [
                r'\beligible\s+for\b',
                r'\bqualifies\s+for\b',
                r'\bmeets\s+criteria\s+for\b'
            ],
            'requirements': [
                r'\brequires?\s+(.+?)\b',
                r'\bmust\s+(.+?)\b',
                r'\bshall\s+(.+?)\b'
            ],
            'exceptions': [
                r'\bexcept\s+when\b',
                r'\bunless\s+(.+?)\b',
                r'\bhowever\s*,\s*if\b'
            ]
        }
    
    def create_enhanced_relationships(self, 
                                    chunking_result: ChunkingResult,
                                    navigation_structure: NavigationStructure,
                                    enhanced_nodes: Dict[str, EnhancedNavigationNode] = None,
                                    decision_trees: List[DecisionTreeNode] = None) -> RelationshipDetectionResult:
        """Create enhanced relationships from chunking result
        
        Args:
            chunking_result: Output from SemanticChunker (Task 8)
            navigation_structure: Navigation structure from NavigationExtractor (Task 7)
            enhanced_nodes: Enhanced navigation nodes from Task 9
            decision_trees: Decision tree nodes from Task 9
            
        Returns:
            RelationshipDetectionResult: Comprehensive relationship analysis
        """
        try:
            start_time = datetime.now()
            self.logger.info(f"Starting enhanced relationship creation for {len(chunking_result.chunks)} chunks")
            
            # Convert SemanticChunks to HierarchicalChunks for enhanced processing
            hierarchical_chunks = []
            for semantic_chunk in chunking_result.chunks:
                hierarchical_chunk = HierarchicalChunk.from_semantic_chunk(semantic_chunk)
                hierarchical_chunks.append(hierarchical_chunk)
            
            # Initialize relationship detection
            detected_relationships = []
            relationship_evidence = {}
            detection_metrics = {}
            
            # 1. Create hierarchical relationships
            self.logger.info("Creating hierarchical relationships...")
            hierarchical_rels, hierarchical_evidence = self.create_hierarchical_relationships(
                hierarchical_chunks, navigation_structure, enhanced_nodes
            )
            detected_relationships.extend(hierarchical_rels)
            relationship_evidence.update(hierarchical_evidence)
            detection_metrics['hierarchical'] = len(hierarchical_rels)
            
            # 2. Create sequential relationships
            self.logger.info("Creating sequential relationships...")
            sequential_rels, sequential_evidence = self.create_sequential_relationships(
                hierarchical_chunks, navigation_structure
            )
            detected_relationships.extend(sequential_rels)
            relationship_evidence.update(sequential_evidence)
            detection_metrics['sequential'] = len(sequential_rels)
            
            # 3. Create reference relationships
            self.logger.info("Creating reference relationships...")
            reference_rels, reference_evidence = self.create_reference_relationships(
                hierarchical_chunks, navigation_structure
            )
            detected_relationships.extend(reference_rels)
            relationship_evidence.update(reference_evidence)
            detection_metrics['reference'] = len(reference_rels)
            
            # 4. Create decision relationships
            self.logger.info("Creating decision relationships...")
            decision_rels, decision_evidence = self.create_decision_relationships(
                hierarchical_chunks, navigation_structure, decision_trees
            )
            detected_relationships.extend(decision_rels)
            relationship_evidence.update(decision_evidence)
            detection_metrics['decision'] = len(decision_rels)
            
            # 5. Create matrix-guideline relationships
            self.logger.info("Creating matrix-guideline relationships...")
            matrix_rels, matrix_evidence = self._create_matrix_guideline_relationships(
                hierarchical_chunks, navigation_structure
            )
            detected_relationships.extend(matrix_rels)
            relationship_evidence.update(matrix_evidence)
            detection_metrics['matrix_guideline'] = len(matrix_rels)
            
            # 6. Quality filtering and validation
            if self.enable_quality_filtering:
                self.logger.info("Applying quality filtering...")
                detected_relationships = self._filter_relationships_by_quality(
                    detected_relationships, relationship_evidence
                )
            
            # 7. Validate relationships
            validation_errors = validate_chunk_relationships(hierarchical_chunks, detected_relationships)
            
            # 8. Calculate quality assessment
            quality_assessment = self._calculate_relationship_quality_metrics(
                detected_relationships, relationship_evidence, hierarchical_chunks
            )
            
            # 9. Update detection metrics
            detection_metrics.update({
                'total_relationships': len(detected_relationships),
                'processing_time': (datetime.now() - start_time).total_seconds(),
                'unique_relationship_types': len(set(rel.relationship_type for rel in detected_relationships)),
                'average_strength': sum(rel.strength for rel in detected_relationships) / len(detected_relationships) if detected_relationships else 0,
                'average_confidence': sum(rel.confidence for rel in detected_relationships) / len(detected_relationships) if detected_relationships else 0
            })
            
            result = RelationshipDetectionResult(
                detected_relationships=detected_relationships,
                relationship_evidence=relationship_evidence,
                detection_metrics=detection_metrics,
                quality_assessment=quality_assessment,
                validation_errors=validation_errors
            )
            
            self.logger.info(f"Enhanced relationship creation completed: {len(detected_relationships)} relationships created")
            return result
            
        except Exception as e:
            self.logger.error(f"Failed to create enhanced relationships: {str(e)}")
            raise
    
    def create_hierarchical_relationships(self, 
                                        chunks: List[HierarchicalChunk],
                                        navigation_structure: NavigationStructure,
                                        enhanced_nodes: Dict[str, EnhancedNavigationNode] = None) -> Tuple[List[ChunkRelationship], Dict[str, List[RelationshipEvidence]]]:
        """Create parent-child and sibling relationships based on document hierarchy"""
        relationships = []
        evidence_dict = {}
        
        # Group chunks by navigation node
        chunks_by_node = defaultdict(list)
        for chunk in chunks:
            if chunk.source_node_id:
                chunks_by_node[chunk.source_node_id].append(chunk)
        
        # Create parent-child relationships
        for node_id, node_chunks in chunks_by_node.items():
            if node_id in navigation_structure.nodes:
                node = navigation_structure.nodes[node_id]
                
                # Parent-child relationships to child nodes
                for child_id in node.children:
                    if child_id in chunks_by_node:
                        child_chunks = chunks_by_node[child_id]
                        
                        for parent_chunk in node_chunks:
                            for child_chunk in child_chunks:
                                rel_id = f"parent_child_{parent_chunk.chunk_id}_{child_chunk.chunk_id}"
                                
                                # Create relationship
                                relationship = ChunkRelationship(
                                    relationship_id=rel_id,
                                    relationship_type=RelationshipType.PARENT_CHILD,
                                    from_chunk_id=parent_chunk.chunk_id,
                                    to_chunk_id=child_chunk.chunk_id,
                                    from_node_id=node_id,
                                    to_node_id=child_id,
                                    strength=0.9,  # High strength for hierarchical relationships
                                    confidence=0.95,  # High confidence from navigation structure
                                    context=f"Parent section '{node.title}' to child section '{navigation_structure.nodes[child_id].title}'",
                                    evidence=[f"Navigation hierarchy: {node.title} -> {navigation_structure.nodes[child_id].title}"],
                                    extraction_method="hierarchical_structure"
                                )
                                relationships.append(relationship)
                                
                                # Create evidence
                                evidence = RelationshipEvidence(
                                    evidence_type="structural",
                                    evidence_text=[f"Parent: {node.title}", f"Child: {navigation_structure.nodes[child_id].title}"],
                                    confidence=0.95,
                                    source_location=f"Navigation structure: {node_id} -> {child_id}",
                                    detection_method="navigation_hierarchy",
                                    metadata={
                                        'parent_section_number': node.section_number,
                                        'child_section_number': navigation_structure.nodes[child_id].section_number
                                    }
                                )
                                evidence_dict[rel_id] = [evidence]
        
        # Create sibling relationships (same parent)
        for node_id, node_chunks in chunks_by_node.items():
            if node_id in navigation_structure.nodes:
                node = navigation_structure.nodes[node_id]
                parent_id = node.parent_id
                
                if parent_id:
                    # Find sibling nodes
                    sibling_nodes = [child_id for child_id in navigation_structure.nodes[parent_id].children 
                                   if child_id != node_id and child_id in chunks_by_node]
                    
                    for sibling_id in sibling_nodes:
                        sibling_chunks = chunks_by_node[sibling_id]
                        
                        for chunk in node_chunks:
                            for sibling_chunk in sibling_chunks:
                                rel_id = f"sibling_{chunk.chunk_id}_{sibling_chunk.chunk_id}"
                                
                                relationship = ChunkRelationship(
                                    relationship_id=rel_id,
                                    relationship_type=RelationshipType.SEQUENTIAL,  # Siblings are sequential
                                    from_chunk_id=chunk.chunk_id,
                                    to_chunk_id=sibling_chunk.chunk_id,
                                    from_node_id=node_id,
                                    to_node_id=sibling_id,
                                    strength=0.7,
                                    confidence=0.8,
                                    context=f"Sibling sections under '{navigation_structure.nodes[parent_id].title}'",
                                    evidence=[f"Common parent: {navigation_structure.nodes[parent_id].title}"],
                                    extraction_method="sibling_structure"
                                )
                                relationships.append(relationship)
                                
                                evidence = RelationshipEvidence(
                                    evidence_type="structural",
                                    evidence_text=[f"Common parent: {navigation_structure.nodes[parent_id].title}"],
                                    confidence=0.8,
                                    source_location=f"Sibling relationship: {node_id} <-> {sibling_id}",
                                    detection_method="sibling_detection"
                                )
                                evidence_dict[rel_id] = [evidence]
        
        return relationships, evidence_dict
    
    def create_sequential_relationships(self, 
                                      chunks: List[HierarchicalChunk],
                                      navigation_structure: NavigationStructure) -> Tuple[List[ChunkRelationship], Dict[str, List[RelationshipEvidence]]]:
        """Create sequential relationships based on content flow and document order"""
        relationships = []
        evidence_dict = {}
        
        # Sort chunks by navigation order and content position
        sorted_chunks = self._sort_chunks_by_document_order(chunks, navigation_structure)
        
        # Create sequential relationships between adjacent chunks
        for i in range(len(sorted_chunks) - 1):
            current_chunk = sorted_chunks[i]
            next_chunk = sorted_chunks[i + 1]
            
            # Skip if chunks are too far apart in hierarchy
            if not self._chunks_are_sequentially_related(current_chunk, next_chunk, navigation_structure):
                continue
            
            rel_id = f"sequential_{current_chunk.chunk_id}_{next_chunk.chunk_id}"
            
            # Calculate relationship strength based on proximity and context
            strength = self._calculate_sequential_strength(current_chunk, next_chunk, navigation_structure)
            
            relationship = ChunkRelationship(
                relationship_id=rel_id,
                relationship_type=RelationshipType.SEQUENTIAL,
                from_chunk_id=current_chunk.chunk_id,
                to_chunk_id=next_chunk.chunk_id,
                from_node_id=current_chunk.source_node_id,
                to_node_id=next_chunk.source_node_id,
                strength=strength,
                confidence=0.8,
                context=f"Sequential content flow from '{current_chunk.navigation_context.section_title}' to '{next_chunk.navigation_context.section_title}'",
                evidence=[f"Document order: {i} -> {i+1}"],
                extraction_method="sequential_analysis"
            )
            relationships.append(relationship)
            
            # Create evidence
            evidence = RelationshipEvidence(
                evidence_type="positional",
                evidence_text=[f"Sequential order: {i} -> {i+1}"],
                confidence=0.8,
                source_location=f"Document flow: {current_chunk.chunk_id} -> {next_chunk.chunk_id}",
                detection_method="sequential_ordering",
                metadata={
                    'position_current': i,
                    'position_next': i + 1,
                    'strength_score': strength
                }
            )
            evidence_dict[rel_id] = [evidence]
        
        # Create content overlap relationships
        overlap_relationships = self._create_content_overlap_relationships(sorted_chunks)
        relationships.extend(overlap_relationships)
        
        return relationships, evidence_dict
    
    def create_reference_relationships(self, 
                                     chunks: List[HierarchicalChunk],
                                     navigation_structure: NavigationStructure) -> Tuple[List[ChunkRelationship], Dict[str, List[RelationshipEvidence]]]:
        """Create relationships based on cross-references and citations"""
        relationships = []
        evidence_dict = {}
        
        for chunk in chunks:
            # Find references in chunk content
            references = self._extract_references(chunk.content)
            
            for reference in references:
                # Find target chunks for the reference
                target_chunks = self._find_reference_targets(reference, chunks, navigation_structure)
                
                for target_chunk in target_chunks:
                    if target_chunk.chunk_id == chunk.chunk_id:
                        continue  # Skip self-references
                    
                    rel_id = f"reference_{chunk.chunk_id}_{target_chunk.chunk_id}"
                    
                    # Calculate relationship strength based on reference type and clarity
                    strength = self._calculate_reference_strength(reference, chunk, target_chunk)
                    
                    relationship = ChunkRelationship(
                        relationship_id=rel_id,
                        relationship_type=RelationshipType.REFERENCES,
                        from_chunk_id=chunk.chunk_id,
                        to_chunk_id=target_chunk.chunk_id,
                        from_node_id=chunk.source_node_id,
                        to_node_id=target_chunk.source_node_id,
                        strength=strength,
                        confidence=reference['confidence'],
                        context=f"Reference from '{chunk.navigation_context.section_title}' to '{target_chunk.navigation_context.section_title}'",
                        evidence=[reference['text']],
                        keywords=[reference['keyword']],
                        extraction_method="reference_analysis"
                    )
                    relationships.append(relationship)
                    
                    # Create evidence
                    evidence = RelationshipEvidence(
                        evidence_type="keyword",
                        evidence_text=[reference['text'], reference['keyword']],
                        confidence=reference['confidence'],
                        source_location=f"Reference in chunk: {chunk.chunk_id}",
                        detection_method=f"reference_pattern_{reference['type']}",
                        metadata={
                            'reference_type': reference['type'],
                            'reference_text': reference['text'],
                            'target_section': reference.get('target_section')
                        }
                    )
                    evidence_dict[rel_id] = [evidence]
        
        return relationships, evidence_dict
    
    def create_decision_relationships(self, 
                                    chunks: List[HierarchicalChunk],
                                    navigation_structure: NavigationStructure,
                                    decision_trees: List[DecisionTreeNode] = None) -> Tuple[List[ChunkRelationship], Dict[str, List[RelationshipEvidence]]]:
        """Create relationships based on decision logic and conditional statements"""
        relationships = []
        evidence_dict = {}
        
        # Find decision chunks
        decision_chunks = [chunk for chunk in chunks if chunk.is_decision_chunk()]
        
        for decision_chunk in decision_chunks:
            # Extract decision logic from content
            decision_logic = self._extract_decision_logic(decision_chunk.content)
            
            for logic in decision_logic:
                # Find chunks referenced in decision logic
                referenced_chunks = self._find_decision_references(logic, chunks, navigation_structure)
                
                for ref_chunk in referenced_chunks:
                    if ref_chunk.chunk_id == decision_chunk.chunk_id:
                        continue
                    
                    # Determine relationship type based on decision logic
                    relationship_type = self._determine_decision_relationship_type(logic, decision_chunk, ref_chunk)
                    
                    rel_id = f"decision_{relationship_type.value}_{decision_chunk.chunk_id}_{ref_chunk.chunk_id}"
                    
                    # Calculate strength based on decision clarity and relevance
                    strength = self._calculate_decision_strength(logic, decision_chunk, ref_chunk)
                    
                    relationship = ChunkRelationship(
                        relationship_id=rel_id,
                        relationship_type=relationship_type,
                        from_chunk_id=decision_chunk.chunk_id,
                        to_chunk_id=ref_chunk.chunk_id,
                        from_node_id=decision_chunk.source_node_id,
                        to_node_id=ref_chunk.source_node_id,
                        strength=strength,
                        confidence=logic['confidence'],
                        context=f"Decision logic: {logic['type']}",
                        evidence=[logic['text']],
                        decision_condition=logic.get('condition'),
                        decision_outcome=logic.get('outcome'),
                        decision_variables=logic.get('variables', {}),
                        extraction_method="decision_analysis"
                    )
                    relationships.append(relationship)
                    
                    # Create evidence
                    evidence = RelationshipEvidence(
                        evidence_type="semantic",
                        evidence_text=[logic['text'], logic.get('condition', '')],
                        confidence=logic['confidence'],
                        source_location=f"Decision logic in chunk: {decision_chunk.chunk_id}",
                        detection_method=f"decision_pattern_{logic['type']}",
                        metadata={
                            'decision_type': logic['type'],
                            'condition': logic.get('condition'),
                            'outcome': logic.get('outcome'),
                            'variables': logic.get('variables', {})
                        }
                    )
                    evidence_dict[rel_id] = [evidence]
        
        # Create decision tree relationships if decision trees are provided
        if decision_trees:
            tree_relationships = self._create_decision_tree_relationships(decision_chunks, decision_trees)
            relationships.extend(tree_relationships)
        
        return relationships, evidence_dict
    
    # Private helper methods for relationship creation
    
    def _create_matrix_guideline_relationships(self, 
                                             chunks: List[HierarchicalChunk],
                                             navigation_structure: NavigationStructure) -> Tuple[List[ChunkRelationship], Dict[str, List[RelationshipEvidence]]]:
        """Create relationships between matrix documents and guideline documents"""
        relationships = []
        evidence_dict = {}
        
        # Separate matrix and guideline chunks
        matrix_chunks = [chunk for chunk in chunks if chunk.navigation_context.document_type == "matrix"]
        guideline_chunks = [chunk for chunk in chunks if chunk.navigation_context.document_type == "guidelines"]
        
        for matrix_chunk in matrix_chunks:
            # Extract criteria and requirements from matrix chunk
            criteria = self._extract_matrix_criteria(matrix_chunk.content)
            
            for criterion in criteria:
                # Find guideline chunks that define these criteria
                matching_guidelines = self._find_guideline_definitions(criterion, guideline_chunks)
                
                for guideline_chunk in matching_guidelines:
                    rel_id = f"matrix_guideline_{matrix_chunk.chunk_id}_{guideline_chunk.chunk_id}"
                    
                    relationship = ChunkRelationship(
                        relationship_id=rel_id,
                        relationship_type=RelationshipType.MATRIX_GUIDELINE,
                        from_chunk_id=matrix_chunk.chunk_id,
                        to_chunk_id=guideline_chunk.chunk_id,
                        from_node_id=matrix_chunk.source_node_id,
                        to_node_id=guideline_chunk.source_node_id,
                        strength=criterion['strength'],
                        confidence=criterion['confidence'],
                        context=f"Matrix criterion '{criterion['text']}' defined in guidelines",
                        evidence=[criterion['text']],
                        keywords=[criterion['keyword']],
                        extraction_method="matrix_guideline_analysis"
                    )
                    relationships.append(relationship)
                    
                    evidence = RelationshipEvidence(
                        evidence_type="semantic",
                        evidence_text=[criterion['text'], criterion['keyword']],
                        confidence=criterion['confidence'],
                        source_location=f"Matrix chunk: {matrix_chunk.chunk_id}",
                        detection_method="matrix_criteria_extraction",
                        metadata={
                            'criterion_type': criterion['type'],
                            'criterion_text': criterion['text']
                        }
                    )
                    evidence_dict[rel_id] = [evidence]
        
        return relationships, evidence_dict
    
    def _filter_relationships_by_quality(self, 
                                        relationships: List[ChunkRelationship],
                                        evidence_dict: Dict[str, List[RelationshipEvidence]]) -> List[ChunkRelationship]:
        """Filter relationships based on quality criteria"""
        filtered_relationships = []
        
        for relationship in relationships:
            # Check minimum strength threshold
            if relationship.strength < self.min_relationship_strength:
                continue
            
            # Check evidence quality
            if relationship.relationship_id in evidence_dict:
                evidence_list = evidence_dict[relationship.relationship_id]
                avg_evidence_confidence = sum(ev.confidence for ev in evidence_list) / len(evidence_list)
                
                if avg_evidence_confidence < self.min_evidence_confidence:
                    continue
            
            filtered_relationships.append(relationship)
        
        # Limit relationships per chunk to prevent overconnection
        chunk_relationship_counts = defaultdict(int)
        final_relationships = []
        
        for relationship in filtered_relationships:
            from_count = chunk_relationship_counts[relationship.from_chunk_id]
            to_count = chunk_relationship_counts[relationship.to_chunk_id]
            
            if from_count < self.max_relationships_per_chunk and to_count < self.max_relationships_per_chunk:
                final_relationships.append(relationship)
                chunk_relationship_counts[relationship.from_chunk_id] += 1
                chunk_relationship_counts[relationship.to_chunk_id] += 1
        
        return final_relationships
    
    def _calculate_relationship_quality_metrics(self, 
                                              relationships: List[ChunkRelationship],
                                              evidence_dict: Dict[str, List[RelationshipEvidence]],
                                              chunks: List[HierarchicalChunk]) -> Dict[str, float]:
        """Calculate overall relationship quality metrics"""
        if not relationships:
            return {'overall_quality': 0.0}
        
        # Strength distribution
        strengths = [rel.strength for rel in relationships]
        avg_strength = sum(strengths) / len(strengths)
        
        # Confidence distribution  
        confidences = [rel.confidence for rel in relationships]
        avg_confidence = sum(confidences) / len(confidences)
        
        # Evidence quality
        evidence_qualities = []
        for rel_id, evidence_list in evidence_dict.items():
            if evidence_list:
                avg_evidence_conf = sum(ev.confidence for ev in evidence_list) / len(evidence_list)
                evidence_qualities.append(avg_evidence_conf)
        
        avg_evidence_quality = sum(evidence_qualities) / len(evidence_qualities) if evidence_qualities else 0.0
        
        # Coverage (percentage of chunks with relationships)
        chunks_with_relationships = set()
        for rel in relationships:
            chunks_with_relationships.add(rel.from_chunk_id)
            chunks_with_relationships.add(rel.to_chunk_id)
        
        coverage = len(chunks_with_relationships) / len(chunks) if chunks else 0.0
        
        # Type diversity
        unique_types = len(set(rel.relationship_type for rel in relationships))
        type_diversity = unique_types / len(RelationshipType) if RelationshipType else 0.0
        
        return {
            'overall_quality': (avg_strength + avg_confidence + avg_evidence_quality + coverage + type_diversity) / 5,
            'average_strength': avg_strength,
            'average_confidence': avg_confidence,
            'average_evidence_quality': avg_evidence_quality,
            'coverage': coverage,
            'type_diversity': type_diversity,
            'total_relationships': len(relationships),
            'relationships_per_chunk': len(relationships) / len(chunks) if chunks else 0
        }
    
    # Additional helper methods for pattern extraction and analysis
    # (Implementation continues with specific pattern detection methods)
    
    def _sort_chunks_by_document_order(self, chunks: List[HierarchicalChunk], navigation_structure: NavigationStructure) -> List[HierarchicalChunk]:
        """Sort chunks by their order in the document"""
        def sort_key(chunk):
            if chunk.source_node_id and chunk.source_node_id in navigation_structure.nodes:
                node = navigation_structure.nodes[chunk.source_node_id]
                line_num = node.metadata.get('line_number', 999)
                return (line_num, chunk.start_position)
            return (999, chunk.start_position)
        
        return sorted(chunks, key=sort_key)
    
    def _chunks_are_sequentially_related(self, chunk1: HierarchicalChunk, chunk2: HierarchicalChunk, navigation_structure: NavigationStructure) -> bool:
        """Check if two chunks are sequentially related"""
        # Check if chunks are in adjacent sections
        if chunk1.source_node_id and chunk2.source_node_id:
            node1 = navigation_structure.nodes.get(chunk1.source_node_id)
            node2 = navigation_structure.nodes.get(chunk2.source_node_id)
            
            if node1 and node2:
                # Same parent or adjacent hierarchy levels
                return (node1.parent_id == node2.parent_id or 
                       abs(chunk1.navigation_context.hierarchy_level - chunk2.navigation_context.hierarchy_level) <= 1)
        
        return True  # Default to allowing sequential relationships
    
    def _calculate_sequential_strength(self, chunk1: HierarchicalChunk, chunk2: HierarchicalChunk, navigation_structure: NavigationStructure) -> float:
        """Calculate strength of sequential relationship"""
        base_strength = 0.6
        
        # Bonus for same section
        if chunk1.source_node_id == chunk2.source_node_id:
            base_strength += 0.2
        
        # Bonus for adjacent hierarchy levels
        level_diff = abs(chunk1.navigation_context.hierarchy_level - chunk2.navigation_context.hierarchy_level)
        if level_diff <= 1:
            base_strength += 0.1
        
        # Bonus for content overlap
        if chunk1.chunk_id in chunk2.overlap_with or chunk2.chunk_id in chunk1.overlap_with:
            base_strength += 0.1
        
        return min(base_strength, 1.0)
    
    def _create_content_overlap_relationships(self, chunks: List[HierarchicalChunk]) -> List[ChunkRelationship]:
        """Create relationships based on content overlap"""
        relationships = []
        
        for i, chunk1 in enumerate(chunks):
            for j, chunk2 in enumerate(chunks[i+1:], i+1):
                if chunk1.chunk_id in chunk2.overlap_with or chunk2.chunk_id in chunk1.overlap_with:
                    rel_id = f"overlap_{chunk1.chunk_id}_{chunk2.chunk_id}"
                    
                    relationship = ChunkRelationship(
                        relationship_id=rel_id,
                        relationship_type=RelationshipType.SEQUENTIAL,
                        from_chunk_id=chunk1.chunk_id,
                        to_chunk_id=chunk2.chunk_id,
                        strength=0.8,
                        confidence=0.9,
                        context="Content overlap detected",
                        evidence=["overlapping_content"],
                        extraction_method="overlap_analysis"
                    )
                    relationships.append(relationship)
        
        return relationships
    
    def _extract_references(self, content: str) -> List[Dict[str, Any]]:
        """Extract references from chunk content"""
        references = []
        
        # Section references
        for pattern in self.reference_patterns['section_ref']:
            matches = re.finditer(pattern, content, re.IGNORECASE)
            for match in matches:
                references.append({
                    'type': 'section',
                    'text': match.group(0),
                    'keyword': match.group(1) if match.groups() else match.group(0),
                    'target_section': match.group(1) if match.groups() else None,
                    'confidence': 0.9
                })
        
        # Page references
        for pattern in self.reference_patterns['page_ref']:
            matches = re.finditer(pattern, content, re.IGNORECASE)
            for match in matches:
                references.append({
                    'type': 'page',
                    'text': match.group(0),
                    'keyword': match.group(1) if match.groups() else match.group(0),
                    'target_page': match.group(1) if match.groups() else None,
                    'confidence': 0.8
                })
        
        # Document references
        for pattern in self.reference_patterns['document_ref']:
            matches = re.finditer(pattern, content, re.IGNORECASE)
            for match in matches:
                references.append({
                    'type': 'document',
                    'text': match.group(0),
                    'keyword': match.group(1) if match.groups() else match.group(0),
                    'target_document': match.group(1) if match.groups() else None,
                    'confidence': 0.7
                })
        
        return references
    
    def _find_reference_targets(self, reference: Dict[str, Any], chunks: List[HierarchicalChunk], navigation_structure: NavigationStructure) -> List[HierarchicalChunk]:
        """Find target chunks for a reference"""
        targets = []
        
        if reference['type'] == 'section' and reference['target_section']:
            section_num = reference['target_section']
            for chunk in chunks:
                if chunk.navigation_context.section_number == section_num:
                    targets.append(chunk)
        
        elif reference['type'] == 'document' and reference['target_document']:
            doc_name = reference['target_document'].lower()
            for chunk in chunks:
                if doc_name in chunk.navigation_context.document_type.lower():
                    targets.append(chunk)
        
        return targets
    
    def _calculate_reference_strength(self, reference: Dict[str, Any], source_chunk: HierarchicalChunk, target_chunk: HierarchicalChunk) -> float:
        """Calculate strength of reference relationship"""
        base_strength = 0.7
        
        # Bonus for explicit section references
        if reference['type'] == 'section':
            base_strength += 0.2
        
        # Bonus for same document type
        if source_chunk.navigation_context.document_type == target_chunk.navigation_context.document_type:
            base_strength += 0.1
        
        return min(base_strength, 1.0)
    
    def _extract_decision_logic(self, content: str) -> List[Dict[str, Any]]:
        """Extract decision logic patterns from content"""
        decision_logic = []
        
        # Conditional patterns
        for pattern in self.decision_patterns['conditional']:
            matches = re.finditer(pattern, content, re.IGNORECASE)
            for match in matches:
                decision_logic.append({
                    'type': 'conditional',
                    'text': match.group(0),
                    'condition': match.group(1) if match.groups() else None,
                    'confidence': 0.9
                })
        
        # Outcome patterns
        for pattern in self.decision_patterns['outcome']:
            matches = re.finditer(pattern, content, re.IGNORECASE)
            for match in matches:
                decision_logic.append({
                    'type': 'outcome',
                    'text': match.group(0),
                    'outcome': match.group(0).upper(),
                    'confidence': 0.8
                })
        
        # Criteria patterns
        for pattern in self.decision_patterns['criteria']:
            matches = re.finditer(pattern, content, re.IGNORECASE)
            for match in matches:
                decision_logic.append({
                    'type': 'criteria',
                    'text': match.group(0),
                    'criteria': match.group(0),
                    'confidence': 0.85
                })
        
        return decision_logic
    
    def _find_decision_references(self, logic: Dict[str, Any], chunks: List[HierarchicalChunk], navigation_structure: NavigationStructure) -> List[HierarchicalChunk]:
        """Find chunks referenced in decision logic"""
        references = []
        
        if logic['type'] == 'criteria' and 'criteria' in logic:
            criteria_text = logic['criteria'].lower()
            
            for chunk in chunks:
                # Look for chunks that define or mention the criteria
                if any(keyword in chunk.content.lower() for keyword in criteria_text.split()):
                    references.append(chunk)
        
        return references
    
    def _determine_decision_relationship_type(self, logic: Dict[str, Any], decision_chunk: HierarchicalChunk, ref_chunk: HierarchicalChunk) -> RelationshipType:
        """Determine the type of decision relationship"""
        if logic['type'] == 'conditional':
            return RelationshipType.CONDITIONAL
        elif logic['type'] == 'outcome':
            return RelationshipType.DECISION_OUTCOME
        elif logic['type'] == 'criteria':
            return RelationshipType.DECISION_BRANCH
        else:
            return RelationshipType.REFERENCES
    
    def _calculate_decision_strength(self, logic: Dict[str, Any], decision_chunk: HierarchicalChunk, ref_chunk: HierarchicalChunk) -> float:
        """Calculate strength of decision relationship"""
        base_strength = 0.8
        
        # Higher strength for explicit conditionals
        if logic['type'] == 'conditional':
            base_strength += 0.1
        
        # Higher strength for decision chunks
        if decision_chunk.is_decision_chunk():
            base_strength += 0.1
        
        return min(base_strength, 1.0)
    
    def _create_decision_tree_relationships(self, decision_chunks: List[HierarchicalChunk], decision_trees: List[DecisionTreeNode]) -> List[ChunkRelationship]:
        """Create relationships based on decision tree structure"""
        relationships = []
        
        # Map decision chunks to decision tree nodes
        for tree_node in decision_trees:
            matching_chunks = [chunk for chunk in decision_chunks 
                             if tree_node.source_node_id == chunk.source_node_id]
            
            for chunk in matching_chunks:
                # Create relationships to child decision nodes
                for child_id in tree_node.child_decision_ids:
                    child_node = next((node for node in decision_trees if node.node_id == child_id), None)
                    if child_node:
                        child_chunks = [c for c in decision_chunks if c.source_node_id == child_node.source_node_id]
                        
                        for child_chunk in child_chunks:
                            rel_id = f"decision_tree_{chunk.chunk_id}_{child_chunk.chunk_id}"
                            
                            relationship = ChunkRelationship(
                                relationship_id=rel_id,
                                relationship_type=RelationshipType.DECISION_BRANCH,
                                from_chunk_id=chunk.chunk_id,
                                to_chunk_id=child_chunk.chunk_id,
                                strength=0.9,
                                confidence=0.9,
                                context=f"Decision tree: {tree_node.title} -> {child_node.title}",
                                evidence=[f"Decision tree structure: {tree_node.node_id} -> {child_node.node_id}"],
                                extraction_method="decision_tree_structure"
                            )
                            relationships.append(relationship)
        
        return relationships
    
    def _extract_matrix_criteria(self, content: str) -> List[Dict[str, Any]]:
        """Extract criteria from matrix content"""
        criteria = []
        
        # Extract eligibility criteria
        for pattern in self.matrix_patterns['eligibility']:
            matches = re.finditer(pattern, content, re.IGNORECASE)
            for match in matches:
                criteria.append({
                    'type': 'eligibility',
                    'text': match.group(0),
                    'keyword': match.group(0),
                    'strength': 0.8,
                    'confidence': 0.8
                })
        
        # Extract requirements
        for pattern in self.matrix_patterns['requirements']:
            matches = re.finditer(pattern, content, re.IGNORECASE)
            for match in matches:
                criteria.append({
                    'type': 'requirement',
                    'text': match.group(0),
                    'keyword': match.group(1) if match.groups() else match.group(0),
                    'strength': 0.9,
                    'confidence': 0.8
                })
        
        return criteria
    
    def _find_guideline_definitions(self, criterion: Dict[str, Any], guideline_chunks: List[HierarchicalChunk]) -> List[HierarchicalChunk]:
        """Find guideline chunks that define matrix criteria"""
        matching_chunks = []
        
        keyword = criterion['keyword'].lower()
        
        for chunk in guideline_chunks:
            # Look for chunks that contain or define the criterion
            if keyword in chunk.content.lower():
                matching_chunks.append(chunk)
        
        return matching_chunks


# Export the main class
__all__ = ['ChunkRelationshipManager', 'RelationshipEvidence', 'RelationshipDetectionResult']