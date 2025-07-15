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
class CategoryMetadata:
    """Rich metadata for mortgage categories to enhance LLM processing"""
    category: PackageCategory
    display_name: str
    description: str
    key_characteristics: List[str] = field(default_factory=list)
    regulatory_framework: str = ""
    typical_products: List[str] = field(default_factory=list)
    risk_profile: str = ""
    
    def __post_init__(self):
        """Validate category metadata"""
        if not self.display_name.strip():
            raise ValueError("display_name cannot be empty")
        if not self.description.strip():
            raise ValueError("description cannot be empty")


# Default category metadata for enhanced LLM processing
DEFAULT_CATEGORY_METADATA = {
    PackageCategory.CONV: CategoryMetadata(
        category=PackageCategory.CONV,
        display_name="Conventional Mortgage",
        description="Traditional mortgage loans that conform to government-sponsored enterprise (GSE) guidelines, including Fannie Mae and Freddie Mac standards. These loans typically offer competitive rates and terms for qualified borrowers.",
        key_characteristics=[
            "Conforms to GSE guidelines",
            "Typically requires 20% down payment to avoid PMI",
            "Strong credit score requirements (usually 620+)",
            "Standard debt-to-income ratio limits",
            "Competitive interest rates"
        ],
        regulatory_framework="GSE Guidelines, QM Rules",
        typical_products=["Fixed Rate 30-Year", "Fixed Rate 15-Year", "ARM Products"],
        risk_profile="Low to Moderate"
    ),
    PackageCategory.NQM: CategoryMetadata(
        category=PackageCategory.NQM,
        display_name="Non-Qualified Mortgage",
        description="Mortgage loans that do not meet the Consumer Financial Protection Bureau's Qualified Mortgage (QM) standards. These loans provide flexible underwriting for borrowers who may not qualify for traditional mortgages.",
        key_characteristics=[
            "Does not meet QM standards",
            "Flexible underwriting guidelines",
            "Alternative documentation accepted",
            "Higher debt-to-income ratios allowed",
            "Specialized risk assessment required"
        ],
        regulatory_framework="ATR/QM Rules, CFPB Guidelines",
        typical_products=["Interest Only", "Asset-Based", "Bank Statement"],
        risk_profile="Moderate to High"
    ),
    PackageCategory.RTL: CategoryMetadata(
        category=PackageCategory.RTL,
        display_name="Rental/Investment Property",
        description="Mortgage loans for investment properties and rental real estate. These loans are designed for investors purchasing properties to generate rental income or capital appreciation.",
        key_characteristics=[
            "Investment property focus",
            "Rental income considerations",
            "Higher down payment requirements",
            "Cash flow analysis required",
            "Different risk assessment"
        ],
        regulatory_framework="Investment Property Guidelines",
        typical_products=["Fix & Flip", "DSCR Loans", "Portfolio Loans"],
        risk_profile="Moderate to High"
    ),
    PackageCategory.SBC: CategoryMetadata(
        category=PackageCategory.SBC,
        display_name="Small Balance Commercial",
        description="Commercial mortgage loans for smaller commercial properties, typically under $5 million. These loans bridge the gap between residential and large commercial financing.",
        key_characteristics=[
            "Commercial property focus",
            "Smaller loan amounts",
            "Business cash flow analysis",
            "Property income evaluation",
            "Commercial underwriting standards"
        ],
        regulatory_framework="Commercial Lending Guidelines",
        typical_products=["Commercial Term Loans", "Bridge Loans", "SBA Backed"],
        risk_profile="Moderate"
    )
}


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
class PackageProduct:
    """Product tier between package and documents"""
    product_id: str
    product_name: str
    product_type: str  # core, supplemental, conditional
    description: str = ""  # Rich description for enhanced LLM processing
    tier_level: int = 1  # 1 for main tier, 2 for sub-tier
    processing_priority: int = 1  # 1=high, 2=medium, 3=low
    dependencies: List[str] = field(default_factory=list)  # IDs of other products this depends on
    key_features: List[str] = field(default_factory=list)  # Key product features for LLM context
    underwriting_highlights: List[str] = field(default_factory=list)  # Underwriting focus areas
    target_borrowers: List[str] = field(default_factory=list)  # Target borrower profiles
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """Validate product fields"""
        if not self.product_id.strip():
            raise ValueError("product_id cannot be empty")
        if not self.product_name.strip():
            raise ValueError("product_name cannot be empty")
        if not self.product_type.strip():
            raise ValueError("product_type cannot be empty")
        
        # Validate product type
        valid_types = ["core", "supplemental", "conditional"]
        if self.product_type not in valid_types:
            raise ValueError(f"product_type must be one of {valid_types}")
        
        # Validate tier level
        if self.tier_level < 1 or self.tier_level > 3:
            raise ValueError("tier_level must be between 1 and 3")
        
        # Validate processing priority
        if self.processing_priority < 1 or self.processing_priority > 3:
            raise ValueError("processing_priority must be between 1 and 3")


@dataclass
class PackageProgram:
    """Program sub-tier within products for enhanced granularity"""
    program_id: str
    program_name: str
    program_code: str  # Short code like "CORE", "PLUS", "SELECT"
    description: str = ""  # Rich description for enhanced LLM processing
    parent_product_id: str = ""  # Links to parent product
    program_type: str = "standard"  # standard, enhanced, premium
    loan_limits: Dict[str, Any] = field(default_factory=dict)  # Loan amount limits
    rate_adjustments: List[str] = field(default_factory=list)  # Rate pricing adjustments
    feature_differences: List[str] = field(default_factory=list)  # How this differs from base product
    qualification_criteria: List[str] = field(default_factory=list)  # Specific qualification requirements
    processing_priority: int = 1  # 1=high, 2=medium, 3=low
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """Validate program fields"""
        if not self.program_id.strip():
            raise ValueError("program_id cannot be empty")
        if not self.program_name.strip():
            raise ValueError("program_name cannot be empty")
        if not self.program_code.strip():
            raise ValueError("program_code cannot be empty")


@dataclass
class DocumentDefinition:
    """Individual document within a product or program"""
    document_id: str
    document_type: str  # guidelines, matrix, rate_sheet
    document_name: str
    # Enhanced association support
    associated_to: str = "product"  # "product" or "program"
    parent_id: str = ""  # ID of parent product or program
    association_rules: Dict[str, Any] = field(default_factory=dict)  # Rules for association
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
    products: List[PackageProduct] = field(default_factory=list)
    documents: List[DocumentDefinition] = field(default_factory=list)  # Kept for backwards compatibility
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

    def add_product(self, product: PackageProduct) -> None:
        """Add a product to the package"""
        # Check for duplicate product IDs
        existing_ids = [prod.product_id for prod in self.products]
        if product.product_id in existing_ids:
            raise ValueError(f"Product ID {product.product_id} already exists in package")
        
        self.products.append(product)
        self.updated_at = datetime.now()

    def get_product_by_id(self, product_id: str) -> Optional[PackageProduct]:
        """Get a product by its ID"""
        for product in self.products:
            if product.product_id == product_id:
                return product
        return None

    def get_products_by_type(self, product_type: str) -> List[PackageProduct]:
        """Get all products of a specific type"""
        return [prod for prod in self.products if prod.product_type == product_type]

    def add_document(self, document: DocumentDefinition) -> None:
        """Add a document to the package (backwards compatibility)"""
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
    
    # Check if package has either products or documents
    has_products = len(package.products) > 0
    has_documents = len(package.documents) > 0
    
    if not has_products and not has_documents:
        errors.append("Package must contain at least one product or document")
    
    # Validate product IDs are unique
    if has_products:
        product_ids = [prod.product_id for prod in package.products]
        if len(product_ids) != len(set(product_ids)):
            errors.append("Product IDs must be unique within package")
        
        # Validate product types
        for prod in package.products:
            try:
                # This will raise an exception if validation fails
                prod.__post_init__()
            except ValueError as e:
                errors.append(f"Product {prod.product_id}: {str(e)}")
    
    # Validate document IDs are unique (backwards compatibility)
    if has_documents:
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
        if has_documents:
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