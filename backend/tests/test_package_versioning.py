# Task 4: Unit tests for Package Versioning
# This file contains comprehensive tests for the PackageVersionManager class

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime
import sys
import os

# Add the parent directory to the path to import backend modules
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from src.package_versioning import (
    PackageVersionManager,
    ChangeType,
    VersionRecord,
    VersionDiff
)
from src.entities.document_package import (
    DocumentPackage,
    DocumentDefinition,
    PackageRelationship,
    PackageStatus,
    PackageCategory
)


class TestChangeType:
    """Test ChangeType enum"""
    
    def test_change_type_values(self):
        """Test change type enum values"""
        assert ChangeType.MAJOR.value == "MAJOR"
        assert ChangeType.MINOR.value == "MINOR"
        assert ChangeType.PATCH.value == "PATCH"


class TestVersionRecord:
    """Test VersionRecord dataclass"""
    
    def test_version_record_creation(self):
        """Test creating version record"""
        record = VersionRecord(
            version="1.2.3",
            change_type=ChangeType.MINOR,
            changes=["Added new feature"],
            created_at=datetime.now(),
            created_by="test_user",
            metadata={"package_id": "pkg_test_001"}
        )
        
        assert record.version == "1.2.3"
        assert record.change_type == ChangeType.MINOR
        assert record.changes == ["Added new feature"]
        assert record.created_by == "test_user"
        assert record.metadata["package_id"] == "pkg_test_001"
    
    def test_version_record_serialization(self):
        """Test version record to_dict and from_dict"""
        original = VersionRecord(
            version="2.0.0",
            change_type=ChangeType.MAJOR,
            changes=["Breaking change"],
            created_at=datetime.now(),
            created_by="admin",
            metadata={"test": "data"}
        )
        
        # Test to_dict
        data = original.to_dict()
        assert data["version"] == "2.0.0"
        assert data["change_type"] == "MAJOR"
        assert data["changes"] == ["Breaking change"]
        assert isinstance(data["created_at"], str)
        
        # Test from_dict
        restored = VersionRecord.from_dict(data)
        assert restored.version == original.version
        assert restored.change_type == original.change_type
        assert restored.changes == original.changes
        assert restored.created_by == original.created_by


class TestVersionDiff:
    """Test VersionDiff dataclass"""
    
    def test_version_diff_creation(self):
        """Test creating version diff"""
        diff = VersionDiff(
            from_version="1.0.0",
            to_version="1.1.0",
            added_documents=["doc_new"],
            removed_documents=["doc_old"],
            modified_documents=[{"document_id": "doc_mod", "changes": ["Updated"]}],
            structural_changes=["Status changed"],
            relationship_changes=["Added relationship"]
        )
        
        assert diff.from_version == "1.0.0"
        assert diff.to_version == "1.1.0"
        assert "doc_new" in diff.added_documents
        assert "doc_old" in diff.removed_documents
        assert len(diff.modified_documents) == 1
    
    def test_has_changes(self):
        """Test has_changes method"""
        # No changes
        empty_diff = VersionDiff("1.0.0", "1.0.1", [], [], [], [], [])
        assert not empty_diff.has_changes()
        
        # With changes
        diff_with_changes = VersionDiff(
            "1.0.0", "1.1.0", ["new_doc"], [], [], [], []
        )
        assert diff_with_changes.has_changes()


class TestPackageVersionManager:
    """Test PackageVersionManager class"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.mock_graph_db = Mock()
        self.version_manager = PackageVersionManager(self.mock_graph_db)
        
        # Create test package
        self.test_package = DocumentPackage(
            package_id="pkg_test_001",
            package_name="Test Package",
            tenant_id="tenant_001",
            category=PackageCategory.NQM,
            version="1.0.0",
            status=PackageStatus.DRAFT,
            created_by="test_user"
        )
    
    def test_version_manager_initialization(self):
        """Test version manager initialization"""
        assert self.version_manager.graph_db == self.mock_graph_db
        assert self.version_manager.logger is not None
    
    def test_create_version_patch(self):
        """Test creating patch version"""
        # Mock database methods
        self.version_manager._store_version_record = Mock()
        self.version_manager._store_package_snapshot = Mock()
        
        changes = ["Fixed validation bug"]
        new_version = self.version_manager.create_version(
            self.test_package, ChangeType.PATCH, changes, "test_user"
        )
        
        assert new_version == "1.0.1"
        assert self.test_package.version == "1.0.1"
        
        # Verify database methods were called
        self.version_manager._store_version_record.assert_called_once()
        self.version_manager._store_package_snapshot.assert_called_once()
    
    def test_create_version_minor(self):
        """Test creating minor version"""
        self.version_manager._store_version_record = Mock()
        self.version_manager._store_package_snapshot = Mock()
        
        changes = ["Added new document type"]
        new_version = self.version_manager.create_version(
            self.test_package, ChangeType.MINOR, changes
        )
        
        assert new_version == "1.1.0"
        assert self.test_package.version == "1.1.0"
    
    def test_create_version_major(self):
        """Test creating major version"""
        self.version_manager._store_version_record = Mock()
        self.version_manager._store_package_snapshot = Mock()
        
        changes = ["Restructured package format"]
        new_version = self.version_manager.create_version(
            self.test_package, ChangeType.MAJOR, changes
        )
        
        assert new_version == "2.0.0"
        assert self.test_package.version == "2.0.0"
    
    def test_create_version_invalid_current_version(self):
        """Test creating version with invalid current version"""
        self.test_package.version = "invalid_version"
        
        with pytest.raises(ValueError, match="Invalid current version"):
            self.version_manager.create_version(
                self.test_package, ChangeType.PATCH
            )
    
    def test_get_version_history(self):
        """Test getting version history"""
        # Mock version history data
        mock_history = [
            {
                "version": "1.0.0",
                "change_type": "PATCH",
                "changes": ["Initial version"],
                "created_at": datetime.now().isoformat(),
                "created_by": "user1",
                "metadata": {}
            },
            {
                "version": "1.1.0", 
                "change_type": "MINOR",
                "changes": ["Added feature"],
                "created_at": datetime.now().isoformat(),
                "created_by": "user2",
                "metadata": {}
            }
        ]
        
        self.version_manager._retrieve_version_history = Mock(return_value=mock_history)
        
        history = self.version_manager.get_version_history("pkg_test_001")
        
        assert len(history) == 2
        assert history[0].version == "1.1.0"  # Newest first
        assert history[1].version == "1.0.0"
        assert all(isinstance(record, VersionRecord) for record in history)
    
    def test_get_version_by_number(self):
        """Test getting specific version"""
        mock_history = [
            {
                "version": "1.0.0",
                "change_type": "PATCH",
                "changes": ["Initial"],
                "created_at": datetime.now().isoformat(),
                "created_by": "user1",
                "metadata": {}
            }
        ]
        
        self.version_manager._retrieve_version_history = Mock(return_value=mock_history)
        
        record = self.version_manager.get_version_by_number("pkg_test_001", "1.0.0")
        
        assert record is not None
        assert record.version == "1.0.0"
        
        # Test not found
        not_found = self.version_manager.get_version_by_number("pkg_test_001", "9.9.9")
        assert not_found is None
    
    def test_rollback_version(self):
        """Test rolling back to previous version"""
        # Mock version record
        target_record = VersionRecord(
            version="1.0.0",
            change_type=ChangeType.PATCH,
            changes=["Initial"],
            created_at=datetime.now(),
            created_by="user1",
            metadata={}
        )
        
        # Mock package snapshot
        mock_snapshot = {
            "package_id": "pkg_test_001",
            "package_name": "Test Package",
            "tenant_id": "tenant_001",
            "category": "NQM",
            "status": "DRAFT",
            "documents": [],
            "relationships": []
        }
        
        # Mock current package
        current_package = DocumentPackage(
            package_id="pkg_test_001",
            package_name="Test Package",
            tenant_id="tenant_001",
            category=PackageCategory.NQM,
            version="1.2.0"
        )
        
        # Set up mocks
        self.version_manager.get_version_by_number = Mock(return_value=target_record)
        self.version_manager._retrieve_package_snapshot = Mock(return_value=mock_snapshot)
        self.version_manager._load_current_package = Mock(return_value=current_package)
        self.version_manager._store_version_record = Mock()
        self.version_manager._store_package_snapshot = Mock()
        
        # Perform rollback
        restored_package = self.version_manager.rollback_version(
            "pkg_test_001", "1.0.0", "admin"
        )
        
        assert restored_package is not None
        assert restored_package.version == "2.0.0"  # New major version for rollback
        
        # Verify database operations
        self.version_manager._store_version_record.assert_called_once()
        self.version_manager._store_package_snapshot.assert_called_once()
    
    def test_rollback_version_not_found(self):
        """Test rollback with version not found"""
        self.version_manager.get_version_by_number = Mock(return_value=None)
        
        with pytest.raises(ValueError, match="Version 9.9.9 not found"):
            self.version_manager.rollback_version("pkg_test_001", "9.9.9")
    
    def test_diff_versions(self):
        """Test comparing two versions"""
        # Mock snapshots
        snapshot1 = {
            "package_id": "pkg_test_001",
            "category": "NQM",
            "status": "DRAFT",
            "documents": [
                {
                    "document_id": "doc1",
                    "document_name": "Doc 1",
                    "document_type": "guidelines"
                }
            ],
            "relationships": []
        }
        
        snapshot2 = {
            "package_id": "pkg_test_001", 
            "category": "NQM",
            "status": "ACTIVE",
            "documents": [
                {
                    "document_id": "doc1",
                    "document_name": "Doc 1 Updated",
                    "document_type": "guidelines"
                },
                {
                    "document_id": "doc2",
                    "document_name": "Doc 2",
                    "document_type": "matrix"
                }
            ],
            "relationships": []
        }
        
        self.version_manager._retrieve_package_snapshot = Mock(side_effect=[snapshot1, snapshot2])
        
        diff = self.version_manager.diff_versions("pkg_test_001", "1.0.0", "1.1.0")
        
        assert diff.from_version == "1.0.0"
        assert diff.to_version == "1.1.0"
        assert "doc2" in diff.added_documents
        assert len(diff.modified_documents) == 1
        assert diff.modified_documents[0]["document_id"] == "doc1"
        assert "Status changed" in diff.structural_changes
    
    def test_validate_version_sequence(self):
        """Test version sequence validation"""
        # Mock valid version history
        valid_history = [
            {
                "version": "1.0.0",
                "change_type": "PATCH",
                "changes": [],
                "created_at": datetime.now().isoformat(),
                "created_by": "user1",
                "metadata": {}
            },
            {
                "version": "1.0.1",
                "change_type": "PATCH", 
                "changes": [],
                "created_at": datetime.now().isoformat(),
                "created_by": "user1",
                "metadata": {}
            },
            {
                "version": "1.1.0",
                "change_type": "MINOR",
                "changes": [],
                "created_at": datetime.now().isoformat(),
                "created_by": "user1",
                "metadata": {}
            }
        ]
        
        self.version_manager._retrieve_version_history = Mock(return_value=valid_history)
        
        issues = self.version_manager.validate_version_sequence("pkg_test_001")
        assert len(issues) == 0
    
    def test_validate_version_sequence_invalid(self):
        """Test version sequence validation with invalid sequence"""
        # Mock invalid version history (skip from 1.0.0 to 1.2.0)
        invalid_history = [
            {
                "version": "1.0.0",
                "change_type": "PATCH",
                "changes": [],
                "created_at": datetime.now().isoformat(),
                "created_by": "user1",
                "metadata": {}
            },
            {
                "version": "1.2.0",  # Invalid jump
                "change_type": "MINOR",
                "changes": [],
                "created_at": datetime.now().isoformat(),
                "created_by": "user1",
                "metadata": {}
            }
        ]
        
        self.version_manager._retrieve_version_history = Mock(return_value=invalid_history)
        
        issues = self.version_manager.validate_version_sequence("pkg_test_001")
        assert len(issues) > 0
        assert any("Invalid version increment" in issue for issue in issues)


class TestVersionManagerHelpers:
    """Test PackageVersionManager helper methods"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.version_manager = PackageVersionManager()
    
    def test_calculate_new_version(self):
        """Test version calculation"""
        assert self.version_manager._calculate_new_version("1.0.0", ChangeType.MAJOR) == "2.0.0"
        assert self.version_manager._calculate_new_version("1.5.3", ChangeType.MINOR) == "1.6.0"
        assert self.version_manager._calculate_new_version("1.5.3", ChangeType.PATCH) == "1.5.4"
        assert self.version_manager._calculate_new_version("2.10.15", ChangeType.MAJOR) == "3.0.0"
    
    def test_is_valid_version(self):
        """Test version validation"""
        assert self.version_manager._is_valid_version("1.0.0") is True
        assert self.version_manager._is_valid_version("10.5.23") is True
        assert self.version_manager._is_valid_version("0.0.1") is True
        
        assert self.version_manager._is_valid_version("1.0") is False
        assert self.version_manager._is_valid_version("1.0.0.0") is False
        assert self.version_manager._is_valid_version("1.a.0") is False
        assert self.version_manager._is_valid_version("invalid") is False
    
    def test_version_to_tuple(self):
        """Test version to tuple conversion"""
        assert self.version_manager._version_to_tuple("1.0.0") == (1, 0, 0)
        assert self.version_manager._version_to_tuple("2.10.5") == (2, 10, 5)
        assert self.version_manager._version_to_tuple("0.0.1") == (0, 0, 1)
    
    def test_is_valid_version_increment(self):
        """Test version increment validation"""
        # Valid increments
        assert self.version_manager._is_valid_version_increment((1, 0, 0), (2, 0, 0)) is True  # MAJOR
        assert self.version_manager._is_valid_version_increment((1, 0, 0), (1, 1, 0)) is True  # MINOR
        assert self.version_manager._is_valid_version_increment((1, 0, 0), (1, 0, 1)) is True  # PATCH
        
        # Invalid increments
        assert self.version_manager._is_valid_version_increment((1, 0, 0), (2, 1, 0)) is False  # MAJOR with minor
        assert self.version_manager._is_valid_version_increment((1, 0, 0), (1, 2, 0)) is False  # Skip minor
        assert self.version_manager._is_valid_version_increment((1, 0, 0), (1, 0, 2)) is False  # Skip patch
    
    def test_generate_change_summary(self):
        """Test change summary generation"""
        summary = self.version_manager._generate_change_summary(
            ChangeType.MINOR, ["Added feature A", "Added feature B"]
        )
        assert "MINOR" in summary
        assert "Added feature A" in summary
        
        # Test with no changes
        summary_empty = self.version_manager._generate_change_summary(ChangeType.PATCH, [])
        assert "PATCH version update" in summary_empty
        
        # Test with many changes (should truncate)
        many_changes = [f"Change {i}" for i in range(10)]
        summary_many = self.version_manager._generate_change_summary(ChangeType.MAJOR, many_changes)
        assert "..." in summary_many
    
    def test_create_package_snapshot(self):
        """Test package snapshot creation"""
        package = DocumentPackage(
            package_id="pkg_test_001",
            package_name="Test Package",
            tenant_id="tenant_001", 
            category=PackageCategory.NQM,
            version="1.0.0"
        )
        
        # Add a document
        doc = DocumentDefinition(
            document_id="doc_001",
            document_type="guidelines",
            document_name="Test Guidelines"
        )
        package.add_document(doc)
        
        snapshot = self.version_manager._create_package_snapshot(package)
        
        assert snapshot["package_id"] == "pkg_test_001"
        assert snapshot["package_name"] == "Test Package"
        assert snapshot["category"] == "NQM"
        assert len(snapshot["documents"]) == 1
        assert snapshot["documents"][0]["document_id"] == "doc_001"
        assert "snapshot_created" in snapshot
    
    def test_serialize_document(self):
        """Test document serialization"""
        doc = DocumentDefinition(
            document_id="doc_001",
            document_type="guidelines",
            document_name="Test Guidelines",
            required_sections=["Section 1"],
            entity_types=["ENTITY_TYPE"]
        )
        
        serialized = self.version_manager._serialize_document(doc)
        
        assert serialized["document_id"] == "doc_001"
        assert serialized["document_type"] == "guidelines"
        assert serialized["document_name"] == "Test Guidelines"
        assert serialized["required_sections"] == ["Section 1"]
        assert serialized["entity_types"] == ["ENTITY_TYPE"]
    
    def test_compare_documents(self):
        """Test document comparison"""
        doc1 = {
            "document_name": "Original Name",
            "document_type": "guidelines",
            "required_sections": ["Section 1"],
            "entity_types": ["TYPE_A"]
        }
        
        doc2 = {
            "document_name": "Updated Name",
            "document_type": "guidelines", 
            "required_sections": ["Section 1", "Section 2"],
            "entity_types": ["TYPE_A", "TYPE_B"]
        }
        
        changes = self.version_manager._compare_documents(doc1, doc2)
        
        assert len(changes) > 0
        assert any("document_name changed" in change for change in changes)
        assert any("Added required_sections" in change for change in changes)
        assert any("Added entity_types" in change for change in changes)
    
    def test_detect_structural_changes(self):
        """Test structural change detection"""
        snapshot1 = {
            "category": "NQM",
            "status": "DRAFT",
            "documents": [{"id": "doc1"}],
            "relationships": []
        }
        
        snapshot2 = {
            "category": "RTL",
            "status": "ACTIVE", 
            "documents": [{"id": "doc1"}, {"id": "doc2"}],
            "relationships": [{"from": "doc1", "to": "doc2"}]
        }
        
        changes = self.version_manager._detect_structural_changes(snapshot1, snapshot2)
        
        assert len(changes) >= 3
        assert any("Category changed" in change for change in changes)
        assert any("Status changed" in change for change in changes)
        assert any("Document count changed" in change for change in changes)
        assert any("Relationship count changed" in change for change in changes)