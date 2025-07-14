# Task 7: Navigation Extractor Implementation
# This file implements hierarchical document structure extraction for mortgage guidelines

from typing import List, Dict, Any, Optional, Tuple, Union
from dataclasses import dataclass, asdict
from enum import Enum
import re
import json
import logging
from datetime import datetime
import hashlib
from pathlib import Path


class DocumentFormat(Enum):
    """Supported document formats"""
    PDF = "pdf"
    DOCX = "docx"
    HTML = "html"
    TEXT = "text"
    UNKNOWN = "unknown"


class NavigationLevel(Enum):
    """Hierarchy levels for navigation structure"""
    DOCUMENT = 0      # Document root
    CHAPTER = 1       # Major sections/chapters
    SECTION = 2       # Main sections
    SUBSECTION = 3    # Subsections
    PARAGRAPH = 4     # Paragraph level
    ITEM = 5         # List items/specific rules


@dataclass
class NavigationNode:
    """Represents a node in the document navigation structure"""
    node_id: str
    title: str
    level: NavigationLevel
    parent_id: Optional[str] = None
    children: List[str] = None
    content: str = ""
    page_number: Optional[int] = None
    section_number: Optional[str] = None
    decision_type: Optional[str] = None  # For decision trees: ROOT, BRANCH, LEAF
    decision_outcome: Optional[str] = None  # For decision trees: APPROVE, DECLINE, REFER
    extracted_entities: List[str] = None
    confidence_score: float = 0.0
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.children is None:
            self.children = []
        if self.extracted_entities is None:
            self.extracted_entities = []
        if self.metadata is None:
            self.metadata = {}
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        result = asdict(self)
        result['level'] = self.level.value
        return result
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'NavigationNode':
        """Create from dictionary"""
        data = data.copy()
        data['level'] = NavigationLevel(data['level'])
        return cls(**data)


@dataclass
class TableOfContents:
    """Represents extracted table of contents"""
    entries: List[Dict[str, Any]]
    format_detected: str
    confidence_score: float
    extraction_method: str
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return asdict(self)


@dataclass
class NavigationStructure:
    """Complete navigation structure for a document"""
    document_id: str
    document_format: DocumentFormat
    root_node: NavigationNode
    nodes: Dict[str, NavigationNode]
    table_of_contents: Optional[TableOfContents] = None
    decision_trees: List[Dict[str, Any]] = None
    extraction_metadata: Dict[str, Any] = None
    validation_results: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.decision_trees is None:
            self.decision_trees = []
        if self.extraction_metadata is None:
            self.extraction_metadata = {}
        if self.validation_results is None:
            self.validation_results = {}
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        result = {
            'document_id': self.document_id,
            'document_format': self.document_format.value,
            'root_node': self.root_node.to_dict(),
            'nodes': {node_id: node.to_dict() for node_id, node in self.nodes.items()},
            'table_of_contents': self.table_of_contents.to_dict() if self.table_of_contents else None,
            'decision_trees': self.decision_trees,
            'extraction_metadata': self.extraction_metadata,
            'validation_results': self.validation_results
        }
        return result


class NavigationExtractor:
    """Extracts hierarchical navigation structure from mortgage guideline documents"""
    
    def __init__(self, llm_client=None, package_category: str = None):
        """Initialize NavigationExtractor
        
        Args:
            llm_client: LLM client for intelligent structure extraction
            package_category: Package category (NQM, RTL, SBC, CONV) for context-aware processing
        """
        self.llm_client = llm_client
        self.package_category = package_category
        self.logger = logging.getLogger(__name__)
        
        # Heading patterns for different formats
        self.heading_patterns = {
            'numbered_sections': [
                r'^(\d+\.)+\s*(.+)$',  # 1.1.1 Section Title
                r'^([A-Z]+\.)+\s*(.+)$',  # A.1 Section Title
                r'^([IVX]+\.)+\s*(.+)$',  # I.1 Section Title
            ],
            'formatted_headings': [
                r'^#+\s*(.+)$',  # Markdown headings
                r'^(.+)\n=+$',   # Underlined headings
                r'^(.+)\n-+$',   # Underlined headings
            ],
            'decision_indicators': [
                r'(if|when|where|unless|provided that|subject to)',
                r'(approve|decline|refer|eligible|ineligible)',
                r'(must|shall|should|may|cannot|prohibited)',
            ],
            'toc_patterns': [
                r'table\s+of\s+contents',
                r'contents',
                r'index',
                r'outline',
            ]
        }
        
        # Document format detection patterns
        self.format_indicators = {
            DocumentFormat.PDF: ['.pdf', 'pdf'],
            DocumentFormat.DOCX: ['.docx', '.doc', 'word'],
            DocumentFormat.HTML: ['.html', '.htm', '<html', '<body'],
            DocumentFormat.TEXT: ['.txt', '.text']
        }
    
    def extract_navigation_structure(self, 
                                   document_content: str, 
                                   document_name: str = None,
                                   format_hint: str = None) -> NavigationStructure:
        """Extract complete navigation structure from document
        
        Args:
            document_content: Raw document content
            document_name: Optional document name for context
            format_hint: Optional format hint (pdf, docx, html, text)
            
        Returns:
            NavigationStructure: Complete extracted navigation structure
            
        Raises:
            ValueError: If document content is invalid
            Exception: If extraction fails
        """
        try:
            start_time = datetime.now()
            self.logger.info(f"Starting navigation extraction for document: {document_name}")
            
            # Detect document format
            document_format = self._detect_document_format(document_content, format_hint)
            
            # Generate document ID
            document_id = self._generate_document_id(document_name, document_content)
            
            # Extract table of contents first (helps with structure detection)
            toc = self.extract_table_of_contents(document_content, document_format)
            
            # Extract hierarchical structure
            nodes = self._extract_hierarchical_nodes(document_content, document_format, toc)
            
            # Build navigation tree
            root_node, node_dict = self._build_navigation_tree(nodes, document_id)
            
            # Extract decision trees
            decision_trees = self._extract_decision_trees(document_content, nodes)
            
            # Create navigation structure
            structure = NavigationStructure(
                document_id=document_id,
                document_format=document_format,
                root_node=root_node,
                nodes=node_dict,
                table_of_contents=toc,
                decision_trees=decision_trees,
                extraction_metadata={
                    'extraction_time': (datetime.now() - start_time).total_seconds(),
                    'document_name': document_name,
                    'package_category': self.package_category,
                    'total_nodes': len(node_dict),
                    'max_depth': self._calculate_max_depth(node_dict)
                }
            )
            
            # Validate structure
            structure.validation_results = self.validate_navigation_structure(structure)
            
            self.logger.info(f"Navigation extraction completed: {len(node_dict)} nodes extracted")
            return structure
            
        except Exception as e:
            self.logger.error(f"Failed to extract navigation structure: {str(e)}")
            raise
    
    def detect_heading_patterns(self, text: str) -> List[Dict[str, Any]]:
        """Detect heading patterns in text using regex
        
        Args:
            text: Text content to analyze
            
        Returns:
            List of detected headings with metadata
        """
        try:
            detected_headings = []
            lines = text.split('\n')
            
            for line_num, line in enumerate(lines):
                line = line.strip()
                if not line:
                    continue
                
                # Check numbered sections
                for pattern in self.heading_patterns['numbered_sections']:
                    match = re.match(pattern, line, re.IGNORECASE)
                    if match:
                        section_number = match.group(1).rstrip('.')
                        title = match.group(2).strip()
                        level = self._determine_heading_level(section_number)
                        
                        detected_headings.append({
                            'line_number': line_num + 1,
                            'section_number': section_number,
                            'title': title,
                            'level': level,
                            'pattern_type': 'numbered_section',
                            'confidence': 0.9,
                            'full_text': line
                        })
                        break
                
                # Check formatted headings
                for pattern in self.heading_patterns['formatted_headings']:
                    match = re.match(pattern, line)
                    if match:
                        title = match.group(1).strip()
                        level = self._determine_heading_level_by_format(line)
                        
                        detected_headings.append({
                            'line_number': line_num + 1,
                            'section_number': None,
                            'title': title,
                            'level': level,
                            'pattern_type': 'formatted_heading',
                            'confidence': 0.8,
                            'full_text': line
                        })
                        break
                
                # Check for decision indicators
                for pattern in self.heading_patterns['decision_indicators']:
                    if re.search(pattern, line, re.IGNORECASE):
                        detected_headings.append({
                            'line_number': line_num + 1,
                            'section_number': None,
                            'title': line,
                            'level': NavigationLevel.PARAGRAPH,
                            'pattern_type': 'decision_indicator',
                            'confidence': 0.7,
                            'full_text': line,
                            'decision_indicator': True
                        })
                        break
            
            self.logger.info(f"Detected {len(detected_headings)} heading patterns")
            return detected_headings
            
        except Exception as e:
            self.logger.error(f"Failed to detect heading patterns: {str(e)}")
            return []
    
    def extract_table_of_contents(self, 
                                document_content: str, 
                                document_format: DocumentFormat) -> Optional[TableOfContents]:
        """Extract table of contents from document
        
        Args:
            document_content: Document content
            document_format: Detected document format
            
        Returns:
            TableOfContents or None if not found
        """
        try:
            self.logger.info("Extracting table of contents")
            
            # Look for TOC indicators
            toc_section = self._find_toc_section(document_content)
            if not toc_section:
                self.logger.info("No table of contents found")
                return None
            
            # Extract entries based on format
            if document_format == DocumentFormat.HTML:
                entries = self._extract_html_toc(toc_section)
                method = "html_parsing"
            elif document_format == DocumentFormat.PDF:
                entries = self._extract_pdf_toc(toc_section)
                method = "pdf_parsing"
            else:
                entries = self._extract_text_toc(toc_section)
                method = "text_parsing"
            
            if not entries:
                return None
            
            # Calculate confidence score
            confidence = self._calculate_toc_confidence(entries)
            
            toc = TableOfContents(
                entries=entries,
                format_detected=document_format.value,
                confidence_score=confidence,
                extraction_method=method
            )
            
            self.logger.info(f"Extracted TOC with {len(entries)} entries (confidence: {confidence:.2f})")
            return toc
            
        except Exception as e:
            self.logger.error(f"Failed to extract table of contents: {str(e)}")
            return None
    
    def validate_navigation_structure(self, structure: NavigationStructure) -> Dict[str, Any]:
        """Validate navigation structure for completeness and quality
        
        Args:
            structure: NavigationStructure to validate
            
        Returns:
            Dictionary with validation results
        """
        try:
            validation_results = {
                'is_valid': True,
                'issues': [],
                'warnings': [],
                'quality_metrics': {},
                'completeness_score': 0.0,
                'structure_score': 0.0
            }
            
            # Check basic structure
            if not structure.root_node:
                validation_results['issues'].append("Missing root node")
                validation_results['is_valid'] = False
            
            if not structure.nodes:
                validation_results['issues'].append("No navigation nodes found")
                validation_results['is_valid'] = False
                return validation_results
            
            # Validate node relationships
            orphaned_nodes = self._find_orphaned_nodes(structure.nodes, structure.root_node.node_id)
            if orphaned_nodes:
                validation_results['warnings'].append(f"Found {len(orphaned_nodes)} orphaned nodes")
            
            # Check depth consistency
            max_depth = self._calculate_max_depth(structure.nodes)
            if max_depth > 6:
                validation_results['warnings'].append(f"Deep nesting detected: {max_depth} levels")
            
            # Check for decision tree completeness
            decision_completeness = self._validate_decision_trees(structure.decision_trees)
            if decision_completeness < 0.8:
                validation_results['warnings'].append("Incomplete decision trees detected")
            
            # Calculate quality metrics
            validation_results['quality_metrics'] = {
                'total_nodes': len(structure.nodes),
                'max_depth': max_depth,
                'orphaned_nodes': len(orphaned_nodes),
                'decision_tree_count': len(structure.decision_trees),
                'decision_completeness': decision_completeness,
                'has_toc': structure.table_of_contents is not None,
                'toc_confidence': structure.table_of_contents.confidence_score if structure.table_of_contents else 0.0
            }
            
            # Calculate overall scores
            validation_results['completeness_score'] = self._calculate_completeness_score(validation_results['quality_metrics'])
            validation_results['structure_score'] = self._calculate_structure_score(validation_results['quality_metrics'])
            
            self.logger.info(f"Validation completed - Valid: {validation_results['is_valid']}, "
                           f"Completeness: {validation_results['completeness_score']:.2f}")
            
            return validation_results
            
        except Exception as e:
            self.logger.error(f"Failed to validate navigation structure: {str(e)}")
            return {
                'is_valid': False,
                'issues': [f"Validation failed: {str(e)}"],
                'warnings': [],
                'quality_metrics': {},
                'completeness_score': 0.0,
                'structure_score': 0.0
            }
    
    # Private helper methods
    
    def _detect_document_format(self, content: str, format_hint: str = None) -> DocumentFormat:
        """Detect document format from content and hints"""
        if format_hint:
            format_hint = format_hint.lower()
            for fmt, indicators in self.format_indicators.items():
                if any(indicator in format_hint for indicator in indicators):
                    return fmt
        
        # Analyze content for format indicators
        content_lower = content.lower()
        
        if any(indicator in content_lower for indicator in self.format_indicators[DocumentFormat.HTML]):
            return DocumentFormat.HTML
        
        # Default to text format
        return DocumentFormat.TEXT
    
    def _generate_document_id(self, document_name: str, content: str) -> str:
        """Generate unique document ID"""
        if document_name:
            base = f"{document_name}_{len(content)}"
        else:
            base = f"doc_{len(content)}"
        
        # Add hash for uniqueness
        content_hash = hashlib.md5(content.encode()).hexdigest()[:8]
        return f"{base}_{content_hash}"
    
    def _extract_hierarchical_nodes(self, 
                                  content: str, 
                                  document_format: DocumentFormat,
                                  toc: Optional[TableOfContents]) -> List[NavigationNode]:
        """Extract hierarchical nodes from document content"""
        nodes = []
        
        # Get heading patterns
        headings = self.detect_heading_patterns(content)
        
        # Convert headings to navigation nodes
        for i, heading in enumerate(headings):
            node_id = f"node_{i+1:04d}"
            
            node = NavigationNode(
                node_id=node_id,
                title=heading['title'],
                level=heading['level'],
                section_number=heading.get('section_number'),
                content=heading['full_text'],
                confidence_score=heading['confidence'],
                metadata={
                    'line_number': heading['line_number'],
                    'pattern_type': heading['pattern_type'],
                    'decision_indicator': heading.get('decision_indicator', False)
                }
            )
            
            nodes.append(node)
        
        return nodes
    
    def _build_navigation_tree(self, nodes: List[NavigationNode], document_id: str) -> Tuple[NavigationNode, Dict[str, NavigationNode]]:
        """Build hierarchical navigation tree from flat node list"""
        # Create root node
        root_node = NavigationNode(
            node_id=f"{document_id}_root",
            title="Document Root",
            level=NavigationLevel.DOCUMENT,
            metadata={'document_id': document_id}
        )
        
        # Create node dictionary
        node_dict = {root_node.node_id: root_node}
        
        # Add all nodes to dictionary
        for node in nodes:
            node_dict[node.node_id] = node
        
        # Build parent-child relationships
        sorted_nodes = sorted(nodes, key=lambda n: (n.metadata.get('line_number', 0), n.level.value))
        parent_stack = [root_node]
        
        for node in sorted_nodes:
            # Find appropriate parent based on level
            while len(parent_stack) > 1 and parent_stack[-1].level.value >= node.level.value:
                parent_stack.pop()
            
            parent = parent_stack[-1]
            node.parent_id = parent.node_id
            parent.children.append(node.node_id)
            parent_stack.append(node)
        
        return root_node, node_dict
    
    def _extract_decision_trees(self, content: str, nodes: List[NavigationNode]) -> List[Dict[str, Any]]:
        """Extract decision trees from document content"""
        decision_trees = []
        
        # Find nodes with decision indicators
        decision_nodes = [node for node in nodes if node.metadata.get('decision_indicator', False)]
        
        for node in decision_nodes:
            # Extract decision logic around this node
            decision_tree = {
                'root_node_id': node.node_id,
                'decision_type': 'conditional',
                'branches': self._extract_decision_branches(content, node),
                'outcomes': self._extract_decision_outcomes(content, node)
            }
            
            decision_trees.append(decision_tree)
        
        return decision_trees
    
    def _extract_decision_branches(self, content: str, node: NavigationNode) -> List[Dict[str, Any]]:
        """Extract decision branches for a decision node"""
        # Simplified branch extraction - can be enhanced with LLM
        return []
    
    def _extract_decision_outcomes(self, content: str, node: NavigationNode) -> List[str]:
        """Extract decision outcomes (APPROVE, DECLINE, REFER)"""
        outcomes = []
        
        # Look for outcome indicators in content around the node
        outcome_patterns = [
            r'approve[d]?',
            r'decline[d]?',
            r'refer[red]?',
            r'eligible',
            r'ineligible'
        ]
        
        for pattern in outcome_patterns:
            if re.search(pattern, content, re.IGNORECASE):
                outcomes.append(pattern.upper())
        
        return list(set(outcomes))
    
    def _determine_heading_level(self, section_number: str) -> NavigationLevel:
        """Determine heading level from section number"""
        dots = section_number.count('.')
        
        if dots == 0:
            return NavigationLevel.CHAPTER
        elif dots == 1:
            return NavigationLevel.SECTION
        elif dots == 2:
            return NavigationLevel.SUBSECTION
        else:
            return NavigationLevel.PARAGRAPH
    
    def _determine_heading_level_by_format(self, line: str) -> NavigationLevel:
        """Determine heading level from formatting"""
        if line.startswith('###'):
            return NavigationLevel.SUBSECTION
        elif line.startswith('##'):
            return NavigationLevel.SECTION
        elif line.startswith('#'):
            return NavigationLevel.CHAPTER
        else:
            return NavigationLevel.PARAGRAPH
    
    def _find_toc_section(self, content: str) -> Optional[str]:
        """Find table of contents section in document"""
        lines = content.split('\n')
        
        for i, line in enumerate(lines):
            for pattern in self.heading_patterns['toc_patterns']:
                if re.search(pattern, line, re.IGNORECASE):
                    # Extract TOC section (next 50 lines or until next major heading)
                    toc_lines = []
                    for j in range(i, min(i + 50, len(lines))):
                        toc_lines.append(lines[j])
                        
                        # Stop at next major heading
                        if j > i and re.match(r'^\d+\.', lines[j].strip()):
                            break
                    
                    return '\n'.join(toc_lines)
        
        return None
    
    def _extract_html_toc(self, toc_section: str) -> List[Dict[str, Any]]:
        """Extract TOC entries from HTML content"""
        # Simplified HTML TOC extraction
        return []
    
    def _extract_pdf_toc(self, toc_section: str) -> List[Dict[str, Any]]:
        """Extract TOC entries from PDF content"""
        # Simplified PDF TOC extraction
        return []
    
    def _extract_text_toc(self, toc_section: str) -> List[Dict[str, Any]]:
        """Extract TOC entries from text content"""
        entries = []
        lines = toc_section.split('\n')
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Look for patterns like "1.1 Section Title ........ 5"
            match = re.match(r'^(\d+\.[\d\.]*)\s+(.+?)\s+\.{2,}\s*(\d+)$', line)
            if match:
                entries.append({
                    'section_number': match.group(1),
                    'title': match.group(2).strip(),
                    'page_number': int(match.group(3))
                })
            else:
                # Look for simpler patterns
                match = re.match(r'^(\d+\.[\d\.]*)\s+(.+)$', line)
                if match:
                    entries.append({
                        'section_number': match.group(1),
                        'title': match.group(2).strip(),
                        'page_number': None
                    })
        
        return entries
    
    def _calculate_toc_confidence(self, entries: List[Dict[str, Any]]) -> float:
        """Calculate confidence score for TOC extraction"""
        if not entries:
            return 0.0
        
        # Base confidence on number of entries and completeness
        entry_score = min(len(entries) / 10.0, 1.0)  # Up to 10 entries for full score
        
        # Bonus for page numbers
        pages_score = sum(1 for entry in entries if entry.get('page_number')) / len(entries)
        
        # Bonus for section numbers
        sections_score = sum(1 for entry in entries if entry.get('section_number')) / len(entries)
        
        return (entry_score + pages_score + sections_score) / 3.0
    
    def _find_orphaned_nodes(self, nodes: Dict[str, NavigationNode], root_id: str) -> List[str]:
        """Find nodes without proper parent relationships"""
        orphaned = []
        
        for node_id, node in nodes.items():
            if node_id == root_id:
                continue
            
            if not node.parent_id or node.parent_id not in nodes:
                orphaned.append(node_id)
        
        return orphaned
    
    def _calculate_max_depth(self, nodes: Dict[str, NavigationNode]) -> int:
        """Calculate maximum depth of navigation tree"""
        max_depth = 0
        
        for node in nodes.values():
            if node.level != NavigationLevel.DOCUMENT:
                max_depth = max(max_depth, node.level.value)
        
        return max_depth
    
    def _validate_decision_trees(self, decision_trees: List[Dict[str, Any]]) -> float:
        """Validate completeness of decision trees"""
        if not decision_trees:
            return 0.0
        
        # Simple completeness check
        complete_trees = 0
        for tree in decision_trees:
            if tree.get('outcomes') and tree.get('branches'):
                complete_trees += 1
        
        return complete_trees / len(decision_trees)
    
    def _calculate_completeness_score(self, metrics: Dict[str, Any]) -> float:
        """Calculate overall completeness score"""
        score = 0.0
        total_weight = 0.0
        
        # Weight different aspects
        if metrics.get('has_toc'):
            score += 0.3 * metrics.get('toc_confidence', 0.0)
        total_weight += 0.3
        
        if metrics.get('total_nodes', 0) > 0:
            score += 0.4 * min(metrics['total_nodes'] / 20.0, 1.0)
        total_weight += 0.4
        
        if metrics.get('decision_tree_count', 0) > 0:
            score += 0.3 * metrics.get('decision_completeness', 0.0)
        total_weight += 0.3
        
        return score / total_weight if total_weight > 0 else 0.0
    
    def _calculate_structure_score(self, metrics: Dict[str, Any]) -> float:
        """Calculate structure quality score"""
        score = 1.0
        
        # Penalize orphaned nodes
        if metrics.get('orphaned_nodes', 0) > 0:
            score -= 0.2 * (metrics['orphaned_nodes'] / metrics.get('total_nodes', 1))
        
        # Penalize excessive depth
        max_depth = metrics.get('max_depth', 0)
        if max_depth > 5:
            score -= 0.1 * (max_depth - 5)
        
        return max(score, 0.0)