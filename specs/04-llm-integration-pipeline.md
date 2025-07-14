# LLM Integration Pipeline Technical Specification

## Overview

The LLM integration pipeline orchestrates entity and relationship extraction from document chunks using multiple LLM providers. It implements sophisticated prompt engineering, schema enforcement, and quality control mechanisms to ensure consistent knowledge graph construction.

## Architecture

### Core Components

- **Multi-Provider LLM Manager**: Dynamic model selection and configuration
- **Entity Extraction Engine**: `LLMGraphTransformer` integration with custom prompts
- **Schema Enforcement System**: Validation and constraint application
- **Response Processing Pipeline**: Parsing, cleaning, and validation
- **Rate Limiting & Resilience**: Error handling and retry mechanisms

### Data Flow

```
Chunk Data → LLM Model Selection → Prompt Construction → Entity Extraction → Response Validation → Graph Document Creation
```

## Multi-Provider LLM Architecture

### Provider Configuration System

**Location**: `backend/src/llm.py:47-212`

**Configuration Pattern**:
```python
def get_llm_model_name(llm):
    """Extract model name from LLM instance for configuration"""
    if hasattr(llm, 'model_name'):
        return llm.model_name.lower()
    elif hasattr(llm, 'model'):
        return llm.model.lower()
    return "unknown"

def get_llm(model: str):
    """Dynamic LLM provider selection and configuration"""
    model = model.lower().strip()
    env_key = f"LLM_MODEL_CONFIG_{model}"
    env_value = os.environ.get(env_key)
```

### Supported Providers

**OpenAI Integration**:
```python
if "openai" in model:
    if "o3-mini" in model:
        # Special handling for reasoning models
        llm = ChatOpenAI(
            model=model_name,
            api_key=api_key,
            temperature=0,
            timeout=None,
            max_tokens=None,
            max_completion_tokens=200000,  # High token limit for reasoning
            reasoning_effort="medium"       # Reasoning configuration
        )
    else:
        # Standard OpenAI models
        llm = ChatOpenAI(
            model=model_name,
            api_key=api_key,
            temperature=0
        )
```

**Google Vertex AI Integration**:
```python
elif "gemini" in model:
    llm = ChatVertexAI(
        model_name=model_name,
        temperature=0,
        convert_system_message_to_human=True,
        safety_settings={
            HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
        }
    )
```

**Azure OpenAI Integration**:
```python
elif "azure" in model:
    # Parse Azure configuration: model,endpoint,api_key,api_version
    parts = env_value.split(',')
    llm = AzureChatOpenAI(
        deployment_name=parts[0],
        azure_endpoint=parts[1],
        api_key=parts[2],
        api_version=parts[3],
        temperature=0,
        timeout=None
    )
```

**Anthropic Claude Integration**:
```python
elif "anthropic" in model:
    llm = ChatAnthropic(
        api_key=api_key,
        model=model_name,
        temperature=0,
        timeout=None
    )
```

**AWS Bedrock Integration**:
```python
elif "bedrock" in model:
    # Bedrock client initialization
    bedrock_runtime = boto3.client(
        service_name="bedrock-runtime",
        region_name="us-east-1"
    )
    
    llm = ChatBedrock(
        client=bedrock_runtime,
        model_id=model_name,
        model_kwargs={"temperature": 0}
    )
```

**Local Model Support (Ollama)**:
```python
elif "ollama" in model:
    # Parse configuration: model_name,base_url
    parts = env_value.split(',')
    llm = ChatOllama(
        model=parts[0],
        base_url=parts[1],
        temperature=0
    )
```

### Dynamic Model Configuration

**Environment Variable Pattern**:
```bash
# OpenAI Configuration
LLM_MODEL_CONFIG_openai_gpt_4o="gpt-4o-2024-11-20,openai_api_key"

# Azure Configuration  
LLM_MODEL_CONFIG_azure_ai_gpt_4o="gpt-4o,https://endpoint.azure.com/,api_key,2024-05-01-preview"

# Gemini Configuration
LLM_MODEL_CONFIG_gemini_1.5_pro="gemini-1.5-pro-002"

# Ollama Configuration
LLM_MODEL_CONFIG_ollama_llama3="llama3,http://localhost:11434"
```

## Entity Extraction Engine

### LLMGraphTransformer Integration

**Location**: `backend/src/llm.py:212-251`

**Core Implementation**:
```python
async def get_graph_from_llm(model, chunkId_chunkDoc_list, allowedNodes, allowedRelationship, chunks_to_combine, additional_instructions=""):
    # Chunk combination strategy
    combined_chunk_document_list = get_combined_chunks(chunkId_chunkDoc_list, chunks_to_combine)
    
    # LLM initialization
    llm = get_llm(model)
    
    # Tool usage detection for specific models
    model_name = get_llm_model_name(llm)
    TOOL_SUPPORTED_MODELS = {"qwen3", "deepseek"}
    ignore_tool_usage = not any(pattern in model_name for pattern in TOOL_SUPPORTED_MODELS)
    
    # Additional instructions sanitization
    additional_instructions = sanitize_additional_instruction(additional_instructions)
    
    # LLMGraphTransformer configuration
    llm_transformer = LLMGraphTransformer(
        llm=llm,
        node_properties=["description"],
        relationship_properties=["description"],
        allowed_nodes=allowedNodes,
        allowed_relationships=allowedRelationship,
        ignore_tool_usage=ignore_tool_usage,
        additional_instructions=ADDITIONAL_INSTRUCTIONS + additional_instructions
    )
    
    # Extract graph documents
    graph_documents = llm_transformer.convert_to_graph_documents(combined_chunk_document_list)
    return graph_documents
```

### Chunk Combination Strategy

**Implementation**:
```python
def get_combined_chunks(chunkId_chunkDoc_list, chunks_to_combine):
    combined_chunk_document_list = []
    
    if chunks_to_combine <= 1:
        # No combination - process individually
        for row in chunkId_chunkDoc_list:
            combined_chunk_document_list.append(row['chunk_doc'])
    else:
        # Combine chunks for context preservation
        for i in range(0, len(chunkId_chunkDoc_list), chunks_to_combine):
            chunks_to_process = chunkId_chunkDoc_list[i:i + chunks_to_combine]
            
            combined_content = ""
            combined_metadata = {}
            
            for chunk_data in chunks_to_process:
                combined_content += chunk_data['chunk_doc'].page_content + "\n\n"
                combined_metadata.update(chunk_data['chunk_doc'].metadata)
            
            combined_document = Document(
                page_content=combined_content.strip(),
                metadata=combined_metadata
            )
            combined_chunk_document_list.append(combined_document)
    
    return combined_chunk_document_list
```

## Prompt Engineering and Schema Enforcement

### Instruction Sanitization

**Location**: `backend/src/llm.py:26-46`

**Security Implementation**:
```python
def sanitize_additional_instruction(instruction: str) -> str:
    """Sanitize user-provided instructions to prevent injection attacks"""
    # Replace potentially dangerous characters
    instruction = instruction.replace("{", "[").replace("}", "]")
    
    # Block dangerous function calls
    injection_patterns = [
        r"os\.getenv\(",
        r"eval\(",
        r"exec\(",
        r"subprocess\.",
        r"import\s+os",
        r"from\s+os",
        r"__import__",
        r"globals\(",
        r"locals\(",
        r"vars\(",
        r"dir\(",
        r"open\(",
        r"file\(",
        r"input\(",
        r"raw_input\("
    ]
    
    for pattern in injection_patterns:
        instruction = re.sub(pattern, "[BLOCKED]", instruction, flags=re.IGNORECASE)
    
    # Limit instruction length
    max_length = 1000
    if len(instruction) > max_length:
        instruction = instruction[:max_length] + "..."
    
    return instruction
```

### Base Instructions

**System Prompt Configuration** (`shared/constants.py`):
```python
ADDITIONAL_INSTRUCTIONS = """
Your goal is to identify and categorize entities while ensuring that specific data 
types such as dates, numbers, revenues, and other non-entity information are not 
extracted as separate nodes. Instead, treat these as properties associated with the 
relevant entities.

Key Guidelines:
1. Extract meaningful entities that represent real-world concepts, people, places, 
   organizations, or objects.
2. Avoid creating nodes for:
   - Standalone dates, numbers, or measurements
   - Generic descriptive adjectives
   - Common verbs or actions
   - Articles, prepositions, or conjunctions
3. When encountering quantitative data, associate it as properties of relevant entities.
4. Focus on entities that contribute to the semantic understanding of the content.
5. Ensure relationships are meaningful and represent actual connections between entities.
"""
```

### Schema Validation

**Allowed Nodes/Relationships Validation**:
```python
def validate_schema_constraints(allowedNodes, allowedRelationship):
    """Validate schema constraints for entity extraction"""
    if allowedNodes:
        allowed_nodes = [node.strip() for node in allowedNodes.split(',') if node.strip()]
    else:
        allowed_nodes = []
    
    if allowedRelationship:
        items = [item.strip() for item in allowedRelationship.split(',') if item.strip()]
        if len(items) % 3 != 0:
            raise LLMGraphBuilderException("allowedRelationship must be a multiple of 3")
            
        # Validate relationship triplets
        for i in range(0, len(items), 3):
            source, relation, target = items[i:i + 3]
            if allowed_nodes and (source not in allowed_nodes or target not in allowed_nodes):
                raise LLMGraphBuilderException(
                    f"Invalid relationship: source '{source}' or target '{target}' not in allowedNodes"
                )
    
    return allowed_nodes, items if allowedRelationship else []
```

## Response Processing Pipeline

### Graph Document Cleaning

**Location**: `backend/src/shared/common_fn.py:111-129`

**Implementation**:
```python
def handle_backticks_nodes_relationship_id_type(graph_document_list):
    """Clean and validate graph documents from LLM responses"""
    cleaned_documents = []
    
    for graph_document in graph_document_list:
        cleaned_nodes = []
        cleaned_relationships = []
        
        # Node cleaning and validation
        for node in graph_document.nodes:
            if node.type and node.type.strip() and node.id and node.id.strip():
                # Remove backticks and clean formatting
                node.type = node.type.replace('`', '').strip()
                node.id = node.id.replace('`', '').strip()
                
                # Validate node content
                if len(node.type) > 0 and len(node.id) > 0:
                    cleaned_nodes.append(node)
        
        # Relationship cleaning and validation
        for relationship in graph_document.relationships:
            if (relationship.source and relationship.source.id and relationship.source.id.strip() and
                relationship.target and relationship.target.id and relationship.target.id.strip() and
                relationship.type and relationship.type.strip()):
                
                # Clean relationship formatting
                relationship.type = relationship.type.replace('`', '').strip()
                relationship.source.id = relationship.source.id.replace('`', '').strip()
                relationship.target.id = relationship.target.id.replace('`', '').strip()
                
                cleaned_relationships.append(relationship)
        
        # Create cleaned graph document
        if cleaned_nodes or cleaned_relationships:
            graph_document.nodes = cleaned_nodes
            graph_document.relationships = cleaned_relationships
            cleaned_documents.append(graph_document)
    
    return cleaned_documents
```

### Entity Deduplication

**Neo4j Storage with Deduplication**:
```python
def save_graphDocuments_in_neo4j(graph, graph_document_list, max_retries=3, delay=1):
    """Save graph documents with deduplication and retry logic"""
    retries = 0
    while retries < max_retries:
        try:
            # Neo4j's add_graph_documents handles entity deduplication
            graph.add_graph_documents(
                graph_document_list,
                baseEntityLabel=True,  # Add __Entity__ base label
                include_source=True    # Include source document relationships
            )
            return
            
        except TransientError as e:
            if "DeadlockDetected" in str(e):
                retries += 1
                logging.info(f"Deadlock detected. Retrying {retries}/{max_retries} in {delay} seconds...")
                time.sleep(delay)
                delay *= 2  # Exponential backoff
            else:
                raise
        except Exception as e:
            logging.error(f"Failed to save graph documents: {e}")
            raise
    
    raise LLMGraphBuilderException(f"Failed to save graph documents after {max_retries} retries")
```

## Rate Limiting and Resilience

### Retry Mechanisms

**Database Operation Retry**:
```python
def execute_graph_query(graph: Neo4jGraph, query, params=None, max_retries=3, delay=2):
    """Execute graph query with automatic retry for transient errors"""
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
        except Exception as e:
            if retries < max_retries - 1:
                retries += 1
                logging.warning(f"Query failed, retrying {retries}/{max_retries}: {e}")
                time.sleep(delay)
            else:
                raise
    
    raise Exception(f"Query failed after {max_retries} retries")
```

### LLM API Error Handling

**Provider-Specific Error Handling**:
```python
def handle_llm_api_error(e, model_name, retry_count=0):
    """Handle provider-specific API errors with appropriate retry strategies"""
    error_msg = str(e).lower()
    
    if "rate limit" in error_msg or "quota" in error_msg:
        # Rate limiting - exponential backoff
        wait_time = (2 ** retry_count) * 5  # 5, 10, 20, 40 seconds
        logging.warning(f"Rate limit hit for {model_name}, waiting {wait_time} seconds")
        time.sleep(wait_time)
        return True  # Retry
        
    elif "timeout" in error_msg or "connection" in error_msg:
        # Network issues - linear backoff
        wait_time = 10
        logging.warning(f"Network error for {model_name}, waiting {wait_time} seconds")
        time.sleep(wait_time)
        return True  # Retry
        
    elif "authentication" in error_msg or "unauthorized" in error_msg:
        # Auth errors - don't retry
        logging.error(f"Authentication error for {model_name}: {e}")
        return False
        
    else:
        # Unknown error - limited retry
        if retry_count < 2:
            logging.warning(f"Unknown error for {model_name}, retrying: {e}")
            time.sleep(5)
            return True
        return False
```

## Quality Control and Validation

### Response Quality Metrics

**Entity Quality Validation**:
```python
def validate_extracted_entities(graph_documents):
    """Validate quality of extracted entities and relationships"""
    quality_metrics = {
        'total_entities': 0,
        'total_relationships': 0,
        'empty_entities': 0,
        'invalid_relationships': 0,
        'quality_score': 0.0
    }
    
    for doc in graph_documents:
        quality_metrics['total_entities'] += len(doc.nodes)
        quality_metrics['total_relationships'] += len(doc.relationships)
        
        # Check for empty or invalid entities
        for node in doc.nodes:
            if not node.id or not node.type or len(node.id.strip()) < 2:
                quality_metrics['empty_entities'] += 1
                
        # Check for invalid relationships
        for rel in doc.relationships:
            if (not rel.source.id or not rel.target.id or not rel.type or
                rel.source.id == rel.target.id):  # Self-relationships
                quality_metrics['invalid_relationships'] += 1
    
    # Calculate quality score
    total_items = quality_metrics['total_entities'] + quality_metrics['total_relationships']
    invalid_items = quality_metrics['empty_entities'] + quality_metrics['invalid_relationships']
    
    if total_items > 0:
        quality_metrics['quality_score'] = 1.0 - (invalid_items / total_items)
    
    return quality_metrics
```

### Schema Compliance Checking

**Runtime Schema Validation**:
```python
def enforce_schema_compliance(graph_documents, allowed_nodes, allowed_relationships):
    """Enforce schema compliance on extracted entities"""
    compliant_documents = []
    
    for doc in graph_documents:
        compliant_nodes = []
        compliant_relationships = []
        
        # Filter nodes by allowed types
        for node in doc.nodes:
            if not allowed_nodes or node.type in allowed_nodes:
                compliant_nodes.append(node)
                
        # Filter relationships by allowed types
        for rel in doc.relationships:
            if not allowed_relationships or rel.type in allowed_relationships:
                # Ensure both source and target nodes are compliant
                source_compliant = any(n.id == rel.source.id for n in compliant_nodes)
                target_compliant = any(n.id == rel.target.id for n in compliant_nodes)
                
                if source_compliant and target_compliant:
                    compliant_relationships.append(rel)
        
        # Create compliant document
        if compliant_nodes or compliant_relationships:
            doc.nodes = compliant_nodes
            doc.relationships = compliant_relationships
            compliant_documents.append(doc)
    
    return compliant_documents
```

## Performance Optimizations

### Batch Processing

**Chunk Batching Strategy**:
```python
def process_chunks_in_batches(chunkId_chunkDoc_list, model, batch_size, allowedNodes, allowedRelationship):
    """Process chunks in optimized batches for performance"""
    all_graph_documents = []
    
    for i in range(0, len(chunkId_chunkDoc_list), batch_size):
        batch = chunkId_chunkDoc_list[i:i + batch_size]
        
        try:
            # Process batch
            batch_documents = await get_graph_from_llm(
                model, batch, allowedNodes, allowedRelationship, chunks_to_combine=1
            )
            all_graph_documents.extend(batch_documents)
            
        except Exception as e:
            logging.error(f"Batch processing failed for batch {i//batch_size + 1}: {e}")
            # Continue with next batch rather than failing entire operation
            continue
    
    return all_graph_documents
```

### Connection Pooling

**LLM Client Reuse**:
```python
# Global LLM client cache
_llm_cache = {}

def get_cached_llm(model: str):
    """Get or create cached LLM client for reuse"""
    if model not in _llm_cache:
        _llm_cache[model] = get_llm(model)
    return _llm_cache[model]
```

## Configuration Parameters

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `LLM_MODEL_CONFIG_{model}` | - | Model-specific configuration string |
| `OPENAI_API_KEY` | - | OpenAI API authentication |
| `AZURE_OPENAI_API_KEY` | - | Azure OpenAI API key |
| `ANTHROPIC_API_KEY` | - | Anthropic Claude API key |
| `GOOGLE_APPLICATION_CREDENTIALS` | - | Google Cloud credentials path |
| `AWS_REGION` | `us-east-1` | AWS region for Bedrock |
| `MAX_RETRIES` | `3` | Maximum retry attempts |
| `BATCH_SIZE` | `20` | Chunk processing batch size |

### Model-Specific Settings

**Token Limits**:
- OpenAI GPT-4: 128k context window
- Claude: 200k context window  
- Gemini: 1M context window
- O3-mini: 200k completion tokens

**Temperature Settings**:
- All models: `temperature=0` for consistent extraction
- Reasoning models: Additional reasoning effort configuration

## Integration Points

### Upstream Integration

**Chunking Pipeline**:
- Receives chunk-document pairs with metadata
- Processes chunks in configurable batch sizes
- Maintains chunk relationships and context

### Downstream Integration

**Knowledge Graph Construction**:
- Provides cleaned GraphDocument objects
- Ensures schema compliance
- Maintains entity-chunk relationships

### External Services

**LLM Provider APIs**:
- OpenAI GPT models
- Google Vertex AI
- Anthropic Claude
- AWS Bedrock
- Azure OpenAI
- Local models (Ollama)

## Monitoring and Metrics

### Performance Metrics

1. **Extraction Rate**: Entities/relationships per second
2. **API Latency**: Response times by provider
3. **Quality Scores**: Entity/relationship quality metrics
4. **Error Rates**: Failed extractions by error type
5. **Token Usage**: API consumption tracking

### Quality Metrics

1. **Schema Compliance**: Percentage of compliant entities
2. **Relationship Validity**: Valid relationship percentage
3. **Entity Coherence**: Semantic consistency scores
4. **Deduplication Efficiency**: Duplicate detection rates

### Logging Implementation

**Structured Logging**:
```python
extraction_log = {
    'model': model_name,
    'chunks_processed': len(chunkId_chunkDoc_list),
    'entities_extracted': total_entities,
    'relationships_extracted': total_relationships,
    'processing_time': elapsed_time,
    'quality_score': quality_metrics['quality_score'],
    'api_calls': api_call_count,
    'token_usage': token_count,
    'timestamp': datetime.now().isoformat()
}
logger.log_struct(extraction_log, "INFO")
```

This LLM integration pipeline provides robust, scalable entity extraction capabilities with comprehensive quality control, multi-provider support, and enterprise-grade reliability for knowledge graph construction.