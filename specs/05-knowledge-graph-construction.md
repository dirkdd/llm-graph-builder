# Knowledge Graph Construction Technical Specification

## Overview

The knowledge graph construction system transforms LLM-extracted entities and relationships into a structured Neo4j graph database. It implements sophisticated deduplication, relationship inference, community detection, and schema management to create a coherent, queryable knowledge representation.

## Architecture

### Core Components

- **Graph Storage Engine**: Neo4j database with optimized schemas
- **Entity Deduplication System**: Similarity-based entity merging
- **Relationship Manager**: Entity-chunk and inter-entity relationships
- **Community Detection**: Hierarchical clustering using Leiden algorithm
- **Schema Management**: Dynamic schema evolution and validation
- **Post-Processing Pipeline**: Graph enhancement and optimization

### Data Flow

```
Graph Documents → Entity Storage → Relationship Creation → Deduplication → Community Detection → Schema Optimization
```

## Neo4j Data Model

### Core Node Types

**Document Nodes**:
```cypher
CREATE (d:Document {
    fileName: string,
    fileType: string,
    fileSize: integer,
    fileSource: string,
    status: string,
    model: string,
    created_at: datetime,
    updated_at: datetime,
    processing_time: duration,
    total_chunks: integer,
    processed_chunk: integer,
    node_count: integer,
    relationship_count: integer,
    chunkNodeCount: integer,
    chunkRelCount: integer,
    entityNodeCount: integer,
    entityEntityRelCount: integer,
    communityNodeCount: integer,
    communityRelCount: integer
})
```

**Chunk Nodes**:
```cypher
CREATE (c:Chunk {
    id: string,           // SHA1 hash of content
    text: string,         // Chunk content
    position: integer,    // Sequential position in document
    length: integer,      // Character length
    content_offset: integer, // Character offset in document
    embedding: float[]    // Vector embedding
})
```

**Entity Nodes**:
```cypher
CREATE (e:__Entity__:EntityType {
    id: string,          // Entity identifier
    description: string, // LLM-generated description
    embedding: float[]   // Optional entity embedding
})
```

**Community Nodes**:
```cypher
CREATE (c:__Community__ {
    id: string,          // Community identifier
    level: integer,      // Hierarchy level (0=base, 1=intermediate, 2=top)
    size: integer,       // Number of member entities
    weight: float,       // Community coherence score
    title: string,       // Generated community title
    summary: string,     // LLM-generated community summary
    rank: float          // Community importance ranking
})
```

### Relationship Types

**Structural Relationships**:
- `PART_OF`: Chunk → Document
- `FIRST_CHUNK`: Document → Chunk (first chunk)
- `NEXT_CHUNK`: Chunk → Chunk (sequential order)
- `HAS_ENTITY`: Chunk → Entity

**Semantic Relationships**:
- `SIMILAR`: Entity ↔ Entity (embedding similarity)
- Domain-specific relationships extracted by LLMs

**Community Relationships**:
- `IN_COMMUNITY`: Entity → Community
- `PARENT_COMMUNITY`: Community → Community (hierarchy)

## Entity Storage and Deduplication

### Entity Creation Pipeline

**Location**: `backend/src/shared/common_fn.py:95-109`

**Implementation**:
```python
def save_graphDocuments_in_neo4j(graph, graph_document_list, max_retries=3, delay=1):
    """Save entities with automatic deduplication"""
    retries = 0
    while retries < max_retries:
        try:
            # Neo4j's add_graph_documents provides built-in deduplication
            graph.add_graph_documents(
                graph_document_list,
                baseEntityLabel=True,    # Add __Entity__ base label
                include_source=True      # Create source relationships
            )
            return
            
        except TransientError as e:
            if "DeadlockDetected" in str(e):
                retries += 1
                logging.info(f"Deadlock detected. Retrying {retries}/{max_retries}")
                time.sleep(delay)
                delay *= 2  # Exponential backoff
            else:
                raise
                
    raise LLMGraphBuilderException(f"Failed after {max_retries} retries")
```

### Advanced Deduplication System

**Location**: `backend/src/post_processing.py`

**Similarity-Based Deduplication**:
```python
def get_duplicate_nodes_query():
    """Cypher query to identify potential duplicate entities"""
    return """
    MATCH (e1:__Entity__)
    WHERE e1.embedding IS NOT NULL
    
    CALL db.index.vector.queryNodes('entity_embedding_index', 5, e1.embedding)
    YIELD node AS e2, score
    
    WHERE e1 <> e2 
    AND score >= $similarity_threshold
    AND e1.id < e2.id  // Prevent duplicate pairs
    
    RETURN e1.id AS entity1, e2.id AS entity2, score,
           labels(e1) AS labels1, labels(e2) AS labels2
    ORDER BY score DESC
    """
```

**Merge Duplicate Entities**:
```python
def merge_duplicate_nodes(graph, duplicate_pairs):
    """Merge identified duplicate entities"""
    for pair in duplicate_pairs:
        merge_query = """
        MATCH (e1:__Entity__ {id: $entity1_id})
        MATCH (e2:__Entity__ {id: $entity2_id})
        
        // Merge properties
        SET e1 += e2
        
        // Transfer all relationships
        MATCH (e2)-[r]->(target)
        WHERE NOT exists((e1)-[r]->(target))
        CREATE (e1)-[new_r:${rel_type}]->(target)
        SET new_r = r
        
        MATCH (source)-[r]->(e2)  
        WHERE NOT exists((source)-[r]->(e1))
        CREATE (source)-[new_r:${rel_type}]->(e1)
        SET new_r = r
        
        // Delete duplicate entity
        DETACH DELETE e2
        """
        
        execute_graph_query(graph, merge_query, {
            'entity1_id': pair['entity1'],
            'entity2_id': pair['entity2']
        })
```

### Entity-Chunk Relationship Creation

**Location**: `backend/src/make_relationships.py:17-38`

**Implementation**:
```python
def merge_relationship_between_chunk_and_entites(graph, graph_documents_chunk_chunk_Id):
    """Create HAS_ENTITY relationships between chunks and extracted entities"""
    batch_data = []
    
    for graph_doc_chunk_id in graph_documents_chunk_chunk_Id:
        graph_doc = graph_doc_chunk_id['graph_doc']
        chunk_id = graph_doc_chunk_id['chunk_id']
        
        # Process each entity in the graph document
        for node in graph_doc.nodes:
            query_data = {
                'chunk_id': chunk_id,
                'node_type': node.type,
                'node_id': node.id
            }
            batch_data.append(query_data)
    
    # Batch create relationships
    merge_query = """
    UNWIND $data AS row
    MATCH (c:Chunk {id: row.chunk_id})
    MATCH (e:__Entity__ {id: row.node_id})
    WHERE row.node_type IN labels(e)
    MERGE (c)-[:HAS_ENTITY]->(e)
    """
    
    execute_graph_query(graph, merge_query, params={"data": batch_data})
```

## Community Detection System

### Leiden Algorithm Implementation

**Location**: `backend/src/communities.py`

**Graph Data Science Integration**:
```python
def create_communities(uri, username, password, database):
    """Create hierarchical communities using Leiden algorithm"""
    
    # Initialize GDS client
    gds_client = GraphDataScience(uri, auth=(username, password), database=database)
    
    # Project graph for community detection
    graph_project = "communities"
    
    try:
        # Drop existing projection
        gds_client.graph.drop(graph_project)
    except:
        pass  # Ignore if doesn't exist
    
    # Create new graph projection
    graph, result = gds_client.graph.project(
        graph_project,
        ["__Entity__", "Document", "Chunk"],
        {
            "SIMILAR": {"orientation": "UNDIRECTED"},
            "HAS_ENTITY": {"orientation": "UNDIRECTED"},
            "PART_OF": {"orientation": "UNDIRECTED"}
        },
        nodeProperties=["embedding"],
        relationshipProperties=["score"]
    )
    
    # Run Leiden community detection
    gds_client.leiden.write(
        graph_project,
        writeProperty="communities",
        includeIntermediateCommunities=True,
        relationshipWeightProperty="score",
        maxLevels=3,        # Create 3-level hierarchy
        minCommunitySize=1,
        randomSeed=42       # Reproducible results
    )
```

### Community Hierarchy Creation

**Three-Level Community Structure**:
```python
def create_community_hierarchy(gds_client, graph_project):
    """Create hierarchical community structure"""
    
    # Level 0: Base communities (most granular)
    base_communities_query = """
    MATCH (e:__Entity__)
    WHERE e.communities IS NOT NULL AND size(e.communities) >= 1
    WITH e.communities[0] AS communityId, collect(e) AS entities
    WHERE size(entities) > 1
    
    CREATE (c:__Community__ {
        id: 'community_0_' + toString(communityId),
        level: 0,
        size: size(entities),
        weight: 1.0
    })
    
    WITH c, entities
    UNWIND entities AS entity
    MERGE (entity)-[:IN_COMMUNITY]->(c)
    """
    
    # Level 1: Intermediate communities
    intermediate_communities_query = """
    MATCH (e:__Entity__)
    WHERE e.communities IS NOT NULL AND size(e.communities) >= 2
    WITH e.communities[1] AS communityId, collect(e) AS entities
    WHERE size(entities) > 1
    
    CREATE (c:__Community__ {
        id: 'community_1_' + toString(communityId),
        level: 1,
        size: size(entities),
        weight: 1.0
    })
    
    WITH c, entities
    UNWIND entities AS entity
    MERGE (entity)-[:IN_COMMUNITY]->(c)
    """
    
    # Level 2: Top-level communities  
    top_communities_query = """
    MATCH (e:__Entity__)
    WHERE e.communities IS NOT NULL AND size(e.communities) >= 3
    WITH e.communities[2] AS communityId, collect(e) AS entities
    WHERE size(entities) > 1
    
    CREATE (c:__Community__ {
        id: 'community_2_' + toString(communityId),
        level: 2,
        size: size(entities),
        weight: 1.0
    })
    
    WITH c, entities
    UNWIND entities AS entity
    MERGE (entity)-[:IN_COMMUNITY]->(c)
    """
```

### Community Ranking System

**Ranking Algorithm**:
```python
def calculate_community_ranks():
    """Calculate community importance rankings"""
    ranking_query = """
    MATCH (c:__Community__)<-[:IN_COMMUNITY]-(e:__Entity__)
    
    // Count distinct documents contributing to community
    OPTIONAL MATCH (e)<-[:HAS_ENTITY]-(chunk:Chunk)-[:PART_OF]->(d:Document)
    WITH c, e, collect(DISTINCT d) AS documents
    
    // Calculate rank based on document diversity and entity count
    WITH c, 
         count(e) AS entity_count,
         size(documents) AS document_count,
         sum(size(documents)) AS total_weight
         
    SET c.rank = (document_count * 2.0 + entity_count * 1.0) / (c.level + 1.0)
    
    RETURN c.id, c.rank, entity_count, document_count
    ORDER BY c.rank DESC
    """
    
    return execute_graph_query(graph, ranking_query)
```

## Similarity Graph Construction

### Vector Similarity Relationships

**Location**: `backend/src/graphDB_dataAccess.py:631-651`

**KNN Graph Creation**:
```python
def update_KNN_graph(self):
    """Create SIMILAR relationships based on embedding similarity"""
    
    # Configuration from environment
    text_distance = int(os.environ.get('DUPLICATE_TEXT_DISTANCE', 3))
    score_value = float(os.environ.get('DUPLICATE_SCORE_VALUE', 0.97))
    
    knn_query = """
    MATCH (c:Chunk)
    WHERE c.embedding IS NOT NULL
    
    CALL db.index.vector.queryNodes('vector', $k, c.embedding)
    YIELD node AS similar_chunk, score
    
    WHERE c <> similar_chunk 
    AND score >= $similarity_threshold
    AND NOT exists((c)-[:SIMILAR]-(similar_chunk))
    
    // Verify text similarity for additional validation
    WITH c, similar_chunk, score
    WHERE apoc.text.distance(c.text, similar_chunk.text) <= $text_distance
    
    MERGE (c)-[r:SIMILAR]-(similar_chunk)
    SET r.score = score
    """
    
    params = {
        'k': 5,  # Top 5 similar chunks
        'similarity_threshold': score_value,
        'text_distance': text_distance
    }
    
    execute_graph_query(self.graph, knn_query, params)
```

### Entity Embedding Similarities

**Entity-Level Similarity Graph**:
```python
def create_entity_embedding(graph):
    """Generate embeddings for entities and create similarity relationships"""
    
    # Generate entity embeddings from their descriptions
    entity_embedding_query = """
    MATCH (e:__Entity__)
    WHERE e.description IS NOT NULL
    
    // Generate embedding using OpenAI
    CALL apoc.load.json($openai_endpoint, {
        method: 'POST',
        headers: {Authorization: 'Bearer ' + $api_key},
        payload: {
            input: e.description,
            model: 'text-embedding-ada-002'
        }
    }) YIELD value
    
    SET e.embedding = value.data[0].embedding
    """
    
    # Create entity similarity relationships
    similarity_query = """
    MATCH (e1:__Entity__)
    WHERE e1.embedding IS NOT NULL
    
    CALL db.index.vector.queryNodes('entity_embedding_index', 3, e1.embedding)
    YIELD node AS e2, score
    
    WHERE e1 <> e2 
    AND score >= 0.85
    AND NOT exists((e1)-[:SIMILAR_TO]-(e2))
    
    MERGE (e1)-[r:SIMILAR_TO]-(e2)
    SET r.similarity_score = score
    """
```

## Schema Management

### Dynamic Schema Evolution

**Schema Discovery**:
```python
def get_labels_and_relationtypes(uri, userName, password, database):
    """Extract current graph schema"""
    excluded_labels = {'Document', 'Chunk', '_Bloom_Perspective_', '__Community__', '__Entity__', 'Session', 'Message'}
    excluded_relationships = {
        'NEXT_CHUNK', '_Bloom_Perspective_', 'FIRST_CHUNK',
        'SIMILAR', 'IN_COMMUNITY', 'PARENT_COMMUNITY', 'NEXT', 'LAST_MESSAGE'
    }
    
    driver = get_graphDB_driver(uri, userName, password, database)
    triples = set()
    
    with driver.session(database=database) as session:
        result = session.run("""
            MATCH (n)-[r]->(m)
            RETURN DISTINCT labels(n) AS fromLabels, type(r) AS relType, labels(m) AS toLabels
        """)
        
        for record in result:
            from_labels = record["fromLabels"]
            to_labels = record["toLabels"]
            rel_type = record["relType"]
            
            # Filter system labels and relationships
            from_label = next((lbl for lbl in from_labels if lbl not in excluded_labels), None)
            to_label = next((lbl for lbl in to_labels if lbl not in excluded_labels), None)
            
            if from_label and to_label and rel_type not in excluded_relationships:
                triples.add(f"{from_label}-{rel_type}->{to_label}")
    
    return {"triplets": list(triples)}
```

### Schema Consolidation

**Location**: `backend/src/post_processing.py`

**Schema Cleanup and Optimization**:
```python
def graph_schema_consolidation(graph):
    """Consolidate and optimize graph schema"""
    
    # 1. Normalize entity type names
    normalize_labels_query = """
    MATCH (e:__Entity__)
    WHERE size(labels(e)) > 2  // Has specific type beyond __Entity__
    
    WITH e, [label IN labels(e) WHERE label <> '__Entity__'][0] AS primaryLabel
    WITH e, primaryLabel, 
         apoc.text.capitalize(lower(replace(primaryLabel, '_', ' '))) AS normalizedLabel
    
    WHERE primaryLabel <> normalizedLabel
    CALL apoc.create.addLabels(e, [normalizedLabel]) YIELD node
    CALL apoc.create.removeLabels(node, [primaryLabel]) YIELD node AS updatedNode
    RETURN count(updatedNode) AS normalized_entities
    """
    
    # 2. Merge similar relationship types
    merge_relationships_query = """
    MATCH ()-[r]->()
    WITH type(r) AS relType, count(r) AS frequency
    WHERE frequency < 5  // Low frequency relationships
    
    WITH collect({type: relType, freq: frequency}) AS lowFreqRels
    
    // Find similar relationship types and merge them
    UNWIND lowFreqRels AS rel1
    UNWIND lowFreqRels AS rel2
    WHERE rel1.type < rel2.type
    AND apoc.text.distance(rel1.type, rel2.type) <= 2
    
    CALL apoc.refactor.mergeRelationships([rel1.type], {properties: 'combine'})
    YIELD rel
    RETURN count(rel) AS merged_relationships
    """
    
    execute_graph_query(graph, normalize_labels_query)
    execute_graph_query(graph, merge_relationships_query)
```

## Post-Processing Pipeline

### Full-Text and Vector Index Creation

**Location**: `backend/src/post_processing.py`

**Hybrid Search Index Setup**:
```python
def create_vector_fulltext_indexes(uri, username, password, database):
    """Create comprehensive search indexes"""
    
    driver = get_graphDB_driver(uri, username, password, database)
    
    with driver.session(database=database) as session:
        # 1. Full-text search indexes
        fulltext_indexes = [
            "CREATE FULLTEXT INDEX entity_fulltext_index IF NOT EXISTS FOR (e:__Entity__) ON EACH [e.id, e.description]",
            "CREATE FULLTEXT INDEX chunk_fulltext_index IF NOT EXISTS FOR (c:Chunk) ON EACH [c.text]",
            "CREATE FULLTEXT INDEX document_fulltext_index IF NOT EXISTS FOR (d:Document) ON EACH [d.fileName]"
        ]
        
        # 2. Vector similarity indexes
        vector_indexes = [
            "CREATE VECTOR INDEX chunk_embedding_index IF NOT EXISTS FOR (c:Chunk) ON c.embedding OPTIONS {indexConfig: {`vector.dimensions`: 1536, `vector.similarity_function`: 'cosine'}}",
            "CREATE VECTOR INDEX entity_embedding_index IF NOT EXISTS FOR (e:__Entity__) ON e.embedding OPTIONS {indexConfig: {`vector.dimensions`: 1536, `vector.similarity_function`: 'cosine'}}"
        ]
        
        # 3. Property indexes for performance
        property_indexes = [
            "CREATE INDEX entity_id_index IF NOT EXISTS FOR (e:__Entity__) ON (e.id)",
            "CREATE INDEX chunk_position_index IF NOT EXISTS FOR (c:Chunk) ON (c.position)",
            "CREATE INDEX document_status_index IF NOT EXISTS FOR (d:Document) ON (d.status)",
            "CREATE INDEX community_level_index IF NOT EXISTS FOR (c:__Community__) ON (c.level)"
        ]
        
        # Execute all index creation queries
        for query in fulltext_indexes + vector_indexes + property_indexes:
            try:
                session.run(query)
            except Exception as e:
                if "already exists" not in str(e):
                    logging.error(f"Failed to create index: {e}")
```

### Graph Statistics and Optimization

**Performance Monitoring**:
```python
def update_node_relationship_count(self, document_name=""):
    """Update comprehensive graph statistics"""
    
    if document_name:
        # Document-specific statistics
        stats_query = """
        MATCH (d:Document {fileName: $fileName})
        
        OPTIONAL MATCH (d)<-[:PART_OF]-(c:Chunk)
        WITH d, count(c) AS chunkCount
        
        OPTIONAL MATCH (d)<-[:PART_OF]-(c:Chunk)-[:HAS_ENTITY]->(e:__Entity__)
        WITH d, chunkCount, count(DISTINCT e) AS entityCount
        
        OPTIONAL MATCH (d)<-[:PART_OF]-(c:Chunk)-[:HAS_ENTITY]->(e1:__Entity__)
        OPTIONAL MATCH (e1)-[r:!HAS_ENTITY&!PART_OF]-(e2:__Entity__)
        WITH d, chunkCount, entityCount, count(r) AS relationshipCount
        
        OPTIONAL MATCH (d)<-[:PART_OF]-(c:Chunk)-[:HAS_ENTITY]->(e:__Entity__)
        OPTIONAL MATCH (e)-[:IN_COMMUNITY]->(comm:__Community__)
        WITH d, chunkCount, entityCount, relationshipCount, count(DISTINCT comm) AS communityCount
        
        SET d.chunkNodeCount = chunkCount,
            d.entityNodeCount = entityCount,
            d.entityEntityRelCount = relationshipCount,
            d.communityNodeCount = communityCount,
            d.node_count = chunkCount + entityCount,
            d.relationship_count = relationshipCount
            
        RETURN d.fileName AS fileName, chunkCount, entityCount, relationshipCount, communityCount
        """
        
        result = execute_graph_query(self.graph, stats_query, {"fileName": document_name})
        
    else:
        # Global statistics
        global_stats_query = """
        MATCH (d:Document)
        OPTIONAL MATCH (d)<-[:PART_OF]-(c:Chunk)
        OPTIONAL MATCH (c)-[:HAS_ENTITY]->(e:__Entity__)
        OPTIONAL MATCH (e)-[r:!HAS_ENTITY&!PART_OF&!IN_COMMUNITY]-(e2:__Entity__)
        OPTIONAL MATCH (e)-[:IN_COMMUNITY]->(comm:__Community__)
        
        WITH d,
             count(DISTINCT c) AS chunkCount,
             count(DISTINCT e) AS entityCount,
             count(DISTINCT r) AS relationshipCount,
             count(DISTINCT comm) AS communityCount
             
        SET d.chunkNodeCount = chunkCount,
            d.entityNodeCount = entityCount,
            d.entityEntityRelCount = relationshipCount,
            d.communityNodeCount = communityCount,
            d.node_count = chunkCount + entityCount,
            d.relationship_count = relationshipCount
            
        RETURN d.fileName AS fileName, chunkCount, entityCount, relationshipCount, communityCount
        """
        
        result = execute_graph_query(self.graph, global_stats_query)
    
    return result
```

## Configuration Parameters

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `DUPLICATE_SCORE_VALUE` | `0.97` | Similarity threshold for entity deduplication |
| `DUPLICATE_TEXT_DISTANCE` | `3` | Maximum text edit distance for duplicates |
| `KNN_MIN_SCORE` | `0.94` | Minimum similarity score for KNN relationships |
| `ENTITY_EMBEDDING` | `False` | Enable entity embedding generation |
| `COMMUNITY_MIN_SIZE` | `1` | Minimum community size threshold |
| `LEIDEN_MAX_LEVELS` | `3` | Maximum hierarchy levels for communities |

### Neo4j Configuration

**Database Settings**:
```properties
# Memory allocation
dbms.memory.heap.initial_size=512m
dbms.memory.heap.max_size=2G
dbms.memory.pagecache.size=1G

# Performance tuning
dbms.transaction.timeout=300s
dbms.transaction.concurrent.maximum=1000
dbms.connector.bolt.thread_pool_max_size=400

# Vector index settings
db.index.vector.ephemeral_node_cache.enabled=true
db.index.vector.ephemeral_node_cache.size=10000
```

## Integration Points

### Upstream Integration

**LLM Pipeline**:
- Receives GraphDocument objects from entity extraction
- Processes entities and relationships with validation
- Maintains chunk-entity relationships

### Downstream Integration

**Query Pipeline**:
- Provides structured graph for multi-modal retrieval
- Enables community-based search
- Supports similarity-based recommendations

### External Services

**Neo4j Graph Data Science**:
- Community detection algorithms
- Graph analytics and metrics
- Performance optimization tools

## Monitoring and Metrics

### Graph Quality Metrics

1. **Entity Distribution**: Entities per document/chunk
2. **Relationship Density**: Relationships per entity
3. **Community Coherence**: Intra-community similarity scores
4. **Schema Consistency**: Entity type distribution
5. **Deduplication Efficiency**: Duplicate detection rates

### Performance Metrics

1. **Storage Efficiency**: Database size vs. content volume
2. **Query Performance**: Average response times by query type
3. **Index Utilization**: Search index hit rates
4. **Memory Usage**: Heap and page cache utilization

### Logging Implementation

**Graph Construction Logging**:
```python
graph_construction_log = {
    'document_name': document_name,
    'entities_created': entity_count,
    'relationships_created': relationship_count,
    'communities_detected': community_count,
    'deduplication_merges': merge_count,
    'construction_time': elapsed_time,
    'graph_size_mb': database_size_mb,
    'timestamp': datetime.now().isoformat()
}
logger.log_struct(graph_construction_log, "INFO")
```

This knowledge graph construction system creates a rich, interconnected representation of document content that enables sophisticated querying, similarity search, and knowledge discovery while maintaining performance and scalability.