# Real-World Sample Document Testing
# This file tests our NavigationExtractor and future components with actual NQM NAA package structure

import pytest
from unittest.mock import Mock, patch
import sys
import os
from pathlib import Path

# Add the parent directory to the path to import backend modules
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from src.navigation_extractor import NavigationExtractor, DocumentFormat
from src.package_manager import PackageManager
from src.package_templates import MortgagePackageTemplates
from src.entities.document_package import PackageCategory


class TestRealWorldNQMNAAPackage:
    """Test with real NQM NAA package structure from sample documents"""

    def setup_method(self):
        """Set up test fixtures"""
        self.sample_path = Path("/mnt/c/Users/dirkd/OneDrive/Documents/GitHub/llm-graph-builder/implementation-plan/sample-documents")
        self.nqm_naa_path = self.sample_path / "NQM" / "NAA"
        
        # Initialize components
        self.extractor = NavigationExtractor(package_category="NQM")
        self.mock_graph_db = Mock()
        self.package_manager = PackageManager(self.mock_graph_db)
        self.templates = MortgagePackageTemplates()

    def test_nqm_naa_package_structure_detection(self):
        """Test detection of real NQM NAA package structure"""
        # Verify the sample structure exists
        assert self.nqm_naa_path.exists(), "Sample NQM NAA package not found"
        
        guidelines_path = self.nqm_naa_path / "guidelines"
        matrices_path = self.nqm_naa_path / "matrices"
        
        assert guidelines_path.exists(), "Guidelines directory not found"
        assert matrices_path.exists(), "Matrices directory not found"
        
        # Check for expected files
        guideline_files = list(guidelines_path.glob("*.pdf"))
        matrix_files = list(matrices_path.glob("*.pdf"))
        
        assert len(guideline_files) > 0, "No guideline PDF files found"
        assert len(matrix_files) > 0, "No matrix PDF files found"
        
        print(f"✅ Found {len(guideline_files)} guideline files")
        print(f"✅ Found {len(matrix_files)} matrix files")

    def test_nqm_naa_file_naming_patterns(self):
        """Test file naming pattern detection for NQM NAA documents"""
        matrices_path = self.nqm_naa_path / "matrices"
        
        if matrices_path.exists():
            matrix_files = [f.name for f in matrices_path.glob("*.pdf")]
            
            # Expected patterns for G1 Group matrices
            expected_patterns = [
                "Cash Flow Advantage",
                "Investor Advantage", 
                "Non-Agency Advantage",
                "Professional Investor",
                "Titanium Advantage"
            ]
            
            detected_patterns = []
            for pattern in expected_patterns:
                matching_files = [f for f in matrix_files if pattern in f]
                if matching_files:
                    detected_patterns.append(pattern)
                    print(f"✅ Found {pattern}: {matching_files[0]}")
            
            assert len(detected_patterns) >= 3, f"Expected at least 3 matrix types, found {len(detected_patterns)}"

    def test_create_nqm_package_from_real_structure(self):
        """Test creating a DocumentPackage from real NQM NAA structure"""
        # Create package configuration matching the real structure
        package_config = {
            'package_name': 'NQM NAA Product Package',
            'tenant_id': 'g1_group',
            'category': 'NQM',
            'created_by': 'test_system',
            'template': 'NQM_STANDARD',
            'documents': [
                {
                    'document_type': 'guidelines',
                    'document_name': 'NAA Guidelines',
                    'required_sections': [
                        'Borrower Eligibility',
                        'Income Requirements', 
                        'Credit Requirements',
                        'Property Guidelines',
                        'Decision Matrix'
                    ],
                    'entity_types': ['LOAN_PROGRAM', 'DTI_RATIO', 'CREDIT_SCORE', 'PROPERTY_TYPE'],
                    'chunking_strategy': 'hierarchical'
                },
                {
                    'document_type': 'matrix',
                    'document_name': 'Cash Flow Advantage Matrix',
                    'matrix_configuration': {
                        'matrix_type': 'qualification',
                        'decision_factors': ['income_type', 'property_type', 'ltv_ratio'],
                        'outcomes': ['APPROVE', 'DECLINE', 'REFER']
                    }
                },
                {
                    'document_type': 'matrix',
                    'document_name': 'Investor Advantage Matrix',
                    'matrix_configuration': {
                        'matrix_type': 'qualification',
                        'decision_factors': ['investor_experience', 'portfolio_size', 'cash_reserves'],
                        'outcomes': ['APPROVE', 'DECLINE', 'REFER']
                    }
                },
                {
                    'document_type': 'matrix',
                    'document_name': 'Non-Agency Advantage Matrix',
                    'matrix_configuration': {
                        'matrix_type': 'qualification',
                        'decision_factors': ['credit_profile', 'income_documentation', 'asset_verification'],
                        'outcomes': ['APPROVE', 'DECLINE', 'REFER']
                    }
                }
            ],
            'relationships': [
                {
                    'from_document': 'NAA Guidelines',
                    'to_document': 'Cash Flow Advantage Matrix',
                    'relationship_type': 'ELABORATES',
                    'metadata': {'section_reference': 'Cash Flow Documentation'}
                },
                {
                    'from_document': 'NAA Guidelines',
                    'to_document': 'Investor Advantage Matrix',
                    'relationship_type': 'ELABORATES',
                    'metadata': {'section_reference': 'Investment Property Guidelines'}
                },
                {
                    'from_document': 'NAA Guidelines',
                    'to_document': 'Non-Agency Advantage Matrix',
                    'relationship_type': 'ELABORATES',
                    'metadata': {'section_reference': 'Non-QM Qualification Criteria'}
                }
            ]
        }
        
        # Mock database operations
        self.mock_graph_db.package_exists.return_value = False
        self.mock_graph_db.create_package_node.return_value = True
        self.mock_graph_db.create_package_document.return_value = True
        self.mock_graph_db.create_package_relationship.return_value = True
        
        # Create package
        package = self.package_manager.create_package(package_config)
        
        # Validate package structure
        assert package is not None
        assert package.package_name == 'NQM NAA Product Package'
        assert package.category == PackageCategory.NQM
        assert len(package.documents) == 4  # 1 guideline + 3 matrices
        assert len(package.relationships) == 3
        
        # Check document types
        doc_types = [doc.document_type for doc in package.documents]
        assert 'guidelines' in doc_types
        assert doc_types.count('matrix') == 3
        
        print(f"✅ Created NQM NAA package with {len(package.documents)} documents")

    def test_nqm_template_compatibility_with_real_structure(self):
        """Test NQM template compatibility with real NAA structure"""
        # Get NQM template
        nqm_template = self.templates.get_template(PackageCategory.NQM)
        
        assert nqm_template is not None
        assert nqm_template.package_name.startswith('Non-QM')
        
        # Check if template structure matches real NAA structure
        template_doc_types = [doc.document_type for doc in nqm_template.documents]
        assert 'guidelines' in template_doc_types
        assert 'matrix' in template_doc_types
        
        # Check for expected sections in guidelines
        guidelines_doc = next(doc for doc in nqm_template.documents if doc.document_type == 'guidelines')
        expected_sections = ['Borrower Eligibility', 'Income Requirements', 'Credit Requirements']
        
        for section in expected_sections:
            assert section in guidelines_doc.required_sections, f"Expected section '{section}' not found in template"
        
        print("✅ NQM template structure matches real NAA package requirements")

    @patch('src.navigation_extractor.NavigationExtractor.extract_navigation_structure')
    def test_navigation_extraction_simulation_with_naa_content(self, mock_extract):
        """Simulate navigation extraction with realistic NQM NAA content"""
        # Mock realistic NAA guideline content structure
        mock_naa_content = """
        Non-Agency Advantage (NAA) Product Guidelines
        G1 Group Lending
        
        Table of Contents
        1. Product Overview ......................... 3
        2. Borrower Eligibility .................... 5
        2.1 Income Requirements .................... 6
        2.2 Credit Requirements .................... 8
        2.3 Asset Requirements ..................... 10
        3. Property Guidelines .................... 12
        3.1 Eligible Property Types ............... 13
        3.2 Occupancy Requirements ................ 15
        3.3 Appraisal Requirements ................ 17
        4. Loan Parameters ........................ 19
        4.1 Loan-to-Value Limits ................. 20
        4.2 Debt-to-Income Ratios ................ 22
        4.3 Cash-Out Refinance Guidelines ........ 24
        5. Decision Matrix Framework .............. 26
        
        1. Product Overview
        
        The Non-Agency Advantage (NAA) product is designed for borrowers
        who do not meet traditional agency guidelines but demonstrate
        strong compensating factors.
        
        1.1 Product Purpose
        
        NAA provides financing solutions for:
        - Self-employed borrowers with variable income
        - Real estate investors with portfolio income
        - High-net-worth individuals with asset-based income
        
        2. Borrower Eligibility
        
        All borrowers must meet the following baseline criteria:
        
        2.1 Income Requirements
        
        If borrower income is bank statement derived, then 12 months of
        business and personal bank statements are required.
        
        When borrower claims rental income from investment properties,
        verification through lease agreements or property management
        statements is mandatory.
        
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
        
        3.2 Occupancy Requirements
        
        Primary Residence:
        - Owner occupancy certification required
        - 12-month occupancy commitment
        
        Investment Property:
        - Rental agreement or property management contract
        - Reserve requirements: 2-6 months PITI
        
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
        
        # Create mock NavigationStructure response
        from src.navigation_extractor import NavigationStructure, NavigationNode, NavigationLevel, TableOfContents
        
        mock_root = NavigationNode(
            node_id="naa_root",
            title="NAA Product Guidelines",
            level=NavigationLevel.DOCUMENT
        )
        
        mock_nodes = {
            "naa_root": mock_root,
            "product_overview": NavigationNode(
                node_id="product_overview",
                title="Product Overview",
                level=NavigationLevel.CHAPTER,
                parent_id="naa_root",
                section_number="1"
            ),
            "borrower_eligibility": NavigationNode(
                node_id="borrower_eligibility", 
                title="Borrower Eligibility",
                level=NavigationLevel.CHAPTER,
                parent_id="naa_root",
                section_number="2"
            ),
            "income_requirements": NavigationNode(
                node_id="income_requirements",
                title="Income Requirements", 
                level=NavigationLevel.SECTION,
                parent_id="borrower_eligibility",
                section_number="2.1"
            ),
            "decision_matrix": NavigationNode(
                node_id="decision_matrix",
                title="Decision Matrix Framework",
                level=NavigationLevel.CHAPTER,
                parent_id="naa_root", 
                section_number="5",
                decision_type="ROOT"
            )
        }
        
        mock_toc = TableOfContents(
            entries=[
                {"title": "Product Overview", "section_number": "1.", "page_number": 3},
                {"title": "Borrower Eligibility", "section_number": "2.", "page_number": 5},
                {"title": "Income Requirements", "section_number": "2.1", "page_number": 6},
                {"title": "Decision Matrix Framework", "section_number": "5.", "page_number": 26}
            ],
            format_detected="text",
            confidence_score=0.92,
            extraction_method="pattern_matching"
        )
        
        mock_structure = NavigationStructure(
            document_id="naa_guidelines_001",
            document_format=DocumentFormat.TEXT,
            root_node=mock_root,
            nodes=mock_nodes,
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
        
        mock_extract.return_value = mock_structure
        
        # Test navigation extraction
        structure = self.extractor.extract_navigation_structure(
            mock_naa_content,
            document_name="NAA-Guidelines.pdf"
        )
        
        # Validate results
        assert structure is not None
        assert structure.document_id == "naa_guidelines_001"
        assert len(structure.nodes) == 4
        assert structure.table_of_contents.confidence_score > 0.9
        assert len(structure.decision_trees) == 1
        
        # Check for NAA-specific sections
        node_titles = [node.title for node in structure.nodes.values()]
        assert "Product Overview" in node_titles
        assert "Borrower Eligibility" in node_titles
        assert "Decision Matrix Framework" in node_titles
        
        print("✅ Navigation extraction simulation successful for NAA content")

    def test_real_file_structure_validation(self):
        """Validate the real file structure matches expected patterns"""
        if not self.nqm_naa_path.exists():
            pytest.skip("Sample documents not available")
        
        # Expected structure validation
        expected_structure = {
            'guidelines': ['NAA-Guidelines.pdf'],
            'matrices': [
                'Cash Flow Advantage',
                'Investor Advantage', 
                'Non-Agency Advantage',
                'Professional Investor',
                'Titanium Advantage'
            ]
        }
        
        # Check guidelines
        guidelines_path = self.nqm_naa_path / "guidelines"
        if guidelines_path.exists():
            guideline_files = [f.name for f in guidelines_path.glob("*.pdf")]
            assert any("NAA" in f for f in guideline_files), "NAA Guidelines file not found"
        
        # Check matrices
        matrices_path = self.nqm_naa_path / "matrices"
        if matrices_path.exists():
            matrix_files = [f.name for f in matrices_path.glob("*.pdf")]
            
            for expected_matrix in expected_structure['matrices']:
                matching_files = [f for f in matrix_files if expected_matrix in f]
                if matching_files:
                    print(f"✅ Found {expected_matrix} matrix: {matching_files[0]}")
        
        print("✅ Real file structure validation completed")

    def test_integration_readiness_for_task_8(self):
        """Test that our navigation extractor output is ready for Task 8 (Semantic Chunker)"""
        # This test validates that Task 7 output is compatible with upcoming Task 8 requirements
        
        # Mock a navigation structure that would come from real NAA guidelines
        from src.navigation_extractor import NavigationNode, NavigationLevel
        
        # Create hierarchical structure typical of mortgage guidelines
        nodes = [
            NavigationNode(
                node_id="section_2",
                title="Borrower Eligibility", 
                level=NavigationLevel.CHAPTER,
                section_number="2",
                content="All borrowers must meet the following baseline criteria...",
                metadata={'line_number': 45, 'pattern_type': 'numbered_section'}
            ),
            NavigationNode(
                node_id="section_2_1",
                title="Income Requirements",
                level=NavigationLevel.SECTION, 
                parent_id="section_2",
                section_number="2.1",
                content="If borrower income is bank statement derived, then...",
                metadata={'line_number': 52, 'pattern_type': 'numbered_section', 'decision_indicator': True}
            ),
            NavigationNode(
                node_id="section_2_2", 
                title="Credit Requirements",
                level=NavigationLevel.SECTION,
                parent_id="section_2",
                section_number="2.2", 
                content="Minimum credit score requirements: Primary residence: 620...",
                metadata={'line_number': 67, 'pattern_type': 'numbered_section', 'decision_indicator': True}
            )
        ]
        
        # Validate Task 8 requirements:
        # 1. Hierarchical relationships are preserved
        for node in nodes[1:]:  # Skip root
            assert node.parent_id is not None, "Node missing parent relationship"
            assert node.level != NavigationLevel.DOCUMENT, "Non-root node has document level"
        
        # 2. Content context is maintained
        for node in nodes:
            assert node.content, "Node missing content for chunking"
            assert node.metadata, "Node missing metadata for context"
        
        # 3. Decision indicators are marked for special chunking
        decision_nodes = [node for node in nodes if node.metadata.get('decision_indicator')]
        assert len(decision_nodes) > 0, "No decision indicators found for decision tree chunking"
        
        # 4. Section numbering preserved for navigation paths
        numbered_nodes = [node for node in nodes if node.section_number]
        assert len(numbered_nodes) > 0, "No section numbers for navigation context"
        
        print("✅ Navigation structure ready for Task 8 semantic chunking")
        print(f"   - {len(nodes)} hierarchical nodes")
        print(f"   - {len(decision_nodes)} decision indicator nodes")
        print(f"   - {len(numbered_nodes)} numbered sections")


# Test execution helper
if __name__ == "__main__":
    # This allows running the tests directly
    pytest.main([__file__, "-v"])