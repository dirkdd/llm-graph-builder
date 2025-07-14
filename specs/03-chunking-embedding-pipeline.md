# Chunking and Embedding Pipeline Technical Specification

## Overview

The chunking and embedding pipeline transforms processed documents into semantically searchable vector representations. It segments documents into optimal chunks, generates embeddings using multiple providers, and creates efficient vector indexes for retrieval.

## Architecture

### Core Components

- **Chunking Engine**: `CreateChunksofDocument` class in `create_chunks.py`
- **Embedding Generator**: Multi-provider embedding system in `make_relationships.py`
- **Vector Index Manager**: Neo4j vector index creation and management
- **Relationship Builder**: Chunk-to-document and sequential relationships

### Data Flow

```
Document Objects → Text Chunking → Chunk ID Generation → Neo4j Storage → Embedding Generation → Vector Indexing
```

## Chunking Implementation

### TokenTextSplitter Configuration

**Location**: `backend/src/create_chunks.py:27-31`

**Core Implementation**:
```python
class CreateChunksofDocument:
    def __init__(self, pages, graph):
        self.pages = pages
        self.graph = graph
    
    def split_file_into_chunks(self, token_chunk_size, chunk_overlap):
        text_splitter = TokenTextSplitter(
            chunk_size=token_chunk_size, 
            chunk_overlap=chunk_overlap
        )
        
        # Dynamic chunk limitation
        MAX_TOKEN_CHUNK_SIZE = int(os.getenv('MAX_TOKEN_CHUNK_SIZE', 10000))
        chunk_to_be_created = int(MAX_TOKEN_CHUNK_SIZE / token_chunk_size)
```

**Chunking Strategy**:
```python
def split_file_into_chunks(self, token_chunk_size, chunk_overlap):
    all_chunks = []
    for page in self.pages:
        chunks = text_splitter.split_documents([page])
        
        # Apply chunk limit
        if len(all_chunks) + len(chunks) > chunk_to_be_created:
            remaining_chunks = chunk_to_be_created - len(all_chunks)
            chunks = chunks[:remaining_chunks]
            all_chunks.extend(chunks)
            break
        
        all_chunks.extend(chunks)
    
    return all_chunks
```

### Chunk Size Optimization

**Dynamic Calculation**:
```python
MAX_TOKEN_CHUNK_SIZE = int(os.getenv('MAX_TOKEN_CHUNK_SIZE', 10000))
chunk_to_be_created = int(MAX_TOKEN_CHUNK_SIZE / token_chunk_size)
```

**Optimization Factors**:
1. **Token Budget Management**: Prevents exceeding LLM context limits
2. **Memory Efficiency**: Balances chunk size with processing speed
3. **Quality Preservation**: Maintains semantic coherence within chunks
4. **Performance Tuning**: Configurable limits for different deployment scenarios

### Overlap Handling

**Implementation Strategy**:
- **Configurable Overlap**: Via `chunk_overlap` parameter
- **Content Continuity**: Preserves context across chunk boundaries
- **Deduplication**: Automatic handling of overlapping content
- **Performance Balance**: Optimizes overlap vs. processing overhead

## Content-Aware Chunking

### Document Type Specialization

**YouTube Video Handling**:
```python
if 'length' in chunk.metadata:
    # YouTube video with timestamp metadata
    chunk.metadata['timestamp'] = calculate_timestamp(chunk.metadata)
```

**PDF Page-Aware Chunking**:
```python
if 'page' in chunk.metadata:
    # PDF with page number preservation
    chunk.metadata['page_number'] = chunk.metadata['page']
```

**Generic Document Processing**:
```python
# Standard text splitting without special metadata
chunks = text_splitter.split_documents([page])
```

## Chunk ID Generation

### Content-Based Hashing

**Location**: `backend/src/make_relationships.py:75-77`

**Algorithm Implementation**:
```python
def generate_chunk_id(chunk_content):
    page_content_sha1 = hashlib.sha1(chunk_content.encode('utf-8'))
    return page_content_sha1.hexdigest()
```

**Benefits**:
1. **Deterministic IDs**: Consistent across processing runs
2. **Content Deduplication**: Identical chunks automatically merged
3. **Integrity Verification**: Content changes detectable via ID change
4. **Cross-Reference Support**: Reliable chunk identification for relationships

### Metadata Enrichment

**Position Tracking** (`make_relationships.py:78-98`):
```python
def create_chunk_metadata(chunks):
    chunk_metadata = []
    offset = 0
    
    for i, chunk in enumerate(chunks):
        position = i + 1
        if i > 0:
            offset += len(chunks[i-1].page_content)
            
        metadata = {
            "position": position,
            "length": len(chunk.page_content),
            "content_offset": offset,
            "chunk_id": generate_chunk_id(chunk.page_content)
        }
        
        chunk_metadata.append(metadata)
    
    return chunk_metadata
```

## Neo4j Storage Integration

### Chunk Node Creation

**Cypher Query Pattern**:
```cypher
MERGE (d:Document {fileName: $fileName})
MERGE (c:Chunk {id: $chunkId})
SET c.text = $text,
    c.position = $position,
    c.length = $length,
    c.content_offset = $content_offset
MERGE (c)-[:PART_OF]->(d)
```

**Batch Processing Implementation**:
```python
def create_relation_between_chunks(graph, file_name, chunks):
    chunk_batch = []
    
    for i, chunk in enumerate(chunks):
        chunk_data = {
            "chunkId": generate_chunk_id(chunk.page_content),
            "text": chunk.page_content,
            "position": i + 1,
            "length": len(chunk.page_content),
            "fileName": file_name
        }
        chunk_batch.append(chunk_data)
    
    # Batch insert for performance
    execute_batch_query(graph, CREATE_CHUNK_QUERY, chunk_batch)
```

### Sequential Relationships

**Relationship Types**:
1. **FIRST_CHUNK**: Document → First Chunk
2. **NEXT_CHUNK**: Chunk → Next Chunk
3. **PART_OF**: Chunk → Document

**Implementation**:
```cypher
// First chunk relationship
MATCH (d:Document {fileName: $fileName})
MATCH (c:Chunk {id: $firstChunkId})
MERGE (d)-[:FIRST_CHUNK]->(c)

// Sequential relationships
MATCH (c1:Chunk {id: $currentChunkId})
MATCH (c2:Chunk {id: $nextChunkId})
MERGE (c1)-[:NEXT_CHUNK]->(c2)
```

## Multi-Provider Embedding System

### Embedding Provider Configuration

**Location**: `backend/src/shared/common_fn.py:72-93`

**Provider Selection Logic**:
```python
def load_embedding_model():
    embedding_model_name = os.environ.get('EMBEDDING_MODEL', 'all-MiniLM-L6-v2')
    
    if embedding_model_name == "openai":
        return OpenAIEmbeddings(), 1536
    elif embedding_model_name == "vertexai":
        return VertexAIEmbeddings(), 768
    elif embedding_model_name.startswith("bedrock"):
        return BedrockEmbeddings(), 1536
    else:
        # Default to HuggingFace
        return HuggingFaceEmbeddings(model_name=embedding_model_name), 384
```

### Embedding Generation Pipeline

**Location**: `backend/src/make_relationships.py:41-65`

**Core Implementation**:
```python
def create_chunk_embeddings(graph, chunkId_chunkDoc_list, file_name):
    embeddings, embedding_dimension = load_embedding_model()
    isEmbedding = os.environ.get('IS_EMBEDDING', 'true')
    
    if isEmbedding.upper() == "TRUE":
        data_for_query = []
        
        for row in chunkId_chunkDoc_list:
            # Generate embedding for chunk content
            embeddings_arr = embeddings.embed_query(row['chunk_doc'].page_content)
            
            data_for_query.append({
                "chunkId": row['chunk_id'],
                "embeddings": embeddings_arr
            })
        
        # Batch update embeddings in Neo4j
        update_embeddings_query = """
        UNWIND $data AS row
        MATCH (d:Document {fileName: $fileName})
        MERGE (c:Chunk {id: row.chunkId})
        SET c.embedding = row.embeddings
        MERGE (c)-[:PART_OF]->(d)
        """
        
        execute_graph_query(graph, update_embeddings_query, 
                           params={"data": data_for_query, "fileName": file_name})
```

### Provider-Specific Configurations

**OpenAI Embeddings**:
```python
openai_embeddings = OpenAIEmbeddings(
    model="text-embedding-ada-002",
    dimensions=1536
)
```

**Vertex AI Embeddings**:
```python
vertexai_embeddings = VertexAIEmbeddings(
    model_name="textembedding-gecko@003",
    dimensions=768
)
```

**HuggingFace Embeddings**:
```python
huggingface_embeddings = HuggingFaceEmbeddings(
    model_name="all-MiniLM-L6-v2",
    model_kwargs={'device': 'cpu'},
    encode_kwargs={'normalize_embeddings': True}
)
```

**AWS Bedrock Embeddings**:
```python
bedrock_embeddings = BedrockEmbeddings(
    model_id="amazon.titan-embed-text-v1",
    region_name="us-east-1"
)
```

## Vector Index Management

### Index Creation Algorithm

**Location**: `backend/src/make_relationships.py:158-179`

**Implementation**:
```python
def create_chunk_vector_index(graph):
    # Check for existing vector index
    vector_index_query = """
    SHOW INDEXES YIELD name, type, labelsOrTypes, properties 
    WHERE name = 'vector' AND type = 'VECTOR' 
    AND 'Chunk' IN labelsOrTypes AND 'embedding' IN properties 
    RETURN name
    """
    
    vector_index = execute_graph_query(graph, vector_index_query)
    
    if not vector_index:
        try:
            # Create new vector index
            vector_store = Neo4jVector(
                embedding=EMBEDDING_FUNCTION,
                graph=graph,
                node_label="Chunk",
                embedding_node_property="embedding",
                index_name="vector",
                embedding_dimension=EMBEDDING_DIMENSION
            )
            vector_store.create_new_index()
            
        except Exception as e:
            if "already exists" not in str(e):
                logging.error(f"Failed to create vector index: {e}")
                raise
```

### Index Configuration Parameters

**Vector Index Specification**:
```cypher
CREATE VECTOR INDEX vector IF NOT EXISTS 
FOR (c:Chunk) ON c.embedding
OPTIONS {
  indexConfig: {
    `vector.dimensions`: $embedding_dimension,
    `vector.similarity_function`: 'cosine'
  }
}
```

**Performance Tuning**:
- **Similarity Function**: Cosine similarity for semantic search
- **Dimension Matching**: Provider-specific dimension configuration
- **Index Optimization**: HNSW algorithm with configurable parameters

## Performance Optimizations

### Batch Processing

**Chunk Creation Batching**:
```python
BATCH_SIZE = 100

def process_chunks_in_batches(chunks, batch_size=BATCH_SIZE):
    for i in range(0, len(chunks), batch_size):
        batch = chunks[i:i + batch_size]
        process_chunk_batch(batch)
```

**Embedding Generation Batching**:
```python
def generate_embeddings_batch(text_list, embedding_model):
    # Use provider's batch embedding API when available
    if hasattr(embedding_model, 'embed_documents'):
        return embedding_model.embed_documents(text_list)
    else:
        # Fallback to individual embedding generation
        return [embedding_model.embed_query(text) for text in text_list]
```

### Memory Management

**Streaming Processing**:
- Large documents processed in configurable chunks
- Memory-efficient embedding generation
- Garbage collection optimization

**Connection Pooling**:
- Reused database connections
- Optimized transaction management
- Connection lifecycle management

### Concurrent Processing

**Parallel Embedding Generation**:
```python
import concurrent.futures

def generate_embeddings_parallel(chunk_texts, embedding_model, max_workers=4):
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = [executor.submit(embedding_model.embed_query, text) 
                  for text in chunk_texts]
        return [future.result() for future in concurrent.futures.as_completed(futures)]
```

## Error Handling and Resilience

### Embedding Generation Failures

**Retry Mechanism**:
```python
def generate_embedding_with_retry(text, embedding_model, max_retries=3):
    for attempt in range(max_retries):
        try:
            return embedding_model.embed_query(text)
        except Exception as e:
            if attempt == max_retries - 1:
                logging.error(f"Failed to generate embedding after {max_retries} attempts: {e}")
                raise
            logging.warning(f"Embedding generation attempt {attempt + 1} failed, retrying...")
            time.sleep(2 ** attempt)  # Exponential backoff
```

### Database Operation Resilience

**Deadlock Detection and Retry**:
```python
def execute_graph_query(graph, query, params=None, max_retries=3, delay=2):
    retries = 0
    while retries < max_retries:
        try:
            return graph.query(query, params)
        except TransientError as e:
            if "DeadlockDetected" in str(e):
                retries += 1
                logging.info(f"Deadlock detected. Retrying {retries}/{max_retries} in {delay} seconds...")
                time.sleep(delay)
            else:
                raise
    raise Exception(f"Failed after {max_retries} retries")
```

## Configuration Parameters

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `MAX_TOKEN_CHUNK_SIZE` | `10000` | Maximum total tokens per document |
| `EMBEDDING_MODEL` | `all-MiniLM-L6-v2` | Embedding model provider |
| `IS_EMBEDDING` | `true` | Enable/disable embedding generation |
| `EMBEDDING_DIMENSION` | Provider-specific | Vector dimension size |
| `BATCH_SIZE` | `100` | Batch size for processing |

### Chunking Parameters

**Token Configuration**:
- `token_chunk_size`: Individual chunk size (default: 1000)
- `chunk_overlap`: Overlap between chunks (default: 200)
- `chunk_to_be_created`: Dynamic limit based on total token budget

**Quality Settings**:
- Minimum chunk length validation
- Maximum chunk length enforcement
- Content quality filtering

## Integration Points

### Upstream Integration

**Document Processing Pipeline**:
- Receives LangChain Document objects
- Validates document content and metadata
- Reports chunking progress and statistics

### Downstream Integration

**LLM Processing Pipeline**:
- Provides chunk-document pairs for entity extraction
- Maintains chunk relationships for context preservation
- Enables chunk-level progress tracking

### External Services

**Embedding Providers**:
- OpenAI API integration
- Google Vertex AI client
- AWS Bedrock SDK
- HuggingFace transformers library

## Monitoring and Metrics

### Processing Metrics

1. **Chunking Performance**: Chunks per second, average chunk size
2. **Embedding Generation**: Embeddings per second, API latency
3. **Database Operations**: Insert rates, query performance
4. **Memory Usage**: Peak memory consumption, garbage collection

### Quality Metrics

1. **Chunk Quality**: Content coherence, semantic boundaries
2. **Embedding Quality**: Vector similarity distributions
3. **Index Performance**: Search latency, recall rates
4. **Content Coverage**: Percentage of content successfully processed

### Logging Implementation

**Structured Logging**:
```python
chunk_processing_log = {
    'file_name': file_name,
    'total_chunks': len(chunks),
    'total_tokens': sum(len(chunk.page_content.split()) for chunk in chunks),
    'embedding_model': embedding_model_name,
    'embedding_dimension': embedding_dimension,
    'processing_time': elapsed_time,
    'chunks_per_second': len(chunks) / elapsed_time,
    'timestamp': datetime.now().isoformat()
}
logger.log_struct(chunk_processing_log, "INFO")
```

This chunking and embedding pipeline provides the semantic foundation for the knowledge graph by transforming raw documents into searchable vector representations while maintaining document structure and relationships.