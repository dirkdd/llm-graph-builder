# Task 12: Navigation Graph Builder Implementation
# Builds Neo4j navigation graphs from hierarchical navigation structures

from typing import List, Dict, Any, Optional, Tuple, Set
from dataclasses import dataclass, asdict
from datetime import datetime
import logging
import uuid
import json

# Import existing entities and models
from src.entities.navigation_models import (
    EnhancedNavigationNode,
    HierarchicalChunk,
    ChunkRelationship,
    NavigationContext,
    DecisionTreeNode,
    RelationshipType,
    QualityRating
)
from src.graphDB_dataAccess import graphDBdataAccess
from src.navigation_extractor import NavigationExtractor
from src.semantic_chunker import SemanticChunker


@dataclass
class NavigationGraphMetrics:
    """Metrics for navigation graph quality and completeness"""
    total_nodes: int = 0
    total_relationships: int = 0
    navigation_depth: int = 0
    decision_trees_count: int = 0
    orphaned_nodes: int = 0
    completeness_score: float = 0.0
    accuracy_score: float = 0.0
    processing_time_ms: int = 0


@dataclass
class GraphBuildResult:
    """Result of navigation graph building operation"""
    success: bool
    package_id: str
    navigation_graph_id: str
    nodes_created: int
    relationships_created: int
    metrics: NavigationGraphMetrics
    errors: List[str] = None
    warnings: List[str] = None


class NavigationGraphBuilder:
    """
    Builds comprehensive Neo4j navigation graphs from hierarchical navigation structures.
    Integrates with existing package management and chunking systems.
    """
    
    def __init__(self, graph_db: graphDBdataAccess):
        """
        Initialize NavigationGraphBuilder with database connection
        
        Args:
            graph_db: Database access object for Neo4j operations
        """
        self.graph_db = graph_db
        self.logger = logging.getLogger(__name__)
        
        # Node type mappings for Neo4j
        self.neo4j_node_types = {
            "CHAPTER": "NavigationChapter",
            "SECTION": "NavigationSection", 
            "SUBSECTION": "NavigationSubsection",
            "DECISION_FLOW_SECTION": "DecisionFlowSection",
            "CONTENT_SECTION": "ContentSection",
            "MATRIX_SECTION": "MatrixSection",
            "ROOT": "NavigationRoot"
        }
        
        # Relationship type mappings for Neo4j
        self.neo4j_relationship_types = {
            RelationshipType.PARENT_CHILD: "CONTAINS",
            RelationshipType.SEQUENTIAL: "FOLLOWS",
            RelationshipType.REFERENCES: "REFERENCES",
            RelationshipType.ELABORATES: "ELABORATES",
            RelationshipType.DECISION_BRANCH: "BRANCHES_TO",
            RelationshipType.DECISION_OUTCOME: "RESULTS_IN",
            RelationshipType.CONDITIONAL: "CONDITIONAL_ON",
            RelationshipType.INTER_DOCUMENT: "RELATES_TO",
            RelationshipType.MATRIX_GUIDELINE: "IMPLEMENTS"
        }

    def build_navigation_graph(
        self,
        package_id: str,
        navigation_nodes: List[EnhancedNavigationNode],
        hierarchical_chunks: List[HierarchicalChunk],
        chunk_relationships: List[ChunkRelationship],
        package_config: Dict[str, Any] = None
    ) -> GraphBuildResult:
        """
        Build complete navigation graph in Neo4j from navigation structure
        
        Args:
            package_id: Document package identifier
            navigation_nodes: Enhanced navigation nodes from NavigationExtractor
            hierarchical_chunks: Hierarchical chunks from SemanticChunker
            chunk_relationships: Chunk relationships from ChunkRelationshipManager
            package_config: Package configuration for validation
            
        Returns:
            GraphBuildResult: Complete result with metrics and status
        """
        start_time = datetime.now()
        self.logger.info(f"Building navigation graph for package {package_id}")
        
        try:
            # Generate unique navigation graph ID
            navigation_graph_id = self._generate_navigation_graph_id(package_id)
            
            # Initialize result tracking
            result = GraphBuildResult(
                success=False,
                package_id=package_id,
                navigation_graph_id=navigation_graph_id,
                nodes_created=0,
                relationships_created=0,
                metrics=NavigationGraphMetrics(),
                errors=[],
                warnings=[]
            )
            
            # Step 1: Validate input data
            validation_result = self._validate_navigation_input(
                navigation_nodes, hierarchical_chunks, chunk_relationships
            )
            
            if not validation_result['is_valid']:
                result.errors.extend(validation_result['errors'])
                return result
            
            # Step 2: Create navigation graph root
            root_node_id = self._create_navigation_root(navigation_graph_id, package_id)
            
            # Step 3: Create navigation nodes in Neo4j
            node_creation_result = self._create_navigation_nodes(
                navigation_graph_id, navigation_nodes, root_node_id
            )
            
            if not node_creation_result['success']:
                result.errors.extend(node_creation_result['errors'])
                return result
            
            result.nodes_created += node_creation_result['nodes_created']
            
            # Step 4: Create hierarchical chunk nodes
            chunk_creation_result = self._create_chunk_nodes(
                navigation_graph_id, hierarchical_chunks
            )
            
            if not chunk_creation_result['success']:
                result.errors.extend(chunk_creation_result['errors'])
                return result
            
            result.nodes_created += chunk_creation_result['nodes_created']
            
            # Step 5: Create navigation relationships
            nav_rel_result = self._create_navigation_relationships(
                navigation_graph_id, navigation_nodes
            )
            
            if not nav_rel_result['success']:
                result.errors.extend(nav_rel_result['errors'])
                return result
            
            result.relationships_created += nav_rel_result['relationships_created']
            
            # Step 6: Create chunk relationships
            chunk_rel_result = self._create_chunk_relationships(
                navigation_graph_id, chunk_relationships
            )
            
            if not chunk_rel_result['success']:
                result.errors.extend(chunk_rel_result['errors'])
                return result
            
            result.relationships_created += chunk_rel_result['relationships_created']
            
            # Step 7: Link navigation nodes to chunks
            linking_result = self._link_navigation_to_chunks(
                navigation_graph_id, navigation_nodes, hierarchical_chunks
            )
            
            if not linking_result['success']:
                result.errors.extend(linking_result['errors'])
                return result
            
            result.relationships_created += linking_result['relationships_created']
            
            # Step 8: Calculate and store metrics
            metrics = self._calculate_graph_metrics(
                navigation_graph_id, navigation_nodes, hierarchical_chunks, chunk_relationships
            )
            
            processing_time = (datetime.now() - start_time).total_seconds() * 1000
            metrics.processing_time_ms = int(processing_time)
            
            result.metrics = metrics
            
            # Step 9: Store graph metadata
            self._store_graph_metadata(navigation_graph_id, package_id, metrics)
            
            # Step 10: Validate graph completeness
            completeness_result = self._validate_graph_completeness(navigation_graph_id)
            
            if completeness_result['warnings']:
                result.warnings.extend(completeness_result['warnings'])
            
            result.success = True
            self.logger.info(
                f"Navigation graph created successfully: {result.nodes_created} nodes, "
                f"{result.relationships_created} relationships in {processing_time:.2f}ms"
            )
            
            return result
            
        except Exception as e:
            self.logger.error(f"Failed to build navigation graph: {str(e)}")
            if 'result' in locals():
                result.errors.append(f"Graph building failed: {str(e)}")
                return result
            else:
                # Return minimal error result
                return GraphBuildResult(
                    success=False,
                    package_id=package_id,
                    navigation_graph_id="",
                    nodes_created=0,
                    relationships_created=0,
                    metrics=NavigationGraphMetrics(),
                    errors=[f"Graph building failed: {str(e)}"]
                )

    def enhance_navigation_nodes(
        self,
        navigation_graph_id: str,
        enhancement_config: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Enhance existing navigation nodes with additional metadata and relationships
        
        Args:
            navigation_graph_id: Navigation graph identifier
            enhancement_config: Configuration for enhancement operations
            
        Returns:
            Enhancement result with metrics
        """
        self.logger.info(f"Enhancing navigation nodes for graph {navigation_graph_id}")
        
        try:
            result = {
                'success': False,
                'enhancements_applied': 0,
                'errors': [],
                'warnings': []
            }
            
            # Step 1: Retrieve existing navigation nodes
            existing_nodes = self._retrieve_navigation_nodes(navigation_graph_id)
            
            if not existing_nodes:
                result['errors'].append("No navigation nodes found to enhance")
                return result
            
            # Step 2: Apply content-based enhancements
            content_enhancements = self._apply_content_enhancements(
                navigation_graph_id, existing_nodes, enhancement_config
            )
            
            result['enhancements_applied'] += content_enhancements['count']
            
            # Step 3: Apply relationship enhancements
            relationship_enhancements = self._apply_relationship_enhancements(
                navigation_graph_id, existing_nodes, enhancement_config
            )
            
            result['enhancements_applied'] += relationship_enhancements['count']
            
            # Step 4: Apply quality enhancements
            quality_enhancements = self._apply_quality_enhancements(
                navigation_graph_id, existing_nodes, enhancement_config
            )
            
            result['enhancements_applied'] += quality_enhancements['count']
            
            # Step 5: Update graph metadata
            self._update_enhancement_metadata(navigation_graph_id, result)
            
            result['success'] = True
            self.logger.info(
                f"Navigation enhancement completed: {result['enhancements_applied']} enhancements applied"
            )
            
            return result
            
        except Exception as e:
            self.logger.error(f"Failed to enhance navigation nodes: {str(e)}")
            return {
                'success': False,
                'enhancements_applied': 0,
                'errors': [f"Enhancement failed: {str(e)}"],
                'warnings': []
            }

    def query_navigation_path(
        self,
        navigation_graph_id: str,
        start_node_id: str,
        target_criteria: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Query navigation paths within the graph
        
        Args:
            navigation_graph_id: Navigation graph identifier  
            start_node_id: Starting node for path query
            target_criteria: Criteria for target nodes
            
        Returns:
            Navigation paths and related information
        """
        try:
            self.logger.info(f"Querying navigation path from {start_node_id}")
            
            # Build Cypher query based on criteria
            cypher_query = self._build_path_query(start_node_id, target_criteria)
            
            # Execute query
            query_result = self.graph_db.graph.query(cypher_query)
            
            # Process and format results
            paths = self._process_path_results(query_result)
            
            return {
                'success': True,
                'paths_found': len(paths),
                'paths': paths,
                'query_time_ms': 0  # Would track actual query time
            }
            
        except Exception as e:
            self.logger.error(f"Navigation path query failed: {str(e)}")
            return {
                'success': False,
                'paths_found': 0,
                'paths': [],
                'error': str(e)
            }

    def _generate_navigation_graph_id(self, package_id: str) -> str:
        """Generate unique navigation graph identifier"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        unique_id = str(uuid.uuid4())[:8]
        return f"navgraph_{package_id}_{timestamp}_{unique_id}"

    def _validate_navigation_input(
        self,
        navigation_nodes: List[EnhancedNavigationNode],
        hierarchical_chunks: List[HierarchicalChunk],
        chunk_relationships: List[ChunkRelationship]
    ) -> Dict[str, Any]:
        """Validate input data for navigation graph building"""
        errors = []
        warnings = []
        
        # Check for empty inputs
        if not navigation_nodes:
            errors.append("No navigation nodes provided")
        
        if not hierarchical_chunks:
            warnings.append("No hierarchical chunks provided")
        
        # Validate navigation node structure
        node_ids = set()
        for node in navigation_nodes:
            if not node.enhanced_node_id:
                errors.append(f"Navigation node missing ID: {node.title}")
            
            if node.enhanced_node_id in node_ids:
                errors.append(f"Duplicate navigation node ID: {node.enhanced_node_id}")
            
            node_ids.add(node.enhanced_node_id)
        
        # Validate chunk structure
        chunk_ids = set()
        for chunk in hierarchical_chunks:
            if not chunk.chunk_id:
                errors.append(f"Chunk missing ID: {chunk.content[:50]}...")
            
            if chunk.chunk_id in chunk_ids:
                errors.append(f"Duplicate chunk ID: {chunk.chunk_id}")
            
            chunk_ids.add(chunk.chunk_id)
        
        # Validate relationships reference existing entities
        for relationship in chunk_relationships:
            if relationship.source_chunk_id not in chunk_ids:
                errors.append(f"Relationship references unknown source chunk: {relationship.source_chunk_id}")
            
            if relationship.target_chunk_id not in chunk_ids:
                errors.append(f"Relationship references unknown target chunk: {relationship.target_chunk_id}")
        
        return {
            'is_valid': len(errors) == 0,
            'errors': errors,
            'warnings': warnings
        }

    def _create_navigation_root(self, navigation_graph_id: str, package_id: str) -> str:
        """Create root node for navigation graph"""
        root_node_id = f"{navigation_graph_id}_root"
        
        cypher_query = """
        CREATE (root:NavigationRoot {
            node_id: $root_id,
            navigation_graph_id: $graph_id,
            package_id: $package_id,
            created_at: datetime(),
            node_type: 'ROOT',
            title: 'Navigation Root'
        })
        RETURN root.node_id AS root_id
        """
        
        result = self.graph_db.graph.query(
            cypher_query,
            {
                'root_id': root_node_id,
                'graph_id': navigation_graph_id,
                'package_id': package_id
            }
        )
        
        return root_node_id

    def _create_navigation_nodes(
        self,
        navigation_graph_id: str,
        navigation_nodes: List[EnhancedNavigationNode],
        root_node_id: str
    ) -> Dict[str, Any]:
        """Create navigation nodes in Neo4j"""
        try:
            nodes_created = 0
            errors = []
            
            for node in navigation_nodes:
                try:
                    # Map node type to Neo4j label
                    neo4j_label = self.neo4j_node_types.get(node.node_type, "NavigationNode")
                    
                    # Create node with comprehensive properties
                    cypher_query = f"""
                    CREATE (n:{neo4j_label} {{
                        node_id: $node_id,
                        navigation_graph_id: $graph_id,
                        enhanced_node_id: $enhanced_id,
                        node_type: $node_type,
                        title: $title,
                        content: $content,
                        hierarchy_level: $hierarchy_level,
                        navigation_path: $nav_path,
                        parent_node_id: $parent_id,
                        line_number: $line_number,
                        confidence_score: $confidence,
                        quality_rating: $quality,
                        created_at: datetime(),
                        updated_at: datetime()
                    }})
                    RETURN n.node_id AS created_id
                    """
                    
                    result = self.graph_db.graph.query(
                        cypher_query,
                        {
                            'node_id': node.enhanced_node_id,
                            'graph_id': navigation_graph_id,
                            'enhanced_id': node.enhanced_node_id,
                            'node_type': node.node_type,
                            'title': node.title,
                            'content': node.content,
                            'hierarchy_level': node.hierarchy_level,
                            'nav_path': ' > '.join(node.navigation_path),
                            'parent_id': node.parent_id,
                            'line_number': node.line_number,
                            'confidence': node.confidence_score,
                            'quality': node.quality_assessment.value if node.quality_assessment else 'GOOD'
                        }
                    )
                    
                    if result:
                        nodes_created += 1
                        
                except Exception as e:
                    errors.append(f"Failed to create node {node.enhanced_node_id}: {str(e)}")
            
            return {
                'success': len(errors) == 0,
                'nodes_created': nodes_created,
                'errors': errors
            }
            
        except Exception as e:
            return {
                'success': False,
                'nodes_created': 0,
                'errors': [f"Navigation node creation failed: {str(e)}"]
            }

    def _create_chunk_nodes(
        self,
        navigation_graph_id: str,
        hierarchical_chunks: List[HierarchicalChunk]
    ) -> Dict[str, Any]:
        """Create hierarchical chunk nodes in Neo4j"""
        try:
            nodes_created = 0
            errors = []
            
            for chunk in hierarchical_chunks:
                try:
                    # Create chunk node with hierarchical properties
                    cypher_query = """
                    CREATE (c:HierarchicalChunk {
                        chunk_id: $chunk_id,
                        navigation_graph_id: $graph_id,
                        chunk_type: $chunk_type,
                        content: $content,
                        content_summary: $summary,
                        navigation_context: $nav_context,
                        hierarchy_level: $hierarchy_level,
                        parent_chunk_id: $parent_id,
                        decision_logic: $decision_logic,
                        entities_detected: $entities,
                        quality_score: $quality,
                        token_count: $tokens,
                        created_at: datetime(),
                        updated_at: datetime()
                    })
                    RETURN c.chunk_id AS created_id
                    """
                    
                    result = self.graph_db.graph.query(
                        cypher_query,
                        {
                            'chunk_id': chunk.chunk_id,
                            'graph_id': navigation_graph_id,
                            'chunk_type': chunk.chunk_type.value,
                            'content': chunk.content,
                            'summary': chunk.content_summary,
                            'nav_context': ' > '.join(chunk.navigation_context.navigation_path),
                            'hierarchy_level': chunk.navigation_context.hierarchy_level,
                            'parent_id': chunk.parent_chunk_id,
                            'decision_logic': json.dumps(chunk.decision_logic) if chunk.decision_logic else None,
                            'entities': json.dumps([ent.dict() for ent in chunk.entities_detected]),
                            'quality': chunk.quality_score,
                            'tokens': chunk.token_count
                        }
                    )
                    
                    if result:
                        nodes_created += 1
                        
                except Exception as e:
                    errors.append(f"Failed to create chunk {chunk.chunk_id}: {str(e)}")
            
            return {
                'success': len(errors) == 0,
                'nodes_created': nodes_created,
                'errors': errors
            }
            
        except Exception as e:
            return {
                'success': False,
                'nodes_created': 0,
                'errors': [f"Chunk node creation failed: {str(e)}"]
            }

    def _create_navigation_relationships(
        self,
        navigation_graph_id: str,
        navigation_nodes: List[EnhancedNavigationNode]
    ) -> Dict[str, Any]:
        """Create hierarchical relationships between navigation nodes"""
        try:
            relationships_created = 0
            errors = []
            
            # Create parent-child relationships
            for node in navigation_nodes:
                if node.parent_id:
                    try:
                        cypher_query = """
                        MATCH (parent:NavigationRoot {node_id: $parent_id, navigation_graph_id: $graph_id})
                        MATCH (child {node_id: $child_id, navigation_graph_id: $graph_id})
                        CREATE (parent)-[r:CONTAINS {
                            relationship_type: 'PARENT_CHILD',
                            hierarchy_level: $hierarchy_level,
                            created_at: datetime()
                        }]->(child)
                        RETURN r
                        """
                        
                        # First try to find parent as NavigationRoot
                        result = self.graph_db.graph.query(
                            cypher_query,
                            {
                                'parent_id': node.parent_id,
                                'child_id': node.enhanced_node_id,
                                'graph_id': navigation_graph_id,
                                'hierarchy_level': node.hierarchy_level
                            }
                        )
                        
                        # If no result, try finding parent as any navigation node
                        if not result:
                            cypher_query = """
                            MATCH (parent {node_id: $parent_id, navigation_graph_id: $graph_id})
                            MATCH (child {node_id: $child_id, navigation_graph_id: $graph_id})
                            CREATE (parent)-[r:CONTAINS {
                                relationship_type: 'PARENT_CHILD',
                                hierarchy_level: $hierarchy_level,
                                created_at: datetime()
                            }]->(child)
                            RETURN r
                            """
                            
                            result = self.graph_db.graph.query(
                                cypher_query,
                                {
                                    'parent_id': node.parent_id,
                                    'child_id': node.enhanced_node_id,
                                    'graph_id': navigation_graph_id,
                                    'hierarchy_level': node.hierarchy_level
                                }
                            )
                        
                        if result:
                            relationships_created += 1
                            
                    except Exception as e:
                        errors.append(f"Failed to create parent-child relationship for {node.enhanced_node_id}: {str(e)}")
            
            # Create sequential relationships between sibling nodes
            sequential_relationships = self._create_sequential_relationships(navigation_graph_id, navigation_nodes)
            relationships_created += sequential_relationships['count']
            errors.extend(sequential_relationships['errors'])
            
            return {
                'success': len(errors) == 0,
                'relationships_created': relationships_created,
                'errors': errors
            }
            
        except Exception as e:
            return {
                'success': False,
                'relationships_created': 0,
                'errors': [f"Navigation relationship creation failed: {str(e)}"]
            }

    def _create_chunk_relationships(
        self,
        navigation_graph_id: str,
        chunk_relationships: List[ChunkRelationship]
    ) -> Dict[str, Any]:
        """Create relationships between hierarchical chunks"""
        try:
            relationships_created = 0
            errors = []
            
            for relationship in chunk_relationships:
                try:
                    # Map relationship type to Neo4j relationship
                    neo4j_rel_type = self.neo4j_relationship_types.get(
                        relationship.relationship_type, "RELATES_TO"
                    )
                    
                    cypher_query = f"""
                    MATCH (source:HierarchicalChunk {{chunk_id: $source_id, navigation_graph_id: $graph_id}})
                    MATCH (target:HierarchicalChunk {{chunk_id: $target_id, navigation_graph_id: $graph_id}})
                    CREATE (source)-[r:{neo4j_rel_type} {{
                        relationship_type: $rel_type,
                        strength: $strength,
                        confidence: $confidence,
                        evidence: $evidence,
                        created_at: datetime()
                    }}]->(target)
                    RETURN r
                    """
                    
                    result = self.graph_db.graph.query(
                        cypher_query,
                        {
                            'source_id': relationship.source_chunk_id,
                            'target_id': relationship.target_chunk_id,
                            'graph_id': navigation_graph_id,
                            'rel_type': relationship.relationship_type.value,
                            'strength': relationship.strength,
                            'confidence': relationship.confidence,
                            'evidence': json.dumps(relationship.evidence) if relationship.evidence else None
                        }
                    )
                    
                    if result:
                        relationships_created += 1
                        
                except Exception as e:
                    errors.append(f"Failed to create chunk relationship {relationship.source_chunk_id} -> {relationship.target_chunk_id}: {str(e)}")
            
            return {
                'success': len(errors) == 0,
                'relationships_created': relationships_created,
                'errors': errors
            }
            
        except Exception as e:
            return {
                'success': False,
                'relationships_created': 0,
                'errors': [f"Chunk relationship creation failed: {str(e)}"]
            }

    def _link_navigation_to_chunks(
        self,
        navigation_graph_id: str,
        navigation_nodes: List[EnhancedNavigationNode],
        hierarchical_chunks: List[HierarchicalChunk]
    ) -> Dict[str, Any]:
        """Link navigation nodes to their corresponding chunks"""
        try:
            relationships_created = 0
            errors = []
            
            # Create mapping of navigation paths to chunks
            chunk_nav_mapping = {}
            for chunk in hierarchical_chunks:
                nav_path = ' > '.join(chunk.navigation_context.navigation_path)
                if nav_path not in chunk_nav_mapping:
                    chunk_nav_mapping[nav_path] = []
                chunk_nav_mapping[nav_path].append(chunk)
            
            # Link navigation nodes to chunks based on navigation path
            for node in navigation_nodes:
                node_nav_path = ' > '.join(node.navigation_path)
                
                # Find chunks that belong to this navigation node
                matching_chunks = chunk_nav_mapping.get(node_nav_path, [])
                
                for chunk in matching_chunks:
                    try:
                        cypher_query = """
                        MATCH (nav {node_id: $nav_id, navigation_graph_id: $graph_id})
                        MATCH (chunk:HierarchicalChunk {chunk_id: $chunk_id, navigation_graph_id: $graph_id})
                        CREATE (nav)-[r:CONTAINS_CHUNK {
                            relationship_type: 'NAVIGATION_TO_CHUNK',
                            navigation_path: $nav_path,
                            created_at: datetime()
                        }]->(chunk)
                        RETURN r
                        """
                        
                        result = self.graph_db.graph.query(
                            cypher_query,
                            {
                                'nav_id': node.enhanced_node_id,
                                'chunk_id': chunk.chunk_id,
                                'graph_id': navigation_graph_id,
                                'nav_path': node_nav_path
                            }
                        )
                        
                        if result:
                            relationships_created += 1
                            
                    except Exception as e:
                        errors.append(f"Failed to link navigation {node.enhanced_node_id} to chunk {chunk.chunk_id}: {str(e)}")
            
            return {
                'success': len(errors) == 0,
                'relationships_created': relationships_created,
                'errors': errors
            }
            
        except Exception as e:
            return {
                'success': False,
                'relationships_created': 0,
                'errors': [f"Navigation-to-chunk linking failed: {str(e)}"]
            }

    def _calculate_graph_metrics(
        self,
        navigation_graph_id: str,
        navigation_nodes: List[EnhancedNavigationNode],
        hierarchical_chunks: List[HierarchicalChunk],
        chunk_relationships: List[ChunkRelationship]
    ) -> NavigationGraphMetrics:
        """Calculate comprehensive metrics for the navigation graph"""
        try:
            # Count total nodes and relationships in Neo4j
            count_query = """
            MATCH (n {navigation_graph_id: $graph_id})
            OPTIONAL MATCH (n)-[r]->()
            RETURN count(DISTINCT n) AS total_nodes, count(r) AS total_relationships
            """
            
            result = self.graph_db.graph.query(count_query, {'graph_id': navigation_graph_id})
            
            if result:
                db_counts = result[0]
                total_nodes = db_counts['total_nodes']
                total_relationships = db_counts['total_relationships']
            else:
                total_nodes = len(navigation_nodes) + len(hierarchical_chunks)
                total_relationships = len(chunk_relationships)
            
            # Calculate navigation depth
            max_depth = max([node.hierarchy_level for node in navigation_nodes], default=0)
            
            # Count decision trees
            decision_nodes = [node for node in navigation_nodes if node.node_type == "DECISION_FLOW_SECTION"]
            decision_trees_count = len(decision_nodes)
            
            # Calculate orphaned nodes (nodes without parent relationships)
            orphaned_query = """
            MATCH (n {navigation_graph_id: $graph_id})
            WHERE NOT (n)<-[:CONTAINS]-()
            AND NOT n:NavigationRoot
            RETURN count(n) AS orphaned_count
            """
            
            orphaned_result = self.graph_db.graph.query(orphaned_query, {'graph_id': navigation_graph_id})
            orphaned_nodes = orphaned_result[0]['orphaned_count'] if orphaned_result else 0
            
            # Calculate completeness score
            expected_nodes = len(navigation_nodes) + len(hierarchical_chunks)
            completeness_score = min(1.0, total_nodes / max(expected_nodes, 1))
            
            # Calculate accuracy score based on successful relationships
            expected_relationships = len(chunk_relationships) + len(navigation_nodes)  # Approximate
            accuracy_score = min(1.0, total_relationships / max(expected_relationships, 1))
            
            return NavigationGraphMetrics(
                total_nodes=total_nodes,
                total_relationships=total_relationships,
                navigation_depth=max_depth,
                decision_trees_count=decision_trees_count,
                orphaned_nodes=orphaned_nodes,
                completeness_score=completeness_score,
                accuracy_score=accuracy_score,
                processing_time_ms=0  # Will be set by caller
            )
            
        except Exception as e:
            self.logger.error(f"Failed to calculate graph metrics: {str(e)}")
            return NavigationGraphMetrics()

    def _store_graph_metadata(
        self,
        navigation_graph_id: str,
        package_id: str,
        metrics: NavigationGraphMetrics
    ) -> None:
        """Store graph metadata in Neo4j"""
        try:
            cypher_query = """
            CREATE (meta:NavigationGraphMetadata {
                navigation_graph_id: $graph_id,
                package_id: $package_id,
                total_nodes: $total_nodes,
                total_relationships: $total_relationships,
                navigation_depth: $nav_depth,
                decision_trees_count: $decision_count,
                orphaned_nodes: $orphaned,
                completeness_score: $completeness,
                accuracy_score: $accuracy,
                processing_time_ms: $processing_time,
                created_at: datetime(),
                updated_at: datetime()
            })
            RETURN meta.navigation_graph_id AS created_id
            """
            
            self.graph_db.graph.query(
                cypher_query,
                {
                    'graph_id': navigation_graph_id,
                    'package_id': package_id,
                    'total_nodes': metrics.total_nodes,
                    'total_relationships': metrics.total_relationships,
                    'nav_depth': metrics.navigation_depth,
                    'decision_count': metrics.decision_trees_count,
                    'orphaned': metrics.orphaned_nodes,
                    'completeness': metrics.completeness_score,
                    'accuracy': metrics.accuracy_score,
                    'processing_time': metrics.processing_time_ms
                }
            )
            
        except Exception as e:
            self.logger.error(f"Failed to store graph metadata: {str(e)}")

    def _validate_graph_completeness(self, navigation_graph_id: str) -> Dict[str, Any]:
        """Validate the completeness of the created navigation graph"""
        warnings = []
        
        try:
            # Check for orphaned nodes
            orphaned_query = """
            MATCH (n {navigation_graph_id: $graph_id})
            WHERE NOT (n)<-[:CONTAINS]-()
            AND NOT n:NavigationRoot
            RETURN n.node_id AS orphaned_id, labels(n) AS node_labels
            """
            
            orphaned_result = self.graph_db.graph.query(orphaned_query, {'graph_id': navigation_graph_id})
            
            if orphaned_result:
                for orphaned in orphaned_result:
                    warnings.append(f"Orphaned node detected: {orphaned['orphaned_id']} ({orphaned['node_labels']})")
            
            # Check for missing relationships
            isolated_query = """
            MATCH (n {navigation_graph_id: $graph_id})
            WHERE NOT (n)-[]-()
            RETURN n.node_id AS isolated_id, labels(n) AS node_labels
            """
            
            isolated_result = self.graph_db.graph.query(isolated_query, {'graph_id': navigation_graph_id})
            
            if isolated_result:
                for isolated in isolated_result:
                    warnings.append(f"Isolated node detected: {isolated['isolated_id']} ({isolated['node_labels']})")
            
            return {
                'is_complete': len(warnings) == 0,
                'warnings': warnings
            }
            
        except Exception as e:
            self.logger.error(f"Graph validation failed: {str(e)}")
            return {
                'is_complete': False,
                'warnings': [f"Validation failed: {str(e)}"]
            }

    # Helper methods for enhancement and querying
    def _retrieve_navigation_nodes(self, navigation_graph_id: str) -> List[Dict[str, Any]]:
        """Retrieve existing navigation nodes from graph"""
        # Implementation for node retrieval
        pass

    def _apply_content_enhancements(
        self, navigation_graph_id: str, nodes: List[Dict[str, Any]], config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Apply content-based enhancements to nodes"""
        # Implementation for content enhancements
        return {'count': 0}

    def _apply_relationship_enhancements(
        self, navigation_graph_id: str, nodes: List[Dict[str, Any]], config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Apply relationship enhancements"""
        # Implementation for relationship enhancements
        return {'count': 0}

    def _apply_quality_enhancements(
        self, navigation_graph_id: str, nodes: List[Dict[str, Any]], config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Apply quality-based enhancements"""
        # Implementation for quality enhancements
        return {'count': 0}

    def _update_enhancement_metadata(self, navigation_graph_id: str, result: Dict[str, Any]) -> None:
        """Update metadata after enhancements"""
        # Implementation for metadata updates
        pass

    def _build_path_query(self, start_node_id: str, criteria: Dict[str, Any]) -> str:
        """Build Cypher query for path traversal"""
        # Implementation for path query building
        return ""

    def _process_path_results(self, query_result: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Process path query results"""
        # Implementation for path result processing
        return []

    def _create_sequential_relationships(
        self, navigation_graph_id: str, navigation_nodes: List[EnhancedNavigationNode]
    ) -> Dict[str, Any]:
        """Create sequential relationships between sibling nodes"""
        # Implementation for sequential relationship creation
        return {'count': 0, 'errors': []}