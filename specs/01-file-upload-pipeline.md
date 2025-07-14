# File Upload Pipeline Technical Specification

## Overview

The file upload pipeline handles ingestion of documents from multiple sources with support for chunked uploads, metadata extraction, and distributed storage strategies. It provides the foundation for the knowledge graph construction process.

## Architecture

### Core Components

- **Upload Controller**: `/upload` endpoint in `backend/score.py:563-591`
- **Upload Handler**: `upload_file()` in `backend/src/main.py:621-665`
- **Source Node Factory**: Creates initial Document nodes in Neo4j
- **Storage Manager**: Handles local filesystem or GCS bucket storage

### Data Flow

```
File Upload → Chunk Assembly → Metadata Extraction → Source Node Creation → Storage Finalization
```

## Chunked Upload Mechanism

### Implementation Details

**Location**: `backend/src/main.py:621-665`

**Function Signature**:
```python
def upload_file(graph, model, chunk, chunk_number: int, total_chunks: int, originalname, uri, chunk_dir, merged_dir)
```

**Process Flow**:

1. **Chunk Validation**:
   - Validates chunk number sequence (1 to total_chunks)
   - Ensures filename security via `sanitize_filename()`
   - Validates file path via `validate_file_path()`

2. **Storage Decision**:
   ```python
   gcs_file_cache = os.environ.get('GCS_FILE_CACHE')
   if gcs_file_cache == 'True':
       upload_file_to_gcs(chunk, chunk_number, originalname, BUCKET_UPLOAD, folder_name)
   else:
       # Local filesystem storage
   ```

3. **Chunk Assembly**:
   - **Local**: `merge_chunks_local()` - Sequential file concatenation
   - **GCS**: `merge_file_gcs()` - Cloud-based assembly

### Chunk Assembly Algorithms

**Local Assembly** (`merge_chunks_local()` lines 601-617):
```python
def merge_chunks_local(file_name, total_chunks, chunk_dir, merged_dir):
    merged_file_path = os.path.join(merged_dir, file_name)
    with open(merged_file_path, "wb") as write_stream:
        for i in range(1, total_chunks + 1):
            chunk_file_path = os.path.join(chunk_dir, f"{file_name}_part_{i}")
            with open(chunk_file_path, "rb") as chunk_file:
                shutil.copyfileobj(chunk_file, write_stream)
            os.unlink(chunk_file_path)  # Cleanup individual chunks
```

**Key Features**:
- Sequential chunk processing with automatic cleanup
- Atomic file operations with error handling
- File size calculation for metadata

## Multi-Source Support

### Source Types and Handlers

| Source Type | Handler Function | Location | Description |
|-------------|------------------|----------|-------------|
| Local Files | `get_documents_from_file_by_path()` | `document_sources/local_file.py` | Direct file system access |
| S3 Buckets | `create_source_node_graph_url_s3()` | `main.py:40-76` | AWS S3 integration |
| GCS Buckets | `create_source_node_graph_url_gcs()` | `main.py:78-115` | Google Cloud Storage |
| Web URLs | `create_source_node_graph_web_url()` | `main.py:117-159` | Web scraping |
| YouTube | `create_source_node_graph_url_youtube()` | `main.py:161-194` | Video transcript extraction |
| Wikipedia | `create_source_node_graph_url_wikipedia()` | `main.py:196-228` | Wikipedia article processing |

### Source Node Creation Pattern

**Common Source Node Structure**:
```python
obj_source_node = sourceNode()
obj_source_node.file_name = filename
obj_source_node.file_type = file_extension
obj_source_node.file_size = file_size
obj_source_node.file_source = source_type
obj_source_node.model = model
obj_source_node.created_at = datetime.now()
obj_source_node.status = "New"  # Initial status
```

**Node Counters Initialization**:
```python
obj_source_node.chunkNodeCount = 0
obj_source_node.chunkRelCount = 0
obj_source_node.entityNodeCount = 0
obj_source_node.entityEntityRelCount = 0
obj_source_node.communityNodeCount = 0
obj_source_node.communityRelCount = 0
```

## Security and Validation

### Filename Sanitization

**Implementation** (`backend/score.py:44-51`):
```python
def sanitize_filename(filename):
    filename = os.path.basename(filename)
    filename = os.path.normpath(filename)
    return filename
```

### Path Validation

**Implementation** (`backend/score.py:53-63`):
```python
def validate_file_path(directory, filename):
    file_path = os.path.join(directory, filename)
    abs_directory = os.path.abspath(directory)
    abs_file_path = os.path.abspath(file_path)
    if not abs_file_path.startswith(abs_directory):
        raise ValueError("Invalid file path")
    return abs_file_path
```

**Security Features**:
- Directory traversal prevention
- Path normalization
- Absolute path validation

## Storage Strategies

### Local Filesystem Storage

**Configuration**:
```python
CHUNK_DIR = os.path.join(os.path.dirname(__file__), "chunks")
MERGED_DIR = os.path.join(os.path.dirname(__file__), "merged_files")
```

**Features**:
- Automatic directory creation
- Sequential chunk processing
- Immediate cleanup after assembly

### Google Cloud Storage (GCS)

**Configuration**:
```python
gcs_file_cache = os.environ.get('GCS_FILE_CACHE', 'False')
```

**Features**:
- Distributed chunk storage
- Parallel upload capabilities
- Folder-based organization with hashed names
- Automatic cleanup and lifecycle management

### Folder Name Generation

**Implementation**:
```python
def create_gcs_bucket_folder_name_hashed(uri, file_name):
    # Creates deterministic folder names based on URI and filename
    combined = f"{uri}_{file_name}"
    return hashlib.md5(combined.encode()).hexdigest()
```

## Error Handling and Recovery

### Exception Types

**Primary Exception**:
```python
class LLMGraphBuilderException(Exception):
    def __init__(self, message):
        self.message = message
        super().__init__(message)
```

### Error Scenarios and Handling

1. **Upload Failures**:
   - Automatic cleanup of partial chunks
   - Database status update to "Failed"
   - Error message logging with details

2. **Storage Failures**:
   - Retry mechanism for transient errors
   - Fallback to alternative storage strategy
   - Comprehensive error logging

3. **Validation Failures**:
   - Early termination with cleanup
   - Clear error messages for client
   - Security event logging

### Recovery Procedures

**Failed File Processing** (`main.py:759-768`):
```python
def failed_file_process(uri, file_name, merged_file_path):
    gcs_file_cache = os.environ.get('GCS_FILE_CACHE')
    if gcs_file_cache == 'True':
        folder_name = create_gcs_bucket_folder_name_hashed(uri, file_name)
        copy_failed_file(BUCKET_UPLOAD, BUCKET_FAILED_FILE, folder_name, file_name)
        delete_file_from_gcs(BUCKET_UPLOAD, folder_name, file_name)
    else:
        delete_uploaded_local_file(merged_file_path, file_name)
```

## Performance Considerations

### Chunked Upload Benefits

1. **Memory Efficiency**: Prevents large file memory consumption
2. **Network Resilience**: Allows resumable uploads
3. **Parallel Processing**: Enables concurrent chunk handling
4. **Progress Tracking**: Granular upload progress reporting

### Optimization Strategies

1. **Configurable Chunk Sizes**: Via `VITE_CHUNK_SIZE` environment variable
2. **Parallel Uploads**: Multiple chunks processed simultaneously
3. **Compression**: Automatic compression for cloud storage
4. **Connection Pooling**: Reused database connections

## Configuration Parameters

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `GCS_FILE_CACHE` | `False` | Enable GCS storage backend |
| `VITE_CHUNK_SIZE` | `5242880` | Chunk size in bytes (5MB) |
| `BUCKET_UPLOAD` | - | GCS upload bucket name |
| `BUCKET_FAILED_FILE` | - | GCS failed files bucket |
| `PROJECT_ID` | - | GCS project identifier |

### File Size Limits

**Large File Handling**:
- Default chunk size: 5MB
- Maximum file size: Configurable via environment
- Automatic validation and rejection of oversized files

## Integration Points

### Database Integration

**Neo4j Operations**:
- Source node creation via `graphDBdataAccess.create_source_node()`
- Status tracking and updates
- Metadata storage and indexing

### Frontend Integration

**Upload Progress Tracking**:
- Real-time chunk upload status
- Progress percentage calculation
- Error state communication

### Downstream Processing

**Extraction Pipeline Trigger**:
- Status change from "New" to "Ready for Processing"
- Metadata availability for document loaders
- File path resolution for processing engines

## Monitoring and Logging

### Key Metrics

1. **Upload Performance**: Chunk processing times
2. **Storage Utilization**: Disk/cloud usage tracking
3. **Error Rates**: Failed upload percentages
4. **File Type Distribution**: Analysis of uploaded content types

### Logging Implementation

**Structured Logging**:
```python
json_obj = {
    'api_name': 'upload',
    'db_url': uri,
    'userName': userName,
    'database': database,
    'chunkNumber': chunkNumber,
    'totalChunks': totalChunks,
    'original_file_name': originalname,
    'model': model,
    'logging_time': formatted_time(datetime.now(timezone.utc)),
    'elapsed_api_time': f'{elapsed_time:.2f}',
    'email': email
}
logger.log_struct(json_obj, "INFO")
```

This upload pipeline provides a robust, scalable foundation for ingesting diverse document types while maintaining security, performance, and reliability standards essential for enterprise knowledge graph construction.