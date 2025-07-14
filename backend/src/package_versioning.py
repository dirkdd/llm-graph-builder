# Task 4: Package Versioning Implementation
# This file implements semantic versioning for document packages

from typing import List, Dict, Any, Optional, Union
from dataclasses import dataclass, asdict
from datetime import datetime
from enum import Enum
import json
import logging
import copy
from src.entities.document_package import DocumentPackage, DocumentDefinition, PackageRelationship


class ChangeType(Enum):
    """Types of version changes"""
    MAJOR = "MAJOR"  # Breaking changes to structure, incompatible changes
    MINOR = "MINOR"  # New features, backward compatible additions
    PATCH = "PATCH"  # Bug fixes, minor updates, documentation changes


@dataclass
class VersionRecord:
    """Record of a package version"""
    version: str
    change_type: ChangeType
    changes: List[str]
    created_at: datetime
    created_by: str
    metadata: Dict[str, Any]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        result = asdict(self)
        result['change_type'] = self.change_type.value
        result['created_at'] = self.created_at.isoformat()
        return result
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'VersionRecord':
        """Create from dictionary"""
        data = data.copy()
        data['change_type'] = ChangeType(data['change_type'])
        data['created_at'] = datetime.fromisoformat(data['created_at'])
        return cls(**data)


@dataclass
class VersionDiff:
    """Difference between two package versions"""
    from_version: str
    to_version: str
    added_documents: List[str]
    removed_documents: List[str]
    modified_documents: List[Dict[str, Any]]
    structural_changes: List[str]
    relationship_changes: List[str]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return asdict(self)
    
    def has_changes(self) -> bool:
        """Check if there are any changes between versions"""
        return (bool(self.added_documents) or 
                bool(self.removed_documents) or 
                bool(self.modified_documents) or 
                bool(self.structural_changes) or
                bool(self.relationship_changes))


class PackageVersionManager:
    """Manages package versioning and history"""
    
    def __init__(self, graph_db=None):
        """Initialize version manager with database connection"""
        self.graph_db = graph_db
        self.logger = logging.getLogger(__name__)
        
    def create_version(self, package: DocumentPackage, change_type: ChangeType, 
                      changes: List[str] = None, created_by: str = None) -> str:
        """Create new version based on change type
        
        Args:
            package: Package to version
            change_type: Type of changes (MAJOR, MINOR, PATCH)
            changes: List of changes made
            created_by: User who created the version
            
        Returns:
            New version string
            
        Raises:
            ValueError: If current version invalid or change type invalid
            Exception: If version creation fails
        """
        try:
            self.logger.info(f"Creating {change_type.value} version for package {package.package_id}")
            
            current_version = package.version
            if not self._is_valid_version(current_version):
                raise ValueError(f"Invalid current version: {current_version}")
            
            # Calculate new version
            new_version = self._calculate_new_version(current_version, change_type)
            
            # Create package snapshot for current state
            package_snapshot = self._create_package_snapshot(package)
            
            # Create version record
            version_record = VersionRecord(
                version=new_version,
                change_type=change_type,
                changes=changes or [],
                created_at=datetime.now(),
                created_by=created_by or package.created_by or 'system',
                metadata={
                    "previous_version": current_version,
                    "package_id": package.package_id,
                    "package_name": package.package_name,
                    "category": package.category.value,
                    "change_summary": self._generate_change_summary(change_type, changes)
                }
            )
            
            # Store version record and snapshot
            self._store_version_record(package.package_id, version_record)
            self._store_package_snapshot(package.package_id, new_version, package_snapshot)
            
            # Update package version
            previous_version = package.version
            package.version = new_version
            package.updated_at = datetime.now()
            
            self.logger.info(f"Created version {new_version} for package {package.package_id} (was {previous_version})")
            return new_version
            
        except Exception as e:
            self.logger.error(f"Failed to create version for package {package.package_id}: {str(e)}")
            raise
    
    def get_version_history(self, package_id: str) -> List[VersionRecord]:
        """Retrieve complete version history
        
        Args:
            package_id: Package identifier
            
        Returns:
            List of version records in chronological order (newest first)
            
        Raises:
            Exception: If retrieval fails
        """
        try:
            self.logger.info(f"Retrieving version history for package {package_id}")
            
            history_data = self._retrieve_version_history(package_id)
            history = [self._deserialize_version_record(record) for record in history_data]
            
            # Sort by version number (newest first)
            history.sort(key=lambda x: self._version_to_tuple(x.version), reverse=True)
            
            self.logger.info(f"Found {len(history)} versions for package {package_id}")
            return history
            
        except Exception as e:
            self.logger.error(f"Failed to get version history for {package_id}: {str(e)}")
            raise
    
    def get_version_by_number(self, package_id: str, version: str) -> Optional[VersionRecord]:
        """Get specific version record
        
        Args:
            package_id: Package identifier
            version: Version number to retrieve
            
        Returns:
            Version record if found, None otherwise
        """
        try:
            history = self.get_version_history(package_id)
            return next((record for record in history if record.version == version), None)
        except Exception as e:
            self.logger.error(f"Failed to get version {version} for {package_id}: {str(e)}")
            return None
    
    def rollback_version(self, package_id: str, target_version: str, 
                        created_by: str = None) -> DocumentPackage:
        """Rollback to previous version
        
        Args:
            package_id: Package identifier
            target_version: Version to rollback to
            created_by: User performing rollback
            
        Returns:
            Package restored to target version state
            
        Raises:
            ValueError: If target version not found or invalid
            Exception: If rollback fails
        """
        try:
            self.logger.info(f"Rolling back package {package_id} to version {target_version}")
            
            # Validate target version exists
            target_record = self.get_version_by_number(package_id, target_version)
            if not target_record:
                raise ValueError(f"Version {target_version} not found for package {package_id}")
            
            # Retrieve package snapshot at target version
            package_snapshot = self._retrieve_package_snapshot(package_id, target_version)
            if not package_snapshot:
                raise ValueError(f"No snapshot found for version {target_version}")
            
            # Load current package to get current version
            current_package = self._load_current_package(package_id)
            if not current_package:
                raise ValueError(f"Current package {package_id} not found")
            
            # Create new version for rollback (MAJOR change since it's potentially breaking)
            rollback_changes = [f"Rollback to version {target_version}"]
            rollback_version = self._calculate_new_version(current_package.version, ChangeType.MAJOR)
            
            # Restore package from snapshot
            restored_package = self._restore_package_from_snapshot(package_snapshot)
            restored_package.version = rollback_version
            restored_package.updated_at = datetime.now()
            
            # Create version record for rollback
            rollback_record = VersionRecord(
                version=rollback_version,
                change_type=ChangeType.MAJOR,
                changes=rollback_changes,
                created_at=datetime.now(),
                created_by=created_by or 'system',
                metadata={
                    "previous_version": current_package.version,
                    "package_id": package_id,
                    "rollback_target": target_version,
                    "operation": "rollback"
                }
            )
            
            # Store rollback version
            self._store_version_record(package_id, rollback_record)
            self._store_package_snapshot(package_id, rollback_version, self._create_package_snapshot(restored_package))
            
            self.logger.info(f"Successfully rolled back package {package_id} to version {target_version} (new version: {rollback_version})")
            return restored_package
            
        except Exception as e:
            self.logger.error(f"Failed to rollback package {package_id} to {target_version}: {str(e)}")
            raise
    
    def diff_versions(self, package_id: str, v1: str, v2: str) -> VersionDiff:
        """Compare two versions of a package
        
        Args:
            package_id: Package identifier
            v1: First version (from)
            v2: Second version (to)
            
        Returns:
            VersionDiff object showing differences
            
        Raises:
            ValueError: If versions not found
            Exception: If comparison fails
        """
        try:
            self.logger.info(f"Comparing versions {v1} and {v2} for package {package_id}")
            
            # Get package snapshots for both versions
            snapshot1 = self._retrieve_package_snapshot(package_id, v1)
            snapshot2 = self._retrieve_package_snapshot(package_id, v2)
            
            if not snapshot1:
                raise ValueError(f"Version {v1} not found for package {package_id}")
            if not snapshot2:
                raise ValueError(f"Version {v2} not found for package {package_id}")
            
            # Compare documents
            docs1 = {doc['document_id']: doc for doc in snapshot1.get('documents', [])}
            docs2 = {doc['document_id']: doc for doc in snapshot2.get('documents', [])}
            
            added_documents = list(set(docs2.keys()) - set(docs1.keys()))
            removed_documents = list(set(docs1.keys()) - set(docs2.keys()))
            
            # Find modified documents with details
            modified_documents = []
            for doc_id in set(docs1.keys()) & set(docs2.keys()):
                doc_diff = self._compare_documents(docs1[doc_id], docs2[doc_id])
                if doc_diff:
                    modified_documents.append({
                        'document_id': doc_id,
                        'document_name': docs2[doc_id].get('document_name', doc_id),
                        'changes': doc_diff
                    })
            
            # Compare relationships
            rels1 = {self._relationship_key(rel): rel for rel in snapshot1.get('relationships', [])}
            rels2 = {self._relationship_key(rel): rel for rel in snapshot2.get('relationships', [])}
            
            relationship_changes = []
            added_rels = set(rels2.keys()) - set(rels1.keys())
            removed_rels = set(rels1.keys()) - set(rels2.keys())
            
            if added_rels:
                relationship_changes.extend([f"Added relationship: {rel}" for rel in added_rels])
            if removed_rels:
                relationship_changes.extend([f"Removed relationship: {rel}" for rel in removed_rels])
            
            # Detect structural changes
            structural_changes = self._detect_structural_changes(snapshot1, snapshot2)
            
            diff = VersionDiff(
                from_version=v1,
                to_version=v2,
                added_documents=added_documents,
                removed_documents=removed_documents,
                modified_documents=modified_documents,
                structural_changes=structural_changes,
                relationship_changes=relationship_changes
            )
            
            self.logger.info(f"Version diff complete: {len(added_documents)} added, {len(removed_documents)} removed, {len(modified_documents)} modified")
            return diff
            
        except Exception as e:
            self.logger.error(f"Failed to diff versions {v1} and {v2} for package {package_id}: {str(e)}")
            raise
    
    def validate_version_sequence(self, package_id: str) -> List[str]:
        """Validate version sequence for conflicts or gaps
        
        Args:
            package_id: Package identifier
            
        Returns:
            List of validation issues (empty if valid)
        """
        try:
            issues = []
            history = self.get_version_history(package_id)
            
            if not history:
                return ["No version history found"]
            
            # Sort by version number for validation
            history.sort(key=lambda x: self._version_to_tuple(x.version))
            
            # Check for gaps or inconsistencies
            for i in range(1, len(history)):
                current_version = self._version_to_tuple(history[i].version)
                previous_version = self._version_to_tuple(history[i-1].version)
                
                # Check if version increment is valid
                if not self._is_valid_version_increment(previous_version, current_version):
                    issues.append(f"Invalid version increment from {history[i-1].version} to {history[i].version}")
            
            return issues
            
        except Exception as e:
            self.logger.error(f"Failed to validate version sequence for {package_id}: {str(e)}")
            return [f"Validation failed: {str(e)}"]
    
    # Private helper methods
    
    def _calculate_new_version(self, current: str, change_type: ChangeType) -> str:
        """Calculate new version based on change type"""
        major, minor, patch = map(int, current.split('.'))
        
        if change_type == ChangeType.MAJOR:
            return f"{major + 1}.0.0"
        elif change_type == ChangeType.MINOR:
            return f"{major}.{minor + 1}.0"
        else:  # PATCH
            return f"{major}.{minor}.{patch + 1}"
    
    def _is_valid_version(self, version: str) -> bool:
        """Validate version format (semantic versioning)"""
        try:
            parts = version.split('.')
            if len(parts) != 3:
                return False
            
            major, minor, patch = map(int, parts)
            return major >= 0 and minor >= 0 and patch >= 0
            
        except (ValueError, TypeError):
            return False
    
    def _version_to_tuple(self, version: str) -> tuple:
        """Convert version string to tuple for comparison"""
        return tuple(map(int, version.split('.')))
    
    def _is_valid_version_increment(self, prev_version: tuple, current_version: tuple) -> bool:
        """Check if version increment is valid"""
        prev_major, prev_minor, prev_patch = prev_version
        curr_major, curr_minor, curr_patch = current_version
        
        # MAJOR increment: X.0.0
        if curr_major > prev_major:
            return curr_minor == 0 and curr_patch == 0
        
        # MINOR increment: X.Y.0  
        if curr_major == prev_major and curr_minor > prev_minor:
            return curr_patch == 0
        
        # PATCH increment: X.Y.Z
        if curr_major == prev_major and curr_minor == prev_minor:
            return curr_patch > prev_patch
        
        return False
    
    def _generate_change_summary(self, change_type: ChangeType, changes: List[str]) -> str:
        """Generate human-readable change summary"""
        if not changes:
            return f"{change_type.value} version update"
        
        return f"{change_type.value}: {'; '.join(changes[:3])}" + ("..." if len(changes) > 3 else "")
    
    def _create_package_snapshot(self, package: DocumentPackage) -> Dict[str, Any]:
        """Create snapshot of package state"""
        return {
            "package_id": package.package_id,
            "package_name": package.package_name,
            "tenant_id": package.tenant_id,
            "category": package.category.value,
            "status": package.status.value,
            "created_by": package.created_by,
            "template_type": package.template_type,
            "documents": [self._serialize_document(doc) for doc in package.documents],
            "relationships": [self._serialize_relationship(rel) for rel in package.relationships],
            "template_mappings": package.template_mappings,
            "validation_rules": package.validation_rules,
            "snapshot_created": datetime.now().isoformat()
        }
    
    def _serialize_document(self, doc: DocumentDefinition) -> Dict[str, Any]:
        """Serialize document to dictionary"""
        return {
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
    
    def _serialize_relationship(self, rel: PackageRelationship) -> Dict[str, Any]:
        """Serialize relationship to dictionary"""
        return {
            "from_document": rel.from_document,
            "to_document": rel.to_document,
            "relationship_type": rel.relationship_type,
            "metadata": rel.metadata
        }
    
    def _restore_package_from_snapshot(self, snapshot: Dict[str, Any]) -> DocumentPackage:
        """Restore package from snapshot"""
        from src.entities.document_package import PackageCategory, PackageStatus
        
        # Restore documents
        documents = []
        for doc_data in snapshot.get('documents', []):
            doc = DocumentDefinition(
                document_id=doc_data['document_id'],
                document_type=doc_data['document_type'],
                document_name=doc_data['document_name'],
                expected_structure=doc_data.get('expected_structure', {}),
                required_sections=doc_data.get('required_sections', []),
                optional_sections=doc_data.get('optional_sections', []),
                chunking_strategy=doc_data.get('chunking_strategy', 'hierarchical'),
                entity_types=doc_data.get('entity_types', []),
                matrix_configuration=doc_data.get('matrix_configuration'),
                validation_schema=doc_data.get('validation_schema', {}),
                quality_thresholds=doc_data.get('quality_thresholds', {})
            )
            documents.append(doc)
        
        # Restore relationships
        relationships = []
        for rel_data in snapshot.get('relationships', []):
            rel = PackageRelationship(
                from_document=rel_data['from_document'],
                to_document=rel_data['to_document'],
                relationship_type=rel_data['relationship_type'],
                metadata=rel_data.get('metadata', {})
            )
            relationships.append(rel)
        
        # Create package
        package = DocumentPackage(
            package_id=snapshot['package_id'],
            package_name=snapshot['package_name'],
            tenant_id=snapshot['tenant_id'],
            category=PackageCategory(snapshot['category']),
            version="1.0.0",  # Will be updated by caller
            status=PackageStatus(snapshot.get('status', 'DRAFT')),
            created_by=snapshot.get('created_by', 'system'),
            template_type=snapshot.get('template_type', ''),
            created_at=datetime.now(),
            updated_at=datetime.now(),
            template_mappings=snapshot.get('template_mappings', {}),
            validation_rules=snapshot.get('validation_rules', {})
        )
        
        # Add documents and relationships
        package.documents = documents
        package.relationships = relationships
        
        return package
    
    def _compare_documents(self, doc1: Dict[str, Any], doc2: Dict[str, Any]) -> List[str]:
        """Compare two document configurations"""
        changes = []
        
        # Compare basic fields
        for field in ['document_name', 'document_type', 'chunking_strategy']:
            if doc1.get(field) != doc2.get(field):
                changes.append(f"{field} changed from '{doc1.get(field)}' to '{doc2.get(field)}'")
        
        # Compare lists
        for field in ['required_sections', 'optional_sections', 'entity_types']:
            list1 = set(doc1.get(field, []))
            list2 = set(doc2.get(field, []))
            
            added = list2 - list1
            removed = list1 - list2
            
            if added:
                changes.append(f"Added {field}: {list(added)}")
            if removed:
                changes.append(f"Removed {field}: {list(removed)}")
        
        # Compare complex objects
        for field in ['expected_structure', 'matrix_configuration', 'validation_schema', 'quality_thresholds']:
            if doc1.get(field) != doc2.get(field):
                changes.append(f"{field} modified")
        
        return changes
    
    def _relationship_key(self, rel: Dict[str, Any]) -> str:
        """Create unique key for relationship"""
        return f"{rel['from_document']}->{rel['to_document']}:{rel['relationship_type']}"
    
    def _detect_structural_changes(self, snapshot1: Dict, snapshot2: Dict) -> List[str]:
        """Detect structural changes between snapshots"""
        changes = []
        
        # Check category change
        if snapshot1.get('category') != snapshot2.get('category'):
            changes.append(f"Category changed from {snapshot1.get('category')} to {snapshot2.get('category')}")
        
        # Check status change
        if snapshot1.get('status') != snapshot2.get('status'):
            changes.append(f"Status changed from {snapshot1.get('status')} to {snapshot2.get('status')}")
        
        # Check document count
        doc_count1 = len(snapshot1.get('documents', []))
        doc_count2 = len(snapshot2.get('documents', []))
        if doc_count1 != doc_count2:
            changes.append(f"Document count changed from {doc_count1} to {doc_count2}")
        
        # Check relationship count
        rel_count1 = len(snapshot1.get('relationships', []))
        rel_count2 = len(snapshot2.get('relationships', []))
        if rel_count1 != rel_count2:
            changes.append(f"Relationship count changed from {rel_count1} to {rel_count2}")
        
        return changes
    
    # Database interaction methods (Task 5 implementation)
    
    def _store_version_record(self, package_id: str, record: VersionRecord) -> None:
        """Store version record in database"""
        try:
            version_data = record.to_dict()
            self.graph_db.create_version_record(package_id, version_data)
        except Exception as e:
            self.logger.error(f"Failed to store version record: {str(e)}")
            raise
    
    def _store_package_snapshot(self, package_id: str, version: str, snapshot: Dict[str, Any]) -> None:
        """Store package snapshot in database"""
        try:
            self.graph_db.create_package_snapshot(package_id, version, snapshot)
        except Exception as e:
            self.logger.error(f"Failed to store package snapshot: {str(e)}")
            raise
    
    def _retrieve_version_history(self, package_id: str) -> List[Dict[str, Any]]:
        """Retrieve version history from database"""
        try:
            return self.graph_db.get_version_history(package_id)
        except Exception as e:
            self.logger.error(f"Failed to retrieve version history: {str(e)}")
            return []
    
    def _retrieve_package_snapshot(self, package_id: str, version: str) -> Optional[Dict[str, Any]]:
        """Retrieve package snapshot from database"""
        try:
            return self.graph_db.get_package_snapshot(package_id, version)
        except Exception as e:
            self.logger.error(f"Failed to retrieve package snapshot: {str(e)}")
            return None
    
    def _load_current_package(self, package_id: str) -> Optional[DocumentPackage]:
        """Load current package from database"""
        try:
            # Use PackageManager to load the package
            from src.package_manager import PackageManager
            
            package_manager = PackageManager(self.graph_db)
            return package_manager.load_package(package_id)
        except Exception as e:
            self.logger.error(f"Failed to load current package: {str(e)}")
            return None
    
    def _deserialize_version_record(self, data: Dict[str, Any]) -> VersionRecord:
        """Deserialize version record from database data"""
        return VersionRecord.from_dict(data)