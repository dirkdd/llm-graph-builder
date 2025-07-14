# Task 8: Semantic Chunker Implementation
# This file implements hierarchy-aware semantic chunking using NavigationExtractor output

from typing import List, Dict, Any, Optional, Tuple, Union
from dataclasses import dataclass, asdict
from enum import Enum
import logging
from datetime import datetime
import hashlib
import re
from pathlib import Path

# Import navigation extractor components
from .navigation_extractor import (
    NavigationStructure, 
    NavigationNode, 
    NavigationLevel,
    DocumentFormat
)


class ChunkType(Enum):
    """Types of semantic chunks"""
    HEADER = "header"           # Section headers and titles
    CONTENT = "content"         # Main content paragraphs
    DECISION = "decision"       # Decision logic and rules
    MATRIX = "matrix"          # Matrix and table content
    REFERENCE = "reference"     # Cross-references and citations
    SUMMARY = "summary"        # Section summaries


@dataclass
class ChunkContext:
    """Context information for a semantic chunk"""
    navigation_path: List[str]              # Full navigation breadcrumb
    parent_section: Optional[str] = None    # Immediate parent section
    section_number: Optional[str] = None    # Section numbering (1.1.1)
    hierarchy_level: int = 0                # Depth in document hierarchy
    document_type: str = "unknown"          # guidelines, matrix, etc.
    decision_context: Optional[str] = None  # Decision tree context
    related_chunks: List[str] = None        # Related chunk IDs
    quality_score: float = 0.0             # Chunk quality metric
    
    def __post_init__(self):
        if self.related_chunks is None:
            self.related_chunks = []


@dataclass 
class SemanticChunk:
    """A hierarchy-aware semantic chunk"""
    chunk_id: str
    content: str
    chunk_type: ChunkType
    context: ChunkContext
    node_id: Optional[str] = None           # Source NavigationNode ID
    start_position: int = 0                 # Character start position
    end_position: int = 0                   # Character end position
    token_count: int = 0                    # Estimated token count
    overlap_with: List[str] = None          # Overlapping chunk IDs
    metadata: Dict[str, Any] = None         # Additional metadata
    
    def __post_init__(self):
        if self.overlap_with is None:
            self.overlap_with = []
        if self.metadata is None:
            self.metadata = {}
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        result = asdict(self)
        result['chunk_type'] = self.chunk_type.value
        result['context'] = asdict(self.context)
        return result


@dataclass
class ChunkingResult:
    """Result of semantic chunking operation"""
    chunks: List[SemanticChunk]
    chunk_relationships: List[Dict[str, Any]]
    chunking_metadata: Dict[str, Any]
    quality_metrics: Dict[str, Any]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            'chunks': [chunk.to_dict() for chunk in self.chunks],
            'chunk_relationships': self.chunk_relationships,
            'chunking_metadata': self.chunking_metadata,
            'quality_metrics': self.quality_metrics
        }


class SemanticChunker:
    """Creates hierarchy-aware semantic chunks from navigation structures"""
    
    def __init__(self, 
                 min_chunk_size: int = 200,
                 max_chunk_size: int = 1500,
                 target_chunk_size: int = 800,
                 overlap_size: int = 100,
                 context_window: int = 2):
        """Initialize SemanticChunker
        
        Args:
            min_chunk_size: Minimum chunk size in characters
            max_chunk_size: Maximum chunk size in characters  
            target_chunk_size: Target chunk size in characters
            overlap_size: Overlap size between chunks
            context_window: Number of neighboring nodes to include for context
        """
        self.min_chunk_size = min_chunk_size
        self.max_chunk_size = max_chunk_size
        self.target_chunk_size = target_chunk_size
        self.overlap_size = overlap_size
        self.context_window = context_window
        self.logger = logging.getLogger(__name__)
        
        # Token estimation (rough approximation: 1 token ≈ 4 characters)
        self.chars_per_token = 4
    
    def create_hierarchical_chunks(self, 
                                 navigation_structure: NavigationStructure,
                                 document_content: str,
                                 document_type: str = "guidelines") -> ChunkingResult:
        """Create hierarchical chunks from navigation structure
        
        Args:
            navigation_structure: Output from NavigationExtractor
            document_content: Original document content
            document_type: Type of document (guidelines, matrix, etc.)
            
        Returns:
            ChunkingResult: Complete chunking results with relationships
            
        Raises:
            ValueError: If navigation structure is invalid
            Exception: If chunking fails
        """
        try:
            start_time = datetime.now()
            self.logger.info(f"Starting hierarchical chunking for {navigation_structure.document_id}")
            
            # Initialize chunking state
            chunks = []
            chunk_relationships = []
            
            # Create content mapping from navigation nodes
            content_map = self._map_content_to_nodes(navigation_structure, document_content)
            
            # Process each navigation node
            for node_id, node in navigation_structure.nodes.items():
                if node_id == navigation_structure.root_node.node_id:
                    continue  # Skip root node
                
                # Get content for this node
                node_content = content_map.get(node_id, node.content)
                if not node_content or len(node_content.strip()) < 10:
                    continue  # Skip empty or trivial content
                
                # Create chunks for this node
                node_chunks = self._create_node_chunks(
                    node, 
                    node_content, 
                    navigation_structure,
                    document_type
                )
                
                chunks.extend(node_chunks)
                
                # Create relationships for node chunks
                node_relationships = self._create_node_relationships(
                    node_chunks, 
                    node, 
                    navigation_structure
                )
                chunk_relationships.extend(node_relationships)
            
            # Post-process chunks
            chunks = self._post_process_chunks(chunks, navigation_structure)
            
            # Create cross-chunk relationships
            cross_relationships = self._create_cross_chunk_relationships(chunks)
            chunk_relationships.extend(cross_relationships)
            
            # Calculate quality metrics
            quality_metrics = self._calculate_quality_metrics(chunks, navigation_structure)
            
            # Create metadata
            chunking_metadata = {
                'processing_time': (datetime.now() - start_time).total_seconds(),
                'document_id': navigation_structure.document_id,
                'document_type': document_type,
                'total_chunks': len(chunks),
                'average_chunk_size': sum(len(c.content) for c in chunks) / len(chunks) if chunks else 0,
                'navigation_nodes_processed': len([n for n in navigation_structure.nodes.values() if n.node_id != navigation_structure.root_node.node_id]),
                'chunk_types': {chunk_type.value: len([c for c in chunks if c.chunk_type == chunk_type]) for chunk_type in ChunkType}
            }
            
            result = ChunkingResult(
                chunks=chunks,
                chunk_relationships=chunk_relationships,
                chunking_metadata=chunking_metadata,
                quality_metrics=quality_metrics
            )
            
            self.logger.info(f"Hierarchical chunking completed: {len(chunks)} chunks created")
            return result
            
        except Exception as e:
            self.logger.error(f"Failed to create hierarchical chunks: {str(e)}")
            raise
    
    def create_node_chunk(self, 
                         node: NavigationNode,
                         content: str,
                         navigation_structure: NavigationStructure,
                         document_type: str = "guidelines") -> List[SemanticChunk]:
        """Create chunks for a single navigation node
        
        Args:
            node: NavigationNode to chunk
            content: Content text for the node
            navigation_structure: Complete navigation structure for context
            document_type: Type of document
            
        Returns:
            List of SemanticChunks for this node
        """
        return self._create_node_chunks(node, content, navigation_structure, document_type)
    
    def add_hierarchical_context(self, 
                               chunk: SemanticChunk, 
                               navigation_structure: NavigationStructure) -> SemanticChunk:
        """Add hierarchical context to a chunk
        
        Args:
            chunk: SemanticChunk to enhance
            navigation_structure: Navigation structure for context
            
        Returns:
            Enhanced SemanticChunk with hierarchical context
        """
        try:
            if not chunk.node_id or chunk.node_id not in navigation_structure.nodes:
                return chunk
            
            node = navigation_structure.nodes[chunk.node_id]
            
            # Build navigation path
            navigation_path = self._build_navigation_path(node, navigation_structure)
            
            # Find parent section
            parent_section = None
            if node.parent_id and node.parent_id in navigation_structure.nodes:
                parent_node = navigation_structure.nodes[node.parent_id]
                parent_section = parent_node.title
            
            # Calculate hierarchy level
            hierarchy_level = len(navigation_path) - 1
            
            # Determine decision context
            decision_context = None
            if node.metadata.get('decision_indicator') or node.decision_type:
                decision_context = f"Decision node: {node.decision_type or 'conditional'}"
            
            # Update chunk context
            chunk.context.navigation_path = navigation_path
            chunk.context.parent_section = parent_section
            chunk.context.section_number = node.section_number
            chunk.context.hierarchy_level = hierarchy_level
            chunk.context.decision_context = decision_context
            
            # Calculate quality score
            chunk.context.quality_score = self._calculate_chunk_quality(chunk, node)
            
            return chunk
            
        except Exception as e:
            self.logger.error(f"Failed to add hierarchical context: {str(e)}")
            return chunk
    
    # Private helper methods
    
    def _create_node_chunks(self, 
                          node: NavigationNode,
                          content: str, 
                          navigation_structure: NavigationStructure,
                          document_type: str) -> List[SemanticChunk]:
        """Create chunks for a single navigation node"""
        chunks = []
        
        # Determine chunk type based on node characteristics
        chunk_type = self._determine_chunk_type(node, content, document_type)
        
        # Clean and prepare content
        clean_content = self._clean_content(content)
        
        # Split content into chunks if needed
        content_chunks = self._split_content_intelligently(clean_content, node, chunk_type)
        
        for i, chunk_content in enumerate(content_chunks):
            # Generate chunk ID
            chunk_id = self._generate_chunk_id(node, i)
            
            # Create initial context
            context = ChunkContext(
                navigation_path=[],  # Will be filled by add_hierarchical_context
                document_type=document_type
            )
            
            # Create chunk
            chunk = SemanticChunk(
                chunk_id=chunk_id,
                content=chunk_content,
                chunk_type=chunk_type,
                context=context,
                node_id=node.node_id,
                token_count=len(chunk_content) // self.chars_per_token,
                metadata={
                    'source_node_title': node.title,
                    'source_node_level': node.level.value,
                    'chunk_index': i,
                    'total_chunks_for_node': len(content_chunks)
                }
            )
            
            # Add hierarchical context
            chunk = self.add_hierarchical_context(chunk, navigation_structure)
            
            chunks.append(chunk)
        
        return chunks
    
    def _map_content_to_nodes(self, 
                            navigation_structure: NavigationStructure,
                            document_content: str) -> Dict[str, str]:
        """Map document content to navigation nodes"""
        content_map = {}
        
        # Simple approach: use existing node content or extract based on line numbers
        for node_id, node in navigation_structure.nodes.items():
            if node.content:
                content_map[node_id] = node.content
            elif node.metadata.get('line_number'):
                # Extract content around the line number
                lines = document_content.split('\n')
                line_num = node.metadata['line_number'] - 1  # Convert to 0-based
                
                # Extract content from this line to next heading or end
                start_line = max(0, line_num)
                end_line = len(lines)
                
                # Find next heading to determine end
                for i in range(start_line + 1, len(lines)):
                    line = lines[i].strip()
                    if self._is_heading_line(line):
                        end_line = i
                        break
                
                # Extract content
                section_content = '\n'.join(lines[start_line:end_line])
                content_map[node_id] = section_content
        
        return content_map
    
    def _determine_chunk_type(self, 
                            node: NavigationNode, 
                            content: str,
                            document_type: str) -> ChunkType:
        """Determine the type of chunk based on node and content characteristics"""
        
        # Check for decision indicators
        if (node.metadata.get('decision_indicator') or 
            node.decision_type or 
            self._contains_decision_language(content)):
            return ChunkType.DECISION
        
        # Check for matrix content
        if (document_type == "matrix" or 
            "matrix" in node.title.lower() or
            self._contains_matrix_language(content)):
            return ChunkType.MATRIX
        
        # Check for headers (short content, title-like)
        if (len(content.strip()) < 100 and 
            (node.level in [NavigationLevel.CHAPTER, NavigationLevel.SECTION] or
             node.title in content)):
            return ChunkType.HEADER
        
        # Check for references
        if self._contains_reference_language(content):
            return ChunkType.REFERENCE
        
        # Default to content
        return ChunkType.CONTENT
    
    def _split_content_intelligently(self, 
                                   content: str,
                                   node: NavigationNode, 
                                   chunk_type: ChunkType) -> List[str]:
        """Split content into appropriately sized chunks"""
        
        if len(content) <= self.max_chunk_size:
            return [content]
        
        chunks = []
        
        # Different splitting strategies based on chunk type
        if chunk_type == ChunkType.DECISION:
            # Split decision content by logical units (if/then/else)
            chunks = self._split_decision_content(content)
        elif chunk_type == ChunkType.MATRIX:
            # Split matrix content by rows or logical groups
            chunks = self._split_matrix_content(content)
        else:
            # Default paragraph-based splitting
            chunks = self._split_by_paragraphs(content)
        
        # Ensure chunks meet size requirements
        chunks = self._adjust_chunk_sizes(chunks)
        
        return chunks
    
    def _split_decision_content(self, content: str) -> List[str]:
        """Split decision content by logical decision units"""
        chunks = []
        
        # Split by decision keywords
        decision_patterns = [
            r'(?=\bIf\b)',
            r'(?=\bWhen\b)', 
            r'(?=\bUnless\b)',
            r'(?=\bProvided that\b)'
        ]
        
        for pattern in decision_patterns:
            parts = re.split(pattern, content, flags=re.IGNORECASE)
            if len(parts) > 1:
                # First part might be introduction
                if parts[0].strip():
                    chunks.append(parts[0].strip())
                # Rest are decision units
                for part in parts[1:]:
                    if part.strip():
                        chunks.append(part.strip())
                return chunks
        
        # Fallback to paragraph splitting
        return self._split_by_paragraphs(content)
    
    def _split_matrix_content(self, content: str) -> List[str]:
        """Split matrix content by logical groups"""
        # Split by table rows or major sections
        lines = content.split('\n')
        chunks = []
        current_chunk = []
        
        for line in lines:
            current_chunk.append(line)
            
            # Check if this completes a logical unit
            chunk_text = '\n'.join(current_chunk)
            if (len(chunk_text) >= self.target_chunk_size or
                self._is_matrix_row_complete(line)):
                
                if len(chunk_text.strip()) > 0:
                    chunks.append(chunk_text.strip())
                current_chunk = []
        
        # Add remaining content
        if current_chunk:
            remaining = '\n'.join(current_chunk).strip()
            if remaining:
                chunks.append(remaining)
        
        return chunks if chunks else [content]
    
    def _split_by_paragraphs(self, content: str) -> List[str]:
        """Split content by paragraphs with intelligent sizing"""
        paragraphs = [p.strip() for p in content.split('\n\n') if p.strip()]
        
        chunks = []
        current_chunk = []
        current_size = 0
        
        for paragraph in paragraphs:
            para_size = len(paragraph)
            
            # If adding this paragraph exceeds target size, finalize current chunk
            if current_size + para_size > self.target_chunk_size and current_chunk:
                chunks.append('\n\n'.join(current_chunk))
                current_chunk = [paragraph]
                current_size = para_size
            else:
                current_chunk.append(paragraph)
                current_size += para_size
        
        # Add remaining chunk
        if current_chunk:
            chunks.append('\n\n'.join(current_chunk))
        
        return chunks if chunks else [content]
    
    def _adjust_chunk_sizes(self, chunks: List[str]) -> List[str]:
        """Adjust chunk sizes to meet requirements"""
        adjusted_chunks = []
        
        i = 0
        while i < len(chunks):
            chunk = chunks[i]
            
            # If chunk is too small, try to merge with next
            if len(chunk) < self.min_chunk_size and i + 1 < len(chunks):
                next_chunk = chunks[i + 1]
                if len(chunk) + len(next_chunk) <= self.max_chunk_size:
                    merged = chunk + '\n\n' + next_chunk
                    adjusted_chunks.append(merged)
                    i += 2  # Skip next chunk as it's merged
                    continue
            
            # If chunk is too large, split it
            if len(chunk) > self.max_chunk_size:
                # Simple character-based splitting for oversized chunks
                split_chunks = self._split_oversized_chunk(chunk)
                adjusted_chunks.extend(split_chunks)
            else:
                adjusted_chunks.append(chunk)
            
            i += 1
        
        return adjusted_chunks
    
    def _split_oversized_chunk(self, chunk: str) -> List[str]:
        """Split an oversized chunk while preserving sentence boundaries"""
        sentences = re.split(r'(?<=[.!?])\s+', chunk)
        
        chunks = []
        current_chunk = []
        current_size = 0
        
        for sentence in sentences:
            sentence_size = len(sentence)
            
            if current_size + sentence_size > self.max_chunk_size and current_chunk:
                chunks.append(' '.join(current_chunk))
                current_chunk = [sentence]
                current_size = sentence_size
            else:
                current_chunk.append(sentence)
                current_size += sentence_size
        
        if current_chunk:
            chunks.append(' '.join(current_chunk))
        
        return chunks
    
    def _create_node_relationships(self, 
                                 chunks: List[SemanticChunk],
                                 node: NavigationNode,
                                 navigation_structure: NavigationStructure) -> List[Dict[str, Any]]:
        """Create relationships for chunks within a node"""
        relationships = []
        
        # Sequential relationships between chunks in same node
        for i in range(len(chunks) - 1):
            relationships.append({
                'from_chunk': chunks[i].chunk_id,
                'to_chunk': chunks[i + 1].chunk_id,
                'relationship_type': 'SEQUENTIAL',
                'metadata': {
                    'source_node': node.node_id,
                    'sequence_index': i
                }
            })
        
        # Parent-child relationships to chunks in child nodes
        for child_id in node.children:
            if child_id in navigation_structure.nodes:
                relationships.append({
                    'from_chunk': chunks[0].chunk_id if chunks else None,
                    'to_node': child_id,
                    'relationship_type': 'PARENT_CHILD',
                    'metadata': {
                        'parent_node': node.node_id,
                        'child_node': child_id
                    }
                })
        
        return relationships
    
    def _create_cross_chunk_relationships(self, chunks: List[SemanticChunk]) -> List[Dict[str, Any]]:
        """Create relationships between chunks across different nodes"""
        relationships = []
        
        # Find decision chunks that reference other chunks
        decision_chunks = [c for c in chunks if c.chunk_type == ChunkType.DECISION]
        
        for decision_chunk in decision_chunks:
            # Look for references to other sections in decision content
            for other_chunk in chunks:
                if (other_chunk.chunk_id != decision_chunk.chunk_id and
                    self._chunks_are_related(decision_chunk, other_chunk)):
                    
                    relationships.append({
                        'from_chunk': decision_chunk.chunk_id,
                        'to_chunk': other_chunk.chunk_id,
                        'relationship_type': 'REFERENCES',
                        'metadata': {
                            'reference_type': 'decision_reference',
                            'confidence': 0.8
                        }
                    })
        
        return relationships
    
    def _post_process_chunks(self, 
                           chunks: List[SemanticChunk],
                           navigation_structure: NavigationStructure) -> List[SemanticChunk]:
        """Post-process chunks for quality and consistency"""
        
        # Add overlap information
        for i, chunk in enumerate(chunks):
            # Find overlapping chunks
            overlaps = self._find_overlapping_chunks(chunk, chunks)
            chunk.overlap_with = overlaps
        
        # Sort chunks by navigation order
        chunks = self._sort_chunks_by_navigation_order(chunks, navigation_structure)
        
        return chunks
    
    def _build_navigation_path(self, 
                             node: NavigationNode,
                             navigation_structure: NavigationStructure) -> List[str]:
        """Build full navigation path for a node"""
        path = []
        current_node = node
        
        while current_node:
            path.insert(0, current_node.title)
            
            if current_node.parent_id and current_node.parent_id in navigation_structure.nodes:
                current_node = navigation_structure.nodes[current_node.parent_id]
            else:
                break
        
        return path
    
    def _calculate_chunk_quality(self, chunk: SemanticChunk, node: NavigationNode) -> float:
        """Calculate quality score for a chunk"""
        score = 0.8  # Base score
        
        # Bonus for appropriate size
        if self.min_chunk_size <= len(chunk.content) <= self.max_chunk_size:
            score += 0.1
        
        # Bonus for complete sentences
        if chunk.content.strip().endswith(('.', '!', '?')):
            score += 0.05
        
        # Bonus for decision chunks with clear outcomes
        if chunk.chunk_type == ChunkType.DECISION:
            decision_outcomes = ['approve', 'decline', 'refer']
            if any(outcome in chunk.content.lower() for outcome in decision_outcomes):
                score += 0.05
        
        return min(score, 1.0)
    
    def _calculate_quality_metrics(self, 
                                 chunks: List[SemanticChunk],
                                 navigation_structure: NavigationStructure) -> Dict[str, Any]:
        """Calculate overall quality metrics for chunking result"""
        if not chunks:
            return {'overall_quality': 0.0}
        
        # Size distribution
        sizes = [len(chunk.content) for chunk in chunks]
        avg_size = sum(sizes) / len(sizes)
        size_variance = sum((size - avg_size) ** 2 for size in sizes) / len(sizes)
        
        # Quality scores
        quality_scores = [chunk.context.quality_score for chunk in chunks]
        avg_quality = sum(quality_scores) / len(quality_scores)
        
        # Type distribution
        type_counts = {}
        for chunk in chunks:
            type_counts[chunk.chunk_type.value] = type_counts.get(chunk.chunk_type.value, 0) + 1
        
        # Coverage (how many navigation nodes have chunks)
        nodes_with_chunks = len(set(chunk.node_id for chunk in chunks if chunk.node_id))
        total_nodes = len(navigation_structure.nodes) - 1  # Exclude root
        coverage = nodes_with_chunks / total_nodes if total_nodes > 0 else 0
        
        return {
            'overall_quality': avg_quality,
            'average_chunk_size': avg_size,
            'size_variance': size_variance,
            'coverage': coverage,
            'chunk_type_distribution': type_counts,
            'total_chunks': len(chunks),
            'nodes_covered': nodes_with_chunks,
            'total_nodes': total_nodes
        }
    
    # Utility helper methods
    
    def _clean_content(self, content: str) -> str:
        """Clean and normalize content"""
        # Remove excessive whitespace
        content = re.sub(r'\s+', ' ', content)
        # Remove empty lines
        content = re.sub(r'\n\s*\n', '\n\n', content)
        return content.strip()
    
    def _generate_chunk_id(self, node: NavigationNode, chunk_index: int) -> str:
        """Generate unique chunk ID"""
        base = f"{node.node_id}_chunk_{chunk_index:03d}"
        return base
    
    def _is_heading_line(self, line: str) -> bool:
        """Check if a line is a heading"""
        return bool(re.match(r'^\d+\..*|^[A-Z]+\..*|^#+\s', line.strip()))
    
    def _contains_decision_language(self, content: str) -> bool:
        """Check if content contains decision-making language"""
        decision_patterns = [
            r'\b(if|when|unless|provided that)\b',
            r'\b(approve|decline|refer)\b',
            r'\b(must|shall|should|may|cannot)\b'
        ]
        return any(re.search(pattern, content, re.IGNORECASE) for pattern in decision_patterns)
    
    def _contains_matrix_language(self, content: str) -> bool:
        """Check if content contains matrix/table language"""
        matrix_patterns = [
            r'\b(matrix|table|grid)\b',
            r'\b(row|column|cell)\b',
            r'\|.*\|',  # Table separator
            r'^\s*[-+]{3,}'  # Table border
        ]
        return any(re.search(pattern, content, re.IGNORECASE | re.MULTILINE) for pattern in matrix_patterns)
    
    def _contains_reference_language(self, content: str) -> bool:
        """Check if content contains reference language"""
        reference_patterns = [
            r'\bsee\s+(section|chapter|appendix)\b',
            r'\brefer\s+to\b',
            r'\bas\s+defined\s+in\b',
            r'\baccording\s+to\b'
        ]
        return any(re.search(pattern, content, re.IGNORECASE) for pattern in reference_patterns)
    
    def _is_matrix_row_complete(self, line: str) -> bool:
        """Check if a matrix row is complete"""
        # Simple heuristic: line ends with decision outcome or separator
        return bool(re.search(r'(approve|decline|refer|\|)$', line.strip(), re.IGNORECASE))
    
    def _chunks_are_related(self, chunk1: SemanticChunk, chunk2: SemanticChunk) -> bool:
        """Check if two chunks are semantically related"""
        # Simple approach: check for section number references
        if chunk2.context.section_number:
            return chunk2.context.section_number in chunk1.content
        
        # Check for title references
        if chunk2.context.parent_section:
            return chunk2.context.parent_section.lower() in chunk1.content.lower()
        
        return False
    
    def _find_overlapping_chunks(self, 
                               target_chunk: SemanticChunk,
                               all_chunks: List[SemanticChunk]) -> List[str]:
        """Find chunks that overlap with target chunk"""
        overlaps = []
        
        for chunk in all_chunks:
            if (chunk.chunk_id != target_chunk.chunk_id and
                chunk.node_id == target_chunk.node_id):
                overlaps.append(chunk.chunk_id)
        
        return overlaps
    
    def _sort_chunks_by_navigation_order(self, 
                                       chunks: List[SemanticChunk],
                                       navigation_structure: NavigationStructure) -> List[SemanticChunk]:
        """Sort chunks by navigation order"""
        def sort_key(chunk):
            if not chunk.node_id or chunk.node_id not in navigation_structure.nodes:
                return (999, 999)  # Put unknown chunks at end
            
            node = navigation_structure.nodes[chunk.node_id]
            line_num = node.metadata.get('line_number', 999)
            chunk_index = chunk.metadata.get('chunk_index', 0)
            
            return (line_num, chunk_index)
        
        return sorted(chunks, key=sort_key)