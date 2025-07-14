# Error Handling and Monitoring Technical Specification

## Overview

The error handling and monitoring system provides comprehensive fault tolerance, observability, and recovery mechanisms across all pipeline components. It implements structured exception hierarchies, intelligent retry strategies, detailed logging, and performance monitoring to ensure reliable operation in production environments.

## Architecture

### Core Components

- **Exception Hierarchy**: Custom exception types with specific handling strategies
- **Retry Engine**: Intelligent retry mechanisms with exponential backoff
- **Status Tracking System**: Comprehensive progress and state management
- **Logging Infrastructure**: Structured logging with context preservation
- **Monitoring Dashboard**: Real-time metrics and alerting
- **Recovery Procedures**: Automated and manual recovery workflows

### Error Handling Flow

```
Error Detection → Classification → Retry Logic → Recovery Action → Monitoring Update → User Notification
```

## Exception Hierarchy

### Custom Exception System

**Location**: `backend/src/shared/llm_graph_builder_exception.py`

**Base Exception Class**:
```python
class LLMGraphBuilderException(Exception):
    """Base exception for all LLM Graph Builder specific errors"""
    
    def __init__(self, message, error_code=None, context=None, recoverable=True):
        self.message = message
        self.error_code = error_code
        self.context = context or {}
        self.recoverable = recoverable
        self.timestamp = datetime.now(timezone.utc)
        super().__init__(message)
    
    def to_dict(self):
        """Convert exception to structured dictionary for logging"""
        return {
            'exception_type': self.__class__.__name__,
            'message': self.message,
            'error_code': self.error_code,
            'context': self.context,
            'recoverable': self.recoverable,
            'timestamp': self.timestamp.isoformat()
        }
```

### Specialized Exception Types

**Pipeline-Specific Exceptions**:
```python
class DocumentProcessingException(LLMGraphBuilderException):
    """Errors during document processing"""
    pass

class ChunkingException(LLMGraphBuilderException):
    """Errors during document chunking"""
    pass

class EmbeddingGenerationException(LLMGraphBuilderException):
    """Errors during embedding generation"""
    pass

class LLMExtractionException(LLMGraphBuilderException):
    """Errors during LLM entity extraction"""
    pass

class GraphConstructionException(LLMGraphBuilderException):
    """Errors during graph construction"""
    pass

class QueryProcessingException(LLMGraphBuilderException):
    """Errors during query processing"""
    pass

class DatabaseConnectionException(LLMGraphBuilderException):
    """Database connectivity issues"""
    def __init__(self, message, connection_string=None):
        super().__init__(message, recoverable=True)
        self.context['connection_string'] = connection_string

class ExternalAPIException(LLMGraphBuilderException):
    """External API service failures"""
    def __init__(self, message, service_name=None, status_code=None):
        super().__init__(message, recoverable=True)
        self.context['service_name'] = service_name
        self.context['status_code'] = status_code
```

## Retry Mechanisms

### Database Operation Retry

**Location**: `backend/src/shared/common_fn.py:131-144`

**Deadlock Detection and Retry**:
```python
def execute_graph_query(graph: Neo4jGraph, query, params=None, max_retries=3, delay=2):
    """Execute graph query with automatic retry for transient errors"""
    retries = 0
    last_exception = None
    
    while retries < max_retries:
        try:
            return graph.query(query, params)
            
        except TransientError as e:
            last_exception = e
            if "DeadlockDetected" in str(e):
                retries += 1
                wait_time = delay * (2 ** (retries - 1))  # Exponential backoff
                logging.info(f"Deadlock detected. Retrying {retries}/{max_retries} in {wait_time} seconds...")
                time.sleep(wait_time)
            else:
                # Non-deadlock transient error - immediate retry
                retries += 1
                logging.warning(f"Transient error: {e}. Retrying {retries}/{max_retries}")
                time.sleep(1)
                
        except Exception as e:
            # Non-transient error - handle based on error type
            if is_recoverable_error(e) and retries < max_retries - 1:
                retries += 1
                logging.warning(f"Recoverable error: {e}. Retrying {retries}/{max_retries}")
                time.sleep(delay)
            else:
                raise GraphConstructionException(f"Query execution failed: {e}", context={'query': query, 'params': params})
    
    # All retries exhausted
    raise GraphConstructionException(f"Query failed after {max_retries} retries: {last_exception}")
```

### LLM API Retry Strategy

**Implementation**:
```python
class LLMAPIRetryHandler:
    """Handles retries for LLM API calls with provider-specific strategies"""
    
    def __init__(self, max_retries=3, base_delay=1):
        self.max_retries = max_retries
        self.base_delay = base_delay
        
    def execute_with_retry(self, api_call, provider, *args, **kwargs):
        """Execute API call with provider-specific retry logic"""
        for attempt in range(self.max_retries + 1):
            try:
                return api_call(*args, **kwargs)
                
            except Exception as e:
                if attempt == self.max_retries:
                    raise LLMExtractionException(
                        f"LLM API call failed after {self.max_retries} retries: {e}",
                        context={'provider': provider, 'attempt': attempt}
                    )
                
                retry_delay = self._calculate_retry_delay(e, provider, attempt)
                if retry_delay is None:
                    # Non-recoverable error
                    raise LLMExtractionException(f"Non-recoverable LLM error: {e}", recoverable=False)
                
                logging.warning(f"LLM API error (attempt {attempt + 1}): {e}. Retrying in {retry_delay}s")
                time.sleep(retry_delay)
    
    def _calculate_retry_delay(self, error, provider, attempt):
        """Calculate retry delay based on error type and provider"""
        error_str = str(error).lower()
        
        if "rate limit" in error_str or "quota" in error_str:
            # Rate limiting - exponential backoff with jitter
            delay = self.base_delay * (2 ** attempt) + random.uniform(0, 1)
            return min(delay, 60)  # Cap at 1 minute
            
        elif "timeout" in error_str or "connection" in error_str:
            # Network issues - linear backoff
            return self.base_delay * 2
            
        elif "authentication" in error_str or "unauthorized" in error_str:
            # Auth errors - don't retry
            return None
            
        elif "invalid" in error_str or "bad request" in error_str:
            # Client errors - don't retry
            return None
            
        else:
            # Unknown error - conservative retry
            return self.base_delay * (attempt + 1)
```

### File Processing Retry

**Multi-Level Retry Strategy**:
```python
class FileProcessingRetryManager:
    """Manages retry strategies for file processing operations"""
    
    RETRY_CONDITIONS = {
        'START_FROM_BEGINNING': 'restart_processing',
        'DELETE_ENTITIES_AND_START_FROM_BEGINNING': 'clean_restart',
        'START_FROM_LAST_PROCESSED_POSITION': 'resume_processing'
    }
    
    def handle_processing_failure(self, file_name, error, graph):
        """Handle file processing failures with appropriate retry strategy"""
        
        error_analysis = self._analyze_error(error)
        retry_strategy = self._determine_retry_strategy(error_analysis)
        
        if retry_strategy == 'clean_restart':
            self._clean_restart_processing(file_name, graph)
        elif retry_strategy == 'resume_processing':
            self._resume_processing(file_name, graph)
        elif retry_strategy == 'restart_processing':
            self._restart_processing(file_name, graph)
        else:
            # Mark as failed
            self._mark_processing_failed(file_name, error, graph)
    
    def _analyze_error(self, error):
        """Analyze error to determine appropriate recovery strategy"""
        if isinstance(error, ChunkingException):
            return {'type': 'chunking', 'severity': 'medium', 'recoverable': True}
        elif isinstance(error, EmbeddingGenerationException):
            return {'type': 'embedding', 'severity': 'low', 'recoverable': True}
        elif isinstance(error, LLMExtractionException):
            return {'type': 'llm', 'severity': 'high', 'recoverable': error.recoverable}
        elif isinstance(error, DatabaseConnectionException):
            return {'type': 'database', 'severity': 'critical', 'recoverable': True}
        else:
            return {'type': 'unknown', 'severity': 'high', 'recoverable': False}
```

## Status Tracking System

### Document Processing Status

**Location**: `backend/src/graphDB_dataAccess.py`

**Status Management**:
```python
class DocumentStatusManager:
    """Manages document processing status throughout the pipeline"""
    
    STATUS_TYPES = {
        'New': 'Document uploaded, ready for processing',
        'Processing': 'Currently being processed',
        'Completed': 'Successfully processed',
        'Failed': 'Processing failed',
        'Cancelled': 'Processing cancelled by user',
        'Ready to Reprocess': 'Marked for reprocessing'
    }
    
    def update_status(self, file_name, status, error_message=None, progress_info=None):
        """Update document processing status with context"""
        
        status_update = {
            'fileName': file_name,
            'status': status,
            'updated_at': datetime.now(timezone.utc),
            'progress_info': progress_info or {}
        }
        
        if error_message:
            status_update['error_message'] = error_message
            status_update['error_timestamp'] = datetime.now(timezone.utc)
        
        # Update database
        update_query = """
        MATCH (d:Document {fileName: $fileName})
        SET d.status = $status,
            d.updated_at = $updated_at,
            d.error_message = $error_message,
            d.progress_info = $progress_info
        RETURN d
        """
        
        execute_graph_query(self.graph, update_query, status_update)
        
        # Log status change
        self._log_status_change(file_name, status, error_message, progress_info)
        
        # Trigger notifications if needed
        self._trigger_status_notifications(file_name, status)
```

### Real-Time Progress Tracking

**Server-Sent Events Implementation**:
```python
@app.get("/update_extract_status/{file_name}")
async def update_extract_status(request: Request, file_name: str, uri: str = None, userName: str = None, password: str = None, database: str = None):
    """Provide real-time status updates via Server-Sent Events"""
    
    async def generate():
        last_status = None
        consecutive_errors = 0
        max_errors = 5
        
        while True:
            try:
                if await request.is_disconnected():
                    logging.info(f"SSE Client disconnected for {file_name}")
                    break
                
                # Get current status
                current_status = get_document_status(file_name, uri, userName, password, database)
                
                # Only send updates when status changes
                if current_status != last_status:
                    status_data = {
                        'fileName': file_name,
                        'status': current_status.get('status', 'Unknown'),
                        'processingTime': current_status.get('processingTime', 0),
                        'nodeCount': current_status.get('nodeCount', 0),
                        'relationshipCount': current_status.get('relationshipCount', 0),
                        'processed_chunk': current_status.get('processed_chunk', 0),
                        'total_chunks': current_status.get('total_chunks', 0),
                        'timestamp': datetime.now(timezone.utc).isoformat()
                    }
                    
                    yield f"data: {json.dumps(status_data)}\n\n"
                    last_status = current_status
                    consecutive_errors = 0
                
                # Terminal status - close connection
                if current_status.get('status') in ['Completed', 'Failed', 'Cancelled']:
                    break
                
                await asyncio.sleep(2)  # Poll interval
                
            except Exception as e:
                consecutive_errors += 1
                logging.error(f"SSE error for {file_name}: {e}")
                
                if consecutive_errors >= max_errors:
                    error_data = {'error': 'Max errors reached', 'fileName': file_name}
                    yield f"data: {json.dumps(error_data)}\n\n"
                    break
                
                await asyncio.sleep(5)  # Longer delay on errors
    
    return EventSourceResponse(generate(), ping=60)
```

## Logging Infrastructure

### Structured Logging Implementation

**Location**: `backend/src/logger.py`

**Custom Logger Class**:
```python
class CustomLogger:
    """Custom logger with structured logging capabilities"""
    
    def __init__(self):
        self.logger = logging.getLogger('llm-graph-builder')
        self.setup_logger()
        
    def setup_logger(self):
        """Configure structured logging"""
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)
        self.logger.setLevel(logging.INFO)
        
    def log_struct(self, data, level="INFO"):
        """Log structured data with context preservation"""
        
        # Add system context
        enriched_data = {
            **data,
            'service': 'llm-graph-builder',
            'version': get_application_version(),
            'environment': os.environ.get('ENVIRONMENT', 'development'),
            'instance_id': get_instance_id(),
            'correlation_id': get_correlation_id()
        }
        
        # Log with appropriate level
        log_method = getattr(self.logger, level.lower(), self.logger.info)
        log_method(json.dumps(enriched_data, default=str))
        
        # Send to external monitoring if configured
        self._send_to_monitoring(enriched_data, level)
    
    def _send_to_monitoring(self, data, level):
        """Send logs to external monitoring systems"""
        try:
            # Google Cloud Logging
            if os.environ.get('GCP_LOG_METRICS_ENABLED', 'False').lower() == 'true':
                self._send_to_gcp_logging(data, level)
                
            # Other monitoring systems can be added here
            
        except Exception as e:
            # Don't fail on monitoring errors
            self.logger.warning(f"Failed to send logs to monitoring: {e}")
```

### Performance Metrics Logging

**Comprehensive Performance Tracking**:
```python
class PerformanceTracker:
    """Track and log performance metrics across all pipelines"""
    
    def __init__(self):
        self.metrics = {}
        self.timers = {}
        
    def start_timer(self, operation_name, context=None):
        """Start timing an operation"""
        timer_id = f"{operation_name}_{id(context) if context else 'global'}"
        self.timers[timer_id] = {
            'start_time': time.time(),
            'operation': operation_name,
            'context': context or {}
        }
        return timer_id
    
    def end_timer(self, timer_id, additional_metrics=None):
        """End timing and log performance metrics"""
        if timer_id not in self.timers:
            logging.warning(f"Timer {timer_id} not found")
            return
            
        timer_data = self.timers.pop(timer_id)
        elapsed_time = time.time() - timer_data['start_time']
        
        performance_log = {
            'operation': timer_data['operation'],
            'elapsed_time': elapsed_time,
            'context': timer_data['context'],
            'timestamp': datetime.now(timezone.utc).isoformat()
        }
        
        if additional_metrics:
            performance_log.update(additional_metrics)
            
        # Calculate performance score
        performance_log['performance_score'] = self._calculate_performance_score(
            timer_data['operation'], elapsed_time, additional_metrics
        )
        
        logger.log_struct(performance_log, "INFO")
        
        # Update metrics aggregation
        self._update_aggregated_metrics(timer_data['operation'], elapsed_time)
    
    def _calculate_performance_score(self, operation, elapsed_time, metrics):
        """Calculate performance score based on operation type and metrics"""
        
        # Operation-specific performance thresholds
        thresholds = {
            'document_processing': {'excellent': 5, 'good': 15, 'acceptable': 30},
            'chunking': {'excellent': 2, 'good': 5, 'acceptable': 10},
            'embedding_generation': {'excellent': 10, 'good': 30, 'acceptable': 60},
            'llm_extraction': {'excellent': 30, 'good': 90, 'acceptable': 180},
            'graph_construction': {'excellent': 5, 'good': 15, 'acceptable': 30},
            'query_processing': {'excellent': 1, 'good': 3, 'acceptable': 5}
        }
        
        threshold = thresholds.get(operation, {'excellent': 10, 'good': 30, 'acceptable': 60})
        
        if elapsed_time <= threshold['excellent']:
            return 'excellent'
        elif elapsed_time <= threshold['good']:
            return 'good'
        elif elapsed_time <= threshold['acceptable']:
            return 'acceptable'
        else:
            return 'poor'
```

## Recovery Procedures

### Automated Recovery Workflows

**Self-Healing Mechanisms**:
```python
class AutoRecoveryManager:
    """Manages automated recovery procedures"""
    
    def __init__(self, graph):
        self.graph = graph
        self.recovery_strategies = {
            'database_connection_lost': self._recover_database_connection,
            'llm_api_quota_exceeded': self._handle_quota_exhaustion,
            'embedding_service_down': self._fallback_embedding_service,
            'disk_space_low': self._cleanup_temporary_files,
            'memory_pressure': self._trigger_garbage_collection
        }
    
    def attempt_recovery(self, error_type, context):
        """Attempt automated recovery based on error type"""
        
        recovery_function = self.recovery_strategies.get(error_type)
        if not recovery_function:
            logging.warning(f"No recovery strategy for error type: {error_type}")
            return False
            
        try:
            recovery_result = recovery_function(context)
            
            # Log recovery attempt
            recovery_log = {
                'error_type': error_type,
                'recovery_strategy': recovery_function.__name__,
                'success': recovery_result,
                'context': context,
                'timestamp': datetime.now(timezone.utc).isoformat()
            }
            logger.log_struct(recovery_log, "INFO")
            
            return recovery_result
            
        except Exception as e:
            logging.error(f"Recovery attempt failed for {error_type}: {e}")
            return False
    
    def _recover_database_connection(self, context):
        """Attempt to recover database connection"""
        try:
            # Close existing connections
            if hasattr(self.graph, '_driver') and self.graph._driver:
                self.graph._driver.close()
            
            # Recreate connection with backoff
            for attempt in range(3):
                try:
                    self.graph = create_graph_database_connection(
                        context.get('uri'),
                        context.get('username'),
                        context.get('password'),
                        context.get('database')
                    )
                    return True
                except Exception as e:
                    time.sleep(2 ** attempt)
                    
            return False
            
        except Exception:
            return False
    
    def _handle_quota_exhaustion(self, context):
        """Handle LLM API quota exhaustion"""
        # Switch to alternative model or queue for later processing
        alternative_models = context.get('alternative_models', [])
        
        for alt_model in alternative_models:
            try:
                # Test alternative model
                test_llm = get_llm(alt_model)
                test_response = test_llm.invoke("Test query")
                
                # Update context to use alternative model
                context['active_model'] = alt_model
                logging.info(f"Switched to alternative model: {alt_model}")
                return True
                
            except Exception:
                continue
                
        # Queue for later processing if no alternatives work
        self._queue_for_later_processing(context)
        return False
```

### Manual Recovery Procedures

**Recovery Procedure Documentation**:
```python
class ManualRecoveryProcedures:
    """Documentation and helpers for manual recovery procedures"""
    
    RECOVERY_PROCEDURES = {
        'corrupted_graph_data': {
            'description': 'Graph database contains corrupted or inconsistent data',
            'steps': [
                '1. Identify corrupted documents using status queries',
                '2. Stop processing for affected documents',
                '3. Delete corrupted entities and relationships',
                '4. Restart processing from beginning with DELETE_ENTITIES_AND_START_FROM_BEGINNING',
                '5. Monitor processing progress carefully',
                '6. Validate graph consistency after completion'
            ],
            'queries': [
                'MATCH (d:Document {status: "Failed"}) RETURN d.fileName, d.error_message',
                'MATCH (d:Document)-[:PART_OF]-(c:Chunk) WHERE c.text IS NULL RETURN d.fileName'
            ]
        },
        
        'embedding_dimension_mismatch': {
            'description': 'Embedding dimensions do not match vector index',
            'steps': [
                '1. Identify current vector index dimensions',
                '2. Drop existing vector index',
                '3. Recreate index with correct dimensions',
                '4. Regenerate embeddings for all chunks',
                '5. Update configuration to prevent recurrence'
            ],
            'queries': [
                'SHOW INDEXES YIELD name, type, entityType, properties WHERE type = "VECTOR"',
                'DROP INDEX vector_index_name',
                'CREATE VECTOR INDEX vector FOR (c:Chunk) ON c.embedding OPTIONS {indexConfig: {`vector.dimensions`: 1536}}'
            ]
        },
        
        'community_detection_failure': {
            'description': 'Community detection algorithm failed or produced poor results',
            'steps': [
                '1. Check graph connectivity and entity relationships',
                '2. Verify similarity relationships exist',
                '3. Clear existing community data',
                '4. Reconfigure Leiden algorithm parameters',
                '5. Re-run community detection',
                '6. Validate community structure quality'
            ],
            'queries': [
                'MATCH (c:__Community__) DETACH DELETE c',
                'MATCH ()-[r:SIMILAR]-() RETURN count(r) as similarity_count',
                'MATCH (e:__Entity__) WHERE size((e)-[:SIMILAR]-()) > 0 RETURN count(e) as connected_entities'
            ]
        }
    }
    
    def get_recovery_procedure(self, issue_type):
        """Get manual recovery procedure for specific issue"""
        return self.RECOVERY_PROCEDURES.get(issue_type)
    
    def validate_recovery_completion(self, issue_type, graph):
        """Validate that recovery procedure was successful"""
        
        validation_queries = {
            'corrupted_graph_data': [
                'MATCH (d:Document) WHERE d.status = "Failed" RETURN count(d) as failed_docs',
                'MATCH (c:Chunk) WHERE c.text IS NULL RETURN count(c) as corrupted_chunks'
            ],
            'embedding_dimension_mismatch': [
                'MATCH (c:Chunk) WHERE c.embedding IS NOT NULL RETURN size(c.embedding[0..1]) as dim_sample',
                'SHOW INDEXES YIELD name, type WHERE type = "VECTOR" RETURN count(*) as vector_indexes'
            ],
            'community_detection_failure': [
                'MATCH (c:__Community__) RETURN count(c) as total_communities',
                'MATCH (e:__Entity__)-[:IN_COMMUNITY]->(c:__Community__) RETURN count(e) as entities_in_communities'
            ]
        }
        
        queries = validation_queries.get(issue_type, [])
        results = []
        
        for query in queries:
            try:
                result = execute_graph_query(graph, query)
                results.append(result)
            except Exception as e:
                results.append({'error': str(e)})
        
        return results
```

## Monitoring Dashboard

### Key Performance Indicators

**System Health Metrics**:
```python
class SystemHealthMonitor:
    """Monitor system health and performance indicators"""
    
    def __init__(self, graph):
        self.graph = graph
        
    def get_system_health_metrics(self):
        """Collect comprehensive system health metrics"""
        
        metrics = {
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'database_health': self._check_database_health(),
            'processing_pipeline': self._check_pipeline_health(),
            'api_health': self._check_api_health(),
            'resource_utilization': self._check_resource_utilization(),
            'error_rates': self._calculate_error_rates(),
            'performance_scores': self._calculate_performance_scores()
        }
        
        # Calculate overall health score
        metrics['overall_health_score'] = self._calculate_overall_health(metrics)
        
        return metrics
    
    def _check_database_health(self):
        """Check Neo4j database health"""
        try:
            # Connection test
            connection_test = execute_graph_query(self.graph, "RETURN 1 as test")
            
            # Database size and performance
            size_query = """
            CALL apoc.monitor.store() YIELD logSize, stringStoreSize, arrayStoreSize, relStoreSize, propStoreSize, totalStoreSize
            RETURN logSize, stringStoreSize, arrayStoreSize, relStoreSize, propStoreSize, totalStoreSize
            """
            
            size_info = execute_graph_query(self.graph, size_query)
            
            # Active connections
            connections_query = "CALL dbms.listConnections() YIELD connectionId, connector, username RETURN count(*) as active_connections"
            connections = execute_graph_query(self.graph, connections_query)
            
            return {
                'status': 'healthy',
                'connection_test': 'passed',
                'database_size': size_info[0] if size_info else {},
                'active_connections': connections[0]['active_connections'] if connections else 0
            }
            
        except Exception as e:
            return {
                'status': 'unhealthy',
                'error': str(e),
                'connection_test': 'failed'
            }
    
    def _check_pipeline_health(self):
        """Check processing pipeline health"""
        try:
            # Document processing status distribution
            status_query = """
            MATCH (d:Document)
            RETURN d.status as status, count(*) as count
            ORDER BY count DESC
            """
            
            status_distribution = execute_graph_query(self.graph, status_query)
            
            # Recent processing performance
            recent_query = """
            MATCH (d:Document)
            WHERE d.updated_at > datetime() - duration('P1D')
            RETURN 
                avg(d.processing_time) as avg_processing_time,
                count(*) as documents_processed_24h,
                sum(CASE WHEN d.status = 'Failed' THEN 1 ELSE 0 END) as failed_documents
            """
            
            recent_performance = execute_graph_query(self.graph, recent_query)
            
            return {
                'status': 'healthy',
                'status_distribution': status_distribution,
                'recent_performance': recent_performance[0] if recent_performance else {}
            }
            
        except Exception as e:
            return {
                'status': 'unhealthy',
                'error': str(e)
            }
```

### Alerting System

**Intelligent Alerting**:
```python
class AlertingSystem:
    """Intelligent alerting based on system metrics and thresholds"""
    
    def __init__(self):
        self.alert_thresholds = self._load_alert_thresholds()
        self.alert_channels = self._configure_alert_channels()
        
    def evaluate_alerts(self, metrics):
        """Evaluate metrics against thresholds and trigger alerts"""
        
        alerts = []
        
        # Database health alerts
        if metrics['database_health']['status'] != 'healthy':
            alerts.append({
                'severity': 'critical',
                'component': 'database',
                'message': 'Database health check failed',
                'details': metrics['database_health']
            })
        
        # Error rate alerts
        error_rate = metrics['error_rates'].get('overall_error_rate', 0)
        if error_rate > self.alert_thresholds['error_rate']['critical']:
            alerts.append({
                'severity': 'critical',
                'component': 'processing',
                'message': f'High error rate detected: {error_rate:.2%}',
                'details': metrics['error_rates']
            })
        elif error_rate > self.alert_thresholds['error_rate']['warning']:
            alerts.append({
                'severity': 'warning',
                'component': 'processing',
                'message': f'Elevated error rate: {error_rate:.2%}',
                'details': metrics['error_rates']
            })
        
        # Performance alerts
        overall_health = metrics.get('overall_health_score', 1.0)
        if overall_health < self.alert_thresholds['health_score']['critical']:
            alerts.append({
                'severity': 'critical',
                'component': 'system',
                'message': f'Poor system health: {overall_health:.2f}',
                'details': metrics
            })
        
        # Send alerts
        for alert in alerts:
            self._send_alert(alert)
        
        return alerts
    
    def _send_alert(self, alert):
        """Send alert through configured channels"""
        
        alert_message = {
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'severity': alert['severity'],
            'component': alert['component'],
            'message': alert['message'],
            'details': alert['details'],
            'environment': os.environ.get('ENVIRONMENT', 'development')
        }
        
        # Log alert
        logger.log_struct(alert_message, "ERROR" if alert['severity'] == 'critical' else "WARNING")
        
        # Send to external systems
        for channel in self.alert_channels:
            try:
                channel.send_alert(alert_message)
            except Exception as e:
                logging.error(f"Failed to send alert via {channel.__class__.__name__}: {e}")
```

## Configuration Parameters

### Error Handling Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `MAX_RETRIES` | `3` | Maximum retry attempts for operations |
| `RETRY_DELAY` | `2` | Base delay between retries (seconds) |
| `DEADLOCK_RETRY_DELAY` | `2` | Delay for deadlock retries (seconds) |
| `API_TIMEOUT` | `30` | API call timeout (seconds) |
| `CONNECTION_TIMEOUT` | `10` | Database connection timeout (seconds) |
| `MAX_CONSECUTIVE_ERRORS` | `5` | Maximum consecutive errors before circuit breaker |

### Monitoring Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `ENABLE_PERFORMANCE_MONITORING` | `true` | Enable performance metrics collection |
| `METRICS_COLLECTION_INTERVAL` | `60` | Metrics collection interval (seconds) |
| `LOG_LEVEL` | `INFO` | Logging level |
| `ENABLE_STRUCTURED_LOGGING` | `true` | Enable structured JSON logging |
| `ALERT_THRESHOLD_ERROR_RATE` | `0.1` | Error rate threshold for alerts |

This comprehensive error handling and monitoring system ensures robust operation, quick problem detection, and efficient recovery procedures for the LLM Graph Builder platform.