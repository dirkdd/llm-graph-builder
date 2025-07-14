# Task 6: Package API Endpoints Integration Tests
# This file contains tests for the complete package API endpoint integration

import pytest
from unittest.mock import Mock, patch, MagicMock
from fastapi.testclient import TestClient
import json
import sys
import os

# Add the parent directory to the path to import backend modules
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from score import app
from src.entities.document_package import PackageCategory, PackageStatus

# Create test client
client = TestClient(app)


class TestPackageAPIEndpoints:
    """Test Package API endpoints integration"""

    def setup_method(self):
        """Set up test fixtures"""
        # Mock common form data for database connection
        self.db_form_data = {
            'uri': 'neo4j+s://test.neo4j.io',
            'userName': 'test_user',
            'password': 'test_password',
            'database': 'test_database'
        }

    @patch('score.create_graph_database_connection')
    @patch('score.graphDBdataAccess')
    @patch('score.PackageManager')
    def test_create_package_endpoint(self, mock_package_manager_class, mock_graph_db_class, mock_create_connection):
        """Test POST /packages endpoint"""
        # Mock database connection
        mock_graph = Mock()
        mock_create_connection.return_value = mock_graph
        
        # Mock graph database access
        mock_graph_db = Mock()
        mock_graph_db_class.return_value = mock_graph_db
        
        # Mock package manager and created package
        mock_package_manager = Mock()
        mock_package_manager_class.return_value = mock_package_manager
        
        mock_package = Mock()
        mock_package.package_id = 'pkg_nqm_test001'
        mock_package.package_name = 'Test NQM Package'
        mock_package.category.value = 'NQM'
        mock_package.version = '1.0.0'
        mock_package.status.value = 'DRAFT'
        mock_package.created_at.isoformat.return_value = '2023-01-01T00:00:00'
        mock_package.documents = []
        mock_package.relationships = []
        
        mock_package_manager.create_package.return_value = mock_package
        
        # Prepare request data
        form_data = {
            **self.db_form_data,
            'package_name': 'Test NQM Package',
            'tenant_id': 'tenant_001',
            'category': 'NQM',
            'created_by': 'test_user',
            'documents': json.dumps([
                {
                    'document_type': 'guidelines',
                    'document_name': 'NQM Guidelines',
                    'required_sections': ['Borrower Eligibility']
                }
            ])
        }
        
        # Make request
        response = client.post("/packages", data=form_data)
        
        # Assertions
        assert response.status_code == 200
        response_data = response.json()
        assert response_data['status'] == 'Success'
        assert 'Package \'Test NQM Package\' created successfully' in response_data['message']
        assert response_data['data']['package_id'] == 'pkg_nqm_test001'
        assert response_data['data']['package_name'] == 'Test NQM Package'
        assert response_data['data']['category'] == 'NQM'
        
        # Verify manager was called correctly
        mock_package_manager.create_package.assert_called_once()
        call_args = mock_package_manager.create_package.call_args[0][0]
        assert call_args['package_name'] == 'Test NQM Package'
        assert call_args['tenant_id'] == 'tenant_001'
        assert call_args['category'] == 'NQM'

    @patch('score.create_graph_database_connection')
    @patch('score.graphDBdataAccess')
    @patch('score.PackageManager')
    def test_get_package_endpoint(self, mock_package_manager_class, mock_graph_db_class, mock_create_connection):
        """Test GET /packages/{package_id} endpoint"""
        # Mock database connection
        mock_graph = Mock()
        mock_create_connection.return_value = mock_graph
        
        # Mock graph database access
        mock_graph_db = Mock()
        mock_graph_db_class.return_value = mock_graph_db
        
        # Mock package manager and loaded package
        mock_package_manager = Mock()
        mock_package_manager_class.return_value = mock_package_manager
        
        mock_package = Mock()
        mock_package.package_id = 'pkg_nqm_test001'
        mock_package.package_name = 'Test NQM Package'
        mock_package.tenant_id = 'tenant_001'
        mock_package.category.value = 'NQM'
        mock_package.version = '1.0.0'
        mock_package.status.value = 'DRAFT'
        mock_package.created_by = 'test_user'
        mock_package.template_type = 'NQM_STANDARD'
        mock_package.created_at.isoformat.return_value = '2023-01-01T00:00:00'
        mock_package.updated_at.isoformat.return_value = '2023-01-01T00:00:00'
        mock_package.template_mappings = {'test': 'mapping'}
        mock_package.validation_rules = {'test': 'rule'}
        mock_package.documents = []
        mock_package.relationships = []
        
        mock_package_manager.load_package.return_value = mock_package
        
        # Prepare request data
        form_data = self.db_form_data
        
        # Make request
        response = client.request("GET", "/packages/pkg_nqm_test001", data=form_data)
        
        # Assertions
        assert response.status_code == 200
        response_data = response.json()
        assert response_data['status'] == 'Success'
        assert 'Package \'pkg_nqm_test001\' retrieved successfully' in response_data['message']
        assert response_data['data']['package_id'] == 'pkg_nqm_test001'
        assert response_data['data']['package_name'] == 'Test NQM Package'
        assert response_data['data']['category'] == 'NQM'
        
        # Verify manager was called correctly
        mock_package_manager.load_package.assert_called_once_with('pkg_nqm_test001')

    @patch('score.create_graph_database_connection')
    @patch('score.graphDBdataAccess')
    @patch('score.PackageManager')
    def test_list_packages_endpoint(self, mock_package_manager_class, mock_graph_db_class, mock_create_connection):
        """Test GET /packages endpoint"""
        # Mock database connection
        mock_graph = Mock()
        mock_create_connection.return_value = mock_graph
        
        # Mock graph database access
        mock_graph_db = Mock()
        mock_graph_db_class.return_value = mock_graph_db
        
        # Mock package manager and package list
        mock_package_manager = Mock()
        mock_package_manager_class.return_value = mock_package_manager
        
        mock_packages = [
            {
                'package_id': 'pkg_nqm_001',
                'package_name': 'NQM Package 1',
                'category': 'NQM',
                'status': 'ACTIVE'
            },
            {
                'package_id': 'pkg_nqm_002',
                'package_name': 'NQM Package 2',
                'category': 'NQM', 
                'status': 'DRAFT'
            }
        ]
        
        mock_package_manager.list_packages.return_value = mock_packages
        
        # Prepare request data with filters
        form_data = {
            **self.db_form_data,
            'tenant_id': 'tenant_001',
            'category': 'NQM',
            'status': 'ACTIVE'
        }
        
        # Make request
        response = client.request("GET", "/packages", data=form_data)
        
        # Assertions
        assert response.status_code == 200
        response_data = response.json()
        assert response_data['status'] == 'Success'
        assert 'Found 2 packages' in response_data['message']
        assert response_data['data']['total_count'] == 2
        assert len(response_data['data']['packages']) == 2
        assert response_data['data']['filters']['tenant_id'] == 'tenant_001'
        assert response_data['data']['filters']['category'] == 'NQM'
        
        # Verify manager was called correctly with filters
        mock_package_manager.list_packages.assert_called_once()

    @patch('score.create_graph_database_connection')
    @patch('score.graphDBdataAccess')
    @patch('score.PackageManager')
    def test_update_package_endpoint(self, mock_package_manager_class, mock_graph_db_class, mock_create_connection):
        """Test PUT /packages/{package_id} endpoint"""
        # Mock database connection
        mock_graph = Mock()
        mock_create_connection.return_value = mock_graph
        
        # Mock graph database access
        mock_graph_db = Mock()
        mock_graph_db_class.return_value = mock_graph_db
        
        # Mock package manager and updated package
        mock_package_manager = Mock()
        mock_package_manager_class.return_value = mock_package_manager
        
        mock_package = Mock()
        mock_package.package_id = 'pkg_nqm_test001'
        mock_package.package_name = 'Updated NQM Package'
        mock_package.version = '1.1.0'
        mock_package.status.value = 'ACTIVE'
        mock_package.updated_at.isoformat.return_value = '2023-01-02T00:00:00'
        mock_package.documents = []
        mock_package.relationships = []
        
        mock_package_manager.update_package.return_value = mock_package
        
        # Prepare request data
        form_data = {
            **self.db_form_data,
            'package_name': 'Updated NQM Package',
            'status': 'ACTIVE',
            'version_type': 'MINOR'
        }
        
        # Make request
        response = client.put("/packages/pkg_nqm_test001", data=form_data)
        
        # Assertions
        assert response.status_code == 200
        response_data = response.json()
        assert response_data['status'] == 'Success'
        assert 'Package \'pkg_nqm_test001\' updated successfully to version 1.1.0' in response_data['message']
        assert response_data['data']['package_id'] == 'pkg_nqm_test001'
        assert response_data['data']['package_name'] == 'Updated NQM Package'
        assert response_data['data']['version'] == '1.1.0'
        
        # Verify manager was called correctly
        mock_package_manager.update_package.assert_called_once()
        call_args = mock_package_manager.update_package.call_args
        assert call_args[0][0] == 'pkg_nqm_test001'  # package_id
        updates = call_args[0][1]  # updates dict
        assert updates['package_name'] == 'Updated NQM Package'
        assert updates['status'] == 'ACTIVE'
        assert updates['version_type'] == 'MINOR'

    @patch('score.create_graph_database_connection')
    @patch('score.graphDBdataAccess')
    @patch('score.PackageManager')
    def test_delete_package_endpoint(self, mock_package_manager_class, mock_graph_db_class, mock_create_connection):
        """Test DELETE /packages/{package_id} endpoint"""
        # Mock database connection
        mock_graph = Mock()
        mock_create_connection.return_value = mock_graph
        
        # Mock graph database access
        mock_graph_db = Mock()
        mock_graph_db_class.return_value = mock_graph_db
        
        # Mock package manager
        mock_package_manager = Mock()
        mock_package_manager_class.return_value = mock_package_manager
        mock_package_manager.delete_package.return_value = True
        
        # Prepare request data
        form_data = self.db_form_data
        
        # Make request
        response = client.delete("/packages/pkg_nqm_test001", data=form_data)
        
        # Assertions
        assert response.status_code == 200
        response_data = response.json()
        assert response_data['status'] == 'Success'
        assert 'Package \'pkg_nqm_test001\' deleted successfully' in response_data['message']
        assert response_data['data']['package_id'] == 'pkg_nqm_test001'
        assert response_data['data']['deleted'] == True
        
        # Verify manager was called correctly
        mock_package_manager.delete_package.assert_called_once_with('pkg_nqm_test001')

    @patch('score.create_graph_database_connection')
    @patch('score.graphDBdataAccess')
    @patch('score.PackageVersionManager')
    def test_get_package_versions_endpoint(self, mock_version_manager_class, mock_graph_db_class, mock_create_connection):
        """Test GET /packages/{package_id}/versions endpoint"""
        # Mock database connection
        mock_graph = Mock()
        mock_create_connection.return_value = mock_graph
        
        # Mock graph database access
        mock_graph_db = Mock()
        mock_graph_db_class.return_value = mock_graph_db
        
        # Mock version manager and version history
        mock_version_manager = Mock()
        mock_version_manager_class.return_value = mock_version_manager
        
        mock_version1 = Mock()
        mock_version1.version = '1.1.0'
        mock_version1.change_type.value = 'MINOR'
        mock_version1.changes = ['Added new feature']
        mock_version1.created_at.isoformat.return_value = '2023-01-02T00:00:00'
        mock_version1.created_by = 'test_user'
        mock_version1.metadata = {'test': 'metadata'}
        
        mock_version2 = Mock()
        mock_version2.version = '1.0.0'
        mock_version2.change_type.value = 'PATCH'
        mock_version2.changes = ['Initial version']
        mock_version2.created_at.isoformat.return_value = '2023-01-01T00:00:00'
        mock_version2.created_by = 'test_user'
        mock_version2.metadata = {}
        
        mock_version_manager.get_version_history.return_value = [mock_version1, mock_version2]
        
        # Prepare request data
        form_data = self.db_form_data
        
        # Make request
        response = client.request("GET", "/packages/pkg_nqm_test001/versions", data=form_data)
        
        # Assertions
        assert response.status_code == 200
        response_data = response.json()
        assert response_data['status'] == 'Success'
        assert 'Found 2 versions for package \'pkg_nqm_test001\'' in response_data['message']
        assert response_data['data']['package_id'] == 'pkg_nqm_test001'
        assert response_data['data']['total_versions'] == 2
        assert len(response_data['data']['versions']) == 2
        assert response_data['data']['versions'][0]['version'] == '1.1.0'
        assert response_data['data']['versions'][1]['version'] == '1.0.0'
        
        # Verify manager was called correctly
        mock_version_manager.get_version_history.assert_called_once_with('pkg_nqm_test001')

    @patch('score.create_graph_database_connection')
    @patch('score.graphDBdataAccess')
    @patch('score.PackageVersionManager')
    def test_rollback_package_endpoint(self, mock_version_manager_class, mock_graph_db_class, mock_create_connection):
        """Test POST /packages/{package_id}/rollback endpoint"""
        # Mock database connection
        mock_graph = Mock()
        mock_create_connection.return_value = mock_graph
        
        # Mock graph database access
        mock_graph_db = Mock()
        mock_graph_db_class.return_value = mock_graph_db
        
        # Mock version manager and restored package
        mock_version_manager = Mock()
        mock_version_manager_class.return_value = mock_version_manager
        
        mock_restored_package = Mock()
        mock_restored_package.package_id = 'pkg_nqm_test001'
        mock_restored_package.package_name = 'Test NQM Package'
        mock_restored_package.version = '2.0.0'  # New version after rollback
        mock_restored_package.status.value = 'DRAFT'
        mock_restored_package.updated_at.isoformat.return_value = '2023-01-03T00:00:00'
        mock_restored_package.documents = []
        mock_restored_package.relationships = []
        
        mock_version_manager.rollback_version.return_value = mock_restored_package
        
        # Prepare request data
        form_data = {
            **self.db_form_data,
            'target_version': '1.0.0',
            'created_by': 'test_user'
        }
        
        # Make request
        response = client.post("/packages/pkg_nqm_test001/rollback", data=form_data)
        
        # Assertions
        assert response.status_code == 200
        response_data = response.json()
        assert response_data['status'] == 'Success'
        assert 'Package \'pkg_nqm_test001\' rolled back to version 1.0.0 (new version: 2.0.0)' in response_data['message']
        assert response_data['data']['package_id'] == 'pkg_nqm_test001'
        assert response_data['data']['target_version'] == '1.0.0'
        assert response_data['data']['new_version'] == '2.0.0'
        
        # Verify manager was called correctly
        mock_version_manager.rollback_version.assert_called_once_with('pkg_nqm_test001', '1.0.0', 'test_user')

    @patch('score.create_graph_database_connection')
    @patch('score.graphDBdataAccess')
    @patch('score.PackageVersionManager')
    def test_diff_package_versions_endpoint(self, mock_version_manager_class, mock_graph_db_class, mock_create_connection):
        """Test GET /packages/{package_id}/diff endpoint"""
        # Mock database connection
        mock_graph = Mock()
        mock_create_connection.return_value = mock_graph
        
        # Mock graph database access
        mock_graph_db = Mock()
        mock_graph_db_class.return_value = mock_graph_db
        
        # Mock version manager and version diff
        mock_version_manager = Mock()
        mock_version_manager_class.return_value = mock_version_manager
        
        mock_diff = Mock()
        mock_diff.has_changes.return_value = True
        mock_diff.added_documents = ['doc_new']
        mock_diff.removed_documents = []
        mock_diff.modified_documents = [{'document_id': 'doc_001', 'changes': ['name changed']}]
        mock_diff.structural_changes = ['Status changed from DRAFT to ACTIVE']
        mock_diff.relationship_changes = []
        
        mock_version_manager.diff_versions.return_value = mock_diff
        
        # Prepare request data
        form_data = {
            **self.db_form_data,
            'from_version': '1.0.0',
            'to_version': '1.1.0'
        }
        
        # Make request
        response = client.request("GET", "/packages/pkg_nqm_test001/diff", data=form_data)
        
        # Assertions
        assert response.status_code == 200
        response_data = response.json()
        assert response_data['status'] == 'Success'
        assert 'Version comparison complete' in response_data['message']
        assert response_data['data']['package_id'] == 'pkg_nqm_test001'
        assert response_data['data']['from_version'] == '1.0.0'
        assert response_data['data']['to_version'] == '1.1.0'
        assert response_data['data']['has_changes'] == True
        assert response_data['data']['summary']['documents_added'] == 1
        assert response_data['data']['summary']['documents_modified'] == 1
        
        # Verify manager was called correctly
        mock_version_manager.diff_versions.assert_called_once_with('pkg_nqm_test001', '1.0.0', '1.1.0')

    def test_validate_package_config_endpoint(self):
        """Test POST /packages/validate endpoint"""
        # Prepare request data
        form_data = {
            **self.db_form_data,
            'package_name': 'Test Validation Package',
            'tenant_id': 'tenant_001',
            'category': 'NQM',
            'documents': json.dumps([
                {
                    'document_type': 'guidelines',
                    'document_name': 'Test Guidelines',
                    'required_sections': ['Section 1']
                }
            ])
        }
        
        # Make request
        response = client.post("/packages/validate", data=form_data)
        
        # Assertions
        assert response.status_code == 200
        response_data = response.json()
        assert response_data['status'] == 'Success'
        assert 'Package configuration is valid' in response_data['message']
        assert response_data['data']['is_valid'] == True
        assert response_data['data']['package_name'] == 'Test Validation Package'
        assert response_data['data']['category'] == 'NQM'
        assert response_data['data']['document_count'] == 1

    def test_create_package_invalid_json(self):
        """Test POST /packages with invalid JSON"""
        form_data = {
            **self.db_form_data,
            'package_name': 'Test Package',
            'tenant_id': 'tenant_001',
            'category': 'NQM',
            'documents': 'invalid json'  # Invalid JSON
        }
        
        response = client.post("/packages", data=form_data)
        
        assert response.status_code == 200
        response_data = response.json()
        assert response_data['status'] == 'Failed'
        assert 'Invalid documents JSON format' in response_data['message']

    def test_validate_package_invalid_category(self):
        """Test validation with invalid category"""
        form_data = {
            **self.db_form_data,
            'package_name': 'Test Package',
            'tenant_id': 'tenant_001',
            'category': 'INVALID_CATEGORY'
        }
        
        response = client.post("/packages/validate", data=form_data)
        
        assert response.status_code == 200
        response_data = response.json()
        assert response_data['status'] == 'Failed'
        assert 'Validation failed' in response_data['message']


class TestPackageAPIErrorHandling:
    """Test Package API error handling scenarios"""

    def setup_method(self):
        """Set up test fixtures"""
        self.db_form_data = {
            'uri': 'neo4j+s://test.neo4j.io',
            'userName': 'test_user',
            'password': 'test_password',
            'database': 'test_database'
        }

    @patch('score.create_graph_database_connection')
    @patch('score.graphDBdataAccess')
    @patch('score.PackageManager')
    def test_get_package_not_found(self, mock_package_manager_class, mock_graph_db_class, mock_create_connection):
        """Test GET /packages/{package_id} with non-existent package"""
        # Mock database connection
        mock_graph = Mock()
        mock_create_connection.return_value = mock_graph
        
        # Mock graph database access
        mock_graph_db = Mock()
        mock_graph_db_class.return_value = mock_graph_db
        
        # Mock package manager to raise ValueError (package not found)
        mock_package_manager = Mock()
        mock_package_manager_class.return_value = mock_package_manager
        mock_package_manager.load_package.side_effect = ValueError("Package not found")
        
        # Make request
        response = client.request("GET", "/packages/nonexistent_package", data=self.db_form_data)
        
        # Assertions
        assert response.status_code == 200
        response_data = response.json()
        assert response_data['status'] == 'Failed'
        assert 'Package not found: nonexistent_package' in response_data['message']

    @patch('score.create_graph_database_connection')
    def test_database_connection_failure(self, mock_create_connection):
        """Test API endpoint with database connection failure"""
        # Mock database connection to raise exception
        mock_create_connection.side_effect = Exception("Database connection failed")
        
        form_data = {
            **self.db_form_data,
            'package_name': 'Test Package',
            'tenant_id': 'tenant_001',
            'category': 'NQM'
        }
        
        # Make request
        response = client.post("/packages", data=form_data)
        
        # Assertions
        assert response.status_code == 200
        response_data = response.json()
        assert response_data['status'] == 'Failed'
        assert 'Unexpected error during package creation' in response_data['message']


# Test execution helper
if __name__ == "__main__":
    # This allows running the tests directly
    pytest.main([__file__, "-v"])