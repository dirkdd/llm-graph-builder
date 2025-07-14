# Task 2: Unit tests for Package Manager Core
# This file contains comprehensive tests for the PackageManager class

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime
import sys
import os

# Add the parent directory to the path to import backend modules
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from src.package_manager import PackageManager
from src.entities.document_package import (
    DocumentPackage,
    DocumentDefinition,
    PackageRelationship,
    PackageStatus,
    PackageCategory
)
from src.shared.llm_graph_builder_exception import LLMGraphBuilderException


class TestPackageManager:
    """Test PackageManager class functionality"""
    
    def setup_method(self):
        """Set up test fixtures"""
        # Mock database connection
        self.mock_graph_db = Mock()
        self.package_manager = PackageManager(self.mock_graph_db)
    
    def test_package_manager_initialization(self):
        """Test PackageManager initialization"""
        assert self.package_manager.graph_db == self.mock_graph_db
        assert self.package_manager.logger is not None
    
    def test_create_package_basic(self):
        """Test basic package creation"""
        package_config = {
            'package_name': 'Test NQM Package',
            'tenant_id': 'tenant_001',
            'category': 'NQM',
            'created_by': 'test_user'
        }
        
        # Mock the database storage method
        self.package_manager._store_package_in_db = Mock()
        
        package = self.package_manager.create_package(package_config)
        
        assert package.package_name == 'Test NQM Package'
        assert package.tenant_id == 'tenant_001'
        assert package.category == PackageCategory.NQM
        assert package.version == '1.0.0'
        assert package.status == PackageStatus.DRAFT
        assert package.created_by == 'test_user'
        assert package.package_id.startswith('pkg_nqm_')
        
        # Verify database storage was called
        self.package_manager._store_package_in_db.assert_called_once()
    
    def test_create_package_with_documents(self):
        """Test package creation with documents"""
        package_config = {
            'package_name': 'Test Package with Documents',
            'tenant_id': 'tenant_001',
            'category': 'NQM',
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
            ]
        }
        
        self.package_manager._store_package_in_db = Mock()
        
        package = self.package_manager.create_package(package_config)
        
        assert len(package.documents) == 2
        assert package.documents[0].document_type == 'guidelines'
        assert package.documents[1].document_type == 'matrix'
        assert package.documents[0].document_name == 'NQM Guidelines'
        assert package.documents[1].document_name == 'NQM Matrix'
    
    def test_create_package_with_relationships(self):
        """Test package creation with relationships"""
        package_config = {
            'package_name': 'Test Package with Relationships',
            'tenant_id': 'tenant_001',
            'category': 'NQM',
            'documents': [
                {
                    'document_id': 'doc_guidelines',
                    'document_type': 'guidelines',
                    'document_name': 'Guidelines'
                },
                {
                    'document_id': 'doc_matrix',
                    'document_type': 'matrix',
                    'document_name': 'Matrix'
                }
            ],
            'relationships': [
                {
                    'from_document': 'doc_guidelines',
                    'to_document': 'doc_matrix',
                    'relationship_type': 'ELABORATES',
                    'metadata': {'connection_type': 'policy_to_matrix'}
                }
            ]
        }
        
        self.package_manager._store_package_in_db = Mock()
        
        package = self.package_manager.create_package(package_config)
        
        assert len(package.relationships) == 1
        assert package.relationships[0].from_document == 'doc_guidelines'
        assert package.relationships[0].to_document == 'doc_matrix'
        assert package.relationships[0].relationship_type == 'ELABORATES'
        assert package.relationships[0].metadata['connection_type'] == 'policy_to_matrix'
    
    def test_create_package_validation_errors(self):
        """Test package creation validation errors"""
        # Test missing required fields
        invalid_configs = [
            {},  # Empty config
            {'package_name': 'Test'},  # Missing tenant_id and category
            {'package_name': 'Test', 'tenant_id': 'tenant'},  # Missing category
            {'package_name': '', 'tenant_id': 'tenant', 'category': 'NQM'},  # Empty name
            {'package_name': 'Test', 'tenant_id': 'tenant', 'category': 'INVALID'},  # Invalid category
        ]
        
        for config in invalid_configs:
            with pytest.raises(ValueError):
                self.package_manager.create_package(config)
    
    def test_load_package_not_found(self):
        """Test loading non-existent package"""
        # Mock database to return None (package not found)
        self.package_manager._retrieve_package_from_db = Mock(return_value=None)
        
        with pytest.raises(ValueError, match="Package pkg_not_found not found"):
            self.package_manager.load_package('pkg_not_found')
    
    def test_load_package_success(self):
        """Test successful package loading"""
        # Mock package data
        mock_package_data = {
            'package_id': 'pkg_nqm_001',
            'package_name': 'Test Package',
            'tenant_id': 'tenant_001',
            'category': 'NQM',
            'version': '1.0.0'
        }
        
        # Mock database methods
        self.package_manager._retrieve_package_from_db = Mock(return_value=mock_package_data)
        self.package_manager._deserialize_package = Mock(return_value=Mock())
        self.package_manager._load_package_relationships = Mock(return_value=[])
        
        # Mock the returned package
        mock_package = DocumentPackage(
            package_id='pkg_nqm_001',
            package_name='Test Package',
            tenant_id='tenant_001',
            category=PackageCategory.NQM,
            version='1.0.0'
        )
        self.package_manager._deserialize_package.return_value = mock_package
        
        package = self.package_manager.load_package('pkg_nqm_001')
        
        assert package == mock_package
        self.package_manager._retrieve_package_from_db.assert_called_once_with('pkg_nqm_001')
        self.package_manager._deserialize_package.assert_called_once_with(mock_package_data)
        self.package_manager._load_package_relationships.assert_called_once_with('pkg_nqm_001')
    
    def test_update_package_basic(self):
        """Test basic package update"""
        # Create a package to update
        mock_package = DocumentPackage(
            package_id='pkg_nqm_001',
            package_name='Original Name',
            tenant_id='tenant_001',
            category=PackageCategory.NQM,
            version='1.0.0'
        )
        
        # Mock load_package to return our mock package
        self.package_manager.load_package = Mock(return_value=mock_package)
        self.package_manager._store_package_in_db = Mock()
        
        updates = {
            'package_name': 'Updated Name',
            'status': 'ACTIVE',
            'version_type': 'MINOR'
        }
        
        updated_package = self.package_manager.update_package('pkg_nqm_001', updates)
        
        assert updated_package.package_name == 'Updated Name'
        assert updated_package.status == PackageStatus.ACTIVE
        assert updated_package.version == '1.1.0'  # Minor version increment
        
        self.package_manager._store_package_in_db.assert_called_once()
    
    def test_update_package_invalid_changes(self):
        """Test package update with invalid changes"""
        mock_package = DocumentPackage(
            package_id='pkg_nqm_001',
            package_name='Test Package',
            tenant_id='tenant_001',
            category=PackageCategory.NQM,
            version='1.0.0'
        )
        
        self.package_manager.load_package = Mock(return_value=mock_package)
        
        # Test changing category (should fail)
        invalid_updates = {
            'category': 'RTL'
        }
        
        with pytest.raises(ValueError, match="Cannot change package category"):
            self.package_manager.update_package('pkg_nqm_001', invalid_updates)
        
        # Test changing tenant_id (should fail)
        invalid_updates = {
            'tenant_id': 'different_tenant'
        }
        
        with pytest.raises(ValueError, match="Cannot change tenant_id"):
            self.package_manager.update_package('pkg_nqm_001', invalid_updates)
    
    def test_clone_package_basic(self):
        """Test basic package cloning"""
        # Create source package
        source_package = DocumentPackage(
            package_id='pkg_nqm_001',
            package_name='Source Package',
            tenant_id='tenant_001',
            category=PackageCategory.NQM,
            version='2.1.0',
            status=PackageStatus.ACTIVE,
            template_type='NQM_STANDARD'
        )
        
        # Add a document to source package
        doc = DocumentDefinition(
            document_id='doc_001',
            document_type='guidelines',
            document_name='Source Guidelines'
        )
        source_package.add_document(doc)
        
        # Mock load_package and store methods
        self.package_manager.load_package = Mock(return_value=source_package)
        self.package_manager._store_package_in_db = Mock()
        
        cloned_package = self.package_manager.clone_package('pkg_nqm_001', 'Cloned Package')
        
        # Verify cloned package properties
        assert cloned_package.package_name == 'Cloned Package'
        assert cloned_package.tenant_id == source_package.tenant_id
        assert cloned_package.category == source_package.category
        assert cloned_package.version == '1.0.0'  # Reset to 1.0.0
        assert cloned_package.status == PackageStatus.DRAFT  # Reset to draft
        assert cloned_package.template_type == source_package.template_type
        assert cloned_package.package_id != source_package.package_id  # New ID
        assert cloned_package.package_id.startswith('pkg_nqm_')
        
        # Verify documents were cloned
        assert len(cloned_package.documents) == 1
        assert cloned_package.documents[0].document_name == 'Source Guidelines'
        assert cloned_package.documents[0].document_id != doc.document_id  # New ID
        
        self.package_manager._store_package_in_db.assert_called_once()
    
    def test_clone_package_with_modifications(self):
        """Test package cloning with modifications"""
        source_package = DocumentPackage(
            package_id='pkg_nqm_001',
            package_name='Source Package',
            tenant_id='tenant_001',
            category=PackageCategory.NQM,
            version='1.0.0'
        )
        
        self.package_manager.load_package = Mock(return_value=source_package)
        self.package_manager._store_package_in_db = Mock()
        
        modifications = {
            'category': 'RTL',
            'created_by': 'clone_user',
            'customizations': {
                'additional_sections': ['New Section']
            }
        }
        
        cloned_package = self.package_manager.clone_package(
            'pkg_nqm_001', 'Modified Clone', modifications
        )
        
        assert cloned_package.category == PackageCategory.RTL
        assert cloned_package.created_by == 'clone_user'
        assert cloned_package.package_id.startswith('pkg_rtl_')  # New category prefix
    
    def test_delete_package_success(self):
        """Test successful package deletion"""
        mock_package = DocumentPackage(
            package_id='pkg_nqm_001',
            package_name='Test Package',
            tenant_id='tenant_001',
            category=PackageCategory.NQM,
            version='1.0.0',
            status=PackageStatus.DRAFT  # Draft can be deleted
        )
        
        self.package_manager.load_package = Mock(return_value=mock_package)
        self.package_manager._delete_package_from_db = Mock(return_value=True)
        
        result = self.package_manager.delete_package('pkg_nqm_001')
        
        assert result is True
        self.package_manager._delete_package_from_db.assert_called_once_with('pkg_nqm_001')
    
    def test_delete_package_active_package(self):
        """Test deletion of active package (should fail)"""
        mock_package = DocumentPackage(
            package_id='pkg_nqm_001',
            package_name='Test Package',
            tenant_id='tenant_001',
            category=PackageCategory.NQM,
            version='1.0.0',
            status=PackageStatus.ACTIVE  # Active packages cannot be deleted
        )
        
        self.package_manager.load_package = Mock(return_value=mock_package)
        
        with pytest.raises(ValueError, match="Cannot delete active packages"):
            self.package_manager.delete_package('pkg_nqm_001')
    
    def test_list_packages(self):
        """Test package listing"""
        mock_packages = [
            {'package_id': 'pkg_nqm_001', 'package_name': 'NQM Package'},
            {'package_id': 'pkg_rtl_001', 'package_name': 'RTL Package'}
        ]
        
        self.package_manager._list_packages_from_db = Mock(return_value=mock_packages)
        
        packages = self.package_manager.list_packages(
            tenant_id='tenant_001',
            category=PackageCategory.NQM,
            status=PackageStatus.ACTIVE
        )
        
        assert packages == mock_packages
        self.package_manager._list_packages_from_db.assert_called_once_with(
            'tenant_001', PackageCategory.NQM, PackageStatus.ACTIVE
        )
    
    def test_version_increment(self):
        """Test version increment functionality"""
        assert self.package_manager._increment_version('1.0.0', 'MAJOR') == '2.0.0'
        assert self.package_manager._increment_version('1.5.3', 'MINOR') == '1.6.0'
        assert self.package_manager._increment_version('1.5.3', 'PATCH') == '1.5.4'
        assert self.package_manager._increment_version('2.10.15', 'MAJOR') == '3.0.0'
    
    def test_document_cloning(self):
        """Test document cloning functionality"""
        source_doc = DocumentDefinition(
            document_id='doc_001',
            document_type='guidelines',
            document_name='Source Guidelines',
            required_sections=['Section 1', 'Section 2'],
            entity_types=['LOAN_PROGRAM'],
            quality_thresholds={'accuracy': 0.95}
        )
        
        cloned_doc = self.package_manager._clone_document(source_doc)
        
        # Should have new ID but same content
        assert cloned_doc.document_id != source_doc.document_id
        assert cloned_doc.document_id.startswith('doc_')
        assert cloned_doc.document_type == source_doc.document_type
        assert cloned_doc.document_name == source_doc.document_name
        assert cloned_doc.required_sections == source_doc.required_sections
        assert cloned_doc.entity_types == source_doc.entity_types
        assert cloned_doc.quality_thresholds == source_doc.quality_thresholds
    
    def test_error_handling(self):
        """Test error handling and exception wrapping"""
        # Test database error handling
        self.package_manager._store_package_in_db = Mock(side_effect=Exception("Database error"))
        
        package_config = {
            'package_name': 'Test Package',
            'tenant_id': 'tenant_001',
            'category': 'NQM'
        }
        
        with pytest.raises(LLMGraphBuilderException, match="Package creation failed"):
            self.package_manager.create_package(package_config)


class TestPackageManagerHelpers:
    """Test PackageManager helper methods"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.mock_graph_db = Mock()
        self.package_manager = PackageManager(self.mock_graph_db)
    
    def test_validate_package_config(self):
        """Test package configuration validation"""
        # Valid config
        valid_config = {
            'package_name': 'Test Package',
            'tenant_id': 'tenant_001',
            'category': 'NQM'
        }
        
        # Should not raise exception
        self.package_manager._validate_package_config(valid_config)
        
        # Invalid configs
        invalid_configs = [
            {},  # Missing all fields
            {'package_name': 'Test'},  # Missing tenant_id and category
            {'package_name': '', 'tenant_id': 'tenant', 'category': 'NQM'},  # Empty name
            {'package_name': 'Test', 'tenant_id': 'tenant', 'category': 'INVALID'},  # Invalid category
        ]
        
        for config in invalid_configs:
            with pytest.raises(ValueError):
                self.package_manager._validate_package_config(config)
    
    def test_create_document_from_config(self):
        """Test document creation from configuration"""
        doc_config = {
            'document_type': 'guidelines',
            'document_name': 'Test Guidelines',
            'required_sections': ['Section 1'],
            'entity_types': ['LOAN_PROGRAM'],
            'quality_thresholds': {'accuracy': 0.95}
        }
        
        document = self.package_manager._create_document_from_config(doc_config)
        
        assert document.document_type == 'guidelines'
        assert document.document_name == 'Test Guidelines'
        assert document.required_sections == ['Section 1']
        assert document.entity_types == ['LOAN_PROGRAM']
        assert document.quality_thresholds == {'accuracy': 0.95}
        assert document.document_id.startswith('doc_')  # Auto-generated ID
        assert document.chunking_strategy == 'hierarchical'  # Default value
    
    def test_update_compatibility_validation(self):
        """Test update compatibility validation"""
        package = DocumentPackage(
            package_id='pkg_nqm_001',
            package_name='Test Package',
            tenant_id='tenant_001',
            category=PackageCategory.NQM,
            version='1.0.0'
        )
        
        # Valid updates (should not raise)
        valid_updates = {
            'package_name': 'New Name',
            'status': 'ACTIVE',
            'version_type': 'MINOR'
        }
        self.package_manager._validate_update_compatibility(package, valid_updates)
        
        # Invalid updates (should raise)
        invalid_updates = [
            {'category': 'RTL'},  # Cannot change category
            {'tenant_id': 'new_tenant'},  # Cannot change tenant
        ]
        
        for updates in invalid_updates:
            with pytest.raises(ValueError):
                self.package_manager._validate_update_compatibility(package, updates)