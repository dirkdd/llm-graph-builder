# Task 9: Hierarchical Chunk Models Test Suite
# Comprehensive tests for navigation models and hierarchical chunks

import pytest
from unittest.mock import Mock, patch
import sys
import os
from datetime import datetime
from pathlib import Path

# Add the parent directory to the path to import backend modules
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from src.entities.navigation_models import (
    # Enums
    RelationshipType,
    DecisionOutcome,
    QualityRating,
    # Core models
    DatabaseMetadata,
    NavigationContext,
    EnhancedNavigationNode,
    HierarchicalChunk,
    DecisionTreeNode,
    ChunkRelationship,
    # Utility functions
    create_navigation_hierarchy,
    validate_chunk_relationships,
    calculate_navigation_quality
)
from src.navigation_extractor import NavigationLevel, NavigationNode
from src.semantic_chunker import ChunkType, SemanticChunk, ChunkContext


class TestDatabaseMetadata:
    """Test DatabaseMetadata class"""
    
    def test_database_metadata_initialization(self):
        """Test DatabaseMetadata initialization with defaults"""
        metadata = DatabaseMetadata()
        
        assert metadata.version == "1.0.0"
        assert metadata.checksum is not None
        assert isinstance(metadata.created_at, datetime)
        assert isinstance(metadata.updated_at, datetime)
        assert isinstance(metadata.indexed_fields, list)
        assert isinstance(metadata.storage_metadata, dict)
    
    def test_database_metadata_to_dict(self):
        """Test DatabaseMetadata serialization"""
        metadata = DatabaseMetadata()
        result = metadata.to_dict()
        
        assert 'created_at' in result
        assert 'updated_at' in result
        assert 'version' in result
        assert 'checksum' in result
        assert isinstance(result['created_at'], str)  # ISO format
        assert isinstance(result['updated_at'], str)  # ISO format


class TestNavigationContext:
    """Test NavigationContext class"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.basic_context = NavigationContext(
            navigation_path=["NAA Guidelines", "Borrower Eligibility", "Income Requirements"],
            parent_section="Borrower Eligibility",
            section_number="2.1",
            hierarchy_level=2,
            document_type="guidelines"
        )
    
    def test_navigation_context_initialization(self):
        """Test NavigationContext initialization and post-processing"""
        context = self.basic_context
        
        assert context.context_quality > 0.8  # Should be high quality
        assert context.chapter_title == "Borrower Eligibility"
        assert context.section_title == "Income Requirements"
        assert len(context.validation_errors) == 0
    
    def test_get_breadcrumb(self):
        """Test breadcrumb generation"""
        context = self.basic_context
        
        breadcrumb = context.get_breadcrumb()
        expected = "NAA Guidelines > Borrower Eligibility > Income Requirements"
        assert breadcrumb == expected
        
        # Test custom separator
        breadcrumb_custom = context.get_breadcrumb(" / ")
        expected_custom = "NAA Guidelines / Borrower Eligibility / Income Requirements"
        assert breadcrumb_custom == expected_custom
    
    def test_context_quality_calculation(self):
        """Test context quality score calculation"""
        # High quality context
        high_quality = NavigationContext(
            navigation_path=["Doc", "Chapter", "Section"],
            section_number="1.1",
            parent_section="Chapter",
            hierarchy_level=2,
            document_type="guidelines"
        )
        assert high_quality.context_quality >= 0.8
        
        # Low quality context
        low_quality = NavigationContext(
            navigation_path=[],
            hierarchy_level=0,
            document_type="unknown"
        )
        assert low_quality.context_quality <= 0.4
    
    def test_navigation_context_serialization(self):
        """Test NavigationContext serialization"""
        context = self.basic_context
        result = context.to_dict()
        
        assert 'navigation_path' in result
        assert 'context_quality' in result
        assert 'chapter_title' in result
        assert result['navigation_path'] == context.navigation_path


class TestEnhancedNavigationNode:
    """Test EnhancedNavigationNode class"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.basic_node = EnhancedNavigationNode(
            node_id="income_req_001",
            title="Income Requirements",
            level=NavigationLevel.SECTION,
            content="If borrower income is bank statement derived, then 12 months of statements are required.",
            section_number="2.1",
            confidence_score=0.85
        )
    
    def test_enhanced_navigation_node_initialization(self):
        """Test EnhancedNavigationNode initialization"""
        node = self.basic_node
        
        assert node.node_id == "income_req_001"
        assert node.level == NavigationLevel.SECTION
        assert node.content_length == len(node.content)
        assert node.quality_rating == QualityRating.GOOD  # 0.85 confidence
        assert node.database_metadata is not None
        assert isinstance(node.children, list)
        assert isinstance(node.extracted_entities, list)
    
    def test_add_remove_child(self):
        """Test child node management"""
        parent = self.basic_node
        child_id = "subsection_001"
        
        # Add child
        parent.add_child(child_id)
        assert child_id in parent.children
        
        # Add duplicate (should not add twice)
        parent.add_child(child_id)
        assert parent.children.count(child_id) == 1
        
        # Remove child
        parent.remove_child(child_id)
        assert child_id not in parent.children
    
    def test_decision_node_detection(self):
        """Test decision node detection"""
        # Regular node
        regular_node = self.basic_node
        assert not regular_node.is_decision_node()
        
        # Decision node
        decision_node = EnhancedNavigationNode(
            node_id="decision_001",
            title="Credit Decision",
            level=NavigationLevel.SECTION,
            decision_type="BRANCH",
            decision_outcome=DecisionOutcome.APPROVE,
            decision_criteria=["credit_score >= 620"]
        )
        assert decision_node.is_decision_node()
    
    def test_quality_rating_assignment(self):
        """Test quality rating based on confidence score"""
        # Test different confidence levels
        excellent_node = EnhancedNavigationNode(
            node_id="test_1", title="Test", level=NavigationLevel.SECTION,
            confidence_score=0.95
        )
        assert excellent_node.quality_rating == QualityRating.EXCELLENT
        
        good_node = EnhancedNavigationNode(
            node_id="test_2", title="Test", level=NavigationLevel.SECTION,
            confidence_score=0.75
        )
        assert good_node.quality_rating == QualityRating.GOOD
        
        fair_node = EnhancedNavigationNode(
            node_id="test_3", title="Test", level=NavigationLevel.SECTION,
            confidence_score=0.55
        )
        assert fair_node.quality_rating == QualityRating.FAIR
        
        poor_node = EnhancedNavigationNode(
            node_id="test_4", title="Test", level=NavigationLevel.SECTION,
            confidence_score=0.25
        )
        assert poor_node.quality_rating == QualityRating.POOR
    
    def test_from_navigation_node_compatibility(self):
        """Test creation from Task 7 NavigationNode"""
        # Create Task 7 NavigationNode
        nav_node = NavigationNode(
            node_id="nav_001",
            title="Original Node",
            level=NavigationLevel.CHAPTER,
            content="Original content",
            confidence_score=0.8
        )
        
        # Convert to EnhancedNavigationNode
        enhanced = EnhancedNavigationNode.from_navigation_node(nav_node)
        
        assert enhanced.node_id == nav_node.node_id
        assert enhanced.title == nav_node.title
        assert enhanced.level == nav_node.level
        assert enhanced.content == nav_node.content
        assert enhanced.confidence_score == nav_node.confidence_score
        assert enhanced.database_metadata is not None
    
    def test_enhanced_navigation_node_serialization(self):
        """Test EnhancedNavigationNode serialization"""
        node = self.basic_node
        result = node.to_dict()
        
        assert 'node_id' in result
        assert 'level' in result
        assert 'quality_rating' in result
        assert 'database_metadata' in result
        assert result['level'] == NavigationLevel.SECTION.value
        assert result['quality_rating'] == QualityRating.GOOD.value


class TestHierarchicalChunk:
    """Test HierarchicalChunk class"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.navigation_context = NavigationContext(
            navigation_path=["NAA Guidelines", "Borrower Eligibility", "Income Requirements"],
            parent_section="Borrower Eligibility",
            section_number="2.1",
            hierarchy_level=2,
            document_type="guidelines"
        )
        
        self.basic_chunk = HierarchicalChunk(
            chunk_id="chunk_001",
            content="If borrower income is bank statement derived, then 12 months of business and personal bank statements are required.",
            chunk_type=ChunkType.DECISION,
            navigation_context=self.navigation_context,
            source_node_id="income_req_001",
            quality_score=0.85
        )
    
    def test_hierarchical_chunk_initialization(self):
        """Test HierarchicalChunk initialization"""
        chunk = self.basic_chunk
        
        assert chunk.chunk_id == "chunk_001"
        assert chunk.chunk_type == ChunkType.DECISION
        assert chunk.content_length == len(chunk.content)
        assert chunk.sentence_count > 0
        assert chunk.content_hash is not None
        assert chunk.quality_rating == QualityRating.GOOD
        assert chunk.database_metadata is not None
        assert chunk.chunking_algorithm == "hierarchical_semantic"
    
    def test_decision_chunk_detection(self):
        """Test decision chunk detection"""
        # Decision chunk by type
        decision_chunk = self.basic_chunk
        assert decision_chunk.is_decision_chunk()
        
        # Decision chunk by criteria
        criteria_chunk = HierarchicalChunk(
            chunk_id="chunk_002",
            content="Test content",
            chunk_type=ChunkType.CONTENT,
            navigation_context=self.navigation_context,
            decision_criteria=["credit_score >= 620"]
        )
        assert criteria_chunk.is_decision_chunk()
        
        # Regular content chunk
        content_chunk = HierarchicalChunk(
            chunk_id="chunk_003",
            content="Regular content",
            chunk_type=ChunkType.CONTENT,
            navigation_context=self.navigation_context
        )
        assert not content_chunk.is_decision_chunk()
    
    def test_add_relationships(self):
        """Test chunk relationship management"""
        chunk = self.basic_chunk
        
        # Add related chunk
        chunk.add_related_chunk("related_001")
        assert "related_001" in chunk.related_chunks
        
        # Add duplicate (should not add twice)
        chunk.add_related_chunk("related_001")
        assert chunk.related_chunks.count("related_001") == 1
        
        # Add overlap
        chunk.add_overlap("overlap_001")
        assert "overlap_001" in chunk.overlap_with
    
    def test_navigation_breadcrumb(self):
        """Test navigation breadcrumb generation"""
        chunk = self.basic_chunk
        breadcrumb = chunk.get_navigation_breadcrumb()
        
        expected = "NAA Guidelines > Borrower Eligibility > Income Requirements"
        assert breadcrumb == expected
    
    def test_from_semantic_chunk_compatibility(self):
        """Test creation from Task 8 SemanticChunk"""
        # Create Task 8 SemanticChunk
        chunk_context = ChunkContext(
            navigation_path=["Doc", "Section"],
            parent_section="Section",
            section_number="1.1",
            hierarchy_level=1,
            document_type="guidelines",
            quality_score=0.9
        )
        
        semantic_chunk = SemanticChunk(
            chunk_id="semantic_001",
            content="Test content",
            chunk_type=ChunkType.CONTENT,
            context=chunk_context,
            node_id="node_001",
            token_count=50
        )
        
        # Convert to HierarchicalChunk
        hierarchical = HierarchicalChunk.from_semantic_chunk(semantic_chunk)
        
        assert hierarchical.chunk_id == semantic_chunk.chunk_id
        assert hierarchical.content == semantic_chunk.content
        assert hierarchical.chunk_type == semantic_chunk.chunk_type
        assert hierarchical.source_node_id == semantic_chunk.node_id
        assert hierarchical.token_count == semantic_chunk.token_count
        assert hierarchical.quality_score == semantic_chunk.context.quality_score
    
    def test_hierarchical_chunk_serialization(self):
        """Test HierarchicalChunk serialization"""
        chunk = self.basic_chunk
        result = chunk.to_dict()
        
        assert 'chunk_id' in result
        assert 'chunk_type' in result
        assert 'navigation_context' in result
        assert 'quality_rating' in result
        assert 'processing_timestamp' in result
        assert result['chunk_type'] == ChunkType.DECISION.value
        assert result['quality_rating'] == QualityRating.GOOD.value


class TestDecisionTreeNode:
    """Test DecisionTreeNode class"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.decision_node = DecisionTreeNode(
            node_id="decision_001",
            title="Credit Score Decision",
            decision_type="BRANCH",
            condition="credit_score >= 620",
            criteria=["credit_score", "loan_purpose"],
            outcomes=[DecisionOutcome.APPROVE, DecisionOutcome.DECLINE],
            source_node_id="credit_section_001"
        )
    
    def test_decision_tree_node_initialization(self):
        """Test DecisionTreeNode initialization"""
        node = self.decision_node
        
        assert node.node_id == "decision_001"
        assert node.decision_type == "BRANCH"
        assert node.condition == "credit_score >= 620"
        assert len(node.outcomes) == 2
        assert node.complexity_score > 0
        assert node.database_metadata is not None
        assert node.validation_status == "pending"
    
    def test_add_criterion_and_outcome(self):
        """Test adding criteria and outcomes"""
        node = self.decision_node
        
        # Add criterion
        node.add_criterion("income_verified")
        assert "income_verified" in node.criteria
        
        # Add duplicate criterion (should not add twice)
        node.add_criterion("income_verified")
        assert node.criteria.count("income_verified") == 1
        
        # Add outcome with description
        node.add_outcome(DecisionOutcome.REFER, "Requires manual review")
        assert DecisionOutcome.REFER in node.outcomes
        assert node.outcome_descriptions[DecisionOutcome.REFER] == "Requires manual review"
    
    def test_node_type_detection(self):
        """Test leaf and root node detection"""
        # Root node (no parent)
        root_node = DecisionTreeNode(
            node_id="root_001",
            title="Root Decision",
            decision_type="ROOT"
        )
        assert root_node.is_root_node()
        assert root_node.is_leaf_node()  # No children yet
        
        # Leaf node (with parent, no children)
        leaf_node = DecisionTreeNode(
            node_id="leaf_001",
            title="Leaf Decision",
            decision_type="LEAF",
            parent_decision_id="root_001"
        )
        assert not leaf_node.is_root_node()
        assert leaf_node.is_leaf_node()
        
        # Branch node (with parent and children)
        branch_node = DecisionTreeNode(
            node_id="branch_001",
            title="Branch Decision",
            decision_type="BRANCH",
            parent_decision_id="root_001",
            child_decision_ids=["leaf_001", "leaf_002"]
        )
        assert not branch_node.is_root_node()
        assert not branch_node.is_leaf_node()
    
    def test_complexity_calculation(self):
        """Test decision complexity calculation"""
        # Simple decision
        simple_node = DecisionTreeNode(
            node_id="simple_001",
            title="Simple Decision",
            decision_type="LEAF",
            criteria=["one_criterion"]
        )
        simple_complexity = simple_node.complexity_score
        
        # Complex decision
        complex_node = DecisionTreeNode(
            node_id="complex_001",
            title="Complex Decision",
            decision_type="BRANCH",
            condition="complex_condition",
            criteria=["crit1", "crit2", "crit3", "crit4"],
            variables={"var1": "value1", "var2": "value2"},
            operators=["AND", "OR"],
            child_decision_ids=["child1", "child2", "child3"]
        )
        complex_complexity = complex_node.complexity_score
        
        assert complex_complexity > simple_complexity
        assert complex_complexity <= 1.0
    
    def test_decision_tree_node_serialization(self):
        """Test DecisionTreeNode serialization"""
        node = self.decision_node
        result = node.to_dict()
        
        assert 'node_id' in result
        assert 'decision_type' in result
        assert 'outcomes' in result
        assert 'complexity_score' in result
        assert 'database_metadata' in result
        assert all(isinstance(outcome, str) for outcome in result['outcomes'])


class TestChunkRelationship:
    """Test ChunkRelationship class"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.relationship = ChunkRelationship(
            relationship_id="rel_001",
            relationship_type=RelationshipType.PARENT_CHILD,
            from_chunk_id="chunk_001",
            to_chunk_id="chunk_002",
            strength=0.8,
            confidence=0.9
        )
    
    def test_chunk_relationship_initialization(self):
        """Test ChunkRelationship initialization"""
        rel = self.relationship
        
        assert rel.relationship_id == "rel_001"
        assert rel.relationship_type == RelationshipType.PARENT_CHILD
        assert rel.from_chunk_id == "chunk_001"
        assert rel.to_chunk_id == "chunk_002"
        assert rel.strength == 0.8
        assert rel.confidence == 0.9
        assert rel.database_metadata is not None
        assert rel.direction == "bidirectional"
    
    def test_auto_generated_relationship_id(self):
        """Test automatic relationship ID generation"""
        rel = ChunkRelationship(
            relationship_id="",  # Empty ID
            relationship_type=RelationshipType.REFERENCES,
            from_chunk_id="chunk_A",
            to_chunk_id="chunk_B"
        )
        
        assert rel.relationship_id != ""
        assert len(rel.relationship_id) == 12  # MD5 hash truncated to 12 chars
    
    def test_relationship_type_detection(self):
        """Test relationship type detection methods"""
        # Hierarchical relationship
        hierarchical_rel = ChunkRelationship(
            relationship_id="hier_001",
            relationship_type=RelationshipType.PARENT_CHILD,
            from_chunk_id="parent",
            to_chunk_id="child"
        )
        assert hierarchical_rel.is_hierarchical()
        assert not hierarchical_rel.is_decision_related()
        
        # Decision relationship
        decision_rel = ChunkRelationship(
            relationship_id="dec_001",
            relationship_type=RelationshipType.DECISION_BRANCH,
            from_chunk_id="decision",
            to_chunk_id="outcome",
            decision_outcome=DecisionOutcome.APPROVE
        )
        assert not decision_rel.is_hierarchical()
        assert decision_rel.is_decision_related()
    
    def test_relationship_summary(self):
        """Test relationship summary generation"""
        rel = self.relationship
        summary = rel.get_relationship_summary()
        
        expected = "chunk_001 PARENT_CHILD chunk_002"
        assert summary == expected
    
    def test_chunk_relationship_serialization(self):
        """Test ChunkRelationship serialization"""
        rel = self.relationship
        result = rel.to_dict()
        
        assert 'relationship_id' in result
        assert 'relationship_type' in result
        assert 'from_chunk_id' in result
        assert 'to_chunk_id' in result
        assert result['relationship_type'] == RelationshipType.PARENT_CHILD.value


class TestUtilityFunctions:
    """Test utility functions"""
    
    def test_create_navigation_hierarchy(self):
        """Test navigation hierarchy creation"""
        # Create nodes with parent-child relationships
        root = EnhancedNavigationNode(
            node_id="root",
            title="Document Root",
            level=NavigationLevel.DOCUMENT
        )
        
        chapter = EnhancedNavigationNode(
            node_id="chapter_1",
            title="Chapter 1",
            level=NavigationLevel.CHAPTER,
            parent_id="root"
        )
        
        section = EnhancedNavigationNode(
            node_id="section_1_1",
            title="Section 1.1",
            level=NavigationLevel.SECTION,
            parent_id="chapter_1"
        )
        
        nodes = [root, chapter, section]
        hierarchy = create_navigation_hierarchy(nodes)
        
        # Verify hierarchy was built correctly
        assert "section_1_1" in hierarchy["chapter_1"].children
        assert "chapter_1" in hierarchy["root"].children
        assert "root" in hierarchy["section_1_1"].ancestor_ids
        assert "chapter_1" in hierarchy["section_1_1"].ancestor_ids
        assert "section_1_1" in hierarchy["root"].descendant_ids
    
    def test_validate_chunk_relationships(self):
        """Test chunk relationship validation"""
        # Create test chunks
        chunk1 = HierarchicalChunk(
            chunk_id="chunk_1",
            content="Content 1",
            chunk_type=ChunkType.CONTENT,
            navigation_context=NavigationContext(navigation_path=["Test"])
        )
        
        chunk2 = HierarchicalChunk(
            chunk_id="chunk_2",
            content="Content 2",
            chunk_type=ChunkType.CONTENT,
            navigation_context=NavigationContext(navigation_path=["Test"])
        )
        
        chunks = [chunk1, chunk2]
        
        # Valid relationship
        valid_rel = ChunkRelationship(
            relationship_id="valid_rel",
            relationship_type=RelationshipType.SEQUENTIAL,
            from_chunk_id="chunk_1",
            to_chunk_id="chunk_2",
            strength=0.8,
            confidence=0.9
        )
        
        # Invalid relationship (references non-existent chunk)
        invalid_rel = ChunkRelationship(
            relationship_id="invalid_rel",
            relationship_type=RelationshipType.REFERENCES,
            from_chunk_id="chunk_1",
            to_chunk_id="nonexistent_chunk",
            strength=1.5,  # Invalid strength > 1.0
            confidence=0.8
        )
        
        relationships = [valid_rel, invalid_rel]
        errors = validate_chunk_relationships(chunks, relationships)
        
        assert len(errors) >= 2  # Should find at least 2 errors
        assert any("nonexistent_chunk" in error for error in errors)
        assert any("strength must be between" in error for error in errors)
    
    def test_calculate_navigation_quality(self):
        """Test navigation quality calculation"""
        # High quality navigation context
        high_quality_context = NavigationContext(
            navigation_path=["Doc", "Chapter", "Section"],
            section_number="1.1",
            parent_section="Chapter",
            hierarchy_level=2,
            document_type="guidelines"
        )
        
        high_quality = calculate_navigation_quality(high_quality_context)
        
        # Low quality navigation context
        low_quality_context = NavigationContext(
            navigation_path=[],
            hierarchy_level=0,
            document_type="unknown"
        )
        
        low_quality = calculate_navigation_quality(low_quality_context)
        
        assert high_quality > low_quality
        assert 0.0 <= high_quality <= 1.0
        assert 0.0 <= low_quality <= 1.0


class TestIntegrationWithExistingTasks:
    """Test integration with Task 7 and Task 8 components"""
    
    def test_navigation_extractor_integration(self):
        """Test integration with NavigationExtractor (Task 7)"""
        # Create NavigationNode from Task 7
        nav_node = NavigationNode(
            node_id="test_node",
            title="Test Section",
            level=NavigationLevel.SECTION,
            content="Test content for integration",
            section_number="1.1",
            confidence_score=0.8,
            metadata={'source': 'navigation_extractor'}
        )
        
        # Convert to EnhancedNavigationNode
        enhanced_node = EnhancedNavigationNode.from_navigation_node(nav_node)
        
        # Verify conversion preserved all data
        assert enhanced_node.node_id == nav_node.node_id
        assert enhanced_node.title == nav_node.title
        assert enhanced_node.level == nav_node.level
        assert enhanced_node.content == nav_node.content
        assert enhanced_node.section_number == nav_node.section_number
        assert enhanced_node.confidence_score == nav_node.confidence_score
        
        # Verify enhancement
        assert enhanced_node.database_metadata is not None
        assert enhanced_node.quality_rating != QualityRating.POOR
    
    def test_semantic_chunker_integration(self):
        """Test integration with SemanticChunker (Task 8)"""
        # Create ChunkContext from Task 8
        chunk_context = ChunkContext(
            navigation_path=["NAA Guidelines", "Income Requirements"],
            parent_section="Income Requirements",
            section_number="2.1",
            hierarchy_level=2,
            document_type="guidelines",
            decision_context="Income verification decision",
            related_chunks=["related_001"],
            quality_score=0.85
        )
        
        # Create SemanticChunk from Task 8
        semantic_chunk = SemanticChunk(
            chunk_id="semantic_test",
            content="If borrower income is bank statement derived, then statements are required.",
            chunk_type=ChunkType.DECISION,
            context=chunk_context,
            node_id="income_node_001",
            token_count=15,
            metadata={'source': 'semantic_chunker'}
        )
        
        # Convert to HierarchicalChunk
        hierarchical_chunk = HierarchicalChunk.from_semantic_chunk(semantic_chunk)
        
        # Verify conversion preserved all data
        assert hierarchical_chunk.chunk_id == semantic_chunk.chunk_id
        assert hierarchical_chunk.content == semantic_chunk.content
        assert hierarchical_chunk.chunk_type == semantic_chunk.chunk_type
        assert hierarchical_chunk.source_node_id == semantic_chunk.node_id
        assert hierarchical_chunk.token_count == semantic_chunk.token_count
        assert hierarchical_chunk.quality_score == semantic_chunk.context.quality_score
        
        # Verify navigation context conversion
        nav_context = hierarchical_chunk.navigation_context
        assert nav_context.navigation_path == chunk_context.navigation_path
        assert nav_context.parent_section == chunk_context.parent_section
        assert nav_context.section_number == chunk_context.section_number
        assert nav_context.hierarchy_level == chunk_context.hierarchy_level
        assert nav_context.document_type == chunk_context.document_type
        assert nav_context.decision_context == chunk_context.decision_context
        
        # Verify enhancement
        assert hierarchical_chunk.database_metadata is not None
        assert hierarchical_chunk.content_hash is not None
        assert hierarchical_chunk.processing_timestamp is not None


# Test execution helper
if __name__ == "__main__":
    pytest.main([__file__, "-v"])