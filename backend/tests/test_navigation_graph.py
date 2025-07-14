# Task 12: Navigation Graph Builder Tests
# Comprehensive tests for NavigationGraphBuilder class

import unittest
from unittest.mock import Mock, MagicMock, patch
from datetime import datetime
from typing import List, Dict, Any

# Import the classes being tested
from src.navigation_graph import (
    NavigationGraphBuilder,
    NavigationGraphMetrics,
    GraphBuildResult
)

# Import dependencies
from src.entities.navigation_models import (
    EnhancedNavigationNode,
    HierarchicalChunk,
    ChunkRelationship,
    NavigationContext,
    DecisionTreeNode,
    RelationshipType,
    QualityRating
)
from src.semantic_chunker import ChunkType
from src.navigation_extractor import NavigationLevel


class TestNavigationGraphBuilder(unittest.TestCase):
    """Test suite for NavigationGraphBuilder class"""
    
    def setUp(self):
        """Set up test fixtures"""
        # Mock database connection
        self.mock_graph_db = Mock()
        self.mock_graph_db.graph = Mock()
        
        # Initialize NavigationGraphBuilder
        self.builder = NavigationGraphBuilder(self.mock_graph_db)
        
        # Sample test data
        self.package_id = "test_package_001"
        self.navigation_graph_id = "navgraph_test_package_001_20240101_12345678"
        
        # Create sample navigation nodes
        self.sample_navigation_nodes = self._create_sample_navigation_nodes()
        
        # Create sample hierarchical chunks
        self.sample_hierarchical_chunks = self._create_sample_hierarchical_chunks()
        
        # Create sample chunk relationships
        self.sample_chunk_relationships = self._create_sample_chunk_relationships()

    def _create_sample_navigation_nodes(self) -> List[EnhancedNavigationNode]:
        """Create sample navigation nodes for testing"""
        return [
            EnhancedNavigationNode(
                node_id="nav_001",
                level=NavigationLevel.CHAPTER,
                title="Borrower Eligibility",
                content="Chapter content about borrower eligibility requirements...",
                parent_id="nav_root",
                confidence_score=0.95,
                quality_rating=QualityRating.EXCELLENT
            ),
            EnhancedNavigationNode(
                node_id="nav_002",
                level=NavigationLevel.SECTION,
                title="Income Requirements",
                content="Section content about income requirements and documentation...",
                parent_id="nav_001",
                confidence_score=0.92,
                quality_rating=QualityRating.GOOD
            ),
            EnhancedNavigationNode(
                node_id="nav_003",
                level=NavigationLevel.SUBSECTION,
                title="Income Verification Decision",
                content="Decision logic for income verification processes...",
                parent_id="nav_002",
                confidence_score=0.88,
                quality_rating=QualityRating.GOOD
            )
        ]

    def _create_sample_hierarchical_chunks(self) -> List[HierarchicalChunk]:
        """Create sample hierarchical chunks for testing"""
        return [
            HierarchicalChunk(
                chunk_id="chunk_001",
                chunk_type=ChunkType.HEADER,
                content="Borrower Eligibility Overview\n\nThis section outlines the basic requirements for borrower eligibility...",
                content_summary="Overview of borrower eligibility requirements",
                navigation_context=NavigationContext(
                    navigation_path=["NAA Product Guidelines", "Borrower Eligibility"],
                    hierarchy_level=1
                ),
                parent_chunk_id=None,
                decision_logic=None,
                quality_score=0.95,
                token_count=150
            ),
            HierarchicalChunk(
                chunk_id="chunk_002",
                chunk_type=ChunkType.CONTENT,
                content="Income Requirements:\n1. Minimum 2 years employment history\n2. Debt-to-income ratio below 45%\n3. Verified income documentation required",
                content_summary="Specific income requirements and documentation needs",
                navigation_context=NavigationContext(
                    navigation_path=["NAA Product Guidelines", "Borrower Eligibility", "Income Requirements"],
                    hierarchy_level=2
                ),
                parent_chunk_id="chunk_001",
                decision_logic="eligibility_check: employment_history, dti_ratio, income_verification",
                quality_score=0.92,
                token_count=75
            ),
            HierarchicalChunk(
                chunk_id="chunk_003",
                chunk_type=ChunkType.DECISION,
                content="Decision Tree: Income Verification\nIF employment_history >= 2_years AND dti_ratio <= 0.45 THEN APPROVE\nELSE IF employment_history >= 1_year AND dti_ratio <= 0.40 THEN REFER\nELSE DECLINE",
                content_summary="Decision tree for income verification approval",
                navigation_context=NavigationContext(
                    navigation_path=["NAA Product Guidelines", "Borrower Eligibility", "Income Requirements", "Income Verification Decision"],
                    hierarchy_level=3
                ),
                parent_chunk_id="chunk_002",
                decision_logic="decision_tree: APPROVE, REFER, DECLINE",
                quality_score=0.88,
                token_count=120
            )
        ]

    def _create_sample_chunk_relationships(self) -> List[ChunkRelationship]:
        """Create sample chunk relationships for testing"""
        return [
            ChunkRelationship(
                source_chunk_id="chunk_001",
                target_chunk_id="chunk_002",
                relationship_type=RelationshipType.PARENT_CHILD,
                strength=0.95,
                confidence=0.92,
                evidence=["hierarchical_structure", "content_flow"]
            ),
            ChunkRelationship(
                source_chunk_id="chunk_002",
                target_chunk_id="chunk_003",
                relationship_type=RelationshipType.DECISION_BRANCH,
                strength=0.88,
                confidence=0.85,
                evidence=["decision_logic", "conditional_statements"]
            )
        ]

    def test_navigation_graph_builder_initialization(self):
        """Test NavigationGraphBuilder initialization"""
        self.assertIsNotNone(self.builder)
        self.assertEqual(self.builder.graph_db, self.mock_graph_db)
        self.assertIsNotNone(self.builder.logger)
        
        # Test node type mappings
        self.assertIn("CHAPTER", self.builder.neo4j_node_types)
        self.assertIn("SECTION", self.builder.neo4j_node_types)
        self.assertIn("DECISION_FLOW_SECTION", self.builder.neo4j_node_types)
        
        # Test relationship type mappings
        self.assertIn(RelationshipType.PARENT_CHILD, self.builder.neo4j_relationship_types)
        self.assertIn(RelationshipType.DECISION_BRANCH, self.builder.neo4j_relationship_types)

    def test_generate_navigation_graph_id(self):
        """Test navigation graph ID generation"""
        graph_id = self.builder._generate_navigation_graph_id(self.package_id)
        
        self.assertTrue(graph_id.startswith("navgraph_"))
        self.assertIn(self.package_id, graph_id)
        self.assertTrue(len(graph_id) > 30)  # Should be substantial length
        
        # Test uniqueness
        graph_id2 = self.builder._generate_navigation_graph_id(self.package_id)
        self.assertNotEqual(graph_id, graph_id2)

    def test_validate_navigation_input_valid(self):
        """Test input validation with valid data"""
        result = self.builder._validate_navigation_input(
            self.sample_navigation_nodes,
            self.sample_hierarchical_chunks,
            self.sample_chunk_relationships
        )
        
        self.assertTrue(result['is_valid'])
        self.assertEqual(len(result['errors']), 0)

    def test_validate_navigation_input_empty_nodes(self):
        """Test input validation with empty navigation nodes"""
        result = self.builder._validate_navigation_input(
            [],  # Empty navigation nodes
            self.sample_hierarchical_chunks,
            self.sample_chunk_relationships
        )
        
        self.assertFalse(result['is_valid'])
        self.assertIn("No navigation nodes provided", result['errors'])

    def test_validate_navigation_input_duplicate_ids(self):
        """Test input validation with duplicate node IDs"""
        # Create duplicate node
        duplicate_nodes = self.sample_navigation_nodes.copy()
        duplicate_nodes.append(self.sample_navigation_nodes[0])  # Duplicate first node
        
        result = self.builder._validate_navigation_input(
            duplicate_nodes,
            self.sample_hierarchical_chunks,
            self.sample_chunk_relationships
        )
        
        self.assertFalse(result['is_valid'])
        self.assertTrue(any("Duplicate navigation node ID" in error for error in result['errors']))

    def test_validate_navigation_input_invalid_relationships(self):
        """Test input validation with invalid relationships"""
        # Create relationship with non-existent chunk ID
        invalid_relationships = [
            ChunkRelationship(
                source_chunk_id="non_existent_chunk",
                target_chunk_id="chunk_002",
                relationship_type=RelationshipType.REFERENCES,
                strength=0.5,
                confidence=0.5,
                evidence=[]
            )
        ]
        
        result = self.builder._validate_navigation_input(
            self.sample_navigation_nodes,
            self.sample_hierarchical_chunks,
            invalid_relationships
        )
        
        self.assertFalse(result['is_valid'])
        self.assertTrue(any("unknown source chunk" in error for error in result['errors']))

    @patch.object(NavigationGraphBuilder, '_generate_navigation_graph_id')
    @patch.object(NavigationGraphBuilder, '_create_navigation_root')
    @patch.object(NavigationGraphBuilder, '_create_navigation_nodes')
    @patch.object(NavigationGraphBuilder, '_create_chunk_nodes')
    @patch.object(NavigationGraphBuilder, '_create_navigation_relationships')
    @patch.object(NavigationGraphBuilder, '_create_chunk_relationships')
    @patch.object(NavigationGraphBuilder, '_link_navigation_to_chunks')
    @patch.object(NavigationGraphBuilder, '_calculate_graph_metrics')
    @patch.object(NavigationGraphBuilder, '_store_graph_metadata')
    @patch.object(NavigationGraphBuilder, '_validate_graph_completeness')
    def test_build_navigation_graph_success(
        self,
        mock_validate_completeness,
        mock_store_metadata,
        mock_calculate_metrics,
        mock_link_nav_chunks,
        mock_create_chunk_rels,
        mock_create_nav_rels,
        mock_create_chunks,
        mock_create_nav_nodes,
        mock_create_root,
        mock_generate_id
    ):
        """Test successful navigation graph building"""
        # Setup mocks
        mock_generate_id.return_value = self.navigation_graph_id
        mock_create_root.return_value = f"{self.navigation_graph_id}_root"
        
        mock_create_nav_nodes.return_value = {
            'success': True,
            'nodes_created': 3,
            'errors': []
        }
        
        mock_create_chunks.return_value = {
            'success': True,
            'nodes_created': 3,
            'errors': []
        }
        
        mock_create_nav_rels.return_value = {
            'success': True,
            'relationships_created': 2,
            'errors': []
        }
        
        mock_create_chunk_rels.return_value = {
            'success': True,
            'relationships_created': 2,
            'errors': []
        }
        
        mock_link_nav_chunks.return_value = {
            'success': True,
            'relationships_created': 3,
            'errors': []
        }
        
        mock_calculate_metrics.return_value = NavigationGraphMetrics(
            total_nodes=6,
            total_relationships=7,
            navigation_depth=3,
            decision_trees_count=1,
            orphaned_nodes=0,
            completeness_score=1.0,
            accuracy_score=0.95
        )
        
        mock_validate_completeness.return_value = {
            'warnings': []
        }
        
        # Execute test
        result = self.builder.build_navigation_graph(
            self.package_id,
            self.sample_navigation_nodes,
            self.sample_hierarchical_chunks,
            self.sample_chunk_relationships
        )
        
        # Verify result
        self.assertTrue(result.success)
        self.assertEqual(result.package_id, self.package_id)
        self.assertEqual(result.navigation_graph_id, self.navigation_graph_id)
        self.assertEqual(result.nodes_created, 6)
        self.assertEqual(result.relationships_created, 7)
        self.assertEqual(len(result.errors), 0)
        
        # Verify metrics
        self.assertEqual(result.metrics.total_nodes, 6)
        self.assertEqual(result.metrics.decision_trees_count, 1)
        self.assertEqual(result.metrics.completeness_score, 1.0)

    @patch.object(NavigationGraphBuilder, '_generate_navigation_graph_id')
    def test_build_navigation_graph_validation_failure(self, mock_generate_id):
        """Test navigation graph building with validation failure"""
        mock_generate_id.return_value = self.navigation_graph_id
        
        # Use empty navigation nodes to trigger validation failure
        result = self.builder.build_navigation_graph(
            self.package_id,
            [],  # Empty navigation nodes
            self.sample_hierarchical_chunks,
            self.sample_chunk_relationships
        )
        
        self.assertFalse(result.success)
        self.assertGreater(len(result.errors), 0)
        self.assertIn("No navigation nodes provided", result.errors)

    def test_create_navigation_root(self):
        """Test navigation root creation"""
        # Mock query result
        self.mock_graph_db.graph.query.return_value = [{'root_id': f"{self.navigation_graph_id}_root"}]
        
        root_id = self.builder._create_navigation_root(self.navigation_graph_id, self.package_id)
        
        self.assertEqual(root_id, f"{self.navigation_graph_id}_root")
        self.mock_graph_db.graph.query.assert_called_once()
        
        # Verify query parameters
        call_args = self.mock_graph_db.graph.query.call_args
        query_params = call_args[0][1]
        self.assertEqual(query_params['graph_id'], self.navigation_graph_id)
        self.assertEqual(query_params['package_id'], self.package_id)

    def test_create_navigation_nodes_success(self):
        """Test successful navigation node creation"""
        # Mock successful query results
        self.mock_graph_db.graph.query.return_value = [{'created_id': 'nav_001'}]
        
        result = self.builder._create_navigation_nodes(
            self.navigation_graph_id,
            self.sample_navigation_nodes,
            f"{self.navigation_graph_id}_root"
        )
        
        self.assertTrue(result['success'])
        self.assertEqual(result['nodes_created'], len(self.sample_navigation_nodes))
        self.assertEqual(len(result['errors']), 0)
        
        # Verify correct number of database calls
        self.assertEqual(self.mock_graph_db.graph.query.call_count, len(self.sample_navigation_nodes))

    def test_create_navigation_nodes_failure(self):
        """Test navigation node creation with database failures"""
        # Mock query to raise exception
        self.mock_graph_db.graph.query.side_effect = Exception("Database connection failed")
        
        result = self.builder._create_navigation_nodes(
            self.navigation_graph_id,
            self.sample_navigation_nodes,
            f"{self.navigation_graph_id}_root"
        )
        
        self.assertFalse(result['success'])
        self.assertEqual(result['nodes_created'], 0)
        self.assertGreater(len(result['errors']), 0)

    def test_create_chunk_nodes_success(self):
        """Test successful chunk node creation"""
        # Mock successful query results
        self.mock_graph_db.graph.query.return_value = [{'created_id': 'chunk_001'}]
        
        result = self.builder._create_chunk_nodes(
            self.navigation_graph_id,
            self.sample_hierarchical_chunks
        )
        
        self.assertTrue(result['success'])
        self.assertEqual(result['nodes_created'], len(self.sample_hierarchical_chunks))
        self.assertEqual(len(result['errors']), 0)

    def test_create_chunk_relationships_success(self):
        """Test successful chunk relationship creation"""
        # Mock successful query results
        self.mock_graph_db.graph.query.return_value = [{'r': 'relationship_created'}]
        
        result = self.builder._create_chunk_relationships(
            self.navigation_graph_id,
            self.sample_chunk_relationships
        )
        
        self.assertTrue(result['success'])
        self.assertEqual(result['relationships_created'], len(self.sample_chunk_relationships))
        self.assertEqual(len(result['errors']), 0)

    def test_calculate_graph_metrics(self):
        """Test graph metrics calculation"""
        # Mock database query results
        self.mock_graph_db.graph.query.side_effect = [
            [{'total_nodes': 6, 'total_relationships': 7}],  # Count query
            [{'orphaned_count': 0}]  # Orphaned nodes query
        ]
        
        metrics = self.builder._calculate_graph_metrics(
            self.navigation_graph_id,
            self.sample_navigation_nodes,
            self.sample_hierarchical_chunks,
            self.sample_chunk_relationships
        )
        
        self.assertEqual(metrics.total_nodes, 6)
        self.assertEqual(metrics.total_relationships, 7)
        self.assertEqual(metrics.navigation_depth, 3)  # Max hierarchy level from sample data
        self.assertEqual(metrics.decision_trees_count, 1)  # One DECISION_FLOW_SECTION in sample
        self.assertEqual(metrics.orphaned_nodes, 0)
        self.assertGreater(metrics.completeness_score, 0)
        self.assertGreater(metrics.accuracy_score, 0)

    def test_store_graph_metadata(self):
        """Test graph metadata storage"""
        metrics = NavigationGraphMetrics(
            total_nodes=6,
            total_relationships=7,
            navigation_depth=3,
            decision_trees_count=1,
            orphaned_nodes=0,
            completeness_score=1.0,
            accuracy_score=0.95,
            processing_time_ms=1500
        )
        
        # Mock successful query
        self.mock_graph_db.graph.query.return_value = [{'created_id': self.navigation_graph_id}]
        
        # Should not raise exception
        self.builder._store_graph_metadata(self.navigation_graph_id, self.package_id, metrics)
        
        # Verify database call
        self.mock_graph_db.graph.query.assert_called_once()
        
        # Verify query parameters
        call_args = self.mock_graph_db.graph.query.call_args
        query_params = call_args[0][1]
        self.assertEqual(query_params['graph_id'], self.navigation_graph_id)
        self.assertEqual(query_params['package_id'], self.package_id)
        self.assertEqual(query_params['total_nodes'], 6)
        self.assertEqual(query_params['completeness'], 1.0)

    def test_validate_graph_completeness_success(self):
        """Test graph completeness validation with no issues"""
        # Mock queries to return no orphaned or isolated nodes
        self.mock_graph_db.graph.query.side_effect = [
            [],  # No orphaned nodes
            []   # No isolated nodes
        ]
        
        result = self.builder._validate_graph_completeness(self.navigation_graph_id)
        
        self.assertTrue(result['is_complete'])
        self.assertEqual(len(result['warnings']), 0)

    def test_validate_graph_completeness_with_issues(self):
        """Test graph completeness validation with orphaned nodes"""
        # Mock queries to return orphaned nodes
        self.mock_graph_db.graph.query.side_effect = [
            [{'orphaned_id': 'nav_orphan_001', 'node_labels': ['NavigationSection']}],  # Orphaned nodes
            []  # No isolated nodes
        ]
        
        result = self.builder._validate_graph_completeness(self.navigation_graph_id)
        
        self.assertFalse(result['is_complete'])
        self.assertGreater(len(result['warnings']), 0)
        self.assertTrue(any("Orphaned node detected" in warning for warning in result['warnings']))

    def test_enhance_navigation_nodes_placeholder(self):
        """Test enhance_navigation_nodes method (placeholder implementation)"""
        enhancement_config = {
            'apply_content_enhancement': True,
            'apply_relationship_enhancement': True,
            'apply_quality_enhancement': True
        }
        
        # Mock the helper methods since they're not fully implemented
        with patch.object(self.builder, '_retrieve_navigation_nodes', return_value=[{'node_id': 'nav_001'}]):
            with patch.object(self.builder, '_apply_content_enhancements', return_value={'count': 1}):
                with patch.object(self.builder, '_apply_relationship_enhancements', return_value={'count': 1}):
                    with patch.object(self.builder, '_apply_quality_enhancements', return_value={'count': 1}):
                        with patch.object(self.builder, '_update_enhancement_metadata'):
                            result = self.builder.enhance_navigation_nodes(
                                self.navigation_graph_id,
                                enhancement_config
                            )
        
        self.assertTrue(result['success'])
        self.assertEqual(result['enhancements_applied'], 3)

    def test_query_navigation_path_placeholder(self):
        """Test query_navigation_path method (placeholder implementation)"""
        target_criteria = {
            'node_type': 'DECISION_FLOW_SECTION',
            'hierarchy_level': 3
        }
        
        # Mock the helper methods
        with patch.object(self.builder, '_build_path_query', return_value="MATCH (n) RETURN n"):
            with patch.object(self.builder, '_process_path_results', return_value=[]):
                result = self.builder.query_navigation_path(
                    self.navigation_graph_id,
                    "nav_001",
                    target_criteria
                )
        
        self.assertTrue(result['success'])
        self.assertEqual(result['paths_found'], 0)

    def test_link_navigation_to_chunks_success(self):
        """Test successful linking of navigation nodes to chunks"""
        # Mock successful query results
        self.mock_graph_db.graph.query.return_value = [{'r': 'relationship_created'}]
        
        result = self.builder._link_navigation_to_chunks(
            self.navigation_graph_id,
            self.sample_navigation_nodes,
            self.sample_hierarchical_chunks
        )
        
        self.assertTrue(result['success'])
        self.assertGreater(result['relationships_created'], 0)
        self.assertEqual(len(result['errors']), 0)

    def test_error_handling_in_build_navigation_graph(self):
        """Test error handling during graph building"""
        # Mock an exception during validation
        with patch.object(self.builder, '_validate_navigation_input', side_effect=Exception("Validation error")):
            result = self.builder.build_navigation_graph(
                self.package_id,
                self.sample_navigation_nodes,
                self.sample_hierarchical_chunks,
                self.sample_chunk_relationships
            )
        
        self.assertFalse(result.success)
        self.assertGreater(len(result.errors), 0)
        self.assertTrue(any("Graph building failed" in error for error in result.errors))


class TestNavigationGraphMetrics(unittest.TestCase):
    """Test suite for NavigationGraphMetrics class"""
    
    def test_navigation_graph_metrics_initialization(self):
        """Test NavigationGraphMetrics initialization with defaults"""
        metrics = NavigationGraphMetrics()
        
        self.assertEqual(metrics.total_nodes, 0)
        self.assertEqual(metrics.total_relationships, 0)
        self.assertEqual(metrics.navigation_depth, 0)
        self.assertEqual(metrics.decision_trees_count, 0)
        self.assertEqual(metrics.orphaned_nodes, 0)
        self.assertEqual(metrics.completeness_score, 0.0)
        self.assertEqual(metrics.accuracy_score, 0.0)
        self.assertEqual(metrics.processing_time_ms, 0)

    def test_navigation_graph_metrics_with_values(self):
        """Test NavigationGraphMetrics with specific values"""
        metrics = NavigationGraphMetrics(
            total_nodes=10,
            total_relationships=15,
            navigation_depth=4,
            decision_trees_count=2,
            orphaned_nodes=1,
            completeness_score=0.95,
            accuracy_score=0.88,
            processing_time_ms=2500
        )
        
        self.assertEqual(metrics.total_nodes, 10)
        self.assertEqual(metrics.total_relationships, 15)
        self.assertEqual(metrics.navigation_depth, 4)
        self.assertEqual(metrics.decision_trees_count, 2)
        self.assertEqual(metrics.orphaned_nodes, 1)
        self.assertEqual(metrics.completeness_score, 0.95)
        self.assertEqual(metrics.accuracy_score, 0.88)
        self.assertEqual(metrics.processing_time_ms, 2500)


class TestGraphBuildResult(unittest.TestCase):
    """Test suite for GraphBuildResult class"""
    
    def test_graph_build_result_success(self):
        """Test GraphBuildResult for successful operation"""
        metrics = NavigationGraphMetrics(
            total_nodes=5,
            total_relationships=7,
            completeness_score=1.0,
            accuracy_score=0.95
        )
        
        result = GraphBuildResult(
            success=True,
            package_id="test_package",
            navigation_graph_id="navgraph_123",
            nodes_created=5,
            relationships_created=7,
            metrics=metrics,
            errors=[],
            warnings=[]
        )
        
        self.assertTrue(result.success)
        self.assertEqual(result.package_id, "test_package")
        self.assertEqual(result.navigation_graph_id, "navgraph_123")
        self.assertEqual(result.nodes_created, 5)
        self.assertEqual(result.relationships_created, 7)
        self.assertEqual(len(result.errors), 0)
        self.assertEqual(len(result.warnings), 0)

    def test_graph_build_result_failure(self):
        """Test GraphBuildResult for failed operation"""
        result = GraphBuildResult(
            success=False,
            package_id="test_package",
            navigation_graph_id="",
            nodes_created=0,
            relationships_created=0,
            metrics=NavigationGraphMetrics(),
            errors=["Database connection failed", "Validation error"],
            warnings=[]
        )
        
        self.assertFalse(result.success)
        self.assertEqual(result.package_id, "test_package")
        self.assertEqual(result.navigation_graph_id, "")
        self.assertEqual(result.nodes_created, 0)
        self.assertEqual(result.relationships_created, 0)
        self.assertEqual(len(result.errors), 2)
        self.assertIn("Database connection failed", result.errors)


if __name__ == '__main__':
    unittest.main()