# Task 14: Guidelines Entity Extractor Tests
# Comprehensive tests for GuidelineEntityExtractor class

import unittest
from unittest.mock import Mock, MagicMock, patch
from datetime import datetime
from typing import List, Dict, Any

# Import the classes being tested
from src.guideline_entity_extractor import (
    GuidelineEntityExtractor,
    ExtractedEntity,
    EntityExtractionResult,
    EntityExtractionMetrics,
    EntityType
)

# Import dependencies
from src.entities.navigation_models import (
    EnhancedNavigationNode,
    HierarchicalChunk,
    NavigationContext,
    QualityRating
)
from src.navigation_extractor import NavigationLevel
from src.semantic_chunker import ChunkType


class TestGuidelineEntityExtractor(unittest.TestCase):
    """Test suite for GuidelineEntityExtractor class"""
    
    def setUp(self):
        """Set up test fixtures"""
        # Mock LLM
        self.mock_llm = Mock()
        
        # Initialize GuidelineEntityExtractor with mocked LLM
        with patch('src.guideline_entity_extractor.get_llm', return_value=self.mock_llm):
            self.extractor = GuidelineEntityExtractor()
        
        # Sample test data
        self.sample_navigation_nodes = self._create_sample_navigation_nodes()
        self.sample_hierarchical_chunks = self._create_sample_hierarchical_chunks()

    def _create_sample_navigation_nodes(self) -> List[EnhancedNavigationNode]:
        """Create sample navigation nodes with entity-rich content"""
        return [
            EnhancedNavigationNode(
                node_id="nav_entity_001",
                level=NavigationLevel.SECTION,
                title="Credit Score Requirements",
                content="""
                Credit Score Requirements for Non-QM Loans:
                
                Minimum credit score: 620
                Preferred FICO score >= 680
                Maximum DTI ratio: 45%
                Minimum income: $75,000 annually
                Employment history: 2 years minimum
                
                For self-employed borrowers:
                - 2 years tax returns required
                - Profit and loss statements
                - Bank statements (24 months)
                
                Property types accepted:
                - Single family residence
                - Condominium (warrantable)
                - Townhouse
                
                Occupancy types:
                - Primary residence
                - Second home
                - Investment property
                """,
                parent_id="nav_eligibility",
                confidence_score=0.95,
                quality_rating=QualityRating.EXCELLENT,
                navigation_context=NavigationContext(
                    navigation_path=["NAA Guidelines", "Borrower Eligibility", "Credit Requirements"],
                    hierarchy_level=2,
                    decision_context="credit_evaluation"
                )
            ),
            EnhancedNavigationNode(
                node_id="nav_entity_002",
                level=NavigationLevel.SECTION,
                title="Loan Amount Limits",
                content="""
                Loan Amount Guidelines:
                
                Conventional conforming limit: $766,550
                Jumbo loan minimum: $766,551
                Maximum loan amount: $3,000,000
                
                LTV requirements:
                - Primary residence: 95% maximum LTV
                - Second home: 90% maximum LTV  
                - Investment property: 80% maximum LTV
                
                Cash-out refinance limits:
                - Maximum 80% LTV for all property types
                - Minimum $50,000 loan amount
                """,
                parent_id="nav_loan_params",
                confidence_score=0.92,
                quality_rating=QualityRating.EXCELLENT,
                navigation_context=NavigationContext(
                    navigation_path=["NAA Guidelines", "Loan Parameters", "Amount Limits"],
                    hierarchy_level=2
                )
            )
        ]

    def _create_sample_hierarchical_chunks(self) -> List[HierarchicalChunk]:
        """Create sample hierarchical chunks with entities"""
        return [
            HierarchicalChunk(
                chunk_id="chunk_entity_001",
                chunk_type=ChunkType.DECISION,
                content="""
                Decision Tree: Loan Approval Process
                
                IF credit score >= 620 AND employment history >= 2 years THEN
                    IF DTI ratio <= 45% THEN APPROVE
                    ELSE IF DTI ratio <= 50% AND assets >= 6 months THEN REFER
                    ELSE DECLINE
                ELSE
                    DECLINE for insufficient credit or employment
                """,
                content_summary="Loan approval decision logic with credit and employment criteria",
                navigation_context=NavigationContext(
                    navigation_path=["NAA Guidelines", "Underwriting", "Approval Process"],
                    hierarchy_level=3,
                    decision_context="approval_determination"
                ),
                decision_criteria=["credit_score", "employment_history", "dti_ratio"],
                quality_score=0.92,
                token_count=85
            ),
            HierarchicalChunk(
                chunk_id="chunk_entity_002",
                chunk_type=ChunkType.CONTENT,
                content="""
                Income Documentation Requirements:
                
                W-2 Employees:
                - Most recent 2 years W-2 forms
                - 30 days of pay stubs
                - Verification of employment (VOE)
                
                Self-Employed Borrowers:
                - 2 years personal tax returns
                - 2 years business tax returns (if applicable)
                - Profit and loss statement (YTD)
                - CPA letter confirming business existence
                
                Minimum qualifying income: $50,000 per year
                Maximum debt-to-income ratio: 50% for qualified borrowers
                """,
                content_summary="Documentation requirements for different borrower types",
                navigation_context=NavigationContext(
                    navigation_path=["NAA Guidelines", "Documentation", "Income Verification"],
                    hierarchy_level=3
                ),
                quality_score=0.88,
                token_count=120
            )
        ]

    def test_guideline_entity_extractor_initialization(self):
        """Test GuidelineEntityExtractor initialization"""
        self.assertIsNotNone(self.extractor)
        self.assertIsNotNone(self.extractor.entity_patterns)
        self.assertIsNotNone(self.extractor.domain_vocabulary)
        self.assertIsNotNone(self.extractor.validation_rules)
        
        # Test entity patterns
        self.assertIn(EntityType.NUMERIC_THRESHOLD, self.extractor.entity_patterns)
        self.assertIn(EntityType.DOLLAR_AMOUNT, self.extractor.entity_patterns)
        self.assertIn(EntityType.LOAN_PROGRAM, self.extractor.entity_patterns)
        
        # Test domain vocabulary
        self.assertIn("non-qm", self.extractor.domain_vocabulary)
        self.assertIn("ltv", self.extractor.domain_vocabulary)
        self.assertIn("single family", self.extractor.domain_vocabulary)

    def test_initialize_entity_patterns(self):
        """Test entity pattern initialization"""
        patterns = self.extractor._initialize_entity_patterns()
        
        # Check all entity types have patterns
        expected_types = [
            EntityType.NUMERIC_THRESHOLD,
            EntityType.DOLLAR_AMOUNT,
            EntityType.PERCENTAGE,
            EntityType.LOAN_PROGRAM,
            EntityType.BORROWER_TYPE,
            EntityType.PROPERTY_TYPE,
            EntityType.DECISION_CRITERIA
        ]
        
        for entity_type in expected_types:
            self.assertIn(entity_type, patterns)
            self.assertGreater(len(patterns[entity_type]), 0)
        
        # Test specific patterns
        numeric_patterns = patterns[EntityType.NUMERIC_THRESHOLD]
        self.assertTrue(any("credit score" in pattern.lower() for pattern in numeric_patterns))
        self.assertTrue(any("ltv" in pattern.lower() for pattern in numeric_patterns))

    def test_initialize_domain_vocabulary(self):
        """Test domain vocabulary initialization"""
        vocab = self.extractor._initialize_domain_vocabulary()
        
        # Test loan program terms
        self.assertEqual(vocab["non-qm"], EntityType.LOAN_PROGRAM)
        self.assertEqual(vocab["conventional"], EntityType.LOAN_PROGRAM)
        
        # Test financial terms
        self.assertEqual(vocab["ltv"], EntityType.FINANCIAL_RATIO)
        self.assertEqual(vocab["dti"], EntityType.FINANCIAL_RATIO)
        
        # Test property terms
        self.assertEqual(vocab["single family"], EntityType.PROPERTY_TYPE)
        self.assertEqual(vocab["condo"], EntityType.PROPERTY_TYPE)

    def test_extract_node_entities(self):
        """Test entity extraction from navigation nodes"""
        node = self.sample_navigation_nodes[0]  # Credit score requirements node
        
        entities = self.extractor.extract_node_entities(node)
        
        # Should extract multiple entities
        self.assertGreater(len(entities), 0)
        
        # Check for specific entity types
        entity_types = [e.entity_type for e in entities]
        self.assertIn(EntityType.NUMERIC_THRESHOLD, entity_types)
        
        # Check entities have navigation context
        for entity in entities:
            self.assertIsNotNone(entity.navigation_context)
            self.assertEqual(entity.source_chunk_id, node.enhanced_node_id)

    def test_extract_entities_by_patterns_numeric_threshold(self):
        """Test extraction of numeric threshold entities"""
        content = "Minimum credit score: 620, Maximum DTI ratio: 45%, LTV <= 80%"
        
        entities = self.extractor._extract_entities_by_patterns(content)
        
        # Should find numeric thresholds
        numeric_entities = [e for e in entities if e.entity_type == EntityType.NUMERIC_THRESHOLD]
        self.assertGreater(len(numeric_entities), 0)
        
        # Check specific extractions
        entity_texts = [e.entity_text for e in numeric_entities]
        self.assertTrue(any("620" in text for text in entity_texts))
        self.assertTrue(any("45%" in text for text in entity_texts))

    def test_extract_entities_by_patterns_dollar_amount(self):
        """Test extraction of dollar amount entities"""
        content = "Maximum loan amount: $3,000,000. Minimum income $75,000 annually."
        
        entities = self.extractor._extract_entities_by_patterns(content)
        
        # Should find dollar amounts
        dollar_entities = [e for e in entities if e.entity_type == EntityType.DOLLAR_AMOUNT]
        self.assertGreater(len(dollar_entities), 0)
        
        # Check specific extractions
        entity_texts = [e.entity_text for e in dollar_entities]
        self.assertTrue(any("3,000,000" in text for text in entity_texts))
        self.assertTrue(any("75,000" in text for text in entity_texts))

    def test_extract_entities_by_vocabulary(self):
        """Test extraction using domain vocabulary"""
        content = "Non-QM loans for single family residence with conventional terms"
        
        entities = self.extractor._extract_entities_by_vocabulary(content)
        
        # Should find vocabulary matches
        self.assertGreater(len(entities), 0)
        
        # Check specific entity types
        entity_types = [e.entity_type for e in entities]
        self.assertIn(EntityType.LOAN_PROGRAM, entity_types)
        self.assertIn(EntityType.PROPERTY_TYPE, entity_types)

    def test_extract_decision_entities(self):
        """Test extraction of decision-specific entities"""
        content = """
        Eligibility criteria: If credit score >= 620 and employment >= 2 years, then approve.
        Decline if DTI > 50%. Refer when assets >= 6 months reserves.
        """
        
        entities = self.extractor._extract_decision_entities(content)
        
        # Should find decision criteria
        decision_entities = [e for e in entities if e.entity_type == EntityType.DECISION_CRITERIA]
        self.assertGreater(len(decision_entities), 0)
        
        # Check decision impact is set
        for entity in decision_entities:
            self.assertIsNotNone(entity.decision_impact)

    def test_deduplicate_entities(self):
        """Test entity deduplication"""
        # Create duplicate entities
        entity1 = ExtractedEntity(
            entity_id="test1",
            entity_text="Credit Score >= 620",
            entity_type=EntityType.NUMERIC_THRESHOLD,
            confidence_score=0.8
        )
        
        entity2 = ExtractedEntity(
            entity_id="test2",
            entity_text="credit score >= 620",  # Same text, different case
            entity_type=EntityType.NUMERIC_THRESHOLD,
            confidence_score=0.9  # Higher confidence
        )
        
        entity3 = ExtractedEntity(
            entity_id="test3",
            entity_text="DTI <= 45%",
            entity_type=EntityType.NUMERIC_THRESHOLD,
            confidence_score=0.7
        )
        
        entities = [entity1, entity2, entity3]
        deduplicated = self.extractor._deduplicate_entities(entities)
        
        # Should have 2 unique entities
        self.assertEqual(len(deduplicated), 2)
        
        # Should keep the higher confidence entity
        kept_entity = next(e for e in deduplicated if "credit score" in e.entity_text.lower())
        self.assertEqual(kept_entity.confidence_score, 0.9)

    def test_build_entity_relationships(self):
        """Test building relationships between entities"""
        # Create related entities
        decision_entity = ExtractedEntity(
            entity_id="decision_1",
            entity_text="Approve if credit score >= 620",
            entity_type=EntityType.DECISION_CRITERIA,
            confidence_score=0.9,
            navigation_context=NavigationContext(
                navigation_path=["Guidelines", "Approval"]
            )
        )
        
        threshold_entity = ExtractedEntity(
            entity_id="threshold_1",
            entity_text="credit score >= 620",
            entity_type=EntityType.NUMERIC_THRESHOLD,
            confidence_score=0.8,
            navigation_context=NavigationContext(
                navigation_path=["Guidelines", "Approval"]
            )
        )
        
        entities = [decision_entity, threshold_entity]
        relationships = self.extractor._build_entity_relationships(entities)
        
        # Should create relationship
        self.assertGreater(len(relationships), 0)
        
        # Check relationship structure
        relationship = relationships[0]
        self.assertIn("from_entity_id", relationship)
        self.assertIn("to_entity_id", relationship)
        self.assertIn("relationship_type", relationship)

    def test_validate_entities(self):
        """Test entity validation"""
        # Create entities with different validation scenarios
        valid_entity = ExtractedEntity(
            entity_id="valid_1",
            entity_text="credit score >= 720",
            entity_type=EntityType.NUMERIC_THRESHOLD,
            confidence_score=0.9,
            normalized_value="720"
        )
        
        low_confidence_entity = ExtractedEntity(
            entity_id="low_conf_1",
            entity_text="some requirement",
            entity_type=EntityType.NUMERIC_THRESHOLD,
            confidence_score=0.3  # Below minimum
        )
        
        entities = [valid_entity, low_confidence_entity]
        validated = self.extractor._validate_entities(entities)
        
        # Should only keep valid entities
        self.assertEqual(len(validated), 1)
        self.assertEqual(validated[0].validation_status, "valid")

    def test_validate_numeric_entity(self):
        """Test numeric entity validation"""
        # Valid numeric entity
        valid_entity = ExtractedEntity(
            entity_id="valid_numeric",
            entity_text="credit score >= 720",
            entity_type=EntityType.NUMERIC_THRESHOLD,
            confidence_score=0.8,
            normalized_value="720"
        )
        
        rules = {
            "require_numeric_value": True,
            "valid_ranges": {
                "credit_score": (300, 850)
            }
        }
        
        is_valid = self.extractor._validate_numeric_entity(valid_entity, rules)
        self.assertTrue(is_valid)
        self.assertEqual(valid_entity.financial_value, 720.0)
        
        # Invalid range
        invalid_entity = ExtractedEntity(
            entity_id="invalid_numeric",
            entity_text="credit score >= 900",  # Above valid range
            entity_type=EntityType.NUMERIC_THRESHOLD,
            confidence_score=0.8,
            normalized_value="900"
        )
        
        is_valid = self.extractor._validate_numeric_entity(invalid_entity, rules)
        self.assertFalse(is_valid)

    def test_normalize_entity_value(self):
        """Test entity value normalization"""
        # Test numeric threshold normalization
        result = self.extractor._normalize_entity_value(
            "credit score >= 620", EntityType.NUMERIC_THRESHOLD
        )
        self.assertEqual(result, "620")
        
        # Test dollar amount normalization
        result = self.extractor._normalize_entity_value(
            "$3,000,000", EntityType.DOLLAR_AMOUNT
        )
        self.assertEqual(result, "3000000")
        
        # Test text entity normalization
        result = self.extractor._normalize_entity_value(
            "Non-QM Loan", EntityType.LOAN_PROGRAM
        )
        self.assertEqual(result, "non-qm loan")

    def test_calculate_pattern_confidence(self):
        """Test pattern confidence calculation"""
        import re
        
        # High confidence pattern
        match = re.search(r'credit score >= (\d+)', "credit score >= 620")
        confidence = self.extractor._calculate_pattern_confidence(match, EntityType.NUMERIC_THRESHOLD)
        self.assertGreater(confidence, 0.8)
        
        # Lower confidence pattern
        match = re.search(r'(\d+)', "some number 500")
        confidence = self.extractor._calculate_pattern_confidence(match, EntityType.NUMERIC_THRESHOLD)
        self.assertLess(confidence, 0.9)

    def test_calculate_extraction_metrics(self):
        """Test extraction metrics calculation"""
        entities = [
            ExtractedEntity(
                entity_id="e1",
                entity_text="credit score >= 620",
                entity_type=EntityType.NUMERIC_THRESHOLD,
                confidence_score=0.9,
                validation_status="valid"
            ),
            ExtractedEntity(
                entity_id="e2",
                entity_text="non-qm",
                entity_type=EntityType.LOAN_PROGRAM,
                confidence_score=0.8,
                validation_status="valid"
            ),
            ExtractedEntity(
                entity_id="e3",
                entity_text="some requirement",
                entity_type=EntityType.REQUIREMENT,
                confidence_score=0.5,
                validation_status="low_confidence"
            )
        ]
        
        metrics = self.extractor._calculate_extraction_metrics(
            entities, self.sample_navigation_nodes, self.sample_hierarchical_chunks
        )
        
        self.assertEqual(metrics.total_entities, 3)
        self.assertGreater(metrics.avg_confidence_score, 0)
        self.assertGreater(metrics.validation_success_rate, 0)
        self.assertIn(EntityType.NUMERIC_THRESHOLD, metrics.entities_by_type)

    @patch.object(GuidelineEntityExtractor, 'extract_node_entities')
    @patch.object(GuidelineEntityExtractor, '_extract_chunk_entities')
    @patch.object(GuidelineEntityExtractor, '_deduplicate_entities')
    @patch.object(GuidelineEntityExtractor, '_enhance_entities_with_llm')
    @patch.object(GuidelineEntityExtractor, '_build_entity_relationships')
    @patch.object(GuidelineEntityExtractor, '_validate_entities')
    @patch.object(GuidelineEntityExtractor, '_calculate_extraction_metrics')
    def test_extract_entities_with_context_success(
        self,
        mock_calculate_metrics,
        mock_validate,
        mock_build_relationships,
        mock_enhance_llm,
        mock_deduplicate,
        mock_extract_chunks,
        mock_extract_nodes
    ):
        """Test successful entity extraction with context"""
        # Setup mocks
        sample_entity = ExtractedEntity(
            entity_id="test_entity",
            entity_text="credit score >= 620",
            entity_type=EntityType.NUMERIC_THRESHOLD,
            confidence_score=0.9
        )
        
        mock_extract_nodes.return_value = [sample_entity]
        mock_extract_chunks.return_value = [sample_entity]
        mock_deduplicate.return_value = [sample_entity]
        mock_enhance_llm.return_value = [sample_entity]
        mock_validate.return_value = [sample_entity]
        mock_build_relationships.return_value = []
        mock_calculate_metrics.return_value = EntityExtractionMetrics(
            total_entities=1,
            avg_confidence_score=0.9
        )
        
        # Execute test
        result = self.extractor.extract_entities_with_context(
            self.sample_navigation_nodes,
            self.sample_hierarchical_chunks
        )
        
        # Verify result
        self.assertTrue(result.success)
        self.assertEqual(len(result.entities), 1)
        self.assertEqual(result.entities[0].entity_id, "test_entity")

    def test_extract_entities_with_context_extraction_failure(self):
        """Test extraction with node processing failures"""
        # Mock node extraction to raise exception
        with patch.object(self.extractor, 'extract_node_entities', side_effect=Exception("Extraction failed")):
            result = self.extractor.extract_entities_with_context(
                self.sample_navigation_nodes,
                self.sample_hierarchical_chunks
            )
        
        self.assertGreater(len(result.validation_errors), 0)
        self.assertIn("Extraction failed", str(result.validation_errors))

    def test_entity_type_enum(self):
        """Test EntityType enum completeness"""
        # Test all expected entity types are present
        expected_types = [
            "LOAN_PROGRAM", "BORROWER_TYPE", "NUMERIC_THRESHOLD", "DOLLAR_AMOUNT",
            "PROPERTY_TYPE", "DECISION_CRITERIA", "MATRIX_VALUE", "REQUIREMENT"
        ]
        
        enum_values = [e.value for e in EntityType]
        for expected_type in expected_types:
            self.assertIn(expected_type, enum_values)


class TestExtractedEntity(unittest.TestCase):
    """Test suite for ExtractedEntity class"""
    
    def test_extracted_entity_initialization(self):
        """Test ExtractedEntity initialization"""
        entity = ExtractedEntity(
            entity_id="test_entity",
            entity_text="credit score >= 620",
            entity_type=EntityType.NUMERIC_THRESHOLD,
            confidence_score=0.9
        )
        
        self.assertEqual(entity.entity_id, "test_entity")
        self.assertEqual(entity.entity_text, "credit score >= 620")
        self.assertEqual(entity.entity_type, EntityType.NUMERIC_THRESHOLD)
        self.assertEqual(entity.confidence_score, 0.9)
        self.assertEqual(entity.validation_status, "pending")

    def test_extracted_entity_with_context(self):
        """Test ExtractedEntity with navigation context"""
        nav_context = NavigationContext(
            navigation_path=["Guidelines", "Credit Requirements"],
            hierarchy_level=2
        )
        
        entity = ExtractedEntity(
            entity_id="test_entity",
            entity_text="FICO >= 620",
            entity_type=EntityType.NUMERIC_THRESHOLD,
            confidence_score=0.85,
            navigation_context=nav_context,
            normalized_value="620",
            financial_value=620.0
        )
        
        self.assertEqual(entity.navigation_context, nav_context)
        self.assertEqual(entity.normalized_value, "620")
        self.assertEqual(entity.financial_value, 620.0)


class TestEntityExtractionResult(unittest.TestCase):
    """Test suite for EntityExtractionResult class"""
    
    def test_extraction_result_initialization(self):
        """Test EntityExtractionResult initialization"""
        result = EntityExtractionResult(success=True)
        
        self.assertTrue(result.success)
        self.assertEqual(len(result.entities), 0)
        self.assertEqual(len(result.entity_relationships), 0)
        self.assertEqual(len(result.extraction_metrics), 0)
        self.assertEqual(len(result.validation_errors), 0)

    def test_extraction_result_with_data(self):
        """Test EntityExtractionResult with sample data"""
        entity = ExtractedEntity(
            entity_id="test_entity",
            entity_text="credit score >= 620",
            entity_type=EntityType.NUMERIC_THRESHOLD,
            confidence_score=0.9
        )
        
        relationship = {
            "from_entity_id": "entity1",
            "to_entity_id": "entity2",
            "relationship_type": "USES_THRESHOLD"
        }
        
        result = EntityExtractionResult(
            success=True,
            entities=[entity],
            entity_relationships=[relationship],
            processing_time_ms=1500
        )
        
        self.assertTrue(result.success)
        self.assertEqual(len(result.entities), 1)
        self.assertEqual(len(result.entity_relationships), 1)
        self.assertEqual(result.processing_time_ms, 1500)


class TestEntityExtractionMetrics(unittest.TestCase):
    """Test suite for EntityExtractionMetrics class"""
    
    def test_metrics_initialization(self):
        """Test EntityExtractionMetrics initialization with defaults"""
        metrics = EntityExtractionMetrics()
        
        self.assertEqual(metrics.total_entities, 0)
        self.assertEqual(len(metrics.entities_by_type), 0)
        self.assertEqual(metrics.avg_confidence_score, 0.0)
        self.assertEqual(metrics.navigation_coverage, 0.0)
        self.assertEqual(metrics.validation_success_rate, 0.0)

    def test_metrics_with_values(self):
        """Test EntityExtractionMetrics with specific values"""
        metrics = EntityExtractionMetrics(
            total_entities=15,
            avg_confidence_score=0.85,
            navigation_coverage=0.92,
            validation_success_rate=0.88
        )
        
        metrics.entities_by_type[EntityType.NUMERIC_THRESHOLD] = 5
        metrics.entities_by_type[EntityType.LOAN_PROGRAM] = 3
        
        self.assertEqual(metrics.total_entities, 15)
        self.assertEqual(metrics.avg_confidence_score, 0.85)
        self.assertEqual(metrics.entities_by_type[EntityType.NUMERIC_THRESHOLD], 5)


if __name__ == '__main__':
    unittest.main()