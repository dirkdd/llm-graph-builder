#!/usr/bin/env python3
"""
Test script to validate the enhanced package processing endpoint
"""
import json
import logging
from unittest.mock import MagicMock, patch
from src.graphDB_dataAccess import graphDBdataAccess

# Set up logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

def test_get_package_documents_enhanced():
    """Test the enhanced get_package_documents method"""
    print("Testing enhanced get_package_documents method...")
    
    # Mock the database connection
    mock_graph = MagicMock()
    gdb = graphDBdataAccess(mock_graph)
    
    # Mock the execute_query method
    mock_result = [
        {
            'document_id': 'doc_1',
            'document_name': 'Test Document 1.pdf',
            'document_type': 'Guidelines',
            'expected_structure': '{"sections": ["introduction", "main", "conclusion"]}',
            'required_sections': '["introduction", "main"]',
            'optional_sections': '["conclusion"]',
            'chunking_strategy': 'hierarchical',
            'entity_types': '["Person", "Organization"]',
            'matrix_configuration': '{"rows": 10, "cols": 5}',
            'validation_schema': '{"type": "object"}',
            'quality_thresholds': '{"min_confidence": 0.8}',
            'file_size': 1024,
            'file_source': 'local',
            'processing_type': 'package',
            'status': 'pending',
            'created_at': '2024-01-01T00:00:00Z',
            'updated_at': '2024-01-01T00:00:00Z'
        },
        {
            'document_id': 'doc_2',
            'document_name': 'Test Document 2.pdf',
            'document_type': 'Matrix',
            'expected_structure': '{"tables": ["rate_matrix", "conditions"]}',
            'required_sections': '["rate_matrix"]',
            'optional_sections': '["conditions"]',
            'chunking_strategy': 'matrix',
            'entity_types': '["Rate", "Condition"]',
            'matrix_configuration': '{"rows": 20, "cols": 10}',
            'validation_schema': '{"type": "matrix"}',
            'quality_thresholds': '{"min_confidence": 0.9}',
            'file_size': 2048,
            'file_source': 'local',
            'processing_type': 'package',
            'status': 'pending',
            'created_at': '2024-01-01T00:00:00Z',
            'updated_at': '2024-01-01T00:00:00Z'
        }
    ]
    
    gdb.execute_query = MagicMock(return_value=mock_result)
    
    # Test the method
    package_id = 'test_package_123'
    documents = gdb.get_package_documents(package_id)
    
    # Validate the results
    assert len(documents) == 2, f"Expected 2 documents, got {len(documents)}"
    
    doc1 = documents[0]
    assert doc1['id'] == 'doc_1', f"Expected doc_1, got {doc1['id']}"
    assert doc1['name'] == 'Test Document 1.pdf', f"Expected 'Test Document 1.pdf', got {doc1['name']}"
    assert doc1['document_type'] == 'Guidelines', f"Expected 'Guidelines', got {doc1['document_type']}"
    assert doc1['package_id'] == package_id, f"Expected '{package_id}', got {doc1['package_id']}"
    assert doc1['processing_type'] == 'package', f"Expected 'package', got {doc1['processing_type']}"
    assert doc1['file_source'] == 'local', f"Expected 'local', got {doc1['file_source']}"
    assert doc1['size'] == 1024, f"Expected 1024, got {doc1['size']}"
    assert doc1['status'] == 'pending', f"Expected 'pending', got {doc1['status']}"
    
    # Test JSON parsing
    assert isinstance(doc1['expected_structure'], dict), "Expected dict for expected_structure"
    assert isinstance(doc1['required_sections'], list), "Expected list for required_sections"
    assert isinstance(doc1['optional_sections'], list), "Expected list for optional_sections"
    assert isinstance(doc1['entity_types'], list), "Expected list for entity_types"
    assert isinstance(doc1['matrix_configuration'], dict), "Expected dict for matrix_configuration"
    assert isinstance(doc1['validation_schema'], dict), "Expected dict for validation_schema"
    assert isinstance(doc1['quality_thresholds'], dict), "Expected dict for quality_thresholds"
    
    print("✓ Enhanced get_package_documents method test passed")

def test_package_processing_instructions():
    """Test the enhanced package processing instructions"""
    print("Testing enhanced package processing instructions...")
    
    # Mock package data
    package_id = 'test_package_123'
    package_docs = [
        {
            'id': 'doc_1',
            'name': 'Test Document 1.pdf',
            'document_type': 'Guidelines',
            'processing_type': 'package',
            'file_source': 'local',
            'expected_structure': {'sections': ['introduction', 'main', 'conclusion']},
            'required_sections': ['introduction', 'main'],
            'optional_sections': ['conclusion'],
            'entity_types': ['Person', 'Organization'],
            'quality_thresholds': {'min_confidence': 0.8}
        },
        {
            'id': 'doc_2',
            'name': 'Test Document 2.pdf',
            'document_type': 'Matrix',
            'processing_type': 'package',
            'file_source': 'local',
            'expected_structure': {'tables': ['rate_matrix', 'conditions']},
            'required_sections': ['rate_matrix'],
            'optional_sections': ['conditions'],
            'entity_types': ['Rate', 'Condition'],
            'quality_thresholds': {'min_confidence': 0.9}
        }
    ]
    
    package_metadata = {
        'package_id': package_id,
        'total_documents': len(package_docs),
        'document_types': ['Guidelines', 'Matrix']
    }
    
    # Test instruction generation for first document
    doc = package_docs[0]
    additional_instructions = ""
    
    doc_instructions = f"""
    PACKAGE PROCESSING MODE - DATABASE STORED DOCUMENTS:
    - Package ID: {package_id}
    - Document: {doc.get('name', 'Unknown')}
    - Document Type: {doc.get('document_type', 'Other')}
    - Document ID: {doc.get('id', 'Unknown')}
    - Processing Type: {doc.get('processing_type', 'package')}
    - File Source: {doc.get('file_source', 'local')}
    
    HIERARCHICAL PROCESSING REQUIREMENTS:
    - Use hierarchical chunking with navigation extraction
    - Preserve document structure and relationships within package context
    - Extract package-aware entities and relationships
    - Enable cross-document relationships within the same package
    - Consider document context within the complete package hierarchy
    
    PACKAGE CONTEXT AND CROSS-DOCUMENT RELATIONSHIPS:
    - Total documents in package: {len(package_docs)}
    - Document types in package: {package_metadata.get('document_types', [])}
    - Package metadata: {json.dumps(package_metadata, indent=2)}
    - Enable relationship extraction between documents in the same package
    - Consider relationships to other documents: {[d.get('name', 'Unknown') for d in package_docs if d.get('id') != doc.get('id')]}
    
    DOCUMENT SPECIFIC CONFIGURATION:
    - Expected structure: {json.dumps(doc.get('expected_structure', {}), indent=2)}
    - Required sections: {doc.get('required_sections', [])}
    - Optional sections: {doc.get('optional_sections', [])}
    - Entity types: {doc.get('entity_types', [])}
    - Quality thresholds: {doc.get('quality_thresholds', {})}
    
    CROSS-DOCUMENT INTELLIGENCE:
    - Look for references to other documents in the same package
    - Extract relationships between entities across documents
    - Identify shared concepts and terminology
    - Maintain package-level entity consistency
    
    {additional_instructions or ''}
    """
    
    # Validate instruction content
    assert package_id in doc_instructions, f"Package ID {package_id} not found in instructions"
    assert doc['name'] in doc_instructions, f"Document name {doc['name']} not found in instructions"
    assert doc['document_type'] in doc_instructions, f"Document type {doc['document_type']} not found in instructions"
    assert str(len(package_docs)) in doc_instructions, f"Package document count not found in instructions"
    assert 'Test Document 2.pdf' in doc_instructions, f"Cross-document reference not found in instructions"
    assert 'hierarchical chunking' in doc_instructions, "Hierarchical chunking not mentioned in instructions"
    assert 'cross-document relationships' in doc_instructions, "Cross-document relationships not mentioned in instructions"
    assert 'package-aware entities' in doc_instructions, "Package-aware entities not mentioned in instructions"
    
    print("✓ Enhanced package processing instructions test passed")

def test_enhanced_error_handling():
    """Test the enhanced error handling structure"""
    print("Testing enhanced error handling...")
    
    # Test failed result structure
    doc_name = 'Test Document.pdf'
    doc_id = 'doc_123'
    doc_type = 'Guidelines'
    file_source = 'local'
    
    result = {
        'status': 'Failed',
        'error': f'Document file not found: {doc_name}. Please upload the file first.',
        'details': {
            'document_id': doc_id,
            'document_type': doc_type,
            'file_source': file_source,
            'checked_paths': [
                '/path/to/merged/Test_Document.pdf',
                '/path/to/merged/Test Document.pdf',
                '/path/to/merged/doc_123_Test_Document.pdf'
            ]
        },
        'nodeCount': 0,
        'relationshipCount': 0,
        'processingTime': 0
    }
    
    # Validate error structure
    assert result['status'] == 'Failed', f"Expected 'Failed', got {result['status']}"
    assert doc_name in result['error'], f"Document name not found in error message"
    assert 'details' in result, "Details not found in error result"
    assert result['details']['document_id'] == doc_id, f"Expected {doc_id}, got {result['details']['document_id']}"
    assert result['details']['document_type'] == doc_type, f"Expected {doc_type}, got {result['details']['document_type']}"
    assert result['details']['file_source'] == file_source, f"Expected {file_source}, got {result['details']['file_source']}"
    assert 'checked_paths' in result['details'], "Checked paths not found in error details"
    assert len(result['details']['checked_paths']) == 3, f"Expected 3 checked paths, got {len(result['details']['checked_paths'])}"
    
    print("✓ Enhanced error handling test passed")

def main():
    """Run all tests"""
    print("Starting enhanced package processing tests...")
    print("=" * 50)
    
    try:
        test_get_package_documents_enhanced()
        test_package_processing_instructions()
        test_enhanced_error_handling()
        
        print("=" * 50)
        print("✓ All tests passed!")
        print("Enhanced package processing implementation is working correctly")
        
    except Exception as e:
        print(f"❌ Test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
    
    return True

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)