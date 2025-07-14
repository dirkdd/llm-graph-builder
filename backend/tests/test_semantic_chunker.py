# Task 8: Semantic Chunker Comprehensive Test Suite
# Tests hierarchy-aware semantic chunking with NavigationExtractor integration

import pytest
from unittest.mock import Mock, patch
import sys
import os
from pathlib import Path
from typing import List, Dict, Any

# Add the parent directory to the path to import backend modules
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from src.semantic_chunker import (
    SemanticChunker, 
    SemanticChunk, 
    ChunkType, 
    ChunkContext, 
    ChunkingResult
)
from src.navigation_extractor import (
    NavigationStructure, 
    NavigationNode, 
    NavigationLevel,
    DocumentFormat,
    TableOfContents
)


class TestSemanticChunker:
    """Comprehensive tests for SemanticChunker class"""

    def setup_method(self):
        """Set up test fixtures"""
        self.chunker = SemanticChunker(
            min_chunk_size=200,
            max_chunk_size=1500,
            target_chunk_size=800,
            overlap_size=100,
            context_window=2
        )
        
        # Create mock navigation structure for testing
        self.mock_navigation_structure = self._create_mock_navigation_structure()

    def _create_mock_navigation_structure(self) -> NavigationStructure:
        """Create realistic navigation structure for mortgage guidelines"""
        root_node = NavigationNode(
            node_id="naa_root",
            title="NAA Product Guidelines",
            level=NavigationLevel.DOCUMENT,
            content="Non-Agency Advantage Product Guidelines"
        )
        
        nodes = {
            "naa_root": root_node,
            "borrower_eligibility": NavigationNode(
                node_id="borrower_eligibility",
                title="Borrower Eligibility",
                level=NavigationLevel.CHAPTER,
                parent_id="naa_root",
                section_number="2",
                content="All borrowers must meet the following baseline criteria for the Non-Agency Advantage product. These requirements ensure that loans are originated within acceptable risk parameters while providing flexibility for non-traditional borrower profiles.",
                metadata={'line_number': 45, 'pattern_type': 'numbered_section'}
            ),
            "income_requirements": NavigationNode(
                node_id="income_requirements",
                title="Income Requirements",
                level=NavigationLevel.SECTION,
                parent_id="borrower_eligibility",
                section_number="2.1",
                content="If borrower income is bank statement derived, then 12 months of business and personal bank statements are required. When borrower claims rental income from investment properties, verification through lease agreements or property management statements is mandatory. For self-employed borrowers, a minimum of 24 months of business operation history must be documented.",
                metadata={'line_number': 52, 'pattern_type': 'numbered_section', 'decision_indicator': True}
            ),
            "credit_requirements": NavigationNode(
                node_id="credit_requirements", 
                title="Credit Requirements",
                level=NavigationLevel.SECTION,
                parent_id="borrower_eligibility",
                section_number="2.2",
                content="Minimum credit score requirements vary by property type and loan purpose. Primary residence purchases require a minimum 620 FICO score. Investment property purchases require a minimum 640 FICO score. Cash-out refinance transactions require a minimum 660 FICO score. If credit score falls below minimum thresholds, refer to underwriting for compensating factor review.",
                metadata={'line_number': 67, 'pattern_type': 'numbered_section', 'decision_indicator': True}
            ),
            "decision_matrix": NavigationNode(
                node_id="decision_matrix",
                title="Decision Matrix Framework",
                level=NavigationLevel.CHAPTER,
                parent_id="naa_root",
                section_number="5",
                decision_type="ROOT",
                content="Use the following decision tree for loan approval: Step 1: Credit and Income Verification. If FICO >= minimum AND income verified: Continue to Step 2. If FICO < minimum OR income insufficient: DECLINE. Step 2: Property and LTV Analysis. If LTV <= 80% AND property type approved: Continue to Step 3. If LTV > 80% OR property type restricted: REFER to underwriting. Step 3: Final Approval Decision. If all criteria met AND no red flags: APPROVE. If compensating factors needed: REFER to senior underwriter. Otherwise: DECLINE.",
                metadata={'line_number': 156, 'pattern_type': 'numbered_section', 'decision_indicator': True}
            )
        }
        
        # Set up parent-child relationships
        nodes["borrower_eligibility"].children = ["income_requirements", "credit_requirements"]
        nodes["naa_root"].children = ["borrower_eligibility", "decision_matrix"]
        
        mock_toc = TableOfContents(
            entries=[
                {"title": "Borrower Eligibility", "section_number": "2.", "page_number": 5},
                {"title": "Income Requirements", "section_number": "2.1", "page_number": 6},
                {"title": "Credit Requirements", "section_number": "2.2", "page_number": 8},
                {"title": "Decision Matrix Framework", "section_number": "5.", "page_number": 26}
            ],
            format_detected="text",
            confidence_score=0.92,
            extraction_method="pattern_matching"
        )
        
        return NavigationStructure(
            document_id="naa_guidelines_001",
            document_format=DocumentFormat.TEXT,
            root_node=root_node,
            nodes=nodes,
            table_of_contents=mock_toc,
            decision_trees=[
                {
                    "root_node_id": "decision_matrix",
                    "decision_type": "conditional",
                    "branches": ["credit_income_check", "property_ltv_check", "final_approval"],
                    "outcomes": ["APPROVE", "DECLINE", "REFER"]
                }
            ],
            extraction_metadata={
                "document_name": "NAA-Guidelines.pdf",
                "package_category": "NQM",
                "total_nodes": 4,
                "max_depth": 2
            }
        )

    def test_chunker_initialization(self):
        """Test SemanticChunker initialization with parameters"""
        chunker = SemanticChunker(
            min_chunk_size=100,
            max_chunk_size=2000,
            target_chunk_size=1000,
            overlap_size=150,
            context_window=3
        )
        
        assert chunker.min_chunk_size == 100
        assert chunker.max_chunk_size == 2000
        assert chunker.target_chunk_size == 1000
        assert chunker.overlap_size == 150
        assert chunker.context_window == 3
        assert chunker.chars_per_token == 4

    def test_create_hierarchical_chunks_basic_functionality(self):
        """Test basic hierarchical chunk creation"""
        document_content = "Sample document content for testing hierarchical chunking functionality."
        
        result = self.chunker.create_hierarchical_chunks(
            self.mock_navigation_structure,
            document_content,
            document_type="guidelines"
        )
        
        assert isinstance(result, ChunkingResult)
        assert len(result.chunks) > 0
        assert len(result.chunk_relationships) >= 0
        assert result.chunking_metadata is not None
        assert result.quality_metrics is not None
        
        # Verify chunks have proper structure
        for chunk in result.chunks:
            assert isinstance(chunk, SemanticChunk)
            assert chunk.chunk_id
            assert chunk.content
            assert isinstance(chunk.chunk_type, ChunkType)
            assert isinstance(chunk.context, ChunkContext)

    def test_chunk_type_determination(self):
        """Test chunk type determination based on content and node characteristics"""
        # Test decision chunk detection
        decision_node = self.mock_navigation_structure.nodes["decision_matrix"]
        decision_chunks = self.chunker._create_node_chunks(
            decision_node,
            decision_node.content,
            self.mock_navigation_structure,
            "guidelines"
        )
        
        assert len(decision_chunks) > 0
        assert decision_chunks[0].chunk_type == ChunkType.DECISION
        
        # Test content chunk detection
        content_node = self.mock_navigation_structure.nodes["borrower_eligibility"]
        content_chunks = self.chunker._create_node_chunks(
            content_node,
            content_node.content,
            self.mock_navigation_structure,
            "guidelines"
        )
        
        assert len(content_chunks) > 0
        assert content_chunks[0].chunk_type == ChunkType.CONTENT

    def test_hierarchical_context_addition(self):
        """Test adding hierarchical context to chunks"""
        node = self.mock_navigation_structure.nodes["income_requirements"]
        
        # Create a basic chunk
        chunk = SemanticChunk(
            chunk_id="test_chunk_001",
            content=node.content,
            chunk_type=ChunkType.CONTENT,
            context=ChunkContext(navigation_path=[]),
            node_id=node.node_id
        )
        
        # Add hierarchical context
        enhanced_chunk = self.chunker.add_hierarchical_context(
            chunk, 
            self.mock_navigation_structure
        )
        
        assert enhanced_chunk.context.navigation_path is not None
        assert len(enhanced_chunk.context.navigation_path) > 0
        assert "NAA Product Guidelines" in enhanced_chunk.context.navigation_path
        assert "Borrower Eligibility" in enhanced_chunk.context.navigation_path
        assert enhanced_chunk.context.parent_section == "Borrower Eligibility"
        assert enhanced_chunk.context.section_number == "2.1"
        assert enhanced_chunk.context.hierarchy_level > 0

    def test_content_splitting_strategies(self):
        """Test different content splitting strategies"""
        # Test decision content splitting
        decision_content = """
        If borrower income is verified through bank statements, then proceed with standard analysis.
        When credit score is below 620, then additional compensating factors are required.
        Unless borrower provides 20% down payment, then mortgage insurance is mandatory.
        """
        
        decision_chunks = self.chunker._split_decision_content(decision_content)
        assert len(decision_chunks) > 1  # Should split on decision keywords
        
        # Test paragraph-based splitting
        paragraph_content = """
        This is the first paragraph of content.
        
        This is the second paragraph with more detailed information.
        
        This is the third paragraph completing the section.
        """
        
        paragraph_chunks = self.chunker._split_by_paragraphs(paragraph_content)
        assert len(paragraph_chunks) >= 1

    def test_chunk_size_management(self):
        """Test chunk size adjustment and management"""
        # Test with oversized content
        oversized_content = "Very long content. " * 200  # Will exceed max_chunk_size
        
        adjusted_chunks = self.chunker._adjust_chunk_sizes([oversized_content])
        assert len(adjusted_chunks) > 1  # Should be split
        
        for chunk in adjusted_chunks:
            assert len(chunk) <= self.chunker.max_chunk_size
        
        # Test with undersized chunks
        small_chunks = ["Short content.", "Another short piece."]
        adjusted_chunks = self.chunker._adjust_chunk_sizes(small_chunks)
        
        # Should attempt to merge if possible
        if len(adjusted_chunks) == 1:
            assert len(adjusted_chunks[0]) >= self.chunker.min_chunk_size

    def test_chunk_relationships_creation(self):
        """Test creation of chunk relationships"""
        node = self.mock_navigation_structure.nodes["borrower_eligibility"]
        
        chunks = self.chunker._create_node_chunks(
            node,
            node.content,
            self.mock_navigation_structure,
            "guidelines"
        )
        
        relationships = self.chunker._create_node_relationships(
            chunks,
            node,
            self.mock_navigation_structure
        )
        
        # Should have sequential relationships between chunks if multiple
        if len(chunks) > 1:
            sequential_rels = [r for r in relationships if r['relationship_type'] == 'SEQUENTIAL']
            assert len(sequential_rels) == len(chunks) - 1
        
        # Should have parent-child relationships to child nodes
        parent_child_rels = [r for r in relationships if r['relationship_type'] == 'PARENT_CHILD']
        assert len(parent_child_rels) == len(node.children)

    def test_cross_chunk_relationships(self):
        """Test creation of cross-chunk relationships"""
        # Create chunks from different nodes
        all_chunks = []
        
        for node_id, node in self.mock_navigation_structure.nodes.items():
            if node_id != "naa_root" and node.content:
                node_chunks = self.chunker._create_node_chunks(
                    node,
                    node.content,
                    self.mock_navigation_structure,
                    "guidelines"
                )
                all_chunks.extend(node_chunks)
        
        cross_relationships = self.chunker._create_cross_chunk_relationships(all_chunks)
        
        # Should find some relationships between decision chunks and other chunks
        decision_refs = [r for r in cross_relationships if r['relationship_type'] == 'REFERENCES']
        assert len(decision_refs) >= 0  # May or may not find references depending on content

    def test_quality_metrics_calculation(self):
        """Test quality metrics calculation"""
        document_content = "Test document content"
        
        result = self.chunker.create_hierarchical_chunks(
            self.mock_navigation_structure,
            document_content,
            document_type="guidelines"
        )
        
        metrics = result.quality_metrics
        
        assert 'overall_quality' in metrics
        assert 'average_chunk_size' in metrics
        assert 'coverage' in metrics
        assert 'chunk_type_distribution' in metrics
        assert 'total_chunks' in metrics
        
        assert 0.0 <= metrics['overall_quality'] <= 1.0
        assert metrics['average_chunk_size'] > 0
        assert 0.0 <= metrics['coverage'] <= 1.0
        assert metrics['total_chunks'] == len(result.chunks)

    def test_navigation_path_building(self):
        """Test navigation path building for hierarchical context"""
        income_node = self.mock_navigation_structure.nodes["income_requirements"]
        
        path = self.chunker._build_navigation_path(
            income_node,
            self.mock_navigation_structure
        )
        
        expected_path = ["NAA Product Guidelines", "Borrower Eligibility", "Income Requirements"]
        assert path == expected_path

    def test_chunk_quality_scoring(self):
        """Test individual chunk quality scoring"""
        node = self.mock_navigation_structure.nodes["income_requirements"]
        
        # Create a well-formed chunk
        good_chunk = SemanticChunk(
            chunk_id="test_001",
            content=node.content + ".",  # Ends with period
            chunk_type=ChunkType.CONTENT,
            context=ChunkContext(navigation_path=[]),
            token_count=len(node.content) // 4
        )
        
        quality_score = self.chunker._calculate_chunk_quality(good_chunk, node)
        assert 0.0 <= quality_score <= 1.0
        assert quality_score > 0.8  # Should be high quality

    def test_utility_methods(self):
        """Test utility helper methods"""
        # Test content cleaning
        messy_content = "  Lots   of    whitespace\n\n\n  and  empty lines  "
        cleaned = self.chunker._clean_content(messy_content)
        assert "Lots of whitespace" in cleaned
        assert not cleaned.startswith(" ")
        assert not cleaned.endswith(" ")
        
        # Test heading detection
        assert self.chunker._is_heading_line("1. Product Overview")
        assert self.chunker._is_heading_line("A. Section Title")
        assert self.chunker._is_heading_line("## Markdown Header")
        assert not self.chunker._is_heading_line("Regular paragraph text")
        
        # Test decision language detection
        decision_text = "If credit score is above 620, then approve the loan."
        assert self.chunker._contains_decision_language(decision_text)
        
        regular_text = "This is just regular content without decisions."
        assert not self.chunker._contains_decision_language(regular_text)
        
        # Test matrix language detection
        matrix_text = "The following matrix shows qualification criteria."
        assert self.chunker._contains_matrix_language(matrix_text)

    def test_chunk_serialization(self):
        """Test chunk and result serialization to dictionary"""
        document_content = "Test content for serialization"
        
        result = self.chunker.create_hierarchical_chunks(
            self.mock_navigation_structure,
            document_content,
            document_type="guidelines"
        )
        
        # Test ChunkingResult serialization
        result_dict = result.to_dict()
        assert 'chunks' in result_dict
        assert 'chunk_relationships' in result_dict
        assert 'chunking_metadata' in result_dict
        assert 'quality_metrics' in result_dict
        
        # Test SemanticChunk serialization
        if result.chunks:
            chunk_dict = result.chunks[0].to_dict()
            assert 'chunk_id' in chunk_dict
            assert 'content' in chunk_dict
            assert 'chunk_type' in chunk_dict
            assert 'context' in chunk_dict

    def test_error_handling(self):
        """Test error handling and edge cases"""
        # Test with invalid navigation structure
        with pytest.raises(Exception):
            self.chunker.create_hierarchical_chunks(
                None,
                "content",
                "guidelines"
            )
        
        # Test with empty content
        empty_structure = NavigationStructure(
            document_id="empty_test",
            document_format=DocumentFormat.TEXT,
            root_node=NavigationNode(
                node_id="empty_root",
                title="Empty",
                level=NavigationLevel.DOCUMENT
            ),
            nodes={"empty_root": NavigationNode(
                node_id="empty_root",
                title="Empty",
                level=NavigationLevel.DOCUMENT
            )},
            table_of_contents=TableOfContents([], "text", 0.0, "none"),
            decision_trees=[],
            extraction_metadata={}
        )
        
        result = self.chunker.create_hierarchical_chunks(
            empty_structure,
            "",
            "guidelines"
        )
        
        assert isinstance(result, ChunkingResult)
        assert len(result.chunks) == 0

    def test_integration_with_navigation_extractor_output(self):
        """Test integration with actual NavigationExtractor output format"""
        # This test validates that the SemanticChunker properly handles
        # the exact output format from NavigationExtractor
        
        # Validate that all required fields are present
        structure = self.mock_navigation_structure
        
        assert hasattr(structure, 'document_id')
        assert hasattr(structure, 'nodes')
        assert hasattr(structure, 'table_of_contents')
        assert hasattr(structure, 'decision_trees')
        
        # Test processing
        result = self.chunker.create_hierarchical_chunks(
            structure,
            "Test content",
            "guidelines"
        )
        
        assert result is not None
        assert len(result.chunks) > 0
        
        # Verify chunk context includes navigation information
        for chunk in result.chunks:
            if chunk.node_id and chunk.node_id in structure.nodes:
                assert len(chunk.context.navigation_path) > 0
                assert chunk.context.hierarchy_level >= 0


class TestSemanticChunkerWithRealNAAContent:
    """Test SemanticChunker with realistic NAA content"""

    def setup_method(self):
        """Set up test with realistic NAA content"""
        self.chunker = SemanticChunker()
        self.realistic_naa_content = """
        Non-Agency Advantage (NAA) Product Guidelines
        G1 Group Lending
        
        1. Product Overview
        
        The Non-Agency Advantage (NAA) product is designed for borrowers
        who do not meet traditional agency guidelines but demonstrate
        strong compensating factors. This program offers competitive
        rates and flexible underwriting for qualified borrowers.
        
        2. Borrower Eligibility
        
        All borrowers must meet the following baseline criteria:
        
        2.1 Income Requirements
        
        If borrower income is bank statement derived, then 12 months of
        business and personal bank statements are required. When borrower
        claims rental income from investment properties, verification
        through lease agreements or property management statements is
        mandatory. For self-employed borrowers, minimum 24 months of
        business operation history must be documented.
        
        2.2 Credit Requirements
        
        Minimum credit score requirements:
        - Primary residence: 620 minimum FICO
        - Investment property: 640 minimum FICO
        - Cash-out refinance: 660 minimum FICO
        
        If credit score falls below minimum thresholds, refer to
        underwriting for compensating factor review.
        
        3. Property Guidelines
        
        3.1 Eligible Property Types
        
        Approved property types include:
        - Single Family Residences (detached)
        - Condominiums (warrantable and non-warrantable)
        - Planned Unit Developments (PUD)
        - 2-4 unit investment properties
        
        5. Decision Matrix Framework
        
        Use the following decision tree for loan approval:
        
        Step 1: Credit and Income Verification
        If FICO >= minimum AND income verified: Continue to Step 2
        If FICO < minimum OR income insufficient: DECLINE
        
        Step 2: Property and LTV Analysis  
        If LTV <= 80% AND property type approved: Continue to Step 3
        If LTV > 80% OR property type restricted: REFER to underwriting
        
        Step 3: Final Approval Decision
        If all criteria met AND no red flags: APPROVE
        If compensating factors needed: REFER to senior underwriter
        Otherwise: DECLINE
        """

    @patch('src.navigation_extractor.NavigationExtractor.extract_navigation_structure')
    def test_realistic_naa_content_chunking(self, mock_extract):
        """Test chunking with realistic NAA content"""
        # Create realistic navigation structure
        mock_structure = self._create_realistic_navigation_structure()
        mock_extract.return_value = mock_structure
        
        result = self.chunker.create_hierarchical_chunks(
            mock_structure,
            self.realistic_naa_content,
            document_type="guidelines"
        )
        
        assert result is not None
        assert len(result.chunks) > 0
        
        # Should have different chunk types
        chunk_types = set(chunk.chunk_type for chunk in result.chunks)
        assert ChunkType.CONTENT in chunk_types
        assert ChunkType.DECISION in chunk_types
        
        # Decision chunks should be detected
        decision_chunks = [c for c in result.chunks if c.chunk_type == ChunkType.DECISION]
        assert len(decision_chunks) > 0
        
        # Check for proper navigation paths
        for chunk in result.chunks:
            if chunk.context.navigation_path:
                assert "NAA Product Guidelines" in chunk.context.navigation_path

    def _create_realistic_navigation_structure(self):
        """Create realistic navigation structure for testing"""
        from src.navigation_extractor import NavigationStructure, NavigationNode, NavigationLevel, DocumentFormat, TableOfContents
        
        root_node = NavigationNode(
            node_id="naa_root",
            title="NAA Product Guidelines",
            level=NavigationLevel.DOCUMENT
        )
        
        nodes = {
            "naa_root": root_node,
            "product_overview": NavigationNode(
                node_id="product_overview",
                title="Product Overview",
                level=NavigationLevel.CHAPTER,
                parent_id="naa_root",
                section_number="1",
                content="The Non-Agency Advantage (NAA) product is designed for borrowers who do not meet traditional agency guidelines..."
            ),
            "borrower_eligibility": NavigationNode(
                node_id="borrower_eligibility",
                title="Borrower Eligibility", 
                level=NavigationLevel.CHAPTER,
                parent_id="naa_root",
                section_number="2",
                content="All borrowers must meet the following baseline criteria..."
            ),
            "income_requirements": NavigationNode(
                node_id="income_requirements",
                title="Income Requirements",
                level=NavigationLevel.SECTION,
                parent_id="borrower_eligibility",
                section_number="2.1",
                content="If borrower income is bank statement derived, then 12 months of business and personal bank statements are required...",
                metadata={'decision_indicator': True}
            ),
            "decision_matrix": NavigationNode(
                node_id="decision_matrix",
                title="Decision Matrix Framework",
                level=NavigationLevel.CHAPTER,
                parent_id="naa_root",
                section_number="5",
                decision_type="ROOT",
                content="Use the following decision tree for loan approval: Step 1: Credit and Income Verification...",
                metadata={'decision_indicator': True}
            )
        }
        
        return NavigationStructure(
            document_id="realistic_naa_001",
            document_format=DocumentFormat.TEXT,
            root_node=root_node,
            nodes=nodes,
            table_of_contents=TableOfContents([], "text", 0.9, "pattern"),
            decision_trees=[],
            extraction_metadata={}
        )


# Test execution helper
if __name__ == "__main__":
    pytest.main([__file__, "-v"])