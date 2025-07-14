# Task 14: Guidelines Entity Extractor Implementation
# Extract mortgage-specific entities with navigation context preservation

from typing import List, Dict, Any, Optional, Set, Tuple
from dataclasses import dataclass, field
from datetime import datetime
import logging
import re
import json
import uuid
from enum import Enum

# Import existing entities and models
from src.entities.navigation_models import (
    EnhancedNavigationNode,
    HierarchicalChunk,
    NavigationContext,
    QualityRating
)
from src.llm import get_llm
from src.navigation_graph import NavigationGraphBuilder
from src.decision_tree_extractor import DecisionTreeExtractor


class EntityType(Enum):
    """Mortgage-specific entity types for guidelines processing"""
    # Loan and borrower entities
    LOAN_PROGRAM = "LOAN_PROGRAM"
    BORROWER_TYPE = "BORROWER_TYPE"
    INCOME_TYPE = "INCOME_TYPE"
    CREDIT_REQUIREMENT = "CREDIT_REQUIREMENT"
    
    # Financial entities
    NUMERIC_THRESHOLD = "NUMERIC_THRESHOLD"
    FINANCIAL_RATIO = "FINANCIAL_RATIO"
    DOLLAR_AMOUNT = "DOLLAR_AMOUNT"
    PERCENTAGE = "PERCENTAGE"
    
    # Property entities
    PROPERTY_TYPE = "PROPERTY_TYPE"
    OCCUPANCY_TYPE = "OCCUPANCY_TYPE"
    LOCATION_REQUIREMENT = "LOCATION_REQUIREMENT"
    PROPERTY_STANDARD = "PROPERTY_STANDARD"
    
    # Document and process entities
    DOCUMENT_TYPE = "DOCUMENT_TYPE"
    REQUIREMENT = "REQUIREMENT"
    VALIDATION_RULE = "VALIDATION_RULE"
    PROCESS_STEP = "PROCESS_STEP"
    
    # Decision entities
    DECISION_CRITERIA = "DECISION_CRITERIA"
    APPROVAL_CONDITION = "APPROVAL_CONDITION"
    DECLINE_REASON = "DECLINE_REASON"
    REFER_CONDITION = "REFER_CONDITION"
    
    # Matrix entities
    MATRIX_VALUE = "MATRIX_VALUE"
    MATRIX_DIMENSION = "MATRIX_DIMENSION"
    THRESHOLD = "THRESHOLD"
    CONDITION = "CONDITION"
    
    # Organization entities
    INVESTOR_REQUIREMENT = "INVESTOR_REQUIREMENT"
    AGENCY_GUIDELINE = "AGENCY_GUIDELINE"
    STATE_REQUIREMENT = "STATE_REQUIREMENT"
    DISCLOSURE = "DISCLOSURE"


@dataclass
class ExtractedEntity:
    """Represents an extracted entity with context and metadata"""
    entity_id: str
    entity_text: str
    entity_type: EntityType
    confidence_score: float
    
    # Context information
    source_chunk_id: Optional[str] = None
    navigation_context: Optional[NavigationContext] = None
    start_position: int = 0
    end_position: int = 0
    
    # Entity relationships
    related_entities: List[str] = field(default_factory=list)
    parent_entity_id: Optional[str] = None
    child_entity_ids: List[str] = field(default_factory=list)
    
    # Additional metadata
    normalized_value: Optional[str] = None
    validation_status: str = "pending"
    extraction_method: str = "pattern"
    quality_score: float = 0.0
    
    # Mortgage-specific attributes
    financial_value: Optional[float] = None
    unit_of_measure: Optional[str] = None
    condition_context: Optional[str] = None
    decision_impact: Optional[str] = None


@dataclass
class EntityExtractionResult:
    """Result of entity extraction operation"""
    success: bool
    entities: List[ExtractedEntity] = field(default_factory=list)
    entity_relationships: List[Dict[str, Any]] = field(default_factory=list)
    extraction_metrics: Dict[str, Any] = field(default_factory=dict)
    validation_errors: List[str] = field(default_factory=list)
    validation_warnings: List[str] = field(default_factory=list)
    processing_time_ms: int = 0


@dataclass
class EntityExtractionMetrics:
    """Metrics for entity extraction quality and completeness"""
    total_entities: int = 0
    entities_by_type: Dict[EntityType, int] = field(default_factory=dict)
    avg_confidence_score: float = 0.0
    navigation_coverage: float = 0.0  # Percentage of navigation nodes with entities
    validation_success_rate: float = 0.0
    relationship_accuracy: float = 0.0
    processing_efficiency: float = 0.0  # Entities per second


class GuidelineEntityExtractor:
    """
    Extracts mortgage-specific entities with navigation context preservation.
    Provides contextual entity extraction for guidelines processing.
    """
    
    def __init__(self, llm_model: str = "claude-sonnet-4"):
        """
        Initialize GuidelineEntityExtractor
        
        Args:
            llm_model: LLM model to use for entity extraction
        """
        self.llm = get_llm(llm_model)
        self.logger = logging.getLogger(__name__)
        
        # Entity extraction patterns
        self.entity_patterns = self._initialize_entity_patterns()
        
        # Mortgage domain vocabulary
        self.domain_vocabulary = self._initialize_domain_vocabulary()
        
        # Entity validation rules
        self.validation_rules = self._initialize_validation_rules()

    def _initialize_entity_patterns(self) -> Dict[EntityType, List[str]]:
        """Initialize regex patterns for entity extraction"""
        return {
            EntityType.NUMERIC_THRESHOLD: [
                r'(?i)(credit score|fico score|score)\s*[><=≥≤]+\s*(\d+)',
                r'(?i)(ltv|loan.to.value)\s*[><=≥≤]+\s*(\d+(?:\.\d+)?%?)',
                r'(?i)(dti|debt.to.income)\s*[><=≥≤]+\s*(\d+(?:\.\d+)?%?)',
                r'(?i)(income)\s*[><=≥≤]+\s*\$?(\d+(?:,\d{3})*)',
                r'(?i)(employment|work)\s+.*?(\d+)\s+years?',
                r'(?i)(assets?)\s*[><=≥≤]+\s*\$?(\d+(?:,\d{3})*)'
            ],
            EntityType.DOLLAR_AMOUNT: [
                r'\$(\d+(?:,\d{3})*(?:\.\d{2})?)',
                r'(?i)(loan amount|purchase price|appraised value)\s*:?\s*\$?(\d+(?:,\d{3})*)',
                r'(?i)(minimum|maximum)\s+.*?\$?(\d+(?:,\d{3})*)'
            ],
            EntityType.PERCENTAGE: [
                r'(\d+(?:\.\d+)?)\s*%',
                r'(?i)(rate|ratio|percentage)\s*:?\s*(\d+(?:\.\d+)?)\s*%?'
            ],
            EntityType.LOAN_PROGRAM: [
                r'(?i)(non.?qm|non.qualified mortgage|nqm)',
                r'(?i)(conventional|conforming)',
                r'(?i)(jumbo|super.?jumbo)',
                r'(?i)(fha|va|usda)',
                r'(?i)(investment|rental|rtl)',
                r'(?i)(commercial|sbc)'
            ],
            EntityType.BORROWER_TYPE: [
                r'(?i)(w.?2\s+employee|salaried|wage.earner)',
                r'(?i)(self.?employed|1099|independent contractor)',
                r'(?i)(retired|retiree)',
                r'(?i)(first.?time\s+buyer|first.?time\s+homebuyer)',
                r'(?i)(foreign\s+national|non.?resident)',
                r'(?i)(investor|real\s+estate\s+investor)'
            ],
            EntityType.PROPERTY_TYPE: [
                r'(?i)(single.?family\s+residence|sfr)',
                r'(?i)(condominium|condo)',
                r'(?i)(townhouse|townhome)',
                r'(?i)(manufactured\s+home|mobile\s+home)',
                r'(?i)(multi.?family|duplex|triplex|fourplex)',
                r'(?i)(commercial\s+property)',
                r'(?i)(investment\s+property)'
            ],
            EntityType.OCCUPANCY_TYPE: [
                r'(?i)(owner.?occupied|primary\s+residence)',
                r'(?i)(second\s+home|vacation\s+home)',
                r'(?i)(investment|rental|non.?owner.?occupied)'
            ],
            EntityType.DOCUMENT_TYPE: [
                r'(?i)(pay\s+stub|paystub)',
                r'(?i)(w.?2|tax\s+return)',
                r'(?i)(bank\s+statement)',
                r'(?i)(verification\s+of\s+employment|voe)',
                r'(?i)(appraisal|bpo|broker\s+price\s+opinion)',
                r'(?i)(credit\s+report)',
                r'(?i)(profit\s+and\s+loss|p&l)'
            ],
            EntityType.DECISION_CRITERIA: [
                r'(?i)(approve|approval)\s+if',
                r'(?i)(decline|denial)\s+if',
                r'(?i)(refer|referral)\s+if',
                r'(?i)(eligibility\s+criteria)',
                r'(?i)(qualification\s+requirements)',
                r'(?i)(underwriting\s+guidelines)'
            ]
        }

    def _initialize_domain_vocabulary(self) -> Dict[str, EntityType]:
        """Initialize mortgage domain vocabulary"""
        return {
            # Loan programs
            "non-qm": EntityType.LOAN_PROGRAM,
            "conventional": EntityType.LOAN_PROGRAM,
            "jumbo": EntityType.LOAN_PROGRAM,
            "investment": EntityType.LOAN_PROGRAM,
            "commercial": EntityType.LOAN_PROGRAM,
            
            # Financial terms
            "ltv": EntityType.FINANCIAL_RATIO,
            "dti": EntityType.FINANCIAL_RATIO,
            "fico": EntityType.NUMERIC_THRESHOLD,
            "credit score": EntityType.NUMERIC_THRESHOLD,
            
            # Property types
            "single family": EntityType.PROPERTY_TYPE,
            "condo": EntityType.PROPERTY_TYPE,
            "townhouse": EntityType.PROPERTY_TYPE,
            "multi-family": EntityType.PROPERTY_TYPE,
            
            # Occupancy
            "owner occupied": EntityType.OCCUPANCY_TYPE,
            "primary residence": EntityType.OCCUPANCY_TYPE,
            "second home": EntityType.OCCUPANCY_TYPE,
            "investment property": EntityType.OCCUPANCY_TYPE,
            
            # Requirements
            "employment history": EntityType.REQUIREMENT,
            "income documentation": EntityType.REQUIREMENT,
            "asset verification": EntityType.REQUIREMENT,
            "credit history": EntityType.REQUIREMENT
        }

    def _initialize_validation_rules(self) -> Dict[EntityType, Dict[str, Any]]:
        """Initialize validation rules for entity types"""
        return {
            EntityType.NUMERIC_THRESHOLD: {
                "min_confidence": 0.8,
                "require_numeric_value": True,
                "valid_ranges": {
                    "credit_score": (300, 850),
                    "ltv": (0, 100),
                    "dti": (0, 100)
                }
            },
            EntityType.DOLLAR_AMOUNT: {
                "min_confidence": 0.85,
                "require_numeric_value": True,
                "min_value": 0
            },
            EntityType.PERCENTAGE: {
                "min_confidence": 0.8,
                "require_numeric_value": True,
                "valid_range": (0, 100)
            },
            EntityType.LOAN_PROGRAM: {
                "min_confidence": 0.7,
                "require_vocabulary_match": True
            },
            EntityType.DECISION_CRITERIA: {
                "min_confidence": 0.9,
                "require_decision_context": True
            }
        }

    def extract_entities_with_context(
        self,
        navigation_nodes: List[EnhancedNavigationNode],
        hierarchical_chunks: List[HierarchicalChunk],
        package_config: Dict[str, Any] = None
    ) -> EntityExtractionResult:
        """
        Extract entities with navigation context preservation
        
        Args:
            navigation_nodes: Enhanced navigation nodes from NavigationExtractor
            hierarchical_chunks: Hierarchical chunks from SemanticChunker
            package_config: Package configuration for entity type preferences
            
        Returns:
            EntityExtractionResult: Complete extraction result with entities and metrics
        """
        start_time = datetime.now()
        self.logger.info("Starting entity extraction with navigation context")
        
        try:
            result = EntityExtractionResult(success=False)
            
            # Step 1: Extract entities from navigation nodes
            node_entities = []
            for node in navigation_nodes:
                try:
                    entities = self.extract_node_entities(node, package_config)
                    node_entities.extend(entities)
                except Exception as e:
                    result.validation_errors.append(
                        f"Failed to extract from node {node.enhanced_node_id}: {str(e)}"
                    )
            
            # Step 2: Extract entities from hierarchical chunks
            chunk_entities = []
            for chunk in hierarchical_chunks:
                try:
                    entities = self._extract_chunk_entities(chunk, package_config)
                    chunk_entities.extend(entities)
                except Exception as e:
                    result.validation_errors.append(
                        f"Failed to extract from chunk {chunk.chunk_id}: {str(e)}"
                    )
            
            # Step 3: Combine and deduplicate entities
            all_entities = node_entities + chunk_entities
            deduplicated_entities = self._deduplicate_entities(all_entities)
            
            # Step 4: Enhance entities with LLM extraction
            enhanced_entities = self._enhance_entities_with_llm(
                deduplicated_entities, navigation_nodes, hierarchical_chunks
            )
            
            # Step 5: Build entity relationships
            entity_relationships = self._build_entity_relationships(enhanced_entities)
            
            # Step 6: Validate extracted entities
            validated_entities = self._validate_entities(enhanced_entities)
            
            # Step 7: Calculate extraction metrics
            metrics = self._calculate_extraction_metrics(
                validated_entities, navigation_nodes, hierarchical_chunks
            )
            
            processing_time = (datetime.now() - start_time).total_seconds() * 1000
            
            result.success = len(result.validation_errors) == 0
            result.entities = validated_entities
            result.entity_relationships = entity_relationships
            result.extraction_metrics = metrics.__dict__
            result.processing_time_ms = int(processing_time)
            
            if result.success:
                self.logger.info(
                    f"Entity extraction completed: {len(validated_entities)} entities, "
                    f"time: {processing_time:.2f}ms"
                )
            else:
                self.logger.warning(
                    f"Entity extraction incomplete: {len(result.validation_errors)} errors"
                )
            
            return result
            
        except Exception as e:
            self.logger.error(f"Entity extraction failed: {str(e)}")
            processing_time = (datetime.now() - start_time).total_seconds() * 1000
            return EntityExtractionResult(
                success=False,
                validation_errors=[f"Extraction failed: {str(e)}"],
                processing_time_ms=int(processing_time)
            )

    def extract_node_entities(
        self,
        navigation_node: EnhancedNavigationNode,
        package_config: Dict[str, Any] = None
    ) -> List[ExtractedEntity]:
        """
        Extract entities from a specific navigation node
        
        Args:
            navigation_node: Enhanced navigation node to extract from
            package_config: Package configuration for entity preferences
            
        Returns:
            List[ExtractedEntity]: Entities found in the navigation node
        """
        entities = []
        content = navigation_node.content + " " + navigation_node.title
        
        # Extract using pattern matching
        pattern_entities = self._extract_entities_by_patterns(
            content, navigation_node.navigation_context
        )
        entities.extend(pattern_entities)
        
        # Extract using domain vocabulary
        vocab_entities = self._extract_entities_by_vocabulary(
            content, navigation_node.navigation_context
        )
        entities.extend(vocab_entities)
        
        # Extract decision-specific entities if this is a decision node
        if navigation_node.node_type == "DECISION_FLOW_SECTION":
            decision_entities = self._extract_decision_entities(
                content, navigation_node.navigation_context
            )
            entities.extend(decision_entities)
        
        # Update entities with navigation context
        for entity in entities:
            entity.source_chunk_id = navigation_node.enhanced_node_id
            entity.navigation_context = navigation_node.navigation_context
        
        return entities

    def _extract_chunk_entities(
        self,
        chunk: HierarchicalChunk,
        package_config: Dict[str, Any] = None
    ) -> List[ExtractedEntity]:
        """Extract entities from hierarchical chunk"""
        entities = []
        
        # Extract using pattern matching
        pattern_entities = self._extract_entities_by_patterns(
            chunk.content, chunk.navigation_context
        )
        entities.extend(pattern_entities)
        
        # Extract decision entities if this is a decision chunk
        if chunk.is_decision_chunk():
            decision_entities = self._extract_decision_entities(
                chunk.content, chunk.navigation_context
            )
            entities.extend(decision_entities)
        
        # Update entities with chunk context
        for entity in entities:
            entity.source_chunk_id = chunk.chunk_id
            entity.navigation_context = chunk.navigation_context
        
        return entities

    def _extract_entities_by_patterns(
        self,
        content: str,
        nav_context: Optional[NavigationContext] = None
    ) -> List[ExtractedEntity]:
        """Extract entities using regex patterns"""
        entities = []
        
        for entity_type, patterns in self.entity_patterns.items():
            for pattern in patterns:
                matches = re.finditer(pattern, content, re.IGNORECASE | re.MULTILINE)
                
                for match in matches:
                    entity_text = match.group(0)
                    start_pos = match.start()
                    end_pos = match.end()
                    
                    # Calculate confidence based on pattern specificity
                    confidence = self._calculate_pattern_confidence(match, entity_type)
                    
                    # Extract normalized value if applicable
                    normalized_value = self._normalize_entity_value(entity_text, entity_type)
                    
                    entity = ExtractedEntity(
                        entity_id=f"entity_{entity_type.value.lower()}_{uuid.uuid4().hex[:8]}",
                        entity_text=entity_text,
                        entity_type=entity_type,
                        confidence_score=confidence,
                        navigation_context=nav_context,
                        start_position=start_pos,
                        end_position=end_pos,
                        normalized_value=normalized_value,
                        extraction_method="pattern"
                    )
                    
                    entities.append(entity)
        
        return entities

    def _extract_entities_by_vocabulary(
        self,
        content: str,
        nav_context: Optional[NavigationContext] = None
    ) -> List[ExtractedEntity]:
        """Extract entities using domain vocabulary"""
        entities = []
        content_lower = content.lower()
        
        for term, entity_type in self.domain_vocabulary.items():
            if term.lower() in content_lower:
                # Find all occurrences
                for match in re.finditer(re.escape(term.lower()), content_lower):
                    start_pos = match.start()
                    end_pos = match.end()
                    entity_text = content[start_pos:end_pos]
                    
                    entity = ExtractedEntity(
                        entity_id=f"entity_{entity_type.value.lower()}_{uuid.uuid4().hex[:8]}",
                        entity_text=entity_text,
                        entity_type=entity_type,
                        confidence_score=0.75,  # Base confidence for vocabulary matches
                        navigation_context=nav_context,
                        start_position=start_pos,
                        end_position=end_pos,
                        extraction_method="vocabulary"
                    )
                    
                    entities.append(entity)
        
        return entities

    def _extract_decision_entities(
        self,
        content: str,
        nav_context: Optional[NavigationContext] = None
    ) -> List[ExtractedEntity]:
        """Extract decision-specific entities"""
        entities = []
        
        # Extract decision criteria
        criteria_patterns = [
            r'(?i)(if|when)\s+([^,]+),?\s+(then|must)',
            r'(?i)(eligibility|criteria|requirements?)\s*:?\s*([^.]+)',
            r'(?i)(approve|decline|refer)\s+(if|when)\s+([^.]+)'
        ]
        
        for pattern in criteria_patterns:
            matches = re.finditer(pattern, content, re.IGNORECASE | re.MULTILINE)
            
            for match in matches:
                entity_text = match.group(0)
                
                entity = ExtractedEntity(
                    entity_id=f"entity_decision_{uuid.uuid4().hex[:8]}",
                    entity_text=entity_text,
                    entity_type=EntityType.DECISION_CRITERIA,
                    confidence_score=0.8,
                    navigation_context=nav_context,
                    start_position=match.start(),
                    end_position=match.end(),
                    extraction_method="decision_pattern",
                    decision_impact="direct"
                )
                
                entities.append(entity)
        
        return entities

    def _enhance_entities_with_llm(
        self,
        entities: List[ExtractedEntity],
        navigation_nodes: List[EnhancedNavigationNode],
        hierarchical_chunks: List[HierarchicalChunk]
    ) -> List[ExtractedEntity]:
        """Enhance entities using LLM analysis"""
        # For now, return entities as-is. In full implementation, would use LLM
        # to identify additional entities, improve confidence scores, and
        # extract semantic relationships
        
        # Basic enhancement: improve confidence scores based on context
        for entity in entities:
            if entity.navigation_context:
                # Boost confidence for entities in decision contexts
                if entity.navigation_context.decision_context:
                    entity.confidence_score = min(1.0, entity.confidence_score + 0.1)
                
                # Boost confidence for entities in specific navigation paths
                nav_path = " ".join(entity.navigation_context.navigation_path).lower()
                if any(keyword in nav_path for keyword in ["eligibility", "requirements", "criteria"]):
                    entity.confidence_score = min(1.0, entity.confidence_score + 0.05)
        
        return entities

    def _deduplicate_entities(self, entities: List[ExtractedEntity]) -> List[ExtractedEntity]:
        """Remove duplicate entities based on text and type"""
        seen = set()
        deduplicated = []
        
        for entity in entities:
            # Create key based on normalized text and type
            normalized_text = entity.entity_text.lower().strip()
            key = (normalized_text, entity.entity_type)
            
            if key not in seen:
                seen.add(key)
                deduplicated.append(entity)
            else:
                # Keep entity with higher confidence
                existing_idx = next(
                    i for i, e in enumerate(deduplicated)
                    if e.entity_text.lower().strip() == normalized_text and e.entity_type == entity.entity_type
                )
                if entity.confidence_score > deduplicated[existing_idx].confidence_score:
                    deduplicated[existing_idx] = entity
        
        return deduplicated

    def _build_entity_relationships(self, entities: List[ExtractedEntity]) -> List[Dict[str, Any]]:
        """Build relationships between extracted entities"""
        relationships = []
        
        # Group entities by navigation context
        entities_by_context = {}
        for entity in entities:
            if entity.navigation_context:
                nav_path = " > ".join(entity.navigation_context.navigation_path)
                if nav_path not in entities_by_context:
                    entities_by_context[nav_path] = []
                entities_by_context[nav_path].append(entity)
        
        # Create relationships within same navigation context
        for nav_path, context_entities in entities_by_context.items():
            for i, entity1 in enumerate(context_entities):
                for entity2 in context_entities[i+1:]:
                    # Create relationship based on entity types
                    relationship = self._determine_entity_relationship(entity1, entity2)
                    if relationship:
                        relationships.append(relationship)
        
        return relationships

    def _determine_entity_relationship(
        self, entity1: ExtractedEntity, entity2: ExtractedEntity
    ) -> Optional[Dict[str, Any]]:
        """Determine relationship between two entities"""
        # Define relationship rules
        relationship_rules = {
            (EntityType.DECISION_CRITERIA, EntityType.NUMERIC_THRESHOLD): "USES_THRESHOLD",
            (EntityType.DECISION_CRITERIA, EntityType.DOLLAR_AMOUNT): "EVALUATES_AMOUNT",
            (EntityType.LOAN_PROGRAM, EntityType.REQUIREMENT): "HAS_REQUIREMENT",
            (EntityType.BORROWER_TYPE, EntityType.DOCUMENT_TYPE): "REQUIRES_DOCUMENT",
            (EntityType.PROPERTY_TYPE, EntityType.PROPERTY_STANDARD): "MUST_MEET_STANDARD"
        }
        
        key = (entity1.entity_type, entity2.entity_type)
        reverse_key = (entity2.entity_type, entity1.entity_type)
        
        if key in relationship_rules:
            return {
                "from_entity_id": entity1.entity_id,
                "to_entity_id": entity2.entity_id,
                "relationship_type": relationship_rules[key],
                "confidence": min(entity1.confidence_score, entity2.confidence_score)
            }
        elif reverse_key in relationship_rules:
            return {
                "from_entity_id": entity2.entity_id,
                "to_entity_id": entity1.entity_id,
                "relationship_type": relationship_rules[reverse_key],
                "confidence": min(entity1.confidence_score, entity2.confidence_score)
            }
        
        return None

    def _validate_entities(self, entities: List[ExtractedEntity]) -> List[ExtractedEntity]:
        """Validate extracted entities against validation rules"""
        validated_entities = []
        
        for entity in entities:
            validation_rules = self.validation_rules.get(entity.entity_type, {})
            
            # Check minimum confidence
            min_confidence = validation_rules.get("min_confidence", 0.5)
            if entity.confidence_score < min_confidence:
                entity.validation_status = "low_confidence"
                continue
            
            # Validate numeric values
            if validation_rules.get("require_numeric_value", False):
                if not self._validate_numeric_entity(entity, validation_rules):
                    entity.validation_status = "invalid_numeric"
                    continue
            
            # Check vocabulary match requirement
            if validation_rules.get("require_vocabulary_match", False):
                if entity.entity_text.lower() not in [k.lower() for k in self.domain_vocabulary.keys()]:
                    entity.validation_status = "no_vocabulary_match"
                    continue
            
            entity.validation_status = "valid"
            entity.quality_score = entity.confidence_score
            validated_entities.append(entity)
        
        return validated_entities

    def _validate_numeric_entity(self, entity: ExtractedEntity, rules: Dict[str, Any]) -> bool:
        """Validate numeric entity values"""
        if not entity.normalized_value:
            return False
        
        try:
            numeric_value = float(entity.normalized_value)
            entity.financial_value = numeric_value
            
            # Check valid ranges
            valid_ranges = rules.get("valid_ranges", {})
            for range_type, (min_val, max_val) in valid_ranges.items():
                if range_type.lower() in entity.entity_text.lower():
                    if not (min_val <= numeric_value <= max_val):
                        return False
            
            # Check general min value
            min_value = rules.get("min_value")
            if min_value is not None and numeric_value < min_value:
                return False
            
            return True
            
        except (ValueError, TypeError):
            return False

    def _calculate_pattern_confidence(self, match: re.Match, entity_type: EntityType) -> float:
        """Calculate confidence score for pattern match"""
        base_confidence = 0.7
        
        # Boost confidence for specific patterns
        if entity_type == EntityType.NUMERIC_THRESHOLD:
            if "score" in match.group(0).lower():
                base_confidence += 0.15
            if any(op in match.group(0) for op in [">=", "<=", ">", "<"]):
                base_confidence += 0.1
        
        elif entity_type == EntityType.DOLLAR_AMOUNT:
            if "$" in match.group(0):
                base_confidence += 0.1
            if "," in match.group(0):  # Formatted numbers
                base_confidence += 0.05
        
        return min(1.0, base_confidence)

    def _normalize_entity_value(self, entity_text: str, entity_type: EntityType) -> Optional[str]:
        """Normalize entity value for consistent representation"""
        if entity_type in [EntityType.NUMERIC_THRESHOLD, EntityType.DOLLAR_AMOUNT, EntityType.PERCENTAGE]:
            # Extract numeric value
            numbers = re.findall(r'\d+(?:\.\d+)?', entity_text.replace(',', ''))
            if numbers:
                return numbers[0]
        
        elif entity_type in [EntityType.LOAN_PROGRAM, EntityType.BORROWER_TYPE, EntityType.PROPERTY_TYPE]:
            # Normalize text entities
            return entity_text.lower().strip()
        
        return None

    def _calculate_extraction_metrics(
        self,
        entities: List[ExtractedEntity],
        navigation_nodes: List[EnhancedNavigationNode],
        hierarchical_chunks: List[HierarchicalChunk]
    ) -> EntityExtractionMetrics:
        """Calculate comprehensive extraction metrics"""
        metrics = EntityExtractionMetrics()
        
        metrics.total_entities = len(entities)
        
        # Count entities by type
        for entity in entities:
            if entity.entity_type not in metrics.entities_by_type:
                metrics.entities_by_type[entity.entity_type] = 0
            metrics.entities_by_type[entity.entity_type] += 1
        
        # Calculate average confidence
        if entities:
            metrics.avg_confidence_score = sum(e.confidence_score for e in entities) / len(entities)
        
        # Calculate navigation coverage
        nodes_with_entities = set()
        for entity in entities:
            if entity.source_chunk_id:
                nodes_with_entities.add(entity.source_chunk_id)
        
        total_nodes = len(navigation_nodes) + len(hierarchical_chunks)
        if total_nodes > 0:
            metrics.navigation_coverage = len(nodes_with_entities) / total_nodes
        
        # Calculate validation success rate
        valid_entities = [e for e in entities if e.validation_status == "valid"]
        if entities:
            metrics.validation_success_rate = len(valid_entities) / len(entities)
        
        # Simple relationship accuracy (would be more sophisticated in full implementation)
        metrics.relationship_accuracy = 0.85  # Placeholder
        
        # Processing efficiency (entities per second)
        metrics.processing_efficiency = 50.0  # Placeholder
        
        return metrics