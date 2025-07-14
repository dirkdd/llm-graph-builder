# Task 16: Enhanced Processing Prompts Implementation
# Specialized prompts for mortgage document processing with domain expertise

from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
import json
from datetime import datetime

# Import existing entities and models
from src.entities.navigation_models import (
    NavigationContext,
    DecisionOutcome,
    QualityRating
)


class PromptType(Enum):
    """Types of prompts for different processing stages"""
    NAVIGATION = "NAVIGATION"
    DECISION_TREE = "DECISION_TREE"
    ENTITY_EXTRACTION = "ENTITY_EXTRACTION"
    RELATIONSHIP = "RELATIONSHIP"
    VALIDATION = "VALIDATION"
    QUALITY_ASSESSMENT = "QUALITY_ASSESSMENT"


class MortgageCategory(Enum):
    """Mortgage categories for specialized processing"""
    NQM = "NQM"          # Non-QM loans
    RTL = "RTL"          # Rehab-to-Let
    SBC = "SBC"          # Small Business Commercial
    CONV = "CONV"        # Conventional mortgages
    UNIVERSAL = "UNIVERSAL"  # Common patterns across all categories


@dataclass
class PromptTemplate:
    """Template for generating specialized prompts"""
    template_id: str
    prompt_type: PromptType
    mortgage_category: MortgageCategory
    base_template: str
    context_variables: List[str] = field(default_factory=list)
    domain_specific_instructions: Dict[str, str] = field(default_factory=dict)
    examples: List[str] = field(default_factory=list)
    validation_criteria: List[str] = field(default_factory=list)
    performance_hints: List[str] = field(default_factory=list)
    
    def generate_prompt(self, context: Dict[str, Any]) -> str:
        """Generate a complete prompt from template and context"""
        prompt = self.base_template
        
        # Replace context variables
        for var in self.context_variables:
            if var in context:
                prompt = prompt.replace(f"{{{var}}}", str(context[var]))
        
        # Add domain-specific instructions
        if self.domain_specific_instructions:
            instructions = "\n\nDomain-Specific Instructions:\n"
            for key, instruction in self.domain_specific_instructions.items():
                instructions += f"- {key}: {instruction}\n"
            prompt += instructions
        
        # Add examples if available
        if self.examples:
            examples_section = "\n\nExamples:\n"
            for i, example in enumerate(self.examples, 1):
                examples_section += f"{i}. {example}\n"
            prompt += examples_section
        
        # Add validation criteria
        if self.validation_criteria:
            validation_section = "\n\nValidation Criteria:\n"
            for criterion in self.validation_criteria:
                validation_section += f"- {criterion}\n"
            prompt += validation_section
        
        return prompt


@dataclass
class PromptContext:
    """Context information for prompt generation"""
    document_type: str
    mortgage_category: MortgageCategory
    navigation_context: Optional[NavigationContext] = None
    extracted_entities: List[str] = field(default_factory=list)
    decision_context: Dict[str, Any] = field(default_factory=dict)
    quality_requirements: Dict[str, float] = field(default_factory=dict)
    processing_hints: List[str] = field(default_factory=list)


@dataclass
class PromptMetrics:
    """Metrics for prompt performance and optimization"""
    prompt_id: str
    execution_time_ms: int
    output_quality_score: float
    extraction_accuracy: float
    consistency_score: float
    user_satisfaction: float
    usage_count: int = 0
    optimization_suggestions: List[str] = field(default_factory=list)


class GuidelinesPromptEngine:
    """Engine for generating specialized mortgage document processing prompts"""
    
    def __init__(self):
        self.templates: Dict[str, PromptTemplate] = {}
        self.metrics: Dict[str, PromptMetrics] = {}
        self._initialize_templates()
    
    def _initialize_templates(self):
        """Initialize all prompt templates"""
        # Navigation extraction templates
        self._create_navigation_templates()
        
        # Decision tree extraction templates
        self._create_decision_tree_templates()
        
        # Entity extraction templates
        self._create_entity_extraction_templates()
        
        # Relationship extraction templates
        self._create_relationship_templates()
        
        # Validation templates
        self._create_validation_templates()
        
        # Quality assessment templates
        self._create_quality_templates()
    
    def _create_navigation_templates(self):
        """Create navigation extraction prompt templates"""
        
        # Universal navigation template
        universal_nav = PromptTemplate(
            template_id="nav_universal",
            prompt_type=PromptType.NAVIGATION,
            mortgage_category=MortgageCategory.UNIVERSAL,
            base_template="""
Extract the hierarchical navigation structure from this mortgage document.

Document Type: {document_type}
Content: {content}

Extract the following navigation elements:
1. Main sections and subsections with proper hierarchy
2. Section numbers and titles
3. Page references where available
4. Table of contents structure
5. Cross-references between sections

Return the navigation structure as a JSON object with the following format:
{{
    "root_sections": [
        {{
            "section_id": "unique_id",
            "section_number": "1.0",
            "title": "Section Title",
            "level": 1,
            "page_reference": 5,
            "children": [
                {{
                    "section_id": "unique_id",
                    "section_number": "1.1",
                    "title": "Subsection Title",
                    "level": 2,
                    "page_reference": 6,
                    "children": []
                }}
            ]
        }}
    ],
    "cross_references": [
        {{
            "from_section": "section_id",
            "to_section": "section_id",
            "reference_type": "see_also"
        }}
    ]
}}
""",
            context_variables=["document_type", "content"],
            domain_specific_instructions={
                "mortgage_focus": "Pay special attention to loan programs, borrower requirements, and approval criteria sections",
                "hierarchy_preservation": "Maintain exact document hierarchy including numbering systems",
                "cross_references": "Identify all references to other sections, appendices, and external documents"
            },
            validation_criteria=[
                "All sections must have unique identifiers",
                "Section numbering must be consistent with document",
                "Hierarchy levels must be accurate",
                "Cross-references must be valid"
            ]
        )
        self.templates["nav_universal"] = universal_nav
        
        # NQM-specific navigation template
        nqm_nav = PromptTemplate(
            template_id="nav_nqm",
            prompt_type=PromptType.NAVIGATION,
            mortgage_category=MortgageCategory.NQM,
            base_template=universal_nav.base_template,
            context_variables=["document_type", "content"],
            domain_specific_instructions={
                "nqm_focus": "Focus on Non-QM specific sections: Bank Statement programs, Asset Depletion, P&L programs",
                "alternative_doc": "Identify alternative documentation requirements and validation methods",
                "investor_guidelines": "Extract investor-specific guidelines and overlays",
                "risk_factors": "Highlight non-traditional risk assessment criteria"
            },
            examples=[
                "Bank Statement Program requirements with 12-24 month bank statements",
                "Asset Depletion calculation methods and asset types",
                "Profit & Loss statement requirements for self-employed borrowers"
            ]
        )
        self.templates["nav_nqm"] = nqm_nav
    
    def _create_decision_tree_templates(self):
        """Create decision tree extraction prompt templates"""
        
        decision_template = PromptTemplate(
            template_id="decision_universal",
            prompt_type=PromptType.DECISION_TREE,
            mortgage_category=MortgageCategory.UNIVERSAL,
            base_template="""
Extract complete decision trees from this mortgage content with mandatory outcomes.

Content: {content}
Navigation Context: {navigation_context}

Extract decision trees that include:
1. ROOT nodes: Entry points to decision processes
2. BRANCH nodes: Decision points with specific conditions
3. LEAF nodes: Final outcomes (APPROVE, DECLINE, REFER)

For each decision tree, ensure:
- Every path from ROOT to LEAF is complete
- All decision conditions are clearly defined
- Mandatory outcomes are present: APPROVE, DECLINE, REFER
- Logical consistency throughout the tree

Return decision trees in JSON format:
{{
    "decision_trees": [
        {{
            "tree_id": "unique_tree_id",
            "root_condition": "Initial condition or entry point",
            "branches": [
                {{
                    "condition": "credit_score >= 620",
                    "outcome_type": "BRANCH",
                    "next_conditions": [
                        {{
                            "condition": "dti <= 0.43",
                            "outcome_type": "LEAF",
                            "final_outcome": "APPROVE"
                        }},
                        {{
                            "condition": "dti > 0.43",
                            "outcome_type": "LEAF", 
                            "final_outcome": "DECLINE"
                        }}
                    ]
                }},
                {{
                    "condition": "credit_score < 620",
                    "outcome_type": "LEAF",
                    "final_outcome": "REFER"
                }}
            ]
        }}
    ]
}}

CRITICAL: Every decision path MUST end with one of: APPROVE, DECLINE, or REFER.
""",
            context_variables=["content", "navigation_context"],
            domain_specific_instructions={
                "completeness_requirement": "Every decision tree must have complete paths with guaranteed outcomes",
                "mortgage_criteria": "Focus on credit scores, DTI ratios, LTV ratios, employment history, and income verification",
                "logical_flow": "Ensure logical consistency in decision conditions and outcomes"
            },
            validation_criteria=[
                "All decision paths must be complete",
                "Every path must end with APPROVE, DECLINE, or REFER",
                "No orphaned decision nodes allowed",
                "Decision conditions must be mutually exclusive where appropriate"
            ]
        )
        self.templates["decision_universal"] = decision_template
    
    def _create_entity_extraction_templates(self):
        """Create entity extraction prompt templates"""
        
        entity_template = PromptTemplate(
            template_id="entity_universal", 
            prompt_type=PromptType.ENTITY_EXTRACTION,
            mortgage_category=MortgageCategory.UNIVERSAL,
            base_template="""
Extract mortgage-specific entities from this content with navigation context preservation.

Content: {content}
Navigation Context: {navigation_context}

Extract the following entity types:
1. LOAN_PROGRAM: Specific loan programs (FHA, VA, USDA, Conventional, etc.)
2. BORROWER_TYPE: Borrower classifications (first-time buyer, investor, etc.)
3. NUMERIC_THRESHOLD: Credit scores, DTI ratios, LTV limits, etc.
4. DOLLAR_AMOUNT: Loan amounts, income requirements, reserve amounts
5. PROPERTY_TYPE: Single family, condo, townhome, multi-unit, etc.
6. DECISION_CRITERIA: Approval/decline criteria and conditions
7. MATRIX_VALUE: Specific values from rate/pricing matrices
8. REQUIREMENT: Documentation and verification requirements
9. FINANCIAL_RATIO: DTI, LTV, Coverage ratios, etc.
10. OCCUPANCY_TYPE: Primary residence, secondary home, investment

For each entity, provide:
- Entity type and value
- Confidence score (0.0 to 1.0)
- Source location in navigation hierarchy
- Related entities and relationships
- Validation rules where applicable

Return entities in JSON format:
{{
    "extracted_entities": [
        {{
            "entity_id": "unique_id",
            "entity_type": "NUMERIC_THRESHOLD",
            "value": "620",
            "normalized_value": "620",
            "unit": "credit_score",
            "confidence": 0.95,
            "navigation_path": "Borrower Eligibility > Credit Requirements",
            "source_chunk_id": "chunk_123",
            "related_entities": ["entity_id_2", "entity_id_3"],
            "validation_rules": ["must_be_numeric", "range_580_850"]
        }}
    ]
}}
""",
            context_variables=["content", "navigation_context"],
            domain_specific_instructions={
                "domain_vocabulary": "Use mortgage industry standard terminology and classifications",
                "context_preservation": "Maintain navigation context for all extracted entities",
                "validation_focus": "Apply mortgage-specific validation rules for numeric thresholds and amounts"
            },
            validation_criteria=[
                "All numeric entities must have valid ranges",
                "Entity types must match mortgage domain standards", 
                "Navigation context must be preserved",
                "Confidence scores must be justified"
            ]
        )
        self.templates["entity_universal"] = entity_template
    
    def _create_relationship_templates(self):
        """Create relationship extraction prompt templates"""
        
        relationship_template = PromptTemplate(
            template_id="relationship_universal",
            prompt_type=PromptType.RELATIONSHIP,
            mortgage_category=MortgageCategory.UNIVERSAL,
            base_template="""
Extract relationships between entities and decision elements in this mortgage content.

Content: {content}
Extracted Entities: {extracted_entities}
Navigation Context: {navigation_context}

Identify the following relationship types:
1. ENTITY_DEPENDENCY: Entities that depend on other entities
2. DECISION_DEPENDENCY: Entities that influence decision outcomes
3. CONDITIONAL_RELATIONSHIP: If/then relationships between entities
4. HIERARCHICAL_RELATIONSHIP: Parent-child entity relationships
5. CROSS_REFERENCE: References between different document sections
6. MATRIX_GUIDELINE: Relationships between matrix values and guidelines

For each relationship, provide:
- Relationship type and strength
- Source and target entities
- Relationship conditions
- Navigation context preservation

Return relationships in JSON format:
{{
    "entity_relationships": [
        {{
            "relationship_id": "unique_id",
            "relationship_type": "DECISION_DEPENDENCY",
            "source_entity_id": "credit_score_620",
            "target_entity_id": "approval_decision",
            "relationship_strength": 0.9,
            "conditions": ["credit_score >= 620"],
            "navigation_context": "Credit Requirements > Approval Criteria"
        }}
    ]
}}
""",
            context_variables=["content", "extracted_entities", "navigation_context"],
            validation_criteria=[
                "All referenced entities must exist",
                "Relationship strengths must be between 0.0 and 1.0", 
                "Navigation context must be maintained",
                "Conditions must be clearly defined"
            ]
        )
        self.templates["relationship_universal"] = relationship_template
    
    def _create_validation_templates(self):
        """Create validation prompt templates"""
        
        validation_template = PromptTemplate(
            template_id="validation_universal",
            prompt_type=PromptType.VALIDATION,
            mortgage_category=MortgageCategory.UNIVERSAL,
            base_template="""
Validate the completeness and consistency of extracted mortgage document information.

Extracted Data: {extracted_data}
Navigation Structure: {navigation_structure}
Decision Trees: {decision_trees}

Validate the following aspects:
1. Navigation structure completeness and consistency
2. Decision tree completeness (all paths end with outcomes)
3. Entity extraction accuracy and domain compliance
4. Relationship consistency and logical flow
5. Cross-reference validity
6. Missing critical information identification

For each validation check, provide:
- Validation status (PASS/FAIL/WARNING)
- Issue description if applicable
- Suggested fixes for issues
- Quality score (0.0 to 1.0)

Return validation results in JSON format:
{{
    "validation_results": [
        {{
            "validation_type": "DECISION_TREE_COMPLETENESS",
            "status": "PASS",
            "quality_score": 0.95,
            "issues": [],
            "suggestions": []
        }},
        {{
            "validation_type": "ENTITY_CONSISTENCY", 
            "status": "WARNING",
            "quality_score": 0.78,
            "issues": ["Missing DTI threshold for investor properties"],
            "suggestions": ["Add default DTI threshold of 0.43 for investor properties"]
        }}
    ],
    "overall_quality_score": 0.87,
    "completeness_percentage": 92.5
}}
""",
            context_variables=["extracted_data", "navigation_structure", "decision_trees"],
            validation_criteria=[
                "All validation checks must have status and quality score",
                "Issues must have corresponding suggestions where possible",
                "Overall quality score must reflect individual validation scores"
            ]
        )
        self.templates["validation_universal"] = validation_template
    
    def _create_quality_templates(self):
        """Create quality assessment prompt templates"""
        
        quality_template = PromptTemplate(
            template_id="quality_universal",
            prompt_type=PromptType.QUALITY_ASSESSMENT,
            mortgage_category=MortgageCategory.UNIVERSAL,
            base_template="""
Assess the quality of mortgage document processing results.

Processing Results: {processing_results}
Expected Standards: {quality_standards}

Assess quality across these dimensions:
1. Accuracy: Correctness of extracted information
2. Completeness: Coverage of all required information
3. Consistency: Logical consistency across all extractions
4. Domain Compliance: Adherence to mortgage industry standards
5. Navigation Preservation: Maintenance of document structure
6. Decision Logic: Completeness and validity of decision trees

For each dimension, provide:
- Quality score (0.0 to 1.0)
- Specific assessment criteria
- Areas of strength and improvement
- Recommendations for enhancement

Return quality assessment in JSON format:
{{
    "quality_assessment": {{
        "accuracy": {{
            "score": 0.92,
            "criteria": "Extracted entities match document content",
            "strengths": ["Accurate numeric threshold extraction"],
            "improvements": ["Better property type classification"],
            "recommendations": ["Enhance property type vocabulary"]
        }},
        "overall_quality": {{
            "score": 0.89,
            "rating": "GOOD",
            "summary": "High quality extraction with minor improvements needed"
        }}
    }}
}}
""",
            context_variables=["processing_results", "quality_standards"],
            validation_criteria=[
                "All quality scores must be between 0.0 and 1.0",
                "Each dimension must have specific criteria",
                "Recommendations must be actionable"
            ]
        )
        self.templates["quality_universal"] = quality_template
    
    def generate_navigation_prompt(
        self, 
        content: str, 
        context: PromptContext
    ) -> str:
        """Generate navigation extraction prompt"""
        template_key = f"nav_{context.mortgage_category.value.lower()}"
        if template_key not in self.templates:
            template_key = "nav_universal"
        
        template = self.templates[template_key]
        prompt_context = {
            "document_type": context.document_type,
            "content": content
        }
        
        return template.generate_prompt(prompt_context)
    
    def generate_decision_prompt(
        self, 
        content: str, 
        navigation_context: str, 
        context: PromptContext
    ) -> str:
        """Generate decision tree extraction prompt with outcome guarantees"""
        template = self.templates["decision_universal"]
        prompt_context = {
            "content": content,
            "navigation_context": navigation_context
        }
        
        return template.generate_prompt(prompt_context)
    
    def generate_entity_prompt(
        self, 
        content: str, 
        navigation_context: str, 
        context: PromptContext
    ) -> str:
        """Generate entity extraction prompt with domain context"""
        template = self.templates["entity_universal"]
        prompt_context = {
            "content": content,
            "navigation_context": navigation_context
        }
        
        return template.generate_prompt(prompt_context)
    
    def generate_relationship_prompt(
        self, 
        content: str, 
        extracted_entities: List[str], 
        navigation_context: str, 
        context: PromptContext
    ) -> str:
        """Generate relationship extraction prompt"""
        template = self.templates["relationship_universal"]
        prompt_context = {
            "content": content,
            "extracted_entities": json.dumps(extracted_entities),
            "navigation_context": navigation_context
        }
        
        return template.generate_prompt(prompt_context)
    
    def generate_validation_prompt(
        self, 
        extracted_data: Dict[str, Any], 
        navigation_structure: Dict[str, Any], 
        decision_trees: List[Dict[str, Any]]
    ) -> str:
        """Generate validation prompt for completeness checking"""
        template = self.templates["validation_universal"]
        prompt_context = {
            "extracted_data": json.dumps(extracted_data),
            "navigation_structure": json.dumps(navigation_structure),
            "decision_trees": json.dumps(decision_trees)
        }
        
        return template.generate_prompt(prompt_context)
    
    def generate_quality_prompt(
        self, 
        processing_results: Dict[str, Any], 
        quality_standards: Dict[str, float]
    ) -> str:
        """Generate quality assessment prompt"""
        template = self.templates["quality_universal"]
        prompt_context = {
            "processing_results": json.dumps(processing_results),
            "quality_standards": json.dumps(quality_standards)
        }
        
        return template.generate_prompt(prompt_context)
    
    def optimize_prompts(self, metrics: Dict[str, PromptMetrics]) -> Dict[str, str]:
        """Optimize prompts based on performance metrics"""
        optimizations = {}
        
        for prompt_id, metric in metrics.items():
            if metric.output_quality_score < 0.8:
                suggestions = []
                
                if metric.extraction_accuracy < 0.85:
                    suggestions.append("Add more specific domain examples")
                    suggestions.append("Enhance validation criteria")
                
                if metric.consistency_score < 0.8:
                    suggestions.append("Improve logical flow instructions")
                    suggestions.append("Add consistency validation checks")
                
                optimizations[prompt_id] = suggestions
        
        return optimizations
    
    def get_prompt_performance(self, prompt_id: str) -> Optional[PromptMetrics]:
        """Get performance metrics for a specific prompt"""
        return self.metrics.get(prompt_id)
    
    def update_prompt_metrics(
        self, 
        prompt_id: str, 
        execution_time: int, 
        quality_score: float, 
        accuracy: float
    ):
        """Update performance metrics for a prompt"""
        if prompt_id not in self.metrics:
            self.metrics[prompt_id] = PromptMetrics(
                prompt_id=prompt_id,
                execution_time_ms=execution_time,
                output_quality_score=quality_score,
                extraction_accuracy=accuracy,
                consistency_score=0.0,
                user_satisfaction=0.0
            )
        else:
            metric = self.metrics[prompt_id]
            metric.usage_count += 1
            metric.execution_time_ms = execution_time
            metric.output_quality_score = quality_score
            metric.extraction_accuracy = accuracy


# Convenience functions for easy integration
def create_navigation_prompt(content: str, document_type: str, mortgage_category: str = "UNIVERSAL") -> str:
    """Create navigation extraction prompt"""
    engine = GuidelinesPromptEngine()
    context = PromptContext(
        document_type=document_type,
        mortgage_category=MortgageCategory(mortgage_category)
    )
    return engine.generate_navigation_prompt(content, context)


def create_decision_prompt(content: str, navigation_context: str) -> str:
    """Create decision tree extraction prompt with outcome guarantees"""
    engine = GuidelinesPromptEngine()
    context = PromptContext(
        document_type="guidelines",
        mortgage_category=MortgageCategory.UNIVERSAL
    )
    return engine.generate_decision_prompt(content, navigation_context, context)


def create_entity_prompt(content: str, navigation_context: str) -> str:
    """Create entity extraction prompt with domain expertise"""
    engine = GuidelinesPromptEngine()
    context = PromptContext(
        document_type="guidelines",
        mortgage_category=MortgageCategory.UNIVERSAL
    )
    return engine.generate_entity_prompt(content, navigation_context, context)


def create_validation_prompt(extracted_data: Dict[str, Any], navigation_structure: Dict[str, Any], decision_trees: List[Dict[str, Any]]) -> str:
    """Create validation prompt for quality checking"""
    engine = GuidelinesPromptEngine()
    return engine.generate_validation_prompt(extracted_data, navigation_structure, decision_trees)