# Two-Structure Architecture Implementation Guide

## 🚀 **IMPLEMENTATION STATUS: COMPLETE**
✅ **Package Management Structure**: DocumentPackage → MortgageCategory → Product → PackageDocument  
✅ **Knowledge Extraction Structure**: DocumentPackage (knowledge) → MortgageCategory (knowledge) → Product (knowledge) → Document → Content  
✅ **Cross-Structure Linking**: Document serves as bridge between both structures  
✅ **Processing-Time Creation**: Knowledge structure created only during document processing  

## Overview

The Two-Structure Architecture provides clear separation between **Package Management** (templates/expectations) and **Knowledge Extraction** (processed content), enabling sophisticated mortgage document processing while maintaining clean organizational structure.

## Architectural Principles

### 1. **Clear Separation of Concerns**
- **Package Management**: What documents are expected and their organizational structure
- **Knowledge Extraction**: What content was actually extracted and processed

### 2. **Timing-Based Creation**
- **Package Management**: Created immediately when users set up document packages
- **Knowledge Extraction**: Created only during document processing

### 3. **Shared Identifiers**
- Both structures use the same `package_id`, `category_code`, and `product_id` for linking
- `knowledge_extracted: true` flag distinguishes knowledge structure nodes

### 4. **Document as Bridge**
- Document nodes serve as the connection point between both structures
- Documents fulfill PackageDocuments and are processed into knowledge content

## Structure 1: Package Management (Templates/Expectations)

### Purpose
- Define expected document structure and hierarchy
- Track what documents should be uploaded and processed
- Manage package organization and metadata
- Provide templates for document processing

### Node Types
```cypher
(:DocumentPackage {package_id, package_name, description, workspace_id, tenant_id})
(:MortgageCategory {category_code, display_name, description, regulatory_framework})
(:Product {product_id, product_name, description, key_features, target_borrowers})
(:PackageDocument {document_id, document_name, document_type, has_upload, processing_status})
(:Document {fileName, fileSize, fileType, status, package_upload: true})
```

### Relationships
```cypher
(DocumentPackage)-[:CONTAINS_CATEGORY]->(MortgageCategory)
(MortgageCategory)-[:CONTAINS]->(Product)
(Product)-[:CONTAINS]->(PackageDocument)
(PackageDocument)-[:HAS_UPLOADED]->(Document)
```

### Creation Timeline
1. **User creates category** → DocumentPackage + MortgageCategory created
2. **User creates product** → Product + PackageDocument templates created
3. **User uploads file** → Document created
4. **User sets document type** → PackageDocument-Document relationship created

### Sample Cypher Queries
```cypher
// Get all expected documents in a package
MATCH (dp:DocumentPackage {package_id: $packageId})
      -[:CONTAINS_CATEGORY]->(:MortgageCategory)
      -[:CONTAINS]->(:Product)
      -[:CONTAINS]->(pd:PackageDocument)
RETURN pd.document_name, pd.document_type, pd.has_upload, pd.processing_status

// Check package completion status
MATCH (dp:DocumentPackage {package_id: $packageId})
      -[:CONTAINS_CATEGORY]->(:MortgageCategory)
      -[:CONTAINS]->(:Product)
      -[:CONTAINS]->(pd:PackageDocument)
OPTIONAL MATCH (pd)-[:HAS_UPLOADED]->(d:Document)
RETURN pd.document_name, 
       CASE WHEN d IS NOT NULL THEN true ELSE false END as has_upload,
       pd.processing_status
```

## Structure 2: Knowledge Extraction (Content/Results)

### Purpose
- Store actual extracted knowledge and content
- Maintain processing results and relationships
- Enable sophisticated querying and retrieval
- Provide knowledge graph for AI interactions

### Node Types
```cypher
(:DocumentPackage {package_id, package_name, knowledge_extracted: true, last_processed})
(:MortgageCategory {category_code, display_name, knowledge_extracted: true, last_processed})
(:Product {product_id, product_name, knowledge_extracted: true, last_processed})
(:Document {fileName, documentType, categoryId, productId})
(:Guidelines {guidelines_id, content, sections, discovered_programs, processed_at})
(:Matrix {matrix_id, content, dimensions, cells, processed_at})
```

### Relationships
```cypher
(DocumentPackage {knowledge_extracted: true})-[:CONTAINS_CATEGORY]->(MortgageCategory {knowledge_extracted: true})
(MortgageCategory {knowledge_extracted: true})-[:CONTAINS]->(Product {knowledge_extracted: true})
(Product {knowledge_extracted: true})-[:EXTRACTED_FROM_DOCUMENT]->(Document)
(Document)-[:PROCESSED_INTO]->(Guidelines)
(Document)-[:PROCESSED_INTO]->(Matrix)
```

### Creation Timeline
1. **Document processing starts** → Knowledge DocumentPackage, MortgageCategory, Product created
2. **Content extraction** → Guidelines/Matrix nodes created
3. **Processing completion** → All relationships established

### Sample Cypher Queries
```cypher
// Get all extracted content from a package
MATCH (dp:DocumentPackage {package_id: $packageId, knowledge_extracted: true})
      -[:CONTAINS_CATEGORY]->(:MortgageCategory {knowledge_extracted: true})
      -[:CONTAINS]->(:Product {knowledge_extracted: true})
      -[:EXTRACTED_FROM_DOCUMENT]->(d:Document)
      -[:PROCESSED_INTO]->(content)
RETURN d.fileName, labels(content)[0] as content_type, content

// Find relationships between different categories in same package
MATCH (dp:DocumentPackage {knowledge_extracted: true})
      -[:CONTAINS_CATEGORY]->(cat1:MortgageCategory {knowledge_extracted: true})
      -[:CONTAINS]->(:Product {knowledge_extracted: true})
      -[:EXTRACTED_FROM_DOCUMENT]->(:Document)
      -[:PROCESSED_INTO]->(content1),
      (dp)-[:CONTAINS_CATEGORY]->(cat2:MortgageCategory {knowledge_extracted: true})
      -[:CONTAINS]->(:Product {knowledge_extracted: true})  
      -[:EXTRACTED_FROM_DOCUMENT]->(:Document)
      -[:PROCESSED_INTO]->(content2)
WHERE cat1.category_code <> cat2.category_code
RETURN cat1.category_code, cat2.category_code, content1, content2
```

## Implementation Details

### Backend Components

#### 1. Database Access Layer
```python
# graphDB_dataAccess.py
def create_document_package_node(self, package_metadata: dict) -> bool:
    """Create DocumentPackage root node for package management"""

def create_knowledge_structure_nodes(self, file_name: str, package_metadata: dict) -> bool:
    """Create knowledge extraction versions of DocumentPackage, MortgageCategory and Product"""

def link_category_to_package(self, package_id: str, category_code: str) -> bool:
    """Create CONTAINS_CATEGORY relationship between DocumentPackage and MortgageCategory"""

def _link_document_to_package_document(self, file_name: str, document_type: str, product_id: str) -> bool:
    """Link an uploaded Document to its corresponding PackageDocument"""
```

#### 2. API Endpoints
```python
# score.py
@app.post("/document-packages")
async def create_document_package(...):
    """Create DocumentPackage root node for package management"""

@app.post("/categories")
async def create_category(..., package_id=Form(None)):
    """Create category and optionally link to DocumentPackage"""
```

#### 3. Processing Pipeline
```python
# main.py
def create_knowledge_structure_nodes(file_name: str, package_metadata: dict):
    """Create knowledge structure during document processing"""

def create_processed_content_nodes(file_name, document_type, content_data, graph_db):
    """Create Guidelines or Matrix nodes from processed content"""
```

### Frontend Components

#### 1. Package Management UI
```typescript
// PackageWorkspace.tsx
const handleAddCategory = useCallback(async (categoryType: string, categoryName: string) => {
  // Check if first category - create DocumentPackage if needed
  if (isFirstCategory) {
    const packageResponse = await createDocumentPackageNode(packageName, packageDescription);
    setCurrentPackageId(packageResponse.data.package_id);
  }
  
  // Create category and link to DocumentPackage
  const response = await createCategory(categoryType, categoryName, categoryDescription, currentPackageId);
});
```

#### 2. API Integration
```typescript
// PackageAPI.ts
export const createDocumentPackageNode = async (packageName: string, packageDescription?: string) => {
  // Create DocumentPackage root node
};

export const createCategory = async (categoryCode: string, categoryName: string, categoryDescription?: string, packageId?: string) => {
  // Create category and optionally link to package
};
```

## Benefits of Two-Structure Architecture

### 1. **Clear Separation**
- Package management concerns separated from knowledge extraction
- Easier to understand and maintain
- Clear boundaries between planning and processing

### 2. **Flexible Querying**
- Query package structure without knowledge extraction overhead
- Query knowledge content without package management noise
- Cross-structure queries when needed

### 3. **Status Tracking**
- Package management tracks what's expected vs. uploaded
- Knowledge structure tracks what's been processed
- Clear visibility into completion status

### 4. **Scalability**
- Package structure remains lightweight
- Knowledge structure can grow with complex content
- Independent optimization of both structures

### 5. **Multi-Package Support**
- Multiple categories can be connected via DocumentPackage root
- Package-level analytics and queries
- Clear organizational hierarchy

## Usage Patterns

### Package Setup Workflow
```cypher
// 1. Create DocumentPackage and first category
CREATE (dp:DocumentPackage {package_id: "pkg_123", package_name: "Q1 2024 Package"})
CREATE (mc:MortgageCategory {category_code: "NQM", display_name: "Non-QM"})
CREATE (dp)-[:CONTAINS_CATEGORY]->(mc)

// 2. Add products and document templates
CREATE (p:Product {product_id: "prod_123", product_name: "Bank Statement"})
CREATE (pd:PackageDocument {document_name: "Bank Statement Guidelines", document_type: "Guidelines"})
CREATE (mc)-[:CONTAINS]->(p)-[:CONTAINS]->(pd)

// 3. Upload and link documents
CREATE (d:Document {fileName: "bs_guidelines.pdf"})
CREATE (pd)-[:HAS_UPLOADED]->(d)
```

### Processing Workflow
```cypher
// 1. Create knowledge structure during processing
CREATE (dp_k:DocumentPackage {package_id: "pkg_123", knowledge_extracted: true})
CREATE (mc_k:MortgageCategory {category_code: "NQM", knowledge_extracted: true})
CREATE (p_k:Product {product_id: "prod_123", knowledge_extracted: true})
CREATE (dp_k)-[:CONTAINS_CATEGORY]->(mc_k)-[:CONTAINS]->(p_k)

// 2. Link to document and create content
MATCH (d:Document {fileName: "bs_guidelines.pdf"})
CREATE (p_k)-[:EXTRACTED_FROM_DOCUMENT]->(d)
CREATE (g:Guidelines {content: "extracted guidelines content..."})
CREATE (d)-[:PROCESSED_INTO]->(g)
```

### Cross-Structure Queries
```cypher
// Find all documents that need processing
MATCH (dp:DocumentPackage {package_id: $packageId})
      -[:CONTAINS_CATEGORY]->(:MortgageCategory)
      -[:CONTAINS]->(:Product)
      -[:CONTAINS]->(pd:PackageDocument)-[:HAS_UPLOADED]->(d:Document)
WHERE NOT EXISTS {
  MATCH (dp_k:DocumentPackage {package_id: $packageId, knowledge_extracted: true})
        -[:CONTAINS_CATEGORY]->(:MortgageCategory {knowledge_extracted: true})
        -[:CONTAINS]->(:Product {knowledge_extracted: true})
        -[:EXTRACTED_FROM_DOCUMENT]->(d)
}
RETURN d.fileName, pd.document_type
```

## Quality Assurance

### Validation Rules
1. **Package Management Structure**
   - Every DocumentPackage must have at least one MortgageCategory
   - Every MortgageCategory must have at least one Product
   - Every Product must have at least one PackageDocument
   - Document-PackageDocument relationships must match document_type

2. **Knowledge Extraction Structure**
   - Knowledge nodes must have corresponding package management nodes
   - Knowledge structures must be created only during processing
   - Content nodes (Guidelines/Matrix) must be linked to Documents
   - All knowledge nodes must have `knowledge_extracted: true`

3. **Cross-Structure Consistency**
   - Same package_id in both structures
   - Same category_code and product_id in both structures
   - Documents must exist in package management before knowledge creation

### Monitoring Queries
```cypher
// Check for orphaned knowledge nodes
MATCH (n {knowledge_extracted: true})
WHERE NOT EXISTS {
  MATCH (orig) 
  WHERE orig.package_id = n.package_id OR orig.category_code = n.category_code OR orig.product_id = n.product_id
  AND NOT exists(orig.knowledge_extracted)
}
RETURN n

// Check processing completion
MATCH (dp:DocumentPackage)-[:CONTAINS_CATEGORY]->(:MortgageCategory)-[:CONTAINS]->(:Product)-[:CONTAINS]->(pd:PackageDocument)-[:HAS_UPLOADED]->(d:Document)
OPTIONAL MATCH (dp_k:DocumentPackage {package_id: dp.package_id, knowledge_extracted: true})-[:CONTAINS_CATEGORY]->(:MortgageCategory {knowledge_extracted: true})-[:CONTAINS]->(:Product {knowledge_extracted: true})-[:EXTRACTED_FROM_DOCUMENT]->(d)
RETURN dp.package_name, 
       COUNT(d) as total_documents, 
       COUNT(dp_k) as processed_documents,
       ROUND(100.0 * COUNT(dp_k) / COUNT(d), 1) as completion_percentage
```

## Future Enhancements

### Phase 2: Matrix Intelligence
- Enhanced Matrix content nodes with multi-dimensional classification
- Cross-document matrix relationships
- Matrix-guidelines mapping validation

### Phase 3: Advanced Knowledge Graph
- Multi-layer knowledge structure
- Enhanced entity relationships
- Advanced querying capabilities

### Phase 4: Production Features
- Audit trails across both structures
- Advanced monitoring and analytics
- Export capabilities for both structures

This two-structure architecture provides a solid foundation for sophisticated mortgage document processing while maintaining clear separation of concerns and enabling flexible querying and analytics capabilities.