# Task 15: Decision Tree Validator Tests
# Comprehensive test suite for decision tree validation framework

import unittest
from unittest.mock import Mock, patch
from datetime import datetime
from typing import List

from src.decision_tree_validator import (
    DecisionTreeValidator,
    ValidationResult,
    ValidationIssue,
    QualityMetrics,
    validate_decision_trees
)
from src.entities.navigation_models import (
    DecisionTreeNode,
    DecisionOutcome,
    NavigationContext,
    QualityRating
)
from src.decision_tree_extractor import DecisionPath


class TestValidationIssue(unittest.TestCase):
    """Test ValidationIssue data structure"""
    
    def test_validation_issue_creation(self):
        """Test basic ValidationIssue creation"""
        issue = ValidationIssue(
            issue_id="test-issue-1",
            severity="CRITICAL",
            issue_type="COMPLETENESS",
            message="Test validation issue",
            affected_node_ids=["node1", "node2"],
            suggested_fix="Fix suggestion",
            auto_fixable=True
        )
        
        self.assertEqual(issue.issue_id, "test-issue-1")
        self.assertEqual(issue.severity, "CRITICAL")
        self.assertEqual(issue.issue_type, "COMPLETENESS")
        self.assertEqual(issue.message, "Test validation issue")
        self.assertEqual(issue.affected_node_ids, ["node1", "node2"])
        self.assertEqual(issue.suggested_fix, "Fix suggestion")
        self.assertTrue(issue.auto_fixable)


class TestValidationResult(unittest.TestCase):
    """Test ValidationResult data structure"""
    
    def test_validation_result_creation(self):
        """Test basic ValidationResult creation"""
        result = ValidationResult(
            validation_id="test-validation-1",
            success=True,
            completeness_score=0.95,
            consistency_score=0.90,
            coverage_score=0.85,
            outcome_score=1.0,
            overall_quality_score=0.92
        )
        
        self.assertEqual(result.validation_id, "test-validation-1")
        self.assertTrue(result.success)
        self.assertEqual(result.completeness_score, 0.95)
        self.assertEqual(result.consistency_score, 0.90)
        self.assertEqual(result.coverage_score, 0.85)
        self.assertEqual(result.outcome_score, 1.0)
        self.assertEqual(result.overall_quality_score, 0.92)
    
    def test_is_valid_passing(self):
        """Test is_valid method with passing scores"""
        result = ValidationResult(
            validation_id="test-validation-1",
            success=True,
            completeness_score=0.96,
            consistency_score=0.92,
            coverage_score=0.85,
            outcome_score=1.0,
            overall_quality_score=0.92
        )
        
        self.assertTrue(result.is_valid())
    
    def test_is_valid_failing_completeness(self):
        """Test is_valid method with failing completeness score"""
        result = ValidationResult(
            validation_id="test-validation-1",
            success=True,
            completeness_score=0.90,  # Below 0.95 threshold
            consistency_score=0.92,
            coverage_score=0.85,
            outcome_score=1.0,
            overall_quality_score=0.92
        )
        
        self.assertFalse(result.is_valid())
    
    def test_is_valid_failing_with_critical_issues(self):
        """Test is_valid method with critical issues"""
        result = ValidationResult(
            validation_id="test-validation-1",
            success=True,
            completeness_score=0.96,
            consistency_score=0.92,
            coverage_score=0.85,
            outcome_score=1.0,
            overall_quality_score=0.92,
            critical_issues=[ValidationIssue(
                issue_id="critical-1",
                severity="CRITICAL",
                issue_type="COMPLETENESS",
                message="Critical issue"
            )]
        )
        
        self.assertFalse(result.is_valid())


class TestQualityMetrics(unittest.TestCase):
    """Test QualityMetrics calculation"""
    
    def test_quality_metrics_creation(self):
        """Test basic QualityMetrics creation"""
        metrics = QualityMetrics(
            structural_integrity=0.95,
            logical_consistency=0.90,
            outcome_completeness=1.0,
            path_coverage=0.85,
            entity_linkage=0.80,
            navigation_preservation=0.90
        )
        
        self.assertEqual(metrics.structural_integrity, 0.95)
        self.assertEqual(metrics.logical_consistency, 0.90)
        self.assertEqual(metrics.outcome_completeness, 1.0)
        self.assertEqual(metrics.path_coverage, 0.85)
        self.assertEqual(metrics.entity_linkage, 0.80)
        self.assertEqual(metrics.navigation_preservation, 0.90)
    
    def test_calculate_overall_quality(self):
        """Test overall quality calculation"""
        metrics = QualityMetrics(
            structural_integrity=0.90,
            logical_consistency=0.85,
            outcome_completeness=1.0,
            path_coverage=0.80,
            entity_linkage=0.75,
            navigation_preservation=0.90
        )
        
        overall = metrics.calculate_overall_quality()
        
        # Expected: 0.90*0.25 + 0.85*0.20 + 1.0*0.25 + 0.80*0.15 + 0.75*0.10 + 0.90*0.05
        expected = 0.225 + 0.17 + 0.25 + 0.12 + 0.075 + 0.045
        self.assertAlmostEqual(overall, expected, places=3)


class TestDecisionTreeValidator(unittest.TestCase):
    """Test DecisionTreeValidator functionality"""
    
    def setUp(self):
        """Set up test environment"""
        self.validator = DecisionTreeValidator()
        
        # Create mock decision tree nodes
        self.root_node = Mock(spec=DecisionTreeNode)
        self.root_node.node_id = "root-1"
        self.root_node.node_type = "ROOT"
        self.root_node.children = []
        
        self.branch_node = Mock(spec=DecisionTreeNode)
        self.branch_node.node_id = "branch-1"
        self.branch_node.node_type = "BRANCH"
        self.branch_node.children = []
        self.branch_node.condition = "credit_score >= 620"
        
        self.leaf_node = Mock(spec=DecisionTreeNode)
        self.leaf_node.node_id = "leaf-1"
        self.leaf_node.node_type = "LEAF"
        self.leaf_node.children = []
        self.leaf_node.outcome = DecisionOutcome.APPROVE
        
        # Set up tree structure
        self.root_node.children = [self.branch_node]
        self.branch_node.children = [self.leaf_node]
    
    def test_validator_initialization(self):
        """Test validator initialization"""
        self.assertIsNotNone(self.validator.validation_rules)
        self.assertTrue(self.validator.auto_fix_enabled)
        self.assertIn('min_completeness_score', self.validator.validation_rules)
        self.assertEqual(self.validator.validation_rules['min_completeness_score'], 0.95)
    
    def test_validate_empty_trees(self):
        """Test validation with empty tree list"""
        result = self.validator.validate_decision_trees([])
        
        self.assertFalse(result.success)
        self.assertEqual(len(result.critical_issues), 1)
        self.assertEqual(result.critical_issues[0].issue_type, "NO_TREES")
    
    def test_validate_single_complete_tree(self):
        """Test validation with single complete tree"""
        with patch.object(self.validator, '_collect_all_nodes') as mock_collect:
            mock_collect.return_value = [self.root_node, self.branch_node, self.leaf_node]
            
            with patch.object(self.validator, '_extract_all_paths') as mock_paths:
                mock_path = Mock(spec=DecisionPath)
                mock_path.path_id = "path-1"
                mock_path.start_node_id = "root-1"
                mock_path.end_node_id = "leaf-1"
                mock_path.final_outcome = DecisionOutcome.APPROVE
                mock_paths.return_value = [mock_path]
                
                with patch.object(self.validator, '_is_path_complete') as mock_complete:
                    mock_complete.return_value = True
                    
                    result = self.validator.validate_decision_trees([self.root_node])
        
        self.assertIsNotNone(result.validation_id)
        self.assertEqual(result.total_nodes, 3)
        self.assertEqual(result.completeness_score, 1.0)
        self.assertEqual(result.valid_paths, 1)
        self.assertEqual(result.incomplete_paths, 0)
    
    def test_validate_incomplete_tree(self):
        """Test validation with incomplete tree"""
        # Create incomplete tree (leaf without outcome)
        incomplete_leaf = Mock(spec=DecisionTreeNode)
        incomplete_leaf.node_id = "incomplete-leaf-1"
        incomplete_leaf.node_type = "LEAF"
        incomplete_leaf.children = []
        incomplete_leaf.outcome = None
        
        self.branch_node.children = [incomplete_leaf]
        
        with patch.object(self.validator, '_collect_all_nodes') as mock_collect:
            mock_collect.return_value = [self.root_node, self.branch_node, incomplete_leaf]
            
            with patch.object(self.validator, '_extract_all_paths') as mock_paths:
                mock_path = Mock(spec=DecisionPath)
                mock_path.path_id = "incomplete-path-1"
                mock_path.start_node_id = "root-1"
                mock_path.end_node_id = "incomplete-leaf-1"
                mock_path.final_outcome = None
                mock_paths.return_value = [mock_path]
                
                with patch.object(self.validator, '_is_path_complete') as mock_complete:
                    mock_complete.return_value = False
                    
                    result = self.validator.validate_decision_trees([self.root_node])
        
        self.assertEqual(result.completeness_score, 0.0)
        self.assertEqual(result.valid_paths, 0)
        self.assertEqual(result.incomplete_paths, 1)
        self.assertTrue(len(result.critical_issues) > 0)
    
    def test_validate_missing_mandatory_outcomes(self):
        """Test validation detects missing mandatory outcomes"""
        with patch.object(self.validator, '_collect_all_nodes') as mock_collect:
            mock_collect.return_value = [self.root_node, self.branch_node, self.leaf_node]
            
            with patch.object(self.validator, '_extract_all_paths') as mock_paths:
                # Only APPROVE outcome, missing DECLINE and REFER
                mock_path = Mock(spec=DecisionPath)
                mock_path.path_id = "path-1"
                mock_path.final_outcome = DecisionOutcome.APPROVE
                mock_paths.return_value = [mock_path]
                
                with patch.object(self.validator, '_is_path_complete') as mock_complete:
                    mock_complete.return_value = True
                    
                    result = self.validator.validate_decision_trees([self.root_node])
        
        # Should have critical issue for missing outcomes
        missing_outcome_issues = [
            issue for issue in result.critical_issues
            if issue.issue_type == "MISSING_OUTCOMES"
        ]
        self.assertTrue(len(missing_outcome_issues) > 0)
    
    def test_auto_fix_enabled(self):
        """Test automatic fixing functionality"""
        self.validator.auto_fix_enabled = True
        
        with patch.object(self.validator, '_auto_complete_trees') as mock_auto_fix:
            mock_auto_fix.return_value = None
            
            with patch.object(self.validator, '_collect_all_nodes') as mock_collect:
                mock_collect.return_value = [self.root_node]
                
                with patch.object(self.validator, '_extract_all_paths') as mock_paths:
                    mock_paths.return_value = []
                    
                    result = self.validator.validate_decision_trees([self.root_node])
            
            mock_auto_fix.assert_called_once()
    
    def test_collect_all_nodes(self):
        """Test node collection functionality"""
        nodes = self.validator._collect_all_nodes(self.root_node)
        
        # Should collect all nodes in the tree
        node_ids = [getattr(node, 'node_id', None) for node in nodes]
        self.assertIn("root-1", node_ids)
        self.assertIn("branch-1", node_ids)
        self.assertIn("leaf-1", node_ids)
    
    def test_extract_all_paths(self):
        """Test path extraction functionality"""
        paths = self.validator._extract_all_paths(self.root_node)
        
        # Should extract paths from root to leaf
        self.assertTrue(len(paths) > 0)
        path = paths[0]
        self.assertEqual(path.start_node_id, "root-1")
        self.assertEqual(path.end_node_id, "leaf-1")
    
    def test_is_path_complete(self):
        """Test path completeness checking"""
        # Complete path (with outcome)
        complete_path = Mock(spec=DecisionPath)
        complete_path.final_outcome = DecisionOutcome.APPROVE
        
        self.assertTrue(self.validator._is_path_complete(complete_path))
        
        # Incomplete path (no outcome)
        incomplete_path = Mock(spec=DecisionPath)
        incomplete_path.final_outcome = None
        
        self.assertFalse(self.validator._is_path_complete(incomplete_path))
    
    def test_is_path_logically_consistent(self):
        """Test path logical consistency checking"""
        # Path with decision sequence
        consistent_path = Mock(spec=DecisionPath)
        consistent_path.decision_sequence = ["credit_score >= 620", "dti <= 0.43"]
        
        self.assertTrue(self.validator._is_path_logically_consistent(consistent_path))
        
        # Path without decision sequence
        inconsistent_path = Mock(spec=DecisionPath)
        inconsistent_path.decision_sequence = []
        
        self.assertFalse(self.validator._is_path_logically_consistent(inconsistent_path))
    
    def test_create_default_outcome(self):
        """Test default outcome creation"""
        mock_path = Mock(spec=DecisionPath)
        mock_path.path_id = "test-path-1"
        
        result = self.validator._create_default_outcome(mock_path, DecisionOutcome.REFER)
        
        # Currently returns True as placeholder
        self.assertTrue(result)


class TestValidationIntegration(unittest.TestCase):
    """Integration tests for decision tree validation"""
    
    def test_complete_validation_workflow(self):
        """Test complete validation workflow"""
        # Create complex decision tree
        root = Mock(spec=DecisionTreeNode)
        root.node_id = "root-complex"
        root.node_type = "ROOT"
        
        branch1 = Mock(spec=DecisionTreeNode)
        branch1.node_id = "branch-1"
        branch1.node_type = "BRANCH"
        branch1.condition = "credit_score >= 620"
        
        branch2 = Mock(spec=DecisionTreeNode)
        branch2.node_id = "branch-2"
        branch2.node_type = "BRANCH"
        branch2.condition = "credit_score < 620"
        
        leaf1 = Mock(spec=DecisionTreeNode)
        leaf1.node_id = "leaf-approve"
        leaf1.node_type = "LEAF"
        leaf1.outcome = DecisionOutcome.APPROVE
        leaf1.children = []
        
        leaf2 = Mock(spec=DecisionTreeNode)
        leaf2.node_id = "leaf-decline"
        leaf2.node_type = "LEAF"
        leaf2.outcome = DecisionOutcome.DECLINE
        leaf2.children = []
        
        leaf3 = Mock(spec=DecisionTreeNode)
        leaf3.node_id = "leaf-refer"
        leaf3.node_type = "LEAF"
        leaf3.outcome = DecisionOutcome.REFER
        leaf3.children = []
        
        # Set up tree structure
        root.children = [branch1, branch2]
        branch1.children = [leaf1, leaf3]
        branch2.children = [leaf2]
        
        validator = DecisionTreeValidator()
        
        with patch.object(validator, '_collect_all_nodes') as mock_collect:
            mock_collect.return_value = [root, branch1, branch2, leaf1, leaf2, leaf3]
            
            with patch.object(validator, '_extract_all_paths') as mock_paths:
                path1 = Mock(spec=DecisionPath)
                path1.path_id = "path-1"
                path1.final_outcome = DecisionOutcome.APPROVE
                
                path2 = Mock(spec=DecisionPath)
                path2.path_id = "path-2"
                path2.final_outcome = DecisionOutcome.DECLINE
                
                path3 = Mock(spec=DecisionPath)
                path3.path_id = "path-3"
                path3.final_outcome = DecisionOutcome.REFER
                
                mock_paths.return_value = [path1, path2, path3]
                
                with patch.object(validator, '_is_path_complete') as mock_complete:
                    mock_complete.return_value = True
                    
                    result = validator.validate_decision_trees([root])
        
        # Should have high quality scores with complete tree
        self.assertEqual(result.total_nodes, 6)
        self.assertEqual(result.completeness_score, 1.0)
        self.assertEqual(result.valid_paths, 3)
        self.assertEqual(result.incomplete_paths, 0)
    
    def test_convenience_function(self):
        """Test convenience validation function"""
        mock_tree = Mock(spec=DecisionTreeNode)
        mock_tree.node_id = "test-tree"
        
        with patch('src.decision_tree_validator.DecisionTreeValidator') as mock_validator_class:
            mock_validator = Mock()
            mock_result = Mock(spec=ValidationResult)
            mock_validator.validate_decision_trees.return_value = mock_result
            mock_validator_class.return_value = mock_validator
            
            result = validate_decision_trees([mock_tree], auto_fix=False)
            
            mock_validator_class.assert_called_once()
            mock_validator.validate_decision_trees.assert_called_once_with([mock_tree], None)
            self.assertEqual(result, mock_result)


if __name__ == '__main__':
    unittest.main()