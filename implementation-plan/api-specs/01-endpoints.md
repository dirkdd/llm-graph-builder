# API Specifications: Endpoints

## Overview
This document defines all API endpoints for the enhanced LLM Graph Builder system, including document package management, hierarchical processing, matrix classification, knowledge graph operations, and production features.

## API Architecture

### Base URL Structure
```
Production: https://api.llm-graph-builder.com/api/v3
Staging: https://staging-api.llm-graph-builder.com/api/v3
Development: http://localhost:8000/api/v3
```

### Authentication
- **Type**: Bearer Token (JWT)
- **Header**: `Authorization: Bearer <token>`
- **Token Expiry**: 24 hours
- **Refresh**: Available through `/auth/refresh` endpoint

### Standard Response Format
```json
{
  "success": boolean,
  "data": object | array | null,
  "error": string | null,
  "message": string | null,
  "metadata": {
    "timestamp": "2024-01-15T10:30:00Z",
    "request_id": "req_123456789",
    "version": "3.0.0",
    "processing_time_ms": 150
  }
}
```

## Phase 1: Document Package APIs

### Package Management

#### Create Document Package
```http
POST /api/v3/packages
Content-Type: application/json
Authorization: Bearer <token>

{
  "package_name": "NQM Titanium Advantage",
  "category": "NQM",
  "template": "NQM_STANDARD",
  "tenant_id": "the_g1_group",
  "documents": [
    {
      "document_type": "guidelines",
      "expected_sections": [
        "Borrower Eligibility",
        "Income Documentation",
        "Asset Requirements"
      ],
      "processing_config": {
        "chunking_strategy": "hierarchical",
        "entity_extraction": true,
        "decision_tree_extraction": true
      }
    }
  ],
  "customizations": {
    "additional_sections": ["Foreign National Requirements"],
    "matrix_types": ["foreign_national_matrix"]
  }
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "package_id": "pkg_nqm_titanium_v1_0_0",
    "package_name": "NQM Titanium Advantage",
    "version": "1.0.0",
    "status": "DRAFT",
    "created_at": "2024-01-15T10:30:00Z",
    "documents": [...],
    "validation_results": {
      "is_valid": true,
      "issues": []
    }
  }
}
```

#### Get Package Details
```http
GET /api/v3/packages/{package_id}
Authorization: Bearer <token>
```

#### List Packages
```http
GET /api/v3/packages?category=NQM&status=ACTIVE&limit=20&offset=0
Authorization: Bearer <token>
```

#### Update Package
```http
PUT /api/v3/packages/{package_id}
Content-Type: application/json
Authorization: Bearer <token>

{
  "updates": {
    "package_name": "NQM Titanium Advantage Plus",
    "documents": [...],
    "version_type": "MINOR"
  },
  "changelog": "Added new foreign national requirements section"
}
```

#### Clone Package
```http
POST /api/v3/packages/{package_id}/clone
Content-Type: application/json
Authorization: Bearer <token>

{
  "new_name": "NQM Platinum Advantage",
  "modifications": [
    {
      "type": "add_section",
      "section": "DSCR Analysis",
      "document_type": "guidelines"
    }
  ]
}
```

#### Apply Package to Documents
```http
POST /api/v3/packages/{package_id}/apply
Content-Type: multipart/form-data
Authorization: Bearer <token>

files: [file1.pdf, file2.pdf]
document_mappings: {
  "file1.pdf": "guidelines",
  "file2.pdf": "matrix"
}
options: {
  "update_in_place": true,
  "validate_structure": true,
  "auto_map_sections": true
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "task_id": "task_123456",
    "status": "PROCESSING",
    "applied_documents": [
      {
        "file_name": "file1.pdf",
        "document_id": "doc_123",
        "document_type": "guidelines",
        "processing_status": "QUEUED"
      }
    ],
    "estimated_completion": "2024-01-15T10:35:00Z"
  }
}
```

### Package Version Management

#### Get Package History
```http
GET /api/v3/packages/{package_id}/history
Authorization: Bearer <token>
```

#### Rollback Package Version
```http
POST /api/v3/packages/{package_id}/rollback
Content-Type: application/json
Authorization: Bearer <token>

{
  "target_version": "2.1.0",
  "reason": "Critical bug in version 2.2.0"
}
```

#### Compare Package Versions
```http
GET /api/v3/packages/{package_id}/compare?from=2.1.0&to=2.2.0
Authorization: Bearer <token>
```

## Phase 2: Matrix Processing APIs

### Matrix Classification

#### Classify Matrix
```http
POST /api/v3/matrices/classify
Content-Type: multipart/form-data
Authorization: Bearer <token>

file: matrix.pdf
context: {
  "document_type": "qualification_matrix",
  "expected_dimensions": ["fico_score", "ltv_ratio", "dti_ratio"]
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "matrix_id": "matrix_123",
    "classification": {
      "detected_types": [
        {
          "type_name": "multi_dimensional_decision",
          "confidence": 0.92,
          "characteristics": ["3_dimensions", "decision_outcomes"]
        },
        {
          "type_name": "risk_segmentation", 
          "confidence": 0.78,
          "characteristics": ["risk_tiers", "graduated_terms"]
        }
      ],
      "primary_type": "multi_dimensional_decision",
      "complexity_score": 0.87,
      "processing_strategy": "dimension_analysis"
    },
    "dimensions": [
      {
        "name": "fico_score",
        "data_type": "numeric",
        "range": [580, 850],
        "values": [580, 620, 660, 700, 740, 780, 820]
      }
    ]
  }
}
```

#### Get Matrix Classification Results
```http
GET /api/v3/matrices/{matrix_id}/classification
Authorization: Bearer <token>
```

#### Update Matrix Classification
```http
PUT /api/v3/matrices/{matrix_id}/classification
Content-Type: application/json
Authorization: Bearer <token>

{
  "corrections": {
    "primary_type": "business_rules_engine",
    "additional_dimensions": ["property_type"]
  },
  "user_feedback": "Matrix also contains property type rules"
}
```

### Range Extraction

#### Extract Matrix Ranges
```http
POST /api/v3/matrices/{matrix_id}/extract-ranges
Authorization: Bearer <token>
```

#### Validate Extracted Ranges
```http
POST /api/v3/matrices/{matrix_id}/validate-ranges
Content-Type: application/json
Authorization: Bearer <token>

{
  "range_corrections": [
    {
      "dimension": "fico_score",
      "corrected_values": [580, 620, 660, 700, 740, 780, 820],
      "notes": "Added missing 820 threshold"
    }
  ]
}
```

### Cross-Document Relationships

#### Discover Relationships
```http
POST /api/v3/documents/discover-relationships
Content-Type: application/json
Authorization: Bearer <token>

{
  "document_ids": ["doc_123", "doc_456", "doc_789"],
  "relationship_types": ["REFERENCES", "ELABORATES", "CONFLICTS"],
  "confidence_threshold": 0.75
}
```

#### Validate Relationships
```http
POST /api/v3/relationships/validate
Content-Type: application/json
Authorization: Bearer <token>

{
  "relationship_ids": ["rel_123", "rel_456"],
  "validation_context": {
    "check_consistency": true,
    "detect_conflicts": true
  }
}
```

#### Get Consistency Report
```http
GET /api/v3/packages/{package_id}/consistency-report
Authorization: Bearer <token>
```

## Phase 3: Knowledge Graph APIs

### Multi-Layer Graph Operations

#### Build Knowledge Graph
```http
POST /api/v3/knowledge-graph/build
Content-Type: application/json
Authorization: Bearer <token>

{
  "package_id": "pkg_nqm_titanium_v1_0_0",
  "documents": ["doc_123", "doc_456"],
  "layers": ["document", "structure", "entity", "decision", "business"],
  "processing_options": {
    "parallel_processing": true,
    "quality_validation": true,
    "relationship_discovery": true
  }
}
```

#### Query Knowledge Graph
```http
POST /api/v3/knowledge-graph/query
Content-Type: application/json
Authorization: Bearer <token>

{
  "query": "What are the FICO requirements for foreign national borrowers?",
  "retrieval_modes": ["vector_similarity", "graph_traversal", "decision_path"],
  "context": {
    "package_id": "pkg_nqm_titanium_v1_0_0",
    "user_role": "underwriter",
    "max_results": 10
  },
  "filters": {
    "document_types": ["guidelines", "matrix"],
    "sections": ["borrower_eligibility"],
    "confidence_threshold": 0.8
  }
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "query": "What are the FICO requirements for foreign national borrowers?",
    "results": [
      {
        "content": "Foreign national borrowers require minimum FICO score of 720...",
        "source": {
          "document_id": "doc_123",
          "section": "Foreign National Requirements",
          "page": 15
        },
        "relevance_score": 0.94,
        "retrieval_mode": "vector_similarity"
      }
    ],
    "retrieval_summary": {
      "modes_used": ["vector_similarity", "graph_traversal"],
      "total_results": 8,
      "average_confidence": 0.87,
      "processing_time_ms": 145
    }
  }
}
```

### Hybrid Retrieval

#### Analyze Query Intent
```http
POST /api/v3/query/analyze
Content-Type: application/json
Authorization: Bearer <token>

{
  "query": "Can a borrower with 680 FICO and 85% LTV qualify for NQM?",
  "context": {
    "package_id": "pkg_nqm_titanium_v1_0_0",
    "conversation_history": []
  }
}
```

#### Get Retrieval Recommendations
```http
GET /api/v3/query/retrieval-recommendations?query={encoded_query}&package_id={package_id}
Authorization: Bearer <token>
```

### Graph Visualization

#### Get Graph Structure
```http
GET /api/v3/knowledge-graph/{package_id}/structure?layers=entity,decision&limit=100
Authorization: Bearer <token>
```

#### Get Node Details
```http
GET /api/v3/knowledge-graph/nodes/{node_id}
Authorization: Bearer <token>
```

#### Get Relationship Details
```http
GET /api/v3/knowledge-graph/relationships/{relationship_id}
Authorization: Bearer <token>
```

## Phase 4: Production Feature APIs

### Webhook Management

#### Register Webhook
```http
POST /api/v3/webhooks
Content-Type: application/json
Authorization: Bearer <token>

{
  "url": "https://client-system.com/webhooks/graph-updates",
  "events": [
    "document.processed",
    "package.updated",
    "quality.alert"
  ],
  "secret": "webhook_secret_key",
  "retry_config": {
    "max_retries": 3,
    "backoff_strategy": "exponential"
  },
  "filters": {
    "package_ids": ["pkg_nqm_titanium_v1_0_0"],
    "severity_levels": ["HIGH", "CRITICAL"]
  }
}
```

#### List Webhooks
```http
GET /api/v3/webhooks?status=active&limit=20
Authorization: Bearer <token>
```

#### Update Webhook
```http
PUT /api/v3/webhooks/{webhook_id}
Content-Type: application/json
Authorization: Bearer <token>

{
  "events": ["document.processed", "quality.alert"],
  "active": true
}
```

#### Delete Webhook
```http
DELETE /api/v3/webhooks/{webhook_id}
Authorization: Bearer <token>
```

#### Get Webhook Delivery Logs
```http
GET /api/v3/webhooks/{webhook_id}/deliveries?start_date=2024-01-01&end_date=2024-01-15
Authorization: Bearer <token>
```

### Export Management

#### Create Export Job
```http
POST /api/v3/exports
Content-Type: application/json
Authorization: Bearer <token>

{
  "export_type": "knowledge_graph",
  "format": "json",
  "scope": {
    "package_ids": ["pkg_nqm_titanium_v1_0_0"],
    "layers": ["entity", "decision"],
    "include_relationships": true
  },
  "delivery": {
    "method": "download",
    "notification_email": "user@company.com"
  }
}
```

#### Get Export Status
```http
GET /api/v3/exports/{export_id}
Authorization: Bearer <token>
```

#### Download Export
```http
GET /api/v3/exports/{export_id}/download
Authorization: Bearer <token>
```

#### List Exports
```http
GET /api/v3/exports?status=completed&limit=20
Authorization: Bearer <token>
```

### AI Enhancement

#### Trigger Quality Analysis
```http
POST /api/v3/ai/quality-analysis
Content-Type: application/json
Authorization: Bearer <token>

{
  "scope": {
    "package_ids": ["pkg_nqm_titanium_v1_0_0"],
    "analysis_types": ["completeness", "consistency", "accuracy"]
  },
  "auto_correct": true
}
```

#### Get AI Recommendations
```http
GET /api/v3/ai/recommendations?package_id={package_id}&type=quality
Authorization: Bearer <token>
```

#### Get Predictive Analytics
```http
POST /api/v3/ai/predict
Content-Type: application/json
Authorization: Bearer <token>

{
  "prediction_type": "loan_outcome",
  "inputs": {
    "fico_score": 720,
    "ltv_ratio": 80,
    "dti_ratio": 38,
    "property_type": "SFR"
  },
  "package_context": "pkg_nqm_titanium_v1_0_0"
}
```

### Monitoring and Analytics

#### Get System Health
```http
GET /api/v3/system/health
Authorization: Bearer <token>
```

#### Get Performance Metrics
```http
GET /api/v3/analytics/performance?period=24h&metrics=response_time,throughput,error_rate
Authorization: Bearer <token>
```

#### Get Quality Metrics
```http
GET /api/v3/analytics/quality?package_id={package_id}&period=7d
Authorization: Bearer <token>
```

#### Get Usage Analytics
```http
GET /api/v3/analytics/usage?tenant_id={tenant_id}&start_date=2024-01-01&end_date=2024-01-15
Authorization: Bearer <token>
```

### Audit and Compliance

#### Get Audit Trail
```http
GET /api/v3/audit/trail?entity_type=package&entity_id={package_id}&start_date=2024-01-01
Authorization: Bearer <token>
```

#### Generate Compliance Report
```http
POST /api/v3/compliance/report
Content-Type: application/json
Authorization: Bearer <token>

{
  "report_type": "processing_compliance",
  "period": {
    "start_date": "2024-01-01",
    "end_date": "2024-01-31"
  },
  "scope": {
    "tenant_ids": ["the_g1_group"],
    "package_ids": ["pkg_nqm_titanium_v1_0_0"]
  }
}
```

## Error Handling

### Standard Error Codes
- `400` - Bad Request (Invalid input)
- `401` - Unauthorized (Invalid or missing token)
- `403` - Forbidden (Insufficient permissions)
- `404` - Not Found (Resource doesn't exist)
- `409` - Conflict (Resource already exists)
- `422` - Unprocessable Entity (Validation failed)
- `429` - Too Many Requests (Rate limited)
- `500` - Internal Server Error
- `503` - Service Unavailable

### Error Response Format
```json
{
  "success": false,
  "error": "VALIDATION_FAILED",
  "message": "Package validation failed: missing required documents",
  "details": {
    "validation_errors": [
      {
        "field": "documents",
        "error": "Guidelines document is required for NQM packages"
      }
    ]
  },
  "metadata": {
    "timestamp": "2024-01-15T10:30:00Z",
    "request_id": "req_123456789"
  }
}
```

## Rate Limiting

### Standard Limits
- **Authentication**: 100 requests/hour per IP
- **Package Operations**: 1000 requests/hour per user
- **Query Operations**: 10,000 requests/hour per user
- **Webhook Delivery**: 10,000 events/hour per endpoint
- **Export Operations**: 100 requests/day per user

### Rate Limit Headers
```http
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 999
X-RateLimit-Reset: 1642248000
X-RateLimit-Window: 3600
```

## Pagination

### Standard Pagination
```http
GET /api/v3/packages?limit=20&offset=40&sort=created_at&order=desc
```

### Pagination Response
```json
{
  "success": true,
  "data": [...],
  "pagination": {
    "total": 156,
    "limit": 20,
    "offset": 40,
    "has_next": true,
    "has_previous": true,
    "next_offset": 60,
    "previous_offset": 20
  }
}
```