# Task 10: Chunk Relationships Test Suite
# Comprehensive tests for chunk relationship management

import pytest
from unittest.mock import Mock, patch
import sys
import os
from datetime import datetime
from pathlib import Path

# Add the parent directory to the path to import backend modules
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from src.chunk_relationships import (
    ChunkRelationshipManager,
    RelationshipEvidence,
    RelationshipDetectionResult
)
from src.entities.navigation_models import (
    ChunkRelationship,
    RelationshipType,
    DecisionOutcome,
    HierarchicalChunk,
    EnhancedNavigationNode,
    DecisionTreeNode,
    NavigationContext
)
from src.semantic_chunker import ChunkingResult, SemanticChunk, ChunkContext, ChunkType
from src.navigation_extractor import NavigationStructure, NavigationNode, NavigationLevel, DocumentFormat


class TestRelationshipEvidence:
    """Test RelationshipEvidence class"""
    
    def test_relationship_evidence_initialization(self):
        """Test RelationshipEvidence initialization"""
        evidence = RelationshipEvidence(
            evidence_type="keyword",
            evidence_text=["section 2.1", "income requirements"],
            confidence=0.8,
            source_location="chunk_001",
            detection_method="pattern_matching"
        )
        
        assert evidence.evidence_type == "keyword"
        assert len(evidence.evidence_text) == 2
        assert evidence.confidence == 0.8
        assert evidence.source_location == "chunk_001"
        assert evidence.detection_method == "pattern_matching"
        assert isinstance(evidence.metadata, dict)
    
    def test_relationship_evidence_serialization(self):
        """Test RelationshipEvidence serialization"""
        evidence = RelationshipEvidence(
            evidence_type="structural",
            evidence_text=["parent-child"],
            confidence=0.9,
            source_location="navigation_structure",
            detection_method="hierarchy_analysis",
            metadata={"hierarchy_level": 2}
        )
        
        result = evidence.to_dict()
        
        assert 'evidence_type' in result
        assert 'confidence' in result
        assert 'metadata' in result
        assert result['evidence_type'] == "structural"
        assert result['confidence'] == 0.9
        assert result['metadata']['hierarchy_level'] == 2


class TestRelationshipDetectionResult:
    """Test RelationshipDetectionResult class"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.sample_relationship = ChunkRelationship(
            relationship_id="test_rel_001",
            relationship_type=RelationshipType.PARENT_CHILD,
            from_chunk_id="chunk_001",
            to_chunk_id="chunk_002",
            strength=0.8,
            confidence=0.9
        )
        
        self.sample_evidence = RelationshipEvidence(
            evidence_type="structural",
            evidence_text=["hierarchy evidence"],
            confidence=0.9,
            source_location="test",
            detection_method="test_method"
        )
    
    def test_detection_result_initialization(self):
        """Test RelationshipDetectionResult initialization"""
        result = RelationshipDetectionResult(
            detected_relationships=[self.sample_relationship],
            relationship_evidence={"test_rel_001": [self.sample_evidence]},
            detection_metrics={"total": 1},
            quality_assessment={"overall_quality": 0.85}
        )
        
        assert len(result.detected_relationships) == 1
        assert "test_rel_001" in result.relationship_evidence
        assert result.detection_metrics["total"] == 1
        assert result.quality_assessment["overall_quality"] == 0.85
        assert len(result.validation_errors) == 0
    
    def test_detection_result_serialization(self):
        """Test RelationshipDetectionResult serialization"""
        result = RelationshipDetectionResult(
            detected_relationships=[self.sample_relationship],
            relationship_evidence={"test_rel_001": [self.sample_evidence]},
            detection_metrics={"total": 1},
            quality_assessment={"overall_quality": 0.85}
        )
        
        serialized = result.to_dict()
        
        assert 'detected_relationships' in serialized
        assert 'relationship_evidence' in serialized
        assert 'detection_metrics' in serialized
        assert 'quality_assessment' in serialized
        assert len(serialized['detected_relationships']) == 1


class TestChunkRelationshipManager:
    """Test ChunkRelationshipManager class"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.manager = ChunkRelationshipManager(
            min_relationship_strength=0.3,
            min_evidence_confidence=0.5,
            max_relationships_per_chunk=20,
            enable_quality_filtering=True
        )
        
        # Create test navigation structure
        self.navigation_structure = self._create_test_navigation_structure()
        
        # Create test chunks
        self.test_chunks = self._create_test_hierarchical_chunks()
        
        # Create test chunking result
        self.chunking_result = self._create_test_chunking_result()
    
    def _create_test_navigation_structure(self) -> NavigationStructure:
        """Create test navigation structure"""
        root_node = NavigationNode(
            node_id="root",
            title="NAA Guidelines",
            level=NavigationLevel.DOCUMENT
        )
        
        eligibility_node = NavigationNode(
            node_id="eligibility",
            title="Borrower Eligibility",
            level=NavigationLevel.CHAPTER,
            parent_id="root",
            section_number="2",
            metadata={'line_number': 10}
        )
        
        income_node = NavigationNode(
            node_id="income",
            title="Income Requirements",
            level=NavigationLevel.SECTION,
            parent_id="eligibility",
            section_number="2.1",
            metadata={'line_number': 15}
        )
        
        credit_node = NavigationNode(
            node_id="credit",
            title="Credit Requirements",
            level=NavigationLevel.SECTION,
            parent_id="eligibility",
            section_number="2.2",
            metadata={'line_number': 25}
        )
        
        decision_node = NavigationNode(
            node_id="decision",
            title="Decision Matrix",
            level=NavigationLevel.CHAPTER,
            parent_id="root",
            section_number="5",
            decision_type="ROOT",
            metadata={'line_number': 50}
        )
        
        # Set up children
        root_node.children = ["eligibility", "decision"]
        eligibility_node.children = ["income", "credit"]
        
        nodes = {
            "root": root_node,
            "eligibility": eligibility_node,
            "income": income_node,
            "credit": credit_node,
            "decision": decision_node
        }
        
        return NavigationStructure(
            document_id="test_naa_001",
            document_format=DocumentFormat.TEXT,
            root_node=root_node,
            nodes=nodes,
            decision_trees=[],
            extraction_metadata={}
        )
    
    def _create_test_hierarchical_chunks(self) -> List[HierarchicalChunk]:
        """Create test hierarchical chunks"""
        chunks = []
        
        # Eligibility chunk
        eligibility_context = NavigationContext(
            navigation_path=["NAA Guidelines", "Borrower Eligibility"],
            section_number="2",
            hierarchy_level=1,
            document_type="guidelines"
        )
        
        eligibility_chunk = HierarchicalChunk(
            chunk_id="chunk_eligibility",
            content="All borrowers must meet the following baseline criteria for the NAA product.",
            chunk_type=ChunkType.CONTENT,
            navigation_context=eligibility_context,
            source_node_id="eligibility"
        )
        chunks.append(eligibility_chunk)
        
        # Income requirements chunk (decision)
        income_context = NavigationContext(
            navigation_path=["NAA Guidelines", "Borrower Eligibility", "Income Requirements"],
            section_number="2.1",
            hierarchy_level=2,
            document_type="guidelines",
            decision_context="Income verification requirements"
        )
        
        income_chunk = HierarchicalChunk(
            chunk_id="chunk_income",
            content="If borrower income is bank statement derived, then 12 months of business and personal bank statements are required. See section 2.2 for credit requirements.",
            chunk_type=ChunkType.DECISION,
            navigation_context=income_context,
            source_node_id="income",
            decision_criteria=["income_type", "documentation_requirements"],
            decision_outcomes=[DecisionOutcome.APPROVE, DecisionOutcome.PENDING_REVIEW]
        )
        chunks.append(income_chunk)
        
        # Credit requirements chunk (decision)
        credit_context = NavigationContext(
            navigation_path=["NAA Guidelines", "Borrower Eligibility", "Credit Requirements"],
            section_number="2.2",
            hierarchy_level=2,
            document_type="guidelines",
            decision_context="Credit score requirements"
        )
        
        credit_chunk = HierarchicalChunk(
            chunk_id="chunk_credit",
            content="Minimum credit score requirements: Primary residence requires 620 FICO. Investment property requires 640 FICO. Refer to the Decision Matrix for additional criteria.",
            chunk_type=ChunkType.DECISION,
            navigation_context=credit_context,
            source_node_id="credit",
            decision_criteria=["credit_score", "property_type"],
            decision_outcomes=[DecisionOutcome.APPROVE, DecisionOutcome.DECLINE]
        )
        chunks.append(credit_chunk)
        
        # Decision matrix chunk
        decision_context = NavigationContext(
            navigation_path=["NAA Guidelines", "Decision Matrix"],
            section_number="5",
            hierarchy_level=1,
            document_type="guidelines",
            decision_context="Loan approval decision tree"
        )
        
        decision_chunk = HierarchicalChunk(
            chunk_id="chunk_decision",
            content="Use the following decision tree: Step 1: Verify credit score and income. If FICO >= minimum AND income verified: Continue. Otherwise: DECLINE.",
            chunk_type=ChunkType.DECISION,
            navigation_context=decision_context,
            source_node_id="decision",
            decision_criteria=["credit_score", "income_verification"],
            decision_outcomes=[DecisionOutcome.APPROVE, DecisionOutcome.DECLINE]
        )
        chunks.append(decision_chunk)
        
        return chunks
    
    def _create_test_chunking_result(self) -> ChunkingResult:
        """Create test chunking result"""
        # Convert HierarchicalChunks to SemanticChunks for compatibility
        semantic_chunks = []
        chunk_relationships = []
        
        for chunk in self.test_chunks:
            context = ChunkContext(
                navigation_path=chunk.navigation_context.navigation_path,
                section_number=chunk.navigation_context.section_number,
                hierarchy_level=chunk.navigation_context.hierarchy_level,
                document_type=chunk.navigation_context.document_type,
                quality_score=chunk.quality_score
            )
            
            semantic_chunk = SemanticChunk(
                chunk_id=chunk.chunk_id,
                content=chunk.content,
                chunk_type=chunk.chunk_type,
                context=context,
                node_id=chunk.source_node_id
            )
            semantic_chunks.append(semantic_chunk)
        
        # Basic relationships from semantic chunker
        chunk_relationships = [
            {
                'from_chunk': 'chunk_eligibility',
                'to_chunk': 'chunk_income',
                'relationship_type': 'PARENT_CHILD',
                'metadata': {'source': 'hierarchy'}
            },
            {
                'from_chunk': 'chunk_income',
                'to_chunk': 'chunk_credit',
                'relationship_type': 'SEQUENTIAL',
                'metadata': {'source': 'sibling'}
            }
        ]
        
        return ChunkingResult(
            chunks=semantic_chunks,
            chunk_relationships=chunk_relationships,
            chunking_metadata={'total_chunks': len(semantic_chunks)},
            quality_metrics={'overall_quality': 0.85}
        )
    
    def test_manager_initialization(self):
        """Test ChunkRelationshipManager initialization"""
        manager = ChunkRelationshipManager(
            min_relationship_strength=0.4,
            min_evidence_confidence=0.6,
            max_relationships_per_chunk=15,
            enable_quality_filtering=False
        )
        
        assert manager.min_relationship_strength == 0.4
        assert manager.min_evidence_confidence == 0.6
        assert manager.max_relationships_per_chunk == 15
        assert manager.enable_quality_filtering == False
        assert hasattr(manager, 'decision_patterns')
        assert hasattr(manager, 'reference_patterns')
        assert hasattr(manager, 'matrix_patterns')
    
    def test_create_enhanced_relationships(self):
        """Test complete enhanced relationship creation"""
        result = self.manager.create_enhanced_relationships(
            self.chunking_result,
            self.navigation_structure
        )
        
        assert isinstance(result, RelationshipDetectionResult)
        assert len(result.detected_relationships) > 0
        assert len(result.relationship_evidence) > 0
        assert 'total_relationships' in result.detection_metrics
        assert 'overall_quality' in result.quality_assessment
        assert isinstance(result.validation_errors, list)
    
    def test_create_hierarchical_relationships(self):
        """Test hierarchical relationship creation"""
        relationships, evidence = self.manager.create_hierarchical_relationships(
            self.test_chunks,
            self.navigation_structure
        )
        
        assert len(relationships) > 0
        assert len(evidence) > 0
        
        # Check for parent-child relationships
        parent_child_rels = [rel for rel in relationships if rel.relationship_type == RelationshipType.PARENT_CHILD]
        assert len(parent_child_rels) > 0
        
        # Verify relationship structure
        for rel in parent_child_rels:
            assert rel.strength >= 0.8  # High strength for hierarchical
            assert rel.confidence >= 0.8
            assert rel.relationship_id in evidence
    
    def test_create_sequential_relationships(self):
        """Test sequential relationship creation"""
        relationships, evidence = self.manager.create_sequential_relationships(
            self.test_chunks,
            self.navigation_structure
        )
        
        assert len(relationships) >= 0  # May or may not find sequential relationships
        
        # If relationships found, validate structure
        for rel in relationships:
            assert rel.relationship_type == RelationshipType.SEQUENTIAL
            assert 0.0 <= rel.strength <= 1.0
            assert 0.0 <= rel.confidence <= 1.0
            assert rel.relationship_id in evidence
    
    def test_create_reference_relationships(self):
        """Test reference relationship creation"""
        relationships, evidence = self.manager.create_reference_relationships(
            self.test_chunks,
            self.navigation_structure
        )
        
        # Should find references like "See section 2.2" and "Refer to the Decision Matrix"
        assert len(relationships) > 0
        
        reference_rels = [rel for rel in relationships if rel.relationship_type == RelationshipType.REFERENCES]
        assert len(reference_rels) > 0
        
        # Verify reference structure
        for rel in reference_rels:
            assert rel.strength > 0.0
            assert rel.confidence > 0.0
            assert len(rel.evidence) > 0
            assert rel.relationship_id in evidence
    
    def test_create_decision_relationships(self):
        """Test decision relationship creation"""
        relationships, evidence = self.manager.create_decision_relationships(
            self.test_chunks,
            self.navigation_structure
        )
        
        # Should find decision logic relationships
        assert len(relationships) >= 0
        
        # Check for decision-related relationship types
        decision_types = [RelationshipType.CONDITIONAL, RelationshipType.DECISION_BRANCH, RelationshipType.DECISION_OUTCOME]
        decision_rels = [rel for rel in relationships if rel.relationship_type in decision_types]
        
        # Validate decision relationship structure
        for rel in decision_rels:
            assert rel.strength > 0.0
            assert rel.confidence > 0.0
            assert rel.relationship_id in evidence
    
    def test_relationship_pattern_detection(self):
        """Test pattern detection methods"""
        manager = self.manager
        
        # Test reference extraction
        content_with_refs = "This requirement is defined in section 2.1. See page 15 for details. Refer to the Credit Matrix for additional criteria."
        references = manager._extract_references(content_with_refs)
        
        assert len(references) >= 2  # Should find section and document references
        
        # Check reference types
        ref_types = [ref['type'] for ref in references]
        assert 'section' in ref_types
        assert 'document' in ref_types or 'page' in ref_types
    
    def test_decision_logic_extraction(self):
        """Test decision logic extraction"""
        manager = self.manager
        
        # Test decision logic extraction
        decision_content = "If credit score is above 620, then approve the loan. When income is verified, proceed to next step. Unless borrower provides 20% down payment, mortgage insurance is required."
        logic = manager._extract_decision_logic(decision_content)
        
        assert len(logic) > 0
        
        # Check for conditional logic
        conditional_logic = [l for l in logic if l['type'] == 'conditional']
        assert len(conditional_logic) > 0
        
        # Validate logic structure
        for l in conditional_logic:
            assert 'text' in l
            assert 'confidence' in l
            assert l['confidence'] > 0.0
    
    def test_matrix_criteria_extraction(self):
        """Test matrix criteria extraction"""
        manager = self.manager
        
        # Test matrix criteria extraction
        matrix_content = "Borrower must provide 12 months bank statements. Property must be eligible for the program. Loan requires minimum 620 FICO score."
        criteria = manager._extract_matrix_criteria(matrix_content)
        
        assert len(criteria) > 0
        
        # Check criteria types
        criteria_types = [c['type'] for c in criteria]
        assert 'requirement' in criteria_types
        
        # Validate criteria structure
        for c in criteria:
            assert 'text' in c
            assert 'keyword' in c
            assert 'confidence' in c
            assert 'strength' in c
    
    def test_relationship_quality_filtering(self):
        """Test relationship quality filtering"""
        # Create test relationships with varying quality
        test_relationships = [
            ChunkRelationship(
                relationship_id="high_quality",
                relationship_type=RelationshipType.PARENT_CHILD,
                from_chunk_id="chunk_1",
                to_chunk_id="chunk_2",
                strength=0.9,
                confidence=0.9
            ),
            ChunkRelationship(
                relationship_id="low_quality",
                relationship_type=RelationshipType.REFERENCES,
                from_chunk_id="chunk_3",
                to_chunk_id="chunk_4",
                strength=0.1,  # Below threshold
                confidence=0.2
            ),
            ChunkRelationship(
                relationship_id="medium_quality",
                relationship_type=RelationshipType.SEQUENTIAL,
                from_chunk_id="chunk_5",
                to_chunk_id="chunk_6",
                strength=0.6,
                confidence=0.7
            )
        ]
        
        evidence_dict = {
            "high_quality": [RelationshipEvidence("structural", ["evidence"], 0.9, "test", "test")],
            "low_quality": [RelationshipEvidence("weak", ["weak evidence"], 0.2, "test", "test")],
            "medium_quality": [RelationshipEvidence("semantic", ["medium evidence"], 0.7, "test", "test")]
        }
        
        filtered = self.manager._filter_relationships_by_quality(test_relationships, evidence_dict)
        
        # Should filter out low quality relationship
        assert len(filtered) == 2
        filtered_ids = [rel.relationship_id for rel in filtered]
        assert "high_quality" in filtered_ids
        assert "medium_quality" in filtered_ids
        assert "low_quality" not in filtered_ids
    
    def test_relationship_quality_metrics(self):
        """Test relationship quality metrics calculation"""
        # Create test relationships and evidence
        test_relationships = [
            ChunkRelationship(
                relationship_id="rel_1",
                relationship_type=RelationshipType.PARENT_CHILD,
                from_chunk_id="chunk_1",
                to_chunk_id="chunk_2",
                strength=0.8,
                confidence=0.9
            ),
            ChunkRelationship(
                relationship_id="rel_2",
                relationship_type=RelationshipType.REFERENCES,
                from_chunk_id="chunk_2",
                to_chunk_id="chunk_3",
                strength=0.7,
                confidence=0.8
            )
        ]
        
        evidence_dict = {
            "rel_1": [RelationshipEvidence("structural", ["evidence1"], 0.9, "test", "test")],
            "rel_2": [RelationshipEvidence("semantic", ["evidence2"], 0.8, "test", "test")]
        }
        
        metrics = self.manager._calculate_relationship_quality_metrics(
            test_relationships, evidence_dict, self.test_chunks
        )
        
        assert 'overall_quality' in metrics
        assert 'average_strength' in metrics
        assert 'average_confidence' in metrics
        assert 'coverage' in metrics
        assert 'type_diversity' in metrics
        
        assert 0.0 <= metrics['overall_quality'] <= 1.0
        assert metrics['average_strength'] == 0.75  # (0.8 + 0.7) / 2
        assert metrics['average_confidence'] == 0.85  # (0.9 + 0.8) / 2
    
    def test_chunk_sorting_by_document_order(self):
        """Test chunk sorting by document order"""
        # Create chunks in random order
        unsorted_chunks = [self.test_chunks[2], self.test_chunks[0], self.test_chunks[3], self.test_chunks[1]]
        
        sorted_chunks = self.manager._sort_chunks_by_document_order(unsorted_chunks, self.navigation_structure)
        
        # Should be sorted by navigation structure order
        assert len(sorted_chunks) == len(unsorted_chunks)
        
        # First chunk should be from earlier in document
        assert sorted_chunks[0].source_node_id in ['eligibility', 'root']
        
        # Last chunk should be from later in document
        assert sorted_chunks[-1].source_node_id in ['decision', 'credit']
    
    def test_sequential_relationship_detection(self):
        """Test sequential relationship detection logic"""
        chunk1 = self.test_chunks[1]  # income chunk
        chunk2 = self.test_chunks[2]  # credit chunk
        
        # Test sequential relationship detection
        are_sequential = self.manager._chunks_are_sequentially_related(chunk1, chunk2, self.navigation_structure)
        assert are_sequential  # Same parent (eligibility)
        
        # Test strength calculation
        strength = self.manager._calculate_sequential_strength(chunk1, chunk2, self.navigation_structure)
        assert 0.0 <= strength <= 1.0
        assert strength > 0.5  # Should be reasonably strong for sibling sections
    
    def test_enhanced_nodes_integration(self):
        """Test integration with enhanced navigation nodes"""
        # Create enhanced nodes
        enhanced_nodes = {}
        for node_id, node in self.navigation_structure.nodes.items():
            enhanced_node = EnhancedNavigationNode.from_navigation_node(node)
            enhanced_nodes[node_id] = enhanced_node
        
        # Test with enhanced nodes
        relationships, evidence = self.manager.create_hierarchical_relationships(
            self.test_chunks,
            self.navigation_structure,
            enhanced_nodes
        )
        
        assert len(relationships) > 0
        assert len(evidence) > 0
        
        # Enhanced nodes should provide additional relationship context
        for rel in relationships:
            assert rel.strength > 0.0
            assert rel.confidence > 0.0
    
    def test_decision_tree_integration(self):
        """Test integration with decision tree nodes"""
        # Create test decision tree nodes
        decision_trees = [
            DecisionTreeNode(
                node_id="decision_tree_root",
                title="NAA Approval Decision",
                decision_type="ROOT",
                source_node_id="decision",
                child_decision_ids=["step_1", "step_2"]
            ),
            DecisionTreeNode(
                node_id="step_1",
                title="Credit and Income Check",
                decision_type="BRANCH",
                parent_decision_id="decision_tree_root",
                source_node_id="income"
            )
        ]
        
        # Test decision relationship creation with decision trees
        relationships, evidence = self.manager.create_decision_relationships(
            self.test_chunks,
            self.navigation_structure,
            decision_trees
        )
        
        assert len(relationships) >= 0
        
        # If decision tree relationships found, validate structure
        tree_rels = [rel for rel in relationships if rel.relationship_type == RelationshipType.DECISION_BRANCH]
        for rel in tree_rels:
            assert rel.strength > 0.0
            assert rel.confidence > 0.0


class TestIntegrationWithPreviousTasks:
    """Test integration with Tasks 8 and 9"""
    
    def test_semantic_chunker_integration(self):
        """Test integration with SemanticChunker output (Task 8)"""
        # Create realistic ChunkingResult from Task 8
        context = ChunkContext(
            navigation_path=["Test Document", "Test Section"],
            quality_score=0.8
        )
        
        semantic_chunk = SemanticChunk(
            chunk_id="semantic_test",
            content="Test content with decision logic: If credit score >= 620, then approve.",
            chunk_type=ChunkType.DECISION,
            context=context,
            node_id="test_node"
        )
        
        chunking_result = ChunkingResult(
            chunks=[semantic_chunk],
            chunk_relationships=[],
            chunking_metadata={},
            quality_metrics={}
        )
        
        # Create minimal navigation structure
        root_node = NavigationNode(
            node_id="test_node",
            title="Test Section",
            level=NavigationLevel.SECTION
        )
        
        navigation_structure = NavigationStructure(
            document_id="test_doc",
            document_format=DocumentFormat.TEXT,
            root_node=root_node,
            nodes={"test_node": root_node},
            decision_trees=[],
            extraction_metadata={}
        )
        
        # Test relationship creation
        manager = ChunkRelationshipManager()
        result = manager.create_enhanced_relationships(chunking_result, navigation_structure)
        
        assert isinstance(result, RelationshipDetectionResult)
        assert len(result.detected_relationships) >= 0
        assert 'processing_time' in result.detection_metrics
    
    def test_hierarchical_chunk_models_integration(self):
        """Test integration with HierarchicalChunk models (Task 9)"""
        # Create HierarchicalChunk directly
        navigation_context = NavigationContext(
            navigation_path=["Test", "Section"],
            section_number="1.1",
            hierarchy_level=1
        )
        
        hierarchical_chunk = HierarchicalChunk(
            chunk_id="hierarchical_test",
            content="Test content for hierarchical processing",
            chunk_type=ChunkType.CONTENT,
            navigation_context=navigation_context,
            source_node_id="test_node"
        )
        
        # Test that ChunkRelationshipManager can process HierarchicalChunks
        chunks = [hierarchical_chunk]
        
        # Create test navigation structure
        node = NavigationNode(
            node_id="test_node",
            title="Test Node",
            level=NavigationLevel.SECTION
        )
        
        navigation_structure = NavigationStructure(
            document_id="test",
            document_format=DocumentFormat.TEXT,
            root_node=node,
            nodes={"test_node": node},
            decision_trees=[],
            extraction_metadata={}
        )
        
        manager = ChunkRelationshipManager()
        
        # Test hierarchical relationship creation
        relationships, evidence = manager.create_hierarchical_relationships(
            chunks, navigation_structure
        )
        
        # Should handle HierarchicalChunks without errors
        assert isinstance(relationships, list)
        assert isinstance(evidence, dict)


# Test execution helper
if __name__ == "__main__":
    pytest.main([__file__, "-v"])