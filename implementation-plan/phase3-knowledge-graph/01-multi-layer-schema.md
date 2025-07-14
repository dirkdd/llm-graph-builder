# Phase 3.1: Multi-Layer Knowledge Graph Schema

## Overview
The Multi-Layer Knowledge Graph Schema implements a sophisticated, hierarchical graph architecture that integrates document packages, hierarchical navigation, matrix classifications, and their complex relationships. This system provides multiple abstraction layers enabling both granular analysis and high-level strategic insights.

## Core Architecture Principles

### Multi-Layer Design Philosophy
The knowledge graph operates on five distinct but interconnected layers:

1. **Document Layer**: Raw documents and their metadata
2. **Structure Layer**: Navigation hierarchies and document organization
3. **Entity Layer**: Extracted entities with contextual relationships
4. **Decision Layer**: Complete decision trees and outcome paths
5. **Business Layer**: High-level business rules and policy abstractions

Each layer maintains its own schema while providing seamless connectivity to other layers through well-defined relationship types.

## Schema Architecture

### Layer 1: Document Layer

#### Core Document Nodes

```cypher
// Document Package Nodes
(:DocumentPackage {
  package_id: "pkg_nqm_titanium_v2_1_0",
  package_name: "NQM Titanium Advantage Package",
  tenant_id: "the_g1_group",
  category: "NQM",
  version: "2.1.0",
  status: "ACTIVE",
  created_at: datetime(),
  updated_at: datetime(),
  template_type: "NQM_STANDARD",
  complexity_score: 0.87,
  completeness_score: 0.95,
  metadata: {
    expected_documents: ["guidelines", "matrix", "rate_sheet"],
    processing_rules: {...},
    validation_rules: {...}
  }
})

// Individual Document Nodes
(:Document {
  document_id: "doc_nqm_guidelines_001",
  file_name: "NQM_Guidelines_v10.pdf",
  document_type: "guidelines",
  package_id: "pkg_nqm_titanium_v2_1_0",
  upload_timestamp: datetime(),
  processing_status: "COMPLETED",
  file_size_mb: 12.4,
  page_count: 156,
  processing_metadata: {
    navigation_extracted: true,
    hierarchical_chunks_created: true,
    decision_trees_complete: true,
    entity_extraction_complete: true,
    matrix_mappings_created: true
  },
  quality_metrics: {
    navigation_extraction_accuracy: 0.97,
    entity_extraction_recall: 0.93,
    decision_tree_completeness: 1.0
  }
})

// Matrix Document Specialization
(:MatrixDocument:Document {
  document_id: "doc_nqm_matrix_001",
  matrix_classification: {
    primary_type: "MULTI_DIMENSIONAL_DECISION",
    detected_types: ["MULTI_DIMENSIONAL_DECISION", "RISK_BASED_SEGMENTATION"],
    complexity_score: 0.78,
    processing_strategy: "HYBRID_MULTI_TYPE"
  },
  dimensions: ["fico_score", "ltv_ratio", "property_type"],
  cell_count: 847,
  range_coverage: {
    fico_score: 0.95,
    ltv_ratio: 0.98,
    property_type: 1.0
  }
})
```

### Layer 2: Structure Layer

#### Navigation and Hierarchy Nodes

```cypher
// Navigation Nodes with Enhanced Hierarchy
(:NavigationNode {
  enhanced_node_id: "NQM_titanium_ch1_s2_ss3",
  node_type: "SUBSECTION",
  title: "Foreign National Borrower Requirements",
  raw_summary: "Detailed requirements for foreign national borrowers...",
  
  // Hierarchy Information
  chapter_number: 1,
  section_number: "1.2",
  subsection_number: "1.2.3",
  depth_level: 3,
  absolute_position: 15,
  relative_position_in_parent: 3,
  
  // Content Metadata
  word_count: 1247,
  paragraph_count: 8,
  contains_tables: true,
  contains_lists: true,
  
  // Processing Metadata
  decision_tree_metadata: {
    contains_decision_logic: true,
    decision_types: ["BRANCH", "LEAF"],
    decision_complexity: 0.67,
    requires_complete_tree: true
  },
  
  // Quality Indicators
  extraction_confidence: 0.94,
  content_completeness: 0.98,
  hierarchy_validation: true
})

// Hierarchical Chunk Nodes
(:HierarchicalChunk {
  chunk_id: "chunk_NQM_titanium_ch1_s2_ss3_001",
  enhanced_node_id: "NQM_titanium_ch1_s2_ss3",
  content: "Foreign national borrowers must meet enhanced documentation requirements...",
  
  // Hierarchy Context
  navigation_path: "Chapter 1 > Section 1.2 > Subsection 1.2.3",
  breadcrumb: "NQM Guidelines > Borrower Eligibility > Foreign Nationals",
  parent_context: "Section 1.2 establishes general borrower requirements...",
  
  // Chunking Metadata
  chunk_type: "SEMANTIC_BOUNDARY",
  token_count: 1456,
  semantic_coherence_score: 0.91,
  boundary_confidence: 0.88,
  
  // Embeddings and Search
  embedding_vector: [0.123, -0.456, ...], // 1536 dimensions
  embedding_model: "text-embedding-3-large",
  search_keywords: ["foreign", "national", "documentation", "requirements"],
  
  // Cross-references
  references: ["1.1.2", "3.4.1", "matrix_qualification"],
  referenced_by: ["1.3.1", "2.1.4"]
})

// Decision Tree Nodes
(:DecisionTree {
  tree_id: "dt_foreign_national_eligibility",
  section_id: "NQM_titanium_ch1_s2_ss3",
  tree_name: "Foreign National Eligibility Decision Tree",
  
  // Tree Structure
  root_node_id: "dt_fn_root_001",
  branch_count: 7,
  leaf_count: 5,
  max_depth: 4,
  
  // Decision Metadata
  decision_domain: "BORROWER_ELIGIBILITY",
  complexity_score: 0.73,
  completeness_verified: true,
  
  // Outcomes
  possible_outcomes: ["APPROVE", "DECLINE", "REFER_MANUAL", "ADDITIONAL_DOCS"],
  default_outcome: "REFER_MANUAL",
  
  // Validation
  all_paths_tested: true,
  logical_consistency: true,
  exception_handling_complete: true
})
```

### Layer 3: Entity Layer

#### Enhanced Entity Nodes

```cypher
// Contextual Entity Nodes
(:Entity {
  enhanced_entity_id: "ent_foreign_national_req_001",
  temp_entity_id: "temp_ent_456",
  entity_type: "REQUIREMENT",
  primary_mention: "Foreign National Documentation Requirements",
  
  // Content and Context
  raw_context: "Foreign national borrowers must provide additional documentation including...",
  navigation_context: {
    node_id: "NQM_titanium_ch1_s2_ss3",
    navigation_path: "Chapter 1 > Section 1.2 > Subsection 1.2.3",
    chapter: 1,
    section: "1.2"
  },
  
  // Entity Characteristics
  entity_confidence: 0.92,
  mention_count: 8,
  canonical_form: "Foreign National Documentation Requirements",
  aliases: ["FN Documentation", "International Borrower Docs", "Non-US Citizen Requirements"],
  
  // Semantic Properties
  semantic_category: "BORROWER_REQUIREMENT",
  business_domain: "UNDERWRITING",
  regulatory_context: ["BSA", "AML", "PATRIOT_ACT"],
  
  // Decision Context (if applicable)
  decision_metadata: {
    is_decision_entity: true,
    decision_type: "BRANCH",
    evaluation_precedence: 15,
    logical_expression: "IF borrower_citizenship != 'US' THEN additional_docs_required",
    dependencies: ["borrower_citizenship", "visa_status"],
    affects_outcomes: ["APPROVE", "ADDITIONAL_DOCS"]
  },
  
  // Matrix Context (if applicable)
  matrix_metadata: {
    appears_in_matrices: ["qualification_matrix", "documentation_matrix"],
    matrix_coordinates: [
      {matrix_id: "matrix_001", row: "Foreign National", column: "Documentation"},
      {matrix_id: "matrix_002", row: "Non-US", column: "Required Docs"}
    ]
  }
})

// Mortgage-Specific Entity Specializations
(:LoanProgram:Entity {
  enhanced_entity_id: "ent_nqm_titanium_program",
  program_name: "NQM Titanium Advantage",
  program_code: "NQM-TIT-ADV",
  
  // Program Characteristics
  loan_category: "NON_QM",
  investor_guidelines: true,
  max_loan_amount: 3000000,
  min_fico_score: 620,
  max_ltv_ratio: 0.85,
  max_dti_ratio: 0.50,
  
  // Geographic Restrictions
  eligible_states: ["CA", "FL", "TX", "NY", "WA"],
  excluded_areas: ["flood_zones", "declining_markets"],
  
  // Product Features
  features: ["foreign_nationals", "bank_statements", "asset_depletion"],
  restrictions: ["no_prepay_penalty", "full_documentation"],
  
  // Compliance
  regulatory_compliance: ["regulation_z", "tila_respa", "safe_act"],
  audit_requirements: ["monthly_reporting", "quarterly_review"]
})

(:NumericThreshold:Entity {
  enhanced_entity_id: "ent_fico_threshold_620",
  threshold_type: "MINIMUM_FICO_SCORE",
  numeric_value: 620,
  
  // Threshold Context
  applies_to: ["primary_borrower", "co_borrower"],
  exceptions: ["compensating_factors", "manual_underwriting"],
  override_authority: "Senior_Underwriter",
  
  // Business Rules
  enforcement_level: "HARD_STOP",
  exception_frequency: 0.12,
  business_justification: "Risk management policy requires minimum credit standards",
  
  // Related Thresholds
  related_thresholds: [
    {type: "DTI_RATIO", value: 0.43, relationship: "COMBINED_WITH"},
    {type: "LTV_RATIO", value: 0.80, relationship: "AFFECTS"}
  ]
})
```

### Layer 4: Decision Layer

#### Decision Flow Nodes

```cypher
// Decision Flow Nodes
(:DecisionFlow {
  flow_id: "df_nqm_qualification",
  flow_name: "NQM Qualification Decision Flow",
  document_package_id: "pkg_nqm_titanium_v2_1_0",
  
  // Flow Characteristics
  entry_points: ["borrower_eligibility", "property_eligibility", "loan_eligibility"],
  exit_points: ["approved", "declined", "refer_manual", "additional_docs"],
  total_decision_nodes: 23,
  average_path_length: 4.7,
  
  // Flow Metadata
  business_process: "LOAN_QUALIFICATION",
  automation_level: 0.78,
  manual_review_frequency: 0.22,
  
  // Performance Metrics
  average_processing_time_minutes: 12.5,
  automation_accuracy: 0.94,
  manual_review_override_rate: 0.08
})

// Individual Decision Nodes
(:DecisionNode {
  decision_node_id: "dn_fico_evaluation_001",
  enhanced_node_id: "NQM_titanium_ch1_s2_ss1",
  decision_type: "BRANCH",
  
  // Decision Logic
  decision_name: "FICO Score Evaluation",
  logical_expression: "primary_borrower.fico_score >= 620 AND co_borrower.fico_score >= 620",
  evaluation_precedence: 5,
  
  // Decision Outcomes
  true_outcome: "proceed_to_ltv_check",
  false_outcome: "check_compensating_factors",
  exception_outcome: "manual_underwriting",
  
  // Business Context
  business_rule_id: "BR_FICO_001",
  regulatory_basis: "Internal Risk Policy",
  last_reviewed: date("2024-06-15"),
  review_frequency: "QUARTERLY",
  
  // Performance Data
  execution_frequency: 0.95,
  true_rate: 0.87,
  false_rate: 0.13,
  exception_rate: 0.02,
  
  // Dependencies
  input_requirements: ["credit_report", "tri_merge_report"],
  data_dependencies: ["borrower.fico_score", "co_borrower.fico_score"],
  prerequisite_decisions: ["borrower_count_determination"],
  
  // Matrix Connections
  matrix_references: [
    {matrix_id: "matrix_001", coordinates: {fico: "620-679", ltv: "*"}},
    {matrix_id: "matrix_002", coordinates: {credit_tier: "Tier_2"}}
  ]
})

// Outcome Nodes (LEAF nodes)
(:DecisionOutcome {
  outcome_id: "outcome_approved_standard",
  outcome_type: "APPROVED",
  outcome_name: "Standard Approval",
  
  // Outcome Details
  approval_level: "AUTOMATED",
  conditions: ["standard_documentation", "standard_pricing"],
  restrictions: ["no_prepayment_penalty", "standard_terms"],
  
  // Processing Instructions
  next_steps: ["generate_approval_letter", "order_appraisal", "process_application"],
  required_documents: ["purchase_contract", "insurance_binder", "title_commitment"],
  estimated_closing_days: 21,
  
  // Business Metrics
  frequency: 0.67,
  average_loan_amount: 485000,
  average_interest_rate: 0.0675,
  profit_margin: 0.0245
})
```

### Layer 5: Business Layer

#### Business Rule and Policy Nodes

```cypher
// Business Policy Nodes
(:BusinessPolicy {
  policy_id: "bp_nqm_foreign_national_policy",
  policy_name: "Foreign National Lending Policy",
  policy_version: "3.2",
  
  // Policy Scope
  applies_to: ["NQM", "RTL"],
  geographic_scope: ["US", "US_Territories"],
  borrower_scope: ["foreign_nationals", "visa_holders"],
  
  // Policy Details
  policy_statement: "Foreign national borrowers require enhanced documentation and verification procedures",
  effective_date: date("2024-01-01"),
  review_date: date("2024-12-31"),
  
  // Implementation
  implementation_level: "MANDATORY",
  exception_process: "SVP_APPROVAL_REQUIRED",
  compliance_monitoring: "MONTHLY_AUDIT",
  
  // Related Regulations
  regulatory_basis: ["BSA", "AML", "OFAC"],
  internal_policies: ["risk_management", "compliance", "underwriting"],
  
  // Impact Analysis
  affected_loan_volume: 0.15,
  additional_processing_time: 5.2,
  compliance_cost_per_loan: 847.50
})

// Compliance Nodes
(:ComplianceRule {
  rule_id: "cr_bsa_foreign_national",
  rule_name: "BSA Foreign National Verification",
  regulation: "BANK_SECRECY_ACT",
  
  // Rule Definition
  rule_text: "Verify identity and source of funds for foreign national borrowers",
  implementation_requirement: "MANDATORY",
  violation_severity: "HIGH",
  
  // Monitoring
  monitoring_frequency: "EVERY_TRANSACTION",
  audit_requirements: ["documentation_review", "process_validation"],
  
  // Penalties
  violation_penalties: ["regulatory_fine", "license_suspension", "consent_order"],
  historical_violations: 0,
  
  // Implementation in System
  system_controls: ["automated_checks", "manual_reviews", "exception_reporting"],
  implementation_effectiveness: 0.98
})

// Performance Tracking Nodes
(:PerformanceMetric {
  metric_id: "pm_nqm_approval_rate",
  metric_name: "NQM Approval Rate",
  metric_type: "PERCENTAGE",
  
  // Current Performance
  current_value: 0.74,
  target_value: 0.78,
  trend: "STABLE",
  
  // Historical Data
  monthly_values: [0.72, 0.73, 0.74, 0.75, 0.74],
  year_over_year_change: 0.02,
  
  // Business Impact
  revenue_impact: "HIGH",
  operational_impact: "MEDIUM",
  compliance_impact: "LOW",
  
  // Monitoring
  update_frequency: "DAILY",
  alert_thresholds: {
    warning: 0.70,
    critical: 0.65
  }
})
```

## Relationship Schema

### Cross-Layer Relationships

```cypher
// Layer 1 to Layer 2 Relationships
(:DocumentPackage)-[:CONTAINS]->(:Document)
(:Document)-[:HAS_NAVIGATION]->(:NavigationNode)
(:Document)-[:CHUNKED_INTO]->(:HierarchicalChunk)
(:NavigationNode)-[:CONTAINS_CHUNK]->(:HierarchicalChunk)
(:NavigationNode)-[:HAS_DECISION_TREE]->(:DecisionTree)

// Layer 2 to Layer 3 Relationships
(:NavigationNode)-[:CONTAINS_ENTITY]->(:Entity)
(:HierarchicalChunk)-[:MENTIONS]->(:Entity)
(:DecisionTree)-[:IMPLEMENTS]->(:Entity {entity_type: "BUSINESS_RULE"})

// Layer 3 to Layer 4 Relationships
(:Entity)-[:PARTICIPATES_IN]->(:DecisionFlow)
(:Entity)-[:EVALUATED_BY]->(:DecisionNode)
(:DecisionNode)-[:REFERENCES_ENTITY]->(:Entity)
(:DecisionNode)-[:LEADS_TO]->(:DecisionOutcome)

// Layer 4 to Layer 5 Relationships
(:DecisionFlow)-[:IMPLEMENTS]->(:BusinessPolicy)
(:DecisionNode)-[:ENFORCES]->(:ComplianceRule)
(:DecisionOutcome)-[:AFFECTS]->(:PerformanceMetric)
(:BusinessPolicy)-[:MONITORED_BY]->(:PerformanceMetric)

// Matrix Integration Relationships
(:MatrixDocument)-[:CLASSIFIED_AS]->(:MatrixClassification)
(:MatrixCell)-[:REFERENCES]->(:NavigationNode)
(:MatrixCell)-[:ELABORATED_BY]->(:HierarchicalChunk)
(:MatrixCell)-[:IMPLEMENTS]->(:DecisionNode)
(:MatrixDimension)-[:MAPS_TO]->(:Entity)
(:MatrixRange)-[:DEFINES_THRESHOLD]->(:NumericThreshold)

// Cross-Document Relationships
(:Entity)-[:SAME_AS]->(:Entity) // Entity resolution across documents
(:NavigationNode)-[:REFERENCES]->(:NavigationNode) // Cross-document references
(:DecisionNode)-[:DEPENDS_ON]->(:DecisionNode) // Decision dependencies
(:BusinessPolicy)-[:SUPERSEDES]->(:BusinessPolicy) // Policy evolution

// Temporal Relationships
(:Document)-[:VERSION_OF]->(:Document)
(:BusinessPolicy)-[:PREVIOUS_VERSION]->(:BusinessPolicy)
(:DecisionNode)-[:HISTORICAL_VERSION]->(:DecisionNode)
```

### Specialized Relationship Types

```cypher
// Hierarchical Relationships
(:NavigationNode)-[:PARENT_OF {depth: 1}]->(:NavigationNode)
(:NavigationNode)-[:CHILD_OF {depth: 1}]->(:NavigationNode)
(:NavigationNode)-[:ANCESTOR_OF {depth: n}]->(:NavigationNode)
(:NavigationNode)-[:DESCENDANT_OF {depth: n}]->(:NavigationNode)
(:NavigationNode)-[:SIBLING_OF]->(:NavigationNode)

// Sequential Relationships
(:NavigationNode)-[:FOLLOWS {sequence: n}]->(:NavigationNode)
(:NavigationNode)-[:PRECEDES {sequence: n}]->(:NavigationNode)
(:HierarchicalChunk)-[:NEXT_CHUNK]->(:HierarchicalChunk)
(:HierarchicalChunk)-[:PREVIOUS_CHUNK]->(:HierarchicalChunk)

// Decision Flow Relationships
(:DecisionNode)-[:ROOT_OF_TREE]->(:DecisionTree)
(:DecisionNode)-[:BRANCH_OF_TREE]->(:DecisionTree)
(:DecisionOutcome)-[:LEAF_OF_TREE]->(:DecisionTree)
(:DecisionNode)-[:IF_TRUE]->(:DecisionNode)
(:DecisionNode)-[:IF_FALSE]->(:DecisionNode)
(:DecisionNode)-[:IF_EXCEPTION]->(:DecisionNode)

// Entity Relationships
(:Entity)-[:RELATED_TO {strength: float, type: string}]->(:Entity)
(:Entity)-[:SYNONYM_OF]->(:Entity)
(:Entity)-[:HYPERNYM_OF]->(:Entity) // More general concept
(:Entity)-[:HYPONYM_OF]->(:Entity) // More specific concept
(:Entity)-[:MERONYM_OF]->(:Entity) // Part of relationship
(:Entity)-[:HOLONYM_OF]->(:Entity) // Has part relationship

// Conflict and Validation Relationships
(:MatrixCell)-[:CONFLICTS_WITH {severity: string}]->(:NavigationNode)
(:Entity)-[:CONTRADICTS {confidence: float}]->(:Entity)
(:DecisionNode)-[:INCONSISTENT_WITH]->(:DecisionNode)
(:BusinessPolicy)-[:CONFLICTS_WITH]->(:ComplianceRule)

// Semantic Relationships
(:Entity)-[:SEMANTICALLY_SIMILAR {score: float}]->(:Entity)
(:HierarchicalChunk)-[:TOPICALLY_RELATED {score: float}]->(:HierarchicalChunk)
(:NavigationNode)-[:CONCEPTUALLY_LINKED]->(:NavigationNode)
```

## Graph Indexes and Constraints

### Performance Indexes

```cypher
// Core Node Indexes
CREATE INDEX enhanced_node_id_index FOR (n:NavigationNode) ON (n.enhanced_node_id);
CREATE INDEX enhanced_entity_id_index FOR (e:Entity) ON (e.enhanced_entity_id);
CREATE INDEX package_id_index FOR (p:DocumentPackage) ON (p.package_id);
CREATE INDEX document_id_index FOR (d:Document) ON (d.document_id);
CREATE INDEX chunk_id_index FOR (c:HierarchicalChunk) ON (c.chunk_id);

// Hierarchy Indexes
CREATE INDEX navigation_hierarchy_index FOR (n:NavigationNode) ON (n.chapter_number, n.section_number, n.subsection_number);
CREATE INDEX depth_level_index FOR (n:NavigationNode) ON (n.depth_level);

// Decision Flow Indexes
CREATE INDEX decision_node_type_index FOR (dn:DecisionNode) ON (dn.decision_type);
CREATE INDEX decision_precedence_index FOR (dn:DecisionNode) ON (dn.evaluation_precedence);
CREATE INDEX outcome_type_index FOR (do:DecisionOutcome) ON (do.outcome_type);

// Entity Type Indexes
CREATE INDEX entity_type_index FOR (e:Entity) ON (e.entity_type);
CREATE INDEX entity_category_index FOR (e:Entity) ON (e.semantic_category);
CREATE INDEX entity_confidence_index FOR (e:Entity) ON (e.entity_confidence);

// Matrix Indexes
CREATE INDEX matrix_classification_index FOR (m:MatrixDocument) ON (m.matrix_classification.primary_type);
CREATE INDEX matrix_dimensions_index FOR (m:MatrixDocument) ON (m.dimensions);

// Temporal Indexes
CREATE INDEX document_timestamp_index FOR (d:Document) ON (d.upload_timestamp);
CREATE INDEX policy_effective_date_index FOR (bp:BusinessPolicy) ON (bp.effective_date);

// Full-text Search Indexes
CREATE FULLTEXT INDEX entity_search_index FOR (e:Entity) ON EACH [e.primary_mention, e.canonical_form, e.aliases];
CREATE FULLTEXT INDEX navigation_search_index FOR (n:NavigationNode) ON EACH [n.title, n.raw_summary];
CREATE FULLTEXT INDEX chunk_content_index FOR (c:HierarchicalChunk) ON EACH [c.content];
```

### Data Integrity Constraints

```cypher
// Uniqueness Constraints
CREATE CONSTRAINT package_id_unique FOR (p:DocumentPackage) REQUIRE p.package_id IS UNIQUE;
CREATE CONSTRAINT document_id_unique FOR (d:Document) REQUIRE d.document_id IS UNIQUE;
CREATE CONSTRAINT enhanced_node_id_unique FOR (n:NavigationNode) REQUIRE n.enhanced_node_id IS UNIQUE;
CREATE CONSTRAINT enhanced_entity_id_unique FOR (e:Entity) REQUIRE e.enhanced_entity_id IS UNIQUE;
CREATE CONSTRAINT chunk_id_unique FOR (c:HierarchicalChunk) REQUIRE c.chunk_id IS UNIQUE;
CREATE CONSTRAINT decision_node_id_unique FOR (dn:DecisionNode) REQUIRE dn.decision_node_id IS UNIQUE;

// Existence Constraints (Neo4j Enterprise)
CREATE CONSTRAINT package_name_exists FOR (p:DocumentPackage) REQUIRE p.package_name IS NOT NULL;
CREATE CONSTRAINT document_type_exists FOR (d:Document) REQUIRE d.document_type IS NOT NULL;
CREATE CONSTRAINT navigation_node_type_exists FOR (n:NavigationNode) REQUIRE n.node_type IS NOT NULL;
CREATE CONSTRAINT entity_type_exists FOR (e:Entity) REQUIRE e.entity_type IS NOT NULL;

// Property Type Constraints
CREATE CONSTRAINT package_version_format FOR (p:DocumentPackage) REQUIRE p.version IS :: STRING;
CREATE CONSTRAINT document_file_size_positive FOR (d:Document) REQUIRE d.file_size_mb >= 0;
CREATE CONSTRAINT navigation_depth_positive FOR (n:NavigationNode) REQUIRE n.depth_level >= 1;
CREATE CONSTRAINT entity_confidence_range FOR (e:Entity) REQUIRE e.entity_confidence >= 0 AND e.entity_confidence <= 1;
```

## Query Optimization Patterns

### Common Query Patterns

```cypher
// 1. Package-Centric Navigation
MATCH (pkg:DocumentPackage {package_id: $packageId})-[:CONTAINS]->(doc:Document)
      -[:HAS_NAVIGATION]->(nav:NavigationNode)
WHERE nav.depth_level <= 3
RETURN nav.title, nav.navigation_path, nav.chapter_number, nav.section_number
ORDER BY nav.absolute_position;

// 2. Entity Discovery Across Documents
MATCH (pkg:DocumentPackage {category: $category})-[:CONTAINS]->(doc:Document)
      -[:CONTAINS_ENTITY]->(entity:Entity {entity_type: $entityType})
RETURN entity.canonical_form, entity.entity_confidence, 
       collect(doc.document_type) as document_types,
       count(doc) as document_count
ORDER BY entity.entity_confidence DESC;

// 3. Decision Path Traversal
MATCH path = (root:DecisionNode {decision_type: "ROOT"})-[:IF_TRUE|IF_FALSE*]->(leaf:DecisionOutcome)
WHERE root.enhanced_node_id STARTS WITH $nodePrefix
RETURN path, leaf.outcome_type, length(path) as path_length
ORDER BY path_length;

// 4. Matrix-Guidelines Relationship Discovery
MATCH (matrix:MatrixDocument)-[:CONTAINS_CELL]->(cell:MatrixCell)
      -[:REFERENCES]->(nav:NavigationNode)-[:CONTAINS_CHUNK]->(chunk:HierarchicalChunk)
WHERE matrix.document_id = $matrixDocId
RETURN cell.coordinates, cell.value, nav.title, chunk.content
ORDER BY cell.row_index, cell.column_index;

// 5. Cross-Document Consistency Checking
MATCH (e1:Entity)-[:SAME_AS]->(e2:Entity)
WHERE e1.enhanced_entity_id <> e2.enhanced_entity_id
  AND e1.primary_mention = e2.primary_mention
WITH e1, e2, 
     [(e1)<-[:CONTAINS_ENTITY]-(doc1) | doc1.document_type] as doc1_types,
     [(e2)<-[:CONTAINS_ENTITY]-(doc2) | doc2.document_type] as doc2_types
RETURN e1.canonical_form, doc1_types, doc2_types,
       CASE WHEN size(doc1_types) > size(doc2_types) THEN e1 ELSE e2 END as primary_entity;
```

### Performance Monitoring Queries

```cypher
// Graph Size and Growth Monitoring
MATCH (n) 
RETURN labels(n)[0] as node_type, count(n) as count
ORDER BY count DESC;

// Relationship Distribution
MATCH ()-[r]->() 
RETURN type(r) as relationship_type, count(r) as count
ORDER BY count DESC;

// Decision Tree Completeness Validation
MATCH (dt:DecisionTree)
OPTIONAL MATCH (dt)-[:ROOT_OF_TREE]->(root:DecisionNode)
OPTIONAL MATCH (dt)-[:BRANCH_OF_TREE]->(branch:DecisionNode)
OPTIONAL MATCH (dt)-[:LEAF_OF_TREE]->(leaf:DecisionOutcome)
RETURN dt.tree_name, 
       count(DISTINCT root) as root_count,
       count(DISTINCT branch) as branch_count,
       count(DISTINCT leaf) as leaf_count,
       CASE WHEN count(DISTINCT root) = 1 AND count(DISTINCT leaf) >= 3 
            THEN "COMPLETE" ELSE "INCOMPLETE" END as completeness_status;
```

## Data Migration and Evolution

### Schema Version Management

```cypher
// Schema Version Tracking
(:SchemaVersion {
  version: "3.0.0",
  migration_date: datetime(),
  changes: [
    "Added BusinessPolicy layer",
    "Enhanced decision flow relationships", 
    "Added matrix integration relationships"
  ],
  compatibility: {
    backward_compatible: true,
    forward_compatible: false,
    migration_required: false
  }
})

// Migration Scripts for Schema Evolution
CALL apoc.periodic.iterate(
  "MATCH (old:Entity) WHERE old.enhanced_entity_id IS NULL",
  "SET old.enhanced_entity_id = 'ent_' + old.temp_entity_id + '_migrated'",
  {batchSize: 1000, parallel: false}
);
```

### Data Quality Assurance

```cypher
// Orphaned Node Detection
MATCH (n) 
WHERE NOT ()-[]-(n) AND NOT n:DocumentPackage
RETURN labels(n), count(n) as orphaned_count;

// Relationship Integrity Validation
MATCH (n:NavigationNode)-[r:PARENT_OF]->(child:NavigationNode)
WHERE NOT (child)-[:CHILD_OF]->(n)
RETURN n.enhanced_node_id, child.enhanced_node_id, "Missing reverse relationship";

// Decision Tree Completeness Audit
MATCH (dt:DecisionTree)
WHERE NOT (dt)-[:LEAF_OF_TREE]->(:DecisionOutcome {outcome_type: "APPROVE"})
   OR NOT (dt)-[:LEAF_OF_TREE]->(:DecisionOutcome {outcome_type: "DECLINE"})
RETURN dt.tree_name, "Missing mandatory outcomes";
```

## Integration Points

### API Query Interfaces

The multi-layer schema supports various API query patterns:

1. **Package-Based Queries**: Retrieve all information for a document package
2. **Navigation-Based Queries**: Follow document structure and hierarchy
3. **Entity-Centric Queries**: Find entities and their relationships across documents
4. **Decision-Flow Queries**: Trace decision paths and outcomes
5. **Matrix-Integration Queries**: Link matrix cells to guideline content
6. **Cross-Document Queries**: Find relationships between different documents
7. **Temporal Queries**: Track changes and evolution over time

### Performance Characteristics

- **Node Count**: Expected 10K-100K nodes per package
- **Relationship Count**: Expected 50K-500K relationships per package
- **Query Performance**: <100ms for most common patterns
- **Index Coverage**: >95% of queries use indexes
- **Memory Requirements**: 4-8GB for typical enterprise deployment

## Next Steps

The Multi-Layer Knowledge Graph Schema provides the foundation for:

1. **Advanced Query Capabilities**: Complex cross-document analysis
2. **Intelligent Recommendations**: Context-aware suggestions
3. **Consistency Validation**: Automated conflict detection
4. **Performance Optimization**: Efficient data retrieval patterns
5. **Evolution Support**: Schema versioning and migration capabilities

This schema will be extended in Phase 3.2 with hybrid retrieval capabilities that leverage the multi-layer structure for sophisticated query processing and intelligent information discovery.