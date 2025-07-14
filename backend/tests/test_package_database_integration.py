# Task 5: Integration tests for Package Database Schema
# This file contains tests for the complete package database integration

import pytest
from unittest.mock import Mock, MagicMock
from datetime import datetime
import sys
import os
import json

# Add the parent directory to the path to import backend modules
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from src.graphDB_dataAccess import graphDBdataAccess
from src.package_manager import PackageManager
from src.package_versioning import PackageVersionManager, ChangeType
from src.entities.document_package import (
    DocumentPackage,
    DocumentDefinition,
    PackageRelationship,
    PackageStatus,
    PackageCategory
)


class TestPackageDatabaseIntegration:
    """Test complete package database integration"""
    
    def setup_method(self):
        """Set up test fixtures"""
        # Mock Neo4j graph and database access
        self.mock_graph = Mock()
        self.graph_db = graphDBdataAccess(self.mock_graph)
        
        # Mock the execute_query method to return expected results
        self.graph_db.execute_query = Mock()
        
        # Set up managers
        self.package_manager = PackageManager(self.graph_db)
        self.version_manager = PackageVersionManager(self.graph_db)
    
    def test_create_package_node(self):
        """Test creating a DocumentPackage node"""
        package_data = {
            "package_id": "pkg_nqm_001",
            "package_name": "Test NQM Package",
            "tenant_id": "tenant_001",
            "category": "NQM",
            "version": "1.0.0",
            "status": "DRAFT",
            "created_by": "test_user",
            "template_type": "NQM_STANDARD",
            "created_at": datetime.now(),
            "updated_at": datetime.now(),
            "template_mappings": {"test": "mapping"},
            "validation_rules": {"test": "rule"}
        }
        
        # Mock successful creation
        self.graph_db.execute_query.return_value = [{"package_id": "pkg_nqm_001"}]
        
        result = self.graph_db.create_package_node(package_data)
        
        assert result is True
        self.graph_db.execute_query.assert_called_once()
        
        # Verify the query was called with correct parameters
        call_args = self.graph_db.execute_query.call_args
        assert "CREATE (p:DocumentPackage" in call_args[0][0]
        assert call_args[1]["package_id"] == "pkg_nqm_001"
        assert call_args[1]["package_name"] == "Test NQM Package"
    
    def test_get_package_node(self):
        """Test retrieving a DocumentPackage node"""
        # Mock database response
        mock_response = [{
            "package_id": "pkg_nqm_001",
            "package_name": "Test NQM Package",
            "tenant_id": "tenant_001",
            "category": "NQM",
            "version": "1.0.0",
            "status": "DRAFT",
            "created_by": "test_user",
            "template_type": "NQM_STANDARD",
            "created_at": "2023-01-01T00:00:00",
            "updated_at": "2023-01-01T00:00:00",
            "template_mappings": '{"test": "mapping"}',
            "validation_rules": '{"test": "rule"}'
        }]
        
        self.graph_db.execute_query.return_value = mock_response
        
        result = self.graph_db.get_package_node("pkg_nqm_001")
        
        assert result is not None
        assert result["package_id"] == "pkg_nqm_001"
        assert result["package_name"] == "Test NQM Package"
        assert isinstance(result["template_mappings"], dict)
        assert isinstance(result["validation_rules"], dict)
    
    def test_create_package_document(self):
        """Test creating a PackageDocument node"""
        document_data = {
            "document_id": "doc_001",
            "document_type": "guidelines",
            "document_name": "Test Guidelines",
            "expected_structure": {"chapters": ["Chapter 1"]},
            "required_sections": ["Section 1"],
            "optional_sections": ["Section 2"],
            "chunking_strategy": "hierarchical",
            "entity_types": ["ENTITY_TYPE"],
            "matrix_configuration": None,
            "validation_schema": {"test": "schema"},
            "quality_thresholds": {"accuracy": 0.95}
        }
        
        # Mock successful creation
        self.graph_db.execute_query.return_value = [{"document_id": "doc_001"}]
        
        result = self.graph_db.create_package_document("pkg_nqm_001", document_data)
        
        assert result is True
        self.graph_db.execute_query.assert_called_once()
        
        # Verify the query includes CONTAINS relationship
        call_args = self.graph_db.execute_query.call_args
        assert "CREATE (p)-[:CONTAINS]->(d)" in call_args[0][0]
    
    def test_get_package_documents(self):
        """Test retrieving package documents"""
        # Mock database response
        mock_response = [{
            "document_id": "doc_001",
            "document_type": "guidelines",
            "document_name": "Test Guidelines",
            "expected_structure": '{"chapters": ["Chapter 1"]}',
            "required_sections": '["Section 1"]',
            "optional_sections": '["Section 2"]',
            "chunking_strategy": "hierarchical",
            "entity_types": '["ENTITY_TYPE"]',
            "matrix_configuration": None,
            "validation_schema": '{"test": "schema"}',
            "quality_thresholds": '{"accuracy": 0.95}'
        }]
        
        self.graph_db.execute_query.return_value = mock_response
        
        result = self.graph_db.get_package_documents("pkg_nqm_001")
        
        assert len(result) == 1
        assert result[0]["document_id"] == "doc_001"
        assert isinstance(result[0]["expected_structure"], dict)
        assert isinstance(result[0]["required_sections"], list)
    
    def test_create_package_relationship(self):
        """Test creating package relationships"""
        relationship_data = {
            "from_document": "doc_guidelines",
            "to_document": "doc_matrix",
            "relationship_type": "ELABORATES",
            "metadata": {"connection_type": "policy_to_matrix"}
        }
        
        # Mock successful creation
        self.graph_db.execute_query.return_value = [{"r": "relationship"}]
        
        result = self.graph_db.create_package_relationship("pkg_nqm_001", relationship_data)
        
        assert result is True
        self.graph_db.execute_query.assert_called_once()
        
        # Verify the query creates RELATIONSHIP between documents
        call_args = self.graph_db.execute_query.call_args
        assert "CREATE (from_doc)-[r:RELATIONSHIP" in call_args[0][0]
    
    def test_create_version_record(self):
        """Test creating version records"""
        version_data = {
            "version": "1.1.0",
            "change_type": "MINOR",
            "changes": ["Added new feature"],
            "created_at": datetime.now(),
            "created_by": "test_user",
            "metadata": {"test": "metadata"}
        }
        
        # Mock successful creation
        self.graph_db.execute_query.return_value = [{"version": "1.1.0"}]
        
        result = self.graph_db.create_version_record("pkg_nqm_001", version_data)
        
        assert result is True
        self.graph_db.execute_query.assert_called_once()
        
        # Verify VERSION_OF relationship is created
        call_args = self.graph_db.execute_query.call_args
        assert "CREATE (p)-[:VERSION_OF]->(v)" in call_args[0][0]
    
    def test_create_package_snapshot(self):
        """Test creating package snapshots"""
        snapshot_data = {
            "package_id": "pkg_nqm_001",
            "package_name": "Test Package",
            "documents": [],
            "relationships": [],
            "snapshot_created": datetime.now().isoformat()
        }
        
        # Mock successful creation
        self.graph_db.execute_query.return_value = [{"s": "snapshot"}]
        
        result = self.graph_db.create_package_snapshot("pkg_nqm_001", "1.1.0", snapshot_data)
        
        assert result is True
        self.graph_db.execute_query.assert_called_once()
        
        # Verify SNAPSHOT relationship is created
        call_args = self.graph_db.execute_query.call_args
        assert "CREATE (v)-[:SNAPSHOT]->(s)" in call_args[0][0]
    
    def test_list_packages_with_filters(self):
        """Test listing packages with filters"""
        # Mock database response
        mock_response = [
            {
                "package_id": "pkg_nqm_001",
                "package_name": "NQM Package 1",
                "tenant_id": "tenant_001",
                "category": "NQM",
                "version": "1.0.0",
                "status": "ACTIVE",
                "created_by": "user1",
                "created_at": "2023-01-01T00:00:00",
                "updated_at": "2023-01-01T00:00:00"
            },
            {
                "package_id": "pkg_nqm_002",
                "package_name": "NQM Package 2",
                "tenant_id": "tenant_001",
                "category": "NQM",
                "version": "1.2.0",
                "status": "DRAFT",
                "created_by": "user2",
                "created_at": "2023-01-02T00:00:00",
                "updated_at": "2023-01-02T00:00:00"
            }
        ]
        
        self.graph_db.execute_query.return_value = mock_response
        
        # Test with filters
        result = self.graph_db.list_packages(
            tenant_id="tenant_001",
            category="NQM",
            status="ACTIVE"
        )
        
        assert len(result) == 2  # Mock returns all, filtering happens in query
        self.graph_db.execute_query.assert_called_once()
        
        # Verify query includes WHERE clauses
        call_args = self.graph_db.execute_query.call_args
        assert "WHERE" in call_args[0][0]
        assert call_args[1]["tenant_id"] == "tenant_001"
        assert call_args[1]["category"] == "NQM"
        assert call_args[1]["status"] == "ACTIVE"
    
    def test_package_exists(self):
        """Test checking if package exists"""
        # Mock package exists
        self.graph_db.execute_query.return_value = [{"count": 1}]
        
        result = self.graph_db.package_exists("pkg_nqm_001")
        
        assert result is True
        self.graph_db.execute_query.assert_called_once()
        
        # Test package doesn't exist
        self.graph_db.execute_query.return_value = [{"count": 0}]
        
        result = self.graph_db.package_exists("pkg_not_found")
        
        assert result is False
    
    def test_get_package_statistics(self):
        """Test getting package statistics"""
        # Mock database response for specific package
        mock_response = [{
            "package_id": "pkg_nqm_001",
            "document_count": 2,
            "version_count": 3
        }]
        
        self.graph_db.execute_query.return_value = mock_response
        
        result = self.graph_db.get_package_statistics("pkg_nqm_001")
        
        assert result["package_id"] == "pkg_nqm_001"
        assert result["document_count"] == 2
        assert result["version_count"] == 3
        
        # Test global statistics
        mock_global_response = [{
            "total_packages": 10,
            "total_documents": 25,
            "total_versions": 30
        }]
        
        self.graph_db.execute_query.return_value = mock_global_response
        
        result = self.graph_db.get_package_statistics()
        
        assert result["total_packages"] == 10
        assert result["total_documents"] == 25
        assert result["total_versions"] == 30


class TestPackageManagerDatabaseIntegration:
    """Test PackageManager integration with database"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.mock_graph = Mock()
        self.graph_db = graphDBdataAccess(self.mock_graph)
        self.package_manager = PackageManager(self.graph_db)
        
        # Mock database methods
        self.graph_db.execute_query = Mock()
        self.graph_db.package_exists = Mock()
        self.graph_db.create_package_node = Mock()
        self.graph_db.create_package_document = Mock()
        self.graph_db.create_package_relationship = Mock()
        self.graph_db.get_package_node = Mock()
        self.graph_db.get_package_documents = Mock()
        self.graph_db.get_package_relationships = Mock()
    
    def test_package_manager_store_integration(self):
        """Test PackageManager storing packages in database"""
        # Create test package
        package = DocumentPackage(
            package_id="pkg_nqm_001",
            package_name="Test Package",
            tenant_id="tenant_001",
            category=PackageCategory.NQM,
            version="1.0.0",
            status=PackageStatus.DRAFT,
            created_by="test_user"
        )
        
        # Add document
        doc = DocumentDefinition(
            document_id="doc_001",
            document_type="guidelines",
            document_name="Test Guidelines"
        )
        package.add_document(doc)
        
        # Add relationship
        rel = PackageRelationship(
            from_document="doc_001",
            to_document="doc_002",
            relationship_type="REFERENCES",
            metadata={"test": "metadata"}
        )
        package.relationships.append(rel)
        
        # Mock database responses
        self.graph_db.package_exists.return_value = False
        self.graph_db.create_package_node.return_value = True
        self.graph_db.create_package_document.return_value = True
        self.graph_db.create_package_relationship.return_value = True
        
        # Test storage
        self.package_manager._store_package_in_db(package)
        
        # Verify database calls
        self.graph_db.package_exists.assert_called_once_with("pkg_nqm_001")
        self.graph_db.create_package_node.assert_called_once()
        self.graph_db.create_package_document.assert_called_once()
        self.graph_db.create_package_relationship.assert_called_once()
    
    def test_package_manager_load_integration(self):
        """Test PackageManager loading packages from database"""
        # Mock database responses
        package_data = {
            "package_id": "pkg_nqm_001",
            "package_name": "Test Package",
            "tenant_id": "tenant_001",
            "category": "NQM",
            "version": "1.0.0",
            "status": "DRAFT",
            "created_by": "test_user",
            "template_type": "",
            "created_at": "2023-01-01T00:00:00",
            "updated_at": "2023-01-01T00:00:00",
            "template_mappings": {},
            "validation_rules": {}
        }
        
        documents_data = [{
            "document_id": "doc_001",
            "document_type": "guidelines",
            "document_name": "Test Guidelines",
            "expected_structure": {},
            "required_sections": [],
            "optional_sections": [],
            "chunking_strategy": "hierarchical",
            "entity_types": [],
            "matrix_configuration": None,
            "validation_schema": {},
            "quality_thresholds": {}
        }]
        
        relationships_data = [{
            "from_document": "doc_001",
            "to_document": "doc_002",
            "relationship_type": "REFERENCES",
            "metadata": {}
        }]
        
        self.graph_db.get_package_node.return_value = package_data
        self.graph_db.get_package_documents.return_value = documents_data
        self.graph_db.get_package_relationships.return_value = relationships_data
        
        # Test deserialization
        package = self.package_manager._deserialize_package(package_data)
        
        assert package.package_id == "pkg_nqm_001"
        assert package.package_name == "Test Package"
        assert package.category == PackageCategory.NQM
        assert len(package.documents) == 1
        assert package.documents[0].document_id == "doc_001"


class TestPackageVersionManagerDatabaseIntegration:
    """Test PackageVersionManager integration with database"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.mock_graph = Mock()
        self.graph_db = graphDBdataAccess(self.mock_graph)
        self.version_manager = PackageVersionManager(self.graph_db)
        
        # Mock database methods
        self.graph_db.create_version_record = Mock()
        self.graph_db.create_package_snapshot = Mock()
        self.graph_db.get_version_history = Mock()
        self.graph_db.get_package_snapshot = Mock()
    
    def test_version_manager_store_integration(self):
        """Test PackageVersionManager storing versions in database"""
        from src.package_versioning import VersionRecord
        
        # Create version record
        version_record = VersionRecord(
            version="1.1.0",
            change_type=ChangeType.MINOR,
            changes=["Added new feature"],
            created_at=datetime.now(),
            created_by="test_user",
            metadata={"test": "metadata"}
        )
        
        # Mock database response
        self.graph_db.create_version_record.return_value = True
        
        # Test storage
        self.version_manager._store_version_record("pkg_nqm_001", version_record)
        
        # Verify database call
        self.graph_db.create_version_record.assert_called_once()
        call_args = self.graph_db.create_version_record.call_args
        assert call_args[0][0] == "pkg_nqm_001"
        assert call_args[0][1]["version"] == "1.1.0"
        assert call_args[0][1]["change_type"] == "MINOR"
    
    def test_version_manager_retrieve_integration(self):
        """Test PackageVersionManager retrieving versions from database"""
        # Mock database response
        mock_history = [
            {
                "version": "1.1.0",
                "change_type": "MINOR",
                "changes": '["Added new feature"]',
                "created_at": "2023-01-01T00:00:00",
                "created_by": "test_user",
                "metadata": '{"test": "metadata"}'
            },
            {
                "version": "1.0.0",
                "change_type": "PATCH",
                "changes": '["Initial version"]',
                "created_at": "2023-01-01T00:00:00",
                "created_by": "test_user",
                "metadata": '{}'
            }
        ]
        
        self.graph_db.get_version_history.return_value = mock_history
        
        # Test retrieval
        history = self.version_manager._retrieve_version_history("pkg_nqm_001")
        
        assert len(history) == 2
        assert history[0]["version"] == "1.1.0"
        assert isinstance(history[0]["changes"], str)  # Still JSON string from DB
        
        # Verify database call
        self.graph_db.get_version_history.assert_called_once_with("pkg_nqm_001")


class TestPackageSchemaMigration:
    """Test package schema migration and validation"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.mock_graph = Mock()
        self.graph_db = graphDBdataAccess(self.mock_graph)
        self.graph_db.execute_query = Mock()
    
    def test_migrate_package_schema(self):
        """Test package schema migration"""
        # Mock successful migration
        self.graph_db.execute_query.return_value = []
        
        result = self.graph_db.migrate_package_schema()
        
        assert result is True
        
        # Verify multiple queries were executed (indexes and constraints)
        assert self.graph_db.execute_query.call_count >= 6  # At least 6 index queries
    
    def test_validate_package_schema(self):
        """Test package schema validation"""
        # Mock schema queries
        self.graph_db.execute_query.side_effect = [
            [],  # SHOW INDEXES
            []   # SHOW CONSTRAINTS
        ]
        
        result = self.graph_db.validate_package_schema()
        
        assert isinstance(result, dict)
        assert "valid" in result
        assert "issues" in result
        assert "recommendations" in result
        
        # Verify schema validation queries were called
        assert self.graph_db.execute_query.call_count == 2
    
    def test_cleanup_orphaned_package_data(self):
        """Test cleanup of orphaned package data"""
        # Mock cleanup results
        self.graph_db.execute_query.side_effect = [
            [{"count": 2}],  # Orphaned documents
            [{"count": 1}],  # Orphaned versions
            [{"count": 0}]   # Orphaned snapshots
        ]
        
        result = self.graph_db.cleanup_orphaned_package_data()
        
        assert result["orphaned_documents"] == 2
        assert result["orphaned_versions"] == 1
        assert result["orphaned_snapshots"] == 0
        
        # Verify cleanup queries were executed
        assert self.graph_db.execute_query.call_count == 3


class TestEndToEndPackageWorkflow:
    """Test complete end-to-end package workflow"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.mock_graph = Mock()
        self.graph_db = graphDBdataAccess(self.mock_graph)
        
        # Mock all database methods to simulate successful operations
        self.graph_db.execute_query = Mock()
        self.graph_db.package_exists = Mock(return_value=False)
        self.graph_db.create_package_node = Mock(return_value=True)
        self.graph_db.create_package_document = Mock(return_value=True)
        self.graph_db.create_package_relationship = Mock(return_value=True)
        self.graph_db.create_version_record = Mock(return_value=True)
        self.graph_db.create_package_snapshot = Mock(return_value=True)
        
        self.package_manager = PackageManager(self.graph_db)
        self.version_manager = PackageVersionManager(self.graph_db)
    
    def test_complete_package_lifecycle(self):
        """Test complete package lifecycle with database integration"""
        # Step 1: Create package
        package_config = {
            'package_name': 'End-to-End Test Package',
            'tenant_id': 'tenant_001',
            'category': 'NQM',
            'created_by': 'test_user',
            'documents': [
                {
                    'document_type': 'guidelines',
                    'document_name': 'NQM Guidelines',
                    'required_sections': ['Borrower Eligibility'],
                    'entity_types': ['LOAN_PROGRAM']
                },
                {
                    'document_type': 'matrix',
                    'document_name': 'NQM Matrix',
                    'matrix_configuration': {'matrix_types': ['qualification']}
                }
            ],
            'relationships': [
                {
                    'from_document': 'guidelines',
                    'to_document': 'matrix',
                    'relationship_type': 'ELABORATES',
                    'metadata': {'connection_type': 'policy_to_matrix'}
                }
            ]
        }
        
        # Create package
        package = self.package_manager.create_package(package_config)
        
        assert package is not None
        assert package.package_name == 'End-to-End Test Package'
        assert len(package.documents) == 2
        assert len(package.relationships) == 1
        
        # Verify database storage was called
        self.graph_db.create_package_node.assert_called_once()
        assert self.graph_db.create_package_document.call_count == 2
        self.graph_db.create_package_relationship.assert_called_once()
        
        # Step 2: Create version
        new_version = self.version_manager.create_version(
            package, ChangeType.MINOR, ['Added new section'], 'test_user'
        )
        
        assert new_version == '1.1.0'
        assert package.version == '1.1.0'
        
        # Verify version storage was called
        self.graph_db.create_version_record.assert_called_once()
        self.graph_db.create_package_snapshot.assert_called_once()
        
        print("✅ Complete package lifecycle test passed")


# Test execution helper
if __name__ == "__main__":
    # This allows running the tests directly
    pytest.main([__file__, "-v"])