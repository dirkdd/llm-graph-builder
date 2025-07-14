# Phase 1.3: Guidelines Navigation Processing System

## Overview
The Guidelines Navigation Processing System implements sophisticated extraction and processing of mortgage guidelines documents, focusing on complete decision tree extraction with mandatory ROOT → BRANCH → LEAF paths. This system ensures every decision in the guidelines has a complete path to final outcomes.

## Core Requirements

### Decision Tree Completeness
Every decision-making section MUST have:
1. **ROOT Nodes**: 1-3 primary policy entry points per document
2. **BRANCH Nodes**: 5-15 evaluation criteria per document
3. **LEAF Nodes**: Minimum 6 per document (at least 2 per ROOT)
   - APPROVE outcomes
   - DECLINE outcomes
   - REFER (manual review) outcomes

## System Architecture

### 1. Navigation Graph Builder (`navigation_graph.py`)

```python
class NavigationGraphBuilder:
    """Builds comprehensive navigation graph from guidelines"""
    
    def __init__(self, llm_model: str = "claude-sonnet-4"):
        self.llm = get_llm(llm_model)
        self.prompt_engine = GuidelinesPromptEngine()
        
    def build_navigation_graph(self, document: Document, package_config: PackageConfig) -> NavigationGraph:
        """Build complete navigation graph with decision trees"""
        
        # Step 1: Extract navigation structure using specialized prompt
        nav_prompt = self.prompt_engine.get_navigation_extraction_prompt(
            document_type="guidelines",
            category=package_config.category,
            product_name=package_config.product_name
        )
        
        nav_structure = self.llm.extract_with_prompt(document, nav_prompt)
        
        # Step 2: Validate and enhance navigation nodes
        enhanced_nodes = self.enhance_navigation_nodes(nav_structure.nodes)
        
        # Step 3: Extract decision trees with mandatory completion
        decision_trees = self.extract_complete_decision_trees(enhanced_nodes)
        
        # Step 4: Create navigation relationships
        relationships = self.create_navigation_relationships(enhanced_nodes)
        
        # Step 5: Validate completeness
        validation_result = self.validate_navigation_completeness(
            nodes=enhanced_nodes,
            trees=decision_trees,
            relationships=relationships
        )
        
        if not validation_result.is_complete:
            # Force creation of missing LEAF nodes
            enhanced_nodes, decision_trees = self.complete_decision_trees(
                enhanced_nodes, decision_trees, validation_result.missing_elements
            )
        
        return NavigationGraph(
            nodes=enhanced_nodes,
            decision_trees=decision_trees,
            relationships=relationships,
            metadata=self.build_graph_metadata(document)
        )
    
    def enhance_navigation_nodes(self, raw_nodes: List[Dict]) -> List[NavigationNode]:
        """Enhance raw navigation nodes with full context"""
        enhanced_nodes = []
        
        for raw_node in raw_nodes:
            node = NavigationNode(
                enhanced_node_id=self.generate_enhanced_id(raw_node),
                node_type=raw_node['node_type'],
                title=raw_node['title'],
                raw_summary=raw_node['raw_summary'],
                hierarchy_markers=HierarchyMarkers(**raw_node['hierarchy_markers']),
                scope_hints=ScopeHints(**raw_node['scope_hints']),
                decision_tree_metadata=self.process_decision_metadata(
                    raw_node.get('decision_tree_metadata', {})
                )
            )
            
            # Identify decision flow sections
            if self.is_decision_section(node):
                node.node_type = "DECISION_FLOW_SECTION"
                node.requires_complete_tree = True
            
            enhanced_nodes.append(node)
        
        return enhanced_nodes
    
    def extract_complete_decision_trees(self, nodes: List[NavigationNode]) -> List[DecisionTree]:
        """Extract decision trees ensuring complete paths"""
        decision_trees = []
        decision_sections = [n for n in nodes if n.requires_complete_tree]
        
        for section in decision_sections:
            tree = DecisionTree(section_id=section.enhanced_node_id)
            
            # Step 1: Identify ROOT node (policy entry)
            root_node = self.extract_root_node(section, nodes)
            if not root_node:
                root_node = self.create_default_root_node(section)
            tree.root = root_node
            
            # Step 2: Extract BRANCH nodes (criteria)
            branch_nodes = self.extract_branch_nodes(section, nodes)
            if len(branch_nodes) < 2:
                # Ensure minimum branches
                branch_nodes.extend(self.create_default_branches(section, 2 - len(branch_nodes)))
            tree.branches = branch_nodes
            
            # Step 3: Extract/Create LEAF nodes (MANDATORY)
            leaf_nodes = self.extract_leaf_nodes(section, nodes)
            
            # Ensure minimum LEAF nodes
            required_leaves = {
                "APPROVE": "Loan Approved - Guidelines Satisfied",
                "DECLINE": "Loan Declined - Guidelines Not Met",
                "REFER": "Manual Review Required"
            }
            
            existing_outcomes = {leaf.outcome for leaf in leaf_nodes}
            
            for outcome, title in required_leaves.items():
                if outcome not in existing_outcomes:
                    leaf_nodes.append(self.create_leaf_node(
                        section=section,
                        outcome=outcome,
                        title=title
                    ))
            
            tree.leaves = leaf_nodes
            
            # Step 4: Create decision paths
            tree.paths = self.create_decision_paths(root_node, branch_nodes, leaf_nodes)
            
            # Validate tree completeness
            if self.validate_tree_completeness(tree):
                decision_trees.append(tree)
            
        return decision_trees
    
    def create_leaf_node(self, section: NavigationNode, outcome: str, title: str) -> DecisionLeafNode:
        """Create a mandatory LEAF node"""
        return DecisionLeafNode(
            temp_id=f"nav_temp_{98 if outcome == 'APPROVE' else 99 if outcome == 'DECLINE' else 97}",
            enhanced_node_id=f"{section.enhanced_node_id}_{outcome.lower()}",
            node_type="DECISION_FLOW_SECTION",
            title=title,
            raw_summary=self.generate_leaf_summary(outcome),
            hierarchy_markers={
                "chapter_number": section.hierarchy_markers.chapter_number,
                "depth_level": section.hierarchy_markers.depth_level + 1,
                "decision_precedence": 98 if outcome == 'APPROVE' else 99 if outcome == 'DECLINE' else 97
            },
            decision_tree_metadata={
                "contains_decision_logic": True,
                "decision_types": ["LEAF" if outcome != "REFER" else "TERMINAL"],
                "decision_type": "LEAF" if outcome != "REFER" else "TERMINAL",
                "evaluation_precedence": 98 if outcome == 'APPROVE' else 99 if outcome == 'DECLINE' else 97,
                "logical_expression": self.generate_leaf_logic(outcome),
                "decision_outcomes": [outcome],
                "default_outcome": {
                    "action": outcome,
                    "message": self.generate_outcome_message(outcome)
                }
            }
        )
```

### 2. Decision Tree Extractor (`decision_tree_extractor.py`)

```python
class DecisionTreeExtractor:
    """Extracts and validates complete decision trees"""
    
    def __init__(self):
        self.validation_rules = DecisionTreeValidationRules()
        
    def extract_decision_tree_from_section(self, section: NavigationNode, context: List[NavigationNode]) -> DecisionTree:
        """Extract a complete decision tree from a section"""
        
        # Identify decision elements in section content
        decision_elements = self.identify_decision_elements(section)
        
        # Build tree structure
        tree = DecisionTree()
        
        # ROOT: Find primary policy or decision entry
        root_candidates = self.find_root_candidates(decision_elements)
        tree.root = self.select_best_root(root_candidates) or self.create_default_root(section)
        
        # BRANCHES: Extract evaluation criteria
        branch_candidates = self.find_branch_candidates(decision_elements)
        tree.branches = self.organize_branches(branch_candidates)
        
        # LEAVES: Extract or create final outcomes
        leaf_candidates = self.find_leaf_candidates(decision_elements)
        tree.leaves = self.ensure_complete_leaves(leaf_candidates)
        
        # Create logical flow
        tree.flow = self.create_logical_flow(tree.root, tree.branches, tree.leaves)
        
        return tree
    
    def ensure_complete_leaves(self, candidates: List[DecisionElement]) -> List[DecisionLeafNode]:
        """Ensure all required LEAF nodes exist"""
        leaves = []
        found_outcomes = set()
        
        # Process existing candidates
        for candidate in candidates:
            leaf = self.create_leaf_from_candidate(candidate)
            leaves.append(leaf)
            found_outcomes.add(leaf.outcome)
        
        # Add missing mandatory outcomes
        mandatory_outcomes = ["APPROVE", "DECLINE", "REFER"]
        
        for outcome in mandatory_outcomes:
            if outcome not in found_outcomes:
                leaves.append(self.create_mandatory_leaf(outcome))
        
        return leaves
    
    def create_logical_flow(self, root: DecisionNode, branches: List[DecisionNode], leaves: List[DecisionNode]) -> DecisionFlow:
        """Create the logical flow from ROOT through BRANCHES to LEAVES"""
        flow = DecisionFlow()
        
        # Connect ROOT to initial BRANCHES
        initial_branches = [b for b in branches if b.evaluation_precedence < 10]
        for branch in initial_branches:
            flow.add_connection(root.id, branch.id, "EVALUATES")
        
        # Connect BRANCHES to other BRANCHES or LEAVES
        for i, branch in enumerate(branches):
            # Find next branches in sequence
            next_branches = [b for b in branches if b.evaluation_precedence == branch.evaluation_precedence + 1]
            
            if next_branches:
                for next_branch in next_branches:
                    flow.add_connection(branch.id, next_branch.id, "LEADS_TO")
            else:
                # Connect to appropriate LEAF based on logic
                appropriate_leaves = self.match_branch_to_leaves(branch, leaves)
                for leaf in appropriate_leaves:
                    flow.add_connection(branch.id, leaf.id, "RESULTS_IN")
        
        # Ensure all LEAVES are connected
        for leaf in leaves:
            if not flow.has_incoming_connections(leaf.id):
                # Connect to most relevant branch
                best_branch = self.find_best_branch_for_leaf(leaf, branches)
                flow.add_connection(best_branch.id, leaf.id, "DEFAULT_OUTCOME")
        
        return flow
```

### 3. Guidelines Entity Extractor (`guideline_entity_extractor.py`)

```python
class GuidelineEntityExtractor:
    """Extracts mortgage-specific entities from guidelines"""
    
    def __init__(self, llm_model: str = "claude-sonnet-4"):
        self.llm = get_llm(llm_model)
        self.entity_patterns = MortgageEntityPatterns()
        
    def extract_entities_with_context(self, nav_graph: NavigationGraph) -> List[ContextualEntity]:
        """Extract entities maintaining navigation context"""
        entities = []
        
        for node in nav_graph.nodes:
            # Extract entities from this navigation node
            node_entities = self.extract_node_entities(node)
            
            # Add navigation context to each entity
            for entity in node_entities:
                contextual_entity = ContextualEntity(
                    entity=entity,
                    navigation_context={
                        "node_id": node.enhanced_node_id,
                        "node_type": node.node_type,
                        "navigation_path": self.build_navigation_path(node, nav_graph),
                        "chapter": node.hierarchy_markers.chapter_number,
                        "section": node.hierarchy_markers.section_number
                    },
                    decision_context=self.get_decision_context(entity, nav_graph)
                )
                entities.append(contextual_entity)
        
        # Extract decision tree entities
        decision_entities = self.extract_decision_entities(nav_graph.decision_trees)
        entities.extend(decision_entities)
        
        return entities
    
    def extract_node_entities(self, node: NavigationNode) -> List[Entity]:
        """Extract entities from a navigation node"""
        entities = []
        
        # Entity types to extract
        entity_types = [
            ("LOAN_PROGRAM", self.entity_patterns.loan_program_patterns),
            ("BORROWER_TYPE", self.entity_patterns.borrower_type_patterns),
            ("REQUIREMENT", self.entity_patterns.requirement_patterns),
            ("NUMERIC_THRESHOLD", self.entity_patterns.threshold_patterns),
            ("PROPERTY_TYPE", self.entity_patterns.property_patterns),
            ("COMPLIANCE_ITEM", self.entity_patterns.compliance_patterns)
        ]
        
        for entity_type, patterns in entity_types:
            found_entities = self.find_entities_by_pattern(
                node.raw_summary, 
                patterns, 
                entity_type
            )
            entities.extend(found_entities)
        
        # Use LLM for complex entity extraction
        if node.node_type == "DECISION_FLOW_SECTION":
            llm_entities = self.extract_decision_entities_with_llm(node)
            entities.extend(llm_entities)
        
        return entities
    
    def extract_decision_entities(self, decision_trees: List[DecisionTree]) -> List[ContextualEntity]:
        """Extract entities from decision trees"""
        entities = []
        
        for tree in decision_trees:
            # ROOT entity
            root_entity = Entity(
                temp_entity_id=f"ent_{tree.root.id}",
                enhanced_entity_id=f"{tree.root.enhanced_node_id}_entity",
                entity_type="DECISION_TREE_NODE",
                primary_mention=tree.root.title,
                raw_context=tree.root.raw_summary,
                matrix_decision_metadata={
                    "decision_type": "ROOT",
                    "evaluation_precedence": tree.root.evaluation_precedence,
                    "logical_expression": tree.root.logical_expression
                }
            )
            entities.append(self.contextualize_entity(root_entity, tree))
            
            # BRANCH entities
            for branch in tree.branches:
                branch_entity = self.create_branch_entity(branch, tree)
                entities.append(branch_entity)
            
            # LEAF entities (guaranteed to exist)
            for leaf in tree.leaves:
                leaf_entity = self.create_leaf_entity(leaf, tree)
                entities.append(leaf_entity)
        
        return entities
```

## Data Models

### Navigation Models

```python
@dataclass
class NavigationNode:
    """Enhanced navigation node with decision capabilities"""
    enhanced_node_id: str  # e.g., "NQM_titanium_001"
    node_type: str  # CHAPTER, SECTION, SUBSECTION, DECISION_FLOW_SECTION
    title: str
    raw_summary: str
    
    # Hierarchy
    hierarchy_markers: HierarchyMarkers
    scope_hints: ScopeHints
    
    # Decision tree metadata
    decision_tree_metadata: Optional[DecisionTreeMetadata]
    requires_complete_tree: bool = False
    
    # Relationships
    parent_id: Optional[str] = None
    children_ids: List[str] = field(default_factory=list)

@dataclass
class DecisionTree:
    """Complete decision tree structure"""
    section_id: str
    root: DecisionNode
    branches: List[DecisionNode]
    leaves: List[DecisionLeafNode]  # MANDATORY - minimum 3
    flow: DecisionFlow
    paths: List[DecisionPath]
    
    def is_complete(self) -> bool:
        """Validate tree completeness"""
        has_root = self.root is not None
        has_branches = len(self.branches) >= 2
        has_all_leaves = (
            any(l.outcome == "APPROVE" for l in self.leaves) and
            any(l.outcome == "DECLINE" for l in self.leaves) and
            len(self.leaves) >= 3
        )
        all_connected = all(self.flow.is_connected(l.id) for l in self.leaves)
        
        return has_root and has_branches and has_all_leaves and all_connected

@dataclass
class DecisionLeafNode:
    """Mandatory leaf node for decision outcomes"""
    enhanced_node_id: str
    node_type: str = "DECISION_FLOW_SECTION"
    title: str
    outcome: str  # APPROVE, DECLINE, REFER
    
    # Decision metadata
    decision_type: str  # LEAF or TERMINAL
    evaluation_precedence: int  # 90-99
    logical_expression: str
    default_outcome: DecisionOutcome
    
    # Context
    dependencies: List[str]
    exception_rules: List[ExceptionRule]
```

### Entity Models

```python
@dataclass
class ContextualEntity:
    """Entity with full navigation and decision context"""
    entity: Entity
    navigation_context: NavigationContext
    decision_context: Optional[DecisionContext]
    
    def get_full_path(self) -> str:
        """Get complete navigation path to entity"""
        return self.navigation_context['navigation_path']
    
    def is_decision_entity(self) -> bool:
        """Check if entity is part of decision tree"""
        return self.decision_context is not None

@dataclass
class MortgageEntity(Entity):
    """Specialized mortgage entity"""
    entity_type: str  # LOAN_PROGRAM, BORROWER_TYPE, etc.
    primary_mention: str
    
    # Mortgage-specific attributes
    program_details: Optional[Dict]
    borrower_criteria: Optional[Dict]
    property_requirements: Optional[Dict]
    compliance_references: Optional[List[str]]
    
    # Thresholds
    numeric_thresholds: Optional[Dict[str, NumericRange]]
```

## Processing Pipeline

### 1. Document Analysis
```python
# Load guidelines document
document = load_document("NQM_Guidelines_v10.pdf")

# Build navigation graph
nav_builder = NavigationGraphBuilder()
nav_graph = nav_builder.build_navigation_graph(document, package_config)

# Validate decision tree completeness
if not nav_graph.all_trees_complete():
    nav_graph = nav_builder.complete_missing_trees(nav_graph)
```

### 2. Entity Extraction
```python
# Extract entities with context
entity_extractor = GuidelineEntityExtractor()
contextual_entities = entity_extractor.extract_entities_with_context(nav_graph)

# Validate entity coverage
validation = entity_extractor.validate_entity_coverage(
    entities=contextual_entities,
    expected_types=["LOAN_PROGRAM", "DECISION_TREE_NODE", "REQUIREMENT"]
)
```

### 3. Graph Construction
```python
# Build comprehensive graph
graph_builder = GuidelinesGraphBuilder(neo4j_driver)

# Create navigation structure
graph_builder.create_navigation_structure(nav_graph)

# Create entities with context
graph_builder.create_contextual_entities(contextual_entities)

# Create decision trees
graph_builder.create_decision_trees(nav_graph.decision_trees)

# Create all relationships
graph_builder.create_comprehensive_relationships(nav_graph)
```

## Quality Assurance

### Validation Rules

1. **Navigation Completeness**
   - All sections have proper hierarchy
   - No orphaned nodes
   - All decision sections identified

2. **Decision Tree Completeness**
   - Every tree has exactly 1 ROOT
   - Every tree has 2+ BRANCHES
   - Every tree has 3+ LEAVES (APPROVE, DECLINE, REFER minimum)
   - All leaves connected to branches

3. **Entity Coverage**
   - All loan programs extracted
   - All decision nodes created as entities
   - All requirements identified

### Metrics
- Navigation Extraction: >95% accuracy
- Decision Tree Completeness: 100% (mandatory)
- Entity Extraction: >90% recall
- Processing Time: <45 seconds per 100 pages