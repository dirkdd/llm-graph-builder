# Task 7: Navigation Extractor Tests
# This file contains comprehensive tests for the NavigationExtractor implementation

import pytest
from unittest.mock import Mock, patch
import sys
import os
from datetime import datetime

# Add the parent directory to the path to import backend modules
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from src.navigation_extractor import (
    NavigationExtractor,
    NavigationNode,
    NavigationStructure,
    TableOfContents,
    DocumentFormat,
    NavigationLevel
)


class TestNavigationExtractor:
    """Test NavigationExtractor functionality"""

    def setup_method(self):
        """Set up test fixtures"""
        self.extractor = NavigationExtractor(package_category="NQM")
        
        # Sample mortgage document content
        self.sample_nqm_content = """
        Non-QM Mortgage Guidelines
        
        Table of Contents
        1. Introduction ............................ 3
        2. Borrower Eligibility ................... 5
        2.1 Income Requirements .................... 6
        2.2 Credit Requirements .................... 8
        3. Property Requirements .................. 10
        3.1 Property Types ........................ 11
        3.2 Occupancy Requirements ................ 12
        4. Decision Matrix ........................ 15
        
        1. Introduction
        
        This document outlines the Non-Qualified Mortgage (Non-QM) guidelines
        for residential mortgage lending.
        
        1.1 Purpose and Scope
        
        These guidelines apply to all Non-QM loan products offered by the institution.
        
        2. Borrower Eligibility
        
        All borrowers must meet the following criteria:
        
        2.1 Income Requirements
        
        If the borrower's debt-to-income ratio exceeds 43%, then additional
        documentation is required.
        
        When bank statements are used for income verification, the borrower
        must provide 12 months of statements.
        
        2.2 Credit Requirements
        
        Credit score must be 620 or higher for approval.
        If credit score is below 620, decline the application.
        
        3. Property Requirements
        
        3.1 Property Types
        
        Eligible property types include:
        - Single family residences
        - Condominiums
        - Townhomes
        
        3.2 Occupancy Requirements
        
        Primary residence loans require owner occupancy certification.
        
        4. Decision Matrix
        
        Use the following decision tree:
        
        If DTI <= 43% and Credit >= 620: APPROVE
        If DTI > 43% and Credit >= 680: REFER to underwriter
        Otherwise: DECLINE
        """
        
        # Sample table of contents content
        self.sample_toc_content = """
        Table of Contents
        
        1. Introduction ............................ 3
        2. Borrower Requirements ................... 5
        2.1 Income Verification ................... 6
        2.2 Credit Analysis ....................... 8
        3. Property Guidelines .................... 10
        3.1 Eligible Properties .................. 11
        3.2 Appraisal Requirements ............... 13
        4. Underwriting Matrix ................... 15
        """

    def test_initialization(self):
        """Test NavigationExtractor initialization"""
        extractor = NavigationExtractor(package_category="RTL")
        assert extractor.package_category == "RTL"
        assert extractor.llm_client is None
        assert len(extractor.heading_patterns) > 0
        assert len(extractor.format_indicators) > 0

    def test_detect_heading_patterns(self):
        """Test heading pattern detection"""
        headings = self.extractor.detect_heading_patterns(self.sample_nqm_content)
        
        assert len(headings) > 0
        
        # Check for main sections
        section_titles = [h['title'] for h in headings if h['pattern_type'] == 'numbered_section']
        assert 'Introduction' in section_titles
        assert 'Borrower Eligibility' in section_titles
        assert 'Property Requirements' in section_titles
        
        # Check for subsections
        subsection_numbers = [h['section_number'] for h in headings if h.get('section_number')]
        assert '2.1' in subsection_numbers
        assert '2.2' in subsection_numbers
        assert '3.1' in subsection_numbers
        
        # Check for decision indicators
        decision_headings = [h for h in headings if h.get('decision_indicator')]
        assert len(decision_headings) > 0

    def test_detect_numbered_sections(self):
        """Test detection of numbered sections"""
        test_content = """
        1. First Section
        1.1 First Subsection
        1.1.1 First Sub-subsection
        2. Second Section
        A.1 Appendix Section
        """
        
        headings = self.extractor.detect_heading_patterns(test_content)
        
        # Should detect all numbered sections
        numbered_headings = [h for h in headings if h['pattern_type'] == 'numbered_section']
        assert len(numbered_headings) == 5
        
        # Check section numbers
        section_numbers = [h['section_number'] for h in numbered_headings]
        assert '1' in section_numbers
        assert '1.1' in section_numbers
        assert '1.1.1' in section_numbers
        assert '2' in section_numbers
        assert 'A.1' in section_numbers

    def test_detect_decision_indicators(self):
        """Test detection of decision-making language"""
        test_content = """
        If the borrower meets all requirements, approve the loan.
        When credit score is below 620, decline immediately.
        Borrowers must provide documentation.
        The loan shall be referred to underwriting.
        """
        
        headings = self.extractor.detect_heading_patterns(test_content)
        decision_headings = [h for h in headings if h.get('decision_indicator')]
        
        assert len(decision_headings) >= 3
        
        # Check for key decision words
        decision_text = ' '.join(h['title'] for h in decision_headings)
        assert 'approve' in decision_text.lower()
        assert 'decline' in decision_text.lower()
        assert 'must' in decision_text.lower()

    def test_extract_table_of_contents(self):
        """Test table of contents extraction"""
        toc = self.extractor.extract_table_of_contents(self.sample_toc_content, DocumentFormat.TEXT)
        
        assert toc is not None
        assert len(toc.entries) > 0
        assert toc.format_detected == DocumentFormat.TEXT.value
        assert toc.confidence_score > 0.0
        
        # Check entries
        entry_titles = [entry['title'] for entry in toc.entries]
        assert 'Introduction' in entry_titles
        assert 'Borrower Requirements' in entry_titles
        assert 'Property Guidelines' in entry_titles
        
        # Check section numbers
        section_numbers = [entry['section_number'] for entry in toc.entries if entry.get('section_number')]
        assert '1.' in section_numbers
        assert '2.1' in section_numbers
        assert '3.2' in section_numbers

    def test_extract_table_of_contents_no_toc(self):
        """Test TOC extraction when no TOC is present"""
        content_without_toc = """
        Some regular document content without a table of contents.
        Just regular paragraphs and text.
        """
        
        toc = self.extractor.extract_table_of_contents(content_without_toc, DocumentFormat.TEXT)
        assert toc is None

    def test_document_format_detection(self):
        """Test document format detection"""
        # Test HTML detection
        html_content = "<html><body><h1>Title</h1></body></html>"
        format_detected = self.extractor._detect_document_format(html_content)
        assert format_detected == DocumentFormat.HTML
        
        # Test with format hint
        format_with_hint = self.extractor._detect_document_format("content", "pdf")
        assert format_with_hint == DocumentFormat.PDF
        
        # Test default (text)
        text_content = "Regular text content"
        format_default = self.extractor._detect_document_format(text_content)
        assert format_default == DocumentFormat.TEXT

    def test_extract_navigation_structure(self):
        """Test complete navigation structure extraction"""
        structure = self.extractor.extract_navigation_structure(
            self.sample_nqm_content,
            document_name="test_nqm_guidelines.txt"
        )
        
        assert structure is not None
        assert structure.document_format == DocumentFormat.TEXT
        assert structure.root_node is not None
        assert len(structure.nodes) > 1
        
        # Check root node
        assert structure.root_node.level == NavigationLevel.DOCUMENT
        assert structure.root_node.title == "Document Root"
        assert len(structure.root_node.children) > 0
        
        # Check for main sections
        node_titles = [node.title for node in structure.nodes.values()]
        assert 'Introduction' in node_titles
        assert 'Borrower Eligibility' in node_titles
        
        # Check table of contents
        assert structure.table_of_contents is not None
        assert len(structure.table_of_contents.entries) > 0
        
        # Check decision trees
        assert len(structure.decision_trees) > 0
        
        # Check metadata
        assert structure.extraction_metadata['document_name'] == "test_nqm_guidelines.txt"
        assert structure.extraction_metadata['package_category'] == "NQM"
        assert structure.extraction_metadata['total_nodes'] > 0

    def test_build_navigation_tree(self):
        """Test navigation tree building"""
        # Create sample nodes
        nodes = [
            NavigationNode(
                node_id="node_001",
                title="Section 1",
                level=NavigationLevel.SECTION,
                metadata={'line_number': 10}
            ),
            NavigationNode(
                node_id="node_002", 
                title="Section 1.1",
                level=NavigationLevel.SUBSECTION,
                metadata={'line_number': 15}
            ),
            NavigationNode(
                node_id="node_003",
                title="Section 2",
                level=NavigationLevel.SECTION,
                metadata={'line_number': 25}
            )
        ]
        
        root_node, node_dict = self.extractor._build_navigation_tree(nodes, "test_doc")
        
        # Check root node
        assert root_node.level == NavigationLevel.DOCUMENT
        assert len(root_node.children) == 2  # Two main sections
        
        # Check parent-child relationships
        section1 = node_dict["node_001"]
        section1_1 = node_dict["node_002"]
        section2 = node_dict["node_003"]
        
        assert section1.parent_id == root_node.node_id
        assert section1_1.parent_id == section1.node_id
        assert section2.parent_id == root_node.node_id
        assert len(section1.children) == 1
        assert section1.children[0] == section1_1.node_id

    def test_validate_navigation_structure(self):
        """Test navigation structure validation"""
        # Create a test structure
        root_node = NavigationNode(
            node_id="root",
            title="Document Root",
            level=NavigationLevel.DOCUMENT
        )
        
        section_node = NavigationNode(
            node_id="section1",
            title="Section 1",
            level=NavigationLevel.SECTION,
            parent_id="root"
        )
        
        root_node.children = ["section1"]
        
        structure = NavigationStructure(
            document_id="test_doc",
            document_format=DocumentFormat.TEXT,
            root_node=root_node,
            nodes={"root": root_node, "section1": section_node},
            decision_trees=[],
            table_of_contents=TableOfContents(
                entries=[{"title": "Section 1", "section_number": "1."}],
                format_detected="text",
                confidence_score=0.8,
                extraction_method="text_parsing"
            )
        )
        
        validation_results = self.extractor.validate_navigation_structure(structure)
        
        assert validation_results['is_valid'] is True
        assert 'quality_metrics' in validation_results
        assert validation_results['completeness_score'] > 0.0
        assert validation_results['structure_score'] > 0.0

    def test_validate_structure_with_issues(self):
        """Test validation with structural issues"""
        # Create structure with orphaned node
        root_node = NavigationNode(
            node_id="root",
            title="Document Root", 
            level=NavigationLevel.DOCUMENT
        )
        
        orphaned_node = NavigationNode(
            node_id="orphan",
            title="Orphaned Section",
            level=NavigationLevel.SECTION,
            parent_id="nonexistent_parent"
        )
        
        structure = NavigationStructure(
            document_id="test_doc",
            document_format=DocumentFormat.TEXT,
            root_node=root_node,
            nodes={"root": root_node, "orphan": orphaned_node}
        )
        
        validation_results = self.extractor.validate_navigation_structure(structure)
        
        assert len(validation_results['warnings']) > 0
        assert any('orphaned' in warning.lower() for warning in validation_results['warnings'])

    def test_heading_level_determination(self):
        """Test heading level determination from section numbers"""
        # Test different section number formats
        assert self.extractor._determine_heading_level("1") == NavigationLevel.CHAPTER
        assert self.extractor._determine_heading_level("1.1") == NavigationLevel.SECTION
        assert self.extractor._determine_heading_level("1.1.1") == NavigationLevel.SUBSECTION
        assert self.extractor._determine_heading_level("1.1.1.1") == NavigationLevel.PARAGRAPH

    def test_document_id_generation(self):
        """Test document ID generation"""
        doc_id1 = self.extractor._generate_document_id("test.txt", "content")
        doc_id2 = self.extractor._generate_document_id("test.txt", "different content")
        doc_id3 = self.extractor._generate_document_id(None, "content")
        
        assert doc_id1 != doc_id2  # Different content should give different IDs
        assert "test.txt" in doc_id1
        assert "doc_" in doc_id3  # Default prefix for unnamed documents
        assert len(doc_id1.split('_')) >= 3  # Should have name, length, and hash

    def test_decision_tree_extraction(self):
        """Test decision tree extraction"""
        decision_content = """
        2.1 Credit Requirements
        
        If credit score is 620 or higher, then approve the loan.
        When credit score is between 580-619, refer to underwriter.
        If credit score is below 580, decline the application.
        """
        
        headings = self.extractor.detect_heading_patterns(decision_content)
        decision_trees = self.extractor._extract_decision_trees(decision_content, headings)
        
        assert len(decision_trees) > 0
        
        # Check for decision tree structure
        for tree in decision_trees:
            assert 'root_node_id' in tree
            assert 'decision_type' in tree
            assert tree['decision_type'] == 'conditional'

    def test_toc_confidence_calculation(self):
        """Test table of contents confidence calculation"""
        # High confidence entries (with page numbers and section numbers)
        high_confidence_entries = [
            {'title': 'Introduction', 'section_number': '1.', 'page_number': 3},
            {'title': 'Requirements', 'section_number': '2.', 'page_number': 5},
            {'title': 'Guidelines', 'section_number': '3.', 'page_number': 8}
        ]
        
        # Low confidence entries (minimal information)
        low_confidence_entries = [
            {'title': 'Some Section'},
            {'title': 'Another Section'}
        ]
        
        high_score = self.extractor._calculate_toc_confidence(high_confidence_entries)
        low_score = self.extractor._calculate_toc_confidence(low_confidence_entries)
        empty_score = self.extractor._calculate_toc_confidence([])
        
        assert high_score > low_score > empty_score
        assert 0.0 <= high_score <= 1.0
        assert 0.0 <= low_score <= 1.0
        assert empty_score == 0.0

    def test_mortgage_specific_patterns(self):
        """Test detection of mortgage-specific content patterns"""
        mortgage_content = """
        Loan-to-Value Requirements
        
        If LTV exceeds 80%, mortgage insurance is required.
        When DTI ratio is above 43%, additional documentation must be provided.
        Borrowers with credit scores below 620 are ineligible.
        Property must be owner-occupied for primary residence loans.
        """
        
        headings = self.extractor.detect_heading_patterns(mortgage_content)
        
        # Check for mortgage-specific terms in decision indicators
        decision_headings = [h for h in headings if h.get('decision_indicator')]
        decision_text = ' '.join(h['title'].lower() for h in decision_headings)
        
        # Should detect mortgage-specific terms
        mortgage_terms = ['ltv', 'dti', 'credit score', 'mortgage insurance', 'owner-occupied']
        detected_terms = [term for term in mortgage_terms if term in decision_text]
        
        assert len(detected_terms) > 0

    def test_extraction_with_package_category(self):
        """Test extraction with different package categories"""
        rtl_extractor = NavigationExtractor(package_category="RTL")
        structure = rtl_extractor.extract_navigation_structure(
            self.sample_nqm_content,
            document_name="rtl_guidelines.txt"
        )
        
        assert structure.extraction_metadata['package_category'] == "RTL"

    def test_error_handling(self):
        """Test error handling for malformed content"""
        # Test with empty content
        with pytest.raises(Exception):
            self.extractor.extract_navigation_structure("")
        
        # Test with None content
        with pytest.raises(Exception):
            self.extractor.extract_navigation_structure(None)

    def test_navigation_node_serialization(self):
        """Test NavigationNode serialization and deserialization"""
        node = NavigationNode(
            node_id="test_node",
            title="Test Node",
            level=NavigationLevel.SECTION,
            parent_id="parent_node",
            children=["child1", "child2"],
            content="Test content",
            section_number="1.1",
            confidence_score=0.95,
            metadata={'test': 'data'}
        )
        
        # Test serialization
        node_dict = node.to_dict()
        assert node_dict['node_id'] == "test_node"
        assert node_dict['level'] == NavigationLevel.SECTION.value
        assert node_dict['children'] == ["child1", "child2"]
        
        # Test deserialization
        restored_node = NavigationNode.from_dict(node_dict)
        assert restored_node.node_id == node.node_id
        assert restored_node.level == node.level
        assert restored_node.children == node.children

    def test_navigation_structure_serialization(self):
        """Test NavigationStructure serialization"""
        root_node = NavigationNode(
            node_id="root",
            title="Document Root",
            level=NavigationLevel.DOCUMENT
        )
        
        structure = NavigationStructure(
            document_id="test_doc",
            document_format=DocumentFormat.TEXT,
            root_node=root_node,
            nodes={"root": root_node}
        )
        
        structure_dict = structure.to_dict()
        
        assert structure_dict['document_id'] == "test_doc"
        assert structure_dict['document_format'] == DocumentFormat.TEXT.value
        assert structure_dict['root_node']['node_id'] == "root"
        assert 'root' in structure_dict['nodes']


class TestNavigationDataModels:
    """Test navigation data models"""

    def test_navigation_node_creation(self):
        """Test NavigationNode creation and defaults"""
        node = NavigationNode(
            node_id="test",
            title="Test Node",
            level=NavigationLevel.SECTION
        )
        
        assert node.node_id == "test"
        assert node.title == "Test Node"
        assert node.level == NavigationLevel.SECTION
        assert node.children == []
        assert node.extracted_entities == []
        assert node.metadata == {}

    def test_table_of_contents_creation(self):
        """Test TableOfContents creation"""
        entries = [
            {'title': 'Section 1', 'page': 1},
            {'title': 'Section 2', 'page': 5}
        ]
        
        toc = TableOfContents(
            entries=entries,
            format_detected="text",
            confidence_score=0.85,
            extraction_method="pattern_matching"
        )
        
        assert len(toc.entries) == 2
        assert toc.confidence_score == 0.85
        assert toc.extraction_method == "pattern_matching"

    def test_navigation_structure_creation(self):
        """Test NavigationStructure creation with defaults"""
        root_node = NavigationNode(
            node_id="root",
            title="Root",
            level=NavigationLevel.DOCUMENT
        )
        
        structure = NavigationStructure(
            document_id="test",
            document_format=DocumentFormat.TEXT,
            root_node=root_node,
            nodes={"root": root_node}
        )
        
        assert structure.document_id == "test"
        assert structure.document_format == DocumentFormat.TEXT
        assert structure.decision_trees == []
        assert structure.extraction_metadata == {}
        assert structure.validation_results == {}


# Test execution helper
if __name__ == "__main__":
    # This allows running the tests directly
    pytest.main([__file__, "-v"])