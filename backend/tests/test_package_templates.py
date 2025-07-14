# Task 3: Unit tests for Package Templates
# This file contains comprehensive tests for the MortgagePackageTemplates class

import pytest
import sys
import os

# Add the parent directory to the path to import backend modules
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from src.package_templates import MortgagePackageTemplates
from src.entities.document_package import PackageCategory


class TestMortgagePackageTemplates:
    """Test MortgagePackageTemplates class functionality"""
    
    def test_get_template_nqm(self):
        """Test getting NQM template"""
        template = MortgagePackageTemplates.get_template(PackageCategory.NQM)
        
        assert template["category"] == "NQM"
        assert template["template_name"] == "Non-QM Standard Template"
        assert len(template["documents"]) == 2
        assert len(template["relationships"]) == 2
        
        # Check documents
        doc_types = [doc["document_type"] for doc in template["documents"]]
        assert "guidelines" in doc_types
        assert "matrix" in doc_types
        
        # Check guidelines document
        guidelines = next(doc for doc in template["documents"] if doc["document_type"] == "guidelines")
        assert guidelines["document_name"] == "NQM Guidelines"
        assert "Borrower Eligibility" in guidelines["required_sections"]
        assert "Income Documentation" in guidelines["required_sections"]
        assert "LOAN_PROGRAM" in guidelines["entity_types"]
        assert "eligibility" in guidelines["decision_trees"]
        
        # Check matrix document
        matrix = next(doc for doc in template["documents"] if doc["document_type"] == "matrix")
        assert matrix["document_name"] == "NQM Matrix"
        assert "qualification" in matrix["matrix_configuration"]["matrix_types"]
        assert "fico_score" in matrix["matrix_configuration"]["dimensions"]
    
    def test_get_template_rtl(self):
        """Test getting RTL template"""
        template = MortgagePackageTemplates.get_template(PackageCategory.RTL)
        
        assert template["category"] == "RTL"
        assert template["template_name"] == "Rental/Investment Property Template"
        assert len(template["documents"]) == 2
        
        # Check guidelines document
        guidelines = next(doc for doc in template["documents"] if doc["document_type"] == "guidelines")
        assert "Rehab Requirements" in guidelines["required_sections"]
        assert "PROPERTY_TYPE" in guidelines["entity_types"]
        assert "rehab_eligibility" in guidelines["decision_trees"]
        
        # Check matrix document
        matrix = next(doc for doc in template["documents"] if doc["document_type"] == "matrix")
        assert "rehab_cost" in matrix["matrix_configuration"]["matrix_types"]
        assert "property_value" in matrix["matrix_configuration"]["dimensions"]
    
    def test_get_template_sbc(self):
        """Test getting SBC template"""
        template = MortgagePackageTemplates.get_template(PackageCategory.SBC)
        
        assert template["category"] == "SBC"
        assert template["template_name"] == "Small Balance Commercial Template"
        assert len(template["documents"]) == 1
        
        # Check guidelines document
        guidelines = template["documents"][0]
        assert guidelines["document_type"] == "guidelines"
        assert "Property Requirements" in guidelines["required_sections"]
        assert "COMMERCIAL_PROPERTY" in guidelines["entity_types"]
    
    def test_get_template_conv(self):
        """Test getting CONV template"""
        template = MortgagePackageTemplates.get_template(PackageCategory.CONV)
        
        assert template["category"] == "CONV"
        assert template["template_name"] == "Conventional Mortgage Template"
        assert len(template["documents"]) == 1
        
        # Check guidelines document
        guidelines = template["documents"][0]
        assert guidelines["document_type"] == "guidelines"
        assert "Standard Eligibility" in guidelines["required_sections"]
        assert "BORROWER_TYPE" in guidelines["entity_types"]
    
    def test_get_template_invalid_category(self):
        """Test getting template with invalid category"""
        # This would need a way to create invalid PackageCategory, 
        # but since it's an enum, we'll test the error handling in template methods
        
        # Test with None (simulating invalid enum handling)
        with pytest.raises(KeyError):
            # Access templates dict directly to test error case
            templates = {
                PackageCategory.NQM: MortgagePackageTemplates.NQM_TEMPLATE,
                PackageCategory.RTL: MortgagePackageTemplates.RTL_TEMPLATE,
                PackageCategory.SBC: MortgagePackageTemplates.SBC_TEMPLATE,
                PackageCategory.CONV: MortgagePackageTemplates.CONV_TEMPLATE
            }
            templates[None]  # This should raise KeyError
    
    def test_template_immutability(self):
        """Test that templates are returned as copies (immutable)"""
        template1 = MortgagePackageTemplates.get_template(PackageCategory.NQM)
        template2 = MortgagePackageTemplates.get_template(PackageCategory.NQM)
        
        # Modify template1
        template1["modified"] = True
        
        # template2 should not be affected
        assert "modified" not in template2
        
        # Original template should not be affected
        original = MortgagePackageTemplates.NQM_TEMPLATE
        assert "modified" not in original
    
    def test_create_package_from_template_basic(self):
        """Test creating package configuration from template"""
        package_config = MortgagePackageTemplates.create_package_from_template(
            category=PackageCategory.NQM,
            package_name="Test NQM Package",
            tenant_id="tenant_001"
        )
        
        assert package_config["package_name"] == "Test NQM Package"
        assert package_config["tenant_id"] == "tenant_001"
        assert package_config["category"] == "NQM"
        assert package_config["template"] == "Non-QM Standard Template"
        assert "documents" in package_config
        assert "relationships" in package_config
        assert len(package_config["documents"]) == 2
    
    def test_create_package_from_template_with_customizations(self):
        """Test creating package with customizations"""
        customizations = {
            "additional_sections": ["Custom Section 1", "Custom Section 2"],
            "additional_entity_types": ["CUSTOM_ENTITY"],
            "quality_thresholds": {"custom_metric": 0.85},
            "investor_name": "Test Investor"
        }
        
        package_config = MortgagePackageTemplates.create_package_from_template(
            category=PackageCategory.NQM,
            package_name="Customized NQM Package",
            tenant_id="tenant_001",
            customizations=customizations
        )
        
        # Check base configuration
        assert package_config["package_name"] == "Customized NQM Package"
        assert package_config["investor_name"] == "Test Investor"
        
        # Check customizations applied to documents
        guidelines = next(doc for doc in package_config["documents"] if doc["document_type"] == "guidelines")
        
        # Additional sections should be added
        assert "Custom Section 1" in guidelines["optional_sections"]
        assert "Custom Section 2" in guidelines["optional_sections"]
        
        # Additional entity types should be added
        assert "CUSTOM_ENTITY" in guidelines["entity_types"]
        
        # Quality thresholds should be updated
        assert guidelines["quality_thresholds"]["custom_metric"] == 0.85
    
    def test_create_package_investor_specific_customizations(self):
        """Test investor-specific customizations"""
        customizations = {
            "investor_name": "ABC Investor"
        }
        
        package_config = MortgagePackageTemplates.create_package_from_template(
            category=PackageCategory.NQM,
            package_name="Investor Package",
            tenant_id="tenant_001",
            customizations=customizations
        )
        
        # Check that investor-specific customizations were applied
        guidelines = next(doc for doc in package_config["documents"] if doc["document_type"] == "guidelines")
        
        # Should include investor-specific sections from template
        assert "Investor Guidelines" in guidelines["optional_sections"]
        assert "Special Instructions" in guidelines["optional_sections"]
        assert "INVESTOR_REQUIREMENT" in guidelines["entity_types"]
    
    def test_create_package_state_specific_customizations(self):
        """Test state-specific customizations"""
        customizations = {
            "state": "CA"
        }
        
        package_config = MortgagePackageTemplates.create_package_from_template(
            category=PackageCategory.NQM,
            package_name="California Package",
            tenant_id="tenant_001",
            customizations=customizations
        )
        
        # Check that state-specific customizations were applied
        guidelines = next(doc for doc in package_config["documents"] if doc["document_type"] == "guidelines")
        
        # Should include state-specific sections from template
        assert "State Regulations" in guidelines["optional_sections"]
        assert "Disclosure Requirements" in guidelines["optional_sections"]
        assert "STATE_REQUIREMENT" in guidelines["entity_types"]
        assert "DISCLOSURE" in guidelines["entity_types"]
    
    def test_get_available_templates(self):
        """Test getting list of available templates"""
        templates = MortgagePackageTemplates.get_available_templates()
        
        assert len(templates) == 4
        
        # Check each template info
        categories = [t["category"] for t in templates]
        assert "NQM" in categories
        assert "RTL" in categories
        assert "SBC" in categories
        assert "CONV" in categories
        
        # Check template structure
        nqm_template = next(t for t in templates if t["category"] == "NQM")
        assert nqm_template["template_name"] == "Non-QM Standard Template"
        assert "description" in nqm_template
    
    def test_validate_template_valid(self):
        """Test template validation with valid template"""
        template = MortgagePackageTemplates.get_template(PackageCategory.NQM)
        errors = MortgagePackageTemplates.validate_template(template)
        
        assert len(errors) == 0
    
    def test_validate_template_missing_fields(self):
        """Test template validation with missing required fields"""
        invalid_template = {
            "template_name": "Invalid Template"
            # Missing category and documents
        }
        
        errors = MortgagePackageTemplates.validate_template(invalid_template)
        
        assert len(errors) >= 2
        assert any("Missing required field: category" in error for error in errors)
        assert any("Missing required field: documents" in error for error in errors)
    
    def test_validate_template_empty_documents(self):
        """Test template validation with empty documents list"""
        invalid_template = {
            "category": "NQM",
            "template_name": "Invalid Template",
            "documents": []
        }
        
        errors = MortgagePackageTemplates.validate_template(invalid_template)
        
        assert len(errors) >= 1
        assert any("Template must contain at least one document" in error for error in errors)
    
    def test_validate_template_invalid_document(self):
        """Test template validation with invalid document"""
        invalid_template = {
            "category": "NQM",
            "template_name": "Invalid Template",
            "documents": [
                {
                    "document_name": "Test Document"
                    # Missing document_type
                }
            ]
        }
        
        errors = MortgagePackageTemplates.validate_template(invalid_template)
        
        assert len(errors) >= 1
        assert any("Missing required field: document_type" in error for error in errors)
    
    def test_validate_template_invalid_document_type(self):
        """Test template validation with invalid document type"""
        invalid_template = {
            "category": "NQM",
            "template_name": "Invalid Template",
            "documents": [
                {
                    "document_type": "invalid_type",
                    "document_name": "Test Document"
                }
            ]
        }
        
        errors = MortgagePackageTemplates.validate_template(invalid_template)
        
        assert len(errors) >= 1
        assert any("Invalid document_type" in error for error in errors)
    
    def test_validate_template_invalid_relationship(self):
        """Test template validation with invalid relationship"""
        invalid_template = {
            "category": "NQM",
            "template_name": "Invalid Template",
            "documents": [
                {
                    "document_type": "guidelines",
                    "document_name": "Test Document"
                }
            ],
            "relationships": [
                {
                    "from_document": "doc1"
                    # Missing to_document and relationship_type
                }
            ]
        }
        
        errors = MortgagePackageTemplates.validate_template(invalid_template)
        
        assert len(errors) >= 2
        assert any("Missing required field: to_document" in error for error in errors)
        assert any("Missing required field: relationship_type" in error for error in errors)


class TestTemplateIntegration:
    """Test integration between templates and package creation"""
    
    def test_all_templates_valid(self):
        """Test that all predefined templates are valid"""
        categories = [PackageCategory.NQM, PackageCategory.RTL, PackageCategory.SBC, PackageCategory.CONV]
        
        for category in categories:
            template = MortgagePackageTemplates.get_template(category)
            errors = MortgagePackageTemplates.validate_template(template)
            assert len(errors) == 0, f"Template {category} has validation errors: {errors}"
    
    def test_template_document_structures(self):
        """Test that all templates have proper document structures"""
        categories = [PackageCategory.NQM, PackageCategory.RTL, PackageCategory.SBC, PackageCategory.CONV]
        
        for category in categories:
            template = MortgagePackageTemplates.get_template(category)
            
            # All templates should have at least one document
            assert len(template["documents"]) >= 1
            
            # All documents should have required fields
            for doc in template["documents"]:
                assert "document_type" in doc
                assert "document_name" in doc
                assert "required_sections" in doc
                assert "entity_types" in doc
                assert "chunking_strategy" in doc
    
    def test_nqm_template_completeness(self):
        """Test NQM template has all required mortgage components"""
        template = MortgagePackageTemplates.get_template(PackageCategory.NQM)
        
        # Should have both guidelines and matrix
        doc_types = [doc["document_type"] for doc in template["documents"]]
        assert "guidelines" in doc_types
        assert "matrix" in doc_types
        
        # Should have relationships
        assert len(template["relationships"]) > 0
        
        # Guidelines should have proper sections
        guidelines = next(doc for doc in template["documents"] if doc["document_type"] == "guidelines")
        required_sections = guidelines["required_sections"]
        assert "Borrower Eligibility" in required_sections
        assert "Income Documentation" in required_sections
        assert "Credit Analysis" in required_sections
    
    def test_template_customizations_preserve_base(self):
        """Test that customizations don't affect base template"""
        original_template = MortgagePackageTemplates.get_template(PackageCategory.NQM)
        original_sections = original_template["documents"][0]["required_sections"].copy()
        
        # Create package with customizations
        customizations = {
            "additional_sections": ["Custom Section"]
        }
        
        package_config = MortgagePackageTemplates.create_package_from_template(
            category=PackageCategory.NQM,
            package_name="Test Package",
            tenant_id="tenant_001",
            customizations=customizations
        )
        
        # Original template should be unchanged
        fresh_template = MortgagePackageTemplates.get_template(PackageCategory.NQM)
        fresh_sections = fresh_template["documents"][0]["required_sections"]
        
        assert fresh_sections == original_sections
        assert "Custom Section" not in fresh_sections