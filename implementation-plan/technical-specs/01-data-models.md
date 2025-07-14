# Technical Specifications: Data Models

## Overview
This document defines the comprehensive data models for the enhanced LLM Graph Builder system, including document packages, hierarchical navigation, matrix classifications, and multi-layer knowledge graph structures.

## Core Data Models

### 1. Document Package Models

#### DocumentPackage
```python
class DocumentPackage:
    package_id: str  # Format: "pkg_{category}_{name}_{version}"
    package_name: str
    tenant_id: str
    category: str  # NQM, RTL, SBC, CONV
    version: str  # Semantic versioning
    status: str  # DRAFT, ACTIVE, ARCHIVED
    created_at: datetime
    updated_at: datetime
    created_by: str
    
    # Structure
    documents: List[DocumentDefinition]
    relationships: List[PackageRelationship]
    processing_rules: ProcessingConfiguration
    
    # Template
    template_mappings: Dict[str, TemplateMapping]
    validation_rules: List[ValidationRule]
    
    # Metrics
    complexity_score: float
    completeness_score: float
    quality_score: float
```

#### DocumentDefinition
```python
class DocumentDefinition:
    document_id: str
    document_type: str  # guidelines, matrix, rate_sheet
    document_name: str
    
    # Structure
    expected_structure: NavigationStructure
    required_sections: List[str]
    optional_sections: List[str]
    
    # Processing
    chunking_strategy: str
    entity_types: List[str]
    matrix_configuration: Optional[MatrixConfig]
    
    # Validation
    validation_schema: Dict
    quality_thresholds: QualityMetrics
```

### 2. Navigation and Hierarchy Models

#### NavigationStructure
```python
class NavigationStructure:
    structure_id: str
    document_id: str
    
    # Hierarchy
    chapters: List[NavigationChapter]
    sections: List[NavigationSection]
    subsections: List[NavigationSubsection]
    
    # Decision Trees
    decision_trees: List[DecisionTree]
    root_nodes: List[DecisionNode]
    branch_nodes: List[DecisionNode]
    leaf_nodes: List[DecisionNode]
    
    # Metadata
    extraction_confidence: float
    completeness_score: float
    validation_status: str
```

#### DecisionTree
```python
class DecisionTree:
    tree_id: str
    document_id: str
    tree_name: str
    tree_type: str  # eligibility, documentation, property, pricing
    
    # Structure
    root_node: DecisionNode
    all_nodes: List[DecisionNode]
    all_paths: List[DecisionPath]
    
    # Validation
    is_complete: bool
    missing_paths: List[str]
    orphaned_nodes: List[str]
    
    # Metrics
    complexity_score: float
    coverage_percentage: float
```

#### DecisionNode
```python
class DecisionNode:
    node_id: str
    node_type: str  # ROOT, BRANCH, LEAF
    node_text: str
    
    # Hierarchy
    parent_nodes: List[str]
    child_nodes: List[str]
    depth_level: int
    
    # Classification
    decision_type: str
    outcome_type: Optional[str]  # APPROVE, DECLINE, REFER
    conditions: List[Condition]
    
    # Context
    section_reference: str
    page_reference: Optional[int]
    confidence_score: float
```

### 3. Matrix Classification Models

#### MatrixClassification
```python
class MatrixClassification:
    matrix_id: str
    document_id: str
    
    # Multi-type classification
    detected_types: List[MatrixType]
    primary_type: MatrixType
    confidence_scores: Dict[str, float]
    complexity_score: float
    
    # Structure
    dimensions: List[MatrixDimension]
    ranges: List[RangeExtraction]
    lookup_table: Optional[LookupTable]
    business_rules: List[BusinessRule]
    
    # Relationships
    guidelines_references: List[GuidelinesReference]
    cross_matrix_relationships: List[MatrixRelationship]
```

#### MatrixType
```python
class MatrixType:
    type_name: str  # multi_dimensional, risk_segmentation, business_rules, etc.
    confidence: float
    characteristics: List[str]
    processing_strategy: str
    
    # Specific configurations
    dimension_count: Optional[int]
    rule_complexity: Optional[str]
    lookup_method: Optional[str]
```

#### RangeExtraction
```python
class RangeExtraction:
    range_id: str
    dimension_name: str
    
    # Range details
    min_value: Optional[float]
    max_value: Optional[float]
    data_type: str  # numeric, categorical, boolean
    
    # Extracted values
    raw_values: List[str]
    normalized_values: List[Union[float, str]]
    validation_status: str
    
    # Context
    source_text: str
    extraction_confidence: float
```

### 4. Knowledge Graph Layer Models

#### Layer1_Document
```python
class Layer1_Document:
    # Core document metadata
    document_id: str
    package_id: str
    file_name: str
    document_type: str
    processing_status: str
    
    # Content
    raw_content: str
    processed_content: str
    embeddings: List[float]
    
    # Processing metadata
    chunk_count: int
    entity_count: int
    relationship_count: int
    quality_score: float
```

#### Layer2_Structure
```python
class Layer2_Structure:
    # Navigation elements
    navigation_id: str
    parent_id: Optional[str]
    structure_type: str  # chapter, section, subsection
    
    # Content
    title: str
    content: str
    page_numbers: List[int]
    
    # Hierarchy
    depth_level: int
    child_count: int
    path_from_root: List[str]
```

#### Layer3_Entity
```python
class Layer3_Entity:
    # Entity identification
    entity_id: str
    entity_type: str
    entity_name: str
    
    # Properties
    properties: Dict[str, Any]
    aliases: List[str]
    confidence_score: float
    
    # Context
    source_chunks: List[str]
    document_context: str
    extraction_method: str
```

#### Layer4_Decision
```python
class Layer4_Decision:
    # Decision identification
    decision_id: str
    decision_type: str
    decision_text: str
    
    # Structure
    conditions: List[Condition]
    outcomes: List[Outcome]
    alternatives: List[str]
    
    # Traceability
    source_section: str
    related_matrices: List[str]
    business_rules: List[str]
```

#### Layer5_Business
```python
class Layer5_Business:
    # Business rule identification
    rule_id: str
    rule_name: str
    rule_category: str
    
    # Logic
    rule_logic: str
    conditions: List[BusinessCondition]
    actions: List[BusinessAction]
    
    # Policy context
    policy_area: str
    compliance_requirements: List[str]
    regulatory_references: List[str]
```

### 5. Relationship Models

#### CrossDocumentRelationship
```python
class CrossDocumentRelationship:
    relationship_id: str
    relationship_type: str  # REFERENCES, ELABORATES, CONFLICTS, SUPERSEDES
    
    # Source and target
    source_id: str
    source_type: str
    target_id: str
    target_type: str
    
    # Relationship details
    confidence_score: float
    validation_status: str
    relationship_context: str
    
    # Consistency checking
    is_consistent: bool
    conflicts: List[ConflictDetection]
    last_validated: datetime
```

#### ConflictDetection
```python
class ConflictDetection:
    conflict_id: str
    conflict_type: str  # VALUE_MISMATCH, LOGIC_CONTRADICTION, MISSING_REFERENCE
    
    # Conflict details
    description: str
    severity: str  # LOW, MEDIUM, HIGH, CRITICAL
    suggested_resolution: str
    
    # Context
    affected_documents: List[str]
    affected_sections: List[str]
    detection_date: datetime
```

### 6. Quality and Validation Models

#### QualityMetrics
```python
class QualityMetrics:
    document_id: str
    package_id: str
    
    # Extraction quality
    entity_extraction_score: float
    relationship_accuracy: float
    decision_tree_completeness: float
    
    # Structure quality
    navigation_accuracy: float
    hierarchy_consistency: float
    section_coverage: float
    
    # Matrix quality
    matrix_classification_confidence: float
    range_extraction_accuracy: float
    cross_reference_validity: float
    
    # Overall scores
    overall_quality_score: float
    processing_confidence: float
    validation_status: str
```

#### ValidationRule
```python
class ValidationRule:
    rule_id: str
    rule_name: str
    rule_type: str  # STRUCTURE, CONTENT, RELATIONSHIP, BUSINESS
    
    # Rule definition
    rule_logic: str
    validation_criteria: List[ValidationCriterion]
    error_message: str
    
    # Application
    applies_to: List[str]  # Document types or sections
    severity: str
    auto_correctable: bool
```

## Database Schema Mapping

### Neo4j Node Labels
- `:DocumentPackage`
- `:Document`
- `:NavigationChapter`
- `:NavigationSection`
- `:NavigationSubsection`
- `:DecisionNode`
- `:MatrixCell`
- `:Entity`
- `:BusinessRule`
- `:Chunk`

### Relationship Types
- `:CONTAINS`
- `:HAS_STRUCTURE`
- `:REFERENCES`
- `:ELABORATES`
- `:CONFLICTS`
- `:SUPERSEDES`
- `:LEADS_TO`
- `:QUALIFIES_FOR`
- `:PARENT_OF`
- `:CHILD_OF`
- `:EXTRACTED_FROM`

## API Response Models

### Standard API Response
```python
class APIResponse:
    success: bool
    data: Optional[Any]
    error: Optional[str]
    message: Optional[str]
    metadata: Dict[str, Any]
    timestamp: datetime
    request_id: str
```

### Processing Status Response
```python
class ProcessingStatusResponse:
    task_id: str
    status: str  # PENDING, PROCESSING, COMPLETED, FAILED
    progress_percentage: float
    current_step: str
    estimated_completion: Optional[datetime]
    results: Optional[Dict]
    errors: List[str]
```

## Data Validation and Constraints

### Required Fields
- All models must have unique IDs
- Timestamps must be in UTC
- Confidence scores must be between 0.0 and 1.0
- Status fields must use predefined enums

### Data Integrity Rules
- Document packages must have at least one document
- Decision trees must have complete ROOT → LEAF paths
- Matrix classifications must have at least one detected type
- Cross-document relationships must reference valid documents

### Performance Considerations
- Entity IDs should be indexed for fast lookups
- Relationship queries should use graph traversal optimization
- Large text fields should be stored separately from metadata
- Embeddings should use efficient vector storage formats