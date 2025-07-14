# Task 1: Unit tests for Document Package Data Models
# This file contains comprehensive tests for the package data models

import pytest
from datetime import datetime
import sys
import os

# Add the parent directory to the path to import backend modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from src.entities.document_package import (
    DocumentPackage,
    DocumentDefinition, 
    PackageRelationship,
    PackageStatus,
    PackageCategory,
    validate_package,
    create_package_id,
    is_valid_semantic_version
)


class TestPackageEnums:
    """Test the enum classes"""
    
    def test_package_status_values(self):
        """Test PackageStatus enum values"""
        assert PackageStatus.DRAFT.value == "DRAFT"
        assert PackageStatus.ACTIVE.value == "ACTIVE"
        assert PackageStatus.ARCHIVED.value == "ARCHIVED"
    
    def test_package_category_values(self):
        """Test PackageCategory enum values"""
        assert PackageCategory.NQM.value == "NQM"
        assert PackageCategory.RTL.value == "RTL"
        assert PackageCategory.SBC.value == "SBC"
        assert PackageCategory.CONV.value == "CONV"


class TestPackageRelationship:
    """Test PackageRelationship dataclass"""
    
    def test_package_relationship_creation(self):
        """Test creating a valid PackageRelationship"""
        rel = PackageRelationship(
            from_document="doc1",
            to_document="doc2", 
            relationship_type="ELABORATES",
            metadata={"connection_type": "policy_to_matrix"}
        )
        
        assert rel.from_document == "doc1"
        assert rel.to_document == "doc2"
        assert rel.relationship_type == "ELABORATES"
        assert rel.metadata["connection_type"] == "policy_to_matrix"
    
    def test_package_relationship_validation(self):
        """Test PackageRelationship validation"""
        # Test empty from_document
        with pytest.raises(ValueError, match="from_document cannot be empty"):
            PackageRelationship(
                from_document="",
                to_document="doc2",
                relationship_type="ELABORATES"
            )
        
        # Test empty to_document
        with pytest.raises(ValueError, match="to_document cannot be empty"):
            PackageRelationship(
                from_document="doc1",
                to_document="",
                relationship_type="ELABORATES"
            )
        
        # Test empty relationship_type
        with pytest.raises(ValueError, match="relationship_type cannot be empty"):
            PackageRelationship(
                from_document="doc1",
                to_document="doc2",
                relationship_type=""
            )


class TestDocumentDefinition:
    """Test DocumentDefinition dataclass"""
    
    def test_document_definition_creation(self):
        """Test creating a valid DocumentDefinition"""
        doc = DocumentDefinition(
            document_id="doc_001",
            document_type="guidelines",
            document_name="NQM Guidelines",
            required_sections=["Borrower Eligibility", "Income Documentation"],
            entity_types=["LOAN_PROGRAM", "BORROWER_TYPE"]
        )
        
        assert doc.document_id == "doc_001"
        assert doc.document_type == "guidelines"
        assert doc.document_name == "NQM Guidelines"
        assert doc.chunking_strategy == "hierarchical"  # default value
        assert len(doc.required_sections) == 2
        assert len(doc.entity_types) == 2
    
    def test_document_definition_validation(self):
        """Test DocumentDefinition validation"""
        # Test empty document_id
        with pytest.raises(ValueError, match="document_id cannot be empty"):
            DocumentDefinition(
                document_id="",
                document_type="guidelines",
                document_name="Test"
            )
        
        # Test invalid document_type
        with pytest.raises(ValueError, match="document_type must be one of"):
            DocumentDefinition(
                document_id="doc_001",
                document_type="invalid_type",
                document_name="Test"
            )
        
        # Test invalid chunking_strategy
        with pytest.raises(ValueError, match="chunking_strategy must be one of"):
            DocumentDefinition(
                document_id="doc_001",
                document_type="guidelines",
                document_name="Test",
                chunking_strategy="invalid_strategy"
            )
    
    def test_document_definition_valid_types(self):
        """Test valid document types"""
        valid_types = ["guidelines", "matrix", "rate_sheet"]
        
        for doc_type in valid_types:
            doc = DocumentDefinition(
                document_id="doc_001",
                document_type=doc_type,
                document_name="Test Document"
            )
            assert doc.document_type == doc_type


class TestDocumentPackage:
    """Test DocumentPackage dataclass"""
    
    def test_document_package_creation(self):
        """Test creating a valid DocumentPackage"""
        package = DocumentPackage(
            package_id="pkg_nqm_001",
            package_name="Test NQM Package",
            tenant_id="tenant_001",
            category=PackageCategory.NQM,
            version="1.0.0"
        )
        
        assert package.package_id == "pkg_nqm_001"
        assert package.package_name == "Test NQM Package"
        assert package.tenant_id == "tenant_001"
        assert package.category == PackageCategory.NQM
        assert package.version == "1.0.0"
        assert package.status == PackageStatus.DRAFT  # default value
        assert isinstance(package.created_at, datetime)
        assert len(package.documents) == 0  # default empty list
    
    def test_document_package_validation(self):
        """Test DocumentPackage validation"""
        # Test empty package_id
        with pytest.raises(ValueError, match="package_id cannot be empty"):
            DocumentPackage(
                package_id="",
                package_name="Test Package",
                tenant_id="tenant_001",
                category=PackageCategory.NQM,
                version="1.0.0"
            )
        
        # Test invalid version format
        with pytest.raises(ValueError, match="version must follow semantic versioning"):
            DocumentPackage(
                package_id="pkg_001",
                package_name="Test Package",
                tenant_id="tenant_001",
                category=PackageCategory.NQM,
                version="1.0"  # Missing patch version
            )
        
        # Test non-numeric version parts
        with pytest.raises(ValueError, match="version parts must be integers"):
            DocumentPackage(
                package_id="pkg_001",
                package_name="Test Package",
                tenant_id="tenant_001",
                category=PackageCategory.NQM,
                version="1.0.a"
            )
    
    def test_package_add_document(self):
        """Test adding documents to a package"""
        package = DocumentPackage(
            package_id="pkg_nqm_001",
            package_name="Test Package",
            tenant_id="tenant_001",
            category=PackageCategory.NQM,
            version="1.0.0"
        )
        
        doc = DocumentDefinition(
            document_id="doc_001",
            document_type="guidelines",
            document_name="Test Guidelines"
        )
        
        package.add_document(doc)
        
        assert len(package.documents) == 1
        assert package.documents[0].document_id == "doc_001"
    
    def test_package_duplicate_document_id(self):
        """Test adding duplicate document IDs"""
        package = DocumentPackage(
            package_id="pkg_nqm_001",
            package_name="Test Package",
            tenant_id="tenant_001",
            category=PackageCategory.NQM,
            version="1.0.0"
        )
        
        doc1 = DocumentDefinition(
            document_id="doc_001",
            document_type="guidelines",
            document_name="Test Guidelines 1"
        )
        
        doc2 = DocumentDefinition(
            document_id="doc_001",  # Same ID
            document_type="matrix",
            document_name="Test Matrix"
        )
        
        package.add_document(doc1)
        
        with pytest.raises(ValueError, match="Document ID doc_001 already exists"):
            package.add_document(doc2)
    
    def test_get_document_by_id(self):
        """Test retrieving document by ID"""
        package = DocumentPackage(
            package_id="pkg_nqm_001",
            package_name="Test Package",
            tenant_id="tenant_001",
            category=PackageCategory.NQM,
            version="1.0.0"
        )
        
        doc = DocumentDefinition(
            document_id="doc_001",
            document_type="guidelines",
            document_name="Test Guidelines"
        )
        
        package.add_document(doc)
        
        # Test existing document
        retrieved_doc = package.get_document_by_id("doc_001")
        assert retrieved_doc is not None
        assert retrieved_doc.document_id == "doc_001"
        
        # Test non-existing document
        missing_doc = package.get_document_by_id("doc_999")
        assert missing_doc is None
    
    def test_get_documents_by_type(self):
        """Test retrieving documents by type"""
        package = DocumentPackage(
            package_id="pkg_nqm_001",
            package_name="Test Package",
            tenant_id="tenant_001",
            category=PackageCategory.NQM,
            version="1.0.0"
        )
        
        doc1 = DocumentDefinition(
            document_id="doc_001",
            document_type="guidelines",
            document_name="Guidelines 1"
        )
        
        doc2 = DocumentDefinition(
            document_id="doc_002",
            document_type="matrix",
            document_name="Matrix 1"
        )
        
        doc3 = DocumentDefinition(
            document_id="doc_003",
            document_type="guidelines",
            document_name="Guidelines 2"
        )
        
        package.add_document(doc1)
        package.add_document(doc2)
        package.add_document(doc3)
        
        guidelines_docs = package.get_documents_by_type("guidelines")
        matrix_docs = package.get_documents_by_type("matrix")
        
        assert len(guidelines_docs) == 2
        assert len(matrix_docs) == 1
        assert guidelines_docs[0].document_type == "guidelines"
        assert matrix_docs[0].document_type == "matrix"


class TestPackageValidation:
    """Test package validation functions"""
    
    def test_validate_empty_package(self):
        """Test validation of empty package"""
        package = DocumentPackage(
            package_id="pkg_nqm_001",
            package_name="Test Package",
            tenant_id="tenant_001",
            category=PackageCategory.NQM,
            version="1.0.0"
        )
        
        errors = validate_package(package)
        
        # Should have errors for empty documents and missing required documents
        assert len(errors) > 0
        assert any("Package must contain at least one document" in error for error in errors)
    
    def test_validate_valid_package(self):
        """Test validation of valid package"""
        package = DocumentPackage(
            package_id="pkg_nqm_001",
            package_name="Test Package",
            tenant_id="tenant_001",
            category=PackageCategory.NQM,
            version="1.0.0"
        )
        
        # Add required documents for NQM
        guidelines_doc = DocumentDefinition(
            document_id="doc_guidelines",
            document_type="guidelines",
            document_name="NQM Guidelines"
        )
        
        matrix_doc = DocumentDefinition(
            document_id="doc_matrix",
            document_type="matrix",
            document_name="NQM Matrix"
        )
        
        package.add_document(guidelines_doc)
        package.add_document(matrix_doc)
        
        errors = validate_package(package)
        
        # Should have no errors
        assert len(errors) == 0
    
    def test_validate_duplicate_document_ids(self):
        """Test validation catches duplicate document IDs"""
        package = DocumentPackage(
            package_id="pkg_nqm_001",
            package_name="Test Package",
            tenant_id="tenant_001",
            category=PackageCategory.NQM,
            version="1.0.0"
        )
        
        # Manually add documents with duplicate IDs (bypassing add_document validation)
        doc1 = DocumentDefinition(
            document_id="doc_001",
            document_type="guidelines",
            document_name="Guidelines"
        )
        
        doc2 = DocumentDefinition(
            document_id="doc_001",  # Duplicate ID
            document_type="matrix",
            document_name="Matrix"
        )
        
        package.documents.append(doc1)
        package.documents.append(doc2)
        
        errors = validate_package(package)
        
        assert any("Document IDs must be unique" in error for error in errors)


class TestUtilityFunctions:
    """Test utility functions"""
    
    def test_create_package_id(self):
        """Test package ID creation"""
        package_id = create_package_id(PackageCategory.NQM, "abc123")
        assert package_id == "pkg_nqm_abc123"
        
        package_id = create_package_id(PackageCategory.RTL, "def456")
        assert package_id == "pkg_rtl_def456"
    
    def test_is_valid_semantic_version(self):
        """Test semantic version validation"""
        # Valid versions
        assert is_valid_semantic_version("1.0.0") == True
        assert is_valid_semantic_version("10.20.30") == True
        assert is_valid_semantic_version("0.0.1") == True
        
        # Invalid versions
        assert is_valid_semantic_version("1.0") == False
        assert is_valid_semantic_version("1.0.0.0") == False
        assert is_valid_semantic_version("1.0.a") == False
        assert is_valid_semantic_version("a.b.c") == False
        assert is_valid_semantic_version("") == False


class TestComplexScenarios:
    """Test complex package scenarios"""
    
    def test_complete_nqm_package(self):
        """Test creating a complete NQM package with relationships"""
        package = DocumentPackage(
            package_id="pkg_nqm_titanium_001",
            package_name="NQM Titanium Advantage Package",
            tenant_id="the_g1_group",
            category=PackageCategory.NQM,
            version="2.1.0",
            status=PackageStatus.ACTIVE,
            created_by="system",
            template_type="NQM_STANDARD"
        )
        
        # Add guidelines document
        guidelines_doc = DocumentDefinition(
            document_id="doc_guidelines_001",
            document_type="guidelines",
            document_name="NQM Guidelines",
            required_sections=["Borrower Eligibility", "Income Documentation", "Asset Requirements"],
            entity_types=["LOAN_PROGRAM", "BORROWER_TYPE", "REQUIREMENT"],
            quality_thresholds={"navigation_accuracy": 0.95, "decision_completeness": 1.0}
        )
        
        # Add matrix document
        matrix_doc = DocumentDefinition(
            document_id="doc_matrix_001",
            document_type="matrix",
            document_name="NQM Matrix",
            matrix_configuration={"matrix_types": ["qualification", "pricing"], "dimensions": ["fico_score", "ltv_ratio"]},
            quality_thresholds={"extraction_accuracy": 0.90}
        )
        
        package.add_document(guidelines_doc)
        package.add_document(matrix_doc)
        
        # Add relationship
        relationship = PackageRelationship(
            from_document="doc_guidelines_001",
            to_document="doc_matrix_001",
            relationship_type="ELABORATES",
            metadata={"connection_type": "policy_to_matrix"}
        )
        
        package.relationships.append(relationship)
        
        # Validate the complete package
        errors = validate_package(package)
        assert len(errors) == 0
        
        # Test package structure
        assert len(package.documents) == 2
        assert len(package.relationships) == 1
        assert package.get_documents_by_type("guidelines")[0].document_name == "NQM Guidelines"
        assert package.get_documents_by_type("matrix")[0].document_name == "NQM Matrix"