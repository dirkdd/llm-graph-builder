# Task 14: Create Guidelines Entity Extractor - READY

## Overview
**Estimated Time**: 3 hours  
**Priority**: High  
**Dependencies**: Task 12  
**Phase**: 1.3 Guidelines Navigation

## Description
Extract mortgage-specific entities with navigation context from guideline documents. This task implements contextual entity extraction that preserves hierarchical relationships and mortgage domain knowledge.

## Acceptance Criteria

### Core Implementation
- [ ] GuidelineEntityExtractor class with mortgage domain expertise
- [ ] extract_entities_with_context method with 7-step process
- [ ] extract_node_entities method with navigation integration
- [ ] Mortgage-specific entity patterns (100% domain coverage)
- [ ] Navigation context preservation throughout extraction
- [ ] Entity validation and quality metrics with validation rules
- [ ] Tests with various mortgage document types

### Technical Requirements
- [ ] Create `backend/src/guideline_entity_extractor.py`
- [ ] 10 mortgage-specific entity types: LOAN_PROGRAM, BORROWER_TYPE, NUMERIC_THRESHOLD, etc.
- [ ] Pattern-based and vocabulary-based entity extraction with regex and domain knowledge
- [ ] Navigation context preservation with source tracking and hierarchical relationships
- [ ] Entity validation and quality metrics with confidence scoring and numeric validation
- [ ] Comprehensive relationship building between extracted entities
- [ ] Complete test suite with mortgage document scenarios

### Entity Types
- [ ] **LOAN_PROGRAM**: FHA, VA, USDA, Conventional, etc.
- [ ] **BORROWER_TYPE**: First-time buyer, investor, primary residence, etc.
- [ ] **NUMERIC_THRESHOLD**: Credit scores, DTI ratios, LTV limits, etc.
- [ ] **INCOME_TYPE**: W-2, 1099, self-employed, rental, etc.
- [ ] **ASSET_TYPE**: Checking, savings, retirement, gift funds, etc.
- [ ] **PROPERTY_TYPE**: Single family, condo, townhome, multi-unit, etc.
- [ ] **DOCUMENTATION_TYPE**: Full doc, bank statements, asset depletion, etc.
- [ ] **OCCUPANCY_TYPE**: Primary, secondary, investment property
- [ ] **CREDIT_EVENT**: Bankruptcy, foreclosure, short sale, etc.
- [ ] **GUIDELINE_SECTION**: Policy references and section numbers

### Validation Requirements
- [ ] Entity validation with domain-specific rules
- [ ] Quality metrics and confidence scoring
- [ ] Navigation context preservation and tracking
- [ ] Relationship building between related entities
- [ ] Numeric threshold validation and range checking

## Files to Create
- `backend/src/guideline_entity_extractor.py` - Complete implementation
- `backend/tests/test_guideline_entity_extractor.py` - Comprehensive test suite
- `backend/validate_task_14.py` - Validation script

## Success Metrics
- All acceptance criteria must pass validation
- 100% mortgage domain coverage for entity types
- Navigation context preserved for all extracted entities
- Entity relationships properly established and validated
- Performance meets standards for large guideline documents

## Integration Points
- Uses NavigationGraphBuilder from Task 12
- Integrates with decision tree structures from Task 13
- Provides foundation for enhanced processing prompts (Task 16)
- Enables comprehensive mortgage knowledge extraction

## Domain Expertise Requirements
- Deep understanding of mortgage lending terminology
- Knowledge of regulatory compliance requirements
- Familiarity with loan origination processes
- Understanding of risk assessment criteria