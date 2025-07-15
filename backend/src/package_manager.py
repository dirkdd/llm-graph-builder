# Task 2: Package Manager Core
# This file implements the core package management functionality

from typing import List, Optional, Dict, Any, Union
import uuid
import json
import logging
from datetime import datetime
from src.entities.document_package import (
    DocumentPackage,
    DocumentDefinition,
    PackageProduct,
    PackageRelationship,
    PackageStatus,
    PackageCategory,
    validate_package,
    create_package_id,
    is_valid_semantic_version
)
# Import will be enabled in Task 5 when database integration is implemented
# from src.graphDB_dataAccess import graphDBdataAccess
from src.shared.llm_graph_builder_exception import LLMGraphBuilderException


class PackageManager:
    """Manages document package lifecycle and operations"""
    
    def __init__(self, graph_db):
        """Initialize PackageManager with database connection"""
        self.graph_db = graph_db
        self.logger = logging.getLogger(__name__)
        
    def create_package(self, package_config: Dict[str, Any]) -> DocumentPackage:
        """Create a new document package
        
        Args:
            package_config: Dictionary containing package configuration
                - package_name (str): Human-readable package name
                - tenant_id (str): Organization identifier  
                - category (str): Mortgage category (NQM, RTL, SBC, CONV)
                - template (str, optional): Base template to use
                - created_by (str, optional): User who created the package
                - documents (List[Dict], optional): Document configurations
                - customizations (Dict, optional): Template customizations
                
        Returns:
            DocumentPackage: Created package instance
            
        Raises:
            ValueError: If configuration is invalid
            LLMGraphBuilderException: If database operation fails
        """
        try:
            self.logger.info(f"Creating package: {package_config.get('package_name', 'Unknown')}")
            
            # Validate required fields
            self._validate_package_config(package_config)
            
            # Generate unique package ID
            category = PackageCategory(package_config['category'])
            package_id = create_package_id(category, uuid.uuid4().hex[:8])
            
            # Initialize package structure
            package = DocumentPackage(
                package_id=package_id,
                package_name=package_config['package_name'],
                tenant_id=package_config['tenant_id'], 
                category=category,
                version="1.0.0",
                status=PackageStatus.DRAFT,
                created_by=package_config.get('created_by', 'system'),
                template_type=package_config.get('template', ''),
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
            
            # Add products from configuration (3-tier hierarchy)
            for prod_config in package_config.get('products', []):
                product = self._create_product_from_config(prod_config)
                package.add_product(product)
            
            # Add documents from configuration (backwards compatibility)
            for doc_config in package_config.get('documents', []):
                document = self._create_document_from_config(doc_config)
                package.add_document(document)
            
            # Add relationships from configuration  
            for rel_config in package_config.get('relationships', []):
                relationship = PackageRelationship(
                    from_document=rel_config['from_document'],
                    to_document=rel_config['to_document'],
                    relationship_type=rel_config['relationship_type'],
                    metadata=rel_config.get('metadata', {})
                )
                package.relationships.append(relationship)
            
            # Validate package before storing
            validation_errors = validate_package(package)
            if validation_errors:
                raise ValueError(f"Package validation failed: {validation_errors}")
            
            # Store in database
            self._store_package_in_db(package)
            
            self.logger.info(f"Successfully created package {package_id}")
            return package
            
        except Exception as e:
            self.logger.error(f"Failed to create package: {str(e)}")
            if isinstance(e, (ValueError, LLMGraphBuilderException)):
                raise
            raise LLMGraphBuilderException(f"Package creation failed: {str(e)}")
    
    def load_package(self, package_id: str) -> DocumentPackage:
        """Load existing package for use
        
        Args:
            package_id: Unique package identifier
            
        Returns:
            DocumentPackage: Loaded package instance
            
        Raises:
            ValueError: If package not found or validation fails
            LLMGraphBuilderException: If database operation fails
        """
        try:
            self.logger.info(f"Loading package: {package_id}")
            
            # Retrieve from database
            package_data = self._retrieve_package_from_db(package_id)
            
            if not package_data:
                raise ValueError(f"Package {package_id} not found")
            
            # Deserialize package
            package = self._deserialize_package(package_data)
            
            # Validate package integrity
            validation_errors = validate_package(package)
            if validation_errors:
                self.logger.warning(f"Package {package_id} has validation issues: {validation_errors}")
                # For loading, we allow packages with validation issues but log them
            
            # Load relationships
            package.relationships = self._load_package_relationships(package_id)
            
            self.logger.info(f"Successfully loaded package {package_id}")
            return package
            
        except Exception as e:
            self.logger.error(f"Failed to load package {package_id}: {str(e)}")
            if isinstance(e, (ValueError, LLMGraphBuilderException)):
                raise
            raise LLMGraphBuilderException(f"Package loading failed: {str(e)}")
    
    def update_package(self, package_id: str, updates: Dict[str, Any]) -> DocumentPackage:
        """Update package in place
        
        Args:
            package_id: Package identifier to update
            updates: Dictionary containing updates
                - documents (List[Dict], optional): Document updates
                - version_type (str, optional): MAJOR, MINOR, PATCH
                - package_name (str, optional): New package name
                - status (str, optional): New status
                - relationships (List[Dict], optional): Relationship updates
                
        Returns:
            DocumentPackage: Updated package instance
            
        Raises:
            ValueError: If updates are invalid or incompatible
            LLMGraphBuilderException: If database operation fails
        """
        try:
            self.logger.info(f"Updating package: {package_id}")
            
            # Load existing package
            package = self.load_package(package_id)
            
            # Validate update compatibility
            self._validate_update_compatibility(package, updates)
            
            # Apply package-level updates
            if 'package_name' in updates:
                package.package_name = updates['package_name']
            
            if 'status' in updates:
                package.status = PackageStatus(updates['status'])
            
            # Apply document updates
            if 'documents' in updates:
                package.documents = self._merge_document_updates(
                    package.documents, updates['documents']
                )
            
            # Apply relationship updates
            if 'relationships' in updates:
                package.relationships = self._merge_relationship_updates(
                    package.relationships, updates['relationships']
                )
            
            # Update version based on change type
            version_type = updates.get('version_type', 'PATCH')
            package.version = self._increment_version(package.version, version_type)
            package.updated_at = datetime.now()
            
            # Validate updated package
            validation_errors = validate_package(package)
            if validation_errors:
                raise ValueError(f"Updated package validation failed: {validation_errors}")
            
            # Store updated package
            self._store_package_in_db(package)
            
            self.logger.info(f"Successfully updated package {package_id} to version {package.version}")
            return package
            
        except Exception as e:
            self.logger.error(f"Failed to update package {package_id}: {str(e)}")
            if isinstance(e, (ValueError, LLMGraphBuilderException)):
                raise
            raise LLMGraphBuilderException(f"Package update failed: {str(e)}")
    
    def clone_package(self, package_id: str, new_name: str, modifications: Dict[str, Any] = None) -> DocumentPackage:
        """Create a copy of existing package
        
        Args:
            package_id: Source package identifier
            new_name: Name for the new package
            modifications: Optional modifications to apply
                - category (str, optional): Change category
                - created_by (str, optional): Creator of cloned package
                - customizations (Dict, optional): Additional customizations
                
        Returns:
            DocumentPackage: Cloned package instance
            
        Raises:
            ValueError: If source package not found or clone invalid
            LLMGraphBuilderException: If database operation fails
        """
        try:
            self.logger.info(f"Cloning package {package_id} as '{new_name}'")
            
            # Load source package
            source_package = self.load_package(package_id)
            
            # Determine category (use modification or keep original)
            target_category = source_package.category
            if modifications and 'category' in modifications:
                target_category = PackageCategory(modifications['category'])
            
            # Generate new package ID
            cloned_package_id = create_package_id(target_category, uuid.uuid4().hex[:8])
            
            # Deep copy structure with new IDs
            cloned_package = DocumentPackage(
                package_id=cloned_package_id,
                package_name=new_name,
                tenant_id=source_package.tenant_id,
                category=target_category,
                version="1.0.0",  # Reset version for clone
                status=PackageStatus.DRAFT,  # New clones start as draft
                created_by=modifications.get('created_by', 'system') if modifications else 'system',
                template_type=source_package.template_type,
                created_at=datetime.now(),
                updated_at=datetime.now(),
                template_mappings=source_package.template_mappings.copy(),
                validation_rules=source_package.validation_rules.copy()
            )
            
            # Clone products with new IDs
            for source_product in source_package.products:
                cloned_product = self._clone_product(source_product)
                cloned_package.add_product(cloned_product)
            
            # Clone documents with new IDs (backwards compatibility)
            for source_doc in source_package.documents:
                cloned_doc = self._clone_document(source_doc)
                cloned_package.add_document(cloned_doc)
            
            # Clone relationships with updated document IDs
            document_id_mapping = {
                source_package.documents[i].document_id: cloned_package.documents[i].document_id
                for i in range(len(source_package.documents))
            }
            
            for source_rel in source_package.relationships:
                cloned_rel = PackageRelationship(
                    from_document=document_id_mapping.get(source_rel.from_document, source_rel.from_document),
                    to_document=document_id_mapping.get(source_rel.to_document, source_rel.to_document),
                    relationship_type=source_rel.relationship_type,
                    metadata=source_rel.metadata.copy()
                )
                cloned_package.relationships.append(cloned_rel)
            
            # Apply additional modifications if provided
            if modifications:
                self._apply_modifications(cloned_package, modifications)
            
            # Validate cloned package
            validation_errors = validate_package(cloned_package)
            if validation_errors:
                raise ValueError(f"Cloned package validation failed: {validation_errors}")
            
            # Store cloned package
            self._store_package_in_db(cloned_package)
            
            self.logger.info(f"Successfully cloned package {package_id} to {cloned_package_id}")
            return cloned_package
            
        except Exception as e:
            self.logger.error(f"Failed to clone package {package_id}: {str(e)}")
            if isinstance(e, (ValueError, LLMGraphBuilderException)):
                raise
            raise LLMGraphBuilderException(f"Package cloning failed: {str(e)}")
    
    def delete_package(self, package_id: str) -> bool:
        """Delete a package
        
        Args:
            package_id: Package identifier to delete
            
        Returns:
            bool: True if deleted successfully
            
        Raises:
            ValueError: If package not found or cannot be deleted
            LLMGraphBuilderException: If database operation fails
        """
        try:
            self.logger.info(f"Deleting package: {package_id}")
            
            # Check if package exists
            package = self.load_package(package_id)
            
            # Check if package can be deleted (business rules)
            if package.status == PackageStatus.ACTIVE:
                raise ValueError("Cannot delete active packages. Archive first.")
            
            # Delete from database
            success = self._delete_package_from_db(package_id)
            
            if success:
                self.logger.info(f"Successfully deleted package {package_id}")
            else:
                raise LLMGraphBuilderException(f"Failed to delete package {package_id}")
                
            return success
            
        except Exception as e:
            self.logger.error(f"Failed to delete package {package_id}: {str(e)}")
            if isinstance(e, (ValueError, LLMGraphBuilderException)):
                raise
            raise LLMGraphBuilderException(f"Package deletion failed: {str(e)}")
    
    def list_packages(self, tenant_id: str = None, category: PackageCategory = None, 
                     status: PackageStatus = None) -> List[Dict[str, Any]]:
        """List packages with optional filtering
        
        Args:
            tenant_id: Filter by tenant
            category: Filter by category  
            status: Filter by status
            
        Returns:
            List[Dict]: List of package metadata
        """
        try:
            self.logger.info("Listing packages with filters")
            
            packages = self._list_packages_from_db(tenant_id, category, status)
            
            self.logger.info(f"Found {len(packages)} packages")
            return packages
            
        except Exception as e:
            self.logger.error(f"Failed to list packages: {str(e)}")
            raise LLMGraphBuilderException(f"Package listing failed: {str(e)}")
    
    # Private helper methods
    
    def _validate_package_config(self, config: Dict[str, Any]) -> None:
        """Validate package configuration"""
        required_fields = ['package_name', 'tenant_id', 'category']
        
        for field in required_fields:
            if field not in config or not config[field]:
                raise ValueError(f"Required field '{field}' is missing or empty")
        
        # Validate category
        try:
            PackageCategory(config['category'])
        except ValueError:
            valid_categories = [c.value for c in PackageCategory]
            raise ValueError(f"Invalid category. Must be one of: {valid_categories}")
    
    def _create_product_from_config(self, prod_config: Dict[str, Any]) -> PackageProduct:
        """Create PackageProduct from configuration"""
        product = PackageProduct(
            product_id=prod_config.get('product_id', f"prod_{uuid.uuid4().hex[:8]}"),
            product_name=prod_config['product_name'],
            product_type=prod_config.get('product_type', 'core'),
            tier_level=prod_config.get('tier_level', 1),
            processing_priority=prod_config.get('processing_priority', 1),
            dependencies=prod_config.get('dependencies', []),
            created_at=datetime.now(),
            updated_at=datetime.now(),
            metadata=prod_config.get('metadata', {})
        )
        
        # Store documents associated with this product for later database storage
        product.metadata['documents'] = prod_config.get('documents', [])
        
        return product

    def _create_document_from_config(self, doc_config: Dict[str, Any]) -> DocumentDefinition:
        """Create DocumentDefinition from configuration"""
        return DocumentDefinition(
            document_id=doc_config.get('document_id', f"doc_{uuid.uuid4().hex[:8]}"),
            document_type=doc_config['document_type'],
            document_name=doc_config['document_name'],
            expected_structure=doc_config.get('expected_structure', {}),
            required_sections=doc_config.get('required_sections', []),
            optional_sections=doc_config.get('optional_sections', []),
            chunking_strategy=doc_config.get('chunking_strategy', 'hierarchical'),
            entity_types=doc_config.get('entity_types', []),
            matrix_configuration=doc_config.get('matrix_configuration'),
            validation_schema=doc_config.get('validation_schema', {}),
            quality_thresholds=doc_config.get('quality_thresholds', {})
        )
    
    def _validate_update_compatibility(self, package: DocumentPackage, updates: Dict[str, Any]) -> None:
        """Validate that updates are compatible with existing package"""
        # Cannot change category for existing packages
        if 'category' in updates and updates['category'] != package.category.value:
            raise ValueError("Cannot change package category in update")
        
        # Cannot change tenant_id
        if 'tenant_id' in updates and updates['tenant_id'] != package.tenant_id:
            raise ValueError("Cannot change tenant_id in update")
    
    def _increment_version(self, current_version: str, version_type: str) -> str:
        """Increment version based on type"""
        major, minor, patch = map(int, current_version.split('.'))
        
        if version_type == 'MAJOR':
            return f"{major + 1}.0.0"
        elif version_type == 'MINOR':
            return f"{major}.{minor + 1}.0"
        else:  # PATCH
            return f"{major}.{minor}.{patch + 1}"
    
    def _merge_document_updates(self, existing_docs: List[DocumentDefinition], 
                              updates: List[Dict[str, Any]]) -> List[DocumentDefinition]:
        """Merge document updates with existing documents"""
        # For now, replace all documents (could be enhanced for partial updates)
        updated_docs = []
        for doc_config in updates:
            doc = self._create_document_from_config(doc_config)
            updated_docs.append(doc)
        return updated_docs
    
    def _merge_relationship_updates(self, existing_rels: List[PackageRelationship],
                                  updates: List[Dict[str, Any]]) -> List[PackageRelationship]:
        """Merge relationship updates with existing relationships"""
        updated_rels = []
        for rel_config in updates:
            rel = PackageRelationship(
                from_document=rel_config['from_document'],
                to_document=rel_config['to_document'],
                relationship_type=rel_config['relationship_type'],
                metadata=rel_config.get('metadata', {})
            )
            updated_rels.append(rel)
        return updated_rels
    
    def _clone_product(self, source_product: PackageProduct) -> PackageProduct:
        """Create a clone of a product with new ID"""
        return PackageProduct(
            product_id=f"prod_{uuid.uuid4().hex[:8]}",
            product_name=source_product.product_name,
            product_type=source_product.product_type,
            tier_level=source_product.tier_level,
            processing_priority=source_product.processing_priority,
            dependencies=source_product.dependencies.copy(),
            created_at=datetime.now(),
            updated_at=datetime.now(),
            metadata=source_product.metadata.copy()
        )

    def _clone_document(self, source_doc: DocumentDefinition) -> DocumentDefinition:
        """Create a clone of a document with new ID"""
        return DocumentDefinition(
            document_id=f"doc_{uuid.uuid4().hex[:8]}",
            document_type=source_doc.document_type,
            document_name=source_doc.document_name,
            expected_structure=source_doc.expected_structure.copy(),
            required_sections=source_doc.required_sections.copy(),
            optional_sections=source_doc.optional_sections.copy(),
            chunking_strategy=source_doc.chunking_strategy,
            entity_types=source_doc.entity_types.copy(),
            matrix_configuration=source_doc.matrix_configuration.copy() if source_doc.matrix_configuration else None,
            validation_schema=source_doc.validation_schema.copy(),
            quality_thresholds=source_doc.quality_thresholds.copy()
        )
    
    def _apply_modifications(self, package: DocumentPackage, modifications: Dict[str, Any]) -> None:
        """Apply modifications to a package"""
        if 'customizations' in modifications:
            # Apply customizations based on the specific needs
            customizations = modifications['customizations']
            
            # Example: Add additional sections to guidelines documents
            if 'additional_sections' in customizations:
                for doc in package.get_documents_by_type('guidelines'):
                    doc.optional_sections.extend(customizations['additional_sections'])
    
    # Database interaction methods (Task 5 implementation)
    
    def _store_package_in_db(self, package: DocumentPackage) -> None:
        """Store package in Neo4j database and create structural nodes immediately"""
        try:
            # Import here to avoid circular imports
            from src.entities.document_package import DEFAULT_CATEGORY_METADATA
            
            # Convert package to database format
            package_data = {
                "package_id": package.package_id,
                "package_name": package.package_name,
                "tenant_id": package.tenant_id,
                "category": package.category.value,
                "version": package.version,
                "status": package.status.value,
                "created_by": package.created_by,
                "template_type": package.template_type,
                "created_at": package.created_at,
                "updated_at": package.updated_at,
                "template_mappings": package.template_mappings,
                "validation_rules": package.validation_rules
            }
            
            # Create or update package node
            if self.graph_db.package_exists(package.package_id):
                self.graph_db.update_package_node(package.package_id, package_data)
            else:
                self.graph_db.create_package_node(package_data)
            
            # Create Category node immediately with rich metadata
            category_metadata = DEFAULT_CATEGORY_METADATA.get(package.category)
            if category_metadata:
                category_data = {
                    "category_code": category_metadata.category.value,
                    "display_name": category_metadata.display_name,
                    "description": category_metadata.description,
                    "key_characteristics": category_metadata.key_characteristics,
                    "regulatory_framework": category_metadata.regulatory_framework,
                    "typical_products": category_metadata.typical_products,
                    "risk_profile": category_metadata.risk_profile
                }
                
                success = self.graph_db.create_category_node(category_data)
                if success:
                    self.logger.info(f"Created category node: {category_metadata.display_name}")
                else:
                    self.logger.warning(f"Failed to create category node: {category_metadata.display_name}")
            
            # Store products (3-tier hierarchy)
            for product in package.products:
                # Create PackageProduct node (existing functionality)
                package_product_data = {
                    "product_id": product.product_id,
                    "product_name": product.product_name,
                    "product_type": product.product_type,
                    "tier_level": product.tier_level,
                    "processing_priority": product.processing_priority,
                    "dependencies": product.dependencies,
                    "created_at": product.created_at,
                    "updated_at": product.updated_at,
                    "metadata": product.metadata
                }
                self.graph_db.create_package_product(package.package_id, package_product_data)
                
                # Create Product node immediately with rich metadata  
                product_node_data = {
                    "product_id": product.product_id,
                    "product_name": product.product_name,
                    "product_type": product.product_type,
                    "description": product.description,
                    "key_features": product.key_features,
                    "underwriting_highlights": product.underwriting_highlights,
                    "target_borrowers": product.target_borrowers,
                    "tier_level": product.tier_level,
                    "processing_priority": product.processing_priority
                }
                
                success = self.graph_db.create_product_node(product_node_data, package.category.value)
                if success:
                    self.logger.info(f"Created product node: {product.product_name}")
                else:
                    self.logger.warning(f"Failed to create product node: {product.product_name}")
                
                # Create Programs within this Product (if any)
                programs = product.metadata.get('programs', [])
                for prog_config in programs:
                    program_node_data = {
                        "program_id": prog_config.get('program_id', f"prog_{uuid.uuid4().hex[:8]}"),
                        "program_name": prog_config.get('program_name', 'Default Program'),
                        "program_code": prog_config.get('program_code', 'STD'),
                        "description": prog_config.get('description', ''),
                        "program_type": prog_config.get('program_type', 'standard'),
                        "loan_limits": prog_config.get('loan_limits', {}),
                        "rate_adjustments": prog_config.get('rate_adjustments', []),
                        "feature_differences": prog_config.get('feature_differences', []),
                        "qualification_criteria": prog_config.get('qualification_criteria', []),
                        "processing_priority": prog_config.get('processing_priority', 1)
                    }
                    
                    prog_success = self.graph_db.create_program_node(program_node_data, product.product_id)
                    if prog_success:
                        self.logger.info(f"Created program node: {prog_config.get('program_name', 'Unknown')}")
                    else:
                        self.logger.warning(f"Failed to create program node: {prog_config.get('program_name', 'Unknown')}")
                
                # Store documents associated with this product or its programs
                product_documents = product.metadata.get('documents', [])
                for doc_config in product_documents:
                    doc_data = {
                        "document_id": doc_config.get('document_id', f"doc_{uuid.uuid4().hex[:8]}"),
                        "document_type": doc_config.get('document_type', 'guidelines'),
                        "document_name": doc_config.get('document_name', 'Unknown Document'),
                        "associated_to": doc_config.get('associated_to', 'product'),  # "product" or "program"
                        "parent_id": doc_config.get('parent_id', product.product_id),  # product_id or program_id
                        "expected_structure": doc_config.get('expected_structure', {}),
                        "required_sections": doc_config.get('required_sections', []),
                        "optional_sections": doc_config.get('optional_sections', []),
                        "chunking_strategy": doc_config.get('chunking_strategy', 'hierarchical'),
                        "entity_types": doc_config.get('entity_types', []),
                        "matrix_configuration": doc_config.get('matrix_configuration'),
                        "validation_schema": doc_config.get('validation_schema', {}),
                        "quality_thresholds": doc_config.get('quality_thresholds', {})
                    }
                    
                    # Determine association level and create document accordingly
                    if doc_data['associated_to'] == 'program':
                        # Document belongs to a specific program
                        program_id = doc_data['parent_id']
                        self.graph_db.create_package_document(package.package_id, doc_data, None)  # No product_id for program docs
                        self.logger.info(f"Created program-level document: {doc_data['document_name']} -> Program {program_id}")
                    else:
                        # Document belongs to product (default behavior)
                        self.graph_db.create_package_document(package.package_id, doc_data, product.product_id)
                        self.logger.info(f"Created product-level document: {doc_data['document_name']} -> Product {product.product_id}")
                
                # Store program-specific documents from program configs
                for prog_config in programs:
                    program_documents = prog_config.get('documents', [])
                    for doc_config in program_documents:
                        doc_data = {
                            "document_id": doc_config.get('document_id', f"doc_{uuid.uuid4().hex[:8]}"),
                            "document_type": doc_config.get('document_type', 'matrix'),
                            "document_name": doc_config.get('document_name', 'Unknown Document'),
                            "associated_to": "program",
                            "parent_id": prog_config.get('program_id'),
                            "expected_structure": doc_config.get('expected_structure', {}),
                            "required_sections": doc_config.get('required_sections', []),
                            "optional_sections": doc_config.get('optional_sections', []),
                            "chunking_strategy": doc_config.get('chunking_strategy', 'hierarchical'),
                            "entity_types": doc_config.get('entity_types', []),
                            "matrix_configuration": doc_config.get('matrix_configuration'),
                            "validation_schema": doc_config.get('validation_schema', {}),
                            "quality_thresholds": doc_config.get('quality_thresholds', {})
                        }
                        
                        # Create program-specific document
                        self.graph_db.create_package_document(package.package_id, doc_data, None)
                        self.logger.info(f"Created program-specific document: {doc_data['document_name']} -> Program {prog_config.get('program_id')}")
            
            # Store documents (backwards compatibility)
            for doc in package.documents:
                doc_data = {
                    "document_id": doc.document_id,
                    "document_type": doc.document_type,
                    "document_name": doc.document_name,
                    "expected_structure": doc.expected_structure,
                    "required_sections": doc.required_sections,
                    "optional_sections": doc.optional_sections,
                    "chunking_strategy": doc.chunking_strategy,
                    "entity_types": doc.entity_types,
                    "matrix_configuration": doc.matrix_configuration,
                    "validation_schema": doc.validation_schema,
                    "quality_thresholds": doc.quality_thresholds
                }
                self.graph_db.create_package_document(package.package_id, doc_data)
            
            # Store relationships
            for rel in package.relationships:
                rel_data = {
                    "from_document": rel.from_document,
                    "to_document": rel.to_document,
                    "relationship_type": rel.relationship_type,
                    "metadata": rel.metadata
                }
                self.graph_db.create_package_relationship(package.package_id, rel_data)
            
        except Exception as e:
            self.logger.error(f"Failed to store package in database: {str(e)}")
            raise
    
    def _retrieve_package_from_db(self, package_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve package data from database"""
        try:
            return self.graph_db.get_package_node(package_id)
        except Exception as e:
            self.logger.error(f"Failed to retrieve package from database: {str(e)}")
            return None
    
    def _deserialize_package(self, package_data: Dict[str, Any]) -> DocumentPackage:
        """Deserialize package data into DocumentPackage object"""
        try:
            from src.entities.document_package import PackageCategory, PackageStatus
            from datetime import datetime
            
            # Create package object
            package = DocumentPackage(
                package_id=package_data["package_id"],
                package_name=package_data["package_name"],
                tenant_id=package_data["tenant_id"],
                category=PackageCategory(package_data["category"]),
                version=package_data["version"],
                status=PackageStatus(package_data["status"]),
                created_by=package_data.get("created_by", "system"),
                template_type=package_data.get("template_type", ""),
                created_at=datetime.fromisoformat(package_data["created_at"]) if package_data.get("created_at") else datetime.now(),
                updated_at=datetime.fromisoformat(package_data["updated_at"]) if package_data.get("updated_at") else datetime.now(),
                template_mappings=package_data.get("template_mappings", {}),
                validation_rules=package_data.get("validation_rules", {})
            )
            
            # Load products (3-tier hierarchy)
            products = self.graph_db.get_package_products(package_data["package_id"])
            for prod_data in products:
                product = PackageProduct(
                    product_id=prod_data["product_id"],
                    product_name=prod_data["product_name"],
                    product_type=prod_data["product_type"],
                    tier_level=prod_data.get("tier_level", 1),
                    processing_priority=prod_data.get("processing_priority", 1),
                    dependencies=prod_data.get("dependencies", []),
                    created_at=datetime.fromisoformat(prod_data["created_at"]) if prod_data.get("created_at") else datetime.now(),
                    updated_at=datetime.fromisoformat(prod_data["updated_at"]) if prod_data.get("updated_at") else datetime.now(),
                    metadata=prod_data.get("metadata", {})
                )
                package.add_product(product)
            
            # Load documents
            documents = self.graph_db.get_package_documents(package_data["package_id"])
            for doc_data in documents:
                doc = DocumentDefinition(
                    document_id=doc_data["document_id"],
                    document_type=doc_data["document_type"],
                    document_name=doc_data["document_name"],
                    expected_structure=doc_data.get("expected_structure", {}),
                    required_sections=doc_data.get("required_sections", []),
                    optional_sections=doc_data.get("optional_sections", []),
                    chunking_strategy=doc_data.get("chunking_strategy", "hierarchical"),
                    entity_types=doc_data.get("entity_types", []),
                    matrix_configuration=doc_data.get("matrix_configuration"),
                    validation_schema=doc_data.get("validation_schema", {}),
                    quality_thresholds=doc_data.get("quality_thresholds", {})
                )
                package.add_document(doc)
            
            return package
            
        except Exception as e:
            self.logger.error(f"Failed to deserialize package: {str(e)}")
            raise
    
    def _load_package_relationships(self, package_id: str) -> List[PackageRelationship]:
        """Load package relationships from database"""
        try:
            relationships = []
            rel_data_list = self.graph_db.get_package_relationships(package_id)
            
            for rel_data in rel_data_list:
                rel = PackageRelationship(
                    from_document=rel_data["from_document"],
                    to_document=rel_data["to_document"],
                    relationship_type=rel_data["relationship_type"],
                    metadata=rel_data.get("metadata", {})
                )
                relationships.append(rel)
            
            return relationships
            
        except Exception as e:
            self.logger.error(f"Failed to load package relationships: {str(e)}")
            return []
    
    def _delete_package_from_db(self, package_id: str) -> bool:
        """Delete package from database"""
        try:
            return self.graph_db.delete_package_node(package_id)
        except Exception as e:
            self.logger.error(f"Failed to delete package from database: {str(e)}")
            return False
    
    def _list_packages_from_db(self, tenant_id: str = None, category: PackageCategory = None,
                             status: PackageStatus = None) -> List[Dict[str, Any]]:
        """List packages from database with filters"""
        try:
            category_str = category.value if category else None
            status_str = status.value if status else None
            return self.graph_db.list_packages(tenant_id, category_str, status_str)
        except Exception as e:
            self.logger.error(f"Failed to list packages from database: {str(e)}")
            return []