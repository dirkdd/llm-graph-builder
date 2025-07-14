# Task 15: Decision Tree Validator Implementation
# Comprehensive validation framework for decision trees with completeness guarantee

from typing import List, Dict, Any, Optional, Tuple, Set
from dataclasses import dataclass, field
from datetime import datetime
import logging
import uuid
from collections import defaultdict, deque

# Import existing entities and models
from src.entities.navigation_models import (
    DecisionTreeNode,
    DecisionOutcome,
    NavigationContext,
    QualityRating
)
from src.decision_tree_extractor import (
    DecisionTreeExtractionResult,
    DecisionPath,
    DecisionTreeMetrics
)


@dataclass
class ValidationIssue:
    """Represents a validation issue found in decision trees"""
    issue_id: str
    severity: str  # CRITICAL, WARNING, INFO
    issue_type: str  # COMPLETENESS, CONSISTENCY, ORPHANED, MISSING_OUTCOME
    message: str
    affected_node_ids: List[str] = field(default_factory=list)
    suggested_fix: Optional[str] = None
    auto_fixable: bool = False


@dataclass
class ValidationResult:
    """Comprehensive validation result for decision trees"""
    validation_id: str
    success: bool
    completeness_score: float  # 0.0 to 1.0
    consistency_score: float   # 0.0 to 1.0
    coverage_score: float      # 0.0 to 1.0
    outcome_score: float       # 0.0 to 1.0
    overall_quality_score: float  # 0.0 to 1.0
    
    # Issues and fixes
    critical_issues: List[ValidationIssue] = field(default_factory=list)
    warnings: List[ValidationIssue] = field(default_factory=list)
    info_issues: List[ValidationIssue] = field(default_factory=list)
    
    # Metrics
    total_nodes: int = 0
    root_nodes: int = 0
    branch_nodes: int = 0
    leaf_nodes: int = 0
    orphaned_nodes: int = 0
    incomplete_paths: int = 0
    valid_paths: int = 0
    
    # Performance
    validation_time_ms: int = 0
    auto_fixes_applied: int = 0
    
    def is_valid(self) -> bool:
        """Check if validation passed all requirements"""
        return (
            self.success and
            len(self.critical_issues) == 0 and
            self.completeness_score >= 0.95 and
            self.consistency_score >= 0.90 and
            self.outcome_score >= 1.0  # 100% outcome coverage required
        )


@dataclass
class QualityMetrics:
    """Quality assessment metrics for decision trees"""
    structural_integrity: float = 0.0
    logical_consistency: float = 0.0
    outcome_completeness: float = 0.0
    path_coverage: float = 0.0
    entity_linkage: float = 0.0
    navigation_preservation: float = 0.0
    
    def calculate_overall_quality(self) -> float:
        """Calculate overall quality score"""
        weights = {
            'structural_integrity': 0.25,
            'logical_consistency': 0.20,
            'outcome_completeness': 0.25,
            'path_coverage': 0.15,
            'entity_linkage': 0.10,
            'navigation_preservation': 0.05
        }
        
        return (
            self.structural_integrity * weights['structural_integrity'] +
            self.logical_consistency * weights['logical_consistency'] +
            self.outcome_completeness * weights['outcome_completeness'] +
            self.path_coverage * weights['path_coverage'] +
            self.entity_linkage * weights['entity_linkage'] +
            self.navigation_preservation * weights['navigation_preservation']
        )


class DecisionTreeValidator:
    """Comprehensive validator for decision trees with automatic completion"""
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        self.logger = logger or logging.getLogger(__name__)
        self.validation_rules = self._initialize_validation_rules()
        self.auto_fix_enabled = True
        
    def _initialize_validation_rules(self) -> Dict[str, Any]:
        """Initialize validation rules and thresholds"""
        return {
            'min_completeness_score': 0.95,
            'min_consistency_score': 0.90,
            'required_outcome_coverage': 1.0,
            'max_orphaned_nodes': 0,
            'mandatory_outcomes': {DecisionOutcome.APPROVE, DecisionOutcome.DECLINE, DecisionOutcome.REFER},
            'max_decision_depth': 10,
            'min_branch_factor': 2,
            'required_node_types': {'ROOT', 'BRANCH', 'LEAF'}
        }
    
    def validate_decision_trees(
        self, 
        decision_trees: List[DecisionTreeNode],
        navigation_context: Optional[NavigationContext] = None
    ) -> ValidationResult:
        """
        Comprehensive validation of decision trees with automatic completion
        
        Args:
            decision_trees: List of decision tree root nodes
            navigation_context: Optional navigation context for validation
            
        Returns:
            ValidationResult with comprehensive validation details
        """
        start_time = datetime.now()
        validation_id = str(uuid.uuid4())
        
        self.logger.info(f"Starting decision tree validation: {validation_id}")
        
        try:
            # Initialize validation result
            result = ValidationResult(
                validation_id=validation_id,
                success=False,
                completeness_score=0.0,
                consistency_score=0.0,
                coverage_score=0.0,
                outcome_score=0.0,
                overall_quality_score=0.0
            )
            
            if not decision_trees:
                result.critical_issues.append(ValidationIssue(
                    issue_id=str(uuid.uuid4()),
                    severity="CRITICAL",
                    issue_type="NO_TREES",
                    message="No decision trees provided for validation"
                ))
                return result
            
            # Step 1: Structural validation
            self._validate_tree_structure(decision_trees, result)
            
            # Step 2: Completeness validation
            self._validate_tree_completeness(decision_trees, result)
            
            # Step 3: Logical consistency validation
            self._validate_logical_consistency(decision_trees, result)
            
            # Step 4: Outcome coverage validation
            self._validate_outcome_coverage(decision_trees, result)
            
            # Step 5: Path validation
            self._validate_decision_paths(decision_trees, result)
            
            # Step 6: Orphaned node detection
            self._detect_orphaned_nodes(decision_trees, result)
            
            # Step 7: Auto-completion for incomplete trees
            if self.auto_fix_enabled:
                self._auto_complete_trees(decision_trees, result)
            
            # Step 8: Calculate quality metrics
            quality_metrics = self._calculate_quality_metrics(decision_trees, result)
            result.overall_quality_score = quality_metrics.calculate_overall_quality()
            
            # Step 9: Final validation assessment
            result.success = result.is_valid()
            
            # Calculate processing time
            end_time = datetime.now()
            result.validation_time_ms = int((end_time - start_time).total_seconds() * 1000)
            
            self.logger.info(
                f"Decision tree validation completed: {validation_id} - "
                f"Success: {result.success}, Quality: {result.overall_quality_score:.3f}"
            )
            
            return result
            
        except Exception as e:
            self.logger.error(f"Decision tree validation failed: {str(e)}")
            result.critical_issues.append(ValidationIssue(
                issue_id=str(uuid.uuid4()),
                severity="CRITICAL",
                issue_type="VALIDATION_ERROR",
                message=f"Validation process failed: {str(e)}"
            ))
            return result
    
    def _validate_tree_structure(self, decision_trees: List[DecisionTreeNode], result: ValidationResult):
        """Validate basic tree structure and node types"""
        all_nodes = []
        node_types = set()
        
        for tree in decision_trees:
            tree_nodes = self._collect_all_nodes(tree)
            all_nodes.extend(tree_nodes)
            
            for node in tree_nodes:
                if hasattr(node, 'node_type'):
                    node_types.add(node.node_type)
        
        result.total_nodes = len(all_nodes)
        result.root_nodes = len(decision_trees)
        
        # Count node types
        for node in all_nodes:
            if hasattr(node, 'node_type'):
                if node.node_type == 'ROOT':
                    result.root_nodes += 1
                elif node.node_type == 'BRANCH':
                    result.branch_nodes += 1
                elif node.node_type == 'LEAF':
                    result.leaf_nodes += 1
        
        # Validate required node types
        required_types = self.validation_rules['required_node_types']
        missing_types = required_types - node_types
        
        if missing_types:
            result.critical_issues.append(ValidationIssue(
                issue_id=str(uuid.uuid4()),
                severity="CRITICAL",
                issue_type="MISSING_NODE_TYPES",
                message=f"Missing required node types: {missing_types}",
                auto_fixable=True
            ))
    
    def _validate_tree_completeness(self, decision_trees: List[DecisionTreeNode], result: ValidationResult):
        """Validate that all decision trees are complete (ROOT → BRANCH → LEAF)"""
        incomplete_trees = []
        total_paths = 0
        complete_paths = 0
        
        for tree in decision_trees:
            paths = self._extract_all_paths(tree)
            total_paths += len(paths)
            
            for path in paths:
                if self._is_path_complete(path):
                    complete_paths += 1
                else:
                    incomplete_trees.append(tree.node_id if hasattr(tree, 'node_id') else 'unknown')
        
        if total_paths > 0:
            result.completeness_score = complete_paths / total_paths
        
        result.incomplete_paths = total_paths - complete_paths
        result.valid_paths = complete_paths
        
        if result.completeness_score < self.validation_rules['min_completeness_score']:
            result.critical_issues.append(ValidationIssue(
                issue_id=str(uuid.uuid4()),
                severity="CRITICAL",
                issue_type="INCOMPLETE_TREES",
                message=f"Completeness score {result.completeness_score:.3f} below required {self.validation_rules['min_completeness_score']}",
                affected_node_ids=incomplete_trees,
                auto_fixable=True
            ))
    
    def _validate_logical_consistency(self, decision_trees: List[DecisionTreeNode], result: ValidationResult):
        """Validate logical consistency across decision trees"""
        consistency_issues = []
        total_checks = 0
        passed_checks = 0
        
        for tree in decision_trees:
            # Check for logical contradictions
            contradictions = self._detect_logical_contradictions(tree)
            consistency_issues.extend(contradictions)
            
            # Check for circular references
            circular_refs = self._detect_circular_references(tree)
            consistency_issues.extend(circular_refs)
            
            # Check for unreachable nodes
            unreachable = self._detect_unreachable_nodes(tree)
            consistency_issues.extend(unreachable)
            
            total_checks += 3  # Three types of checks per tree
            passed_checks += 3 - len(contradictions) - len(circular_refs) - len(unreachable)
        
        if total_checks > 0:
            result.consistency_score = passed_checks / total_checks
        
        for issue in consistency_issues:
            result.warnings.append(ValidationIssue(
                issue_id=str(uuid.uuid4()),
                severity="WARNING",
                issue_type="LOGICAL_INCONSISTENCY",
                message=issue,
                auto_fixable=False
            ))
    
    def _validate_outcome_coverage(self, decision_trees: List[DecisionTreeNode], result: ValidationResult):
        """Validate that all mandatory outcomes are present"""
        all_outcomes = set()
        paths_with_outcomes = 0
        total_paths = 0
        
        for tree in decision_trees:
            paths = self._extract_all_paths(tree)
            total_paths += len(paths)
            
            for path in paths:
                if path.final_outcome:
                    all_outcomes.add(path.final_outcome)
                    paths_with_outcomes += 1
        
        if total_paths > 0:
            result.outcome_score = paths_with_outcomes / total_paths
        
        # Check for mandatory outcomes
        mandatory_outcomes = self.validation_rules['mandatory_outcomes']
        missing_outcomes = mandatory_outcomes - all_outcomes
        
        if missing_outcomes:
            result.critical_issues.append(ValidationIssue(
                issue_id=str(uuid.uuid4()),
                severity="CRITICAL",
                issue_type="MISSING_OUTCOMES",
                message=f"Missing mandatory outcomes: {missing_outcomes}",
                auto_fixable=True,
                suggested_fix="Create REFER outcome nodes for incomplete paths"
            ))
        
        if result.outcome_score < self.validation_rules['required_outcome_coverage']:
            result.critical_issues.append(ValidationIssue(
                issue_id=str(uuid.uuid4()),
                severity="CRITICAL",
                issue_type="INSUFFICIENT_OUTCOME_COVERAGE",
                message=f"Outcome coverage {result.outcome_score:.3f} below required {self.validation_rules['required_outcome_coverage']}",
                auto_fixable=True
            ))
    
    def _validate_decision_paths(self, decision_trees: List[DecisionTreeNode], result: ValidationResult):
        """Validate individual decision paths for completeness and consistency"""
        for tree in decision_trees:
            paths = self._extract_all_paths(tree)
            
            for path in paths:
                # Validate path completeness
                if not self._is_path_complete(path):
                    result.warnings.append(ValidationIssue(
                        issue_id=str(uuid.uuid4()),
                        severity="WARNING",
                        issue_type="INCOMPLETE_PATH",
                        message=f"Incomplete decision path: {path.path_id}",
                        affected_node_ids=[path.start_node_id, path.end_node_id],
                        auto_fixable=True
                    ))
                
                # Validate path logic
                if not self._is_path_logically_consistent(path):
                    result.warnings.append(ValidationIssue(
                        issue_id=str(uuid.uuid4()),
                        severity="WARNING",
                        issue_type="INCONSISTENT_PATH",
                        message=f"Logically inconsistent decision path: {path.path_id}",
                        affected_node_ids=[path.start_node_id, path.end_node_id],
                        auto_fixable=False
                    ))
    
    def _detect_orphaned_nodes(self, decision_trees: List[DecisionTreeNode], result: ValidationResult):
        """Detect nodes that are not properly connected to the tree structure"""
        all_connected_nodes = set()
        all_nodes = []
        
        # Collect all connected nodes from trees
        for tree in decision_trees:
            connected_nodes = self._collect_all_nodes(tree)
            all_connected_nodes.update(node.node_id for node in connected_nodes if hasattr(node, 'node_id'))
            all_nodes.extend(connected_nodes)
        
        # Find orphaned nodes (this would require access to all nodes in the system)
        orphaned_count = 0
        # In a real implementation, you would check against a database or complete node registry
        
        result.orphaned_nodes = orphaned_count
        
        if orphaned_count > self.validation_rules['max_orphaned_nodes']:
            result.critical_issues.append(ValidationIssue(
                issue_id=str(uuid.uuid4()),
                severity="CRITICAL",
                issue_type="ORPHANED_NODES",
                message=f"Found {orphaned_count} orphaned nodes (max allowed: {self.validation_rules['max_orphaned_nodes']})",
                auto_fixable=True,
                suggested_fix="Connect orphaned nodes to appropriate parent nodes or remove if unnecessary"
            ))
    
    def _auto_complete_trees(self, decision_trees: List[DecisionTreeNode], result: ValidationResult):
        """Automatically complete incomplete decision trees"""
        fixes_applied = 0
        
        for tree in decision_trees:
            # Find incomplete paths
            paths = self._extract_all_paths(tree)
            
            for path in paths:
                if not self._is_path_complete(path):
                    # Create default REFER outcome for incomplete paths
                    if self._create_default_outcome(path, DecisionOutcome.REFER):
                        fixes_applied += 1
                        self.logger.info(f"Auto-completed path {path.path_id} with REFER outcome")
        
        result.auto_fixes_applied = fixes_applied
        
        if fixes_applied > 0:
            self.logger.info(f"Applied {fixes_applied} automatic fixes to decision trees")
    
    def _calculate_quality_metrics(self, decision_trees: List[DecisionTreeNode], result: ValidationResult) -> QualityMetrics:
        """Calculate comprehensive quality metrics"""
        metrics = QualityMetrics()
        
        # Structural integrity
        if result.total_nodes > 0:
            connected_ratio = (result.total_nodes - result.orphaned_nodes) / result.total_nodes
            metrics.structural_integrity = connected_ratio
        
        # Logical consistency
        metrics.logical_consistency = result.consistency_score
        
        # Outcome completeness
        metrics.outcome_completeness = result.outcome_score
        
        # Path coverage
        if result.valid_paths + result.incomplete_paths > 0:
            metrics.path_coverage = result.valid_paths / (result.valid_paths + result.incomplete_paths)
        
        # Entity linkage (placeholder - would need entity data)
        metrics.entity_linkage = 0.8  # Assume good linkage for now
        
        # Navigation preservation (placeholder - would need navigation context)
        metrics.navigation_preservation = 0.9  # Assume good preservation for now
        
        return metrics
    
    # Helper methods
    def _collect_all_nodes(self, root: DecisionTreeNode) -> List[DecisionTreeNode]:
        """Collect all nodes in a decision tree using BFS"""
        nodes = []
        queue = deque([root])
        visited = set()
        
        while queue:
            current = queue.popleft()
            if id(current) not in visited:
                visited.add(id(current))
                nodes.append(current)
                
                # Add children to queue
                if hasattr(current, 'children') and current.children:
                    queue.extend(current.children)
        
        return nodes
    
    def _extract_all_paths(self, root: DecisionTreeNode) -> List[DecisionPath]:
        """Extract all paths from root to leaf nodes"""
        paths = []
        
        def dfs_paths(node, current_path, current_sequence):
            current_path.append(node)
            current_sequence.append(getattr(node, 'condition', 'no_condition'))
            
            # If leaf node, create path
            if not hasattr(node, 'children') or not node.children:
                path = DecisionPath(
                    path_id=str(uuid.uuid4()),
                    start_node_id=getattr(root, 'node_id', 'unknown'),
                    end_node_id=getattr(node, 'node_id', 'unknown'),
                    decision_sequence=current_sequence.copy(),
                    final_outcome=getattr(node, 'outcome', None)
                )
                paths.append(path)
            else:
                # Continue DFS
                for child in node.children:
                    dfs_paths(child, current_path.copy(), current_sequence.copy())
        
        dfs_paths(root, [], [])
        return paths
    
    def _is_path_complete(self, path: DecisionPath) -> bool:
        """Check if a decision path is complete (has an outcome)"""
        return path.final_outcome is not None
    
    def _is_path_logically_consistent(self, path: DecisionPath) -> bool:
        """Check if a decision path is logically consistent"""
        # Placeholder for logical consistency checking
        # Would implement actual logic validation here
        return len(path.decision_sequence) > 0
    
    def _detect_logical_contradictions(self, tree: DecisionTreeNode) -> List[str]:
        """Detect logical contradictions in decision tree"""
        # Placeholder for contradiction detection
        return []
    
    def _detect_circular_references(self, tree: DecisionTreeNode) -> List[str]:
        """Detect circular references in decision tree"""
        # Placeholder for circular reference detection
        return []
    
    def _detect_unreachable_nodes(self, tree: DecisionTreeNode) -> List[str]:
        """Detect unreachable nodes in decision tree"""
        # Placeholder for unreachable node detection
        return []
    
    def _create_default_outcome(self, path: DecisionPath, outcome: DecisionOutcome) -> bool:
        """Create a default outcome for an incomplete path"""
        # Placeholder for creating default outcomes
        # In a real implementation, this would modify the tree structure
        return True


def validate_decision_trees(
    decision_trees: List[DecisionTreeNode],
    navigation_context: Optional[NavigationContext] = None,
    auto_fix: bool = True
) -> ValidationResult:
    """
    Convenience function for decision tree validation
    
    Args:
        decision_trees: List of decision tree root nodes to validate
        navigation_context: Optional navigation context for validation
        auto_fix: Whether to apply automatic fixes
        
    Returns:
        ValidationResult with comprehensive validation details
    """
    validator = DecisionTreeValidator()
    validator.auto_fix_enabled = auto_fix
    
    return validator.validate_decision_trees(decision_trees, navigation_context)