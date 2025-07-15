"""
Test configuration and shared fixtures for document type slots tests.
"""

import pytest
import sys
import os
from unittest.mock import MagicMock

# Add the backend src directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

@pytest.fixture
def mock_neo4j_graph():
    """Mock Neo4j graph database for testing."""
    mock_graph = MagicMock()
    mock_graph._database = "test_database"
    return mock_graph

@pytest.fixture
def sample_expected_documents():
    """Sample expected documents data for testing."""
    return [
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

@pytest.fixture
def sample_product_info():
    """Sample product information for testing."""
    return {
        'product_name': 'Test Product',
        'description': 'A test product for unit testing',
        'category_code': 'NQM'
    }

@pytest.fixture
def sample_package_context():
    """Sample package context for testing."""
    return {
        'categoryId': 'cat_123',
        'categoryName': 'Test Category',
        'productId': 'prod_456',
        'productName': 'Test Product',
        'documentType': 'Guidelines',
        'expectedDocumentId': 'doc_789'
    }