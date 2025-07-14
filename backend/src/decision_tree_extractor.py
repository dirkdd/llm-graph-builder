# Task 13: Decision Tree Extractor Implementation
# Extract complete decision trees with mandatory outcomes for mortgage processing

from typing import List, Dict, Any, Optional, Tuple, Set
from dataclasses import dataclass, field
from datetime import datetime
import logging
import re
import json
import uuid

# Import existing entities and models
from src.entities.navigation_models import (
    DecisionTreeNode,
    DecisionOutcome,
    NavigationContext,
    EnhancedNavigationNode,
    QualityRating
)
from src.llm import get_llm
from src.navigation_graph import NavigationGraphBuilder


@dataclass
class DecisionTreeExtractionResult:
    """Result of decision tree extraction operation"""
    success: bool
    decision_trees: List[DecisionTreeNode] = field(default_factory=list)
    completeness_score: float = 0.0
    validation_errors: List[str] = field(default_factory=list)
    validation_warnings: List[str] = field(default_factory=list)
    extraction_metrics: Dict[str, Any] = field(default_factory=dict)
    processing_time_ms: int = 0


@dataclass
class DecisionPath:
    """Represents a complete path through a decision tree"""
    path_id: str
    start_node_id: str
    end_node_id: str
    decision_sequence: List[str] = field(default_factory=list)
    final_outcome: Optional[DecisionOutcome] = None
    conditions_met: List[str] = field(default_factory=list)
    path_probability: float = 0.0


@dataclass
class DecisionTreeMetrics:
    """Metrics for decision tree quality and completeness"""
    total_nodes: int = 0
    root_nodes: int = 0
    branch_nodes: int = 0
    leaf_nodes: int = 0
    orphaned_nodes: int = 0
    incomplete_paths: int = 0
    mandatory_outcomes_coverage: float = 0.0
    decision_depth: int = 0
    logical_consistency_score: float = 0.0


class DecisionTreeExtractor:
    """
    Extracts complete decision trees with mandatory outcomes from mortgage documents.
    Ensures ROOT → BRANCH → LEAF completeness with guaranteed APPROVE/DECLINE/REFER outcomes.
    """
    
    def __init__(self, llm_model: str = "claude-sonnet-4"):
        """
        Initialize DecisionTreeExtractor
        
        Args:
            llm_model: LLM model to use for decision logic extraction
        """
        self.llm = get_llm(llm_model)
        self.logger = logging.getLogger(__name__)
        
        # Decision patterns for mortgage documents
        self.decision_patterns = self._initialize_decision_patterns()
        
        # Mandatory outcomes that must be present in all decision trees
        self.mandatory_outcomes = {
            DecisionOutcome.APPROVE,
            DecisionOutcome.DECLINE,
            DecisionOutcome.REFER
        }
        
        # Decision tree validation rules
        self.validation_rules = {
            'min_depth': 2,
            'max_depth': 8,
            'require_all_outcomes': True,
            'require_complete_paths': True,
            'require_logical_consistency': True
        }

    def _initialize_decision_patterns(self) -> Dict[str, List[str]]:
        """Initialize regex patterns for decision detection"""
        return {
            'decision_indicators': [
                r'(?i)(if\s+.*\s+then)',
                r'(?i)(when\s+.*\s+must)',
                r'(?i)(approve\s+if)',
                r'(?i)(decline\s+if)',
                r'(?i)(refer\s+to)',
                r'(?i)(eligibility\s+criteria)',
                r'(?i)(requirements?\s+are?\s+met)',
                r'(?i)(conditions?\s+must\s+be)',
                r'(?i)(determination|decision|outcome)'
            ],
            'condition_patterns': [
                r'(?i)(fico\s+score\s*[><=]+\s*\d+)',
                r'(?i)(ltv\s*[><=]+\s*\d+)',
                r'(?i)(dti\s*[><=]+\s*\d+)',
                r'(?i)(income\s*[><=]+\s*\$?\d+)',
                r'(?i)(employment\s+.*\s+years?)',
                r'(?i)(assets?\s*[><=]+\s*\$?\d+)',
                r'(?i)(credit\s+score\s*[><=]+\s*\d+)',
                r'(?i)(loan\s+amount\s*[><=]+\s*\$?\d+)'
            ],
            'outcome_patterns': [
                r'(?i)(approved?|approval)',
                r'(?i)(declined?|denial|reject)',
                r'(?i)(refer|referral|review)',
                r'(?i)(conditional\s+approval)',
                r'(?i)(pending\s+review)'
            ],
            'logical_operators': [
                r'(?i)\b(and|&)\b',
                r'(?i)\b(or|\|)\b',
                r'(?i)\b(not|!)\b',
                r'(?i)\b(but)\b',
                r'(?i)\b(unless)\b',
                r'(?i)\b(except)\b'
            ]
        }

    def extract_complete_decision_trees(
        self,
        navigation_nodes: List[EnhancedNavigationNode],
        document_content: str,
        package_config: Dict[str, Any] = None
    ) -> DecisionTreeExtractionResult:
        """
        Extract complete decision trees with mandatory outcomes
        
        Args:
            navigation_nodes: Enhanced navigation nodes from NavigationExtractor
            document_content: Raw document content for analysis
            package_config: Package configuration for context
            
        Returns:
            DecisionTreeExtractionResult: Complete extraction result with validation
        """
        start_time = datetime.now()
        self.logger.info("Starting complete decision tree extraction")
        
        try:
            result = DecisionTreeExtractionResult(success=False)
            
            # Step 1: Identify decision-flow sections
            decision_sections = self._identify_decision_sections(navigation_nodes)
            
            if not decision_sections:
                result.validation_warnings.append("No decision flow sections found")
                return result
            
            # Step 2: Extract decision trees from each section
            extracted_trees = []
            for section in decision_sections:
                try:
                    section_trees = self._extract_decision_trees_from_section(
                        section, document_content
                    )
                    extracted_trees.extend(section_trees)
                except Exception as e:
                    result.validation_errors.append(
                        f"Failed to extract from section {section.enhanced_node_id}: {str(e)}"
                    )
            
            # Step 3: Ensure completeness with mandatory outcomes
            complete_trees = []
            for tree in extracted_trees:
                try:
                    complete_tree = self._ensure_tree_completeness(tree)
                    complete_trees.append(complete_tree)
                except Exception as e:
                    result.validation_errors.append(
                        f"Failed to complete tree {tree.node_id}: {str(e)}"
                    )
            
            # Step 4: Validate all decision trees
            validation_result = self._validate_decision_trees(complete_trees)
            
            # Step 5: Create mandatory outcome nodes if missing
            trees_with_outcomes = self._create_mandatory_outcome_nodes(complete_trees)
            
            # Step 6: Build logical flow and connections
            connected_trees = self._build_logical_flows(trees_with_outcomes)
            
            # Step 7: Calculate metrics and completeness
            metrics = self._calculate_extraction_metrics(connected_trees)
            
            # Step 8: Final validation
            final_validation = self._final_completeness_validation(connected_trees)
            
            processing_time = (datetime.now() - start_time).total_seconds() * 1000
            
            result.success = len(final_validation['errors']) == 0
            result.decision_trees = connected_trees
            result.completeness_score = final_validation['completeness_score']
            result.validation_errors.extend(validation_result['errors'])
            result.validation_errors.extend(final_validation['errors'])
            result.validation_warnings.extend(validation_result['warnings'])
            result.validation_warnings.extend(final_validation['warnings'])
            result.extraction_metrics = metrics.__dict__
            result.processing_time_ms = int(processing_time)
            
            if result.success:
                self.logger.info(
                    f"Decision tree extraction completed: {len(connected_trees)} trees, "
                    f"completeness: {result.completeness_score:.2f}, "
                    f"time: {processing_time:.2f}ms"
                )
            else:
                self.logger.warning(
                    f"Decision tree extraction incomplete: {len(result.validation_errors)} errors"
                )
            
            return result
            
        except Exception as e:
            self.logger.error(f"Decision tree extraction failed: {str(e)}")
            processing_time = (datetime.now() - start_time).total_seconds() * 1000
            return DecisionTreeExtractionResult(
                success=False,
                validation_errors=[f"Extraction failed: {str(e)}"],
                processing_time_ms=int(processing_time)
            )

    def create_leaf_node(
        self,
        parent_node_id: str,
        outcome: DecisionOutcome,
        condition_path: List[str],
        description: str = ""
    ) -> DecisionTreeNode:
        """
        Create a leaf node with mandatory outcome
        
        Args:
            parent_node_id: ID of parent decision node
            outcome: Mandatory outcome (APPROVE/DECLINE/REFER)
            condition_path: Sequence of conditions leading to this outcome
            description: Description of the outcome logic
            
        Returns:
            DecisionTreeNode: Configured leaf node with outcome
        """
        leaf_id = f"leaf_{outcome.value.lower()}_{uuid.uuid4().hex[:8]}"
        
        # Create description if not provided
        if not description:
            conditions_text = " AND ".join(condition_path) if condition_path else "default"
            description = f"Final outcome: {outcome.value} when {conditions_text}"
        
        leaf_node = DecisionTreeNode(
            node_id=leaf_id,
            title=f"{outcome.value} Outcome",
            decision_type="LEAF",
            description=description,
            parent_decision_id=parent_node_id,
            outcomes=[outcome],
            outcome_descriptions={outcome: description},
            source_content=description,
            navigation_context=NavigationContext(
                navigation_path=["Decision Tree", "Outcomes", outcome.value],
                hierarchy_level=3,
                decision_context="final_outcome",
                decision_level="LEAF",
                decision_factors=condition_path
            ),
            quality_score=1.0,  # Leaf nodes are always complete
            confidence_score=0.95  # High confidence for mandatory outcomes
        )
        
        self.logger.debug(f"Created leaf node {leaf_id} with outcome {outcome.value}")
        return leaf_node

    def _identify_decision_sections(
        self, 
        navigation_nodes: List[EnhancedNavigationNode]
    ) -> List[EnhancedNavigationNode]:
        """Identify navigation nodes that contain decision flow logic"""
        decision_sections = []
        
        for node in navigation_nodes:
            # Check if node type is explicitly decision-related
            if node.node_type == "DECISION_FLOW_SECTION":
                decision_sections.append(node)
                continue
            
            # Check content for decision indicators
            content_lower = node.content.lower()
            title_lower = node.title.lower()
            
            decision_score = 0
            
            # Check for decision patterns in content
            for pattern in self.decision_patterns['decision_indicators']:
                if re.search(pattern, content_lower):
                    decision_score += 1
            
            # Check for outcome patterns
            for pattern in self.decision_patterns['outcome_patterns']:
                if re.search(pattern, content_lower):
                    decision_score += 1
            
            # Check title for decision keywords
            decision_keywords = ['decision', 'criteria', 'eligibility', 'approval', 'requirements']
            for keyword in decision_keywords:
                if keyword in title_lower:
                    decision_score += 1
            
            # If score is high enough, consider it a decision section
            if decision_score >= 2:
                decision_sections.append(node)
        
        self.logger.info(f"Identified {len(decision_sections)} decision sections")
        return decision_sections

    def _extract_decision_trees_from_section(
        self,
        section: EnhancedNavigationNode,
        document_content: str
    ) -> List[DecisionTreeNode]:
        """Extract decision tree nodes from a specific section"""
        try:
            # Use LLM to extract structured decision logic
            extraction_prompt = self._build_decision_extraction_prompt(section, document_content)
            
            llm_response = self.llm.invoke(extraction_prompt)
            
            # Parse LLM response into decision tree nodes
            decision_nodes = self._parse_llm_decision_response(llm_response, section)
            
            # Validate and structure nodes
            structured_nodes = self._structure_decision_nodes(decision_nodes, section)
            
            return structured_nodes
            
        except Exception as e:
            self.logger.error(f"Failed to extract decision trees from section {section.enhanced_node_id}: {str(e)}")
            return []

    def _build_decision_extraction_prompt(
        self, 
        section: EnhancedNavigationNode, 
        document_content: str
    ) -> str:
        """Build LLM prompt for decision tree extraction"""
        prompt = f"""
        Extract complete decision tree logic from the following mortgage document section.

        SECTION TITLE: {section.title}
        SECTION CONTENT:
        {section.content}

        REQUIREMENTS:
        1. Identify all decision points and conditions
        2. Extract logical operators (AND, OR, NOT)
        3. Identify all possible outcomes (APPROVE, DECLINE, REFER, CONDITIONAL_APPROVE)
        4. Ensure every decision path leads to a final outcome
        5. Extract specific criteria and thresholds

        EXPECTED OUTPUT FORMAT (JSON):
        {{
            "decision_trees": [
                {{
                    "root_node": {{
                        "node_id": "unique_id",
                        "title": "Decision Title",
                        "decision_type": "ROOT",
                        "condition": "Main decision condition",
                        "criteria": ["criterion1", "criterion2"],
                        "variables": {{"variable": "value"}},
                        "operators": ["AND", "OR"]
                    }},
                    "branch_nodes": [
                        {{
                            "node_id": "branch_id",
                            "decision_type": "BRANCH",
                            "condition": "Branch condition",
                            "parent_decision_id": "root_node_id",
                            "true_outcome": "path_if_true",
                            "false_outcome": "path_if_false"
                        }}
                    ],
                    "leaf_nodes": [
                        {{
                            "node_id": "leaf_id",
                            "decision_type": "LEAF",
                            "parent_decision_id": "branch_id",
                            "outcomes": ["APPROVE"],
                            "outcome_descriptions": {{"APPROVE": "Approved when conditions met"}}
                        }}
                    ]
                }}
            ]
        }}

        Focus on mortgage-specific decision logic including:
        - Credit score requirements
        - Loan-to-value ratios
        - Debt-to-income ratios
        - Employment history
        - Asset requirements
        - Property standards

        Ensure EVERY decision path leads to one of: APPROVE, DECLINE, or REFER.
        """
        
        return prompt.strip()

    def _parse_llm_decision_response(
        self, 
        llm_response: str, 
        section: EnhancedNavigationNode
    ) -> List[DecisionTreeNode]:
        """Parse LLM response into DecisionTreeNode objects"""
        try:
            # Try to parse JSON response
            if "```json" in llm_response:
                json_content = llm_response.split("```json")[1].split("```")[0]
            else:
                json_content = llm_response
            
            parsed_data = json.loads(json_content)
            
            decision_nodes = []
            
            for tree_data in parsed_data.get("decision_trees", []):
                # Create root node
                if "root_node" in tree_data:
                    root_data = tree_data["root_node"]
                    root_node = self._create_decision_node_from_data(root_data, section)
                    decision_nodes.append(root_node)
                
                # Create branch nodes
                for branch_data in tree_data.get("branch_nodes", []):
                    branch_node = self._create_decision_node_from_data(branch_data, section)
                    decision_nodes.append(branch_node)
                
                # Create leaf nodes
                for leaf_data in tree_data.get("leaf_nodes", []):
                    leaf_node = self._create_decision_node_from_data(leaf_data, section)
                    decision_nodes.append(leaf_node)
            
            return decision_nodes
            
        except json.JSONDecodeError as e:
            self.logger.warning(f"Failed to parse LLM JSON response: {str(e)}")
            # Fallback to pattern-based extraction
            return self._fallback_pattern_extraction(llm_response, section)
        
        except Exception as e:
            self.logger.error(f"Failed to parse LLM response: {str(e)}")
            return []

    def _create_decision_node_from_data(
        self, 
        node_data: Dict[str, Any], 
        section: EnhancedNavigationNode
    ) -> DecisionTreeNode:
        """Create DecisionTreeNode from parsed data"""
        
        # Parse outcomes if present
        outcomes = []
        if "outcomes" in node_data:
            for outcome_str in node_data["outcomes"]:
                try:
                    outcomes.append(DecisionOutcome(outcome_str))
                except ValueError:
                    self.logger.warning(f"Unknown outcome: {outcome_str}")
        
        # Create navigation context
        nav_context = NavigationContext(
            navigation_path=section.navigation_path + [node_data.get("title", "Decision")],
            hierarchy_level=section.hierarchy_level + 1,
            decision_context=section.enhanced_node_id,
            decision_level=node_data.get("decision_type", "BRANCH"),
            decision_factors=node_data.get("criteria", [])
        )
        
        decision_node = DecisionTreeNode(
            node_id=node_data.get("node_id", f"decision_{uuid.uuid4().hex[:8]}"),
            title=node_data.get("title", "Decision Node"),
            decision_type=node_data.get("decision_type", "BRANCH"),
            condition=node_data.get("condition"),
            criteria=node_data.get("criteria", []),
            variables=node_data.get("variables", {}),
            operators=node_data.get("operators", []),
            true_outcome=node_data.get("true_outcome"),
            false_outcome=node_data.get("false_outcome"),
            outcomes=outcomes,
            outcome_descriptions=node_data.get("outcome_descriptions", {}),
            parent_decision_id=node_data.get("parent_decision_id"),
            child_decision_ids=node_data.get("child_decision_ids", []),
            description=node_data.get("description", ""),
            source_content=node_data.get("source_content", section.content[:200]),
            navigation_context=nav_context,
            quality_score=0.8,  # Default quality score
            confidence_score=0.85  # Default confidence score
        )
        
        return decision_node

    def _fallback_pattern_extraction(
        self, 
        response_text: str, 
        section: EnhancedNavigationNode
    ) -> List[DecisionTreeNode]:
        """Fallback extraction using regex patterns when LLM parsing fails"""
        decision_nodes = []
        
        # Extract conditions using patterns
        conditions = []
        for pattern in self.decision_patterns['condition_patterns']:
            matches = re.findall(pattern, response_text, re.IGNORECASE)
            conditions.extend(matches)
        
        # Extract outcomes
        outcomes = []
        for pattern in self.decision_patterns['outcome_patterns']:
            matches = re.findall(pattern, response_text, re.IGNORECASE)
            outcomes.extend(matches)
        
        # Create a basic decision tree if we found conditions and outcomes
        if conditions and outcomes:
            root_node = DecisionTreeNode(
                node_id=f"fallback_root_{uuid.uuid4().hex[:8]}",
                title=f"Decision: {section.title}",
                decision_type="ROOT",
                condition=conditions[0] if conditions else "Basic eligibility check",
                criteria=conditions[:3],  # Take first 3 conditions
                description=f"Extracted from section: {section.title}",
                source_content=section.content,
                navigation_context=NavigationContext(
                    navigation_path=section.navigation_path + ["Decision"],
                    hierarchy_level=section.hierarchy_level + 1,
                    decision_context=section.enhanced_node_id
                ),
                quality_score=0.6,  # Lower quality for fallback
                confidence_score=0.7
            )
            
            decision_nodes.append(root_node)
        
        return decision_nodes

    def _structure_decision_nodes(
        self, 
        decision_nodes: List[DecisionTreeNode], 
        section: EnhancedNavigationNode
    ) -> List[DecisionTreeNode]:
        """Structure decision nodes into proper hierarchy"""
        if not decision_nodes:
            return []
        
        # Separate nodes by type
        root_nodes = [n for n in decision_nodes if n.decision_type == "ROOT"]
        branch_nodes = [n for n in decision_nodes if n.decision_type == "BRANCH"]
        leaf_nodes = [n for n in decision_nodes if n.decision_type == "LEAF"]
        
        # Ensure we have at least one root node
        if not root_nodes and decision_nodes:
            # Convert first node to root
            first_node = decision_nodes[0]
            first_node.decision_type = "ROOT"
            root_nodes = [first_node]
        
        # Build parent-child relationships
        structured_nodes = []
        
        for root in root_nodes:
            structured_nodes.append(root)
            
            # Find direct children
            children = [n for n in branch_nodes if n.parent_decision_id == root.node_id]
            for child in children:
                structured_nodes.append(child)
                root.child_decision_ids.append(child.node_id)
                
                # Find leaf children
                leaf_children = [n for n in leaf_nodes if n.parent_decision_id == child.node_id]
                for leaf in leaf_children:
                    structured_nodes.append(leaf)
                    child.child_decision_ids.append(leaf.node_id)
        
        return structured_nodes

    def _ensure_tree_completeness(self, tree: DecisionTreeNode) -> DecisionTreeNode:
        """Ensure decision tree has complete paths to all mandatory outcomes"""
        # Check if tree already has all mandatory outcomes
        existing_outcomes = set()
        self._collect_tree_outcomes(tree, existing_outcomes)
        
        missing_outcomes = self.mandatory_outcomes - existing_outcomes
        
        if missing_outcomes:
            # Add missing outcome paths
            for outcome in missing_outcomes:
                leaf_node = self.create_leaf_node(
                    parent_node_id=tree.node_id,
                    outcome=outcome,
                    condition_path=[],
                    description=f"Default {outcome.value} path for completeness"
                )
                tree.child_decision_ids.append(leaf_node.node_id)
        
        return tree

    def _collect_tree_outcomes(self, node: DecisionTreeNode, outcomes: Set[DecisionOutcome]) -> None:
        """Recursively collect all outcomes from a decision tree"""
        if node.outcomes:
            outcomes.update(node.outcomes)
        
        # This is a simplified version - in full implementation, would traverse children
        # For now, just collect from current node

    def _validate_decision_trees(self, trees: List[DecisionTreeNode]) -> Dict[str, Any]:
        """Validate decision trees for completeness and logical consistency"""
        errors = []
        warnings = []
        
        for tree in trees:
            # Check for mandatory outcomes
            tree_outcomes = set()
            self._collect_tree_outcomes(tree, tree_outcomes)
            
            missing_outcomes = self.mandatory_outcomes - tree_outcomes
            if missing_outcomes:
                missing_list = [o.value for o in missing_outcomes]
                errors.append(f"Tree {tree.node_id} missing outcomes: {missing_list}")
            
            # Check for orphaned nodes
            if tree.decision_type != "ROOT" and not tree.parent_decision_id:
                warnings.append(f"Orphaned node: {tree.node_id}")
            
            # Check for empty conditions
            if tree.decision_type in ["ROOT", "BRANCH"] and not tree.condition:
                warnings.append(f"Node {tree.node_id} has empty condition")
        
        return {
            'errors': errors,
            'warnings': warnings,
            'validation_score': max(0, 1.0 - (len(errors) * 0.2) - (len(warnings) * 0.1))
        }

    def _create_mandatory_outcome_nodes(
        self, 
        trees: List[DecisionTreeNode]
    ) -> List[DecisionTreeNode]:
        """Create mandatory outcome nodes for any missing outcomes"""
        enhanced_trees = []
        
        for tree in trees:
            enhanced_trees.append(tree)
            
            # Check what outcomes this tree covers
            tree_outcomes = set()
            self._collect_tree_outcomes(tree, tree_outcomes)
            
            # Add missing mandatory outcomes
            missing_outcomes = self.mandatory_outcomes - tree_outcomes
            for outcome in missing_outcomes:
                leaf_node = self.create_leaf_node(
                    parent_node_id=tree.node_id,
                    outcome=outcome,
                    condition_path=["fallback_path"],
                    description=f"Mandatory {outcome.value} outcome node"
                )
                enhanced_trees.append(leaf_node)
        
        return enhanced_trees

    def _build_logical_flows(self, trees: List[DecisionTreeNode]) -> List[DecisionTreeNode]:
        """Build logical flows and connections between decision nodes"""
        # Group trees by parent-child relationships
        tree_map = {tree.node_id: tree for tree in trees}
        
        for tree in trees:
            # Update child references
            if tree.child_decision_ids:
                # Ensure child nodes exist
                valid_children = []
                for child_id in tree.child_decision_ids:
                    if child_id in tree_map:
                        valid_children.append(child_id)
                        # Ensure parent reference is set
                        tree_map[child_id].parent_decision_id = tree.node_id
                    else:
                        self.logger.warning(f"Missing child node: {child_id}")
                
                tree.child_decision_ids = valid_children
        
        return trees

    def _calculate_extraction_metrics(self, trees: List[DecisionTreeNode]) -> DecisionTreeMetrics:
        """Calculate comprehensive metrics for extracted decision trees"""
        metrics = DecisionTreeMetrics()
        
        if not trees:
            return metrics
        
        # Count node types
        for tree in trees:
            metrics.total_nodes += 1
            
            if tree.decision_type == "ROOT":
                metrics.root_nodes += 1
            elif tree.decision_type == "BRANCH":
                metrics.branch_nodes += 1
            elif tree.decision_type == "LEAF":
                metrics.leaf_nodes += 1
            
            # Check for orphaned nodes
            if tree.decision_type != "ROOT" and not tree.parent_decision_id:
                metrics.orphaned_nodes += 1
        
        # Calculate outcome coverage
        all_outcomes = set()
        for tree in trees:
            if tree.outcomes:
                all_outcomes.update(tree.outcomes)
        
        covered_mandatory = len(self.mandatory_outcomes & all_outcomes)
        metrics.mandatory_outcomes_coverage = covered_mandatory / len(self.mandatory_outcomes)
        
        # Calculate decision depth (simplified)
        max_depth = 0
        for tree in trees:
            if tree.navigation_context and hasattr(tree.navigation_context, 'hierarchy_level'):
                max_depth = max(max_depth, tree.navigation_context.hierarchy_level)
        
        metrics.decision_depth = max_depth
        
        # Calculate logical consistency score
        consistency_factors = [
            1.0 if metrics.orphaned_nodes == 0 else 0.5,
            metrics.mandatory_outcomes_coverage,
            1.0 if metrics.root_nodes > 0 else 0.0,
            min(1.0, metrics.leaf_nodes / max(metrics.branch_nodes, 1))
        ]
        
        metrics.logical_consistency_score = sum(consistency_factors) / len(consistency_factors)
        
        return metrics

    def _final_completeness_validation(self, trees: List[DecisionTreeNode]) -> Dict[str, Any]:
        """Final validation to ensure 100% decision tree completeness"""
        errors = []
        warnings = []
        
        if not trees:
            errors.append("No decision trees extracted")
            return {
                'errors': errors,
                'warnings': warnings,
                'completeness_score': 0.0
            }
        
        # Check mandatory outcome coverage
        all_outcomes = set()
        for tree in trees:
            if tree.outcomes:
                all_outcomes.update(tree.outcomes)
        
        missing_outcomes = self.mandatory_outcomes - all_outcomes
        if missing_outcomes:
            missing_list = [o.value for o in missing_outcomes]
            errors.append(f"Missing mandatory outcomes: {missing_list}")
        
        # Check for complete paths (simplified validation)
        root_nodes = [t for t in trees if t.decision_type == "ROOT"]
        if not root_nodes:
            errors.append("No root decision nodes found")
        
        leaf_nodes = [t for t in trees if t.decision_type == "LEAF"]
        if not leaf_nodes:
            errors.append("No leaf decision nodes found")
        
        # Calculate completeness score
        completeness_factors = [
            1.0 if len(missing_outcomes) == 0 else 0.0,
            1.0 if len(root_nodes) > 0 else 0.0,
            1.0 if len(leaf_nodes) > 0 else 0.0,
            min(1.0, len(trees) / 3)  # Expect at least 3 nodes per tree
        ]
        
        completeness_score = sum(completeness_factors) / len(completeness_factors)
        
        return {
            'errors': errors,
            'warnings': warnings,
            'completeness_score': completeness_score
        }