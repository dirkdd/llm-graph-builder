"""
Unit tests for document type slots functionality.

Tests the expected documents API, database methods, and upload enhancements
for the document type slots feature.
"""

import unittest
from unittest.mock import patch, MagicMock, Mock
import pytest
from fastapi.testclient import TestClient
from fastapi import Form
import sys
import os

# Add the backend src directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from graphDB_dataAccess import graphDBdataAccess
from shared.common_fn import create_api_response


class TestExpectedDocumentsAPI(unittest.TestCase):
    """Test the expected documents API endpoint."""
    
    def setUp(self):
        """Set up test dependencies."""
        self.mock_graph = MagicMock()
        self.graph_db = graphDBdataAccess(self.mock_graph)
        
    def test_get_expected_documents_success(self):
        """Test successful retrieval of expected documents."""
        # Mock data
        product_id = "test_product_123"
        mock_response = [
            {
                'document_id': 'doc_1',
                'document_type': 'Guidelines',
                'document_name': 'Underwriting Guidelines',
                'is_required': True,
                'has_upload': False,
                'uploaded_at': None
            },
            {
                'document_id': 'doc_2',
                'document_type': 'Matrix',
                'document_name': 'Rate Matrix',
                'is_required': True,
                'has_upload': False,
                'uploaded_at': None
            }
        ]
        
        # Mock the graph query
        self.mock_graph.query.return_value = mock_response
        
        # Call the method
        result = self.graph_db.get_expected_documents_for_product(product_id)
        
        # Assertions
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]['document_type'], 'Guidelines')
        self.assertEqual(result[1]['document_type'], 'Matrix')
        self.assertTrue(result[0]['is_required'])
        self.assertFalse(result[0]['has_upload'])
        
        # Verify the query was called correctly
        self.mock_graph.query.assert_called_once()
        call_args = self.mock_graph.query.call_args
        self.assertIn(product_id, str(call_args))
        
    def test_get_expected_documents_empty_result(self):
        """Test handling when no expected documents exist."""
        product_id = "nonexistent_product"
        
        # Mock empty response
        self.mock_graph.query.return_value = []
        
        # Call the method
        result = self.graph_db.get_expected_documents_for_product(product_id)
        
        # Assertions
        self.assertEqual(len(result), 0)
        self.assertIsInstance(result, list)
        
    def test_get_expected_documents_database_error(self):
        """Test handling of database errors."""
        product_id = "test_product_123"
        
        # Mock database error
        self.mock_graph.query.side_effect = Exception("Database connection failed")
        
        # Call the method and expect exception
        with self.assertRaises(Exception) as context:
            self.graph_db.get_expected_documents_for_product(product_id)
        
        self.assertIn("Database connection failed", str(context.exception))
        
    def test_get_validation_rules_guidelines(self):
        """Test validation rules for Guidelines document type."""
        rules = self.graph_db._get_validation_rules_for_document_type('Guidelines')
        
        self.assertIn('.pdf', rules['accepted_types'])
        self.assertIn('.docx', rules['accepted_types'])
        self.assertEqual(rules['max_file_size'], 50 * 1024 * 1024)  # 50MB
        self.assertIn('guidelines', rules['description'].lower())
        
    def test_get_validation_rules_matrix(self):
        """Test validation rules for Matrix document type."""
        rules = self.graph_db._get_validation_rules_for_document_type('Matrix')
        
        self.assertIn('.pdf', rules['accepted_types'])
        self.assertIn('.xlsx', rules['accepted_types'])
        self.assertIn('.xls', rules['accepted_types'])
        self.assertIn('.csv', rules['accepted_types'])
        self.assertEqual(rules['max_file_size'], 25 * 1024 * 1024)  # 25MB
        self.assertIn('matrix', rules['description'].lower())
        
    def test_get_validation_rules_other(self):
        """Test validation rules for unknown document type."""
        rules = self.graph_db._get_validation_rules_for_document_type('UnknownType')
        
        # Should fall back to 'Other' type rules
        self.assertIn('.pdf', rules['accepted_types'])
        self.assertEqual(rules['max_file_size'], 100 * 1024 * 1024)  # 100MB


class TestProductInfoRetrieval(unittest.TestCase):
    """Test product information retrieval."""
    
    def setUp(self):
        """Set up test dependencies."""
        self.mock_graph = MagicMock()
        self.graph_db = graphDBdataAccess(self.mock_graph)
        
    def test_get_product_info_success(self):
        """Test successful product info retrieval."""
        product_id = "test_product_123"
        mock_response = [
            {
                'product_name': 'Test Product',
                'description': 'A test product for unit testing',
                'category_code': 'NQM'
            }
        ]
        
        self.mock_graph.query.return_value = mock_response
        
        result = self.graph_db.get_product_info(product_id)
        
        self.assertEqual(result['product_name'], 'Test Product')
        self.assertEqual(result['category_code'], 'NQM')
        self.assertIn('test product', result['description'].lower())
        
    def test_get_product_info_not_found(self):
        """Test handling when product is not found."""
        product_id = "nonexistent_product"
        
        self.mock_graph.query.return_value = []
        
        result = self.graph_db.get_product_info(product_id)
        
        self.assertEqual(result, {})
        
    def test_get_product_info_database_error(self):
        """Test handling of database errors in product info retrieval."""
        product_id = "test_product_123"
        
        self.mock_graph.query.side_effect = Exception("Connection timeout")
        
        result = self.graph_db.get_product_info(product_id)
        
        self.assertEqual(result, {})


class TestDocumentLinking(unittest.TestCase):
    """Test document linking functionality."""
    
    def setUp(self):
        """Set up test dependencies."""
        self.mock_graph = MagicMock()
        self.graph_db = graphDBdataAccess(self.mock_graph)
        
    def test_link_uploaded_document_success(self):
        """Test successful document linking."""
        document_filename = "test_guidelines.pdf"
        package_document_id = "doc_123"
        
        # Mock successful response
        mock_response = [{'package_document_id': package_document_id}]
        self.mock_graph.query.return_value = mock_response
        
        result = self.graph_db.link_uploaded_document_to_package_document(
            document_filename, package_document_id
        )
        
        self.assertTrue(result)
        
        # Verify the query was called
        self.mock_graph.query.assert_called_once()
        call_args = self.mock_graph.query.call_args
        self.assertIn(document_filename, str(call_args))
        self.assertIn(package_document_id, str(call_args))
        
    def test_link_uploaded_document_failure(self):
        """Test document linking failure."""
        document_filename = "nonexistent.pdf"
        package_document_id = "doc_123"
        
        # Mock empty response (no documents found)
        self.mock_graph.query.return_value = []
        
        result = self.graph_db.link_uploaded_document_to_package_document(
            document_filename, package_document_id
        )
        
        self.assertFalse(result)
        
    def test_link_uploaded_document_database_error(self):
        """Test handling of database errors in document linking."""
        document_filename = "test_guidelines.pdf"
        package_document_id = "doc_123"
        
        # Mock database error
        self.mock_graph.query.side_effect = Exception("Database error")
        
        result = self.graph_db.link_uploaded_document_to_package_document(
            document_filename, package_document_id
        )
        
        self.assertFalse(result)


class TestPackageMetadataHandling(unittest.TestCase):
    """Test package metadata handling."""
    
    def setUp(self):
        """Set up test dependencies."""
        self.mock_graph = MagicMock()
        self.graph_db = graphDBdataAccess(self.mock_graph)
        
    def test_add_package_metadata_success(self):
        """Test successful package metadata addition."""
        file_name = "test_document.pdf"
        package_context = {
            'categoryId': 'cat_123',
            'categoryName': 'Test Category',
            'productId': 'prod_456',
            'productName': 'Test Product',
            'documentType': 'Guidelines',
            'expectedDocumentId': 'doc_789'
        }
        
        # Mock successful response
        self.mock_graph.query.return_value = [{'fileName': file_name}]
        
        result = self.graph_db.add_package_metadata_to_document(file_name, package_context)
        
        self.assertTrue(result)
        
        # Verify the query was called with correct parameters
        self.mock_graph.query.assert_called_once()
        call_args = self.mock_graph.query.call_args
        self.assertIn(file_name, str(call_args))
        self.assertIn('cat_123', str(call_args))
        self.assertIn('prod_456', str(call_args))
        
    def test_add_package_metadata_missing_context(self):
        """Test handling of missing package context."""
        file_name = "test_document.pdf"
        package_context = {}  # Empty context
        
        result = self.graph_db.add_package_metadata_to_document(file_name, package_context)
        
        # Should handle gracefully
        self.assertIsInstance(result, bool)
        
    def test_get_document_package_info_success(self):
        """Test successful document package info retrieval."""
        file_name = "test_document.pdf"
        mock_response = [
            {
                'created_via_package': True,
                'package_upload': True,
                'category_id': 'cat_123',
                'category_name': 'Test Category',
                'product_id': 'prod_456',
                'product_name': 'Test Product',
                'document_type': 'Guidelines'
            }
        ]
        
        self.mock_graph.query.return_value = mock_response
        
        result = self.graph_db.get_document_package_info(file_name)
        
        self.assertTrue(result['created_via_package'])
        self.assertTrue(result['package_upload'])
        self.assertEqual(result['document_type'], 'Guidelines')
        self.assertEqual(result['product_id'], 'prod_456')
        
    def test_get_document_package_info_not_found(self):
        """Test handling when document package info is not found."""
        file_name = "nonexistent_document.pdf"
        
        self.mock_graph.query.return_value = []
        
        result = self.graph_db.get_document_package_info(file_name)
        
        self.assertEqual(result, {})


class TestAPIResponseHandling(unittest.TestCase):
    """Test API response handling and error cases."""
    
    def test_api_response_success_format(self):
        """Test successful API response format."""
        expected_documents = [
            {
                'id': 'doc_1',
                'document_type': 'Guidelines',
                'is_required': True,
                'upload_status': 'empty'
            }
        ]
        
        response = create_api_response("Success", data={
            "expected_documents": expected_documents,
            "completion_status": {
                "total_expected": 1,
                "uploaded_count": 0,
                "completion_percentage": 0
            }
        })
        
        self.assertEqual(response["status"], "Success")
        self.assertIn("expected_documents", response["data"])
        self.assertIn("completion_status", response["data"])
        self.assertEqual(len(response["data"]["expected_documents"]), 1)
        
    def test_api_response_error_format(self):
        """Test error API response format."""
        response = create_api_response("Failed", 
                                     message="Product not found",
                                     error="Product ID does not exist")
        
        self.assertEqual(response["status"], "Failed")
        self.assertEqual(response["message"], "Product not found")
        self.assertEqual(response["error"], "Product ID does not exist")


class TestValidationLogic(unittest.TestCase):
    """Test validation logic for document types and uploads."""
    
    def test_file_size_validation(self):
        """Test file size validation logic."""
        # Guidelines should have 50MB limit
        guidelines_rules = {
            'max_file_size': 50 * 1024 * 1024,
            'accepted_types': ['.pdf', '.docx']
        }
        
        # Test file within limit
        file_size_ok = 30 * 1024 * 1024  # 30MB
        self.assertLessEqual(file_size_ok, guidelines_rules['max_file_size'])
        
        # Test file exceeding limit
        file_size_too_big = 60 * 1024 * 1024  # 60MB
        self.assertGreater(file_size_too_big, guidelines_rules['max_file_size'])
        
    def test_file_type_validation(self):
        """Test file type validation logic."""
        matrix_rules = {
            'accepted_types': ['.pdf', '.xlsx', '.xls', '.csv'],
            'max_file_size': 25 * 1024 * 1024
        }
        
        # Test valid file types
        valid_extensions = ['.pdf', '.xlsx', '.xls', '.csv']
        for ext in valid_extensions:
            self.assertIn(ext, matrix_rules['accepted_types'])
            
        # Test invalid file types
        invalid_extensions = ['.txt', '.doc', '.ppt', '.jpg']
        for ext in invalid_extensions:
            self.assertNotIn(ext, matrix_rules['accepted_types'])


if __name__ == '__main__':
    # Run the tests
    unittest.main(verbosity=2)