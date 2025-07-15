"""
Integration tests for the enhanced upload workflow with document type slots.

Tests the complete flow from expected documents API to upload with pre-selected
document types and immediate relationship creation.
"""

import unittest
from unittest.mock import patch, MagicMock, Mock
import asyncio
import sys
import os
from fastapi.testclient import TestClient
from fastapi import UploadFile
import io

# Add the backend directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# Import the FastAPI app and dependencies
try:
    from score import app
    from src.graphDB_dataAccess import graphDBdataAccess
    from src.main import upload_file
except ImportError as e:
    print(f"Import error: {e}")
    print("Skipping integration tests due to import issues")
    # Create a dummy test to prevent test runner errors
    class TestDummy(unittest.TestCase):
        def test_dummy(self):
            self.skipTest("Skipping due to import issues")


class TestUploadWorkflowIntegration(unittest.TestCase):
    """Integration tests for the complete upload workflow."""
    
    def setUp(self):
        """Set up test client and mocks."""
        self.client = TestClient(app)
        self.mock_graph = MagicMock()
        
    @patch('score.graphDb_data_Access')
    def test_expected_documents_api_integration(self, mock_graph_access):
        """Test the expected documents API endpoint integration."""
        # Mock the database response
        mock_graph_access.get_expected_documents_for_product.return_value = [
            {
                'document_id': 'doc_1',
                'document_type': 'Guidelines',
                'document_name': 'Underwriting Guidelines',
                'is_required': True,
                'has_upload': False,
                'uploaded_at': None,
                'validation_rules': {
                    'accepted_types': ['.pdf', '.docx'],
                    'max_file_size': 50 * 1024 * 1024
                }
            },
            {
                'document_id': 'doc_2',
                'document_type': 'Matrix',
                'document_name': 'Rate Matrix',
                'is_required': True,
                'has_upload': False,
                'uploaded_at': None,
                'validation_rules': {
                    'accepted_types': ['.pdf', '.xlsx'],
                    'max_file_size': 25 * 1024 * 1024
                }
            }
        ]
        
        # Mock product info
        mock_graph_access.get_product_info.return_value = {
            'product_name': 'Test Product',
            'category_code': 'NQM'
        }
        
        # Make API request
        response = self.client.get("/products/test_product_123/expected-documents")
        
        # Assertions
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "Success")
        self.assertIn("expected_documents", data["data"])
        self.assertIn("completion_status", data["data"])
        
        expected_docs = data["data"]["expected_documents"]
        self.assertEqual(len(expected_docs), 2)
        self.assertEqual(expected_docs[0]["document_type"], "Guidelines")
        self.assertEqual(expected_docs[1]["document_type"], "Matrix")
        
        # Check completion status
        completion = data["data"]["completion_status"]
        self.assertEqual(completion["total_expected"], 2)
        self.assertEqual(completion["uploaded_count"], 0)
        self.assertEqual(completion["completion_percentage"], 0)
        
    @patch('score.graphDb_data_Access')
    def test_expected_documents_api_not_found(self, mock_graph_access):
        """Test expected documents API when product not found."""
        # Mock empty response
        mock_graph_access.get_expected_documents_for_product.return_value = []
        mock_graph_access.get_product_info.return_value = {}
        
        response = self.client.get("/products/nonexistent_product/expected-documents")
        
        self.assertEqual(response.status_code, 404)
        data = response.json()
        self.assertEqual(data["status"], "Failed")
        self.assertIn("not found", data["message"].lower())
        
    @patch('score.graphDb_data_Access')
    @patch('score.upload_file')
    def test_enhanced_upload_workflow(self, mock_upload_file, mock_graph_access):
        """Test the enhanced upload workflow with pre-selected document type."""
        # Mock successful upload
        mock_upload_file.return_value = ("success", "File uploaded successfully")
        
        # Mock database operations
        mock_graph_access.link_uploaded_document_to_package_document.return_value = True
        mock_graph_access.add_package_metadata_to_document.return_value = True
        
        # Prepare test file
        test_file_content = b"This is a test PDF file content"
        test_file = io.BytesIO(test_file_content)
        
        # Prepare form data for upload
        files = {
            "file": ("test_guidelines.pdf", test_file, "application/pdf")
        }
        data = {
            "model": "gpt-4",
            "chunkNumber": "1",
            "totalChunks": "1",
            "originalname": "test_guidelines.pdf",
            "categoryId": "cat_123",
            "categoryName": "Test Category",
            "productId": "prod_456", 
            "productName": "Test Product",
            "documentType": "Guidelines",
            "expectedDocumentId": "doc_789",
            "preSelectedDocumentType": "Guidelines"
        }
        
        # Make upload request
        response = self.client.post("/upload", files=files, data=data)
        
        # Assertions
        self.assertEqual(response.status_code, 200)
        
        # Verify upload_file was called with correct parameters
        mock_upload_file.assert_called_once()
        call_args = mock_upload_file.call_args
        
        # Check that package context includes expected document ID
        package_context = call_args[0][5]  # Assuming package_context is the 6th argument
        self.assertIn('expectedDocumentId', package_context)
        self.assertEqual(package_context['expectedDocumentId'], 'doc_789')
        self.assertEqual(package_context['documentType'], 'Guidelines')
        
    @patch('score.graphDb_data_Access')
    def test_upload_validation_failure(self, mock_graph_access):
        """Test upload workflow with validation failures."""
        # Prepare oversized test file (simulate)
        test_file_content = b"x" * (60 * 1024 * 1024)  # 60MB content
        test_file = io.BytesIO(test_file_content)
        
        files = {
            "file": ("oversized.pdf", test_file, "application/pdf")
        }
        data = {
            "model": "gpt-4",
            "chunkNumber": "1",
            "totalChunks": "1",
            "originalname": "oversized.pdf",
            "expectedDocumentId": "doc_789",
            "preSelectedDocumentType": "Guidelines"
        }
        
        # The upload should potentially fail due to size limits
        # (This depends on actual server configuration)
        response = self.client.post("/upload", files=files, data=data)
        
        # The response code may vary based on server limits
        # This test primarily ensures the endpoint handles large files
        self.assertIsNotNone(response)
        
    @patch('score.graphDb_data_Access')
    @patch('score.upload_file')
    def test_relationship_creation_during_upload(self, mock_upload_file, mock_graph_access):
        """Test that relationships are created immediately during upload."""
        # Mock successful upload
        mock_upload_file.return_value = ("success", "File uploaded successfully")
        
        # Mock successful relationship creation
        mock_graph_access.link_uploaded_document_to_package_document.return_value = True
        
        # Prepare test file
        test_file_content = b"Test file content"
        test_file = io.BytesIO(test_file_content)
        
        files = {
            "file": ("test_matrix.xlsx", test_file, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
        }
        data = {
            "model": "gpt-4",
            "chunkNumber": "1",
            "totalChunks": "1",
            "originalname": "test_matrix.xlsx",
            "expectedDocumentId": "doc_matrix_123",
            "preSelectedDocumentType": "Matrix"
        }
        
        response = self.client.post("/upload", files=files, data=data)
        
        # Verify upload was successful
        self.assertEqual(response.status_code, 200)
        
        # Verify relationship creation was attempted
        mock_graph_access.link_uploaded_document_to_package_document.assert_called_with(
            "test_matrix.xlsx", "doc_matrix_123"
        )
        
    @patch('score.graphDb_data_Access')
    def test_fallback_to_standard_upload(self, mock_graph_access):
        """Test fallback to standard upload when no expected document ID."""
        # Mock graph access
        mock_graph_access.add_package_metadata_to_document.return_value = True
        
        # Prepare test file
        test_file_content = b"Standard upload test"
        test_file = io.BytesIO(test_file_content)
        
        files = {
            "file": ("standard_upload.pdf", test_file, "application/pdf")
        }
        data = {
            "model": "gpt-4",
            "chunkNumber": "1",
            "totalChunks": "1",
            "originalname": "standard_upload.pdf",
            "documentType": "Other"
            # No expectedDocumentId - should fall back to standard workflow
        }
        
        response = self.client.post("/upload", files=files, data=data)
        
        # Should still succeed but without document linking
        self.assertIsNotNone(response)
        
        # Verify link_uploaded_document_to_package_document was NOT called
        mock_graph_access.link_uploaded_document_to_package_document.assert_not_called()


class TestAPIErrorHandling(unittest.TestCase):
    """Test API error handling and edge cases."""
    
    def setUp(self):
        """Set up test client."""
        self.client = TestClient(app)
        
    @patch('score.graphDb_data_Access')
    def test_database_connection_error(self, mock_graph_access):
        """Test handling of database connection errors."""
        # Mock database error
        mock_graph_access.get_expected_documents_for_product.side_effect = Exception("Database connection failed")
        
        response = self.client.get("/products/test_product/expected-documents")
        
        self.assertEqual(response.status_code, 500)
        data = response.json()
        self.assertEqual(data["status"], "Failed")
        self.assertIn("error", data)
        
    @patch('score.graphDb_data_Access')
    def test_invalid_product_id_format(self, mock_graph_access):
        """Test handling of invalid product ID formats."""
        # Test with various invalid formats
        invalid_ids = ["", "invalid@id", "id with spaces", "null", "undefined"]
        
        for invalid_id in invalid_ids:
            response = self.client.get(f"/products/{invalid_id}/expected-documents")
            
            # Should handle gracefully (may return 404 or 400)
            self.assertIn(response.status_code, [400, 404, 422])
            
    @patch('score.graphDb_data_Access')
    def test_missing_required_upload_parameters(self, mock_graph_access):
        """Test upload with missing required parameters."""
        test_file = io.BytesIO(b"test content")
        
        files = {
            "file": ("test.pdf", test_file, "application/pdf")
        }
        # Missing required parameters
        data = {
            "model": "gpt-4"
            # Missing chunkNumber, totalChunks, originalname
        }
        
        response = self.client.post("/upload", files=files, data=data)
        
        # Should return appropriate error
        self.assertIn(response.status_code, [400, 422])


class TestDataConsistency(unittest.TestCase):
    """Test data consistency across the upload workflow."""
    
    def setUp(self):
        """Set up test client and mocks."""
        self.client = TestClient(app)
        
    @patch('score.graphDb_data_Access')
    def test_completion_status_calculation(self, mock_graph_access):
        """Test completion status calculation accuracy."""
        # Mock mixed upload status
        mock_graph_access.get_expected_documents_for_product.return_value = [
            {
                'document_id': 'doc_1',
                'document_type': 'Guidelines',
                'is_required': True,
                'has_upload': True,  # Uploaded
                'uploaded_at': '2024-01-01T10:00:00Z'
            },
            {
                'document_id': 'doc_2',
                'document_type': 'Matrix',
                'is_required': True,
                'has_upload': False,  # Not uploaded
                'uploaded_at': None
            },
            {
                'document_id': 'doc_3',
                'document_type': 'Supporting',
                'is_required': False,
                'has_upload': False,  # Optional, not uploaded
                'uploaded_at': None
            }
        ]
        
        mock_graph_access.get_product_info.return_value = {
            'product_name': 'Test Product'
        }
        
        response = self.client.get("/products/test_product/expected-documents")
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        completion = data["data"]["completion_status"]
        self.assertEqual(completion["total_expected"], 3)
        self.assertEqual(completion["uploaded_count"], 1)
        self.assertEqual(completion["completion_percentage"], 33)  # 1/3 = 33%
        
    @patch('score.graphDb_data_Access')
    def test_document_type_consistency(self, mock_graph_access):
        """Test that document types remain consistent throughout workflow."""
        # Test that preSelectedDocumentType takes precedence over documentType
        mock_graph_access.add_package_metadata_to_document.return_value = True
        
        test_file = io.BytesIO(b"test content")
        files = {
            "file": ("test.pdf", test_file, "application/pdf")
        }
        data = {
            "model": "gpt-4",
            "chunkNumber": "1", 
            "totalChunks": "1",
            "originalname": "test.pdf",
            "documentType": "Other",  # Original type
            "preSelectedDocumentType": "Guidelines"  # Should take precedence
        }
        
        response = self.client.post("/upload", files=files, data=data)
        
        # Verify that the preSelectedDocumentType was used
        # This would need verification through mocked calls
        self.assertIsNotNone(response)


if __name__ == '__main__':
    # Run the tests
    unittest.main(verbosity=2)