# Backend Tasks - Detailed Implementation Guide

## Overview
16 backend tasks across 3 phases, implementing the core package management, hierarchical chunking, and guidelines navigation systems.

---

# Phase 1.1: Package Architecture (Tasks 1-6)

## Task 1: Create Package Data Models
**Duration**: 2 hours | **Priority**: Critical | **Dependencies**: None

### Implementation Steps
1. **Create entities directory and base models** (30 min)
   ```bash
   mkdir -p backend/src/entities
   touch backend/src/entities/__init__.py
   ```

2. **Implement DocumentPackage dataclass** (45 min)
   ```python
   # backend/src/entities/document_package.py
   from dataclasses import dataclass, field
   from typing import List, Optional, Dict, Any
   from datetime import datetime
   from enum import Enum
   
   class PackageStatus(Enum):
       DRAFT = "DRAFT"
       ACTIVE = "ACTIVE"
       ARCHIVED = "ARCHIVED"
   
   class PackageCategory(Enum):
       NQM = "NQM"
       RTL = "RTL" 
       SBC = "SBC"
       CONV = "CONV"
   
   @dataclass
   class DocumentPackage:
       package_id: str
       package_name: str
       tenant_id: str
       category: PackageCategory
       version: str
       status: PackageStatus = PackageStatus.DRAFT
       created_at: datetime = field(default_factory=datetime.now)
       updated_at: datetime = field(default_factory=datetime.now)
       created_by: str = ""
       template_type: str = ""
       documents: List['DocumentDefinition'] = field(default_factory=list)
       relationships: List['PackageRelationship'] = field(default_factory=list)
       template_mappings: Dict[str, Any] = field(default_factory=dict)
       validation_rules: List[Dict[str, Any]] = field(default_factory=list)
   ```

3. **Implement DocumentDefinition dataclass** (30 min)
   ```python
   @dataclass 
   class DocumentDefinition:
       document_id: str
       document_type: str  # guidelines, matrix, rate_sheet
       document_name: str
       expected_structure: Dict[str, Any]
       required_sections: List[str] = field(default_factory=list)
       optional_sections: List[str] = field(default_factory=list)
       chunking_strategy: str = "hierarchical"
       entity_types: List[str] = field(default_factory=list)
       matrix_configuration: Optional[Dict[str, Any]] = None
       validation_schema: Dict[str, Any] = field(default_factory=dict)
       quality_thresholds: Dict[str, float] = field(default_factory=dict)
   ```

4. **Implement PackageRelationship dataclass** (15 min)
   ```python
   @dataclass
   class PackageRelationship:
       from_document: str
       to_document: str
       relationship_type: str  # ELABORATES, REFERENCES, REQUIRES
       metadata: Dict[str, Any] = field(default_factory=dict)
   ```

5. **Add validation methods** (30 min)
   ```python
   def validate_package(package: DocumentPackage) -> List[str]:
       """Validate package structure and return list of errors"""
       errors = []
       
       if not package.package_name.strip():
           errors.append("Package name cannot be empty")
       
       if len(package.documents) == 0:
           errors.append("Package must contain at least one document")
           
       # Validate document IDs are unique
       doc_ids = [doc.document_id for doc in package.documents]
       if len(doc_ids) != len(set(doc_ids)):
           errors.append("Document IDs must be unique within package")
           
       return errors
   ```

6. **Create unit tests** (30 min)
   ```python
   # backend/tests/test_document_package.py
   import pytest
   from src.entities.document_package import DocumentPackage, DocumentDefinition, PackageStatus, PackageCategory
   
   def test_document_package_creation():
       package = DocumentPackage(
           package_id="test_pkg_001",
           package_name="Test Package",
           tenant_id="tenant_001",
           category=PackageCategory.NQM,
           version="1.0.0"
       )
       assert package.status == PackageStatus.DRAFT
       assert len(package.documents) == 0
   ```

### Acceptance Criteria Checklist
- [ ] DocumentPackage dataclass with all required fields
- [ ] DocumentDefinition dataclass with structure validation  
- [ ] PackageRelationship dataclass with relationship types
- [ ] Type hints for all fields using typing module
- [ ] Basic validation methods with error collection
- [ ] Unit tests covering model creation and validation

---

## Task 2: Create Package Manager Core
**Duration**: 3 hours | **Priority**: Critical | **Dependencies**: Task 1

### Implementation Steps

1. **Create PackageManager class structure** (45 min)
   ```python
   # backend/src/package_manager.py
   from typing import List, Optional, Dict, Any
   from src.entities.document_package import DocumentPackage, DocumentDefinition, PackageStatus
   from src.graphDB_dataAccess import graphDBdataAccess
   import uuid
   from datetime import datetime
   
   class PackageManager:
       def __init__(self, graph_db: graphDBdataAccess):
           self.graph_db = graph_db
           self.logger = logging.getLogger(__name__)
   ```

2. **Implement create_package method** (45 min)
   ```python
   def create_package(self, package_config: Dict[str, Any]) -> DocumentPackage:
       """Create a new document package"""
       try:
           # Generate unique package ID
           package_id = f"pkg_{package_config['category'].lower()}_{uuid.uuid4().hex[:8]}"
           
           # Initialize package structure
           package = DocumentPackage(
               package_id=package_id,
               package_name=package_config['package_name'],
               tenant_id=package_config['tenant_id'],
               category=PackageCategory(package_config['category']),
               version="1.0.0",
               created_by=package_config.get('created_by', 'system'),
               template_type=package_config.get('template', '')
           )
           
           # Add documents from configuration
           for doc_config in package_config.get('documents', []):
               document = DocumentDefinition(
                   document_id=f"doc_{uuid.uuid4().hex[:8]}",
                   **doc_config
               )
               package.documents.append(document)
           
           # Store in database
           self._store_package_in_db(package)
           
           self.logger.info(f"Created package {package_id}")
           return package
           
       except Exception as e:
           self.logger.error(f"Failed to create package: {str(e)}")
           raise
   ```

3. **Implement load_package method** (30 min)
   ```python
   def load_package(self, package_id: str) -> DocumentPackage:
       """Load existing package for use"""
       try:
           # Retrieve from database
           package_data = self._retrieve_package_from_db(package_id)
           
           if not package_data:
               raise ValueError(f"Package {package_id} not found")
           
           # Validate package integrity
           package = self._deserialize_package(package_data)
           validation_errors = validate_package(package)
           
           if validation_errors:
               raise ValueError(f"Package validation failed: {validation_errors}")
           
           # Load relationships
           package.relationships = self._load_package_relationships(package_id)
           
           return package
           
       except Exception as e:
           self.logger.error(f"Failed to load package {package_id}: {str(e)}")
           raise
   ```

4. **Implement update_package method** (45 min)
   ```python
   def update_package(self, package_id: str, updates: Dict[str, Any]) -> DocumentPackage:
       """Update package in place"""
       try:
           # Load existing package
           package = self.load_package(package_id)
           
           # Validate update compatibility
           self._validate_update_compatibility(package, updates)
           
           # Apply structural changes
           if 'documents' in updates:
               package.documents = self._merge_document_updates(
                   package.documents, updates['documents']
               )
           
           # Update version based on change type
           if updates.get('version_type') == 'MAJOR':
               package.version = self._increment_major_version(package.version)
           elif updates.get('version_type') == 'MINOR':
               package.version = self._increment_minor_version(package.version)
           else:
               package.version = self._increment_patch_version(package.version)
           
           package.updated_at = datetime.now()
           
           # Store updated package
           self._store_package_in_db(package)
           
           return package
           
       except Exception as e:
           self.logger.error(f"Failed to update package {package_id}: {str(e)}")
           raise
   ```

5. **Implement clone_package method** (30 min)
   ```python
   def clone_package(self, package_id: str, new_name: str, modifications: Dict[str, Any] = None) -> DocumentPackage:
       """Create a copy of existing package"""
       try:
           # Load source package
           source_package = self.load_package(package_id)
           
           # Deep copy structure with new IDs
           cloned_package = DocumentPackage(
               package_id=f"pkg_{source_package.category.value.lower()}_{uuid.uuid4().hex[:8]}",
               package_name=new_name,
               tenant_id=source_package.tenant_id,
               category=source_package.category,
               version="1.0.0",  # Reset version
               created_by=modifications.get('created_by', 'system'),
               template_type=source_package.template_type,
               documents=[self._clone_document(doc) for doc in source_package.documents],
               template_mappings=source_package.template_mappings.copy(),
               validation_rules=source_package.validation_rules.copy()
           )
           
           # Apply modifications if provided
           if modifications:
               self._apply_modifications(cloned_package, modifications)
           
           # Store cloned package
           self._store_package_in_db(cloned_package)
           
           return cloned_package
           
       except Exception as e:
           self.logger.error(f"Failed to clone package {package_id}: {str(e)}")
           raise
   ```

6. **Implement helper methods** (45 min)
   ```python
   def _store_package_in_db(self, package: DocumentPackage) -> None:
       """Store package in Neo4j database"""
       # Implementation depends on Task 5
       pass
   
   def _retrieve_package_from_db(self, package_id: str) -> Dict[str, Any]:
       """Retrieve package data from database"""
       # Implementation depends on Task 5
       pass
   
   def _validate_update_compatibility(self, package: DocumentPackage, updates: Dict[str, Any]) -> None:
       """Validate that updates are compatible with existing package"""
       if 'category' in updates and updates['category'] != package.category.value:
           raise ValueError("Cannot change package category in update")
   
   def _increment_major_version(self, version: str) -> str:
       major, minor, patch = map(int, version.split('.'))
       return f"{major + 1}.0.0"
   ```

### Acceptance Criteria Checklist
- [ ] PackageManager class with database integration
- [ ] create_package method with ID generation and validation
- [ ] load_package method with integrity validation  
- [ ] update_package method with version handling
- [ ] clone_package method with ID regeneration
- [ ] Error handling for all operations with proper logging
- [ ] Unit tests for all methods with mock database

---

## Task 3: Create Package Templates
**Duration**: 2 hours | **Priority**: High | **Dependencies**: Task 1

### Implementation Steps

1. **Create MortgagePackageTemplates class** (30 min)
   ```python
   # backend/src/package_templates.py
   from typing import Dict, Any, List
   from src.entities.document_package import DocumentDefinition, PackageRelationship, PackageCategory
   
   class MortgagePackageTemplates:
       """Pre-defined templates for mortgage categories"""
       
       @staticmethod
       def get_template(category: PackageCategory) -> Dict[str, Any]:
           """Get template configuration for category"""
           templates = {
               PackageCategory.NQM: MortgagePackageTemplates.NQM_TEMPLATE,
               PackageCategory.RTL: MortgagePackageTemplates.RTL_TEMPLATE,
               PackageCategory.SBC: MortgagePackageTemplates.SBC_TEMPLATE,
               PackageCategory.CONV: MortgagePackageTemplates.CONV_TEMPLATE
           }
           return templates.get(category, {})
   ```

2. **Implement NQM_TEMPLATE** (30 min)
   ```python
   NQM_TEMPLATE = {
       "category": "NQM",
       "template_name": "Non-QM Standard Template",
       "documents": [
           {
               "document_type": "guidelines",
               "document_name": "NQM Guidelines",
               "expected_structure": {
                   "chapters": ["Borrower Eligibility", "Income Documentation", "Asset Requirements", "Property Standards", "Credit Analysis"],
                   "navigation_depth": 4
               },
               "required_sections": [
                   "Borrower Eligibility",
                   "Income Documentation", 
                   "Asset Requirements",
                   "Property Standards",
                   "Credit Analysis"
               ],
               "optional_sections": [
                   "Foreign National Requirements",
                   "Specialty Programs"
               ],
               "entity_types": ["LOAN_PROGRAM", "BORROWER_TYPE", "REQUIREMENT", "NUMERIC_THRESHOLD"],
               "decision_trees": ["eligibility", "documentation", "property"],
               "quality_thresholds": {
                   "navigation_accuracy": 0.95,
                   "decision_completeness": 1.0,
                   "entity_coverage": 0.90
               }
           },
           {
               "document_type": "matrix",
               "document_name": "NQM Matrix",
               "matrix_types": ["qualification", "pricing", "ltv_matrix"],
               "dimensions": ["fico_score", "ltv_ratio", "dti_ratio"],
               "expected_structure": {
                   "matrix_count": 3,
                   "dimension_ranges": {
                       "fico_score": [580, 850],
                       "ltv_ratio": [0.1, 0.95],
                       "dti_ratio": [0.1, 0.50]
                   }
               }
           }
       ],
       "relationships": [
           {
               "from": "guidelines.eligibility",
               "to": "matrix.qualification", 
               "type": "ELABORATES",
               "metadata": {"connection_type": "policy_to_matrix"}
           },
           {
               "from": "guidelines.credit_analysis",
               "to": "matrix.pricing",
               "type": "DETERMINES",
               "metadata": {"connection_type": "criteria_to_pricing"}
           }
       ]
   }
   ```

3. **Implement RTL_TEMPLATE** (20 min)
   ```python
   RTL_TEMPLATE = {
       "category": "RTL",
       "template_name": "Rental/Investment Property Template",
       "documents": [
           {
               "document_type": "guidelines",
               "document_name": "RTL Guidelines",
               "required_sections": [
                   "Rehab Requirements",
                   "Draw Schedule", 
                   "Inspection Process",
                   "Completion Standards",
                   "Investment Property Analysis"
               ],
               "decision_trees": ["rehab_eligibility", "draw_approval", "completion_verification"],
               "entity_types": ["PROPERTY_TYPE", "REHAB_REQUIREMENT", "INSPECTION_MILESTONE"]
           },
           {
               "document_type": "matrix",
               "document_name": "RTL Matrix",
               "matrix_types": ["rehab_cost", "arv_matrix", "rental_income"],
               "dimensions": ["property_value", "rehab_percentage", "rental_yield"]
           }
       ]
   }
   ```

4. **Implement SBC and CONV templates** (20 min)
   ```python
   SBC_TEMPLATE = {
       "category": "SBC",
       "template_name": "Small Balance Commercial Template",
       "documents": [
           {
               "document_type": "guidelines",
               "document_name": "SBC Guidelines", 
               "required_sections": [
                   "Property Requirements",
                   "Income Analysis",
                   "Debt Service Coverage",
                   "Environmental Review"
               ],
               "entity_types": ["COMMERCIAL_PROPERTY", "INCOME_SOURCE", "ENVIRONMENTAL_FACTOR"]
           }
       ]
   }
   
   CONV_TEMPLATE = {
       "category": "CONV",
       "template_name": "Conventional Mortgage Template",
       "documents": [
           {
               "document_type": "guidelines",
               "document_name": "Conventional Guidelines",
               "required_sections": [
                   "Standard Eligibility",
                   "Income Requirements", 
                   "Credit Standards",
                   "Property Requirements"
               ],
               "entity_types": ["BORROWER_TYPE", "INCOME_TYPE", "CREDIT_REQUIREMENT"]
           }
       ]
   }
   ```

5. **Add template instantiation methods** (30 min)
   ```python
   @staticmethod
   def create_package_from_template(category: PackageCategory, customizations: Dict[str, Any] = None) -> Dict[str, Any]:
       """Create package configuration from template with customizations"""
       template = MortgagePackageTemplates.get_template(category)
       
       if not template:
           raise ValueError(f"No template found for category {category}")
       
       # Apply customizations if provided
       if customizations:
           template = MortgagePackageTemplates._apply_customizations(template, customizations)
       
       return template
   
   @staticmethod
   def _apply_customizations(template: Dict[str, Any], customizations: Dict[str, Any]) -> Dict[str, Any]:
       """Apply customizations to template"""
       if 'additional_sections' in customizations:
           for doc in template['documents']:
               if doc['document_type'] == 'guidelines':
                   doc['optional_sections'].extend(customizations['additional_sections'])
       
       if 'matrix_types' in customizations:
           for doc in template['documents']:
               if doc['document_type'] == 'matrix':
                   doc['matrix_types'].extend(customizations['matrix_types'])
       
       return template
   ```

6. **Create validation and tests** (30 min)
   ```python
   @staticmethod
   def validate_template(template: Dict[str, Any]) -> List[str]:
       """Validate template structure"""
       errors = []
       
       if 'documents' not in template:
           errors.append("Template must contain documents")
       
       for doc in template.get('documents', []):
           if 'document_type' not in doc:
               errors.append("Document must have type")
           if 'required_sections' not in doc:
               errors.append("Document must have required sections")
       
       return errors
   ```

### Acceptance Criteria Checklist
- [ ] MortgagePackageTemplates class with all category templates
- [ ] NQM_TEMPLATE with complete document structure and relationships
- [ ] RTL_TEMPLATE with rehab-specific sections and matrices
- [ ] SBC_TEMPLATE with commercial property requirements
- [ ] CONV_TEMPLATE with conventional mortgage standards
- [ ] Template validation and instantiation methods
- [ ] Tests for all template types and customization scenarios

---

## Task 4: Implement Package Versioning
**Duration**: 3 hours | **Priority**: High | **Dependencies**: Task 1

### Implementation Steps

1. **Create PackageVersionManager class** (45 min)
   ```python
   # backend/src/package_versioning.py
   from typing import List, Dict, Any, Optional
   from dataclasses import dataclass
   from datetime import datetime
   from enum import Enum
   import json
   
   class ChangeType(Enum):
       MAJOR = "MAJOR"  # Breaking changes to structure
       MINOR = "MINOR"  # New features, backward compatible  
       PATCH = "PATCH"  # Bug fixes, minor updates
   
   @dataclass
   class VersionRecord:
       version: str
       change_type: ChangeType
       changes: List[str]
       created_at: datetime
       created_by: str
       metadata: Dict[str, Any]
   
   @dataclass
   class VersionDiff:
       from_version: str
       to_version: str
       added_documents: List[str]
       removed_documents: List[str]
       modified_documents: List[str]
       structural_changes: List[str]
   ```

2. **Implement create_version method** (45 min)
   ```python
   class PackageVersionManager:
       def __init__(self, graph_db):
           self.graph_db = graph_db
           self.logger = logging.getLogger(__name__)
   
       def create_version(self, package: DocumentPackage, change_type: ChangeType, changes: List[str] = None) -> str:
           """Create new version based on change type"""
           try:
               current_version = package.version
               new_version = self._calculate_new_version(current_version, change_type)
               
               # Create version record
               version_record = VersionRecord(
                   version=new_version,
                   change_type=change_type,
                   changes=changes or [],
                   created_at=datetime.now(),
                   created_by=package.created_by,
                   metadata={
                       "previous_version": current_version,
                       "package_id": package.package_id
                   }
               )
               
               # Store version record
               self._store_version_record(package.package_id, version_record)
               
               # Update package version
               package.version = new_version
               package.updated_at = datetime.now()
               
               self.logger.info(f"Created version {new_version} for package {package.package_id}")
               return new_version
               
           except Exception as e:
               self.logger.error(f"Failed to create version: {str(e)}")
               raise
   
       def _calculate_new_version(self, current: str, change_type: ChangeType) -> str:
           """Calculate new version based on change type"""
           major, minor, patch = map(int, current.split('.'))
           
           if change_type == ChangeType.MAJOR:
               return f"{major + 1}.0.0"
           elif change_type == ChangeType.MINOR:
               return f"{major}.{minor + 1}.0"
           else:  # PATCH
               return f"{major}.{minor}.{patch + 1}"
   ```

3. **Implement version history methods** (30 min)
   ```python
   def get_version_history(self, package_id: str) -> List[VersionRecord]:
       """Retrieve complete version history"""
       try:
           history_data = self._retrieve_version_history(package_id)
           return [self._deserialize_version_record(record) for record in history_data]
       except Exception as e:
           self.logger.error(f"Failed to get version history for {package_id}: {str(e)}")
           raise
   
   def get_version_by_number(self, package_id: str, version: str) -> Optional[VersionRecord]:
       """Get specific version record"""
       history = self.get_version_history(package_id)
       return next((record for record in history if record.version == version), None)
   ```

4. **Implement rollback functionality** (45 min)
   ```python
   def rollback_version(self, package_id: str, target_version: str) -> DocumentPackage:
       """Rollback to previous version"""
       try:
           # Validate target version exists
           target_record = self.get_version_by_number(package_id, target_version)
           if not target_record:
               raise ValueError(f"Version {target_version} not found")
           
           # Retrieve package state at target version
           package_snapshot = self._retrieve_package_snapshot(package_id, target_version)
           
           if not package_snapshot:
               raise ValueError(f"No snapshot found for version {target_version}")
           
           # Create new version for rollback
           current_package = self._load_current_package(package_id)
           rollback_version = self.create_version(
               current_package, 
               ChangeType.MAJOR,
               [f"Rollback to version {target_version}"]
           )
           
           # Restore package state
           restored_package = self._restore_package_from_snapshot(package_snapshot)
           restored_package.version = rollback_version
           
           return restored_package
           
       except Exception as e:
           self.logger.error(f"Failed to rollback package {package_id} to {target_version}: {str(e)}")
           raise
   ```

5. **Implement diff functionality** (45 min)
   ```python
   def diff_versions(self, package_id: str, v1: str, v2: str) -> VersionDiff:
       """Compare two versions of a package"""
       try:
           # Get package snapshots for both versions
           snapshot1 = self._retrieve_package_snapshot(package_id, v1)
           snapshot2 = self._retrieve_package_snapshot(package_id, v2)
           
           if not snapshot1 or not snapshot2:
               raise ValueError("One or both versions not found")
           
           # Compare documents
           docs1 = {doc['document_id']: doc for doc in snapshot1.get('documents', [])}
           docs2 = {doc['document_id']: doc for doc in snapshot2.get('documents', [])}
           
           added_documents = list(set(docs2.keys()) - set(docs1.keys()))
           removed_documents = list(set(docs1.keys()) - set(docs2.keys()))
           
           # Find modified documents
           modified_documents = []
           for doc_id in set(docs1.keys()) & set(docs2.keys()):
               if docs1[doc_id] != docs2[doc_id]:
                   modified_documents.append(doc_id)
           
           # Detect structural changes
           structural_changes = self._detect_structural_changes(snapshot1, snapshot2)
           
           return VersionDiff(
               from_version=v1,
               to_version=v2,
               added_documents=added_documents,
               removed_documents=removed_documents,
               modified_documents=modified_documents,
               structural_changes=structural_changes
           )
           
       except Exception as e:
           self.logger.error(f"Failed to diff versions {v1} and {v2}: {str(e)}")
           raise
   ```

6. **Add helper methods and tests** (30 min)
   ```python
   def _detect_structural_changes(self, snapshot1: Dict, snapshot2: Dict) -> List[str]:
       """Detect structural changes between snapshots"""
       changes = []
       
       if snapshot1.get('category') != snapshot2.get('category'):
           changes.append("Category changed")
       
       if len(snapshot1.get('documents', [])) != len(snapshot2.get('documents', [])):
           changes.append("Document count changed")
       
       return changes
   
   def _store_version_record(self, package_id: str, record: VersionRecord) -> None:
       """Store version record in database"""
       # Implementation depends on Task 5
       pass
   
   def _create_package_snapshot(self, package: DocumentPackage) -> Dict[str, Any]:
       """Create snapshot of package state"""
       return {
           "package_id": package.package_id,
           "package_name": package.package_name,
           "category": package.category.value,
           "documents": [self._serialize_document(doc) for doc in package.documents],
           "relationships": [self._serialize_relationship(rel) for rel in package.relationships],
           "snapshot_created": datetime.now().isoformat()
       }
   ```

### Acceptance Criteria Checklist
- [ ] PackageVersionManager class with database integration
- [ ] create_version method with semantic versioning (MAJOR.MINOR.PATCH)
- [ ] get_version_history method returning chronological list
- [ ] rollback_version method with snapshot restoration
- [ ] diff_versions comparison method showing all changes
- [ ] Version validation and conflict resolution
- [ ] Tests for version operations including edge cases

---

# Phase 1.2: Hierarchical Chunking (Tasks 7-11)

## Task 7: Create Navigation Extractor
**Duration**: 4 hours | **Priority**: Critical | **Dependencies**: Task 1

### Implementation Steps

1. **Create NavigationExtractor class structure** (60 min)
   ```python
   # backend/src/navigation_extractor.py
   from typing import List, Dict, Any, Optional, Tuple
   from dataclasses import dataclass
   import re
   import logging
   from src.llm import get_llm
   from src.entities.navigation_models import NavigationNode, NavigationTree, HeadingPatterns
   
   @dataclass
   class NavigationPatterns:
       chapter_patterns: List[str]
       section_patterns: List[str] 
       subsection_patterns: List[str]
       decision_patterns: List[str]
   
   class NavigationExtractor:
       def __init__(self, llm_model: str = "claude-sonnet-4"):
           self.llm = get_llm(llm_model)
           self.patterns = self._initialize_patterns()
           self.logger = logging.getLogger(__name__)
   
       def _initialize_patterns(self) -> NavigationPatterns:
           return NavigationPatterns(
               chapter_patterns=[
                   r'^\s*CHAPTER\s+(\d+)[:\s]+(.+)$',
                   r'^\s*(\d+)\.\s+([A-Z][A-Z\s]+)$',
                   r'^\s*PART\s+([A-Z]+)[:\s]+(.+)$'
               ],
               section_patterns=[
                   r'^\s*(\d+\.\d+)\s+(.+)$',
                   r'^\s*Section\s+(\d+)[:\s]+(.+)$',
                   r'^\s*([A-Z])\.\s+(.+)$'
               ],
               subsection_patterns=[
                   r'^\s*(\d+\.\d+\.\d+)\s+(.+)$',
                   r'^\s*\(([a-z])\)\s+(.+)$',
                   r'^\s*([ivx]+)\.\s+(.+)$'
               ],
               decision_patterns=[
                   r'(?i)(eligibility|requirements|criteria|standards)',
                   r'(?i)(approve|decline|refer|review)',
                   r'(?i)(if\s+.*\s+then|when\s+.*\s+must)'
               ]
           )
   ```

2. **Implement main extraction method** (60 min)
   ```python
   def extract_navigation_structure(self, document: Dict[str, Any]) -> NavigationTree:
       """Extract complete navigation hierarchy"""
       try:
           self.logger.info(f"Extracting navigation from document: {document.get('name', 'unknown')}")
           
           # Step 1: Detect table of contents
           toc = self.extract_table_of_contents(document)
           
           # Step 2: Identify heading patterns
           heading_patterns = self.detect_heading_patterns(document)
           
           # Step 3: Build navigation tree
           nav_tree = self.build_navigation_tree(document, toc, heading_patterns)
           
           # Step 4: Extract decision trees
           decision_trees = self.extract_decision_trees(nav_tree)
           
           # Step 5: Validate completeness
           validation_result = self.validate_navigation_structure(nav_tree, decision_trees)
           
           if not validation_result['is_complete']:
               self.logger.warning(f"Navigation extraction incomplete: {validation_result['issues']}")
           
           return NavigationTree(
               nodes=nav_tree.nodes,
               decision_trees=decision_trees,
               metadata={
                   'extraction_accuracy': validation_result.get('accuracy', 0),
                   'total_nodes': len(nav_tree.nodes),
                   'decision_sections': len(decision_trees)
               }
           )
           
       except Exception as e:
           self.logger.error(f"Navigation extraction failed: {str(e)}")
           raise
   ```

3. **Implement table of contents extraction** (45 min)
   ```python
   def extract_table_of_contents(self, document: Dict[str, Any]) -> Dict[str, Any]:
       """Extract table of contents from document"""
       content = document.get('content', '')
       
       # Look for common TOC indicators
       toc_indicators = [
           r'(?i)table\s+of\s+contents',
           r'(?i)contents',
           r'(?i)index'
       ]
       
       toc_sections = []
       
       for line_num, line in enumerate(content.split('\n')):
           # Check if line contains TOC indicator
           for indicator in toc_indicators:
               if re.search(indicator, line):
                   # Extract TOC content following this line
                   toc_content = self._extract_toc_content(content, line_num)
                   if toc_content:
                       toc_sections.extend(toc_content)
                   break
       
       return {
           'has_toc': len(toc_sections) > 0,
           'sections': toc_sections,
           'extraction_method': 'pattern_matching'
       }
   
   def _extract_toc_content(self, content: str, start_line: int) -> List[Dict[str, Any]]:
       """Extract TOC entries after TOC header"""
       lines = content.split('\n')
       toc_entries = []
       
       # Look for numbered entries in next 50 lines
       for i in range(start_line + 1, min(start_line + 50, len(lines))):
           line = lines[i].strip()
           
           # Match various TOC formats
           patterns = [
               r'^(\d+)\.\s+([^.]+)\.+(\d+)$',  # 1. Chapter Name....... 5
               r'^(\d+\.\d+)\s+([^.]+)\.+(\d+)$',  # 1.1 Section Name... 15
               r'^([A-Z])\.\s+([^.]+)\.+(\d+)$'  # A. Appendix Name... 25
           ]
           
           for pattern in patterns:
               match = re.match(pattern, line)
               if match:
                   toc_entries.append({
                       'number': match.group(1),
                       'title': match.group(2).strip(),
                       'page': int(match.group(3)),
                       'level': len(match.group(1).split('.'))
                   })
                   break
       
       return toc_entries
   ```

4. **Implement heading pattern detection** (45 min)
   ```python
   def detect_heading_patterns(self, document: Dict[str, Any]) -> HeadingPatterns:
       """Detect document heading patterns"""
       content = document.get('content', '')
       lines = content.split('\n')
       
       detected_patterns = {
           'chapter': [],
           'section': [],
           'subsection': [],
           'decision_indicators': []
       }
       
       for line_num, line in enumerate(lines):
           line = line.strip()
           if not line:
               continue
           
           # Check chapter patterns
           for pattern in self.patterns.chapter_patterns:
               match = re.match(pattern, line, re.IGNORECASE)
               if match:
                   detected_patterns['chapter'].append({
                       'line_number': line_num,
                       'pattern': pattern,
                       'match': match.groups(),
                       'text': line
                   })
                   break
           
           # Check section patterns
           for pattern in self.patterns.section_patterns:
               match = re.match(pattern, line, re.IGNORECASE)
               if match:
                   detected_patterns['section'].append({
                       'line_number': line_num,
                       'pattern': pattern,
                       'match': match.groups(),
                       'text': line
                   })
                   break
           
           # Check subsection patterns
           for pattern in self.patterns.subsection_patterns:
               match = re.match(pattern, line, re.IGNORECASE)
               if match:
                   detected_patterns['subsection'].append({
                       'line_number': line_num,
                       'pattern': pattern,
                       'match': match.groups(),
                       'text': line
                   })
                   break
           
           # Check for decision indicators
           for pattern in self.patterns.decision_patterns:
               if re.search(pattern, line, re.IGNORECASE):
                   detected_patterns['decision_indicators'].append({
                       'line_number': line_num,
                       'indicator': pattern,
                       'text': line
                   })
       
       return HeadingPatterns(**detected_patterns)
   ```

5. **Implement navigation tree building** (45 min)
   ```python
   def build_navigation_tree(self, document: Dict[str, Any], toc: Dict[str, Any], patterns: HeadingPatterns) -> NavigationTree:
       """Build hierarchical navigation tree"""
       nodes = []
       content = document.get('content', '')
       
       # Combine TOC and pattern-detected headings
       all_headings = self._merge_toc_and_patterns(toc, patterns)
       
       # Sort by line number to maintain document order
       all_headings.sort(key=lambda x: x.get('line_number', 0))
       
       # Build hierarchical structure
       node_stack = []  # Stack to maintain hierarchy
       
       for heading in all_headings:
           node = NavigationNode(
               enhanced_node_id=self._generate_node_id(heading),
               node_type=heading['type'],
               title=heading['title'],
               content=self._extract_section_content(content, heading),
               hierarchy_markers={
                   'chapter_number': heading.get('chapter'),
                   'section_number': heading.get('section'),
                   'depth_level': heading.get('level', 1)
               },
               line_number=heading.get('line_number', 0)
           )
           
           # Determine parent-child relationships
           while node_stack and node_stack[-1]['level'] >= heading.get('level', 1):
               node_stack.pop()
           
           if node_stack:
               node.parent_id = node_stack[-1]['node'].enhanced_node_id
               node_stack[-1]['node'].children.append(node)
           
           node_stack.append({'node': node, 'level': heading.get('level', 1)})
           nodes.append(node)
       
       return NavigationTree(nodes=nodes, decision_trees=[], metadata={})
   ```

6. **Add validation and testing** (45 min)
   ```python
   def validate_navigation_structure(self, nav_tree: NavigationTree, decision_trees: List) -> Dict[str, Any]:
       """Validate navigation structure completeness"""
       issues = []
       
       # Check for orphaned nodes
       all_node_ids = {node.enhanced_node_id for node in nav_tree.nodes}
       for node in nav_tree.nodes:
           if node.parent_id and node.parent_id not in all_node_ids:
               issues.append(f"Orphaned node: {node.enhanced_node_id}")
       
       # Check decision tree completeness
       decision_sections = [n for n in nav_tree.nodes if n.node_type == "DECISION_FLOW_SECTION"]
       if len(decision_sections) != len(decision_trees):
           issues.append("Decision tree count mismatch")
       
       # Calculate accuracy metrics
       accuracy = max(0, 1.0 - (len(issues) / max(len(nav_tree.nodes), 1)))
       
       return {
           'is_complete': len(issues) == 0,
           'issues': issues,
           'accuracy': accuracy,
           'total_nodes': len(nav_tree.nodes),
           'decision_sections': len(decision_sections)
       }
   ```

### Acceptance Criteria Checklist
- [ ] NavigationExtractor class with LLM integration
- [ ] extract_navigation_structure method with complete pipeline
- [ ] detect_heading_patterns method with regex pattern matching
- [ ] extract_table_of_contents method for TOC detection
- [ ] validate_navigation_structure method with accuracy metrics
- [ ] Support for multiple document formats (PDF, Word, text)
- [ ] Tests with sample mortgage documents showing >95% accuracy

---

Continue with remaining backend tasks (8-16) following the same detailed format...