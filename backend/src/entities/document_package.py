# Task 1: Document Package Data Models
# This file contains the core data models for document packages

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum


class PackageStatus(Enum):
    """Enum for package status values"""
    DRAFT = "DRAFT"
    ACTIVE = "ACTIVE"
    ARCHIVED = "ARCHIVED"


class PackageCategory(Enum):
    """Enum for mortgage category values"""
    NQM = "NQM"      # Non-Qualified Mortgage
    RTL = "RTL"      # Rental/Investment
    SBC = "SBC"      # Small Balance Commercial
    CONV = "CONV"    # Conventional


@dataclass
class PackageRelationship:
    """Defines relationships between documents in a package"""
    from_document: str
    to_document: str
    relationship_type: str  # ELABORATES, REFERENCES, REQUIRES, DETERMINES
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """Validate relationship fields"""
        if not self.from_document.strip():
            raise ValueError("from_document cannot be empty")
        if not self.to_document.strip():
            raise ValueError("to_document cannot be empty")
        if not self.relationship_type.strip():
            raise ValueError("relationship_type cannot be empty")


@dataclass
class DocumentDefinition:
    """Individual document within a package"""
    document_id: str
    document_type: str  # guidelines, matrix, rate_sheet
    document_name: str
    expected_structure: Dict[str, Any] = field(default_factory=dict)
    required_sections: List[str] = field(default_factory=list)
    optional_sections: List[str] = field(default_factory=list)
    chunking_strategy: str = "hierarchical"
    entity_types: List[str] = field(default_factory=list)
    matrix_configuration: Optional[Dict[str, Any]] = None
    validation_schema: Dict[str, Any] = field(default_factory=dict)
    quality_thresholds: Dict[str, float] = field(default_factory=dict)

    def __post_init__(self):
        """Validate document definition fields"""
        if not self.document_id.strip():
            raise ValueError("document_id cannot be empty")
        if not self.document_type.strip():
            raise ValueError("document_type cannot be empty")
        if not self.document_name.strip():
            raise ValueError("document_name cannot be empty")
        
        # Validate document type
        valid_types = ["guidelines", "matrix", "rate_sheet"]
        if self.document_type not in valid_types:
            raise ValueError(f"document_type must be one of {valid_types}")
        
        # Validate chunking strategy
        valid_strategies = ["hierarchical", "semantic", "hybrid"]
        if self.chunking_strategy not in valid_strategies:
            raise ValueError(f"chunking_strategy must be one of {valid_strategies}")


@dataclass
class DocumentPackage:
    """Core document package structure"""
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
    documents: List[DocumentDefinition] = field(default_factory=list)
    relationships: List[PackageRelationship] = field(default_factory=list)
    template_mappings: Dict[str, Any] = field(default_factory=dict)
    validation_rules: List[Dict[str, Any]] = field(default_factory=list)

    def __post_init__(self):
        """Validate package fields"""
        if not self.package_id.strip():
            raise ValueError("package_id cannot be empty")
        if not self.package_name.strip():
            raise ValueError("package_name cannot be empty")
        if not self.tenant_id.strip():
            raise ValueError("tenant_id cannot be empty")
        if not self.version.strip():
            raise ValueError("version cannot be empty")
        
        # Validate version format (basic semantic versioning)
        version_parts = self.version.split('.')
        if len(version_parts) != 3:
            raise ValueError("version must follow semantic versioning (MAJOR.MINOR.PATCH)")
        
        try:
            for part in version_parts:
                int(part)
        except ValueError:
            raise ValueError("version parts must be integers")

    def add_document(self, document: DocumentDefinition) -> None:
        """Add a document to the package"""
        # Check for duplicate document IDs
        existing_ids = [doc.document_id for doc in self.documents]
        if document.document_id in existing_ids:
            raise ValueError(f"Document ID {document.document_id} already exists in package")
        
        self.documents.append(document)
        self.updated_at = datetime.now()

    def get_document_by_id(self, document_id: str) -> Optional[DocumentDefinition]:
        """Get a document by its ID"""
        for doc in self.documents:
            if doc.document_id == document_id:
                return doc
        return None

    def get_documents_by_type(self, document_type: str) -> List[DocumentDefinition]:
        """Get all documents of a specific type"""
        return [doc for doc in self.documents if doc.document_type == document_type]


def validate_package(package: DocumentPackage) -> List[str]:
    """Validate package structure and return list of errors"""
    errors = []
    
    # Basic field validation
    if not package.package_name.strip():
        errors.append("Package name cannot be empty")
    
    if len(package.documents) == 0:
        errors.append("Package must contain at least one document")
        
    # Validate document IDs are unique
    doc_ids = [doc.document_id for doc in package.documents]
    if len(doc_ids) != len(set(doc_ids)):
        errors.append("Document IDs must be unique within package")
    
    # Validate document types
    for doc in package.documents:
        try:
            # This will raise an exception if validation fails
            doc.__post_init__()
        except ValueError as e:
            errors.append(f"Document {doc.document_id}: {str(e)}")
    
    # Validate relationships reference existing documents
    for rel in package.relationships:
        if rel.from_document not in doc_ids:
            errors.append(f"Relationship references non-existent document: {rel.from_document}")
        if rel.to_document not in doc_ids:
            errors.append(f"Relationship references non-existent document: {rel.to_document}")
    
    # Validate category-specific requirements
    if package.category == PackageCategory.NQM:
        # NQM packages should have guidelines and matrix
        doc_types = [doc.document_type for doc in package.documents]
        if "guidelines" not in doc_types:
            errors.append("NQM packages should include guidelines document")
        if "matrix" not in doc_types:
            errors.append("NQM packages should include matrix document")
    
    return errors


def create_package_id(category: PackageCategory, unique_suffix: str) -> str:
    """Create a standardized package ID"""
    return f"pkg_{category.value.lower()}_{unique_suffix}"


def is_valid_semantic_version(version: str) -> bool:
    """Check if version string follows semantic versioning"""
    try:
        parts = version.split('.')
        if len(parts) != 3:
            return False
        for part in parts:
            int(part)
        return True
    except ValueError:
        return False