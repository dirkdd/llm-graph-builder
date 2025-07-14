# Phase 1.2: Enhanced Hierarchical Chunking System

## Overview
The Enhanced Hierarchical Chunking System revolutionizes document processing by maintaining the natural structure of mortgage guidelines documents. Unlike traditional flat chunking approaches, this system preserves chapter, section, and subsection relationships while creating semantic chunks that respect document boundaries.

## Core Innovation

### Traditional vs. Hierarchical Chunking

**Traditional Approach** (Current System):
- Splits text into fixed-size chunks
- Loses document structure
- No relationship between chunks
- Context often split across chunks

**Hierarchical Approach** (New System):
- Maintains document navigation structure
- Preserves parent-child relationships
- Context-aware chunk boundaries
- Enables navigation-based retrieval

## System Architecture

### 1. Navigation Extractor (`navigation_extractor.py`)

```python
class NavigationExtractor:
    """Extracts hierarchical structure from documents"""
    
    def __init__(self, llm_model: str = "claude-sonnet-4"):
        self.llm = get_llm(llm_model)
        self.patterns = NavigationPatterns()
        
    def extract_navigation_structure(self, document: Document) -> NavigationTree:
        """Extract complete navigation hierarchy"""
        
        # Step 1: Detect table of contents
        toc = self.extract_table_of_contents(document)
        
        # Step 2: Identify heading patterns
        heading_patterns = self.detect_heading_patterns(document)
        
        # Step 3: Build navigation tree
        nav_tree = self.build_navigation_tree(document, toc, heading_patterns)
        
        # Step 4: Extract decision trees
        decision_trees = self.extract_decision_trees(nav_tree)
        
        # Step 5: Validate completeness
        self.validate_navigation_structure(nav_tree, decision_trees)
        
        return nav_tree
    
    def detect_heading_patterns(self, document: Document) -> HeadingPatterns:
        """Detect document heading patterns"""
        patterns = {
            'chapter': [
                r'^\s*CHAPTER\s+(\d+)[:\s]+(.+)$',
                r'^\s*(\d+)\.\s+([A-Z][A-Z\s]+)$',
                r'^\s*PART\s+([A-Z]+)[:\s]+(.+)$'
            ],
            'section': [
                r'^\s*(\d+\.\d+)\s+(.+)$',
                r'^\s*Section\s+(\d+)[:\s]+(.+)$',
                r'^\s*([A-Z])\.\s+(.+)$'
            ],
            'subsection': [
                r'^\s*(\d+\.\d+\.\d+)\s+(.+)$',
                r'^\s*\(([a-z])\)\s+(.+)$',
                r'^\s*([ivx]+)\.\s+(.+)$'
            ]
        }
        return self.match_patterns(document.text, patterns)
    
    def extract_decision_trees(self, nav_tree: NavigationTree) -> List[DecisionTree]:
        """Extract complete decision trees from navigation"""
        decision_sections = self.identify_decision_sections(nav_tree)
        decision_trees = []
        
        for section in decision_sections:
            # Extract ROOT node (policy entry)
            root = self.extract_root_node(section)
            
            # Extract BRANCH nodes (criteria)
            branches = self.extract_branch_nodes(section)
            
            # Extract LEAF nodes (outcomes) - MANDATORY
            leaves = self.extract_leaf_nodes(section)
            
            # Validate complete tree
            if self.validate_decision_tree(root, branches, leaves):
                decision_trees.append(
                    DecisionTree(root=root, branches=branches, leaves=leaves)
                )
        
        return decision_trees
```

### 2. Semantic Chunker (`semantic_chunker.py`)

```python
class SemanticChunker:
    """Creates semantic chunks that respect document structure"""
    
    def __init__(self, navigation_tree: NavigationTree):
        self.nav_tree = navigation_tree
        self.chunk_size_target = 1500  # tokens
        self.chunk_overlap = 200  # tokens
        
    def create_hierarchical_chunks(self, document: Document) -> List[HierarchicalChunk]:
        """Create chunks that maintain hierarchy"""
        chunks = []
        
        for node in self.nav_tree.traverse_depth_first():
            # Create chunk for this navigation node
            chunk = self.create_node_chunk(node, document)
            
            # Ensure chunk includes context
            chunk = self.add_hierarchical_context(chunk, node)
            
            # Handle large sections
            if chunk.token_count > self.chunk_size_target:
                sub_chunks = self.split_large_chunk(chunk)
                chunks.extend(sub_chunks)
            else:
                chunks.append(chunk)
        
        # Create relationship connections
        self.create_chunk_relationships(chunks)
        
        return chunks
    
    def create_node_chunk(self, node: NavigationNode, document: Document) -> HierarchicalChunk:
        """Create chunk from navigation node"""
        return HierarchicalChunk(
            chunk_id=f"{node.enhanced_node_id}_chunk",
            content=node.content,
            navigation_path=self.get_navigation_path(node),
            node_type=node.node_type,
            level=node.depth_level,
            parent_id=node.parent_id,
            children_ids=[child.id for child in node.children],
            metadata={
                'chapter': node.chapter_number,
                'section': node.section_number,
                'subsection': node.subsection_number,
                'decision_metadata': node.decision_metadata
            }
        )
    
    def add_hierarchical_context(self, chunk: HierarchicalChunk, node: NavigationNode) -> HierarchicalChunk:
        """Add parent context to chunk"""
        context_parts = []
        
        # Add breadcrumb navigation
        breadcrumb = self.build_breadcrumb(node)
        context_parts.append(f"Navigation: {breadcrumb}")
        
        # Add parent summary if exists
        if node.parent:
            context_parts.append(f"Parent Section: {node.parent.title}")
            
        # Add sibling context for better understanding
        if node.previous_sibling:
            context_parts.append(f"Previous: {node.previous_sibling.title}")
        
        # Prepend context to chunk
        chunk.content = "\n".join(context_parts) + "\n\n" + chunk.content
        
        return chunk
```

### 3. Chunk Relationships (`chunk_relationships.py`)

```python
class ChunkRelationshipManager:
    """Manages relationships between chunks"""
    
    def create_chunk_relationships(self, chunks: List[HierarchicalChunk]) -> List[ChunkRelationship]:
        """Create all relationships between chunks"""
        relationships = []
        
        # Hierarchical relationships
        relationships.extend(self.create_hierarchical_relationships(chunks))
        
        # Sequential relationships
        relationships.extend(self.create_sequential_relationships(chunks))
        
        # Reference relationships
        relationships.extend(self.create_reference_relationships(chunks))
        
        # Decision tree relationships
        relationships.extend(self.create_decision_relationships(chunks))
        
        return relationships
    
    def create_hierarchical_relationships(self, chunks: List[HierarchicalChunk]) -> List[ChunkRelationship]:
        """Create parent-child relationships"""
        relationships = []
        
        for chunk in chunks:
            # CONTAINS relationship
            for child_id in chunk.children_ids:
                relationships.append(ChunkRelationship(
                    from_chunk_id=chunk.chunk_id,
                    to_chunk_id=child_id,
                    relationship_type="CONTAINS",
                    metadata={"hierarchy_type": "parent_child"}
                ))
            
            # PART_OF relationship (inverse)
            if chunk.parent_id:
                relationships.append(ChunkRelationship(
                    from_chunk_id=chunk.chunk_id,
                    to_chunk_id=chunk.parent_id,
                    relationship_type="PART_OF",
                    metadata={"hierarchy_type": "child_parent"}
                ))
        
        return relationships
    
    def create_decision_relationships(self, chunks: List[HierarchicalChunk]) -> List[ChunkRelationship]:
        """Create decision tree relationships"""
        relationships = []
        decision_chunks = [c for c in chunks if c.has_decision_metadata()]
        
        for chunk in decision_chunks:
            decision_type = chunk.metadata['decision_metadata']['decision_type']
            
            if decision_type == "ROOT":
                # Find connected BRANCH chunks
                branches = self.find_branch_chunks(chunk, chunks)
                for branch in branches:
                    relationships.append(ChunkRelationship(
                        from_chunk_id=chunk.chunk_id,
                        to_chunk_id=branch.chunk_id,
                        relationship_type="LEADS_TO",
                        metadata={"decision_flow": "root_to_branch"}
                    ))
            
            elif decision_type == "BRANCH":
                # Find connected LEAF chunks
                leaves = self.find_leaf_chunks(chunk, chunks)
                for leaf in leaves:
                    relationships.append(ChunkRelationship(
                        from_chunk_id=chunk.chunk_id,
                        to_chunk_id=leaf.chunk_id,
                        relationship_type="RESULTS_IN",
                        metadata={"decision_flow": "branch_to_leaf"}
                    ))
        
        return relationships
```

## Data Models

### Navigation Tree Structure

```python
class NavigationNode:
    """Represents a node in document navigation"""
    enhanced_node_id: str  # e.g., "NQM_titanium_001"
    node_type: str  # CHAPTER, SECTION, SUBSECTION, DECISION_FLOW_SECTION
    title: str
    content: str
    
    # Hierarchy
    depth_level: int  # 1-5
    chapter_number: Optional[int]
    section_number: Optional[str]  # e.g., "2.3"
    subsection_number: Optional[str]  # e.g., "2.3.1"
    
    # Relationships
    parent_id: Optional[str]
    children: List['NavigationNode']
    previous_sibling: Optional['NavigationNode']
    next_sibling: Optional['NavigationNode']
    
    # Decision metadata (if applicable)
    decision_metadata: Optional[DecisionMetadata]
    
class HierarchicalChunk:
    """Enhanced chunk with hierarchy information"""
    chunk_id: str
    content: str
    navigation_path: str  # e.g., "Chapter 1 > Section 1.2 > Subsection 1.2.3"
    
    # Structure
    node_type: str
    level: int
    parent_id: Optional[str]
    children_ids: List[str]
    
    # Context
    chapter_context: str
    section_context: str
    
    # Metadata
    token_count: int
    embeddings: Optional[List[float]]
    metadata: Dict[str, Any]
```

### Decision Tree Components

```python
class DecisionTreeNode:
    """Node in a decision tree"""
    node_id: str
    decision_type: str  # ROOT, BRANCH, LEAF, TERMINAL, GATEWAY
    title: str
    content: str
    
    # Decision logic
    logical_expression: Optional[str]
    evaluation_precedence: int  # 1-99
    
    # Outcomes
    decision_outcomes: List[str]  # APPROVE, DECLINE, REFER
    default_outcome: DecisionOutcome
    
    # Relationships
    parent_nodes: List[str]
    child_nodes: List[str]
    
class DecisionOutcome:
    """Outcome of a decision"""
    action: str  # APPROVE, DECLINE, REFER
    message: str
    conditions: List[str]
    exceptions: List[ExceptionRule]
```

## Neo4j Schema

```cypher
// Hierarchical Chunk Nodes
(:HierarchicalChunk {
  chunk_id: "NQM_titanium_001_chunk",
  content: "...",
  navigation_path: "Chapter 1 > Section 1.2",
  node_type: "SECTION",
  level: 2,
  chapter_number: 1,
  section_number: "1.2",
  token_count: 1200
})

// Navigation Nodes
(:NavigationNode {
  enhanced_node_id: "NQM_titanium_001",
  node_type: "SECTION",
  title: "Borrower Eligibility",
  depth_level: 2,
  decision_type: "BRANCH"
})

// Chunk Relationships
(:HierarchicalChunk)-[:CONTAINS]->(:HierarchicalChunk)
(:HierarchicalChunk)-[:FOLLOWS]->(:HierarchicalChunk)
(:HierarchicalChunk)-[:REFERENCES]->(:HierarchicalChunk)
(:HierarchicalChunk)-[:PREREQUISITE]->(:HierarchicalChunk)

// Decision Relationships
(:HierarchicalChunk {decision_type: "ROOT"})-[:LEADS_TO]->(:HierarchicalChunk {decision_type: "BRANCH"})
(:HierarchicalChunk {decision_type: "BRANCH"})-[:RESULTS_IN]->(:HierarchicalChunk {decision_type: "LEAF"})
```

## Processing Pipeline

### 1. Document Ingestion
```python
# Load document
document = load_document("guidelines.pdf")

# Extract navigation structure
nav_extractor = NavigationExtractor()
nav_tree = nav_extractor.extract_navigation_structure(document)
```

### 2. Hierarchical Chunking
```python
# Create semantic chunks
chunker = SemanticChunker(nav_tree)
chunks = chunker.create_hierarchical_chunks(document)

# Create relationships
relationship_manager = ChunkRelationshipManager()
relationships = relationship_manager.create_chunk_relationships(chunks)
```

### 3. Graph Construction
```python
# Store in Neo4j
graph_builder = HierarchicalGraphBuilder(neo4j_driver)
graph_builder.create_navigation_nodes(nav_tree)
graph_builder.create_chunk_nodes(chunks)
graph_builder.create_relationships(relationships)
```

## Advantages Over Traditional Chunking

1. **Contextual Understanding**: Each chunk knows its place in the document
2. **Navigation-Based Retrieval**: Can follow document structure for answers
3. **Complete Decision Paths**: No orphaned decision nodes
4. **Semantic Boundaries**: Chunks split at logical points, not arbitrary positions
5. **Relationship Preservation**: Maintains all document relationships
6. **Improved Accuracy**: Better understanding leads to better answers

## Quality Metrics

- **Navigation Extraction Accuracy**: >95%
- **Chunk Boundary Quality**: >90% semantic coherence
- **Decision Tree Completeness**: 100% (all trees have leaves)
- **Relationship Accuracy**: >95%
- **Processing Speed**: <30 seconds per 100-page document