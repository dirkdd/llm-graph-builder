  Enhanced Chunking Pipeline Overview

  The enhanced chunking pipeline is a sophisticated, multi-stage system that processes mortgage documents (particularly guidelines) using hierarchical document
  understanding and LLM-powered analysis. Here's the complete flow:

  1. Package Processing Entry Point (package_manager.py:523-710)

  When a package containing guidelines is processed:
  - Package is created with 3-tier hierarchy: Category → Product → Program
  - Documents are associated at product or program level
  - Structural nodes (Category, Product, Program) are immediately created in Neo4j
  - Package metadata includes document types, chunking strategies, and validation rules

  2. Enhanced Chunking Decision (enhanced_chunking.py:63-84)

  The system determines whether to use hierarchical processing based on:
  - Document size (< 50,000 chars by default)
  - Document structure detection (looks for numbered sections, chapters, headers)
  - Processing time constraints (< 300 seconds)

  3. Stage 1: Navigation Structure Extraction (navigation_extractor.py)

  LLM Usage: Uses specialized prompts (guidelines_prompts.py:136-221) to extract:
  - Hierarchical navigation structure (Document → Chapter → Section → Subsection)
  - Section numbering and titles
  - Table of contents
  - Cross-references between sections
  - Decision tree entry points

  Output: NavigationStructure containing NavigationNode objects with hierarchy levels

  4. Stage 2: Hierarchical Semantic Chunking (semantic_chunker.py)

  Creates context-aware chunks that:
  - Respect document hierarchy boundaries
  - Maintain navigation breadcrumbs (navigation_path)
  - Classify chunk types (HEADER, CONTENT, DECISION, MATRIX)
  - Preserve section numbering and hierarchy levels
  - Calculate quality scores based on content coherence

  5. Stage 3: Mortgage-Specific Entity Extraction (guideline_entity_extractor.py)

  LLM Usage: Employs domain-specific prompts to extract:
  - Loan entities: Programs (NQM, RTL, SBC), borrower types, income types
  - Financial entities: Credit scores, DTI ratios, LTV limits, dollar amounts
  - Property entities: Property types, occupancy types, location requirements
  - Decision entities: Approval criteria, decline reasons, refer conditions
  - Process entities: Document requirements, validation rules

  Each entity includes:
  - Navigation context preservation
  - Confidence scores
  - Normalized values
  - Relationship mappings

  6. Stage 4: Relationship Detection (chunk_relationships.py)

  Builds relationships between:
  - Entities within same navigation context
  - Decision criteria and thresholds
  - Loan programs and requirements
  - Cross-referenced sections

  7. Stage 5: Quality Validation

  LLM Usage: Validation prompts (guidelines_prompts.py:415-472) check:
  - Navigation completeness
  - Decision tree completeness (all paths end with APPROVE/DECLINE/REFER)
  - Entity accuracy and domain compliance
  - Relationship consistency

  8. Stage 6: Storage and Integration

  Enhanced chunks are:
  - Converted to compatible format for existing pipeline
  - Stored with hierarchical metadata
  - Connected to package structure in Neo4j
  - Enriched with navigation context for retrieval

  LLM Usage Throughout Pipeline

  Navigation Extraction LLM Calls:

  # Specialized prompt for mortgage navigation
  navigation_prompt = create_navigation_prompt(
      content=document_content,
      document_type="guidelines",
      mortgage_category="NQM"  # or RTL, SBC, CONV
  )
  navigation_structure = llm.process(navigation_prompt)

  Entity Extraction LLM Calls:

  # Domain-aware entity extraction
  entity_prompt = create_entity_prompt(
      content=chunk_content,
      navigation_context=chunk.navigation_context
  )
  entities = llm.extract_entities(entity_prompt)

  Decision Tree LLM Calls:

  # Complete decision tree extraction with guaranteed outcomes
  decision_prompt = create_decision_prompt(
      content=section_content,
      navigation_context=section.navigation_path
  )
  decision_trees = llm.extract_decisions(decision_prompt)

  Guidelines Processing Specialization

  For guidelines documents specifically, the pipeline:

  1. Recognizes mortgage-specific patterns: Eligibility criteria, underwriting guidelines, approval matrices
  2. Preserves regulatory structure: Maintains exact section numbering and cross-references
  3. Extracts complete decision logic: Ensures every decision path has APPROVE/DECLINE/REFER outcomes
  4. Maps to package hierarchy: Links guidelines to specific products/programs in the 3-tier structure
  5. Validates mortgage compliance: Checks against industry standards and validation rules

  Performance and Fallback

  - Hierarchical processing: Used for structured documents < 50k chars
  - Basic fallback: Falls back to traditional chunking if hierarchical processing fails
  - Quality metrics: Tracks navigation coverage, entity completeness, relationship accuracy
  - Processing timeouts: Prevents long-running operations from blocking the pipeline

  This enhanced pipeline transforms raw mortgage guidelines into a rich, hierarchical knowledge graph while preserving document structure and extracting domain-specific     
   intelligence for better retrieval and decision support.