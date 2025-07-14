# Document Processing Pipeline Technical Specification

## Overview

The document processing pipeline transforms raw documents from various sources into structured LangChain Document objects suitable for downstream knowledge graph construction. It handles format-specific extraction, encoding detection, and content preprocessing.

## Architecture

### Core Components

- **Document Loaders**: Format-specific extraction engines
- **Content Processors**: Text cleaning and preprocessing
- **Metadata Extractors**: Document property extraction
- **Encoding Handlers**: Character encoding detection and conversion

### Data Flow

```
Raw Document → Format Detection → Content Extraction → Encoding Processing → Metadata Enrichment → LangChain Document
```

## Document Loader Implementations

### Local File Processing

**Location**: `backend/src/document_sources/local_file.py`

**Primary Function**:
```python
def get_documents_from_file_by_path(merged_file_path, file_name)
```

**Format Detection Algorithm**:
```python
file_extension = file_name.split('.')[-1].lower()
if file_extension == 'pdf':
    # PDF processing with PyMuPDF
    pages = PyMuPDFLoader(merged_file_path).load()
elif file_extension in ['txt', 'csv', 'md']:
    # Text file processing with encoding detection
    pages = get_text_file_documents(merged_file_path, file_name)
else:
    # Unstructured document processing
    pages = UnstructuredFileLoader(merged_file_path).load()
```

### PDF Processing

**PyMuPDF Integration**:
```python
from langchain_community.document_loaders import PyMuPDFLoader

def process_pdf(file_path):
    pages = PyMuPDFLoader(file_path).load()
    for page in pages:
        # Metadata enrichment with page numbers
        page.metadata['page'] = page.metadata.get('page', 0)
        page.metadata['source'] = file_path
    return pages
```

**Features**:
- Page-level content extraction
- Automatic metadata preservation
- Text formatting retention
- Image and table handling

### Text File Processing

**Encoding Detection Implementation**:
```python
def get_text_file_documents(file_path, file_name):
    try:
        # Primary encoding attempt (UTF-8)
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read()
    except UnicodeDecodeError:
        # Fallback encoding detection
        with open(file_path, 'rb') as file:
            raw_data = file.read()
            detected_encoding = chardet.detect(raw_data)['encoding']
            content = raw_data.decode(detected_encoding or 'utf-8', errors='ignore')
    
    return [Document(page_content=content, metadata={'source': file_name})]
```

**Supported Formats**:
- Plain text (.txt)
- Comma-separated values (.csv)
- Markdown (.md)
- Custom text formats

### Unstructured Document Processing

**UnstructuredFileLoader Integration**:
```python
from langchain_community.document_loaders import UnstructuredFileLoader

def process_unstructured(file_path):
    try:
        loader = UnstructuredFileLoader(file_path)
        pages = loader.load()
        return pages
    except Exception as e:
        logging.error(f"Failed to process unstructured file: {e}")
        raise LLMGraphBuilderException(f"Unable to process file: {file_path}")
```

**Supported Formats**:
- Microsoft Office documents (.docx, .xlsx, .pptx)
- OpenDocument formats (.odt, .ods, .odp)
- Email formats (.eml, .msg)
- Rich text formats (.rtf)

## Cloud Storage Integration

### S3 Bucket Processing

**Location**: `backend/src/document_sources/s3_bucket.py`

**Core Functions**:
```python
def get_s3_files_info(source_url, aws_access_key_id, aws_secret_access_key):
    # S3 file metadata extraction
    
def get_documents_from_s3(source_url, aws_access_key_id, aws_secret_access_key):
    # Document content retrieval from S3
```

**Implementation Details**:
```python
def get_documents_from_s3(source_url, aws_access_key_id, aws_secret_access_key):
    bucket_name, prefix = extract_bucket_and_prefix(source_url)
    
    # S3 client initialization
    s3_client = boto3.client(
        's3',
        aws_access_key_id=aws_access_key_id,
        aws_secret_access_key=aws_secret_access_key
    )
    
    # Directory loader for S3 bucket
    loader = S3DirectoryLoader(
        bucket=bucket_name,
        prefix=prefix,
        aws_access_key_id=aws_access_key_id,
        aws_secret_access_key=aws_secret_access_key
    )
    
    pages = loader.load()
    return pages[0].metadata['source'], pages
```

**Features**:
- Automatic bucket and prefix extraction
- Recursive directory scanning
- Metadata preservation from S3 objects
- Error handling for access permissions

### Google Cloud Storage (GCS)

**Location**: `backend/src/document_sources/gcs_bucket.py`

**Core Functions**:
```python
def get_gcs_bucket_files_info(gcs_project_id, gcs_bucket_name, gcs_bucket_folder, credentials):
    # GCS file metadata enumeration
    
def get_documents_from_gcs(gcs_project_id, gcs_bucket_name, gcs_bucket_folder, gcs_blob_filename, access_token=None):
    # Document content retrieval from GCS
```

**Implementation**:
```python
def get_documents_from_gcs(gcs_project_id, gcs_bucket_name, gcs_bucket_folder, gcs_blob_filename, access_token=None):
    try:
        # GCS file loader initialization
        loader = GCSFileLoader(
            project_name=gcs_project_id,
            bucket=gcs_bucket_name,
            blob=os.path.join(gcs_bucket_folder, gcs_blob_filename)
        )
        
        pages = loader.load()
        return gcs_blob_filename, pages
        
    except Exception as e:
        logging.error(f"Error loading document from GCS: {e}")
        raise LLMGraphBuilderException(f"Unable to load file from GCS: {gcs_blob_filename}")
```

**Authentication Methods**:
- OAuth2 access tokens
- Service account credentials
- Application default credentials

## Web Content Processing

### Web Page Extraction

**Location**: `backend/src/document_sources/web_pages.py`

**Implementation**:
```python
def get_documents_from_web_page(source_url):
    try:
        # WebBaseLoader with SSL verification disabled
        pages = WebBaseLoader(source_url, verify_ssl=False).load()
        
        if not pages:
            raise LLMGraphBuilderException(f"Unable to read data from URL: {source_url}")
            
        # Content validation and metadata extraction
        for page in pages:
            page.metadata['source'] = source_url
            page.metadata['title'] = page.metadata.get('title', extract_title_from_url(source_url))
            
        return pages
        
    except Exception as e:
        logging.error(f"Web page extraction failed: {e}")
        raise LLMGraphBuilderException(f"Failed to process web page: {source_url}")
```

**Features**:
- HTML content extraction
- Automatic title detection
- Metadata enrichment
- SSL verification handling

### YouTube Transcript Processing

**Location**: `backend/src/document_sources/youtube.py`

**Core Functions**:
```python
def get_youtube_combined_transcript(video_id):
    # Transcript extraction with fallback languages
    
def get_documents_from_youtube(source_url):
    # Complete YouTube video processing
```

**Transcript Extraction Algorithm**:
```python
def get_youtube_combined_transcript(video_id):
    try:
        # Primary language attempt (English)
        transcript = YouTubeTranscriptApi.get_transcript(video_id, languages=['en'])
        
        # Transcript formatting with timestamps
        formatted_transcript = ""
        for item in transcript:
            timestamp = item['start']
            text = item['text']
            formatted_transcript += f"[{format_timestamp(timestamp)}] {text}\n"
            
        return formatted_transcript
        
    except TranscriptsDisabled:
        logging.info(f"Transcripts disabled for video {video_id}")
        return None
    except NoTranscriptFound:
        # Language fallback mechanism
        try:
            available_transcripts = YouTubeTranscriptApi.list_transcripts(video_id)
            transcript = available_transcripts.find_generated_transcript(['en']).fetch()
            return format_transcript(transcript)
        except:
            return None
```

**Features**:
- Multi-language support with fallback
- Timestamp preservation
- Automatic transcript generation detection
- Error handling for disabled transcripts

### Wikipedia Article Processing

**Location**: `backend/src/document_sources/wikipedia.py`

**Implementation**:
```python
def get_documents_from_Wikipedia(wiki_query, language='en'):
    try:
        # Wikipedia loader with language support
        loader = WikipediaLoader(
            query=wiki_query.strip(),
            lang=language,
            load_max_docs=1,
            load_all_available_meta=True
        )
        
        pages = loader.load()
        
        if not pages:
            raise LLMGraphBuilderException(f"No Wikipedia article found for: {wiki_query}")
            
        # Metadata enrichment
        for page in pages:
            page.metadata['language'] = language
            page.metadata['wiki_query'] = wiki_query
            
        return wiki_query.strip(), pages
        
    except Exception as e:
        logging.error(f"Wikipedia processing failed: {e}")
        raise LLMGraphBuilderException(f"Failed to process Wikipedia article: {wiki_query}")
```

**Features**:
- Multi-language Wikipedia support
- Comprehensive metadata extraction
- Article disambiguation handling
- Content validation and formatting

## Content Preprocessing

### Text Cleaning Pipeline

**Implementation** (`backend/src/main.py:516-524`):
```python
def clean_document_content(pages):
    bad_chars = ['"', "\n", "'"]
    for i in range(0, len(pages)):
        text = pages[i].page_content
        for j in bad_chars:
            if j == '\n':
                text = text.replace(j, ' ')  # Replace newlines with spaces
            else:
                text = text.replace(j, '')   # Remove quotes
        pages[i] = Document(page_content=str(text), metadata=pages[i].metadata)
    return pages
```

**Cleaning Operations**:
1. **Newline Normalization**: Convert newlines to spaces
2. **Quote Removal**: Strip problematic quotation marks
3. **Unicode Normalization**: Handle special characters
4. **Whitespace Cleanup**: Remove excessive spacing

### Metadata Enrichment

**Document Metadata Schema**:
```python
{
    'source': str,          # Original source identifier
    'page': int,            # Page number (for PDFs)
    'title': str,           # Document title
    'language': str,        # Content language
    'file_type': str,       # Document format
    'created_at': datetime, # Processing timestamp
    'file_size': int,       # Content size in bytes
    'encoding': str,        # Character encoding used
    'position': int,        # Sequential position in source
    'content_offset': int   # Character offset in original
}
```

## Error Handling and Validation

### Exception Hierarchy

**Document Processing Exceptions**:
```python
class DocumentProcessingException(LLMGraphBuilderException):
    """Document-specific processing errors"""
    pass

class EncodingDetectionException(DocumentProcessingException):
    """Character encoding detection failures"""
    pass

class ContentExtractionException(DocumentProcessingException):
    """Content extraction failures"""
    pass
```

### Validation Pipeline

**Content Validation**:
```python
def validate_document_content(pages):
    validated_pages = []
    for page in pages:
        if not page.page_content or len(page.page_content.strip()) == 0:
            logging.warning(f"Empty content detected in document: {page.metadata.get('source', 'unknown')}")
            continue
            
        if len(page.page_content) > MAX_CONTENT_LENGTH:
            logging.warning(f"Content length exceeds limit: {len(page.page_content)}")
            page.page_content = page.page_content[:MAX_CONTENT_LENGTH]
            
        validated_pages.append(page)
    
    return validated_pages
```

**Validation Rules**:
1. **Content Length**: Maximum content size enforcement
2. **Empty Content**: Detection and filtering of empty pages
3. **Encoding Validation**: Character encoding consistency checks
4. **Metadata Completeness**: Required metadata field validation

## Performance Optimizations

### Memory Management

**Streaming Processing**:
- Large documents processed in chunks
- Memory-efficient loaders for cloud storage
- Garbage collection optimization

**Concurrent Processing**:
- Parallel document loading for batch operations
- Asynchronous I/O for cloud storage access
- Connection pooling for database operations

### Caching Strategies

**Content Caching**:
- Document content caching for repeated access
- Metadata caching for quick lookups
- Encoding detection result caching

## Configuration Parameters

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `MAX_CONTENT_LENGTH` | `1000000` | Maximum content length per document |
| `DEFAULT_ENCODING` | `utf-8` | Default character encoding |
| `YOUTUBE_TRANSCRIPT_PROXY` | - | Proxy for YouTube transcript API |
| `WEB_SCRAPING_TIMEOUT` | `30` | Web page loading timeout |

### Format-Specific Settings

**PDF Processing**:
- Page extraction limits
- Image handling configuration
- Text extraction quality settings

**Text Files**:
- Encoding detection thresholds
- Fallback encoding priorities
- Content validation rules

## Integration Points

### Upstream Integration

**File Upload Pipeline**:
- Receives file paths and metadata from upload system
- Validates file accessibility and permissions
- Reports processing status back to upload controller

### Downstream Integration

**Chunking Pipeline**:
- Provides structured Document objects
- Ensures consistent metadata format
- Validates content readiness for chunking

### External Services

**Cloud Storage APIs**:
- AWS S3 SDK integration
- Google Cloud Storage client libraries
- Authentication and credential management

**Web Services**:
- YouTube Transcript API
- Wikipedia API
- Web scraping libraries

## Monitoring and Logging

### Processing Metrics

1. **Document Count**: Number of documents processed per source type
2. **Processing Time**: Average time per document type
3. **Error Rate**: Percentage of failed document extractions
4. **Content Size**: Average and maximum content sizes

### Logging Implementation

**Structured Logging Example**:
```python
logging_data = {
    'source_type': source_type,
    'document_count': len(pages),
    'processing_time': elapsed_time,
    'content_size': sum(len(p.page_content) for p in pages),
    'metadata_fields': list(pages[0].metadata.keys()) if pages else [],
    'timestamp': datetime.now().isoformat()
}
logger.log_struct(logging_data, "INFO")
```

This document processing pipeline provides robust, scalable document ingestion capabilities that handle diverse source types while maintaining content quality and metadata integrity essential for downstream knowledge graph construction.