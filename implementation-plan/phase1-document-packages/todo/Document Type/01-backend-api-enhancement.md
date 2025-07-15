# Backend API Enhancement

## Overview
Implement backend API changes to support pre-upload document type selection and eliminate relationship creation failures.

## New API Endpoint: Expected Documents

### Endpoint: `GET /products/{product_id}/expected-documents`

**Purpose**: Return list of expected PackageDocument templates for a product with current upload status.

**Implementation**:
```python
@app.get("/products/{product_id}/expected-documents")
async def get_expected_documents(
    product_id: str,
    uri=Form(None),
    userName=Form(None),
    password=Form(None),
    database=Form(None)
):
    """
    Get list of expected documents for a product with upload status.
    Used to power the document type slots interface.
    """
```

**Response Format**:
```json
{
  "success": true,
  "data": {
    "product_id": "prod_non-agency_advantage_1752608874",
    "product_name": "Non-Agency Advantage",
    "expected_documents": [
      {
        "id": "pkgdoc_prod_non-agency_advantage_1752608874_guidelines_1752608875",
        "document_type": "Guidelines",
        "document_name": "Non-Agency Advantage Guidelines",
        "is_required": true,
        "upload_status": "uploaded",
        "uploaded_file": {
          "fileName": "NAA-Guidelines.pdf",
          "fileSize": 2048576,
          "uploadDate": "2025-07-15T19:49:08Z"
        },
        "validation_rules": {
          "accepted_types": [".pdf", ".docx"],
          "max_file_size": 52428800,
          "content_validation": "guidelines_structure"
        }
      },
      {
        "id": "pkgdoc_prod_non-agency_advantage_1752608874_matrix_1752608876",
        "document_type": "Matrix", 
        "document_name": "Non-Agency Advantage Matrix",
        "is_required": true,
        "upload_status": "empty",
        "uploaded_file": null,
        "validation_rules": {
          "accepted_types": [".pdf", ".xlsx", ".xls"],
          "max_file_size": 52428800,
          "content_validation": "matrix_structure"
        }
      }
    ],
    "completion_status": {
      "total_expected": 2,
      "uploaded_count": 1,
      "completion_percentage": 50
    }
  }
}
```

## Database Method Implementation

### New Method: `get_expected_documents_for_product`

**File**: `backend/src/graphDB_dataAccess.py`

```python
def get_expected_documents_for_product(self, product_id: str) -> list:
    """
    Get all expected documents for a product with their upload status.
    Returns list of PackageDocument nodes with associated uploaded Document nodes.
    """
    try:
        with self.driver.session() as session:
            query = """
            MATCH (prod:Product {product_id: $product_id})-[:EXPECTS_DOCUMENT]->(pd:PackageDocument)
            
            // Get uploaded document if it exists
            OPTIONAL MATCH (pd)-[:HAS_UPLOADED]->(d:Document)
            
            RETURN pd.document_id as document_id,
                   pd.document_type as document_type,
                   pd.document_name as document_name,
                   pd.expected_structure as expected_structure,
                   pd.validation_rules as validation_rules,
                   pd.required_sections as required_sections,
                   pd.optional_sections as optional_sections,
                   pd.has_upload as has_upload,
                   pd.processing_status as processing_status,
                   
                   // Document details if uploaded
                   d.fileName as uploaded_filename,
                   d.fileSize as uploaded_file_size,
                   d.created_at as upload_date,
                   d.Status as processing_status
                   
            ORDER BY pd.document_type, pd.document_name
            """
            
            result = session.run(query, {'product_id': product_id})
            
            expected_documents = []
            for record in result:
                doc_data = {
                    'id': record.get('document_id'),
                    'document_type': record.get('document_type'),
                    'document_name': record.get('document_name'),
                    'is_required': True,  # For now, all PackageDocuments are required
                    'upload_status': 'uploaded' if record.get('has_upload') else 'empty',
                    'uploaded_file': None,
                    'validation_rules': self._get_validation_rules_for_document_type(record.get('document_type')),
                    'expected_structure': json.loads(record.get('expected_structure', '{}')),
                    'required_sections': record.get('required_sections', []),
                    'optional_sections': record.get('optional_sections', [])
                }
                
                # Add uploaded file details if available
                if record.get('uploaded_filename'):
                    doc_data['uploaded_file'] = {
                        'fileName': record.get('uploaded_filename'),
                        'fileSize': record.get('uploaded_file_size'),
                        'uploadDate': record.get('upload_date'),
                        'processingStatus': record.get('processing_status')
                    }
                
                expected_documents.append(doc_data)
            
            return expected_documents
            
    except Exception as e:
        logging.error(f"Error getting expected documents for product {product_id}: {str(e)}")
        return []
```

### Helper Method: Document Type Validation Rules

```python
def _get_validation_rules_for_document_type(self, document_type: str) -> dict:
    """Get validation rules based on document type"""
    
    validation_rules = {
        'Guidelines': {
            'accepted_types': ['.pdf', '.docx'],
            'accepted_mime_types': ['application/pdf', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'],
            'max_file_size': 50 * 1024 * 1024,  # 50MB
            'content_validation': 'guidelines_structure',
            'description': 'Underwriting guidelines and policy documents'
        },
        'Matrix': {
            'accepted_types': ['.pdf', '.xlsx', '.xls', '.csv'],
            'accepted_mime_types': ['application/pdf', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', 'application/vnd.ms-excel', 'text/csv'],
            'max_file_size': 25 * 1024 * 1024,  # 25MB
            'content_validation': 'matrix_structure',
            'description': 'Rate matrices and pricing tables'
        },
        'Supporting': {
            'accepted_types': ['.pdf', '.docx', '.xlsx', '.xls'],
            'accepted_mime_types': ['application/pdf', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', 'application/vnd.ms-excel'],
            'max_file_size': 30 * 1024 * 1024,  # 30MB
            'content_validation': 'supporting_document',
            'description': 'Supporting documentation and supplements'
        },
        'Other': {
            'accepted_types': ['.pdf', '.docx', '.xlsx', '.xls', '.txt', '.csv'],
            'accepted_mime_types': ['application/pdf', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', 'application/vnd.ms-excel', 'text/plain', 'text/csv'],
            'max_file_size': 100 * 1024 * 1024,  # 100MB
            'content_validation': 'none',
            'description': 'Other documents and miscellaneous files'
        }
    }
    
    return validation_rules.get(document_type, validation_rules['Other'])
```

## Enhanced Upload Endpoint

### Modifications to `/upload` endpoint

**File**: `backend/score.py`

**New Parameters**:
- `expectedDocumentId` (optional): ID of the PackageDocument template
- `preSelectedDocumentType` (optional): Pre-selected document type to avoid post-upload changes

```python
@app.post("/upload")
async def upload_large_file_into_chunks(
    file: UploadFile = File(...), 
    chunkNumber=Form(None), 
    totalChunks=Form(None), 
    originalname=Form(None), 
    model=Form(None), 
    uri=Form(None), 
    userName=Form(None), 
    password=Form(None), 
    database=Form(None),
    email=Form(None),
    categoryId=Form(None), 
    categoryName=Form(None), 
    productId=Form(None), 
    productName=Form(None), 
    documentType=Form(None),
    expectedDocumentId=Form(None),  # NEW: PackageDocument template ID
    preSelectedDocumentType=Form(None)  # NEW: Pre-selected type
):
```

**Enhanced Logic**:
```python
# Create package context with pre-selected document type
package_context = None
if categoryId or productId:
    # Use pre-selected document type if provided, otherwise fall back to documentType
    final_document_type = preSelectedDocumentType or documentType or 'Other'
    
    package_context = {
        'categoryId': categoryId,
        'categoryName': categoryName,
        'productId': productId,
        'productName': productName,
        'documentType': final_document_type,
        'expectedDocumentId': expectedDocumentId  # Link to PackageDocument template
    }

# Enhanced package metadata with template linking
if package_context and package_context.get('productId'):
    package_metadata = {
        'categoryId': package_context.get('categoryId'),
        'categoryName': package_context.get('categoryName'),
        'productId': package_context.get('productId'),
        'productName': package_context.get('productName'),
        'documentType': package_context.get('documentType'),
        'expectedDocumentId': package_context.get('expectedDocumentId'),  # NEW
        'package_upload': True,
        'created_via_package': True
    }
    
    # Update the Document node with package metadata and immediately link to PackageDocument
    graphDb_data_Access.add_package_metadata_to_document(originalname, package_metadata)
    
    # If expectedDocumentId is provided, immediately create the relationship
    if package_context.get('expectedDocumentId'):
        success = graphDb_data_Access.link_uploaded_document_to_package_document(
            originalname, 
            package_context.get('expectedDocumentId')
        )
        if success:
            logging.info(f"Immediately linked {originalname} to PackageDocument {package_context.get('expectedDocumentId')}")
        else:
            logging.warning(f"Failed to immediately link {originalname} to PackageDocument")
```

## Implementation Steps

### Step 1: Database Method
1. Add `get_expected_documents_for_product` method to `graphDB_dataAccess.py`
2. Add `_get_validation_rules_for_document_type` helper method
3. Test with existing package data

### Step 2: API Endpoint
1. Implement `GET /products/{product_id}/expected-documents` endpoint
2. Add error handling and logging
3. Test with Postman/curl

### Step 3: Enhanced Upload
1. Modify `/upload` endpoint to accept new parameters
2. Update package metadata logic to use pre-selected types
3. Add immediate PackageDocument linking

### Step 4: Validation
1. Add request validation for new parameters
2. Implement document type compatibility checks
3. Add comprehensive error responses

## Testing Plan

### Unit Tests
- Test `get_expected_documents_for_product` with various product IDs
- Validate response format and data accuracy
- Test edge cases (no documents, invalid product ID)

### Integration Tests
- Test full upload workflow with pre-selected document types
- Verify immediate relationship creation
- Test error handling for invalid document types

### API Tests
- Test GET `/products/{product_id}/expected-documents` endpoint
- Verify response format and performance
- Test with different authentication scenarios

## Success Criteria
1. ✅ New endpoint returns expected documents with correct status
2. ✅ Upload endpoint accepts and uses pre-selected document types
3. ✅ Relationships are created immediately during upload
4. ✅ No post-upload document type changes needed
5. ✅ All existing functionality continues to work