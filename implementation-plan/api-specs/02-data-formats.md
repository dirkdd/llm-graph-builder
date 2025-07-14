# API Specifications: Data Formats

## Overview
This document defines the comprehensive data formats, schemas, and message structures used throughout the enhanced LLM Graph Builder API system.

## Core Data Type Definitions

### Basic Types
```typescript
type UUID = string;  // Format: "xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx"
type Timestamp = string;  // ISO 8601 format: "2024-01-15T10:30:00.000Z"
type Confidence = number;  // Range: 0.0 to 1.0
type Percentage = number;  // Range: 0.0 to 100.0
type Version = string;  // Semantic versioning: "1.2.3"
type EntityID = string;  // Format: "{prefix}_{random_string}"
```

## Document Package Data Formats

### DocumentPackage
```json
{
  "package_id": "pkg_nqm_titanium_v2_1_0",
  "package_name": "NQM Titanium Advantage Package",
  "tenant_id": "the_g1_group",
  "category": "NQM",
  "version": "2.1.0",
  "status": "ACTIVE",
  "created_at": "2024-01-15T10:30:00.000Z",
  "updated_at": "2024-01-15T15:45:00.000Z",
  "created_by": "user_12345",
  "template_type": "NQM_STANDARD",
  "documents": [
    {
      "document_id": "doc_guidelines_001",
      "document_type": "guidelines",
      "document_name": "NQM Guidelines v10",
      "expected_structure": {
        "chapters": ["Borrower Eligibility", "Income Documentation"],
        "sections_per_chapter": 5,
        "estimated_pages": 45
      },
      "required_sections": [
        "Borrower Eligibility",
        "Income Documentation", 
        "Asset Requirements"
      ],
      "optional_sections": [
        "Foreign National Requirements",
        "ITIN Borrower Guidelines"
      ],
      "processing_config": {
        "chunking_strategy": "hierarchical",
        "entity_extraction": true,
        "decision_tree_extraction": true,
        "quality_threshold": 0.85
      }
    }
  ],
  "relationships": [
    {
      "relationship_id": "rel_001",
      "relationship_type": "ELABORATES",
      "source_document": "doc_guidelines_001",
      "source_section": "Borrower Eligibility",
      "target_document": "doc_matrix_001",
      "target_section": "Qualification Matrix",
      "confidence": 0.92
    }
  ],
  "metadata": {
    "complexity_score": 0.87,
    "completeness_score": 0.95,
    "quality_score": 0.91,
    "processing_time_estimate_minutes": 45,
    "last_quality_check": "2024-01-15T14:20:00.000Z"
  }
}
```

### PackageTemplate
```json
{
  "template_id": "tmpl_nqm_standard",
  "template_name": "NQM Standard Template",
  "category": "NQM",
  "version": "1.0.0",
  "documents": [
    {
      "document_type": "guidelines",
      "required": true,
      "expected_sections": [
        "Borrower Eligibility",
        "Income Documentation",
        "Asset Requirements",
        "Property Standards",
        "Credit Analysis"
      ],
      "decision_trees": [
        "eligibility_decision_tree",
        "documentation_decision_tree",
        "property_decision_tree"
      ],
      "minimum_quality_score": 0.90
    },
    {
      "document_type": "matrix",
      "required": true,
      "matrix_types": [
        "qualification_matrix",
        "pricing_matrix",
        "ltv_matrix"
      ],
      "expected_dimensions": ["fico_score", "ltv_ratio", "dti_ratio"],
      "minimum_classification_confidence": 0.85
    }
  ],
  "validation_rules": [
    {
      "rule_id": "req_guidelines_matrix_consistency",
      "rule_name": "Guidelines Matrix Consistency",
      "description": "Guidelines FICO requirements must match matrix FICO ranges",
      "severity": "HIGH",
      "auto_correctable": false
    }
  ]
}
```

## Document Processing Data Formats

### NavigationStructure
```json
{
  "structure_id": "nav_doc_123",
  "document_id": "doc_guidelines_001",
  "extraction_method": "llm_hierarchical",
  "extraction_confidence": 0.94,
  "hierarchy": {
    "chapters": [
      {
        "chapter_id": "chap_001",
        "chapter_number": 1,
        "title": "Borrower Eligibility",
        "page_start": 1,
        "page_end": 15,
        "sections": [
          {
            "section_id": "sec_001_001",
            "section_number": "1.1",
            "title": "General Eligibility Requirements",
            "page_start": 1,
            "page_end": 5,
            "subsections": [
              {
                "subsection_id": "subsec_001_001_001",
                "subsection_number": "1.1.1",
                "title": "Age Requirements",
                "page_start": 1,
                "page_end": 2,
                "content_summary": "Borrower must be at least 18 years old",
                "decision_nodes": ["dn_age_requirement"]
              }
            ]
          }
        ]
      }
    ]
  },
  "decision_trees": [
    {
      "tree_id": "dt_eligibility_001",
      "tree_name": "Primary Eligibility Decision Tree",
      "tree_type": "borrower_eligibility",
      "root_node": "dn_primary_eligibility",
      "total_nodes": 12,
      "complete_paths": 8,
      "validation_status": "COMPLETE"
    }
  ],
  "quality_metrics": {
    "section_detection_accuracy": 0.96,
    "hierarchy_accuracy": 0.94,
    "title_extraction_accuracy": 0.98,
    "decision_tree_completeness": 1.0
  }
}
```

### DecisionTree
```json
{
  "tree_id": "dt_eligibility_001",
  "document_id": "doc_guidelines_001",
  "tree_name": "Primary Eligibility Decision Tree",
  "tree_type": "borrower_eligibility",
  "extraction_confidence": 0.93,
  "nodes": [
    {
      "node_id": "dn_primary_eligibility",
      "node_type": "ROOT",
      "title": "Primary Eligibility Assessment",
      "description": "Initial eligibility determination for NQM loans",
      "conditions": [],
      "parent_nodes": [],
      "child_nodes": ["dn_age_check", "dn_citizenship_check"],
      "depth_level": 0,
      "section_reference": "1.1 General Eligibility Requirements",
      "page_reference": 1
    },
    {
      "node_id": "dn_age_check",
      "node_type": "BRANCH",
      "title": "Age Verification",
      "description": "Verify borrower meets minimum age requirement",
      "conditions": [
        {
          "condition_type": "numeric_comparison",
          "field": "borrower_age",
          "operator": ">=",
          "value": 18,
          "unit": "years"
        }
      ],
      "parent_nodes": ["dn_primary_eligibility"],
      "child_nodes": ["dn_age_approved", "dn_age_declined"],
      "depth_level": 1,
      "section_reference": "1.1.1 Age Requirements",
      "page_reference": 1
    },
    {
      "node_id": "dn_age_approved",
      "node_type": "LEAF",
      "title": "Age Requirement Met",
      "description": "Borrower meets minimum age requirement",
      "outcome_type": "CONTINUE",
      "conditions": [],
      "parent_nodes": ["dn_age_check"],
      "child_nodes": [],
      "depth_level": 2,
      "section_reference": "1.1.1 Age Requirements",
      "page_reference": 1
    }
  ],
  "paths": [
    {
      "path_id": "path_001",
      "path_description": "Age requirement approval path",
      "node_sequence": ["dn_primary_eligibility", "dn_age_check", "dn_age_approved"],
      "final_outcome": "CONTINUE",
      "path_probability": 0.95
    }
  ],
  "validation": {
    "is_complete": true,
    "missing_paths": [],
    "orphaned_nodes": [],
    "validation_issues": []
  }
}
```

## Matrix Classification Data Formats

### MatrixClassification
```json
{
  "matrix_id": "matrix_qualification_001",
  "document_id": "doc_matrix_001",
  "classification_timestamp": "2024-01-15T10:30:00.000Z",
  "detected_types": [
    {
      "type_name": "multi_dimensional_decision_matrix",
      "confidence": 0.92,
      "characteristics": [
        "three_dimensional_input",
        "binary_decision_output",
        "threshold_based_logic"
      ],
      "processing_strategy": "dimensional_analysis"
    },
    {
      "type_name": "risk_based_segmentation_matrix",
      "confidence": 0.78,
      "characteristics": [
        "risk_tier_stratification",
        "graduated_terms",
        "credit_score_based"
      ],
      "processing_strategy": "segmentation_analysis"
    }
  ],
  "primary_type": "multi_dimensional_decision_matrix",
  "complexity_score": 0.87,
  "dimensions": [
    {
      "dimension_id": "dim_fico_score",
      "dimension_name": "FICO Score",
      "data_type": "numeric",
      "range": {
        "min_value": 580,
        "max_value": 850,
        "step_size": 20
      },
      "extracted_values": [580, 600, 620, 640, 660, 680, 700, 720, 740, 760, 780, 800, 820],
      "validation_status": "VALIDATED"
    },
    {
      "dimension_id": "dim_ltv_ratio",
      "dimension_name": "LTV Ratio",
      "data_type": "percentage",
      "range": {
        "min_value": 60,
        "max_value": 90,
        "step_size": 5
      },
      "extracted_values": [60, 65, 70, 75, 80, 85, 90],
      "validation_status": "VALIDATED"
    }
  ],
  "lookup_table": {
    "table_id": "lt_qualification_001",
    "rows": 13,
    "columns": 7,
    "cells": [
      {
        "coordinates": {"fico_score": 720, "ltv_ratio": 80},
        "value": "APPROVED",
        "confidence": 0.95,
        "source_text": "720+ FICO, 80% LTV: Approved"
      }
    ]
  }
}
```

### RangeExtraction
```json
{
  "extraction_id": "range_ext_001",
  "matrix_id": "matrix_qualification_001",
  "dimension_name": "fico_score",
  "extraction_method": "pattern_recognition",
  "extraction_confidence": 0.91,
  "raw_extractions": [
    {
      "source_text": "FICO 580-619: Declined",
      "extracted_value": {"min": 580, "max": 619},
      "confidence": 0.95
    },
    {
      "source_text": "FICO 620+: Conditional approval",
      "extracted_value": {"min": 620, "max": null},
      "confidence": 0.88
    }
  ],
  "normalized_ranges": [
    {
      "range_start": 580,
      "range_end": 619,
      "range_type": "inclusive",
      "associated_outcome": "DECLINED"
    },
    {
      "range_start": 620,
      "range_end": 850,
      "range_type": "inclusive",
      "associated_outcome": "CONDITIONAL"
    }
  ],
  "validation_results": {
    "is_consistent": true,
    "coverage_percentage": 100.0,
    "gaps": [],
    "overlaps": [],
    "validation_notes": "Complete coverage with no gaps or overlaps"
  }
}
```

## Knowledge Graph Data Formats

### MultiLayerGraph
```json
{
  "graph_id": "kg_pkg_nqm_titanium_v2_1_0",
  "package_id": "pkg_nqm_titanium_v2_1_0",
  "creation_timestamp": "2024-01-15T10:30:00.000Z",
  "layers": [
    {
      "layer_id": "layer_1_document",
      "layer_name": "Document Layer",
      "layer_type": "document",
      "node_count": 3,
      "relationship_count": 2,
      "nodes": [
        {
          "node_id": "doc_guidelines_001",
          "node_type": "Document",
          "properties": {
            "document_type": "guidelines",
            "file_name": "NQM_Guidelines_v10.pdf",
            "page_count": 45,
            "processing_status": "COMPLETED",
            "quality_score": 0.91
          }
        }
      ]
    },
    {
      "layer_id": "layer_3_entity",
      "layer_name": "Entity Layer", 
      "layer_type": "entity",
      "node_count": 127,
      "relationship_count": 89,
      "entity_types": {
        "BORROWER_CRITERIA": 23,
        "DOCUMENTATION_REQUIREMENT": 18,
        "QUALIFICATION_THRESHOLD": 15,
        "PROPERTY_REQUIREMENT": 12,
        "BUSINESS_RULE": 59
      }
    }
  ],
  "inter_layer_relationships": [
    {
      "relationship_id": "ilr_001",
      "relationship_type": "EXTRACTED_FROM",
      "source_layer": "entity",
      "source_node": "entity_fico_requirement_001",
      "target_layer": "document",
      "target_node": "doc_guidelines_001",
      "confidence": 0.94
    }
  ],
  "graph_statistics": {
    "total_nodes": 234,
    "total_relationships": 156,
    "average_node_degree": 1.33,
    "graph_density": 0.003,
    "largest_component_size": 198
  }
}
```

### QueryRequest
```json
{
  "query_id": "query_12345",
  "query": "What are the FICO requirements for foreign national borrowers with investment properties?",
  "query_timestamp": "2024-01-15T10:30:00.000Z",
  "retrieval_modes": [
    "vector_similarity",
    "graph_traversal", 
    "decision_path"
  ],
  "context": {
    "package_id": "pkg_nqm_titanium_v2_1_0",
    "user_id": "user_12345",
    "user_role": "underwriter",
    "session_id": "session_67890",
    "conversation_history": [
      {
        "query": "What documents are required for foreign nationals?",
        "timestamp": "2024-01-15T10:25:00.000Z"
      }
    ]
  },
  "filters": {
    "document_types": ["guidelines", "matrix"],
    "sections": ["borrower_eligibility", "foreign_national_requirements"],
    "entity_types": ["QUALIFICATION_THRESHOLD", "BORROWER_CRITERIA"],
    "confidence_threshold": 0.8,
    "max_results": 10,
    "include_source_references": true
  },
  "options": {
    "explain_reasoning": true,
    "include_alternative_paths": true,
    "highlight_conflicts": true,
    "provide_recommendations": true
  }
}
```

### QueryResponse
```json
{
  "query_id": "query_12345",
  "query": "What are the FICO requirements for foreign national borrowers with investment properties?",
  "response_timestamp": "2024-01-15T10:30:15.234Z",
  "processing_time_ms": 234,
  "results": [
    {
      "result_id": "result_001",
      "content": "Foreign national borrowers purchasing investment properties require a minimum FICO score of 740, which is 20 points higher than the standard 720 requirement for owner-occupied properties.",
      "relevance_score": 0.94,
      "confidence_score": 0.91,
      "retrieval_mode": "vector_similarity",
      "source": {
        "document_id": "doc_guidelines_001",
        "document_type": "guidelines",
        "section": "Foreign National Requirements",
        "subsection": "Investment Property Criteria",
        "page_number": 23,
        "chunk_id": "chunk_guidelines_023_002"
      },
      "supporting_evidence": [
        {
          "evidence_type": "matrix_reference",
          "matrix_id": "matrix_foreign_national_001",
          "cell_coordinates": {"borrower_type": "foreign_national", "property_type": "investment"},
          "cell_value": "740"
        }
      ]
    }
  ],
  "retrieval_summary": {
    "modes_executed": [
      {
        "mode": "vector_similarity",
        "results_count": 5,
        "average_relevance": 0.87,
        "execution_time_ms": 89
      },
      {
        "mode": "graph_traversal",
        "results_count": 3,
        "average_relevance": 0.92,
        "execution_time_ms": 145
      }
    ],
    "total_results": 8,
    "merged_results": 5,
    "average_confidence": 0.89
  },
  "reasoning_explanation": {
    "query_classification": {
      "intent": "qualification_inquiry",
      "complexity": "moderate",
      "specificity": "high",
      "entities_identified": ["foreign_national", "investment_property", "fico_score"]
    },
    "retrieval_strategy": {
      "primary_mode": "vector_similarity",
      "secondary_modes": ["graph_traversal"],
      "mode_selection_reason": "High specificity query with clear entity references"
    },
    "result_ranking": {
      "ranking_factors": ["relevance_score", "confidence_score", "source_authority"],
      "ranking_explanation": "Results ranked by semantic similarity to query with confidence weighting"
    }
  },
  "alternative_paths": [
    {
      "path_description": "Standard foreign national requirements (non-investment)",
      "result": "720 FICO minimum for owner-occupied properties",
      "relevance_note": "Lower requirement for different property type"
    }
  ],
  "recommendations": [
    {
      "recommendation_type": "follow_up_query",
      "suggestion": "Ask about down payment requirements for foreign national investment properties",
      "reasoning": "FICO requirements often paired with higher down payment requirements"
    }
  ]
}
```

## Webhook Data Formats

### WebhookEvent
```json
{
  "event_id": "event_123456",
  "event_type": "document.processed",
  "event_timestamp": "2024-01-15T10:30:00.000Z",
  "tenant_id": "the_g1_group",
  "source": "llm_graph_builder",
  "version": "3.0.0",
  "data": {
    "document_id": "doc_guidelines_001",
    "package_id": "pkg_nqm_titanium_v2_1_0",
    "processing_status": "COMPLETED",
    "quality_score": 0.91,
    "processing_time_seconds": 145,
    "extracted_entities": 23,
    "extracted_relationships": 15,
    "decision_trees_count": 3
  },
  "metadata": {
    "processing_node": "worker_node_03",
    "processing_batch": "batch_20240115_001",
    "quality_flags": [],
    "performance_metrics": {
      "cpu_time_seconds": 89,
      "memory_peak_mb": 512,
      "storage_used_mb": 45
    }
  }
}
```

### WebhookRegistration
```json
{
  "webhook_id": "webhook_123456",
  "tenant_id": "the_g1_group",
  "url": "https://client-system.com/webhooks/graph-updates",
  "signing_secret": "whsec_abcdef123456",
  "status": "ACTIVE",
  "created_at": "2024-01-15T10:30:00.000Z",
  "events": [
    "document.processed",
    "package.updated",
    "quality.alert",
    "relationship.discovered"
  ],
  "filters": {
    "package_ids": ["pkg_nqm_titanium_v2_1_0"],
    "document_types": ["guidelines", "matrix"],
    "severity_levels": ["HIGH", "CRITICAL"],
    "quality_threshold": 0.8
  },
  "retry_config": {
    "max_retries": 3,
    "backoff_strategy": "exponential",
    "retry_intervals": [30, 90, 270],
    "timeout_seconds": 30
  },
  "rate_limit": {
    "events_per_minute": 100,
    "burst_capacity": 200
  },
  "delivery_stats": {
    "total_deliveries": 1247,
    "successful_deliveries": 1239,
    "failed_deliveries": 8,
    "average_response_time_ms": 145,
    "success_rate_percentage": 99.36
  }
}
```

## Export Data Formats

### ExportJob
```json
{
  "export_id": "export_123456",
  "export_type": "knowledge_graph",
  "status": "COMPLETED",
  "created_at": "2024-01-15T10:30:00.000Z",
  "completed_at": "2024-01-15T10:45:23.456Z",
  "created_by": "user_12345",
  "tenant_id": "the_g1_group",
  "format": "json",
  "compression": "gzip",
  "scope": {
    "package_ids": ["pkg_nqm_titanium_v2_1_0"],
    "layers": ["entity", "decision", "business"],
    "include_relationships": true,
    "include_metadata": true,
    "date_range": {
      "start_date": "2024-01-01T00:00:00.000Z",
      "end_date": "2024-01-15T23:59:59.999Z"
    }
  },
  "output": {
    "file_size_bytes": 2458934,
    "file_count": 1,
    "download_url": "https://exports.llm-graph-builder.com/downloads/export_123456.json.gz",
    "download_expires_at": "2024-01-22T10:45:23.456Z",
    "checksum_sha256": "a1b2c3d4e5f6..."
  },
  "statistics": {
    "total_nodes": 234,
    "total_relationships": 156,
    "entities_exported": 127,
    "decisions_exported": 45,
    "business_rules_exported": 62
  }
}
```

## Quality Metrics Data Formats

### QualityReport
```json
{
  "report_id": "quality_report_123456",
  "report_type": "weekly_quality_summary",
  "period": {
    "start_date": "2024-01-08T00:00:00.000Z",
    "end_date": "2024-01-14T23:59:59.999Z"
  },
  "tenant_id": "the_g1_group",
  "generated_at": "2024-01-15T10:30:00.000Z",
  "overall_scores": {
    "extraction_quality": 0.91,
    "relationship_accuracy": 0.87,
    "decision_tree_completeness": 0.95,
    "system_performance": 0.88,
    "user_satisfaction": 4.2
  },
  "detailed_metrics": {
    "navigation_extraction": {
      "accuracy_percentage": 95.2,
      "documents_processed": 47,
      "avg_confidence": 0.91,
      "issues_detected": 3
    },
    "entity_extraction": {
      "completeness_percentage": 89.7,
      "entities_extracted": 1247,
      "avg_confidence": 0.87,
      "precision": 0.93,
      "recall": 0.86
    },
    "decision_trees": {
      "completeness_percentage": 95.0,
      "trees_processed": 15,
      "complete_paths": 127,
      "incomplete_paths": 3,
      "orphaned_nodes": 1
    }
  },
  "trends": {
    "week_over_week_change": {
      "extraction_quality": +0.02,
      "relationship_accuracy": -0.01,
      "decision_tree_completeness": +0.03
    },
    "improvement_areas": [
      "Relationship discovery precision",
      "Matrix classification confidence"
    ]
  },
  "recommendations": [
    {
      "priority": "HIGH",
      "area": "relationship_discovery",
      "recommendation": "Improve cross-document reference detection algorithms",
      "expected_impact": "5-8% accuracy improvement"
    }
  ]
}
```

## Validation Schemas

### JSON Schema Examples
```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "DocumentPackage",
  "type": "object",
  "required": ["package_id", "package_name", "tenant_id", "category"],
  "properties": {
    "package_id": {
      "type": "string",
      "pattern": "^pkg_[a-z0-9_]+$"
    },
    "package_name": {
      "type": "string",
      "minLength": 1,
      "maxLength": 100
    },
    "category": {
      "type": "string",
      "enum": ["NQM", "RTL", "SBC", "CONV"]
    },
    "version": {
      "type": "string",
      "pattern": "^\\d+\\.\\d+\\.\\d+$"
    },
    "status": {
      "type": "string",
      "enum": ["DRAFT", "ACTIVE", "ARCHIVED"]
    }
  }
}
```

## Content-Type Headers

### Request Content Types
- `application/json` - Standard JSON requests
- `multipart/form-data` - File uploads with metadata
- `application/x-www-form-urlencoded` - Form submissions
- `text/plain` - Raw text content

### Response Content Types
- `application/json` - Standard API responses
- `application/octet-stream` - Binary file downloads
- `text/csv` - CSV exports
- `application/zip` - Compressed exports
- `application/pdf` - PDF reports