# 3-Tier Hierarchy Design Document

## 📋 Overview

This document details the implementation of the 3-tier hierarchy for mortgage document packages in the LLM Graph Builder system. The hierarchy enables proper document isolation, product-level relationships, and scalable package management.

**Implementation Date**: 2025-07-15  
**Status**: ✅ Complete + File Upload Integration  
**Version**: 1.1  

## 🏗️ Architecture Decision

### **Problem Statement**
The original 2-tier structure (`DocumentPackage -> PackageDocument`) was insufficient for real-world mortgage document organization. We needed proper isolation between products within the same category.

### **Solution: 3-Tier Hierarchy**
```
[DocumentPackage] -> [PackageProduct] -> [PackageDocument]
[NQM] -> [NAA] -> [Guidelines Document], [Matrix Document]
[NQM] -> [FHA] -> [Guidelines Document], [Matrix Document]
```

### **Business Justification**
1. **Real-World Structure**: Reflects actual mortgage industry organization
2. **Document Isolation**: Prevents cross-product contamination
3. **Product Relationships**: Enables dependencies between products
4. **Processing Priority**: Allows ordered processing by product importance
5. **Scalability**: Supports complex document packages

## 🗃️ Database Schema

### **Node Types**

#### 1. DocumentPackage (Root Level)
```cypher
CREATE (pkg:DocumentPackage {
  package_id: $package_id,           // Unique identifier
  package_name: $package_name,       // Human-readable name
  tenant_id: $tenant_id,             // Organization identifier
  category: $category,               // NQM, RTL, SBC, CONV
  version: $version,                 // Package version
  status: $status,                   // DRAFT, ACTIVE, ARCHIVED
  created_by: $created_by,           // Creator identifier
  template_type: $template_type,     // Template used
  created_at: $created_at,           // Creation timestamp
  updated_at: $updated_at,           // Last update timestamp
  template_mappings: $template_mappings, // Template configuration
  validation_rules: $validation_rules    // Validation configuration
})
```

#### 2. PackageProduct (Middle Level)
```cypher
CREATE (prod:PackageProduct {
  product_id: $product_id,           // Unique identifier
  product_name: $product_name,       // Human-readable name
  product_type: $product_type,       // core, supplemental, conditional
  tier_level: $tier_level,           // 1-3 hierarchy level
  processing_priority: $processing_priority, // 1-3 priority level
  dependencies: $dependencies,       // List of dependent product IDs
  created_at: $created_at,           // Creation timestamp
  updated_at: $updated_at,           // Last update timestamp
  metadata: $metadata                // Additional configuration
})
```

#### 3. PackageDocument (Leaf Level)
```cypher
CREATE (doc:PackageDocument {
  document_id: $document_id,         // Unique identifier
  document_name: $document_name,     // Human-readable name
  document_type: $document_type,     // guidelines, matrix, rate_sheet
  expected_structure: $expected_structure, // Expected document structure
  required_sections: $required_sections,   // Required sections
  optional_sections: $optional_sections,   // Optional sections
  chunking_strategy: $chunking_strategy,   // Chunking approach
  entity_types: $entity_types,             // Expected entity types
  matrix_configuration: $matrix_configuration, // Matrix-specific config
  validation_schema: $validation_schema,       // Validation rules
  quality_thresholds: $quality_thresholds,    // Quality metrics
  created_at: $created_at,           // Creation timestamp
  updated_at: $updated_at            // Last update timestamp
})
```

### **Relationships**

#### 1. Package-to-Product Relationship
```cypher
CREATE (pkg:DocumentPackage)-[:CONTAINS]->(prod:PackageProduct)
```
- **Cardinality**: One-to-Many
- **Meaning**: A package contains multiple products
- **Properties**: None

#### 2. Product-to-Document Relationship
```cypher
CREATE (prod:PackageProduct)-[:CONTAINS]->(doc:PackageDocument)
```
- **Cardinality**: One-to-Many
- **Meaning**: A product contains multiple documents
- **Properties**: None

#### 3. Backwards Compatibility (2-Tier)
```cypher
CREATE (pkg:DocumentPackage)-[:CONTAINS]->(doc:PackageDocument)
```
- **Cardinality**: One-to-Many
- **Meaning**: Direct package-to-document relationship
- **Usage**: Legacy packages without products

## 🔧 Implementation Details

### **Backend Implementation**

#### 1. API Endpoint Enhancement
```python
# Added products parameter to /packages endpoint
@app.post("/packages")
async def create_package(
    # ... existing parameters ...
    products=Form(None)  # NEW: Support for 3-tier hierarchy
):
    # Parse products if provided (for 3-tier hierarchy)
    if products:
        try:
            package_config['products'] = json.loads(products)
        except json.JSONDecodeError:
            return create_api_response('Failed', message='Invalid products JSON format')
```

#### 2. Entity Classes
```python
# PackageProduct Entity
@dataclass
class PackageProduct:
    product_id: str
    product_name: str
    product_type: ProductType  # core, supplemental, conditional
    tier_level: int = 1
    processing_priority: int = 1
    dependencies: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)
```

#### 3. Enhanced Package Manager
```python
# Enhanced _store_package_in_db method
def _store_package_in_db(self, package: DocumentPackage) -> None:
    # Store products (3-tier hierarchy)
    for product in package.products:
        self.graph_db.create_package_product(package.package_id, product_data)
        
        # Store documents associated with this product
        product_documents = product.metadata.get('documents', [])
        for doc_config in product_documents:
            # Create document linked to product (3-tier hierarchy)
            self.graph_db.create_package_document(package.package_id, doc_data, product.product_id)
```

#### 4. Database Access Methods
```python
# Create product node
def create_package_product(self, product_data: Dict[str, Any]) -> str:
    query = """
    CREATE (prod:PackageProduct {
        product_id: $product_id,
        product_name: $product_name,
        product_type: $product_type,
        tier_level: $tier_level,
        processing_priority: $processing_priority,
        dependencies: $dependencies,
        created_at: $created_at,
        updated_at: $updated_at,
        metadata: $metadata
    })
    RETURN prod.product_id as product_id
    """
    
# Get package documents with product traversal
def get_package_documents(self, package_id: str) -> list:
    query = """
    MATCH (p:DocumentPackage {package_id: $package_id})
    OPTIONAL MATCH (p)-[:CONTAINS]->(prod:PackageProduct)-[:CONTAINS]->(d:PackageDocument)
    OPTIONAL MATCH (p)-[:CONTAINS]->(d2:PackageDocument)
    WHERE NOT (p)-[:CONTAINS]->(:PackageProduct)-[:CONTAINS]->(d2)
    RETURN d, d2, prod
    ORDER BY prod.processing_priority, d.document_name
    """
```

#### 3. Package Processing Enhancement
```python
# Enhanced processing with product context
for product in package_products:
    product_context = {
        'product_id': product.product_id,
        'product_name': product.product_name,
        'product_type': product.product_type,
        'tier_level': product.tier_level,
        'processing_priority': product.processing_priority
    }
    
    for document in product.documents:
        enhanced_instructions = f"""
        PACKAGE PROCESSING MODE:
        - Package: {package_name}
        - Product: {product.product_name} (Type: {product.product_type})
        - Document: {document.document_name}
        - Tier Level: {product.tier_level}
        - Processing Priority: {product.processing_priority}
        
        CROSS-PRODUCT RELATIONSHIPS:
        - Enable relationships between products in same package
        - Maintain product-level isolation
        - Extract product dependencies
        """
```

### **Frontend Implementation**

#### 1. File Upload Integration
```typescript
// Implemented actual file upload to backend
const handlePackageFilesUpload = useCallback(async (files: File[], context: PackageSelectionContext) => {
    // Upload files to backend filesystem
    for (const file of files) {
        const response = await uploadAPI(file, model, chunkNumber, totalChunks, file.name);
        
        // Update file status after successful upload
        setFilesData(prev => prev.map(f => 
            f.name === file.name 
                ? { ...f, status: 'New', uploadProgress: 100 }
                : f
        ));
    }
}, [model, setFilesData]);
```

#### 2. Package Structure Conversion
```typescript
// Convert frontend hierarchy to 3-tier format
const convertPackageToDatabase = () => {
    const products = [];
    
    Object.values(packageHierarchy.categories).forEach(category => {
        category.products.forEach(product => {
            const productDocuments = [];
            
            product.documents.forEach(doc => {
                productDocuments.push({
                    document_name: doc.name,
                    document_type: mapDocumentType(doc.document_type),
                    document_id: doc.id,
                    // ... other document properties
                });
            });
            
            products.push({
                product_name: product.name,
                product_id: product.id,
                product_type: 'core',
                tier_level: 1,
                processing_priority: 1,
                documents: productDocuments
            });
        });
    });
    
    return { products, ...packageData };
};
```

#### 3. Reset Package Functionality
```typescript
// Added reset button to clear package state
const handleResetPackage = useCallback(() => {
    // Clear the package hierarchy state
    setPackageHierarchy({
        categories: {},
        flattenedItems: [],
        totalFiles: 0,
        totalCategories: 0,
        totalProducts: 0
    });
    
    // Clear stored package data from localStorage
    localStorage.removeItem('packageHierarchy');
    localStorage.removeItem('packageData');
    localStorage.removeItem('selectedFiles');
    
    showSuccessToast('Package workspace reset successfully');
}, []);
```

#### 4. API Integration
```typescript
// Enhanced API call with products
export const createDocumentPackage = async (
    formData: PackageFormData & { products?: any[] }
): Promise<PackageAPIResponse<DocumentPackage>> => {
    const form = new FormData();
    
    // Add products for 3-tier hierarchy
    if (formData.products && formData.products.length > 0) {
        form.append('products', JSON.stringify(formData.products));
    }
    
    const response = await api({
        method: 'POST',
        url: '/packages',
        data: form,
        headers: { 'Content-Type': 'multipart/form-data' }
    });
    
    return response.data;
};
```

## 🔍 Query Patterns

### **Common Query Patterns**

#### 1. Get All Documents in Package (3-Tier)
```cypher
MATCH (p:DocumentPackage {package_id: $package_id})
       -[:CONTAINS]->(prod:PackageProduct)
       -[:CONTAINS]->(d:PackageDocument)
RETURN p.package_name, 
       prod.product_name, 
       prod.processing_priority,
       d.document_name, 
       d.document_type
ORDER BY prod.processing_priority, d.document_name
```

#### 2. Get Products in Priority Order
```cypher
MATCH (p:DocumentPackage {package_id: $package_id})
       -[:CONTAINS]->(prod:PackageProduct)
RETURN prod
ORDER BY prod.processing_priority, prod.product_name
```

#### 3. Find Product Dependencies
```cypher
MATCH (p:DocumentPackage {package_id: $package_id})
       -[:CONTAINS]->(prod:PackageProduct)
WHERE size(prod.dependencies) > 0
UNWIND prod.dependencies as dep_id
MATCH (p)-[:CONTAINS]->(dep:PackageProduct {product_id: dep_id})
RETURN prod.product_name, dep.product_name as dependency
```

#### 4. Cross-Product Document Relationships
```cypher
MATCH (p:DocumentPackage {package_id: $package_id})
       -[:CONTAINS]->(prod1:PackageProduct)
       -[:CONTAINS]->(d1:PackageDocument)
MATCH (p)-[:CONTAINS]->(prod2:PackageProduct)
       -[:CONTAINS]->(d2:PackageDocument)
WHERE prod1 <> prod2
MATCH (d1)-[r:RELATES_TO|REFERENCES|SUPPORTS]->(d2)
RETURN prod1.product_name, d1.document_name,
       type(r) as relationship_type,
       prod2.product_name, d2.document_name
```

#### 5. Backwards Compatibility (2-Tier)
```cypher
MATCH (p:DocumentPackage {package_id: $package_id})
       -[:CONTAINS]->(d:PackageDocument)
WHERE NOT (p)-[:CONTAINS]->(:PackageProduct)-[:CONTAINS]->(d)
RETURN p.package_name, d.document_name, d.document_type
ORDER BY d.document_name
```

## 🚀 Performance Optimizations

### **Database Indexes**
```cypher
// Primary indexes for performance
CREATE INDEX package_id_index FOR (p:DocumentPackage) ON (p.package_id)
CREATE INDEX product_id_index FOR (prod:PackageProduct) ON (prod.product_id)
CREATE INDEX document_id_index FOR (d:PackageDocument) ON (d.document_id)

// Composite indexes for common queries
CREATE INDEX package_product_priority FOR (prod:PackageProduct) ON (prod.processing_priority)
CREATE INDEX document_type_index FOR (d:PackageDocument) ON (d.document_type)
```

### **Query Optimization**
```cypher
// Efficient query with proper index usage
MATCH (p:DocumentPackage {package_id: $package_id})
OPTIONAL MATCH (p)-[:CONTAINS]->(prod:PackageProduct)
OPTIONAL MATCH (prod)-[:CONTAINS]->(d:PackageDocument)
RETURN p, prod, d
ORDER BY prod.processing_priority, d.document_name
```

## 🔄 Migration Strategy

### **Backwards Compatibility**
1. **Existing Packages**: Continue to work with 2-tier structure
2. **New Packages**: Use 3-tier structure by default
3. **Migration Path**: Optional upgrade from 2-tier to 3-tier
4. **Query Support**: Both structures supported in queries

### **Migration Process**
```cypher
// Migrate existing 2-tier package to 3-tier
MATCH (p:DocumentPackage {package_id: $package_id})
       -[:CONTAINS]->(d:PackageDocument)
WHERE NOT (p)-[:CONTAINS]->(:PackageProduct)-[:CONTAINS]->(d)

// Create default product
CREATE (prod:PackageProduct {
    product_id: $package_id + '_default',
    product_name: 'Default Product',
    product_type: 'core',
    tier_level: 1,
    processing_priority: 1,
    created_at: datetime(),
    updated_at: datetime()
})

// Update relationships
CREATE (p)-[:CONTAINS]->(prod)
CREATE (prod)-[:CONTAINS]->(d)
DELETE (p)-[:CONTAINS]->(d)
```

## 📊 Benefits Achieved

### **1. Proper Document Isolation**
- Documents are isolated by product (NAA, FHA, etc.)
- Prevents cross-product contamination
- Enables product-specific processing

### **2. Product-Level Relationships**
- Products can have dependencies
- Processing order based on priorities
- Product-to-product relationships

### **3. Enhanced Processing**
- Product context in LLM instructions
- Better document understanding
- Improved relationship extraction

### **4. Scalability**
- Easy to add new products
- Flexible hierarchy structure
- Supports complex packages

### **5. Query Flexibility**
- Query by package, product, or document level
- Efficient index usage
- Backwards compatibility

## 🧪 Testing Strategy

### **Test Cases**

#### 1. Package Creation Tests
```python
def test_create_3_tier_package():
    """Test creating package with products"""
    package_data = {
        'package_name': 'Test NQM Package',
        'category': 'NQM',
        'products': [
            {
                'product_name': 'Core Guidelines',
                'product_type': 'core',
                'documents': [
                    {'document_name': 'Guidelines.pdf', 'document_type': 'guidelines'}
                ]
            }
        ]
    }
    
    package = create_package(package_data)
    assert package.products[0].product_name == 'Core Guidelines'
    assert len(package.products[0].documents) == 1
```

#### 2. Query Tests
```python
def test_package_document_query():
    """Test 3-tier document retrieval"""
    documents = get_package_documents(package_id)
    
    # Should return documents with product context
    assert documents[0]['product_name'] is not None
    assert documents[0]['processing_priority'] is not None
```

#### 3. Backwards Compatibility Tests
```python
def test_2_tier_compatibility():
    """Test 2-tier package still works"""
    # Create old-style package
    old_package = create_2_tier_package()
    
    # Should still retrieve documents
    documents = get_package_documents(old_package.package_id)
    assert len(documents) > 0
```

## 📈 Monitoring and Metrics

### **Key Metrics**
1. **Package Creation Rate**: 3-tier vs 2-tier packages
2. **Processing Performance**: Time per product vs. time per document
3. **Query Performance**: 3-tier query response times
4. **Error Rates**: Package creation and processing errors
5. **User Adoption**: Usage of 3-tier features

### **Monitoring Queries**
```cypher
// Monitor package types
MATCH (p:DocumentPackage)
OPTIONAL MATCH (p)-[:CONTAINS]->(prod:PackageProduct)
RETURN p.category, 
       CASE WHEN prod IS NULL THEN '2-tier' ELSE '3-tier' END as hierarchy_type,
       count(*) as package_count

// Monitor processing performance
MATCH (p:DocumentPackage)-[:CONTAINS]->(prod:PackageProduct)
RETURN prod.product_type, 
       avg(prod.processing_priority) as avg_priority,
       count(*) as product_count
```

## 🎯 Future Enhancements

### **Phase 2 Enhancements**
1. **Product Templates**: Predefined product structures
2. **Dependency Validation**: Ensure dependency integrity
3. **Processing Optimization**: Parallel product processing
4. **Product Versioning**: Version control for products
5. **Product Relationships**: Enhanced product-to-product relationships

### **Advanced Features**
1. **Conditional Products**: Products based on conditions
2. **Dynamic Hierarchies**: Runtime hierarchy modification
3. **Product Marketplace**: Shared product definitions
4. **AI-Powered Organization**: Automatic product categorization
5. **Multi-Tenant Products**: Shared products across tenants

## 📚 Documentation References

### **Related Documents**
- [Implementation Updates](./IMPLEMENTATION_UPDATES.md)
- [Package Processing Status](./todo/Package%20Tasks/PACKAGE_PROCESSING_STATUS.md)
- [Technical Debt](./todo/Package%20Tasks/TECHNICAL_DEBT.md)
- [Wishlist and TODO](./todo/Package%20Tasks/WISHLIST_AND_TODO.md)

### **Code References**
- `backend/src/entities/document_package.py` - Entity definitions
- `backend/src/graphDB_dataAccess.py` - Database operations
- `backend/src/package_manager.py` - Package management
- `frontend/src/services/PackageAPI.ts` - API integration
- `frontend/src/components/PackageManagement/PackageWorkspace.tsx` - UI components

---

**Document Version**: 1.0  
**Last Updated**: 2025-07-15  
**Next Review**: After Phase 2 planning  
**Owner**: Development Team  
**Status**: Implementation Complete ✅