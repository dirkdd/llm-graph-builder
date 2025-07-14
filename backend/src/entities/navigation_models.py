# Task 9: Hierarchical Chunk Models Implementation
# Enhanced data models for hierarchical chunks and navigation structures

from dataclasses import dataclass, field, asdict
from typing import List, Dict, Any, Optional, Tuple, Union
from datetime import datetime
from enum import Enum
import hashlib
import json
from pathlib import Path

# Import existing enums and types from previous tasks
from ..navigation_extractor import NavigationLevel, DocumentFormat
from ..semantic_chunker import ChunkType


class RelationshipType(Enum):
    """Types of relationships between chunks and navigation nodes"""
    # Hierarchical relationships
    PARENT_CHILD = "PARENT_CHILD"           # Parent-child navigation hierarchy
    SEQUENTIAL = "SEQUENTIAL"               # Sequential content flow
    
    # Content relationships  
    REFERENCES = "REFERENCES"               # Cross-references between chunks
    ELABORATES = "ELABORATES"              # One chunk elaborates on another
    SUMMARIZES = "SUMMARIZES"              # Summary relationship
    
    # Decision relationships
    DECISION_BRANCH = "DECISION_BRANCH"     # Decision tree branching
    DECISION_OUTCOME = "DECISION_OUTCOME"   # Decision outcomes
    CONDITIONAL = "CONDITIONAL"             # If/then relationships
    
    # Document relationships
    INTER_DOCUMENT = "INTER_DOCUMENT"       # Between different documents
    MATRIX_GUIDELINE = "MATRIX_GUIDELINE"   # Matrix references guidelines


class DecisionOutcome(Enum):
    """Standard decision outcomes for mortgage processing"""
    APPROVE = "APPROVE"
    DECLINE = "DECLINE"
    REFER = "REFER"
    CONDITIONAL_APPROVE = "CONDITIONAL_APPROVE"
    PENDING_REVIEW = "PENDING_REVIEW"


class QualityRating(Enum):
    """Quality ratings for chunks and navigation nodes"""
    EXCELLENT = "EXCELLENT"    # 0.9-1.0
    GOOD = "GOOD"             # 0.7-0.89
    FAIR = "FAIR"             # 0.5-0.69
    POOR = "POOR"             # 0.0-0.49


@dataclass
class DatabaseMetadata:
    """Metadata for database storage and indexing"""
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    version: str = "1.0.0"
    checksum: Optional[str] = None
    database_id: Optional[str] = None
    indexed_fields: List[str] = field(default_factory=list)
    storage_metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """Generate checksum and validate metadata"""
        if not self.checksum:
            content = f"{self.version}_{self.created_at.isoformat()}"
            self.checksum = hashlib.md5(content.encode()).hexdigest()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for database storage"""
        result = asdict(self)
        result['created_at'] = self.created_at.isoformat()
        result['updated_at'] = self.updated_at.isoformat()
        return result


@dataclass
class NavigationContext:
    """Enhanced navigation context for hierarchical chunks"""
    navigation_path: List[str]              # Full breadcrumb path
    parent_section: Optional[str] = None    # Immediate parent section
    section_number: Optional[str] = None    # Section numbering (e.g., "2.1.3")
    hierarchy_level: int = 0                # Depth in document hierarchy
    document_type: str = "unknown"          # guidelines, matrix, procedures
    
    # Enhanced context fields
    chapter_title: Optional[str] = None     # Chapter-level title
    section_title: Optional[str] = None     # Section-level title
    subsection_title: Optional[str] = None  # Subsection-level title
    page_reference: Optional[int] = None    # Source page number
    
    # Decision context
    decision_context: Optional[str] = None  # Decision tree context
    decision_level: Optional[str] = None    # ROOT, BRANCH, LEAF
    decision_factors: List[str] = field(default_factory=list)  # Decision criteria
    
    # Quality and validation
    context_quality: float = 0.0           # Context completeness score
    validation_errors: List[str] = field(default_factory=list)
    
    def __post_init__(self):
        """Validate and enhance navigation context"""
        # Calculate context quality based on completeness
        quality_factors = [
            1.0 if self.navigation_path else 0.0,
            1.0 if self.section_number else 0.0,
            1.0 if self.parent_section else 0.0,
            1.0 if self.hierarchy_level > 0 else 0.0,
            1.0 if self.document_type != "unknown" else 0.0
        ]
        self.context_quality = sum(quality_factors) / len(quality_factors)
        
        # Extract titles from navigation path
        if self.navigation_path:
            if len(self.navigation_path) > 1:
                self.chapter_title = self.navigation_path[1]
            if len(self.navigation_path) > 2:
                self.section_title = self.navigation_path[2]
            if len(self.navigation_path) > 3:
                self.subsection_title = self.navigation_path[3]
    
    def get_breadcrumb(self, separator: str = " > ") -> str:
        """Get formatted breadcrumb string"""
        return separator.join(self.navigation_path)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return asdict(self)


@dataclass
class EnhancedNavigationNode:
    """Enhanced version of NavigationNode with database and API compatibility"""
    # Core identification
    node_id: str
    title: str
    level: NavigationLevel
    
    # Hierarchy relationships
    parent_id: Optional[str] = None
    children: List[str] = field(default_factory=list)
    ancestor_ids: List[str] = field(default_factory=list)  # All ancestors
    descendant_ids: List[str] = field(default_factory=list)  # All descendants
    
    # Content and structure
    content: str = ""
    raw_content: str = ""                   # Original unprocessed content
    processed_content: str = ""             # Cleaned and processed content
    content_length: int = 0
    
    # Document structure
    page_number: Optional[int] = None
    section_number: Optional[str] = None
    heading_pattern: Optional[str] = None   # Detected heading pattern
    content_type: str = "text"              # text, table, list, decision
    
    # Decision tree specific
    decision_type: Optional[str] = None     # ROOT, BRANCH, LEAF
    decision_outcome: Optional[DecisionOutcome] = None
    decision_criteria: List[str] = field(default_factory=list)
    decision_logic: Optional[str] = None    # If/then/else logic
    
    # Entity extraction
    extracted_entities: List[str] = field(default_factory=list)
    entity_types: Dict[str, List[str]] = field(default_factory=dict)  # Type -> entities
    named_entities: Dict[str, str] = field(default_factory=dict)      # Entity -> type
    
    # Quality and validation
    confidence_score: float = 0.0
    quality_rating: QualityRating = QualityRating.FAIR
    validation_status: str = "pending"      # pending, valid, invalid, needs_review
    validation_errors: List[str] = field(default_factory=list)
    
    # Metadata and storage
    metadata: Dict[str, Any] = field(default_factory=dict)
    navigation_context: Optional[NavigationContext] = None
    database_metadata: Optional[DatabaseMetadata] = None
    
    def __post_init__(self):
        """Initialize derived fields and validate data"""
        # Set content length
        self.content_length = len(self.content)
        
        # Initialize database metadata if not provided
        if not self.database_metadata:
            self.database_metadata = DatabaseMetadata()
        
        # Set quality rating based on confidence score
        if self.confidence_score >= 0.9:
            self.quality_rating = QualityRating.EXCELLENT
        elif self.confidence_score >= 0.7:
            self.quality_rating = QualityRating.GOOD
        elif self.confidence_score >= 0.5:
            self.quality_rating = QualityRating.FAIR
        else:
            self.quality_rating = QualityRating.POOR
    
    def add_child(self, child_id: str) -> None:
        """Add a child node ID"""
        if child_id not in self.children:
            self.children.append(child_id)
    
    def remove_child(self, child_id: str) -> None:
        """Remove a child node ID"""
        if child_id in self.children:
            self.children.remove(child_id)
    
    def is_decision_node(self) -> bool:
        """Check if this is a decision node"""
        return (self.decision_type is not None or 
                self.decision_outcome is not None or
                len(self.decision_criteria) > 0)
    
    def get_hierarchy_depth(self) -> int:
        """Get the depth of this node in the hierarchy"""
        return len(self.ancestor_ids)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        result = asdict(self)
        result['level'] = self.level.value
        if self.decision_outcome:
            result['decision_outcome'] = self.decision_outcome.value
        result['quality_rating'] = self.quality_rating.value
        if self.navigation_context:
            result['navigation_context'] = self.navigation_context.to_dict()
        if self.database_metadata:
            result['database_metadata'] = self.database_metadata.to_dict()
        return result
    
    @classmethod
    def from_navigation_node(cls, nav_node, enhanced_data: Dict[str, Any] = None) -> 'EnhancedNavigationNode':
        """Create from existing NavigationNode (Task 7 compatibility)"""
        enhanced_data = enhanced_data or {}
        
        return cls(
            node_id=nav_node.node_id,
            title=nav_node.title,
            level=nav_node.level,
            parent_id=nav_node.parent_id,
            children=nav_node.children.copy(),
            content=nav_node.content,
            page_number=nav_node.page_number,
            section_number=nav_node.section_number,
            decision_type=nav_node.decision_type,
            decision_outcome=DecisionOutcome(nav_node.decision_outcome) if nav_node.decision_outcome else None,
            extracted_entities=nav_node.extracted_entities.copy(),
            confidence_score=nav_node.confidence_score,
            metadata=nav_node.metadata.copy(),
            **enhanced_data
        )


@dataclass 
class HierarchicalChunk:
    """Enhanced version of SemanticChunk with database and navigation integration"""
    # Core identification
    chunk_id: str
    content: str
    chunk_type: ChunkType
    
    # Navigation integration
    navigation_context: NavigationContext
    source_node_id: Optional[str] = None    # Source NavigationNode ID
    document_id: Optional[str] = None       # Source document ID
    package_id: Optional[str] = None        # Source package ID
    
    # Content structure  
    start_position: int = 0                 # Character start position
    end_position: int = 0                   # Character end position
    content_length: int = 0
    token_count: int = 0                    # Estimated token count
    sentence_count: int = 0                 # Number of sentences
    
    # Chunk relationships
    overlap_with: List[str] = field(default_factory=list)      # Overlapping chunk IDs
    related_chunks: List[str] = field(default_factory=list)    # Related chunk IDs
    parent_chunk_id: Optional[str] = None   # Parent chunk (for split chunks)
    child_chunk_ids: List[str] = field(default_factory=list)   # Child chunks
    
    # Content analysis
    content_hash: Optional[str] = None      # Content hash for deduplication
    content_summary: Optional[str] = None   # Auto-generated summary
    key_phrases: List[str] = field(default_factory=list)       # Extracted key phrases
    sentiment_score: float = 0.0            # Content sentiment (-1 to 1)
    
    # Decision-specific fields (for decision chunks)
    decision_criteria: List[str] = field(default_factory=list)
    decision_outcomes: List[DecisionOutcome] = field(default_factory=list)
    decision_logic: Optional[str] = None
    decision_variables: Dict[str, Any] = field(default_factory=dict)
    
    # Quality and validation
    quality_score: float = 0.0             # Overall quality score
    quality_rating: QualityRating = QualityRating.FAIR
    readability_score: float = 0.0         # Text readability score
    completeness_score: float = 0.0        # Content completeness score
    validation_errors: List[str] = field(default_factory=list)
    
    # Processing metadata
    extraction_metadata: Dict[str, Any] = field(default_factory=dict)
    processing_timestamp: datetime = field(default_factory=datetime.now)
    chunking_algorithm: str = "hierarchical_semantic"
    chunking_version: str = "1.0.0"
    
    # Database and API fields
    database_metadata: Optional[DatabaseMetadata] = None
    api_metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """Initialize derived fields and validate data"""
        # Set content length
        self.content_length = len(self.content)
        
        # Generate content hash
        if not self.content_hash:
            self.content_hash = hashlib.sha256(self.content.encode()).hexdigest()[:16]
        
        # Count sentences (basic approximation)
        self.sentence_count = len([s for s in self.content.split('.') if s.strip()])
        
        # Initialize database metadata
        if not self.database_metadata:
            self.database_metadata = DatabaseMetadata()
        
        # Set quality rating based on quality score
        if self.quality_score >= 0.9:
            self.quality_rating = QualityRating.EXCELLENT
        elif self.quality_score >= 0.7:
            self.quality_rating = QualityRating.GOOD
        elif self.quality_score >= 0.5:
            self.quality_rating = QualityRating.FAIR
        else:
            self.quality_rating = QualityRating.POOR
        
        # Set processing metadata
        self.extraction_metadata.update({
            'chunk_creation_time': self.processing_timestamp.isoformat(),
            'content_analysis': {
                'length': self.content_length,
                'sentences': self.sentence_count,
                'tokens': self.token_count
            }
        })
    
    def add_related_chunk(self, chunk_id: str) -> None:
        """Add a related chunk ID"""
        if chunk_id not in self.related_chunks:
            self.related_chunks.append(chunk_id)
    
    def add_overlap(self, chunk_id: str) -> None:
        """Add an overlapping chunk ID"""
        if chunk_id not in self.overlap_with:
            self.overlap_with.append(chunk_id)
    
    def is_decision_chunk(self) -> bool:
        """Check if this is a decision chunk"""
        return (self.chunk_type == ChunkType.DECISION or 
                len(self.decision_criteria) > 0 or
                len(self.decision_outcomes) > 0)
    
    def get_navigation_breadcrumb(self, separator: str = " > ") -> str:
        """Get formatted navigation breadcrumb"""
        return self.navigation_context.get_breadcrumb(separator)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        result = asdict(self)
        result['chunk_type'] = self.chunk_type.value
        result['navigation_context'] = self.navigation_context.to_dict()
        result['quality_rating'] = self.quality_rating.value
        result['decision_outcomes'] = [outcome.value for outcome in self.decision_outcomes]
        result['processing_timestamp'] = self.processing_timestamp.isoformat()
        if self.database_metadata:
            result['database_metadata'] = self.database_metadata.to_dict()
        return result
    
    @classmethod
    def from_semantic_chunk(cls, semantic_chunk, enhanced_data: Dict[str, Any] = None) -> 'HierarchicalChunk':
        """Create from existing SemanticChunk (Task 8 compatibility)"""
        enhanced_data = enhanced_data or {}
        
        # Convert ChunkContext to NavigationContext
        navigation_context = NavigationContext(
            navigation_path=semantic_chunk.context.navigation_path,
            parent_section=semantic_chunk.context.parent_section,
            section_number=semantic_chunk.context.section_number,
            hierarchy_level=semantic_chunk.context.hierarchy_level,
            document_type=semantic_chunk.context.document_type,
            decision_context=semantic_chunk.context.decision_context
        )
        
        return cls(
            chunk_id=semantic_chunk.chunk_id,
            content=semantic_chunk.content,
            chunk_type=semantic_chunk.chunk_type,
            navigation_context=navigation_context,
            source_node_id=semantic_chunk.node_id,
            start_position=semantic_chunk.start_position,
            end_position=semantic_chunk.end_position,
            token_count=semantic_chunk.token_count,
            overlap_with=semantic_chunk.overlap_with.copy(),
            related_chunks=semantic_chunk.context.related_chunks.copy(),
            quality_score=semantic_chunk.context.quality_score,
            extraction_metadata=semantic_chunk.metadata.copy(),
            **enhanced_data
        )


@dataclass
class DecisionTreeNode:
    """Specialized model for decision tree nodes in mortgage processing"""
    # Core identification
    node_id: str
    title: str
    decision_type: str                      # ROOT, BRANCH, LEAF, CONDITION
    
    # Decision logic
    condition: Optional[str] = None         # The condition to evaluate
    criteria: List[str] = field(default_factory=list)          # Decision criteria
    variables: Dict[str, Any] = field(default_factory=dict)    # Decision variables
    operators: List[str] = field(default_factory=list)         # AND, OR, NOT logic
    
    # Decision outcomes
    true_outcome: Optional[str] = None      # What happens if condition is true
    false_outcome: Optional[str] = None     # What happens if condition is false
    outcomes: List[DecisionOutcome] = field(default_factory=list)
    outcome_descriptions: Dict[DecisionOutcome, str] = field(default_factory=dict)
    
    # Tree structure
    parent_decision_id: Optional[str] = None
    child_decision_ids: List[str] = field(default_factory=list)
    sibling_decision_ids: List[str] = field(default_factory=list)
    
    # Content and context
    description: str = ""
    examples: List[str] = field(default_factory=list)
    exceptions: List[str] = field(default_factory=list)
    source_content: str = ""                # Original content from document
    
    # Navigation integration
    source_node_id: Optional[str] = None    # Source NavigationNode
    navigation_path: List[str] = field(default_factory=list)
    section_reference: Optional[str] = None # Section where this decision is defined
    
    # Mortgage-specific fields
    loan_programs: List[str] = field(default_factory=list)     # Applicable loan programs
    property_types: List[str] = field(default_factory=list)    # Applicable property types
    borrower_types: List[str] = field(default_factory=list)    # Applicable borrower types
    risk_factors: List[str] = field(default_factory=list)      # Risk considerations
    
    # Processing metadata
    complexity_score: float = 0.0          # Decision complexity (0-1)
    confidence_score: float = 0.0          # Extraction confidence
    validation_status: str = "pending"      # Validation status
    
    # Database fields
    metadata: Dict[str, Any] = field(default_factory=dict)
    database_metadata: Optional[DatabaseMetadata] = None
    
    def __post_init__(self):
        """Initialize and validate decision tree node"""
        if not self.database_metadata:
            self.database_metadata = DatabaseMetadata()
        
        # Calculate complexity based on criteria and variables
        complexity_factors = [
            len(self.criteria) * 0.2,
            len(self.variables) * 0.1,
            len(self.operators) * 0.1,
            len(self.child_decision_ids) * 0.3,
            1.0 if self.condition else 0.0
        ]
        self.complexity_score = min(sum(complexity_factors), 1.0)
    
    def add_criterion(self, criterion: str) -> None:
        """Add a decision criterion"""
        if criterion not in self.criteria:
            self.criteria.append(criterion)
    
    def add_outcome(self, outcome: DecisionOutcome, description: str = "") -> None:
        """Add a decision outcome"""
        if outcome not in self.outcomes:
            self.outcomes.append(outcome)
        if description:
            self.outcome_descriptions[outcome] = description
    
    def is_leaf_node(self) -> bool:
        """Check if this is a leaf node (no children)"""
        return len(self.child_decision_ids) == 0
    
    def is_root_node(self) -> bool:
        """Check if this is a root node (no parent)"""
        return self.parent_decision_id is None
    
    def get_decision_path(self) -> List[str]:
        """Get the decision path as a list of node IDs"""
        return self.navigation_path + [self.node_id]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        result = asdict(self)
        result['outcomes'] = [outcome.value for outcome in self.outcomes]
        result['outcome_descriptions'] = {
            outcome.value: desc for outcome, desc in self.outcome_descriptions.items()
        }
        if self.database_metadata:
            result['database_metadata'] = self.database_metadata.to_dict()
        return result


@dataclass
class ChunkRelationship:
    """Represents relationships between hierarchical chunks"""
    # Core identification
    relationship_id: str
    relationship_type: RelationshipType
    
    # Relationship endpoints
    from_chunk_id: str
    to_chunk_id: str
    from_node_id: Optional[str] = None      # Source navigation node
    to_node_id: Optional[str] = None        # Target navigation node
    
    # Relationship properties
    strength: float = 0.0                   # Relationship strength (0-1)
    confidence: float = 0.0                 # Confidence in relationship (0-1)
    direction: str = "bidirectional"        # unidirectional, bidirectional
    
    # Relationship context
    context: Optional[str] = None           # Description of the relationship
    evidence: List[str] = field(default_factory=list)  # Evidence for relationship
    keywords: List[str] = field(default_factory=list)  # Keywords that indicate relationship
    
    # Decision-specific relationship data
    decision_condition: Optional[str] = None # For conditional relationships
    decision_outcome: Optional[DecisionOutcome] = None  # For outcome relationships
    decision_variables: Dict[str, Any] = field(default_factory=dict)
    
    # Processing metadata
    extraction_method: str = "automatic"    # automatic, manual, hybrid
    extraction_confidence: float = 0.0     # Confidence in extraction
    validation_status: str = "pending"      # pending, validated, rejected
    
    # Metadata and database fields
    metadata: Dict[str, Any] = field(default_factory=dict)
    database_metadata: Optional[DatabaseMetadata] = None
    
    def __post_init__(self):
        """Initialize relationship metadata"""
        if not self.database_metadata:
            self.database_metadata = DatabaseMetadata()
        
        # Generate relationship ID if not provided
        if not self.relationship_id:
            id_content = f"{self.from_chunk_id}_{self.to_chunk_id}_{self.relationship_type.value}"
            self.relationship_id = hashlib.md5(id_content.encode()).hexdigest()[:12]
    
    def is_hierarchical(self) -> bool:
        """Check if this is a hierarchical relationship"""
        return self.relationship_type in [
            RelationshipType.PARENT_CHILD,
            RelationshipType.SEQUENTIAL
        ]
    
    def is_decision_related(self) -> bool:
        """Check if this is a decision-related relationship"""
        return self.relationship_type in [
            RelationshipType.DECISION_BRANCH,
            RelationshipType.DECISION_OUTCOME,
            RelationshipType.CONDITIONAL
        ]
    
    def get_relationship_summary(self) -> str:
        """Get a human-readable summary of the relationship"""
        return f"{self.from_chunk_id} {self.relationship_type.value} {self.to_chunk_id}"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        result = asdict(self)
        result['relationship_type'] = self.relationship_type.value
        if self.decision_outcome:
            result['decision_outcome'] = self.decision_outcome.value
        if self.database_metadata:
            result['database_metadata'] = self.database_metadata.to_dict()
        return result


# Utility functions for model operations

def create_navigation_hierarchy(nodes: List[EnhancedNavigationNode]) -> Dict[str, EnhancedNavigationNode]:
    """Create a hierarchy from a list of navigation nodes"""
    node_dict = {node.node_id: node for node in nodes}
    
    # Build ancestor and descendant relationships
    for node in nodes:
        if node.parent_id and node.parent_id in node_dict:
            parent = node_dict[node.parent_id]
            parent.add_child(node.node_id)
            
            # Build ancestor chain
            current_parent = parent
            while current_parent:
                if current_parent.node_id not in node.ancestor_ids:
                    node.ancestor_ids.append(current_parent.node_id)
                current_parent = node_dict.get(current_parent.parent_id)
    
    # Build descendant relationships
    for node in nodes:
        for ancestor_id in node.ancestor_ids:
            ancestor = node_dict[ancestor_id]
            if node.node_id not in ancestor.descendant_ids:
                ancestor.descendant_ids.append(node.node_id)
    
    return node_dict


def validate_chunk_relationships(chunks: List[HierarchicalChunk], 
                                relationships: List[ChunkRelationship]) -> List[str]:
    """Validate chunk relationships for consistency"""
    errors = []
    chunk_ids = {chunk.chunk_id for chunk in chunks}
    
    for rel in relationships:
        # Check that referenced chunks exist
        if rel.from_chunk_id not in chunk_ids:
            errors.append(f"Relationship {rel.relationship_id}: from_chunk_id '{rel.from_chunk_id}' not found")
        
        if rel.to_chunk_id not in chunk_ids:
            errors.append(f"Relationship {rel.relationship_id}: to_chunk_id '{rel.to_chunk_id}' not found")
        
        # Check relationship strength and confidence bounds
        if not 0.0 <= rel.strength <= 1.0:
            errors.append(f"Relationship {rel.relationship_id}: strength must be between 0.0 and 1.0")
        
        if not 0.0 <= rel.confidence <= 1.0:
            errors.append(f"Relationship {rel.relationship_id}: confidence must be between 0.0 and 1.0")
    
    return errors


def calculate_navigation_quality(navigation_context: NavigationContext) -> float:
    """Calculate overall quality score for navigation context"""
    quality_components = [
        1.0 if navigation_context.navigation_path else 0.0,
        1.0 if navigation_context.section_number else 0.0,
        1.0 if navigation_context.parent_section else 0.0,
        1.0 if navigation_context.hierarchy_level > 0 else 0.0,
        1.0 if navigation_context.document_type != "unknown" else 0.0,
        0.5 if navigation_context.chapter_title else 0.0,
        0.5 if navigation_context.section_title else 0.0
    ]
    
    return sum(quality_components) / len(quality_components)


# Export all classes and functions
__all__ = [
    # Enums
    'RelationshipType',
    'DecisionOutcome', 
    'QualityRating',
    
    # Core models
    'DatabaseMetadata',
    'NavigationContext',
    'EnhancedNavigationNode',
    'HierarchicalChunk',
    'DecisionTreeNode',
    'ChunkRelationship',
    
    # Utility functions
    'create_navigation_hierarchy',
    'validate_chunk_relationships',
    'calculate_navigation_quality'
]