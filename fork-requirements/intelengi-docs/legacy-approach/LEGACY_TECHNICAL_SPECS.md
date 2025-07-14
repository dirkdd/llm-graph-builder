# MGMS v2.0 Legacy Technical Specifications

## System Architecture Overview

### Production Environment
- **Platform**: n8n Cloud (25-node limitation)
- **AI Provider**: Anthropic Claude Sonnet 4
- **Graph Database**: Neo4j AuraDB (Query API v2)
- **Vector Database**: Qdrant (planned for Stage 3)
- **Metadata Storage**: PostgreSQL 15+

### Processing Pipeline
```
Document Input → Category Validation → Stage 1 (Extraction) → Quality Gates → Stage 2 (Graph Construction) → Neo4j Deployment
```

## Stage 1: Document Extraction Pipeline

### Anthropic Batch API Configuration
```json
{
  "model": "claude-sonnet-4-20250514",
  "max_tokens": 64000,
  "temperature": 0.0,
  "system": "[PROMPT_CONTENT]",
  "messages": [{"role": "user", "content": "..."}]
}
```

### Custom ID Pattern
- **Format**: `{stage}_{type}_{sequential}`
- **Examples**: `1A_nav_01`, `1B_ent_02`
- **Constraints**: Max 64 characters, pattern `^[a-zA-Z0-9_-]{1,64}$`
- **Optimization**: 73% reduction from original length

### Parallel Processing Architecture
```
Input Document
├── Stage 1A: Navigation Extraction (Parallel)
└── Stage 1B: Entity Discovery (Parallel)
    └── Quality Gate Validation
        └── Stage 2 Handoff
```

### Document Type Processing

#### Guidelines Documents
- **Input**: PDF text extraction of mortgage policy documents
- **Processing**: Traditional hierarchical navigation (CHAPTER → SECTION → SUBSECTION)
- **Output**: MGMS v2.0 Navigation + Entity Extraction Schemas

#### Matrix Documents  
- **Input**: PDF text extraction of qualification matrices
- **Processing**: Tabular structure recognition (MATRIX_HEADER → MATRIX_SECTION → MATRIX_ROW → MATRIX_CELL)
- **Output**: MGMS v2.0 Matrix variants with decision tree elements

### Quality Gate Requirements
- **Schema Validation**: 95%+ success rate
- **Decision Tree Completeness**: 100% ROOT→BRANCH→LEAF coverage
- **Performance**: <3 minutes per document
- **Error Rate**: <5% failure threshold

## Stage 2: Graph Construction Pipeline

### Neo4j Transaction Batch Format
```json
{
  "stage": "2A_navigation_graph",
  "schema_version": "2.0",
  "outputs": {
    "neo4j_transaction_batches": [
      {
        "transaction_id": "nav_batch_1",
        "statements": [
          {
            "statement": "CREATE (n:NavigationNode {id: $id, title: $title})",
            "parameters": {"id": "nav_001", "title": "..."}
          }
        ]
      }
    ]
  }
}
```

### Multi-Tenant Node ID Generation
```javascript
// Legacy Pattern
const nodeId = `${tenant}_${category}_${product}_nav_${sequence}`;
// Example: "the_g1_group_NQM_naa_nav_001"

// Collision Protection
const hierarchicalId = {
  tenant_code: tenant.replace(/[^a-zA-Z0-9]/g, '_').toLowerCase(),
  category_code: category, // NQM, SBC, RTL
  product_code: product.replace(/[^a-zA-Z0-9]/g, '_').toLowerCase()
};
```

### Graph Schema Design

#### Node Types
- **Navigation Nodes**: CHAPTER, SECTION, SUBSECTION, MATRIX_HEADER, MATRIX_SECTION
- **Entity Nodes**: LOAN_PROGRAM, BORROWER_TYPE, REQUIREMENT, NUMERIC_THRESHOLD
- **Decision Tree Nodes**: ROOT, BRANCH, LEAF, TERMINAL, GATEWAY

#### Relationship Types
- **Structural**: CONTAINS_SECTION, CONTAINS_SUBSECTION, MATRIX_CONTAINS
- **Semantic**: DEFINES_REQUIREMENT, HAS_THRESHOLD, APPLIES_TO
- **Decision Flow**: DECISION_LEADS_TO, IF_TRUE, IF_FALSE, EXCEPTION_FOR

### Property Serialization
```javascript
// Complex objects must be serialized as JSON strings
const nodeProperties = {
  id: nodeId,
  title: title,
  attributes: JSON.stringify(complexAttributes), // CRITICAL
  decision_metadata: JSON.stringify(decisionData) // CRITICAL
};
```

## Decision Tree Framework (Core Legacy Pattern)

### Mandatory Structure
```
ROOT (evaluation_precedence: 1-5)
├── BRANCH (evaluation_precedence: 6-89)
│   ├── LEAF (evaluation_precedence: 90-99, action: APPROVE)
│   ├── LEAF (evaluation_precedence: 90-99, action: DECLINE)
│   └── TERMINAL (evaluation_precedence: 90-99, action: REFER)
```

### Decision Metadata Structure
```json
{
  "decision_tree_metadata": {
    "contains_decision_logic": true,
    "decision_type": "LEAF",
    "evaluation_precedence": 98,
    "logical_expression": "fico_qualified AND ltv_acceptable",
    "decision_outcomes": ["APPROVE"],
    "default_outcome": {
      "action": "APPROVE",
      "message": "Loan approved - criteria satisfied"
    },
    "dependencies": ["fico_evaluation", "ltv_assessment"],
    "exception_rules": [
      {
        "trigger": "Compensating factors present",
        "override_authority": "Senior Underwriter"
      }
    ]
  }
}
```

### Quality Requirements
- **Minimum LEAF Nodes**: 6 per document (2 per ROOT minimum)
- **Required Actions**: APPROVE, DECLINE, REFER outcomes mandatory
- **Completeness**: Every ROOT must connect to LEAF nodes through BRANCH nodes
- **Precedence Rules**: LEAF nodes must have evaluation_precedence 90-99

## Multi-Tenant Architecture

### Category Isolation
```javascript
// Three mortgage categories with strict isolation
const categories = {
  NQM: "Non-Qualified Mortgages",
  SBC: "Standard Bank Credit", 
  RTL: "Retail Lending"
};

// Hierarchical namespace per category
const namespacePattern = `{tenant}_{category}_{product}_*`;
```

### Collision Prevention
- **Tenant-Level**: Organization isolation (`the_g1_group`, `wells_fargo`)
- **Category-Level**: Product type isolation (`NQM`, `SBC`, `RTL`)
- **Product-Level**: Specific program isolation (`naa`, `platinum_advantage`)
- **Sequential**: Ordered node creation within scope

### Data Flow Isolation
```
Input Processing → Category Validation → Isolated Processing Streams
├── NQM Documents → NQM Namespace → NQM Graph Partition
├── SBC Documents → SBC Namespace → SBC Graph Partition  
└── RTL Documents → RTL Namespace → RTL Graph Partition
```

## Performance Optimization Patterns

### Anthropic Batch API Optimization
```javascript
// Batch request optimization
const batchRequests = documents.map((doc, index) => ({
  custom_id: `1A_nav_${String(index + 1).padStart(2, '0')}`,
  params: {
    model: "claude-sonnet-4-20250514",
    max_tokens: 64000,
    temperature: 0.0,
    system: extractionPrompt,
    messages: [{ role: "user", content: JSON.stringify(doc) }]
  }
}));
```

### Neo4j Transaction Batching
```javascript
// Bulk transaction optimization
const transactionBatch = {
  statements: nodes.map(node => ({
    statement: "CREATE (n:Node {id: $id, properties: $props})",
    parameters: {
      id: node.id,
      props: JSON.stringify(node.properties) // Serialization required
    }
  }))
};
```

### Processing Time Targets
- **Stage 1A Navigation**: <90 seconds per document
- **Stage 1B Entity**: <90 seconds per document  
- **Stage 2A Graph**: <300 seconds per document
- **Stage 2B Entity Graph**: <300 seconds per document
- **Total Pipeline**: <600 seconds (10 minutes) per document

## Error Handling and Recovery

### Quality Gate Failures
```javascript
// Stage 1 → Stage 2 quality gate
if (extractionResults.decision_tree_ready !== true) {
  throw new Error('Incomplete decision trees - Stage 2 blocked');
}

if (extractionResults.validation_score < 0.95) {
  throw new Error('Quality threshold not met - manual review required');
}
```

### API Error Recovery
```javascript
// Anthropic Batch API retry logic
const retryConfig = {
  maxRetries: 3,
  backoffMultiplier: 2,
  initialDelay: 1000,
  maxDelay: 10000
};

// Neo4j transaction retry
const transactionRetry = {
  maxAttempts: 5,
  retryableErrors: ['TransientError', 'ServiceUnavailable']
};
```

### Graceful Degradation
- **Partial Success**: Process successful extractions, queue failures for retry
- **Schema Validation**: Repair minor JSON issues automatically
- **Timeout Handling**: Split large documents into smaller chunks
- **Resource Limits**: Queue overflow documents for later processing

## Schema Compliance Requirements

### MGMS v2.0 Navigation Extraction Schema
```json
{
  "stage": "1A_navigation_extraction",
  "schema_version": "2.0",
  "outputs": {
    "document_metadata": { /* required */ },
    "navigation_nodes": [ /* array required */ ],
    "navigation_relationships": [ /* array required */ ],
    "document_structure": { /* required */ }
  }
}
```

### MGMS v2.0 Entity Extraction Schema  
```json
{
  "stage": "1B_entity_discovery", 
  "schema_version": "2.0",
  "outputs": {
    "document_metadata": { /* required */ },
    "discovered_entities": [ /* array required */ ],
    "entity_relationships": [ /* array required */ ],
    "entity_statistics": { /* required */ }
  }
}
```

### Neo4j Transaction Schema
```json
{
  "stage": "2A_navigation_graph",
  "schema_version": "2.0", 
  "outputs": {
    "neo4j_transaction_batches": [
      {
        "transaction_id": "string",
        "statements": [
          {
            "statement": "CYPHER_QUERY",
            "parameters": { /* object */ }
          }
        ]
      }
    ]
  }
}
```

## Token Usage Optimization

### Prompt Engineering Efficiency
- **Stage 1 Prompts**: ~8,000 tokens average
- **Document Input**: 10,000-50,000 tokens typical
- **Output Generation**: 5,000-15,000 tokens
- **Total per Request**: 64,000 token limit utilized efficiently

### Batch Processing Economics
- **Sequential Processing**: 100 requests × 64k tokens = 6.4M tokens
- **Batch Processing**: 1 batch request = 6.4M tokens (same cost, better latency)
- **Optimization**: 73% reduction in API calls through batching

## Validation and Testing

### Automated Quality Checks
```javascript
// Decision tree validation
const validateDecisionTree = (nodes) => {
  const rootNodes = nodes.filter(n => n.decision_type === 'ROOT');
  const leafNodes = nodes.filter(n => n.decision_type === 'LEAF');
  
  return {
    hasRootNodes: rootNodes.length >= 1,
    hasMinimumLeafNodes: leafNodes.length >= 6,
    allLeafNodesHaveActions: leafNodes.every(n => 
      ['APPROVE', 'DECLINE', 'REFER'].includes(n.default_outcome?.action)
    )
  };
};
```

### Performance Benchmarks
```javascript
// Processing time validation
const performanceChecks = {
  stage1MaxTime: 180000, // 3 minutes
  stage2MaxTime: 600000, // 10 minutes
  totalPipelineMaxTime: 780000, // 13 minutes
  qualityScoreMinimum: 0.95 // 95%
};
```

### Production Monitoring
- **Success Rate Tracking**: Daily validation score averages
- **Performance Metrics**: Processing time percentiles
- **Error Pattern Analysis**: Common failure categorization
- **Quality Drift Detection**: Schema compliance degradation alerts

---

## Legacy Implementation Notes

### What This Documentation Provides
- ✅ Complete technical specifications from production implementation
- ✅ Proven patterns that achieved 95%+ accuracy
- ✅ Performance optimizations that worked at scale
- ✅ Multi-tenant architecture that prevented data leakage
- ✅ Quality frameworks that ensured production readiness

### What This Documentation Does NOT Constrain
- ❌ Choice of AI models or providers
- ❌ Architectural patterns or processing stages
- ❌ Database technologies or graph structures
- ❌ Deployment platforms or orchestration tools
- ❌ Output formats or schema designs

**Use these specifications as proven context, not as implementation requirements.**