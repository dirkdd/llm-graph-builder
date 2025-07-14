# Task 3: Package Templates Implementation
# This file contains pre-defined templates for mortgage categories

from typing import Dict, Any, List, Optional
from src.entities.document_package import PackageCategory
import copy


class MortgagePackageTemplates:
    """Pre-defined templates for mortgage categories"""
    
    # NQM Template - Non-QM Standard Template
    NQM_TEMPLATE = {
        "category": "NQM",
        "template_name": "Non-QM Standard Template",
        "documents": [
            {
                "document_type": "guidelines",
                "document_name": "NQM Guidelines",
                "expected_structure": {
                    "chapters": [
                        "Borrower Eligibility", 
                        "Income Documentation", 
                        "Asset Requirements", 
                        "Property Standards", 
                        "Credit Analysis"
                    ],
                    "navigation_depth": 4
                },
                "required_sections": [
                    "Borrower Eligibility",
                    "Income Documentation", 
                    "Asset Requirements",
                    "Property Standards",
                    "Credit Analysis"
                ],
                "optional_sections": [
                    "Foreign National Requirements",
                    "Specialty Programs",
                    "Exception Guidelines"
                ],
                "chunking_strategy": "hierarchical",
                "entity_types": [
                    "LOAN_PROGRAM", 
                    "BORROWER_TYPE", 
                    "REQUIREMENT", 
                    "NUMERIC_THRESHOLD",
                    "POLICY_RULE"
                ],
                "decision_trees": ["eligibility", "documentation", "property"],
                "quality_thresholds": {
                    "navigation_accuracy": 0.95,
                    "decision_completeness": 1.0,
                    "entity_coverage": 0.90
                },
                "validation_schema": {
                    "required_entities": ["LOAN_PROGRAM", "BORROWER_TYPE"],
                    "minimum_sections": 5
                }
            },
            {
                "document_type": "matrix",
                "document_name": "NQM Matrix",
                "matrix_configuration": {
                    "matrix_types": ["qualification", "pricing", "ltv_matrix"],
                    "dimensions": ["fico_score", "ltv_ratio", "dti_ratio"],
                    "expected_structure": {
                        "matrix_count": 3,
                        "dimension_ranges": {
                            "fico_score": [580, 850],
                            "ltv_ratio": [0.1, 0.95],
                            "dti_ratio": [0.1, 0.50]
                        }
                    }
                },
                "chunking_strategy": "matrix_aware",
                "entity_types": ["MATRIX_VALUE", "THRESHOLD", "CONDITION"],
                "quality_thresholds": {
                    "matrix_completeness": 1.0,
                    "value_accuracy": 0.99
                }
            }
        ],
        "relationships": [
            {
                "from_document": "guidelines",
                "to_document": "matrix",
                "relationship_type": "ELABORATES",
                "metadata": {
                    "connection_type": "policy_to_matrix",
                    "sections": ["eligibility", "qualification"]
                }
            },
            {
                "from_document": "guidelines",
                "to_document": "matrix", 
                "relationship_type": "DETERMINES",
                "metadata": {
                    "connection_type": "criteria_to_pricing",
                    "sections": ["credit_analysis", "pricing"]
                }
            }
        ],
        "customizations": {
            "investor_specific": {
                "additional_sections": ["Investor Guidelines", "Special Instructions"],
                "entity_types": ["INVESTOR_REQUIREMENT"]
            },
            "state_specific": {
                "additional_sections": ["State Regulations", "Disclosure Requirements"],
                "entity_types": ["STATE_REQUIREMENT", "DISCLOSURE"]
            }
        }
    }
    
    # RTL Template - Rental/Investment Property Template
    RTL_TEMPLATE = {
        "category": "RTL",
        "template_name": "Rental/Investment Property Template",
        "documents": [
            {
                "document_type": "guidelines",
                "document_name": "RTL Guidelines",
                "expected_structure": {
                    "chapters": [
                        "Rehab Requirements",
                        "Draw Schedule", 
                        "Inspection Process",
                        "Completion Standards",
                        "Investment Property Analysis"
                    ],
                    "navigation_depth": 3
                },
                "required_sections": [
                    "Rehab Requirements",
                    "Draw Schedule", 
                    "Inspection Process",
                    "Completion Standards",
                    "Investment Property Analysis"
                ],
                "optional_sections": [
                    "Environmental Considerations",
                    "Specialty Property Types"
                ],
                "chunking_strategy": "hierarchical",
                "entity_types": [
                    "PROPERTY_TYPE", 
                    "REHAB_REQUIREMENT", 
                    "INSPECTION_MILESTONE",
                    "COMPLETION_STANDARD"
                ],
                "decision_trees": ["rehab_eligibility", "draw_approval", "completion_verification"],
                "quality_thresholds": {
                    "navigation_accuracy": 0.90,
                    "decision_completeness": 0.95,
                    "entity_coverage": 0.85
                }
            },
            {
                "document_type": "matrix",
                "document_name": "RTL Matrix",
                "matrix_configuration": {
                    "matrix_types": ["rehab_cost", "arv_matrix", "rental_income"],
                    "dimensions": ["property_value", "rehab_percentage", "rental_yield"],
                    "expected_structure": {
                        "matrix_count": 3,
                        "dimension_ranges": {
                            "property_value": [50000, 2000000],
                            "rehab_percentage": [0.1, 0.5],
                            "rental_yield": [0.05, 0.15]
                        }
                    }
                },
                "chunking_strategy": "matrix_aware",
                "entity_types": ["MATRIX_VALUE", "PROPERTY_VALUE", "REHAB_COST"]
            }
        ],
        "relationships": [
            {
                "from_document": "guidelines",
                "to_document": "matrix",
                "relationship_type": "DEFINES",
                "metadata": {
                    "connection_type": "requirements_to_matrix",
                    "sections": ["rehab_requirements", "rehab_cost"]
                }
            }
        ]
    }
    
    # SBC Template - Small Balance Commercial Template  
    SBC_TEMPLATE = {
        "category": "SBC",
        "template_name": "Small Balance Commercial Template",
        "documents": [
            {
                "document_type": "guidelines",
                "document_name": "SBC Guidelines",
                "expected_structure": {
                    "chapters": [
                        "Property Requirements",
                        "Income Analysis",
                        "Debt Service Coverage", 
                        "Environmental Review",
                        "Commercial Underwriting"
                    ],
                    "navigation_depth": 3
                },
                "required_sections": [
                    "Property Requirements",
                    "Income Analysis",
                    "Debt Service Coverage",
                    "Environmental Review"
                ],
                "optional_sections": [
                    "Special Use Properties",
                    "Multi-Tenant Considerations"
                ],
                "chunking_strategy": "hierarchical",
                "entity_types": [
                    "COMMERCIAL_PROPERTY", 
                    "INCOME_SOURCE", 
                    "ENVIRONMENTAL_FACTOR",
                    "DEBT_SERVICE_RATIO"
                ],
                "decision_trees": ["property_eligibility", "income_verification", "environmental_assessment"],
                "quality_thresholds": {
                    "navigation_accuracy": 0.90,
                    "decision_completeness": 0.90,
                    "entity_coverage": 0.85
                }
            }
        ],
        "relationships": []
    }
    
    # CONV Template - Conventional Mortgage Template
    CONV_TEMPLATE = {
        "category": "CONV", 
        "template_name": "Conventional Mortgage Template",
        "documents": [
            {
                "document_type": "guidelines",
                "document_name": "Conventional Guidelines",
                "expected_structure": {
                    "chapters": [
                        "Standard Eligibility",
                        "Income Requirements", 
                        "Credit Standards",
                        "Property Requirements",
                        "Standard Underwriting"
                    ],
                    "navigation_depth": 3
                },
                "required_sections": [
                    "Standard Eligibility",
                    "Income Requirements", 
                    "Credit Standards",
                    "Property Requirements"
                ],
                "optional_sections": [
                    "First-Time Buyer Programs",
                    "Special Circumstances"
                ],
                "chunking_strategy": "hierarchical",
                "entity_types": [
                    "BORROWER_TYPE", 
                    "INCOME_TYPE", 
                    "CREDIT_REQUIREMENT",
                    "PROPERTY_STANDARD"
                ],
                "decision_trees": ["standard_eligibility", "income_verification", "credit_assessment"],
                "quality_thresholds": {
                    "navigation_accuracy": 0.95,
                    "decision_completeness": 0.95,
                    "entity_coverage": 0.90
                }
            }
        ],
        "relationships": []
    }
    
    @staticmethod
    def get_template(category: PackageCategory) -> Dict[str, Any]:
        """Get template configuration for category
        
        Args:
            category: Package category enum
            
        Returns:
            Dict containing template configuration
            
        Raises:
            ValueError: If category not supported
        """
        templates = {
            PackageCategory.NQM: MortgagePackageTemplates.NQM_TEMPLATE,
            PackageCategory.RTL: MortgagePackageTemplates.RTL_TEMPLATE,
            PackageCategory.SBC: MortgagePackageTemplates.SBC_TEMPLATE,
            PackageCategory.CONV: MortgagePackageTemplates.CONV_TEMPLATE
        }
        
        template = templates.get(category)
        if not template:
            valid_categories = [c.value for c in PackageCategory]
            raise ValueError(f"No template found for category {category}. Valid categories: {valid_categories}")
        
        # Return deep copy to prevent template modification
        return copy.deepcopy(template)
    
    @staticmethod
    def create_package_from_template(category: PackageCategory, 
                                   package_name: str,
                                   tenant_id: str,
                                   customizations: Dict[str, Any] = None) -> Dict[str, Any]:
        """Create package configuration from template with customizations
        
        Args:
            category: Package category
            package_name: Name for the package
            tenant_id: Tenant identifier
            customizations: Optional customizations to apply
            
        Returns:
            Dict containing complete package configuration
            
        Raises:
            ValueError: If template not found or customizations invalid
        """
        template = MortgagePackageTemplates.get_template(category)
        
        # Create package configuration
        package_config = {
            "package_name": package_name,
            "tenant_id": tenant_id,
            "category": category.value,
            "template": template["template_name"],
            "documents": template["documents"],
            "relationships": template["relationships"]
        }
        
        # Apply customizations if provided
        if customizations:
            package_config = MortgagePackageTemplates._apply_customizations(
                package_config, customizations
            )
        
        return package_config
    
    @staticmethod
    def _apply_customizations(package_config: Dict[str, Any], 
                            customizations: Dict[str, Any]) -> Dict[str, Any]:
        """Apply customizations to package configuration
        
        Args:
            package_config: Base package configuration
            customizations: Customizations to apply
            
        Returns:
            Modified package configuration
        """
        # Apply additional sections to documents
        if "additional_sections" in customizations:
            for doc in package_config["documents"]:
                if "optional_sections" not in doc:
                    doc["optional_sections"] = []
                doc["optional_sections"].extend(customizations["additional_sections"])
        
        # Apply additional entity types
        if "additional_entity_types" in customizations:
            for doc in package_config["documents"]:
                if "entity_types" not in doc:
                    doc["entity_types"] = []
                doc["entity_types"].extend(customizations["additional_entity_types"])
        
        # Apply custom quality thresholds
        if "quality_thresholds" in customizations:
            for doc in package_config["documents"]:
                if "quality_thresholds" not in doc:
                    doc["quality_thresholds"] = {}
                doc["quality_thresholds"].update(customizations["quality_thresholds"])
        
        # Apply investor-specific customizations
        if "investor_name" in customizations:
            package_config["investor_name"] = customizations["investor_name"]
            
            # Add investor-specific sections if available in template
            template = MortgagePackageTemplates.get_template(
                PackageCategory(package_config["category"])
            )
            if "customizations" in template and "investor_specific" in template["customizations"]:
                investor_custom = template["customizations"]["investor_specific"]
                package_config = MortgagePackageTemplates._apply_customizations(
                    package_config, investor_custom
                )
        
        # Apply state-specific customizations
        if "state" in customizations:
            package_config["state"] = customizations["state"]
            
            # Add state-specific sections if available in template
            template = MortgagePackageTemplates.get_template(
                PackageCategory(package_config["category"])
            )
            if "customizations" in template and "state_specific" in template["customizations"]:
                state_custom = template["customizations"]["state_specific"]
                package_config = MortgagePackageTemplates._apply_customizations(
                    package_config, state_custom
                )
        
        return package_config
    
    @staticmethod
    def get_available_templates() -> List[Dict[str, str]]:
        """Get list of available templates
        
        Returns:
            List of template info dictionaries
        """
        return [
            {
                "category": "NQM",
                "template_name": "Non-QM Standard Template",
                "description": "Guidelines and matrix for non-QM loans"
            },
            {
                "category": "RTL", 
                "template_name": "Rental/Investment Property Template",
                "description": "Rehab and investment property guidelines"
            },
            {
                "category": "SBC",
                "template_name": "Small Balance Commercial Template", 
                "description": "Commercial property guidelines"
            },
            {
                "category": "CONV",
                "template_name": "Conventional Mortgage Template",
                "description": "Standard conventional mortgage guidelines"
            }
        ]
    
    @staticmethod
    def validate_template(template: Dict[str, Any]) -> List[str]:
        """Validate template structure
        
        Args:
            template: Template configuration to validate
            
        Returns:
            List of validation errors (empty if valid)
        """
        errors = []
        
        # Check required template fields
        required_fields = ["category", "template_name", "documents"]
        for field in required_fields:
            if field not in template:
                errors.append(f"Missing required field: {field}")
        
        # Validate documents
        if "documents" in template:
            if not template["documents"]:
                errors.append("Template must contain at least one document")
            
            for i, doc in enumerate(template["documents"]):
                doc_errors = MortgagePackageTemplates._validate_document_template(doc, f"documents[{i}]")
                errors.extend(doc_errors)
        
        # Validate relationships if present
        if "relationships" in template:
            for i, rel in enumerate(template["relationships"]):
                rel_errors = MortgagePackageTemplates._validate_relationship_template(rel, f"relationships[{i}]")
                errors.extend(rel_errors)
        
        return errors
    
    @staticmethod
    def _validate_document_template(doc: Dict[str, Any], prefix: str) -> List[str]:
        """Validate document template structure"""
        errors = []
        
        required_fields = ["document_type", "document_name"]
        for field in required_fields:
            if field not in doc:
                errors.append(f"{prefix}: Missing required field: {field}")
        
        # Validate document type
        if "document_type" in doc:
            valid_types = ["guidelines", "matrix", "policy", "checklist"]
            if doc["document_type"] not in valid_types:
                errors.append(f"{prefix}: Invalid document_type. Must be one of: {valid_types}")
        
        return errors
    
    @staticmethod 
    def _validate_relationship_template(rel: Dict[str, Any], prefix: str) -> List[str]:
        """Validate relationship template structure"""
        errors = []
        
        required_fields = ["from_document", "to_document", "relationship_type"]
        for field in required_fields:
            if field not in rel:
                errors.append(f"{prefix}: Missing required field: {field}")
        
        return errors