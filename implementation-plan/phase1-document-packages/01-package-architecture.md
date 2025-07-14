# Phase 1.1: Document Package Architecture

## Overview
The Document Package Architecture introduces a revolutionary approach to mortgage document management, allowing organizations to create, save, and reuse document structures. This system enables updating documents in place while maintaining their relationships and hierarchical structure.

## Core Concepts

### Document Package Definition
A **Document Package** is a reusable template that defines:
- Document structure and hierarchy
- Relationships between documents
- Processing rules and configurations
- Version control and update mechanisms

### Package Components

```python
class DocumentPackage:
    """Core document package structure"""
    package_id: str  # Unique identifier (e.g., "pkg_nqm_titanium_v2")
    package_name: str  # Human-readable name
    tenant_id: str  # Organization identifier
    category: str  # Mortgage category (NQM, RTL, SBC, CONV)
    version: str  # Semantic versioning (e.g., "2.1.0")
    
    # Package Structure
    documents: List[DocumentDefinition]
    relationships: List[PackageRelationship]
    processing_rules: ProcessingConfiguration
    
    # Metadata
    created_at: datetime
    updated_at: datetime
    created_by: str
    status: str  # DRAFT, ACTIVE, ARCHIVED
    
    # Template Configuration
    template_mappings: Dict[str, TemplateMapping]
    validation_rules: List[ValidationRule]
```

### Document Definition Structure

```python
class DocumentDefinition:
    """Individual document within a package"""
    document_id: str  # Package-scoped ID
    document_type: str  # guidelines, matrix, rate_sheet
    document_name: str  # Display name
    
    # Structure Definition
    expected_structure: NavigationStructure
    required_sections: List[str]
    optional_sections: List[str]
    
    # Processing Configuration
    chunking_strategy: str  # hierarchical, semantic, hybrid
    entity_types: List[str]  # Expected entity types
    matrix_configuration: MatrixConfig  # If matrix type
    
    # Validation
    validation_schema: Dict
    quality_thresholds: QualityMetrics
```

## Implementation Architecture

### 1. Package Manager (`package_manager.py`)

```python
class PackageManager:
    """Manages document package lifecycle"""
    
    def create_package(self, package_config: PackageConfig) -> DocumentPackage:
        """Create a new document package"""
        # Generate unique package ID
        # Initialize package structure
        # Set up version control
        # Create in database
        
    def load_package(self, package_id: str) -> DocumentPackage:
        """Load existing package for use"""
        # Retrieve from database
        # Validate package integrity
        # Load relationships
        # Return hydrated package
        
    def update_package(self, package_id: str, updates: PackageUpdate) -> DocumentPackage:
        """Update package in place"""
        # Validate update compatibility
        # Apply structural changes
        # Update version
        # Maintain document relationships
        
    def clone_package(self, package_id: str, new_name: str) -> DocumentPackage:
        """Create a copy of existing package"""
        # Deep copy structure
        # Generate new IDs
        # Preserve relationships
        # Return new package
```

### 2. Package Templates (`package_templates.py`)

```python
class MortgagePackageTemplates:
    """Pre-defined templates for mortgage categories"""
    
    NQM_TEMPLATE = {
        "category": "NQM",
        "documents": [
            {
                "type": "guidelines",
                "expected_sections": [
                    "Borrower Eligibility",
                    "Income Documentation",
                    "Asset Requirements",
                    "Property Standards",
                    "Credit Analysis"
                ],
                "decision_trees": ["eligibility", "documentation", "property"]
            },
            {
                "type": "matrix",
                "matrix_types": ["qualification", "pricing", "ltv_matrix"],
                "dimensions": ["fico_score", "ltv_ratio", "dti_ratio"]
            }
        ],
        "relationships": [
            {
                "from": "guidelines.eligibility",
                "to": "matrix.qualification",
                "type": "ELABORATES"
            }
        ]
    }
    
    RTL_TEMPLATE = {
        "category": "RTL",
        "documents": [
            {
                "type": "guidelines",
                "expected_sections": [
                    "Rehab Requirements",
                    "Draw Schedule",
                    "Inspection Process",
                    "Completion Standards"
                ]
            },
            {
                "type": "matrix",
                "matrix_types": ["rehab_cost", "arv_matrix"],
                "dimensions": ["property_value", "rehab_percentage"]
            }
        ]
    }
```

### 3. Package Versioning (`package_versioning.py`)

```python
class PackageVersionManager:
    """Handles package version control"""
    
    def create_version(self, package: DocumentPackage, change_type: str) -> str:
        """Create new version based on change type"""
        # MAJOR: Breaking changes to structure
        # MINOR: New features, backward compatible
        # PATCH: Bug fixes, minor updates
        
    def get_version_history(self, package_id: str) -> List[VersionRecord]:
        """Retrieve complete version history"""
        
    def rollback_version(self, package_id: str, target_version: str) -> DocumentPackage:
        """Rollback to previous version"""
        
    def diff_versions(self, package_id: str, v1: str, v2: str) -> VersionDiff:
        """Compare two versions of a package"""
```

### 4. Package Relationships (`package_relationships.py`)

```python
class PackageRelationshipManager:
    """Manages relationships within and between packages"""
    
    def define_internal_relationships(self, package: DocumentPackage) -> List[Relationship]:
        """Define relationships between documents in package"""
        relationships = []
        
        # Guidelines to Matrix relationships
        for guideline in package.get_documents(type="guidelines"):
            for matrix in package.get_documents(type="matrix"):
                relationships.extend(
                    self.detect_guideline_matrix_relationships(guideline, matrix)
                )
        
        # Cross-document navigation relationships
        relationships.extend(self.build_navigation_relationships(package))
        
        return relationships
    
    def define_cross_package_relationships(self, pkg1: DocumentPackage, pkg2: DocumentPackage) -> List[Relationship]:
        """Define relationships between packages"""
        # COMPETES_WITH: Similar products
        # UPGRADES_FROM: Premium versions
        # TRANSITIONAL_TO: Category transitions
```

## Database Schema

### Neo4j Nodes

```cypher
// Document Package Node
(:DocumentPackage {
  package_id: "pkg_nqm_titanium_v2",
  package_name: "NQM Titanium Advantage Package",
  tenant_id: "the_g1_group",
  category: "NQM",
  version: "2.1.0",
  status: "ACTIVE",
  created_at: datetime(),
  template_type: "NQM_STANDARD"
})

// Package Document Node
(:PackageDocument {
  document_id: "doc_guidelines_001",
  package_id: "pkg_nqm_titanium_v2",
  document_type: "guidelines",
  expected_structure: {...},
  processing_config: {...}
})
```

### Relationships

```cypher
// Package contains documents
(:DocumentPackage)-[:CONTAINS]->(:PackageDocument)

// Package versioning
(:DocumentPackage)-[:VERSION_OF]->(:DocumentPackage)

// Cross-package relationships
(:DocumentPackage)-[:COMPETES_WITH]->(:DocumentPackage)
(:DocumentPackage)-[:UPGRADES_FROM]->(:DocumentPackage)
```

## API Endpoints

### Package Management APIs

```python
# Create new package
POST /api/v3/packages
{
    "package_name": "NQM Titanium Advantage",
    "category": "NQM",
    "template": "NQM_STANDARD",
    "documents": [...]
}

# Load package
GET /api/v3/packages/{package_id}

# Update package
PUT /api/v3/packages/{package_id}
{
    "updates": {
        "documents": [...],
        "version_type": "MINOR"
    }
}

# Clone package
POST /api/v3/packages/{package_id}/clone
{
    "new_name": "NQM Platinum Advantage",
    "modifications": [...]
}

# Get package history
GET /api/v3/packages/{package_id}/history

# Apply package to documents
POST /api/v3/packages/{package_id}/apply
{
    "document_ids": ["doc_123", "doc_456"],
    "options": {
        "update_in_place": true,
        "preserve_custom_sections": true
    }
}
```

## Usage Workflow

### 1. Creating a Package
```python
# Create package from template
package = PackageManager.create_from_template(
    template="NQM_STANDARD",
    tenant_id="the_g1_group",
    customizations={
        "additional_sections": ["Foreign National Requirements"],
        "matrix_types": ["foreign_national_matrix"]
    }
)
```

### 2. Applying Package to Documents
```python
# Apply package structure to uploaded documents
results = PackageManager.apply_package(
    package_id="pkg_nqm_titanium_v2",
    documents=[
        {"file_id": "file_123", "type": "guidelines"},
        {"file_id": "file_456", "type": "matrix"}
    ],
    options={
        "validate_structure": True,
        "auto_map_sections": True
    }
)
```

### 3. Updating Documents in Place
```python
# Update document while preserving structure
updated_doc = PackageManager.update_document_in_package(
    package_id="pkg_nqm_titanium_v2",
    document_id="doc_guidelines_001",
    updates={
        "sections": {
            "Borrower Eligibility": "Updated content...",
            "New Section": "Additional content..."
        }
    }
)
```

## Benefits

1. **Reusability**: Define once, apply to multiple document sets
2. **Consistency**: Ensure all documents follow standard structure
3. **Versioning**: Track changes and rollback if needed
4. **Relationships**: Maintain connections between documents
5. **Efficiency**: Reduce processing time with pre-defined structures
6. **Quality**: Enforce validation rules and quality standards

## Integration Points

- **Hierarchical Chunking**: Package defines chunking strategy
- **Entity Extraction**: Package specifies expected entities
- **Relationship Detection**: Pre-defined relationship patterns
- **Quality Assurance**: Package-specific quality thresholds