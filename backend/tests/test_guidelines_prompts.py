# Task 16: Enhanced Processing Prompts Tests
# Comprehensive test suite for mortgage-specific prompt engine

import unittest
from unittest.mock import Mock, patch
import json
from datetime import datetime

from src.prompts.guidelines_prompts import (
    GuidelinesPromptEngine,
    PromptTemplate,
    PromptContext,
    PromptMetrics,
    PromptType,
    MortgageCategory,
    create_navigation_prompt,
    create_decision_prompt,
    create_entity_prompt,
    create_validation_prompt
)
from src.entities.navigation_models import NavigationContext


class TestPromptTemplate(unittest.TestCase):
    """Test PromptTemplate functionality"""
    
    def test_prompt_template_creation(self):
        """Test basic PromptTemplate creation"""
        template = PromptTemplate(
            template_id="test-template",
            prompt_type=PromptType.NAVIGATION,
            mortgage_category=MortgageCategory.NQM,
            base_template="Extract navigation from {content}",
            context_variables=["content"],
            domain_specific_instructions={"focus": "Non-QM patterns"},
            examples=["Example 1", "Example 2"],
            validation_criteria=["Must be complete"]
        )
        
        self.assertEqual(template.template_id, "test-template")
        self.assertEqual(template.prompt_type, PromptType.NAVIGATION)
        self.assertEqual(template.mortgage_category, MortgageCategory.NQM)
        self.assertIn("Extract navigation from {content}", template.base_template)
        self.assertEqual(template.context_variables, ["content"])
        self.assertEqual(template.domain_specific_instructions["focus"], "Non-QM patterns")
        self.assertEqual(len(template.examples), 2)
        self.assertEqual(len(template.validation_criteria), 1)
    
    def test_generate_prompt_basic(self):
        """Test basic prompt generation"""
        template = PromptTemplate(
            template_id="test-template",
            prompt_type=PromptType.NAVIGATION,
            mortgage_category=MortgageCategory.UNIVERSAL,
            base_template="Extract navigation from {content}",
            context_variables=["content"]
        )
        
        context = {"content": "test mortgage document"}
        prompt = template.generate_prompt(context)
        
        self.assertIn("Extract navigation from test mortgage document", prompt)
    
    def test_generate_prompt_with_instructions(self):
        """Test prompt generation with domain-specific instructions"""
        template = PromptTemplate(
            template_id="test-template",
            prompt_type=PromptType.ENTITY_EXTRACTION,
            mortgage_category=MortgageCategory.NQM,
            base_template="Extract entities from {content}",
            context_variables=["content"],
            domain_specific_instructions={
                "focus": "Non-QM specific entities",
                "validation": "Apply alternative documentation rules"
            }
        )
        
        context = {"content": "bank statement program"}
        prompt = template.generate_prompt(context)
        
        self.assertIn("Extract entities from bank statement program", prompt)
        self.assertIn("Domain-Specific Instructions:", prompt)
        self.assertIn("focus: Non-QM specific entities", prompt)
        self.assertIn("validation: Apply alternative documentation rules", prompt)
    
    def test_generate_prompt_with_examples(self):
        """Test prompt generation with examples"""
        template = PromptTemplate(
            template_id="test-template",
            prompt_type=PromptType.DECISION_TREE,
            mortgage_category=MortgageCategory.UNIVERSAL,
            base_template="Extract decisions from {content}",
            context_variables=["content"],
            examples=[
                "Credit score >= 620 leads to approval",
                "DTI > 0.43 leads to decline"
            ]
        )
        
        context = {"content": "loan approval criteria"}
        prompt = template.generate_prompt(context)
        
        self.assertIn("Examples:", prompt)
        self.assertIn("Credit score >= 620 leads to approval", prompt)
        self.assertIn("DTI > 0.43 leads to decline", prompt)
    
    def test_generate_prompt_with_validation(self):
        """Test prompt generation with validation criteria"""
        template = PromptTemplate(
            template_id="test-template",
            prompt_type=PromptType.VALIDATION,
            mortgage_category=MortgageCategory.UNIVERSAL,
            base_template="Validate {extracted_data}",
            context_variables=["extracted_data"],
            validation_criteria=[
                "All decision paths must be complete",
                "Entities must have confidence scores"
            ]
        )
        
        context = {"extracted_data": "sample data"}
        prompt = template.generate_prompt(context)
        
        self.assertIn("Validation Criteria:", prompt)
        self.assertIn("All decision paths must be complete", prompt)
        self.assertIn("Entities must have confidence scores", prompt)


class TestPromptContext(unittest.TestCase):
    """Test PromptContext data structure"""
    
    def test_prompt_context_creation(self):
        """Test basic PromptContext creation"""
        nav_context = Mock(spec=NavigationContext)
        nav_context.navigation_path = ["Section 1", "Subsection 1.1"]
        
        context = PromptContext(
            document_type="guidelines",
            mortgage_category=MortgageCategory.RTL,
            navigation_context=nav_context,
            extracted_entities=["entity1", "entity2"],
            decision_context={"current_decision": "credit_approval"},
            quality_requirements={"completeness": 0.95},
            processing_hints=["focus_on_rehab_requirements"]
        )
        
        self.assertEqual(context.document_type, "guidelines")
        self.assertEqual(context.mortgage_category, MortgageCategory.RTL)
        self.assertEqual(context.navigation_context, nav_context)
        self.assertEqual(len(context.extracted_entities), 2)
        self.assertEqual(context.decision_context["current_decision"], "credit_approval")
        self.assertEqual(context.quality_requirements["completeness"], 0.95)
        self.assertEqual(len(context.processing_hints), 1)


class TestPromptMetrics(unittest.TestCase):
    """Test PromptMetrics functionality"""
    
    def test_prompt_metrics_creation(self):
        """Test basic PromptMetrics creation"""
        metrics = PromptMetrics(
            prompt_id="test-prompt-1",
            execution_time_ms=150,
            output_quality_score=0.92,
            extraction_accuracy=0.89,
            consistency_score=0.94,
            user_satisfaction=0.87,
            usage_count=25,
            optimization_suggestions=["Add more examples", "Improve validation"]
        )
        
        self.assertEqual(metrics.prompt_id, "test-prompt-1")
        self.assertEqual(metrics.execution_time_ms, 150)
        self.assertEqual(metrics.output_quality_score, 0.92)
        self.assertEqual(metrics.extraction_accuracy, 0.89)
        self.assertEqual(metrics.consistency_score, 0.94)
        self.assertEqual(metrics.user_satisfaction, 0.87)
        self.assertEqual(metrics.usage_count, 25)
        self.assertEqual(len(metrics.optimization_suggestions), 2)


class TestGuidelinesPromptEngine(unittest.TestCase):
    """Test GuidelinesPromptEngine functionality"""
    
    def setUp(self):
        """Set up test environment"""
        self.engine = GuidelinesPromptEngine()
    
    def test_engine_initialization(self):
        """Test prompt engine initialization"""
        self.assertIsNotNone(self.engine.templates)
        self.assertIsNotNone(self.engine.metrics)
        self.assertTrue(len(self.engine.templates) > 0)
        
        # Check that required templates are created
        expected_templates = [
            "nav_universal",
            "nav_nqm", 
            "decision_universal",
            "entity_universal",
            "relationship_universal",
            "validation_universal",
            "quality_universal"
        ]
        
        for template_key in expected_templates:
            self.assertIn(template_key, self.engine.templates)
    
    def test_navigation_template_creation(self):
        """Test navigation template creation"""
        template = self.engine.templates["nav_universal"]
        
        self.assertEqual(template.prompt_type, PromptType.NAVIGATION)
        self.assertEqual(template.mortgage_category, MortgageCategory.UNIVERSAL)
        self.assertIn("Extract the hierarchical navigation structure", template.base_template)
        self.assertIn("content", template.context_variables)
        self.assertIn("document_type", template.context_variables)
    
    def test_nqm_navigation_template(self):
        """Test NQM-specific navigation template"""
        template = self.engine.templates["nav_nqm"]
        
        self.assertEqual(template.mortgage_category, MortgageCategory.NQM)
        self.assertIn("nqm_focus", template.domain_specific_instructions)
        self.assertIn("Bank Statement Program", template.examples[0])
    
    def test_decision_tree_template(self):
        """Test decision tree template"""
        template = self.engine.templates["decision_universal"]
        
        self.assertEqual(template.prompt_type, PromptType.DECISION_TREE)
        self.assertIn("ROOT nodes", template.base_template)
        self.assertIn("BRANCH nodes", template.base_template)
        self.assertIn("LEAF nodes", template.base_template)
        self.assertIn("APPROVE, DECLINE, REFER", template.base_template)
    
    def test_entity_extraction_template(self):
        """Test entity extraction template"""
        template = self.engine.templates["entity_universal"]
        
        self.assertEqual(template.prompt_type, PromptType.ENTITY_EXTRACTION)
        self.assertIn("LOAN_PROGRAM", template.base_template)
        self.assertIn("BORROWER_TYPE", template.base_template)
        self.assertIn("NUMERIC_THRESHOLD", template.base_template)
        self.assertIn("confidence", template.base_template)
    
    def test_generate_navigation_prompt(self):
        """Test navigation prompt generation"""
        context = PromptContext(
            document_type="guidelines",
            mortgage_category=MortgageCategory.UNIVERSAL
        )
        
        content = "Sample mortgage guideline content with sections"
        prompt = self.engine.generate_navigation_prompt(content, context)
        
        self.assertIn("Extract the hierarchical navigation structure", prompt)
        self.assertIn(content, prompt)
        self.assertIn("guidelines", prompt)
    
    def test_generate_nqm_navigation_prompt(self):
        """Test NQM-specific navigation prompt generation"""
        context = PromptContext(
            document_type="guidelines",
            mortgage_category=MortgageCategory.NQM
        )
        
        content = "Bank Statement program guidelines"
        prompt = self.engine.generate_navigation_prompt(content, context)
        
        self.assertIn("Non-QM specific sections", prompt)
        self.assertIn("Bank Statement programs", prompt)
    
    def test_generate_decision_prompt(self):
        """Test decision tree prompt generation"""
        context = PromptContext(
            document_type="guidelines",
            mortgage_category=MortgageCategory.UNIVERSAL
        )
        
        content = "Credit approval criteria and decision logic"
        navigation_context = "Credit Requirements > Approval Criteria"
        prompt = self.engine.generate_decision_prompt(content, navigation_context, context)
        
        self.assertIn("Extract complete decision trees", prompt)
        self.assertIn("APPROVE, DECLINE, REFER", prompt)
        self.assertIn(content, prompt)
        self.assertIn(navigation_context, prompt)
    
    def test_generate_entity_prompt(self):
        """Test entity extraction prompt generation"""
        context = PromptContext(
            document_type="guidelines",
            mortgage_category=MortgageCategory.UNIVERSAL
        )
        
        content = "Credit score requirements and DTI ratios"
        navigation_context = "Borrower Eligibility > Credit Requirements"
        prompt = self.engine.generate_entity_prompt(content, navigation_context, context)
        
        self.assertIn("mortgage-specific entities", prompt)
        self.assertIn("NUMERIC_THRESHOLD", prompt)
        self.assertIn(content, prompt)
        self.assertIn(navigation_context, prompt)
    
    def test_generate_relationship_prompt(self):
        """Test relationship extraction prompt generation"""
        context = PromptContext(
            document_type="guidelines",
            mortgage_category=MortgageCategory.UNIVERSAL
        )
        
        content = "Loan approval criteria and relationships"
        extracted_entities = ["credit_score_620", "dti_ratio_43"]
        navigation_context = "Approval Criteria"
        
        prompt = self.engine.generate_relationship_prompt(
            content, extracted_entities, navigation_context, context
        )
        
        self.assertIn("relationships between entities", prompt)
        self.assertIn("ENTITY_DEPENDENCY", prompt)
        self.assertIn("DECISION_DEPENDENCY", prompt)
        self.assertIn(content, prompt)
    
    def test_generate_validation_prompt(self):
        """Test validation prompt generation"""
        extracted_data = {"entities": ["entity1"], "decisions": ["decision1"]}
        navigation_structure = {"sections": ["section1"]}
        decision_trees = [{"tree_id": "tree1", "outcomes": ["APPROVE"]}]
        
        prompt = self.engine.generate_validation_prompt(
            extracted_data, navigation_structure, decision_trees
        )
        
        self.assertIn("Validate the completeness and consistency", prompt)
        self.assertIn("Navigation structure completeness", prompt)
        self.assertIn("Decision tree completeness", prompt)
    
    def test_generate_quality_prompt(self):
        """Test quality assessment prompt generation"""
        processing_results = {"accuracy": 0.92, "completeness": 0.89}
        quality_standards = {"min_accuracy": 0.85, "min_completeness": 0.90}
        
        prompt = self.engine.generate_quality_prompt(processing_results, quality_standards)
        
        self.assertIn("Assess the quality", prompt)
        self.assertIn("Accuracy", prompt)
        self.assertIn("Completeness", prompt)
        self.assertIn("Domain Compliance", prompt)
    
    def test_optimize_prompts(self):
        """Test prompt optimization based on metrics"""
        metrics = {
            "prompt1": PromptMetrics(
                prompt_id="prompt1",
                execution_time_ms=100,
                output_quality_score=0.75,  # Low quality
                extraction_accuracy=0.80,   # Low accuracy
                consistency_score=0.75,     # Low consistency
                user_satisfaction=0.80
            ),
            "prompt2": PromptMetrics(
                prompt_id="prompt2", 
                execution_time_ms=100,
                output_quality_score=0.95,  # High quality
                extraction_accuracy=0.93,   # High accuracy
                consistency_score=0.90,     # High consistency
                user_satisfaction=0.92
            )
        }
        
        optimizations = self.engine.optimize_prompts(metrics)
        
        # Should suggest optimizations for low-performing prompt1
        self.assertIn("prompt1", optimizations)
        self.assertTrue(len(optimizations["prompt1"]) > 0)
        
        # Should not suggest optimizations for high-performing prompt2
        self.assertNotIn("prompt2", optimizations)
    
    def test_update_prompt_metrics(self):
        """Test prompt metrics updating"""
        prompt_id = "test-prompt"
        
        # First update (create new metrics)
        self.engine.update_prompt_metrics(prompt_id, 150, 0.92, 0.89)
        
        self.assertIn(prompt_id, self.engine.metrics)
        metrics = self.engine.metrics[prompt_id]
        self.assertEqual(metrics.execution_time_ms, 150)
        self.assertEqual(metrics.output_quality_score, 0.92)
        self.assertEqual(metrics.extraction_accuracy, 0.89)
        self.assertEqual(metrics.usage_count, 0)
        
        # Second update (update existing metrics)
        self.engine.update_prompt_metrics(prompt_id, 120, 0.95, 0.93)
        
        updated_metrics = self.engine.metrics[prompt_id]
        self.assertEqual(updated_metrics.execution_time_ms, 120)
        self.assertEqual(updated_metrics.output_quality_score, 0.95)
        self.assertEqual(updated_metrics.extraction_accuracy, 0.93)
        self.assertEqual(updated_metrics.usage_count, 1)
    
    def test_get_prompt_performance(self):
        """Test getting prompt performance metrics"""
        prompt_id = "test-prompt"
        
        # Non-existent prompt
        metrics = self.engine.get_prompt_performance(prompt_id)
        self.assertIsNone(metrics)
        
        # Create metrics
        self.engine.update_prompt_metrics(prompt_id, 100, 0.85, 0.82)
        
        # Existing prompt
        metrics = self.engine.get_prompt_performance(prompt_id)
        self.assertIsNotNone(metrics)
        self.assertEqual(metrics.prompt_id, prompt_id)


class TestConvenienceFunctions(unittest.TestCase):
    """Test convenience functions for easy integration"""
    
    def test_create_navigation_prompt(self):
        """Test navigation prompt convenience function"""
        content = "Test mortgage document content"
        document_type = "guidelines"
        
        prompt = create_navigation_prompt(content, document_type)
        
        self.assertIn("Extract the hierarchical navigation structure", prompt)
        self.assertIn(content, prompt)
        self.assertIn(document_type, prompt)
    
    def test_create_navigation_prompt_with_category(self):
        """Test navigation prompt with specific mortgage category"""
        content = "Bank statement program guidelines"
        document_type = "guidelines"
        
        prompt = create_navigation_prompt(content, document_type, "NQM")
        
        self.assertIn("Non-QM specific sections", prompt)
        self.assertIn("Bank Statement programs", prompt)
    
    def test_create_decision_prompt(self):
        """Test decision tree prompt convenience function"""
        content = "Credit approval decision criteria"
        navigation_context = "Credit Requirements > Approval Criteria"
        
        prompt = create_decision_prompt(content, navigation_context)
        
        self.assertIn("Extract complete decision trees", prompt)
        self.assertIn("APPROVE, DECLINE, REFER", prompt)
        self.assertIn(content, prompt)
        self.assertIn(navigation_context, prompt)
    
    def test_create_entity_prompt(self):
        """Test entity extraction prompt convenience function"""
        content = "Credit score 620 minimum, DTI ratio 43%"
        navigation_context = "Borrower Requirements"
        
        prompt = create_entity_prompt(content, navigation_context)
        
        self.assertIn("mortgage-specific entities", prompt)
        self.assertIn("NUMERIC_THRESHOLD", prompt)
        self.assertIn(content, prompt)
        self.assertIn(navigation_context, prompt)
    
    def test_create_validation_prompt(self):
        """Test validation prompt convenience function"""
        extracted_data = {"entities": ["credit_score"], "decisions": ["approval"]}
        navigation_structure = {"sections": ["eligibility"]}
        decision_trees = [{"tree_id": "approval_tree"}]
        
        prompt = create_validation_prompt(extracted_data, navigation_structure, decision_trees)
        
        self.assertIn("Validate the completeness and consistency", prompt)
        self.assertIn("Navigation structure completeness", prompt)
        self.assertIn("Decision tree completeness", prompt)


class TestEnumTypes(unittest.TestCase):
    """Test enum types for prompts"""
    
    def test_prompt_type_enum(self):
        """Test PromptType enum values"""
        self.assertEqual(PromptType.NAVIGATION.value, "NAVIGATION")
        self.assertEqual(PromptType.DECISION_TREE.value, "DECISION_TREE")
        self.assertEqual(PromptType.ENTITY_EXTRACTION.value, "ENTITY_EXTRACTION")
        self.assertEqual(PromptType.RELATIONSHIP.value, "RELATIONSHIP")
        self.assertEqual(PromptType.VALIDATION.value, "VALIDATION")
        self.assertEqual(PromptType.QUALITY_ASSESSMENT.value, "QUALITY_ASSESSMENT")
    
    def test_mortgage_category_enum(self):
        """Test MortgageCategory enum values"""
        self.assertEqual(MortgageCategory.NQM.value, "NQM")
        self.assertEqual(MortgageCategory.RTL.value, "RTL")
        self.assertEqual(MortgageCategory.SBC.value, "SBC")
        self.assertEqual(MortgageCategory.CONV.value, "CONV")
        self.assertEqual(MortgageCategory.UNIVERSAL.value, "UNIVERSAL")


if __name__ == '__main__':
    unittest.main()