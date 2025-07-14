# Query and Retrieval Pipeline Technical Specification

## Overview

The query and retrieval pipeline implements a sophisticated multi-modal RAG (Retrieval-Augmented Generation) system that combines vector similarity search, graph traversal, community-based retrieval, and full-text search to provide contextually rich responses with comprehensive source attribution.

## Architecture

### Core Components

- **Multi-Modal Retrieval Engine**: 7 distinct search modes with adaptive strategies
- **RAG Implementation**: Context compilation, compression, and response generation
- **Vector Search System**: Embedding-based similarity retrieval
- **Graph Traversal Engine**: Entity relationship exploration
- **Community Search**: Hierarchical community-based retrieval
- **Response Generation**: LLM-based answer synthesis with citation tracking

### Data Flow

```
User Query → Mode Selection → Context Retrieval → Document Processing → Response Generation → Citation Assembly
```

## Multi-Modal Retrieval Modes

### Mode Configuration System

**Location**: `backend/src/QA_integration.py`

**Mode Definitions**:
```python
CHAT_MODES = {
    "vector": {
        "description": "Pure vector similarity search using embeddings",
        "retriever_type": "vector",
        "graph_traversal": False,
        "community_search": False
    },
    "fulltext": {
        "description": "Hybrid vector + keyword search",
        "retriever_type": "hybrid",
        "graph_traversal": False,
        "community_search": False
    },
    "entity_vector": {
        "description": "Entity-focused vector search with local community traversal",
        "retriever_type": "vector",
        "graph_traversal": True,
        "community_search": "local"
    },
    "graph_vector": {
        "description": "Vector search enhanced with graph relationship traversal",
        "retriever_type": "vector",
        "graph_traversal": True,
        "community_search": False
    },
    "graph_vector_fulltext": {
        "description": "Default mode: vector + graph + fulltext combined",
        "retriever_type": "hybrid",
        "graph_traversal": True,
        "community_search": False
    },
    "global_vector": {
        "description": "Community-level search using hierarchical summaries",
        "retriever_type": "community",
        "graph_traversal": False,
        "community_search": "global"
    },
    "graph": {
        "description": "Pure Cypher-based graph querying",
        "retriever_type": "graph",
        "graph_traversal": True,
        "community_search": False
    }
}
```

### Dynamic Mode Selection

**Implementation**:
```python
def get_chat_mode_settings(mode):
    """Get configuration for specified chat mode"""
    mode_config = CHAT_MODES.get(mode, CHAT_MODES["graph_vector_fulltext"])
    
    return {
        'mode': mode,
        'retriever_type': mode_config['retriever_type'],
        'enable_graph_traversal': mode_config['graph_traversal'],
        'community_level': mode_config.get('community_search', False),
        'use_fulltext': 'fulltext' in mode or 'hybrid' in mode_config['retriever_type']
    }
```

## Vector Search Implementation

### Similarity Search Algorithm

**Location**: `backend/src/graph_query.py`

**Core Vector Query**:
```cypher
CALL db.index.vector.queryNodes('vector', $top_k, $query_vector) 
YIELD node AS chunk, score

WITH chunk, score
WHERE score >= $similarity_threshold

MATCH (chunk)-[:PART_OF]->(d:Document)
WHERE d.fileName IN $document_names OR $document_names = []

WITH d, 
     collect(DISTINCT {chunk: chunk, score: score}) AS chunks,
     avg(score) AS avg_score

RETURN d.fileName AS fileName,
       d.fileSource AS fileSource, 
       chunks,
       avg_score AS similarity_score

ORDER BY avg_score DESC
LIMIT $limit
```

**Configuration Parameters**:
```python
VECTOR_SEARCH_CONFIG = {
    'top_k': int(os.environ.get('VECTOR_SEARCH_TOP_K', 5)),
    'similarity_threshold': float(os.environ.get('CHAT_SEARCH_KWARG_SCORE_THRESHOLD', 0.5)),
    'max_documents': int(os.environ.get('MAX_SEARCH_DOCUMENTS', 20)),
    'effective_search_ratio': float(os.environ.get('EFFECTIVE_SEARCH_RATIO', 1))
}
```

### Advanced Vector Retrieval

**Neo4j Vector Store Integration**:
```python
def setup_vector_retriever(graph, embedding_function, search_kwargs):
    """Initialize vector-based document retriever"""
    
    # Configure vector store
    vector_store = Neo4jVector(
        embedding=embedding_function,
        graph=graph,
        node_label="Chunk",
        embedding_node_property="embedding",
        text_node_property="text",
        index_name="vector",
        search_type="vector"
    )
    
    # Create retriever with similarity threshold
    retriever = vector_store.as_retriever(
        search_kwargs={
            "k": search_kwargs.get('k', 5),
            "score_threshold": search_kwargs.get('score_threshold', 0.5),
            "fetch_k": search_kwargs.get('fetch_k', 20)
        }
    )
    
    return retriever
```

## Graph Traversal Algorithms

### Adaptive Graph Expansion

**Location**: `backend/src/graph_query.py`

**Similarity-Based Traversal Strategy**:
```cypher
MATCH (e:__Entity__)
WHERE e.embedding IS NOT NULL

CALL db.index.vector.queryNodes('entity_embedding_index', 5, $query_vector)
YIELD node AS entity, score

WITH entity, score
WHERE score >= 0.3  // Minimum similarity threshold

CALL {
    WITH entity, score
    CASE 
        WHEN entity.embedding IS NULL OR (0.3 <= score <= 0.9) THEN 
            // 1-hop traversal for moderate similarity
            OPTIONAL MATCH path=(entity)(()-[rels:!HAS_ENTITY&!PART_OF]-()){{0,1}}(:!Chunk&!Document&!__Community__)
            RETURN path LIMIT 20
            
        WHEN score > 0.9 THEN
            // 2-hop traversal for high similarity  
            OPTIONAL MATCH path=(entity)(()-[rels:!HAS_ENTITY&!PART_OF]-()){{0,2}}(:!Chunk&!Document&!__Community__)
            RETURN path LIMIT 40
            
        ELSE 
            // No traversal for low similarity
            MATCH path=(entity) 
            RETURN path
    END
}

UNWIND nodes(path) AS node
WITH DISTINCT node
WHERE node:__Entity__

// Get chunks containing these entities
MATCH (node)<-[:HAS_ENTITY]-(chunk:Chunk)-[:PART_OF]->(doc:Document)
WHERE doc.fileName IN $document_names OR $document_names = []

RETURN doc.fileName AS fileName,
       doc.fileSource AS fileSource,
       collect(DISTINCT {
           chunk: chunk,
           entities: collect(DISTINCT node.id),
           score: 0.8  // Graph-derived score
       }) AS chunks,
       0.8 AS similarity_score

ORDER BY similarity_score DESC
```

### Relationship Type Filtering

**Configurable Relationship Exclusion**:
```python
EXCLUDED_RELATIONSHIPS = {
    'HAS_ENTITY',       # Structural: Chunk-Entity
    'PART_OF',          # Structural: Chunk-Document  
    'FIRST_CHUNK',      # Structural: Document-Chunk
    'NEXT_CHUNK',       # Structural: Chunk-Chunk
    'IN_COMMUNITY',     # Hierarchical: Entity-Community
    'PARENT_COMMUNITY', # Hierarchical: Community-Community
    'SIMILAR',          # Similarity: Various similarity relationships
    '_Bloom_Perspective_' # UI-specific relationships
}

def build_relationship_filter():
    """Build Cypher relationship filter clause"""
    excluded = '|'.join(EXCLUDED_RELATIONSHIPS)
    return f"!{excluded}"
```

## Community-Based Search

### Hierarchical Community Retrieval

**Location**: `backend/src/QA_integration.py`

**Community Search Implementation**:
```python
def community_retrieval(query, graph, document_names, level=0):
    """Retrieve documents using community-based search"""
    
    # Get relevant communities based on query embedding
    community_query = f"""
    MATCH (c:__Community__)
    WHERE c.level = {level} AND c.summary IS NOT NULL
    
    CALL db.index.vector.queryNodes('community_embedding_index', 5, $query_vector)
    YIELD node AS community, score
    WHERE score >= 0.4
    
    // Get entities in relevant communities
    MATCH (community)<-[:IN_COMMUNITY]-(e:__Entity__)
    
    // Get chunks containing these entities
    MATCH (e)<-[:HAS_ENTITY]-(chunk:Chunk)-[:PART_OF]->(doc:Document)
    WHERE doc.fileName IN $document_names OR $document_names = []
    
    WITH doc, community,
         collect(DISTINCT {{
             chunk: chunk,
             community_id: community.id,
             community_summary: community.summary,
             score: score
         }}) AS chunks,
         score AS community_score
    
    RETURN doc.fileName AS fileName,
           doc.fileSource AS fileSource,
           chunks,
           community_score AS similarity_score,
           collect(DISTINCT {{
               id: community.id,
               title: community.title,
               summary: community.summary,
               level: community.level
           }}) AS communities
    
    ORDER BY community_score DESC
    LIMIT 10
    """
    
    results = execute_graph_query(graph, community_query, {
        'query_vector': get_query_embedding(query),
        'document_names': document_names
    })
    
    return format_community_results(results)
```

### Community Summary Generation

**Parallel Summary Processing**:
```python
def generate_community_summaries(communities, llm):
    """Generate summaries for communities using parallel processing"""
    
    def summarize_community(community_data):
        entities = community_data['entities']
        entity_descriptions = [e.get('description', e['id']) for e in entities]
        
        prompt = f"""
        Analyze the following entities that belong to the same community and provide a concise summary:
        
        Entities: {', '.join(entity_descriptions[:20])}  # Limit to prevent token overflow
        
        Provide a 2-3 sentence summary that captures the main theme or topic that connects these entities.
        Focus on the overarching concept rather than listing individual entities.
        """
        
        try:
            response = llm.invoke(prompt)
            return response.content.strip()
        except Exception as e:
            logging.error(f"Failed to generate community summary: {e}")
            return f"Community containing {len(entities)} related entities"
    
    # Use ThreadPoolExecutor for parallel processing
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        future_to_community = {
            executor.submit(summarize_community, comm): comm['id'] 
            for comm in communities
        }
        
        summaries = {}
        for future in concurrent.futures.as_completed(future_to_community):
            community_id = future_to_community[future]
            try:
                summary = future.result(timeout=30)
                summaries[community_id] = summary
            except Exception as e:
                logging.error(f"Community summary generation failed for {community_id}: {e}")
                summaries[community_id] = "Summary generation failed"
    
    return summaries
```

## RAG Implementation

### Context Retrieval Pipeline

**Location**: `backend/src/QA_integration.py:60-120`

**Multi-Stage Retrieval Process**:
```python
def retrieve_documents(doc_retriever, messages):
    """Multi-stage document retrieval with query transformation"""
    
    # Stage 1: Query transformation for conversational context
    query_transform_prompt = ChatPromptTemplate.from_messages([
        ("system", QUESTION_TRANSFORM_TEMPLATE),
        MessagesPlaceholder(variable_name="messages")
    ])
    
    query_transforming_retriever_chain = RunnableBranch(
        (
            lambda x: len(x.get("messages", [])) == 1,
            # Single message - use as-is
            (lambda x: x["messages"][-1].content) | doc_retriever,
        ),
        # Multiple messages - transform for context
        query_transform_prompt | llm | StrOutputParser() | doc_retriever,
    )
    
    # Stage 2: Document retrieval
    docs = query_transforming_retriever_chain.invoke({"messages": messages})
    
    # Stage 3: Query extraction for response generation
    question_extraction_chain = RunnableBranch(
        (
            lambda x: len(x.get("messages", [])) == 1,
            lambda x: x["messages"][-1].content,
        ),
        query_transform_prompt | llm | StrOutputParser(),
    )
    
    transformed_question = question_extraction_chain.invoke({"messages": messages})
    
    return docs, transformed_question
```

### Contextual Compression

**Implementation**:
```python
def setup_compression_retriever(base_retriever, embeddings):
    """Create retriever with contextual compression"""
    
    # Text splitter for long documents
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=3000,
        chunk_overlap=300
    )
    
    # Embedding filter for relevance
    embeddings_filter = EmbeddingsFilter(
        embeddings=embeddings,
        similarity_threshold=float(os.environ.get('CHAT_EMBEDDING_FILTER_SCORE_THRESHOLD', 0.10))
    )
    
    # Compression pipeline
    pipeline_compressor = DocumentCompressorPipeline(
        transformers=[splitter, embeddings_filter]
    )
    
    # Compression retriever
    compression_retriever = ContextualCompressionRetriever(
        base_compressor=pipeline_compressor,
        base_retriever=base_retriever
    )
    
    return compression_retriever
```

### Document Processing and Ranking

**Multi-Criteria Document Scoring**:
```python
def format_documents(documents, model, chat_mode_settings):
    """Process and rank retrieved documents for response generation"""
    
    # Sort by similarity scores
    sorted_documents = sorted(
        documents, 
        key=lambda doc: doc.state.get("query_similarity_score", 0), 
        reverse=True
    )
    
    # Apply model-specific token limits
    prompt_token_cutoff = get_prompt_token_cutoff_by_model(model)
    sorted_documents = sorted_documents[:prompt_token_cutoff]
    
    formatted_docs = []
    entity_ids = set()
    relationship_ids = set()
    chunk_metadata = []
    entity_metadata = []
    community_data = []
    sources = set()
    
    for i, doc in enumerate(sorted_documents):
        # Extract metadata
        source = doc.metadata.get('source', f'source_{i+1}')
        sources.add(source)
        
        # Collect entity information
        if 'entities' in doc.metadata:
            doc_entities = doc.metadata['entities']
            if isinstance(doc_entities, list):
                entity_ids.update(doc_entities)
                
        # Collect relationship information  
        if 'relationships' in doc.metadata:
            doc_relationships = doc.metadata['relationships']
            if isinstance(doc_relationships, list):
                relationship_ids.update(doc_relationships)
                
        # Collect community information
        if 'communitydetails' in doc.metadata:
            community_info = doc.metadata['communitydetails']
            if isinstance(community_info, list):
                community_data.extend(community_info)
                
        # Collect chunk metadata
        chunk_info = {
            'id': doc.metadata.get('id', f'chunk_{i}'),
            'score': doc.state.get("query_similarity_score", 0),
            'source': source,
            'length': len(doc.page_content)
        }
        chunk_metadata.append(chunk_info)
        
        # Format document content
        formatted_doc = f"Document start\nThis Document belongs to the source {source}\nContent: {doc.page_content}\nDocument end\n"
        formatted_docs.append(formatted_doc)
    
    # Compile comprehensive context
    context = '\n'.join(formatted_docs)
    
    return context, {
        'sources': list(sources),
        'nodedetails': {
            "chunkdetails": chunk_metadata,
            "entitydetails": entity_metadata,
            "communitydetails": community_data
        },
        'entities': {
            'entityids': list(entity_ids),
            'relationshipids': list(relationship_ids)
        }
    }
```

## Response Generation

### Multi-Template Response System

**Location**: `backend/src/QA_integration.py:200-250`

**Response Generation Templates**:
```python
CHAT_SYSTEM_TEMPLATE = """
You are an AI-powered question-answering agent with access to a comprehensive knowledge base. 
Your responses should be helpful, accurate, and well-structured.

### Response Guidelines:
1. **Direct Answers**: Provide clear, thorough answers to user questions
2. **Utilize History and Context**: Leverage conversation history and provided context
3. **Admit Unknowns**: Clearly state when information is not available
4. **Avoid Hallucination**: Only use information from the provided context
5. **Structured Responses**: Use formatting to enhance readability when appropriate
6. **Source Awareness**: Be mindful of the sources but don't cite them explicitly

### Context:
<context>
{context}
</context>

### Conversation History:
{chat_history}

### Current Question:
{question}

Provide a comprehensive and helpful response based on the context and conversation history.
"""

CHAT_USER_TEMPLATE = """
Based on the provided context and our conversation history, please answer the following question:

{question}
"""
```

### Response Quality Control

**Implementation**:
```python
def process_documents(docs, question, messages, llm, model, chat_mode_settings):
    """Process documents and generate response with quality control"""
    
    # Format context and extract metadata
    context, result = format_documents(docs, model, chat_mode_settings)
    
    if not context.strip():
        return "I don't have enough information to answer your question.", result, 0, []
    
    # Prepare conversation history
    chat_history = format_chat_history(messages[:-1])
    
    # Create response generation chain
    prompt = ChatPromptTemplate.from_messages([
        ("system", CHAT_SYSTEM_TEMPLATE),
        ("user", CHAT_USER_TEMPLATE)
    ])
    
    chain = prompt | llm | StrOutputParser()
    
    try:
        # Generate response
        response = chain.invoke({
            "context": context,
            "question": question,
            "chat_history": chat_history
        })
        
        # Calculate token usage
        total_tokens = estimate_token_count(context + response)
        
        # Validate response quality
        quality_score = assess_response_quality(response, context, question)
        
        if quality_score < 0.6:
            logging.warning(f"Low quality response detected: {quality_score}")
            
        return response, result, total_tokens, docs
        
    except Exception as e:
        logging.error(f"Response generation failed: {e}")
        return "I encountered an error processing your question. Please try again.", result, 0, []
```

### Citation and Source Attribution

**Comprehensive Source Tracking**:
```python
def compile_source_attribution(result, docs):
    """Compile comprehensive source attribution information"""
    
    attribution = {
        'primary_sources': result.get('sources', []),
        'chunk_details': [],
        'entity_network': {
            'entities': result.get('entities', {}).get('entityids', []),
            'relationships': result.get('entities', {}).get('relationshipids', [])
        },
        'community_context': result.get('nodedetails', {}).get('communitydetails', []),
        'retrieval_metadata': {
            'total_chunks': len(docs),
            'avg_similarity': calculate_average_similarity(docs),
            'retrieval_mode': result.get('mode', 'unknown')
        }
    }
    
    # Detailed chunk information
    for i, doc in enumerate(docs):
        chunk_detail = {
            'index': i,
            'source': doc.metadata.get('source', 'unknown'),
            'similarity_score': doc.state.get("query_similarity_score", 0),
            'content_preview': doc.page_content[:200] + "..." if len(doc.page_content) > 200 else doc.page_content,
            'metadata': {k: v for k, v in doc.metadata.items() if k != 'page_content'}
        }
        attribution['chunk_details'].append(chunk_detail)
    
    return attribution
```

## Performance Optimizations

### Query Optimization

**Index Utilization**:
```python
def optimize_query_performance():
    """Implement query performance optimizations"""
    
    # 1. Vector index configuration
    vector_index_config = {
        'vector.dimensions': 1536,
        'vector.similarity_function': 'cosine',
        'vector.hnsw.ef': 200,      # Search quality parameter
        'vector.hnsw.m': 16         # Index quality parameter
    }
    
    # 2. Query result limiting
    result_limits = {
        'max_chunks_per_document': 5,
        'max_entities_per_chunk': 10,
        'max_traversal_depth': 2,
        'max_community_size': 100
    }
    
    # 3. Caching strategies
    cache_config = {
        'query_result_ttl': 300,    # 5 minutes
        'embedding_cache_size': 1000,
        'community_summary_ttl': 3600  # 1 hour
    }
    
    return vector_index_config, result_limits, cache_config
```

### Parallel Processing

**Concurrent Retrieval**:
```python
def parallel_multimodal_retrieval(query, graph, document_names, mode_settings):
    """Execute multiple retrieval strategies in parallel"""
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
        futures = {}
        
        # Vector search
        if mode_settings.get('use_vector', True):
            futures['vector'] = executor.submit(vector_search, query, graph, document_names)
        
        # Graph traversal
        if mode_settings.get('enable_graph_traversal', False):
            futures['graph'] = executor.submit(graph_traversal_search, query, graph, document_names)
        
        # Community search
        if mode_settings.get('community_level', False):
            futures['community'] = executor.submit(community_search, query, graph, document_names)
        
        # Collect results
        results = {}
        for mode, future in futures.items():
            try:
                results[mode] = future.result(timeout=30)
            except Exception as e:
                logging.error(f"Parallel retrieval failed for {mode}: {e}")
                results[mode] = []
    
    # Merge and rank results
    return merge_retrieval_results(results, mode_settings)
```

## Configuration Parameters

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `VECTOR_SEARCH_TOP_K` | `5` | Number of similar chunks to retrieve |
| `CHAT_SEARCH_KWARG_SCORE_THRESHOLD` | `0.5` | Minimum similarity threshold |
| `CHAT_EMBEDDING_FILTER_SCORE_THRESHOLD` | `0.10` | Compression filter threshold |
| `MAX_SEARCH_DOCUMENTS` | `20` | Maximum documents per query |
| `EFFECTIVE_SEARCH_RATIO` | `1` | Search result multiplier |
| `COMMUNITY_SEARCH_LEVELS` | `3` | Community hierarchy levels |

### Model-Specific Configuration

**Token Limits by Model**:
```python
MODEL_TOKEN_LIMITS = {
    'gpt-3.5-turbo': 4,
    'gpt-4': 8,
    'gpt-4-turbo': 12,
    'claude-3-sonnet': 15,
    'claude-3-opus': 20,
    'gemini-1.5-pro': 28,
    'default': 10
}
```

## Integration Points

### Upstream Integration

**Knowledge Graph**:
- Accesses entities, relationships, and communities
- Utilizes vector and full-text indexes
- Leverages graph structure for traversal

### Downstream Integration

**Frontend Interface**:
- Provides real-time response streaming
- Returns comprehensive metadata for UI display
- Supports chat history management

### External Services

**LLM Providers**:
- Response generation across multiple providers
- Model-specific optimization
- Rate limiting and error handling

## Monitoring and Metrics

### Query Performance Metrics

1. **Response Time**: Average query processing time by mode
2. **Retrieval Quality**: Relevance scores and user feedback
3. **Context Utilization**: Percentage of retrieved context used
4. **Token Efficiency**: Tokens per response by model
5. **Cache Hit Rates**: Caching effectiveness metrics

### Quality Metrics

1. **Answer Relevance**: Response relevance to user queries
2. **Source Attribution**: Accuracy of source citations
3. **Coherence Score**: Response coherence and structure
4. **Factual Accuracy**: Factual correctness assessment
5. **Coverage Completeness**: Question coverage percentage

### Logging Implementation

**Query Processing Logging**:
```python
query_log = {
    'query': question,
    'mode': chat_mode_settings.get('mode', 'unknown'),
    'documents_retrieved': len(docs),
    'entities_found': len(result.get('entities', {}).get('entityids', [])),
    'communities_accessed': len(result.get('nodedetails', {}).get('communitydetails', [])),
    'response_length': len(response),
    'processing_time': elapsed_time,
    'token_usage': total_tokens,
    'similarity_scores': [doc.state.get("query_similarity_score", 0) for doc in docs],
    'timestamp': datetime.now().isoformat()
}
logger.log_struct(query_log, "INFO")
```

This query and retrieval pipeline provides a sophisticated, multi-modal approach to information retrieval that combines the strengths of vector similarity, graph relationships, and community structures to deliver contextually rich, accurate responses with comprehensive source attribution.