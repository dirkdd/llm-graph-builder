# Technical Specifications: Processing Pipeline

## Overview
This document defines the comprehensive processing pipeline for the enhanced LLM Graph Builder, detailing the flow from document upload through knowledge graph creation and quality assurance.

## Pipeline Architecture

### Overall Pipeline Flow
```
Document Upload → Package Assignment → Hierarchical Processing → 
Matrix Classification → Entity Extraction → Relationship Discovery → 
Knowledge Graph Integration → Quality Assurance → Ready for Querying
```

## Phase 1: Document Package Processing Pipeline

### 1. Package Assignment Stage

#### Input Processing
```python
class PackageAssignmentProcessor:
    def process_upload(self, files: List[UploadedFile], package_config: PackageConfig):
        # 1. Validate uploaded files
        validation_results = self.validate_files(files, package_config)
        
        # 2. Assign documents to package structure
        document_assignments = self.assign_documents_to_package(files, package_config)
        
        # 3. Initialize processing tasks
        processing_tasks = self.create_processing_tasks(document_assignments)
        
        # 4. Queue for processing
        self.queue_processing_tasks(processing_tasks)
        
        return ProcessingInitiationResponse(
            task_ids=processing_tasks,
            expected_completion=self.estimate_completion_time(files),
            package_id=package_config.package_id
        )
```

#### Validation Rules
- File type validation against package expectations
- Size limits and format verification  
- Duplicate detection within package
- Required document presence checking

### 2. Enhanced Hierarchical Chunking Stage

#### Enhanced Chunking Decision Pipeline
```python
class EnhancedChunkingPipeline:
    def should_use_hierarchical_chunking(self, pages: List[Document]) -> bool:
        """Enhanced decision logic for hierarchical chunking"""
        if not self.enable_hierarchical:
            return False
        
        # Calculate total document size
        total_size = sum(len(page.page_content) for page in pages)
        content = '\n'.join([page.page_content for page in pages])
        
        # Document type-specific size thresholds (UPDATED 2025-07-15)
        size_threshold = self._get_document_type_threshold(content)
        
        if total_size > size_threshold:
            self.logger.info(f"Document size {total_size} exceeds threshold {size_threshold}")
            return False
        
        # Enhanced structure detection
        has_structure = self._detect_document_structure(content)
        
        return has_structure
    
    def _get_document_type_threshold(self, content: str) -> int:
        """Document type-specific thresholds for optimal processing"""
        content_lower = content.lower()
        
        # Mortgage guidelines - typically 100-500 pages
        if any(term in content_lower for term in ['guidelines', 'eligibility', 'underwriting']):
            return 600000  # 600k characters (was 50k)
        
        # Matrix documents - typically 50-150 pages  
        elif any(term in content_lower for term in ['matrix', 'pricing', 'rate sheet']):
            return 300000  # 300k characters
        
        # Procedure documents - typically 20-100 pages
        elif any(term in content_lower for term in ['procedure', 'process', 'workflow']):
            return 200000  # 200k characters
        
        # Default threshold
        else:
            return self.max_doc_size_hierarchical  # 600k default
```

#### Enhanced Structure Detection
```python
def _detect_document_structure(self, content: str) -> bool:
    """Enhanced structure detection with mortgage-specific patterns"""
    # Updated patterns for mortgage documents (2025-07-15)
    indicators = [
        r'^\s*\d+\.\s+[A-Z]',                      # Numbered sections
        r'^\s*CHAPTER\s+\d+',                      # Chapter headings
        r'^\s*Section\s+\d+',                      # Section headings  
        r'^\s*\d+\.\d+\s+',                        # Subsection numbering
        r'^\s*[A-Z]{2,}\s*$',                      # All caps headings
        
        # NEW: Mortgage-specific patterns
        r'^\s*\d+\.\d+\.\d+\s+',                   # Three-level numbering (11.8.17)
        r'^\s*\d+\s+[A-Z][A-Z\s&/\-]+[A-Z]$',     # "2   GENERAL PROGRAM INFORMATION"
        r'^\s*\d+\.\d+\s+[A-Z][A-Z\s&/\-]+[A-Z]$', # "2.1 THE G1 GROUP LOAN PROGRAMS"
        r'^\s*PART\s+[IVX]+',                      # Roman numeral parts
        r'^\s*APPENDIX\s+[A-Z]',                   # Appendices
        r'^\s*[A-Z]{3,}(\s+[A-Z]{3,})*\s*$',      # Enhanced all caps
        r'^\s*\d+\s+[A-Z][A-Z\s]+$',              # "1   LENDING POLICY" style
    ]
    
    lines = content.split('\n')
    structure_count = 0
    
    # Check first 200 lines (increased from 100)
    check_lines = min(200, len(lines))
    
    for line in lines[:check_lines]:
        line = line.strip()
        if line and len(line) > 2:
            for pattern in indicators:
                if re.search(pattern, line):
                    structure_count += 1
                    break
    
    # Dynamic threshold based on document length
    total_lines = len([l for l in lines if l.strip()])
    if total_lines > 1000:      # Large documents (guidelines)
        min_threshold = max(5, min(15, total_lines // 100))
    elif total_lines > 500:     # Medium documents
        min_threshold = max(3, min(8, total_lines // 50))
    else:                       # Small documents
        min_threshold = 3
    
    return structure_count >= min_threshold
```

#### Configuration Updates (2025-07-15)
```python
# UPDATED: Enhanced chunking configuration
MAX_DOCUMENT_SIZE_FOR_HIERARCHICAL = 600000  # Increased from 50k to 600k
MAX_PROCESSING_TIME_HIERARCHICAL = 900       # Increased from 300s to 900s

# Document type thresholds
DOCUMENT_TYPE_THRESHOLDS = {
    'guidelines': 600000,    # Mortgage guidelines documents
    'matrix': 300000,        # Pricing and rate matrices  
    'procedures': 200000,    # Process and workflow docs
    'default': 600000        # All other documents
}
```

#### Navigation Extraction Pipeline
```python
class HierarchicalChunkingPipeline:
    def process_document(self, document: Document, package_config: PackageConfig):
        # 1. Enhanced navigation extraction with mortgage patterns
        navigation_structure = self.extract_navigation_enhanced(document)
        
        # 2. Create context-aware hierarchical chunks
        hierarchical_chunks = self.create_hierarchical_chunks(document, navigation_structure)
        
        # 3. Extract mortgage-specific entities with navigation context
        entity_extraction = self.extract_entities_with_context(
            navigation_structure.nodes, 
            hierarchical_chunks,
            package_config
        )
        
        # 4. Generate embeddings with enhanced metadata
        chunk_embeddings = self.generate_embeddings(hierarchical_chunks)
        
        # 5. Store with navigation relationships
        self.store_chunks_and_structure(hierarchical_chunks, navigation_structure, entity_extraction)
        
        return HierarchicalProcessingResult(
            chunk_count=len(hierarchical_chunks),
            navigation_nodes=navigation_structure.node_count,
            structure_quality_score=navigation_structure.quality_score,
            entities_extracted=len(entity_extraction.entities),
            processing_method='enhanced_hierarchical'
        )
```

#### Chunking Strategy Selection (Updated)
```python
def select_chunking_strategy(document_type: str, content_analysis: ContentAnalysis) -> ChunkingStrategy:
    """Enhanced strategy selection with size and structure considerations"""
    
    # Check if document qualifies for enhanced chunking
    if content_analysis.document_size <= DOCUMENT_TYPE_THRESHOLDS.get(document_type, 600000):
        if content_analysis.structure_score >= 0.7:
            return ChunkingStrategy.ENHANCED_HIERARCHICAL
    
    # Fallback strategies
    if document_type == "guidelines":
        if content_analysis.has_clear_sections:
            return ChunkingStrategy.SECTION_BASED
        else:
            return ChunkingStrategy.SEMANTIC_HIERARCHICAL
    elif document_type == "matrix":
        return ChunkingStrategy.TABLE_AWARE
    else:
        return ChunkingStrategy.HYBRID
```

### 3. Decision Tree Extraction Stage

#### Decision Path Processing
```python
class DecisionTreeProcessor:
    def extract_decision_trees(self, document: Document, navigation_structure: NavigationStructure):
        # 1. Identify decision-making sections
        decision_sections = self.identify_decision_sections(navigation_structure)
        
        # 2. Extract decision nodes
        all_decision_nodes = []
        for section in decision_sections:
            nodes = self.extract_decision_nodes(section)
            all_decision_nodes.extend(nodes)
        
        # 3. Build decision trees
        decision_trees = self.build_decision_trees(all_decision_nodes)
        
        # 4. Validate completeness
        validation_results = self.validate_decision_completeness(decision_trees)
        
        # 5. Auto-correct missing paths
        if validation_results.has_issues:
            corrected_trees = self.auto_correct_decision_trees(decision_trees, validation_results)
            return corrected_trees
        
        return decision_trees
```

#### Completeness Validation
```python
def validate_decision_completeness(trees: List[DecisionTree]) -> ValidationResult:
    issues = []
    
    for tree in trees:
        # Check ROOT → LEAF connectivity
        if not self.has_complete_paths(tree):
            issues.append(f"Tree {tree.tree_id} has incomplete paths")
        
        # Validate minimum node counts
        if len(tree.leaf_nodes) < 2:
            issues.append(f"Tree {tree.tree_id} needs more leaf nodes")
        
        # Check for orphaned nodes
        orphaned = self.find_orphaned_nodes(tree)
        if orphaned:
            issues.append(f"Tree {tree.tree_id} has orphaned nodes: {orphaned}")
    
    return ValidationResult(
        is_valid=len(issues) == 0,
        issues=issues,
        auto_correctable=self.assess_auto_correctability(issues)
    )
```

## Phase 2: Matrix Processing Pipeline

### 1. Matrix Detection and Classification

#### Multi-Type Classification Pipeline
```python
class MatrixClassificationPipeline:
    def classify_matrix(self, matrix_content: str, context: DocumentContext):
        # 1. Detect table structure
        table_structure = self.detect_table_structure(matrix_content)
        
        # 2. Analyze content patterns
        content_patterns = self.analyze_content_patterns(matrix_content)
        
        # 3. Multi-type classification
        type_classifications = self.classify_matrix_types(table_structure, content_patterns)
        
        # 4. Confidence scoring
        confidence_scores = self.calculate_confidence_scores(type_classifications)
        
        # 5. Select primary type and processing strategy
        primary_type, processing_strategy = self.select_processing_strategy(type_classifications, confidence_scores)
        
        return MatrixClassification(
            detected_types=type_classifications,
            primary_type=primary_type,
            confidence_scores=confidence_scores,
            processing_strategy=processing_strategy
        )
```

### 2. Range Extraction Pipeline

#### Intelligent Range Processing
```python
class RangeExtractionPipeline:
    def extract_ranges(self, matrix: MatrixClassification, content: str):
        # 1. Identify dimensions
        dimensions = self.identify_matrix_dimensions(matrix, content)
        
        # 2. Extract raw values
        raw_extractions = []
        for dimension in dimensions:
            raw_values = self.extract_raw_values(dimension, content)
            raw_extractions.append((dimension, raw_values))
        
        # 3. Normalize and validate
        normalized_ranges = []
        for dimension, raw_values in raw_extractions:
            normalized = self.normalize_range_values(dimension, raw_values)
            validated = self.validate_range_consistency(normalized)
            normalized_ranges.append(RangeExtraction(
                dimension_name=dimension.name,
                raw_values=raw_values,
                normalized_values=validated,
                validation_status="VALIDATED" if validated.is_consistent else "NEEDS_REVIEW"
            ))
        
        return normalized_ranges
```

### 3. Cross-Document Relationship Discovery

#### Relationship Detection Pipeline
```python
class RelationshipDiscoveryPipeline:
    def discover_relationships(self, documents: List[Document], package: DocumentPackage):
        # 1. Identify potential relationships
        potential_relationships = self.identify_potential_relationships(documents)
        
        # 2. Validate relationships
        validated_relationships = []
        for relationship in potential_relationships:
            validation = self.validate_relationship(relationship)
            if validation.is_valid:
                validated_relationships.append(relationship)
        
        # 3. Detect conflicts
        conflicts = self.detect_conflicts(validated_relationships)
        
        # 4. Generate consistency report
        consistency_report = self.generate_consistency_report(validated_relationships, conflicts)
        
        return RelationshipDiscoveryResult(
            relationships=validated_relationships,
            conflicts=conflicts,
            consistency_report=consistency_report
        )
```

## Phase 3: Knowledge Graph Integration Pipeline

### 1. Multi-Layer Graph Construction

#### Layer Assembly Pipeline
```python
class MultiLayerGraphPipeline:
    def construct_knowledge_graph(self, processed_documents: List[ProcessedDocument]):
        # 1. Build Layer 1: Document Layer
        document_layer = self.build_document_layer(processed_documents)
        
        # 2. Build Layer 2: Structure Layer
        structure_layer = self.build_structure_layer(processed_documents)
        
        # 3. Build Layer 3: Entity Layer
        entity_layer = self.build_entity_layer(processed_documents)
        
        # 4. Build Layer 4: Decision Layer
        decision_layer = self.build_decision_layer(processed_documents)
        
        # 5. Build Layer 5: Business Layer
        business_layer = self.build_business_layer(processed_documents)
        
        # 6. Connect layers
        inter_layer_connections = self.connect_layers([
            document_layer, structure_layer, entity_layer, decision_layer, business_layer
        ])
        
        # 7. Validate graph integrity
        validation_results = self.validate_graph_integrity(inter_layer_connections)
        
        return KnowledgeGraph(
            layers=[document_layer, structure_layer, entity_layer, decision_layer, business_layer],
            connections=inter_layer_connections,
            validation_status=validation_results
        )
```

### 2. Hybrid Retrieval System Pipeline

#### Query Processing Pipeline
```python
class HybridRetrievalPipeline:
    def process_query(self, query: str, context: QueryContext):
        # 1. Query classification
        classification = self.classify_query(query, context)
        
        # 2. Select retrieval modes
        retrieval_modes = self.select_retrieval_modes(classification)
        
        # 3. Execute parallel retrieval
        retrieval_results = self.execute_parallel_retrieval(query, retrieval_modes)
        
        # 4. Merge and rank results
        merged_results = self.merge_and_rank_results(retrieval_results)
        
        # 5. Generate response
        response = self.generate_response(merged_results, query, context)
        
        return HybridRetrievalResponse(
            query=query,
            retrieval_modes_used=retrieval_modes,
            results=merged_results,
            response=response,
            confidence_score=response.confidence
        )
```

## Phase 4: AI Enhancement and Production Pipeline

### 1. Autonomous Quality Assurance Pipeline

#### Continuous QA Monitoring
```python
class AutonomousQAPipeline:
    def run_qa_cycle(self):
        # 1. System health check
        system_health = self.check_system_health()
        
        # 2. Document processing quality check
        processing_quality = self.check_processing_quality()
        
        # 3. Relationship consistency check
        relationship_quality = self.check_relationship_consistency()
        
        # 4. Decision tree completeness check
        decision_tree_quality = self.check_decision_tree_completeness()
        
        # 5. Auto-correction
        correction_results = self.auto_correct_issues([
            system_health, processing_quality, relationship_quality, decision_tree_quality
        ])
        
        # 6. Report critical issues
        critical_issues = self.identify_critical_issues(correction_results)
        if critical_issues:
            self.report_critical_issues(critical_issues)
        
        # 7. Update quality metrics
        self.update_quality_metrics(correction_results)
```

### 2. Production Features Pipeline

#### Webhook Processing Pipeline
```python
class WebhookProcessingPipeline:
    def process_webhook_event(self, event: WebhookEvent):
        # 1. Validate event
        validation = self.validate_event(event)
        
        # 2. Find subscribed endpoints
        endpoints = self.find_subscribed_endpoints(event)
        
        # 3. Prepare payloads
        payloads = self.prepare_payloads(event, endpoints)
        
        # 4. Deliver webhooks
        delivery_results = self.deliver_webhooks(payloads)
        
        # 5. Handle failures and retries
        self.handle_delivery_failures(delivery_results)
        
        # 6. Update delivery metrics
        self.update_delivery_metrics(delivery_results)
```

## Performance Optimization

### 1. Processing Optimization
- Parallel processing for independent tasks
- Streaming for large documents
- Caching for repeated operations
- Database connection pooling

### 2. Memory Management
- Chunked processing for large files
- Garbage collection optimization
- Memory monitoring and alerts
- Resource cleanup protocols

### 3. Scalability Patterns
- Horizontal scaling for processing workers
- Load balancing for API endpoints
- Database sharding for large datasets
- Async processing for long-running tasks

## Error Handling and Recovery

### 1. Error Classification
- **Recoverable Errors**: Temporary failures, network issues
- **Data Errors**: Malformed input, validation failures
- **System Errors**: Resource exhaustion, service unavailability
- **Critical Errors**: Data corruption, security breaches

### 2. Recovery Strategies
- Automatic retry with exponential backoff
- Fallback processing modes
- Manual intervention workflows
- Data restoration procedures

### 3. Monitoring and Alerting
- Real-time processing metrics
- Error rate monitoring
- Performance threshold alerts
- Quality degradation detection

## Quality Assurance

### 1. Validation Checkpoints
- Input validation at each stage
- Output quality verification
- Relationship consistency checks
- Performance metric validation

### 2. Quality Metrics
- Processing accuracy rates
- Relationship discovery precision
- Response time measurements
- User satisfaction scores

### 3. Continuous Improvement
- A/B testing for processing improvements
- User feedback integration
- Performance optimization cycles
- Model fine-tuning procedures