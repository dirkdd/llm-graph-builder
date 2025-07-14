# Phase 2.1: Multi-Type Matrix Classification System

## Overview
The Multi-Type Matrix Classification System implements sophisticated matrix processing that recognizes mortgage matrices can exhibit multiple types simultaneously. This system provides confidence-based classification, range extraction, and intelligent linking to guidelines sections.

## Core Innovation

### Multi-Type Matrix Recognition
Traditional systems classify matrices as a single type. Our system recognizes that real-world mortgage matrices often combine multiple characteristics:
- A qualification matrix can be both a Multi-Dimensional Decision Matrix AND a Risk-Based Segmentation Matrix
- A pricing matrix can incorporate Range Lookup Tables AND Business Rules Engine logic
- Each type detected with confidence scoring enables hybrid processing strategies

## Matrix Type Definitions

### 1. Multi-Dimensional Decision Matrix
**Characteristics**: Multiple input dimensions produce decision outcomes
```
FICO Score × LTV Ratio × Property Type → Approval Decision
│           │           │                  │
├─ 620-679  ├─ ≤70%    ├─ SFR            → Approved
├─ 680-719  ├─ 70-80%  ├─ Condo          → Conditional
└─ 720+     └─ >80%    └─ Multi-Family   → Declined
```

### 2. Risk-Based Segmentation Matrix
**Characteristics**: Credit risk tiers with graduated terms
```
Risk Tier    │ Rate Adj │ LTV Max │ Documentation
─────────────┼──────────┼─────────┼──────────────
Tier 1 (740+)│ +0.00%   │ 90%     │ Streamlined
Tier 2 (680) │ +0.25%   │ 85%     │ Standard
Tier 3 (620) │ +0.75%   │ 80%     │ Full Doc
```

### 3. Business Rules Engine Table
**Characteristics**: IF-THEN rules replacing policy text
```
IF (FICO ≥ 720 AND LTV ≤ 80% AND DTI ≤ 43%) THEN
    ApprovalStatus = "Auto-Approved"
    Documentation = "Reduced"
ELSE IF (FICO ≥ 680 AND CompensatingFactors ≥ 2) THEN
    ApprovalStatus = "Manual Review"
    Documentation = "Full"
```

### 4. Sparse Tensor/Multi-Dimensional Array
**Characteristics**: 3D+ data with value optimization
```
dimensions: [FICO, LTV, LoanAmount, PropertyType]
sparse_data: {
    (720, 80, 500000, "SFR"): "Approved",
    (*, *, *, "Manufactured"): "Manual Review",  # Wildcard dimension
    default: "Standard Processing"
}
```

### 5. Range Lookup Table (LUT)
**Characteristics**: Efficient range-based queries
```
FICO Range  │ Base Rate │ Credit Adj
────────────┼───────────┼───────────
580-619     │ 7.25%     │ +1.50%
620-679     │ 6.75%     │ +0.75%
680-739     │ 6.25%     │ +0.25%
740+        │ 6.00%     │ +0.00%
```

### 6. Configuration Matrix
**Characteristics**: Externalized business rules
```
Parameter               │ Value    │ Override │ Authority
───────────────────────┼──────────┼──────────┼──────────
MIN_FICO_SCORE         │ 620      │ 600      │ SVP
MAX_LTV_RATIO          │ 85%      │ 90%      │ CRO
MAX_DTI_RATIO          │ 50%      │ 55%      │ VP
```

## System Architecture

### 1. Matrix Classifier (`matrix_classifier.py`)

```python
class MatrixClassifier:
    """Multi-type matrix classification with confidence scoring"""
    
    def __init__(self, llm_model: str = "claude-sonnet-4"):
        self.llm = get_llm(llm_model)
        self.type_detectors = self._initialize_detectors()
        
    def classify_matrix(self, matrix_content: Union[str, pd.DataFrame], 
                       matrix_metadata: Dict) -> MatrixClassification:
        """Classify matrix with multi-type detection"""
        
        # Step 1: Structural analysis
        structure_features = self.extract_structural_features(matrix_content)
        
        # Step 2: Content analysis
        content_features = self.extract_content_features(matrix_content)
        
        # Step 3: Pattern matching for each type
        type_scores = {}
        for matrix_type, detector in self.type_detectors.items():
            confidence = detector.detect(structure_features, content_features)
            if confidence > 0.5:  # Threshold for consideration
                type_scores[matrix_type] = confidence
        
        # Step 4: Determine primary type and processing strategy
        primary_type = max(type_scores, key=type_scores.get)
        
        # Step 5: Calculate weights for hybrid processing
        total_confidence = sum(type_scores.values())
        weights = {t: c/total_confidence for t, c in type_scores.items()}
        
        # Step 6: Determine complexity score
        complexity = self.calculate_complexity_score(type_scores, structure_features)
        
        return MatrixClassification(
            primary_type=primary_type,
            detected_types=type_scores,
            weights=weights,
            processing_strategy=self.determine_processing_strategy(type_scores),
            complexity_score=complexity,
            dimensions=self.extract_dimensions(matrix_content),
            confidence_threshold=0.75,
            metadata=self.enhance_metadata(matrix_metadata, type_scores)
        )
    
    def extract_structural_features(self, matrix_content) -> StructuralFeatures:
        """Extract structural characteristics"""
        features = StructuralFeatures()
        
        if isinstance(matrix_content, pd.DataFrame):
            features.num_rows = len(matrix_content)
            features.num_columns = len(matrix_content.columns)
            features.has_headers = self.detect_headers(matrix_content)
            features.has_ranges = self.detect_ranges(matrix_content)
            features.sparsity = self.calculate_sparsity(matrix_content)
            features.dimensionality = self.detect_dimensionality(matrix_content)
        else:
            # Parse text-based matrix
            features = self.parse_text_matrix_structure(matrix_content)
        
        return features
    
    def detect_ranges(self, df: pd.DataFrame) -> bool:
        """Detect if matrix uses range values"""
        range_patterns = [
            r'\d+-\d+',  # Numeric ranges: 620-680
            r'≥\s*\d+',  # Greater than or equal
            r'>\s*\d+',  # Greater than
            r'<\s*\d+',  # Less than
            r'\d+%?\s*-\s*\d+%?',  # Percentage ranges
        ]
        
        for column in df.columns:
            for value in df[column].dropna().astype(str):
                for pattern in range_patterns:
                    if re.search(pattern, value):
                        return True
        
        return False
```

### 2. Range Extractor (`range_extractor.py`)

```python
class RangeExtractor:
    """Extract and normalize ranges from matrices"""
    
    def __init__(self):
        self.range_patterns = self._compile_range_patterns()
        self.normalizers = self._initialize_normalizers()
        
    def extract_ranges(self, matrix: pd.DataFrame, 
                      classification: MatrixClassification) -> RangeStructure:
        """Extract all ranges from matrix"""
        
        range_structure = RangeStructure()
        
        # Extract column ranges (dimensions)
        for col in matrix.columns:
            col_ranges = self.extract_column_ranges(matrix[col], col)
            if col_ranges:
                range_structure.dimensions[col] = col_ranges
        
        # Extract row ranges
        if matrix.index.name:
            row_ranges = self.extract_index_ranges(matrix.index)
            if row_ranges:
                range_structure.dimensions[matrix.index.name] = row_ranges
        
        # Extract cell ranges (values)
        cell_ranges = self.extract_cell_ranges(matrix)
        range_structure.cell_ranges = cell_ranges
        
        # Normalize and validate
        range_structure = self.normalize_ranges(range_structure)
        range_structure = self.validate_range_coverage(range_structure)
        
        return range_structure
    
    def extract_column_ranges(self, series: pd.Series, column_name: str) -> List[Range]:
        """Extract ranges from a column"""
        ranges = []
        
        for value in series.dropna().unique():
            value_str = str(value)
            
            # Try each range pattern
            for pattern_name, pattern in self.range_patterns.items():
                match = pattern.search(value_str)
                if match:
                    range_obj = self.parse_range(match, pattern_name, column_name)
                    if range_obj:
                        ranges.append(range_obj)
        
        # Sort and merge overlapping ranges
        ranges = self.merge_overlapping_ranges(sorted(ranges))
        
        return ranges
    
    def parse_range(self, match: re.Match, pattern_type: str, dimension: str) -> Optional[Range]:
        """Parse range from regex match"""
        
        if pattern_type == "numeric_range":
            return NumericRange(
                dimension=dimension,
                min_value=float(match.group(1)),
                max_value=float(match.group(2)),
                inclusive_min=True,
                inclusive_max=True
            )
        
        elif pattern_type == "percentage_range":
            return PercentageRange(
                dimension=dimension,
                min_value=float(match.group(1)),
                max_value=float(match.group(2)),
                format="percentage"
            )
        
        elif pattern_type == "fico_range":
            # Special handling for FICO scores
            return FICORange(
                dimension="fico_score",
                min_value=int(match.group(1)),
                max_value=int(match.group(2)) if match.group(2) else 850,
                tier=self.determine_fico_tier(int(match.group(1)))
            )
        
        elif pattern_type == "comparison":
            operator = match.group(1)
            value = float(match.group(2))
            
            if operator in ["≥", ">="]:
                return NumericRange(dimension=dimension, min_value=value, max_value=float('inf'))
            elif operator in ["≤", "<="]:
                return NumericRange(dimension=dimension, min_value=float('-inf'), max_value=value)
            elif operator == ">":
                return NumericRange(dimension=dimension, min_value=value, max_value=float('inf'), 
                                  inclusive_min=False)
            elif operator == "<":
                return NumericRange(dimension=dimension, min_value=float('-inf'), max_value=value,
                                  inclusive_max=False)
        
        return None
    
    def normalize_ranges(self, range_structure: RangeStructure) -> RangeStructure:
        """Normalize ranges for consistent processing"""
        
        for dimension, ranges in range_structure.dimensions.items():
            normalizer = self.normalizers.get(dimension.lower())
            
            if normalizer:
                normalized_ranges = normalizer.normalize(ranges)
                range_structure.dimensions[dimension] = normalized_ranges
            else:
                # Generic normalization
                range_structure.dimensions[dimension] = self.generic_normalize(ranges)
        
        return range_structure
```

### 3. Matrix to Guideline Mapper (`matrix_to_guideline_mapper.py`)

```python
class MatrixToGuidelineMapper:
    """Maps matrix cells and sections to guidelines content"""
    
    def __init__(self, guidelines_graph: NavigationGraph):
        self.guidelines_graph = guidelines_graph
        self.semantic_matcher = SemanticMatcher()
        
    def map_matrix_to_guidelines(self, matrix: ProcessedMatrix, 
                               classification: MatrixClassification) -> MatrixGuidelineMapping:
        """Create comprehensive mapping between matrix and guidelines"""
        
        mapping = MatrixGuidelineMapping()
        
        # Step 1: Map matrix dimensions to guideline sections
        dimension_mappings = self.map_dimensions_to_sections(
            matrix.dimensions, 
            self.guidelines_graph.nodes
        )
        mapping.dimension_mappings = dimension_mappings
        
        # Step 2: Map matrix cells to specific guideline paragraphs
        cell_mappings = self.map_cells_to_paragraphs(
            matrix.cells,
            self.guidelines_graph
        )
        mapping.cell_mappings = cell_mappings
        
        # Step 3: Map decision outcomes to guideline policies
        outcome_mappings = self.map_outcomes_to_policies(
            matrix.outcomes,
            self.guidelines_graph.decision_trees
        )
        mapping.outcome_mappings = outcome_mappings
        
        # Step 4: Identify conflicts and inconsistencies
        conflicts = self.detect_conflicts(matrix, self.guidelines_graph)
        mapping.conflicts = conflicts
        
        # Step 5: Create bidirectional references
        mapping.create_bidirectional_references()
        
        return mapping
    
    def map_dimensions_to_sections(self, dimensions: List[MatrixDimension], 
                                  guideline_nodes: List[NavigationNode]) -> List[DimensionMapping]:
        """Map matrix dimensions to guideline sections"""
        mappings = []
        
        for dimension in dimensions:
            # Find relevant guideline sections
            relevant_sections = self.find_relevant_sections(dimension, guideline_nodes)
            
            for section in relevant_sections:
                confidence = self.calculate_mapping_confidence(dimension, section)
                
                if confidence > 0.7:
                    mapping = DimensionMapping(
                        dimension=dimension,
                        guideline_section=section,
                        relationship_type=self.determine_relationship_type(dimension, section),
                        confidence=confidence,
                        evidence=self.extract_mapping_evidence(dimension, section)
                    )
                    mappings.append(mapping)
        
        return mappings
    
    def map_cells_to_paragraphs(self, cells: List[MatrixCell], 
                               guidelines_graph: NavigationGraph) -> List[CellMapping]:
        """Map individual matrix cells to guideline paragraphs"""
        mappings = []
        
        for cell in cells:
            # Build semantic query from cell
            query = self.build_cell_query(cell)
            
            # Search guidelines for relevant content
            relevant_chunks = self.semantic_matcher.find_relevant_chunks(
                query, 
                guidelines_graph.get_all_chunks()
            )
            
            for chunk in relevant_chunks[:3]:  # Top 3 matches
                mapping = CellMapping(
                    cell=cell,
                    guideline_chunk=chunk,
                    relationship_type=self.determine_cell_relationship(cell, chunk),
                    confidence=chunk.similarity_score,
                    context={
                        "cell_coordinates": cell.get_coordinates(),
                        "chunk_path": chunk.navigation_path,
                        "semantic_similarity": chunk.similarity_score
                    }
                )
                mappings.append(mapping)
        
        return mappings
    
    def detect_conflicts(self, matrix: ProcessedMatrix, 
                        guidelines_graph: NavigationGraph) -> List[Conflict]:
        """Detect conflicts between matrix and guidelines"""
        conflicts = []
        
        # Check numeric threshold conflicts
        threshold_conflicts = self.check_threshold_conflicts(matrix, guidelines_graph)
        conflicts.extend(threshold_conflicts)
        
        # Check logical rule conflicts
        rule_conflicts = self.check_rule_conflicts(matrix, guidelines_graph)
        conflicts.extend(rule_conflicts)
        
        # Check coverage gaps
        coverage_gaps = self.check_coverage_gaps(matrix, guidelines_graph)
        conflicts.extend(coverage_gaps)
        
        return conflicts
```

## Data Models

### Classification Models

```python
@dataclass
class MatrixClassification:
    """Multi-type matrix classification result"""
    primary_type: str
    detected_types: Dict[str, float]  # Type -> Confidence
    weights: Dict[str, float]  # Processing weights
    processing_strategy: str  # SINGLE_TYPE, HYBRID_MULTI_TYPE, COMPLEX_HYBRID
    complexity_score: float  # 0.0 - 1.0
    dimensions: List[str]  # Detected dimensions
    confidence_threshold: float
    metadata: Dict[str, Any]
    
    def get_processing_instructions(self) -> ProcessingInstructions:
        """Get specific processing instructions based on classification"""
        if self.processing_strategy == "SINGLE_TYPE":
            return SingleTypeProcessor(self.primary_type).get_instructions()
        elif self.processing_strategy == "HYBRID_MULTI_TYPE":
            return HybridProcessor(self.detected_types, self.weights).get_instructions()
        else:
            return ComplexHybridProcessor(self).get_instructions()

@dataclass
class Range:
    """Base range class"""
    dimension: str
    min_value: Union[float, int]
    max_value: Union[float, int]
    inclusive_min: bool = True
    inclusive_max: bool = True
    
    def contains(self, value: Union[float, int]) -> bool:
        """Check if value is within range"""
        if self.inclusive_min and self.inclusive_max:
            return self.min_value <= value <= self.max_value
        elif self.inclusive_min:
            return self.min_value <= value < self.max_value
        elif self.inclusive_max:
            return self.min_value < value <= self.max_value
        else:
            return self.min_value < value < self.max_value
    
    def overlaps(self, other: 'Range') -> bool:
        """Check if ranges overlap"""
        return not (self.max_value < other.min_value or self.min_value > other.max_value)

@dataclass
class FICORange(Range):
    """Specialized FICO score range"""
    tier: str  # Excellent, Good, Fair, Poor
    
    def get_tier_name(self) -> str:
        if self.min_value >= 740:
            return "Excellent"
        elif self.min_value >= 680:
            return "Good"
        elif self.min_value >= 620:
            return "Fair"
        else:
            return "Poor"

@dataclass
class MatrixCell:
    """Individual matrix cell with metadata"""
    row_index: Union[str, int]
    column_index: Union[str, int]
    value: Any
    cell_type: str  # DECISION, THRESHOLD, RATE, RULE
    coordinates: Dict[str, Any]  # Multi-dimensional coordinates
    
    def get_dimensions(self) -> Dict[str, Any]:
        """Get all dimensions for this cell"""
        return {
            "row": self.row_index,
            "column": self.column_index,
            **self.coordinates
        }
```

### Mapping Models

```python
@dataclass
class MatrixGuidelineMapping:
    """Complete mapping between matrix and guidelines"""
    dimension_mappings: List[DimensionMapping]
    cell_mappings: List[CellMapping]
    outcome_mappings: List[OutcomeMapping]
    conflicts: List[Conflict]
    
    def create_bidirectional_references(self):
        """Create references in both directions"""
        # Matrix → Guidelines
        self.matrix_to_guidelines = defaultdict(list)
        for mapping in self.cell_mappings:
            self.matrix_to_guidelines[mapping.cell.id].append(
                mapping.guideline_chunk.id
            )
        
        # Guidelines → Matrix
        self.guidelines_to_matrix = defaultdict(list)
        for mapping in self.cell_mappings:
            self.guidelines_to_matrix[mapping.guideline_chunk.id].append(
                mapping.cell.id
            )

@dataclass
class Conflict:
    """Conflict between matrix and guidelines"""
    conflict_type: str  # THRESHOLD_MISMATCH, MISSING_COVERAGE, LOGICAL_CONFLICT
    severity: str  # HIGH, MEDIUM, LOW
    matrix_element: Union[MatrixCell, MatrixDimension]
    guideline_element: Union[NavigationNode, Entity]
    description: str
    resolution_suggestions: List[str]
```

## Neo4j Schema

```cypher
// Matrix Nodes
(:Matrix {
  matrix_id: "matrix_001",
  document_id: "doc_123",
  primary_type: "MULTI_DIMENSIONAL_DECISION",
  detected_types: ["MULTI_DIMENSIONAL_DECISION", "RISK_BASED_SEGMENTATION"],
  complexity_score: 0.87,
  dimensions: ["fico_score", "ltv_ratio", "property_type"]
})

// Matrix Cell Nodes
(:MatrixCell {
  cell_id: "cell_001",
  matrix_id: "matrix_001",
  row_index: "620-679",
  column_index: "70-80%",
  value: "Approved with conditions",
  cell_type: "DECISION"
})

// Range Nodes
(:Range {
  range_id: "range_fico_001",
  dimension: "fico_score",
  min_value: 620,
  max_value: 679,
  inclusive: true
})

// Relationships
(:Matrix)-[:CONTAINS_CELL]->(:MatrixCell)
(:MatrixCell)-[:USES_RANGE]->(:Range)
(:MatrixCell)-[:REFERENCES]->(:NavigationNode)
(:Matrix)-[:ELABORATED_BY]->(:NavigationNode)
(:MatrixCell)-[:CONFLICTS_WITH]->(:Entity)
```

## Processing Pipeline

### 1. Matrix Analysis
```python
# Load matrix document
matrix_doc = load_matrix("NQM_Qualification_Matrix.xlsx")

# Classify matrix
classifier = MatrixClassifier()
classification = classifier.classify_matrix(matrix_doc.content, matrix_doc.metadata)

print(f"Primary Type: {classification.primary_type}")
print(f"All Types: {classification.detected_types}")
print(f"Strategy: {classification.processing_strategy}")
```

### 2. Range Extraction
```python
# Extract ranges
range_extractor = RangeExtractor()
range_structure = range_extractor.extract_ranges(matrix_doc.df, classification)

# Validate coverage
validation = range_extractor.validate_range_coverage(range_structure)
if validation.has_gaps:
    print(f"Coverage gaps found: {validation.gaps}")
```

### 3. Guidelines Mapping
```python
# Map to guidelines
mapper = MatrixToGuidelineMapper(guidelines_graph)
mapping = mapper.map_matrix_to_guidelines(processed_matrix, classification)

# Check for conflicts
if mapping.conflicts:
    for conflict in mapping.conflicts:
        print(f"{conflict.conflict_type}: {conflict.description}")
```

## Quality Metrics

- Matrix Classification Accuracy: >92%
- Range Extraction Completeness: >95%
- Guidelines Mapping Precision: >90%
- Conflict Detection Rate: >98%
- Processing Speed: <10 seconds per matrix