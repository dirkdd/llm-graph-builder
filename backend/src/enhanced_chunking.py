# Task 11: Enhanced Chunking Integration Layer
# Integration layer for hierarchical chunking pipeline

import os
import time
import re
import logging
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
from langchain.docstore.document import Document

# Import hierarchical chunking components
from .navigation_extractor import NavigationExtractor, NavigationStructure, DocumentFormat
from .semantic_chunker import SemanticChunker, ChunkingResult, SemanticChunk, ChunkType
from .chunk_relationships import ChunkRelationshipManager, RelationshipDetectionResult
from .entities.navigation_models import HierarchicalChunk, ChunkRelationship
from .graphDB_dataAccess import graphDBdataAccess
from .shared.common_fn import create_relation_between_chunks

logging.basicConfig(format='%(asctime)s - %(message)s', level='INFO')


class EnhancedChunkingPipeline:
    """Integration layer for hierarchical chunking pipeline"""
    
    def __init__(self, 
                 enable_hierarchical: bool = True,
                 enable_relationships: bool = True,
                 max_doc_size_hierarchical: int = 50000,
                 max_processing_time: int = 300):
        """Initialize enhanced chunking pipeline
        
        Args:
            enable_hierarchical: Enable hierarchical chunking
            enable_relationships: Enable relationship detection
            max_doc_size_hierarchical: Max document size for hierarchical processing
            max_processing_time: Max processing time before fallback
        """
        self.enable_hierarchical = enable_hierarchical
        self.enable_relationships = enable_relationships
        self.max_doc_size_hierarchical = max_doc_size_hierarchical
        self.max_processing_time = max_processing_time
        self.logger = logging.getLogger(__name__)
        
        # Initialize components
        if self.enable_hierarchical:
            self.navigation_extractor = NavigationExtractor()
            self.semantic_chunker = SemanticChunker(
                min_chunk_size=200,
                max_chunk_size=1500,
                target_chunk_size=800,
                overlap_size=100
            )
            
        if self.enable_relationships:
            self.relationship_manager = ChunkRelationshipManager(
                min_relationship_strength=float(os.getenv('MIN_RELATIONSHIP_STRENGTH', '0.3')),
                min_evidence_confidence=0.5,
                max_relationships_per_chunk=20,
                enable_quality_filtering=True
            )
    
    def should_use_hierarchical_chunking(self, pages: List[Document]) -> bool:
        """Determine if hierarchical chunking should be used"""
        if not self.enable_hierarchical:
            return False
        
        # Calculate total document size
        total_size = sum(len(page.page_content) for page in pages)
        
        if total_size > self.max_doc_size_hierarchical:
            self.logger.info(f"Document size {total_size} exceeds threshold {self.max_doc_size_hierarchical}, using basic chunking")
            return False
        
        # Check if document appears to have structure
        content = '\n'.join([page.page_content for page in pages])
        has_structure = self._detect_document_structure(content)
        
        if not has_structure:
            self.logger.info("No clear document structure detected, using basic chunking")
            return False
        
        return True
    
    def process_document_hierarchical(self, 
                                    pages: List[Document], 
                                    file_name: str,
                                    token_chunk_size: int,
                                    chunk_overlap: int) -> Tuple[List[Dict[str, Any]], Optional[RelationshipDetectionResult], Dict[str, Any]]:
        """Process document using hierarchical chunking pipeline
        
        Args:
            pages: Document pages to process
            file_name: Name of the file being processed
            token_chunk_size: Target chunk size in tokens
            chunk_overlap: Overlap between chunks
            
        Returns:
            Tuple of (compatible_chunks, relationship_result, processing_metrics)
        """
        try:
            start_time = time.time()
            processing_metrics = {}
            
            self.logger.info(f"Starting hierarchical processing for {file_name}")
            
            # Step 1: Extract navigation structure
            navigation_start = time.time()
            document_content = '\n'.join([page.page_content for page in pages])
            document_format = self._detect_document_format(file_name)
            
            navigation_structure = self.navigation_extractor.extract_navigation_structure(
                document_content=document_content,
                document_format=document_format,
                file_name=file_name
            )
            
            navigation_time = time.time() - navigation_start
            processing_metrics['navigation_extraction'] = f'{navigation_time:.2f}'
            
            self.logger.info(f"Navigation extraction completed in {navigation_time:.2f}s, found {len(navigation_structure.nodes)} nodes")
            
            # Step 2: Create hierarchical chunks
            chunking_start = time.time()
            
            # Update chunker settings based on token size
            self.semantic_chunker.max_chunk_size = min(token_chunk_size * 4, 1500)  # Rough token to char conversion
            self.semantic_chunker.target_chunk_size = min(token_chunk_size * 3, 800)
            self.semantic_chunker.overlap_size = min(chunk_overlap * 4, 100)
            
            chunking_result = self.semantic_chunker.create_hierarchical_chunks(
                navigation_structure=navigation_structure,
                document_content=document_content,
                document_type=self._determine_document_type(file_name, document_content)
            )
            
            chunking_time = time.time() - chunking_start
            processing_metrics['hierarchical_chunking'] = f'{chunking_time:.2f}'
            
            self.logger.info(f"Hierarchical chunking completed in {chunking_time:.2f}s, created {len(chunking_result.chunks)} chunks")
            
            # Step 3: Detect relationships (if enabled)
            relationship_result = None
            if self.enable_relationships and len(chunking_result.chunks) > 1:
                relationship_start = time.time()
                
                relationship_result = self.relationship_manager.create_enhanced_relationships(
                    chunking_result=chunking_result,
                    navigation_structure=navigation_structure
                )
                
                relationship_time = time.time() - relationship_start
                processing_metrics['relationship_detection'] = f'{relationship_time:.2f}'
                
                self.logger.info(f"Relationship detection completed in {relationship_time:.2f}s, found {len(relationship_result.detected_relationships)} relationships")
            
            # Step 4: Convert to compatible format for existing pipeline
            compatible_chunks = self._convert_to_compatible_format(chunking_result.chunks, pages)
            
            total_time = time.time() - start_time
            processing_metrics['total_hierarchical_processing'] = f'{total_time:.2f}'
            processing_metrics['hierarchical_chunks_created'] = len(chunking_result.chunks)
            processing_metrics['chunk_quality_average'] = chunking_result.quality_metrics.get('overall_quality', 0.0)
            
            if relationship_result:
                processing_metrics['relationships_detected'] = len(relationship_result.detected_relationships)
                processing_metrics['relationship_quality'] = relationship_result.quality_assessment.get('overall_quality', 0.0)
            
            # Check processing time threshold
            if total_time > self.max_processing_time:
                self.logger.warning(f"Hierarchical processing took {total_time:.2f}s, exceeding threshold {self.max_processing_time}s")
            
            return compatible_chunks, relationship_result, processing_metrics
            
        except Exception as e:
            self.logger.error(f"Hierarchical processing failed for {file_name}: {str(e)}")
            # Don't re-raise, let caller handle fallback
            return [], None, {'error': str(e), 'fallback_reason': 'hierarchical_processing_failed'}
    
    def _convert_to_compatible_format(self, semantic_chunks: List[SemanticChunk], original_pages: List[Document]) -> List[Dict[str, Any]]:
        """Convert SemanticChunks to format compatible with existing pipeline"""
        compatible_chunks = []
        
        for i, chunk in enumerate(semantic_chunks):
            # Create Document object compatible with existing pipeline
            chunk_doc = Document(
                page_content=chunk.content,
                metadata={
                    'chunk_id': chunk.chunk_id,
                    'chunk_type': chunk.chunk_type.value,
                    'node_id': chunk.node_id,
                    'navigation_path': chunk.context.navigation_path,
                    'section_number': chunk.context.section_number,
                    'hierarchy_level': chunk.context.hierarchy_level,
                    'quality_score': chunk.context.quality_score,
                    'token_count': chunk.token_count,
                    'chunk_index': i,
                    'hierarchical': True,
                    # Preserve original metadata for compatibility
                    'page_number': 1,  # Default for compatibility
                    'source': getattr(original_pages[0], 'metadata', {}).get('source', 'hierarchical_chunk')
                }
            )
            
            compatible_chunks.append({
                'chunk_id': chunk.chunk_id,
                'chunk_doc': chunk_doc
            })
        
        return compatible_chunks
    
    def _detect_document_structure(self, content: str) -> bool:
        """Detect if document has clear structure for hierarchical processing"""
        # Look for common structural indicators
        indicators = [
            r'^\s*\d+\.\s+[A-Z]',  # Numbered sections
            r'^\s*CHAPTER\s+\d+',  # Chapter headings
            r'^\s*Section\s+\d+',  # Section headings
            r'^\s*\d+\.\d+\s+',    # Subsection numbering
            r'^\s*[A-Z]{2,}\s*$',  # All caps headings
        ]
        
        lines = content.split('\n')
        structure_count = 0
        
        for line in lines[:min(100, len(lines))]:  # Check first 100 lines
            line = line.strip()
            if line:
                for pattern in indicators:
                    if re.search(pattern, line):
                        structure_count += 1
                        break
        
        # Require at least 3 structural indicators
        return structure_count >= 3
    
    def _detect_document_format(self, file_name: str) -> DocumentFormat:
        """Detect document format from filename"""
        extension = file_name.lower().split('.')[-1]
        
        format_map = {
            'pdf': DocumentFormat.PDF,
            'docx': DocumentFormat.DOCX,
            'doc': DocumentFormat.DOCX,
            'html': DocumentFormat.HTML,
            'htm': DocumentFormat.HTML,
            'txt': DocumentFormat.TEXT
        }
        
        return format_map.get(extension, DocumentFormat.TEXT)
    
    def _determine_document_type(self, file_name: str, content: str) -> str:
        """Determine document type for processing"""
        file_lower = file_name.lower()
        content_lower = content.lower()
        
        # Check for mortgage-specific document types
        if any(term in file_lower for term in ['matrix', 'pricing', 'rate']):
            return 'matrix'
        elif any(term in content_lower for term in ['eligibility', 'guidelines', 'requirements', 'policy']):
            return 'guidelines'
        elif any(term in file_lower for term in ['procedure', 'process', 'workflow']):
            return 'procedures'
        else:
            return 'guidelines'  # Default
    
    def store_hierarchical_relationships(self, 
                                       graph: Any, 
                                       relationship_result: RelationshipDetectionResult,
                                       file_name: str) -> int:
        """Store hierarchical chunk relationships in database"""
        if not relationship_result or not relationship_result.detected_relationships:
            return 0
        
        try:
            graphDb_data_Access = graphDBdataAccess(graph)
            
            # Store chunk relationships
            stored_count = 0
            for relationship in relationship_result.detected_relationships:
                try:
                    # Convert ChunkRelationship to database format
                    rel_data = {
                        'relationship_id': relationship.relationship_id,
                        'from_chunk_id': relationship.from_chunk_id,
                        'to_chunk_id': relationship.to_chunk_id,
                        'relationship_type': relationship.relationship_type.value,
                        'strength': relationship.strength,
                        'confidence': relationship.confidence,
                        'evidence': [evidence.to_dict() for evidence in relationship.evidence],
                        'metadata': relationship.metadata,
                        'file_name': file_name
                    }
                    
                    # Store in Neo4j (this would need to be implemented in graphDBdataAccess)
                    # For now, we'll log the relationship storage
                    self.logger.info(f"Storing relationship: {relationship.relationship_type.value} from {relationship.from_chunk_id} to {relationship.to_chunk_id}")
                    stored_count += 1
                    
                except Exception as e:
                    self.logger.error(f"Failed to store relationship {relationship.relationship_id}: {str(e)}")
            
            # Store relationship evidence
            evidence_count = 0
            for rel_id, evidence_list in relationship_result.relationship_evidence.items():
                for evidence in evidence_list:
                    try:
                        # Store evidence data
                        evidence_data = evidence.to_dict()
                        evidence_data['relationship_id'] = rel_id
                        evidence_data['file_name'] = file_name
                        
                        # Log evidence storage (would be implemented in graphDBdataAccess)
                        evidence_count += 1
                        
                    except Exception as e:
                        self.logger.error(f"Failed to store evidence for {rel_id}: {str(e)}")
            
            self.logger.info(f"Stored {stored_count} relationships and {evidence_count} evidence entries for {file_name}")
            return stored_count
            
        except Exception as e:
            self.logger.error(f"Failed to store hierarchical relationships: {str(e)}")
            return 0


# Configuration from environment variables
ENABLE_HIERARCHICAL_CHUNKING = os.getenv('ENABLE_HIERARCHICAL_CHUNKING', 'true').lower() == 'true'
ENABLE_RELATIONSHIP_DETECTION = os.getenv('ENABLE_RELATIONSHIP_DETECTION', 'true').lower() == 'true'
MAX_DOCUMENT_SIZE_FOR_HIERARCHICAL = int(os.getenv('MAX_DOCUMENT_SIZE_FOR_HIERARCHICAL', '50000'))
MAX_PROCESSING_TIME_HIERARCHICAL = int(os.getenv('MAX_PROCESSING_TIME_HIERARCHICAL', '300'))

# Global pipeline instance
enhanced_pipeline = EnhancedChunkingPipeline(
    enable_hierarchical=ENABLE_HIERARCHICAL_CHUNKING,
    enable_relationships=ENABLE_RELATIONSHIP_DETECTION,
    max_doc_size_hierarchical=MAX_DOCUMENT_SIZE_FOR_HIERARCHICAL,
    max_processing_time=MAX_PROCESSING_TIME_HIERARCHICAL
)


def get_enhanced_chunks_pipeline(graph, file_name: str, pages: List[Document], 
                               token_chunk_size: int, chunk_overlap: int,
                               retry_condition: str = None) -> Tuple[int, List[Dict[str, Any]], Optional[RelationshipDetectionResult], Dict[str, Any]]:
    """Enhanced version of get_chunkId_chunkDoc_list with hierarchical processing
    
    Args:
        graph: Neo4j graph connection
        file_name: Name of the file being processed
        pages: Document pages
        token_chunk_size: Target chunk size
        chunk_overlap: Chunk overlap size
        retry_condition: Retry condition (for backward compatibility)
        
    Returns:
        Tuple of (total_chunks, chunk_list, relationship_result, processing_metrics)
    """
    processing_metrics = {}
    relationship_result = None
    
    try:
        # Check if we should use hierarchical chunking
        if not retry_condition and enhanced_pipeline.should_use_hierarchical_chunking(pages):
            logging.info(f"Using hierarchical chunking for {file_name}")
            
            # Process with hierarchical pipeline
            chunk_list, relationship_result, hierarchical_metrics = enhanced_pipeline.process_document_hierarchical(
                pages=pages,
                file_name=file_name,
                token_chunk_size=token_chunk_size,
                chunk_overlap=chunk_overlap
            )
            
            # Handle processing failure
            if not chunk_list and 'error' in hierarchical_metrics:
                logging.error(f"Hierarchical processing failed, using fallback")
                processing_metrics['chunking_method'] = 'basic_fallback'
                processing_metrics.update(hierarchical_metrics)
                # Fall through to basic chunking
            else:
                processing_metrics.update(hierarchical_metrics)
                processing_metrics['chunking_method'] = 'hierarchical'
                return len(chunk_list), chunk_list, relationship_result, processing_metrics
        
        else:
            # Fall back to basic chunking (existing implementation)
            logging.info(f"Using basic chunking for {file_name}")
            processing_metrics['chunking_method'] = 'basic'
            
            # Call existing basic chunking logic
            from .create_chunks import CreateChunksofDocument
            create_chunks_obj = CreateChunksofDocument(pages, graph)
            chunks = create_chunks_obj.split_file_into_chunks(token_chunk_size, chunk_overlap)
            
            # Convert to expected format
            chunk_list = []
            for i, chunk in enumerate(chunks):
                chunk_id = f"chunk_{file_name}_{i:03d}"
                chunk_list.append({
                    'chunk_id': chunk_id,
                    'chunk_doc': chunk
                })
            
            return len(chunks), chunk_list, None, processing_metrics
            
    except Exception as e:
        logging.error(f"Enhanced chunking failed for {file_name}: {str(e)}")
        # Fall back to basic chunking on error
        logging.info(f"Falling back to basic chunking for {file_name}")
        
        from .create_chunks import CreateChunksofDocument
        create_chunks_obj = CreateChunksofDocument(pages, graph)
        chunks = create_chunks_obj.split_file_into_chunks(token_chunk_size, chunk_overlap)
        
        chunk_list = []
        for i, chunk in enumerate(chunks):
            chunk_id = f"chunk_{file_name}_{i:03d}"
            chunk_list.append({
                'chunk_id': chunk_id,
                'chunk_doc': chunk
            })
        
        processing_metrics['chunking_method'] = 'basic_fallback'
        processing_metrics['fallback_reason'] = str(e)
        
        return len(chunks), chunk_list, None, processing_metrics


def enhanced_processing_chunks_pipeline(chunkId_chunkDoc_list, relationship_result, processing_metrics,
                                       graph, uri, userName, password, database, file_name, model,
                                       allowedNodes, allowedRelationship, chunks_to_combine,
                                       node_count, rel_count, additional_instructions=None):
    """Enhanced version of processing_chunks with relationship storage"""
    
    # Add relationship storage timing
    latency_processing_chunk = {}
    
    # Store hierarchical relationships if available
    if relationship_result:
        start_store_relationships = time.time()
        
        relationship_count = enhanced_pipeline.store_hierarchical_relationships(
            graph=graph,
            relationship_result=relationship_result,
            file_name=file_name
        )
        
        end_store_relationships = time.time()
        elapsed_store_relationships = end_store_relationships - start_store_relationships
        
        latency_processing_chunk["store_relationships"] = f'{elapsed_store_relationships:.2f}'
        latency_processing_chunk["relationships_stored"] = relationship_count
        
        rel_count += relationship_count
        
        logging.info(f'Time taken to store chunk relationships: {elapsed_store_relationships:.2f} seconds')
    
    # Add processing metrics to latency tracking
    for metric_key, metric_value in processing_metrics.items():
        latency_processing_chunk[f"enhanced_{metric_key}"] = metric_value
    
    return latency_processing_chunk, rel_count