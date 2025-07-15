# Phase 1.1: Document Package Architecture

## ✅ **IMPLEMENTED: 4-Tier Hierarchy Architecture**

## Overview
The Document Package Architecture introduces a revolutionary approach to mortgage document management with a **4-tier hierarchical structure**: Category → Product → Program → Document. This system enables immediate node creation, rich metadata support, and program-specific document associations for enhanced LLM processing. Organizations can create, save, and reuse document structures while maintaining their relationships and hierarchical structure.

**🎯 Key Achievement**: Full 4-tier hierarchy implemented with immediate graph node creation and enhanced LLM context support.

## Core Concepts

### Document Package Definition (4-Tier Enhanced)
A **Document Package** is a reusable template that defines a complete 4-tier hierarchy:
- **Category Level**: Mortgage category with regulatory framework and risk profile
- **Product Level**: Product features, underwriting highlights, and target borrowers
- **Program Level**: Program-specific loan limits, rate adjustments, and qualification criteria
- **Document Level**: Documents associated with specific products or programs
- **Immediate Graph Creation**: All structural nodes created upon package creation
- **Enhanced LLM Context**: Rich metadata passed to LLM for superior processing

### Package Components

```python
class DocumentPackage:
    """✅ IMPLEMENTED: 4-Tier document package structure"""
    package_id: str  # Unique identifier (e.g., "pkg_nqm_titanium_v2")
    package_name: str  # Human-readable name
    tenant_id: str  # Organization identifier
    
    # ✅ NEW: 4-Tier Hierarchy Structure
    category: MortgageCategory  # Rich category with metadata
    products: List[Product]  # Product level with descriptions
    programs: List[Program]  # Program sub-tier with limits/adjustments
    documents: List[DocumentDefinition]  # Enhanced document definitions
    
    version: str  # Semantic versioning (e.g., "2.1.0")
    
    # Package Structure
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
    
    # ✅ NEW: 4-Tier Enhancement Features
    immediate_node_creation: bool = True  # Create nodes on package creation
    enhanced_llm_context: bool = True  # Pass rich metadata to LLM
    program_specific_processing: bool = True  # Enable program-aware processing
```

### Document Definition Structure

```python
class DocumentDefinition:
    """✅ ENHANCED: Individual document within 4-tier package"""
    document_id: str  # Package-scoped ID
    document_type: str  # guidelines, matrix, rate_sheet
    document_name: str  # Display name
    
    # ✅ NEW: 4-Tier Association
    associated_to: str  # "product" or "program"
    parent_id: str  # ID of parent product or program
    association_rules: Dict[str, Any]  # Rules for association
    
    # Structure Definition
    expected_structure: NavigationStructure
    required_sections: List[str]
    optional_sections: List[str]
    
    # Processing Configuration (Enhanced)
    chunking_strategy: str  # hierarchical, semantic, hybrid
    entity_types: List[str]  # Expected entity types
    matrix_configuration: Optional[MatrixConfig]  # If matrix type
    program_context: Optional[ProgramContext]  # ✅ NEW: Program-specific context
    
    # Validation
    validation_schema: Dict
    quality_thresholds: QualityMetrics
    
    # ✅ NEW: Enhanced LLM Processing
    enhanced_context: bool = True  # Use rich metadata for LLM
    program_specific_extraction: bool = True  # Program-aware entity extraction
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

### ✅ IMPLEMENTED: Neo4j Nodes (4-Tier)

```cypher
// ✅ NEW: Mortgage Category Node
(:MortgageCategory {
  category_code: "NQM",
  display_name: "Non-Qualified Mortgage",
  description: "Mortgage products that do not meet QM standards but follow ATR requirements",
  key_characteristics: ["ATR compliant", "Non-QM standards"],
  regulatory_framework: "CFPB ATR Rule",
  risk_profile: "Medium to High",
  created_at: datetime()
})

// ✅ NEW: Product Node
(:Product {
  product_id: "prod_titanium_advantage_001",
  product_name: "Titanium Advantage",
  description: "Premium non-QM product with enhanced features",
  product_type: "core",
  key_features: ["Foreign national support", "Bank statement income"],
  underwriting_highlights: ["Alternative income documentation"],
  target_borrowers: ["Self-employed", "Foreign nationals"],
  created_at: datetime()
})

// ✅ NEW: Program Node
(:Program {
  program_id: "prog_titanium_core_001",
  program_name: "Titanium Core",
  program_code: "CORE",
  description: "Standard program with competitive rates",
  loan_limits: {max_amount: 3000000, min_amount: 150000},
  rate_adjustments: ["+0.125% for foreign nationals"],
  qualification_criteria: ["Minimum 680 FICO", "Maximum 43% DTI"],
  created_at: datetime()
})

// ✅ ENHANCED: Document Package Node
(:DocumentPackage {
  package_id: "pkg_nqm_titanium_v2",
  package_name: "NQM Titanium Advantage Package",
  tenant_id: "the_g1_group",
  version: "2.1.0",
  status: "ACTIVE",
  created_at: datetime(),
  template_type: "NQM_STANDARD",
  four_tier_enabled: true
})

// ✅ ENHANCED: Package Document Node
(:PackageDocument {
  document_id: "doc_guidelines_001",
  package_id: "pkg_nqm_titanium_v2",
  document_type: "guidelines",
  associated_to: "product",
  parent_id: "prod_titanium_advantage_001",
  expected_structure: {...},
  processing_config: {...},
  program_context_enabled: true
})
```

### ✅ IMPLEMENTED: Relationships (4-Tier)

```cypher
// ✅ NEW: 4-Tier Hierarchy Relationships
(:MortgageCategory)-[:CONTAINS]->(:Product)
(:Product)-[:CONTAINS]->(:Program)
(:Program)-[:CONTAINS]->(:Document)

// ✅ NEW: Package to Hierarchy Links
(:DocumentPackage)-[:HAS_CATEGORY]->(:MortgageCategory)
(:DocumentPackage)-[:CONTAINS]->(:Product)
(:DocumentPackage)-[:CONTAINS]->(:Program)

// ✅ NEW: Document Association Relationships
(:PackageDocument)-[:REPRESENTS]->(:Document)
(:PackageDocument)-[:ASSOCIATED_WITH]->(:Product)
(:PackageDocument)-[:ASSOCIATED_WITH]->(:Program)

// Package versioning
(:DocumentPackage)-[:VERSION_OF]->(:DocumentPackage)

// Cross-package relationships
(:DocumentPackage)-[:COMPETES_WITH]->(:DocumentPackage)
(:DocumentPackage)-[:UPGRADES_FROM]->(:DocumentPackage)

// ✅ NEW: Program-Specific Relationships
(:Program)-[:HAS_MATRIX]->(:Document {document_type: "matrix"})
(:Program)-[:PRICING_RULES]->(:Document {document_type: "rate_sheet"})
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

## ✅ IMPLEMENTED: Benefits (4-Tier Enhanced)

1. **✅ 4-Tier Hierarchy**: Complete Category → Product → Program → Document structure with immediate creation
2. **✅ Enhanced LLM Context**: Rich metadata passed to LLM for superior entity extraction and processing
3. **✅ Program-Specific Processing**: Documents understand their program context for targeted analysis
4. **✅ Immediate Graph Creation**: All structural nodes created upon package creation for real-time relationships
5. **✅ Rich Metadata Support**: Categories, products, and programs include detailed descriptions and characteristics
6. **✅ Reusability**: Define once, apply to multiple document sets with program-specific context
7. **✅ Consistency**: Ensure all documents follow standard structure with enhanced validation
8. **✅ Versioning**: Track changes and rollback if needed
9. **✅ Advanced Relationships**: Maintain connections between documents with program-level associations
10. **✅ Efficiency**: Reduce processing time with pre-defined structures and enhanced context
11. **✅ Quality**: Enforce validation rules and quality standards with program-specific thresholds

## ✅ IMPLEMENTED: Integration Points (4-Tier Enhanced)

- **✅ 4-Tier Hierarchical Processing**: Package defines complete category/product/program/document structure
- **✅ Enhanced LLM Context**: Rich metadata from all hierarchy levels passed to LLM for superior processing
- **✅ Program-Specific Processing**: Documents processed with program context for targeted extraction
- **✅ Immediate Graph Creation**: All structural nodes created upon package creation
- **✅ Hierarchical Chunking**: Package defines chunking strategy with program awareness
- **✅ Enhanced Entity Extraction**: Package specifies expected entities with program-specific context
- **✅ Advanced Relationship Detection**: Pre-defined relationship patterns with program-level associations
- **✅ Program-Aware Quality Assurance**: Package-specific quality thresholds enhanced with program context
- **✅ Matrix-Program Integration**: Matrices associated with specific programs for precise pricing
- **✅ Frontend Integration**: Full UI support for 4-tier hierarchy management with description fields