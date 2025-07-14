# Phase 2.2: Cross-Document Relationship Engine

## Overview
The Cross-Document Relationship Engine discovers, validates, and maintains sophisticated relationships between guidelines, matrices, and rate sheets. This engine ensures consistency across document types and enables intelligent qualification analysis by understanding how documents reference and depend on each other.

## Core Capabilities

### Relationship Discovery
- Automatic detection of cross-references between documents
- Semantic matching of related concepts across document types
- Temporal relationship tracking for document versions
- Hierarchical relationship inheritance

### Consistency Validation
- Real-time validation of numeric thresholds
- Program coverage verification
- Requirement completeness checking
- Conflict detection and resolution

### Qualification Intelligence
- Matrix-driven borrower qualification
- Decision path tracing across documents
- Alternative program recommendations
- Exception handling and routing

## System Architecture

### 1. Relationship Detector (`relationship_detector.py`)

```python
class CrossDocumentRelationshipDetector:
    """Discovers relationships between different document types"""
    
    def __init__(self, llm_model: str = "claude-sonnet-4"):
        self.llm = get_llm(llm_model)
        self.semantic_analyzer = SemanticAnalyzer()
        self.pattern_matcher = RelationshipPatternMatcher()
        
    def detect_relationships(self, 
                           guidelines_graph: NavigationGraph,
                           matrix_graph: MatrixGraph,
                           rate_sheet_graph: Optional[RateSheetGraph] = None) -> RelationshipNetwork:
        """Detect all relationships between documents"""
        
        relationship_network = RelationshipNetwork()
        
        # Step 1: Direct reference detection
        direct_refs = self.detect_direct_references(guidelines_graph, matrix_graph)
        relationship_network.add_relationships(direct_refs)
        
        # Step 2: Semantic relationship discovery
        semantic_rels = self.discover_semantic_relationships(guidelines_graph, matrix_graph)
        relationship_network.add_relationships(semantic_rels)
        
        # Step 3: Structural relationship mapping
        structural_rels = self.map_structural_relationships(guidelines_graph, matrix_graph)
        relationship_network.add_relationships(structural_rels)
        
        # Step 4: Decision tree to matrix mapping
        decision_rels = self.map_decision_trees_to_matrices(guidelines_graph, matrix_graph)
        relationship_network.add_relationships(decision_rels)
        
        # Step 5: Rate sheet integration (if available)
        if rate_sheet_graph:
            rate_rels = self.integrate_rate_sheet_relationships(
                guidelines_graph, matrix_graph, rate_sheet_graph
            )
            relationship_network.add_relationships(rate_rels)
        
        # Step 6: Validate and score relationships
        relationship_network = self.validate_and_score_relationships(relationship_network)
        
        return relationship_network
    
    def detect_direct_references(self, guidelines: NavigationGraph, 
                               matrices: MatrixGraph) -> List[CrossDocumentRelationship]:
        """Find explicit references between documents"""
        relationships = []
        
        # Pattern matching for references
        reference_patterns = [
            r'(?:see|refer to|as defined in)\s+(?:the\s+)?(\w+\s+matrix)',
            r'(?:per|according to)\s+(?:the\s+)?qualification\s+matrix',
            r'matrix\s+(?:section|table)\s+(\d+(?:\.\d+)?)',
            r'(?:detailed in|explained in)\s+(?:the\s+)?guidelines\s+section\s+(\d+(?:\.\d+)?)'
        ]
        
        # Check guidelines for matrix references
        for node in guidelines.nodes:
            for pattern in reference_patterns:
                matches = re.finditer(pattern, node.raw_summary, re.IGNORECASE)
                for match in matches:
                    # Find corresponding matrix element
                    matrix_element = self.find_matrix_element(match.group(1), matrices)
                    if matrix_element:
                        rel = CrossDocumentRelationship(
                            source_type="guidelines",
                            source_id=node.enhanced_node_id,
                            target_type="matrix",
                            target_id=matrix_element.id,
                            relationship_type="REFERENCES",
                            confidence=0.95,
                            evidence={"pattern": pattern, "text": match.group(0)}
                        )
                        relationships.append(rel)
        
        # Check matrices for guideline references
        for matrix in matrices.matrices:
            for cell in matrix.cells:
                if cell.has_reference:
                    guideline_ref = self.resolve_guideline_reference(cell.reference, guidelines)
                    if guideline_ref:
                        rel = CrossDocumentRelationship(
                            source_type="matrix",
                            source_id=cell.id,
                            target_type="guidelines",
                            target_id=guideline_ref.enhanced_node_id,
                            relationship_type="IMPLEMENTS",
                            confidence=0.92,
                            evidence={"cell_reference": cell.reference}
                        )
                        relationships.append(rel)
        
        return relationships
    
    def discover_semantic_relationships(self, guidelines: NavigationGraph,
                                      matrices: MatrixGraph) -> List[CrossDocumentRelationship]:
        """Discover relationships through semantic similarity"""
        relationships = []
        
        # Build semantic indices
        guideline_embeddings = self.build_semantic_index(guidelines)
        matrix_embeddings = self.build_semantic_index(matrices)
        
        # For each guideline section, find semantically similar matrix sections
        for g_node in guidelines.nodes:
            if g_node.node_type in ["SECTION", "DECISION_FLOW_SECTION"]:
                # Get top semantic matches from matrices
                matches = self.semantic_analyzer.find_similar(
                    query_embedding=guideline_embeddings[g_node.enhanced_node_id],
                    search_embeddings=matrix_embeddings,
                    top_k=5,
                    threshold=0.75
                )
                
                for match in matches:
                    matrix_element = matrices.get_element(match.id)
                    
                    # Determine relationship type based on content analysis
                    rel_type = self.analyze_semantic_relationship(g_node, matrix_element)
                    
                    if rel_type:
                        rel = CrossDocumentRelationship(
                            source_type="guidelines",
                            source_id=g_node.enhanced_node_id,
                            target_type="matrix",
                            target_id=match.id,
                            relationship_type=rel_type,
                            confidence=match.similarity,
                            evidence={
                                "semantic_similarity": match.similarity,
                                "key_terms": match.common_terms
                            }
                        )
                        relationships.append(rel)
        
        return relationships
    
    def map_decision_trees_to_matrices(self, guidelines: NavigationGraph,
                                      matrices: MatrixGraph) -> List[CrossDocumentRelationship]:
        """Map decision tree outcomes to matrix criteria"""
        relationships = []
        
        for tree in guidelines.decision_trees:
            # Map ROOT nodes to matrix headers
            for matrix in matrices.matrices:
                if self.matches_decision_context(tree.root, matrix):
                    rel = CrossDocumentRelationship(
                        source_type="decision_tree",
                        source_id=tree.root.enhanced_node_id,
                        target_type="matrix",
                        target_id=matrix.id,
                        relationship_type="EVALUATES_WITH",
                        confidence=0.88,
                        evidence={"decision_context": tree.root.title}
                    )
                    relationships.append(rel)
            
            # Map LEAF nodes to matrix outcomes
            for leaf in tree.leaves:
                matrix_outcomes = self.find_matrix_outcomes(leaf.outcome, matrices)
                for matrix_outcome in matrix_outcomes:
                    rel = CrossDocumentRelationship(
                        source_type="decision_leaf",
                        source_id=leaf.enhanced_node_id,
                        target_type="matrix_cell",
                        target_id=matrix_outcome.id,
                        relationship_type="OUTCOME_DEFINED_BY",
                        confidence=0.91,
                        evidence={
                            "leaf_outcome": leaf.outcome,
                            "matrix_value": matrix_outcome.value
                        }
                    )
                    relationships.append(rel)
        
        return relationships
```

### 2. Consistency Validator (`consistency_validator.py`)

```python
class CrossDocumentConsistencyValidator:
    """Validates consistency between related documents"""
    
    def __init__(self):
        self.threshold_validator = ThresholdValidator()
        self.coverage_validator = CoverageValidator()
        self.completeness_checker = CompletenessChecker()
        
    def validate_consistency(self, relationship_network: RelationshipNetwork,
                           documents: DocumentCollection) -> ConsistencyReport:
        """Comprehensive consistency validation"""
        
        report = ConsistencyReport()
        
        # Step 1: Validate numeric thresholds
        threshold_results = self.validate_threshold_consistency(
            relationship_network, documents
        )
        report.threshold_validation = threshold_results
        
        # Step 2: Validate program coverage
        coverage_results = self.validate_program_coverage(
            relationship_network, documents
        )
        report.coverage_validation = coverage_results
        
        # Step 3: Check requirement completeness
        completeness_results = self.check_requirement_completeness(
            relationship_network, documents
        )
        report.completeness_validation = completeness_results
        
        # Step 4: Detect conflicts
        conflicts = self.detect_conflicts(relationship_network, documents)
        report.conflicts = conflicts
        
        # Step 5: Generate recommendations
        report.recommendations = self.generate_recommendations(report)
        
        return report
    
    def validate_threshold_consistency(self, network: RelationshipNetwork,
                                     documents: DocumentCollection) -> ThresholdValidation:
        """Validate numeric thresholds across documents"""
        
        validation = ThresholdValidation()
        
        # Extract all thresholds from guidelines
        guideline_thresholds = self.extract_guideline_thresholds(
            documents.guidelines
        )
        
        # Extract all thresholds from matrices
        matrix_thresholds = self.extract_matrix_thresholds(
            documents.matrices
        )
        
        # Compare thresholds
        for g_threshold in guideline_thresholds:
            # Find corresponding matrix threshold
            m_threshold = self.find_corresponding_threshold(
                g_threshold, matrix_thresholds, network
            )
            
            if m_threshold:
                # Check alignment with tolerance
                alignment = self.check_threshold_alignment(g_threshold, m_threshold)
                
                if not alignment.is_aligned:
                    validation.misalignments.append(
                        ThresholdMisalignment(
                            guideline_threshold=g_threshold,
                            matrix_threshold=m_threshold,
                            difference=alignment.difference,
                            tolerance_exceeded=alignment.tolerance_exceeded,
                            severity=self.calculate_severity(alignment)
                        )
                    )
                else:
                    validation.aligned_count += 1
            else:
                validation.missing_in_matrix.append(g_threshold)
        
        # Check for matrix thresholds not in guidelines
        for m_threshold in matrix_thresholds:
            if not self.find_corresponding_threshold(m_threshold, guideline_thresholds, network):
                validation.missing_in_guidelines.append(m_threshold)
        
        validation.calculate_scores()
        return validation
    
    def check_threshold_alignment(self, g_threshold: Threshold, 
                                m_threshold: Threshold) -> ThresholdAlignment:
        """Check if thresholds align within tolerance"""
        
        alignment = ThresholdAlignment()
        
        if g_threshold.dimension != m_threshold.dimension:
            alignment.is_aligned = False
            alignment.reason = "Dimension mismatch"
            return alignment
        
        # Define tolerances by dimension
        tolerances = {
            "fico_score": 5,      # ±5 points
            "ltv_ratio": 0.01,    # ±1%
            "dti_ratio": 0.01,    # ±1%
            "loan_amount": 5000,  # ±$5,000
        }
        
        tolerance = tolerances.get(g_threshold.dimension.lower(), 0)
        
        # Check numeric values
        if isinstance(g_threshold.value, (int, float)) and isinstance(m_threshold.value, (int, float)):
            difference = abs(g_threshold.value - m_threshold.value)
            alignment.difference = difference
            alignment.tolerance = tolerance
            
            if difference <= tolerance:
                alignment.is_aligned = True
            else:
                alignment.is_aligned = False
                alignment.tolerance_exceeded = True
                alignment.reason = f"Difference {difference} exceeds tolerance {tolerance}"
        
        # Check range values
        elif hasattr(g_threshold, 'min_value') and hasattr(m_threshold, 'min_value'):
            min_diff = abs(g_threshold.min_value - m_threshold.min_value)
            max_diff = abs(g_threshold.max_value - m_threshold.max_value)
            
            if min_diff <= tolerance and max_diff <= tolerance:
                alignment.is_aligned = True
            else:
                alignment.is_aligned = False
                alignment.reason = f"Range difference exceeds tolerance"
        
        return alignment
    
    def detect_conflicts(self, network: RelationshipNetwork,
                        documents: DocumentCollection) -> List[Conflict]:
        """Detect all types of conflicts between documents"""
        
        conflicts = []
        
        # Type 1: Contradictory requirements
        contradictions = self.find_contradictions(network, documents)
        conflicts.extend(contradictions)
        
        # Type 2: Incomplete coverage
        coverage_gaps = self.find_coverage_gaps(network, documents)
        conflicts.extend(coverage_gaps)
        
        # Type 3: Logical inconsistencies
        logical_conflicts = self.find_logical_conflicts(network, documents)
        conflicts.extend(logical_conflicts)
        
        # Type 4: Version conflicts
        version_conflicts = self.find_version_conflicts(network, documents)
        conflicts.extend(version_conflicts)
        
        return conflicts
```

### 3. Qualification Analyzer (`qualification_analyzer.py`)

```python
class MatrixDrivenQualificationAnalyzer:
    """Analyzes borrower qualification using matrix criteria and guidelines"""
    
    def __init__(self, relationship_network: RelationshipNetwork):
        self.network = relationship_network
        self.decision_engine = DecisionEngine()
        self.program_matcher = ProgramMatcher()
        
    def analyze_qualification(self, borrower_profile: BorrowerProfile,
                            available_programs: List[Program]) -> QualificationAnalysis:
        """Comprehensive qualification analysis"""
        
        analysis = QualificationAnalysis()
        analysis.borrower_profile = borrower_profile
        
        # Step 1: Check each program
        for program in available_programs:
            program_result = self.check_program_qualification(
                borrower_profile, program
            )
            analysis.program_results[program.id] = program_result
        
        # Step 2: Rank programs by qualification likelihood
        analysis.ranked_programs = self.rank_programs_by_fit(
            analysis.program_results
        )
        
        # Step 3: Find best qualified program
        analysis.best_qualified = self.find_best_qualified_program(
            analysis.ranked_programs
        )
        
        # Step 4: Identify improvement opportunities
        analysis.improvement_suggestions = self.suggest_improvements(
            borrower_profile, analysis.program_results
        )
        
        # Step 5: Generate decision paths
        analysis.decision_paths = self.generate_decision_paths(
            borrower_profile, analysis.best_qualified
        )
        
        return analysis
    
    def check_program_qualification(self, profile: BorrowerProfile,
                                   program: Program) -> ProgramQualificationResult:
        """Check qualification for a specific program"""
        
        result = ProgramQualificationResult(program_id=program.id)
        
        # Get program's matrix
        matrix = program.get_qualification_matrix()
        if not matrix:
            result.status = "NO_MATRIX"
            return result
        
        # Find applicable cell in matrix
        applicable_cell = self.find_applicable_cell(profile, matrix)
        
        if not applicable_cell:
            result.status = "NO_MATCHING_CRITERIA"
            result.reason = "Profile doesn't match any matrix criteria"
            return result
        
        # Check cell outcome
        if applicable_cell.value in ["Approved", "Eligible", "Qualified"]:
            result.status = "QUALIFIED"
            result.confidence = 0.95
        elif applicable_cell.value in ["Declined", "Ineligible", "Not Qualified"]:
            result.status = "NOT_QUALIFIED"
            result.confidence = 0.95
        elif applicable_cell.value in ["Manual Review", "Refer", "Exception"]:
            result.status = "MANUAL_REVIEW"
            result.confidence = 0.70
        else:
            # Complex outcome - need to check guidelines
            result = self.evaluate_complex_outcome(
                profile, applicable_cell, program
            )
        
        # Add supporting evidence
        result.evidence = self.gather_qualification_evidence(
            profile, applicable_cell, program
        )
        
        # Check for exceptions
        result.exceptions = self.check_exceptions(profile, program)
        
        return result
    
    def find_applicable_cell(self, profile: BorrowerProfile,
                           matrix: Matrix) -> Optional[MatrixCell]:
        """Find the matrix cell that applies to the borrower profile"""
        
        # Build query from profile
        query_dimensions = {
            "fico_score": profile.fico_score,
            "ltv_ratio": profile.ltv_ratio,
            "dti_ratio": profile.dti_ratio,
            "property_type": profile.property_type,
            "loan_amount": profile.loan_amount
        }
        
        # Find matching cell
        for cell in matrix.cells:
            if self.cell_matches_profile(cell, query_dimensions):
                return cell
        
        # No exact match - find closest
        return self.find_closest_cell(query_dimensions, matrix)
    
    def cell_matches_profile(self, cell: MatrixCell,
                           query_dimensions: Dict[str, Any]) -> bool:
        """Check if cell matches the query dimensions"""
        
        for dimension, value in query_dimensions.items():
            cell_range = cell.get_range_for_dimension(dimension)
            
            if cell_range:
                if not cell_range.contains(value):
                    return False
            else:
                # Check exact match
                cell_value = cell.get_value_for_dimension(dimension)
                if cell_value and cell_value != value:
                    return False
        
        return True
    
    def generate_decision_paths(self, profile: BorrowerProfile,
                              program: Program) -> List[DecisionPath]:
        """Generate complete decision paths for qualification"""
        
        paths = []
        
        # Get program's decision trees
        decision_trees = self.network.get_decision_trees_for_program(program.id)
        
        for tree in decision_trees:
            path = DecisionPath(tree_id=tree.id)
            
            # Start at ROOT
            current_node = tree.root
            path.add_step(DecisionStep(
                node=current_node,
                evaluation=self.evaluate_node(current_node, profile),
                result="CONTINUE"
            ))
            
            # Traverse through BRANCHes
            while current_node.has_children():
                next_node = self.select_next_node(current_node, profile)
                
                if not next_node:
                    break
                
                evaluation = self.evaluate_node(next_node, profile)
                path.add_step(DecisionStep(
                    node=next_node,
                    evaluation=evaluation,
                    result=evaluation.result
                ))
                
                current_node = next_node
                
                # Check if we've reached a LEAF
                if next_node.is_leaf():
                    path.outcome = next_node.outcome
                    break
            
            paths.append(path)
        
        return paths
```

## Data Models

### Relationship Models

```python
@dataclass
class CrossDocumentRelationship:
    """Relationship between documents of different types"""
    relationship_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    source_type: str  # guidelines, matrix, rate_sheet
    source_id: str
    target_type: str
    target_id: str
    relationship_type: str  # ELABORATES, DEFINES, IMPLEMENTS, etc.
    confidence: float
    evidence: Dict[str, Any]
    
    # Validation
    validated: bool = False
    validation_timestamp: Optional[datetime] = None
    conflicts: List[str] = field(default_factory=list)

@dataclass
class RelationshipNetwork:
    """Network of all cross-document relationships"""
    relationships: List[CrossDocumentRelationship] = field(default_factory=list)
    
    # Indices for fast lookup
    by_source: Dict[str, List[CrossDocumentRelationship]] = field(default_factory=lambda: defaultdict(list))
    by_target: Dict[str, List[CrossDocumentRelationship]] = field(default_factory=lambda: defaultdict(list))
    by_type: Dict[str, List[CrossDocumentRelationship]] = field(default_factory=lambda: defaultdict(list))
    
    def add_relationship(self, rel: CrossDocumentRelationship):
        """Add relationship and update indices"""
        self.relationships.append(rel)
        self.by_source[rel.source_id].append(rel)
        self.by_target[rel.target_id].append(rel)
        self.by_type[rel.relationship_type].append(rel)
```

### Consistency Models

```python
@dataclass
class ConsistencyReport:
    """Comprehensive consistency validation report"""
    threshold_validation: ThresholdValidation
    coverage_validation: CoverageValidation
    completeness_validation: CompletenessValidation
    conflicts: List[Conflict]
    recommendations: List[Recommendation]
    
    overall_score: float = 0.0
    is_consistent: bool = False
    
    def calculate_overall_score(self):
        """Calculate weighted overall consistency score"""
        weights = {
            "threshold": 0.4,
            "coverage": 0.3,
            "completeness": 0.2,
            "conflicts": 0.1
        }
        
        scores = {
            "threshold": self.threshold_validation.score,
            "coverage": self.coverage_validation.score,
            "completeness": self.completeness_validation.score,
            "conflicts": 1.0 - (len(self.conflicts) / 10.0)  # Penalty for conflicts
        }
        
        self.overall_score = sum(weights[k] * scores[k] for k in weights)
        self.is_consistent = self.overall_score >= 0.85

@dataclass
class Conflict:
    """Document conflict representation"""
    conflict_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    conflict_type: str  # THRESHOLD_MISMATCH, MISSING_COVERAGE, etc.
    severity: str  # HIGH, MEDIUM, LOW
    source_element: DocumentElement
    target_element: DocumentElement
    description: str
    
    # Resolution
    resolution_suggestions: List[str]
    auto_resolvable: bool = False
    resolution_applied: Optional[str] = None
```

### Qualification Models

```python
@dataclass
class QualificationAnalysis:
    """Complete qualification analysis results"""
    borrower_profile: BorrowerProfile
    program_results: Dict[str, ProgramQualificationResult]
    ranked_programs: List[Tuple[str, float]]  # (program_id, score)
    best_qualified: Optional[Program]
    improvement_suggestions: List[ImprovementSuggestion]
    decision_paths: List[DecisionPath]
    
    def get_qualified_programs(self) -> List[str]:
        """Get list of programs borrower qualifies for"""
        return [
            prog_id for prog_id, result in self.program_results.items()
            if result.status == "QUALIFIED"
        ]

@dataclass
class DecisionPath:
    """Complete decision path through a tree"""
    tree_id: str
    steps: List[DecisionStep] = field(default_factory=list)
    outcome: Optional[str] = None
    confidence: float = 0.0
    
    def add_step(self, step: DecisionStep):
        """Add step to path"""
        self.steps.append(step)
        # Update confidence based on step
        if len(self.steps) == 1:
            self.confidence = step.evaluation.confidence
        else:
            # Compound confidence
            self.confidence *= step.evaluation.confidence
```

## Neo4j Schema

```cypher
// Cross-Document Relationships
(:NavigationNode)-[:ELABORATES]->(:MatrixCell)
(:MatrixCell)-[:IMPLEMENTS]->(:NavigationNode)
(:DecisionTreeNode)-[:EVALUATES_WITH]->(:Matrix)
(:MatrixCell)-[:PRICING_IN]->(:RateSheet)

// Consistency Tracking
(:ConsistencyCheck {
  check_id: "chk_001",
  timestamp: datetime(),
  type: "threshold_validation",
  source_doc: "guidelines_001",
  target_doc: "matrix_001",
  result: "PASS",
  score: 0.95
})

// Conflict Nodes
(:Conflict {
  conflict_id: "conf_001",
  type: "THRESHOLD_MISMATCH",
  severity: "HIGH",
  description: "FICO threshold differs by 10 points",
  auto_resolvable: false
})

// Qualification Tracking
(:QualificationCheck {
  check_id: "qual_001",
  borrower_id: "borr_123",
  program_id: "prog_456",
  result: "QUALIFIED",
  confidence: 0.92,
  decision_path: [...]
})
```

## Processing Pipeline

### 1. Relationship Discovery
```python
# Initialize engine
relationship_engine = CrossDocumentRelationshipEngine()

# Discover relationships
network = relationship_engine.discover_relationships(
    guidelines_graph=guidelines_graph,
    matrix_graph=matrix_graph,
    rate_sheet_graph=rate_sheet_graph
)

print(f"Found {len(network.relationships)} relationships")
```

### 2. Consistency Validation
```python
# Validate consistency
validator = CrossDocumentConsistencyValidator()
consistency_report = validator.validate_consistency(network, documents)

if not consistency_report.is_consistent:
    print(f"Inconsistencies found: {len(consistency_report.conflicts)}")
    for conflict in consistency_report.conflicts:
        print(f"- {conflict.conflict_type}: {conflict.description}")
```

### 3. Qualification Analysis
```python
# Analyze borrower qualification
analyzer = MatrixDrivenQualificationAnalyzer(network)
qualification = analyzer.analyze_qualification(
    borrower_profile=borrower,
    available_programs=programs
)

print(f"Best qualified: {qualification.best_qualified.name}")
print(f"Qualification path: {qualification.decision_paths[0]}")
```

## Quality Metrics

- Relationship Detection Precision: >92%
- Consistency Validation Accuracy: >98%
- Conflict Detection Rate: >95%
- Qualification Analysis Speed: <500ms
- Cross-Document Navigation: <100ms