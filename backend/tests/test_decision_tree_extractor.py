# Task 13: Decision Tree Extractor Tests
# Comprehensive tests for DecisionTreeExtractor class

import unittest
from unittest.mock import Mock, MagicMock, patch
from datetime import datetime
from typing import List, Dict, Any
import json

# Import the classes being tested
from src.decision_tree_extractor import (
    DecisionTreeExtractor,
    DecisionTreeExtractionResult,
    DecisionPath,
    DecisionTreeMetrics
)

# Import dependencies
from src.entities.navigation_models import (
    DecisionTreeNode,
    DecisionOutcome,
    NavigationContext,
    EnhancedNavigationNode,
    QualityRating
)
from src.navigation_extractor import NavigationLevel


class TestDecisionTreeExtractor(unittest.TestCase):
    """Test suite for DecisionTreeExtractor class"""
    
    def setUp(self):
        """Set up test fixtures"""
        # Mock LLM
        self.mock_llm = Mock()
        
        # Initialize DecisionTreeExtractor with mocked LLM
        with patch('src.decision_tree_extractor.get_llm', return_value=self.mock_llm):
            self.extractor = DecisionTreeExtractor()
        
        # Sample test data
        self.sample_navigation_nodes = self._create_sample_navigation_nodes()
        self.sample_document_content = self._create_sample_document_content()

    def _create_sample_navigation_nodes(self) -> List[EnhancedNavigationNode]:
        """Create sample navigation nodes with decision content"""
        return [
            EnhancedNavigationNode(
                node_id="nav_decision_001",
                level=NavigationLevel.SECTION,
                title="Borrower Eligibility Decision",
                content="""
                Borrower Eligibility Decision Process:
                
                IF credit score >= 620 AND employment history >= 2 years THEN
                    IF debt-to-income ratio <= 45% THEN APPROVE
                    ELSE IF debt-to-income ratio <= 50% THEN REFER to underwriter
                    ELSE DECLINE
                ELSE
                    DECLINE for insufficient credit or employment
                
                Additional Requirements:
                - Minimum income $50,000 annually
                - Maximum loan amount $500,000
                - Property must be owner-occupied
                """,
                parent_id="nav_eligibility",
                confidence_score=0.92,
                quality_rating=QualityRating.EXCELLENT
            ),
            EnhancedNavigationNode(
                node_id="nav_decision_002",
                level=NavigationLevel.SUBSECTION,
                title="Income Verification Requirements",
                content="""
                Income Verification Decision Tree:
                
                For W-2 Employees:
                - IF 2 years employment history AND income stable THEN APPROVE documentation
                - IF 1 year employment BUT income increasing THEN REFER for manual review
                - IF less than 1 year employment THEN DECLINE
                
                For Self-Employed:
                - IF 2 years tax returns AND business operating profit THEN APPROVE
                - IF 1 year tax returns AND CPA letter THEN REFER
                - ELSE DECLINE
                """,
                parent_id="nav_income",
                confidence_score=0.88,
                quality_rating=QualityRating.GOOD
            ),
            EnhancedNavigationNode(
                node_id="nav_regular_001",
                level=NavigationLevel.SECTION,
                title="Property Standards",
                content="""
                Property must meet the following standards:
                - Single family residence or approved condo
                - No major structural issues
                - Appraised value supports loan amount
                - Located in approved geographic area
                """,
                parent_id="nav_property",
                confidence_score=0.85,
                quality_rating=QualityRating.GOOD
            )
        ]

    def _create_sample_document_content(self) -> str:
        """Create sample document content for testing"""
        return """
        NAA Non-QM Lending Guidelines
        
        Section 2: Borrower Eligibility
        
        2.1 Credit Requirements
        All borrowers must have a minimum credit score of 620. Exceptions may be made for 
        borrowers with strong compensating factors.
        
        2.2 Employment History
        Borrowers must demonstrate stable employment for a minimum of 2 years. Self-employed
        borrowers require 2 years of tax returns.
        
        2.3 Decision Matrix
        
        Credit Score >= 620 AND Employment >= 2 years:
            DTI <= 45%: APPROVE
            DTI 45-50%: REFER to underwriter
            DTI > 50%: DECLINE
            
        Credit Score < 620 OR Employment < 2 years:
            DECLINE (exceptions require management approval)
        
        2.4 Income Documentation
        
        W-2 Employment:
        - 2+ years: APPROVE standard documentation
        - 1-2 years with increasing income: REFER for manual review
        - < 1 year: DECLINE
        
        Self-Employment:
        - 2+ years tax returns with profit: APPROVE
        - 1-2 years with CPA letter: REFER
        - < 1 year or losses: DECLINE
        """

    def test_decision_tree_extractor_initialization(self):
        """Test DecisionTreeExtractor initialization"""
        self.assertIsNotNone(self.extractor)
        self.assertIsNotNone(self.extractor.decision_patterns)
        self.assertIn('decision_indicators', self.extractor.decision_patterns)
        self.assertIn('condition_patterns', self.extractor.decision_patterns)
        self.assertIn('outcome_patterns', self.extractor.decision_patterns)
        
        # Test mandatory outcomes
        self.assertEqual(len(self.extractor.mandatory_outcomes), 3)
        self.assertIn(DecisionOutcome.APPROVE, self.extractor.mandatory_outcomes)
        self.assertIn(DecisionOutcome.DECLINE, self.extractor.mandatory_outcomes)
        self.assertIn(DecisionOutcome.REFER, self.extractor.mandatory_outcomes)

    def test_initialize_decision_patterns(self):
        """Test decision pattern initialization"""
        patterns = self.extractor._initialize_decision_patterns()
        
        self.assertIn('decision_indicators', patterns)
        self.assertIn('condition_patterns', patterns)
        self.assertIn('outcome_patterns', patterns)
        self.assertIn('logical_operators', patterns)
        
        # Test specific patterns
        self.assertIn(r'(?i)(if\s+.*\s+then)', patterns['decision_indicators'])
        self.assertIn(r'(?i)(fico\s+score\s*[><=]+\s*\d+)', patterns['condition_patterns'])
        self.assertIn(r'(?i)(approved?|approval)', patterns['outcome_patterns'])

    def test_identify_decision_sections(self):
        """Test identification of decision-flow sections"""
        decision_sections = self.extractor._identify_decision_sections(self.sample_navigation_nodes)
        
        # Should identify the decision flow section and income verification
        self.assertGreaterEqual(len(decision_sections), 1)
        
        # First node should be identified as decision section
        decision_node_ids = [node.enhanced_node_id for node in decision_sections]
        self.assertIn("nav_decision_001", decision_node_ids)
        
        # Regular property section should not be identified as decision section
        self.assertNotIn("nav_regular_001", decision_node_ids)

    def test_create_leaf_node(self):
        """Test creation of leaf nodes with mandatory outcomes"""
        parent_id = "test_parent_001"
        outcome = DecisionOutcome.APPROVE
        condition_path = ["credit_score >= 620", "employment >= 2_years"]
        description = "Test approval outcome"
        
        leaf_node = self.extractor.create_leaf_node(
            parent_id, outcome, condition_path, description
        )
        
        self.assertEqual(leaf_node.decision_type, "LEAF")
        self.assertEqual(leaf_node.parent_decision_id, parent_id)
        self.assertEqual(leaf_node.outcomes, [outcome])
        self.assertEqual(leaf_node.outcome_descriptions[outcome], description)
        self.assertIn("APPROVE", leaf_node.title)
        self.assertEqual(leaf_node.navigation_context.decision_level, "LEAF")
        self.assertEqual(leaf_node.navigation_context.decision_factors, condition_path)

    def test_create_leaf_node_with_generated_description(self):
        """Test leaf node creation with auto-generated description"""
        parent_id = "test_parent_002"
        outcome = DecisionOutcome.DECLINE
        condition_path = ["credit_score < 620"]
        
        leaf_node = self.extractor.create_leaf_node(
            parent_id, outcome, condition_path
        )
        
        self.assertEqual(leaf_node.decision_type, "LEAF")
        self.assertEqual(leaf_node.outcomes, [outcome])
        self.assertIn("DECLINE", leaf_node.outcome_descriptions[outcome])
        self.assertIn("credit_score < 620", leaf_node.outcome_descriptions[outcome])

    def test_build_decision_extraction_prompt(self):
        """Test LLM prompt building for decision extraction"""
        section = self.sample_navigation_nodes[0]  # Decision flow section
        
        prompt = self.extractor._build_decision_extraction_prompt(
            section, self.sample_document_content
        )
        
        self.assertIn("Extract complete decision tree logic", prompt)
        self.assertIn(section.title, prompt)
        self.assertIn(section.content, prompt)
        self.assertIn("APPROVE", prompt)
        self.assertIn("DECLINE", prompt)
        self.assertIn("REFER", prompt)
        self.assertIn("JSON", prompt)

    def test_parse_llm_decision_response_valid_json(self):
        """Test parsing valid JSON response from LLM"""
        section = self.sample_navigation_nodes[0]
        
        mock_response = """
        ```json
        {
            "decision_trees": [
                {
                    "root_node": {
                        "node_id": "root_001",
                        "title": "Credit Check",
                        "decision_type": "ROOT",
                        "condition": "credit_score >= 620",
                        "criteria": ["credit_score", "employment_history"],
                        "variables": {"min_credit_score": 620},
                        "operators": ["AND"]
                    },
                    "branch_nodes": [
                        {
                            "node_id": "branch_001",
                            "decision_type": "BRANCH", 
                            "condition": "dti <= 45",
                            "parent_decision_id": "root_001",
                            "true_outcome": "approve_path",
                            "false_outcome": "refer_path"
                        }
                    ],
                    "leaf_nodes": [
                        {
                            "node_id": "leaf_approve",
                            "decision_type": "LEAF",
                            "parent_decision_id": "branch_001",
                            "outcomes": ["APPROVE"],
                            "outcome_descriptions": {"APPROVE": "Approved for loan"}
                        }
                    ]
                }
            ]
        }
        ```
        """
        
        nodes = self.extractor._parse_llm_decision_response(mock_response, section)
        
        self.assertEqual(len(nodes), 3)  # root + branch + leaf
        
        # Check root node
        root_nodes = [n for n in nodes if n.decision_type == "ROOT"]
        self.assertEqual(len(root_nodes), 1)
        self.assertEqual(root_nodes[0].node_id, "root_001")
        self.assertEqual(root_nodes[0].condition, "credit_score >= 620")
        
        # Check branch node
        branch_nodes = [n for n in nodes if n.decision_type == "BRANCH"]
        self.assertEqual(len(branch_nodes), 1)
        self.assertEqual(branch_nodes[0].parent_decision_id, "root_001")
        
        # Check leaf node
        leaf_nodes = [n for n in nodes if n.decision_type == "LEAF"]
        self.assertEqual(len(leaf_nodes), 1)
        self.assertIn(DecisionOutcome.APPROVE, leaf_nodes[0].outcomes)

    def test_parse_llm_decision_response_invalid_json(self):
        """Test parsing invalid JSON response falls back to pattern extraction"""
        section = self.sample_navigation_nodes[0]
        
        invalid_response = """
        This is not valid JSON but contains decision logic:
        IF credit score >= 620 THEN approve
        IF credit score < 620 THEN decline
        """
        
        with patch.object(self.extractor, '_fallback_pattern_extraction') as mock_fallback:
            mock_fallback.return_value = [Mock()]
            
            nodes = self.extractor._parse_llm_decision_response(invalid_response, section)
            
            mock_fallback.assert_called_once_with(invalid_response, section)

    def test_fallback_pattern_extraction(self):
        """Test fallback pattern extraction when JSON parsing fails"""
        section = self.sample_navigation_nodes[0]
        
        response_text = """
        Decision logic:
        IF FICO score >= 620 AND employment history >= 2 years THEN
            check debt-to-income ratio
        IF DTI <= 45% THEN APPROVE
        IF DTI > 50% THEN DECLINE
        ELSE REFER to underwriter
        """
        
        nodes = self.extractor._fallback_pattern_extraction(response_text, section)
        
        # Should create at least one node from the patterns
        self.assertGreaterEqual(len(nodes), 1)
        if nodes:
            self.assertEqual(nodes[0].decision_type, "ROOT")
            self.assertGreater(len(nodes[0].criteria), 0)

    def test_structure_decision_nodes(self):
        """Test structuring decision nodes into proper hierarchy"""
        section = self.sample_navigation_nodes[0]
        
        # Create unstructured nodes
        root_node = DecisionTreeNode(
            node_id="root_001",
            title="Root Decision",
            decision_type="ROOT",
            condition="credit_score >= 620"
        )
        
        branch_node = DecisionTreeNode(
            node_id="branch_001", 
            title="DTI Check",
            decision_type="BRANCH",
            condition="dti <= 45",
            parent_decision_id="root_001"
        )
        
        leaf_node = DecisionTreeNode(
            node_id="leaf_001",
            title="Approve",
            decision_type="LEAF",
            parent_decision_id="branch_001",
            outcomes=[DecisionOutcome.APPROVE]
        )
        
        unstructured_nodes = [root_node, branch_node, leaf_node]
        
        structured_nodes = self.extractor._structure_decision_nodes(unstructured_nodes, section)
        
        self.assertEqual(len(structured_nodes), 3)
        
        # Check hierarchy is established
        root = next(n for n in structured_nodes if n.decision_type == "ROOT")
        self.assertIn("branch_001", root.child_decision_ids)
        
        branch = next(n for n in structured_nodes if n.decision_type == "BRANCH")  
        self.assertIn("leaf_001", branch.child_decision_ids)

    def test_ensure_tree_completeness(self):
        """Test ensuring decision tree has all mandatory outcomes"""
        # Create tree with only APPROVE outcome
        tree = DecisionTreeNode(
            node_id="incomplete_tree",
            title="Incomplete Tree",
            decision_type="ROOT",
            outcomes=[DecisionOutcome.APPROVE]
        )
        
        complete_tree = self.extractor._ensure_tree_completeness(tree)
        
        # Tree should now reference additional outcome nodes
        self.assertGreater(len(complete_tree.child_decision_ids), 0)

    def test_validate_decision_trees(self):
        """Test decision tree validation"""
        # Create trees with various issues
        complete_tree = DecisionTreeNode(
            node_id="complete_001",
            title="Complete Tree",
            decision_type="ROOT",
            condition="credit_score >= 620",
            outcomes=[DecisionOutcome.APPROVE, DecisionOutcome.DECLINE, DecisionOutcome.REFER]
        )
        
        incomplete_tree = DecisionTreeNode(
            node_id="incomplete_001", 
            title="Incomplete Tree",
            decision_type="ROOT",
            outcomes=[DecisionOutcome.APPROVE]  # Missing DECLINE and REFER
        )
        
        orphaned_tree = DecisionTreeNode(
            node_id="orphaned_001",
            title="Orphaned Tree", 
            decision_type="BRANCH",  # Not ROOT but no parent
            condition="some condition"
        )
        
        trees = [complete_tree, incomplete_tree, orphaned_tree]
        
        validation_result = self.extractor._validate_decision_trees(trees)
        
        self.assertGreater(len(validation_result['errors']), 0)  # Should have errors for incomplete tree
        self.assertGreater(len(validation_result['warnings']), 0)  # Should have warnings for orphaned tree
        self.assertLess(validation_result['validation_score'], 1.0)

    def test_create_mandatory_outcome_nodes(self):
        """Test creation of mandatory outcome nodes"""
        # Tree missing DECLINE and REFER outcomes
        tree = DecisionTreeNode(
            node_id="tree_001",
            title="Partial Tree",
            decision_type="ROOT",
            outcomes=[DecisionOutcome.APPROVE]
        )
        
        enhanced_trees = self.extractor._create_mandatory_outcome_nodes([tree])
        
        # Should have original tree plus additional outcome nodes
        self.assertGreater(len(enhanced_trees), 1)
        
        # Check that new leaf nodes were created
        leaf_nodes = [t for t in enhanced_trees if t.decision_type == "LEAF"]
        self.assertGreater(len(leaf_nodes), 0)

    def test_calculate_extraction_metrics(self):
        """Test calculation of extraction metrics"""
        trees = [
            DecisionTreeNode(
                node_id="root_001",
                title="Root",
                decision_type="ROOT",
                outcomes=[DecisionOutcome.APPROVE]
            ),
            DecisionTreeNode(
                node_id="branch_001",
                title="Branch",
                decision_type="BRANCH",
                parent_decision_id="root_001"
            ),
            DecisionTreeNode(
                node_id="leaf_001",
                title="Leaf",
                decision_type="LEAF",
                parent_decision_id="branch_001",
                outcomes=[DecisionOutcome.DECLINE, DecisionOutcome.REFER]
            )
        ]
        
        metrics = self.extractor._calculate_extraction_metrics(trees)
        
        self.assertEqual(metrics.total_nodes, 3)
        self.assertEqual(metrics.root_nodes, 1)
        self.assertEqual(metrics.branch_nodes, 1)
        self.assertEqual(metrics.leaf_nodes, 1)
        self.assertEqual(metrics.orphaned_nodes, 0)
        self.assertEqual(metrics.mandatory_outcomes_coverage, 1.0)  # All outcomes covered
        self.assertGreater(metrics.logical_consistency_score, 0)

    def test_final_completeness_validation(self):
        """Test final completeness validation"""
        # Complete set of trees
        complete_trees = [
            DecisionTreeNode(
                node_id="root_001",
                title="Root",
                decision_type="ROOT",
                outcomes=[DecisionOutcome.APPROVE, DecisionOutcome.DECLINE, DecisionOutcome.REFER]
            ),
            DecisionTreeNode(
                node_id="leaf_001",
                title="Leaf",
                decision_type="LEAF",
                parent_decision_id="root_001"
            )
        ]
        
        validation_result = self.extractor._final_completeness_validation(complete_trees)
        
        self.assertEqual(len(validation_result['errors']), 0)
        self.assertGreater(validation_result['completeness_score'], 0.7)
        
        # Empty trees
        empty_validation = self.extractor._final_completeness_validation([])
        
        self.assertGreater(len(empty_validation['errors']), 0)
        self.assertEqual(empty_validation['completeness_score'], 0.0)

    @patch.object(DecisionTreeExtractor, '_identify_decision_sections')
    @patch.object(DecisionTreeExtractor, '_extract_decision_trees_from_section')
    @patch.object(DecisionTreeExtractor, '_ensure_tree_completeness')
    @patch.object(DecisionTreeExtractor, '_validate_decision_trees')
    @patch.object(DecisionTreeExtractor, '_create_mandatory_outcome_nodes')
    @patch.object(DecisionTreeExtractor, '_build_logical_flows')
    @patch.object(DecisionTreeExtractor, '_calculate_extraction_metrics')
    @patch.object(DecisionTreeExtractor, '_final_completeness_validation')
    def test_extract_complete_decision_trees_success(
        self,
        mock_final_validation,
        mock_calculate_metrics,
        mock_build_flows,
        mock_create_outcomes,
        mock_validate_trees,
        mock_ensure_completeness,
        mock_extract_from_section,
        mock_identify_sections
    ):
        """Test successful complete decision tree extraction"""
        # Setup mocks
        decision_section = self.sample_navigation_nodes[0]
        mock_identify_sections.return_value = [decision_section]
        
        sample_tree = DecisionTreeNode(
            node_id="test_tree",
            title="Test Tree",
            decision_type="ROOT",
            outcomes=[DecisionOutcome.APPROVE]
        )
        
        mock_extract_from_section.return_value = [sample_tree]
        mock_ensure_completeness.return_value = sample_tree
        mock_validate_trees.return_value = {'errors': [], 'warnings': []}
        mock_create_outcomes.return_value = [sample_tree]
        mock_build_flows.return_value = [sample_tree]
        mock_calculate_metrics.return_value = DecisionTreeMetrics(
            total_nodes=1,
            mandatory_outcomes_coverage=1.0
        )
        mock_final_validation.return_value = {
            'errors': [],
            'warnings': [],
            'completeness_score': 1.0
        }
        
        # Execute test
        result = self.extractor.extract_complete_decision_trees(
            self.sample_navigation_nodes,
            self.sample_document_content
        )
        
        # Verify result
        self.assertTrue(result.success)
        self.assertEqual(len(result.decision_trees), 1)
        self.assertEqual(result.completeness_score, 1.0)
        self.assertEqual(len(result.validation_errors), 0)

    def test_extract_complete_decision_trees_no_sections(self):
        """Test extraction when no decision sections are found"""
        # Mock no decision sections found
        with patch.object(self.extractor, '_identify_decision_sections', return_value=[]):
            result = self.extractor.extract_complete_decision_trees(
                self.sample_navigation_nodes,
                self.sample_document_content
            )
        
        self.assertFalse(result.success)
        self.assertIn("No decision flow sections found", result.validation_warnings)

    def test_extract_complete_decision_trees_extraction_failure(self):
        """Test extraction with section processing failures"""
        decision_section = self.sample_navigation_nodes[0]
        
        with patch.object(self.extractor, '_identify_decision_sections', return_value=[decision_section]):
            with patch.object(self.extractor, '_extract_decision_trees_from_section', side_effect=Exception("Extraction failed")):
                result = self.extractor.extract_complete_decision_trees(
                    self.sample_navigation_nodes,
                    self.sample_document_content
                )
        
        self.assertGreater(len(result.validation_errors), 0)
        self.assertIn("Extraction failed", str(result.validation_errors))


class TestDecisionTreeExtractionResult(unittest.TestCase):
    """Test suite for DecisionTreeExtractionResult class"""
    
    def test_extraction_result_initialization(self):
        """Test DecisionTreeExtractionResult initialization"""
        result = DecisionTreeExtractionResult(success=True)
        
        self.assertTrue(result.success)
        self.assertEqual(len(result.decision_trees), 0)
        self.assertEqual(result.completeness_score, 0.0)
        self.assertEqual(len(result.validation_errors), 0)
        self.assertEqual(len(result.validation_warnings), 0)
        self.assertEqual(len(result.extraction_metrics), 0)
        self.assertEqual(result.processing_time_ms, 0)

    def test_extraction_result_with_data(self):
        """Test DecisionTreeExtractionResult with sample data"""
        sample_tree = DecisionTreeNode(
            node_id="test_tree",
            title="Test Tree",
            decision_type="ROOT"
        )
        
        metrics = {"total_nodes": 1, "completeness": 0.95}
        
        result = DecisionTreeExtractionResult(
            success=True,
            decision_trees=[sample_tree],
            completeness_score=0.95,
            extraction_metrics=metrics,
            processing_time_ms=1500
        )
        
        self.assertTrue(result.success)
        self.assertEqual(len(result.decision_trees), 1)
        self.assertEqual(result.completeness_score, 0.95)
        self.assertEqual(result.extraction_metrics["total_nodes"], 1)
        self.assertEqual(result.processing_time_ms, 1500)


class TestDecisionTreeMetrics(unittest.TestCase):
    """Test suite for DecisionTreeMetrics class"""
    
    def test_metrics_initialization(self):
        """Test DecisionTreeMetrics initialization with defaults"""
        metrics = DecisionTreeMetrics()
        
        self.assertEqual(metrics.total_nodes, 0)
        self.assertEqual(metrics.root_nodes, 0)
        self.assertEqual(metrics.branch_nodes, 0)
        self.assertEqual(metrics.leaf_nodes, 0)
        self.assertEqual(metrics.orphaned_nodes, 0)
        self.assertEqual(metrics.incomplete_paths, 0)
        self.assertEqual(metrics.mandatory_outcomes_coverage, 0.0)
        self.assertEqual(metrics.decision_depth, 0)
        self.assertEqual(metrics.logical_consistency_score, 0.0)

    def test_metrics_with_values(self):
        """Test DecisionTreeMetrics with specific values"""
        metrics = DecisionTreeMetrics(
            total_nodes=5,
            root_nodes=1,
            branch_nodes=2,
            leaf_nodes=2,
            orphaned_nodes=0,
            incomplete_paths=0,
            mandatory_outcomes_coverage=1.0,
            decision_depth=3,
            logical_consistency_score=0.95
        )
        
        self.assertEqual(metrics.total_nodes, 5)
        self.assertEqual(metrics.root_nodes, 1)
        self.assertEqual(metrics.branch_nodes, 2)
        self.assertEqual(metrics.leaf_nodes, 2)
        self.assertEqual(metrics.mandatory_outcomes_coverage, 1.0)
        self.assertEqual(metrics.logical_consistency_score, 0.95)


if __name__ == '__main__':
    unittest.main()