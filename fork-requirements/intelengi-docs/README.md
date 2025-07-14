# Document Processing System Requirements

## Overview

This documentation provides requirements and context for developing AI-powered document processing systems, with a focus on mortgage document analysis and knowledge graph construction. The documentation includes both legacy implementation patterns and guidance for new development approaches.

## 🎯 Purpose

This repository serves as a **requirements and context foundation** for new development teams working on document processing systems. It provides:

- ✅ **Reference Architecture**: Proven patterns from production implementations
- ✅ **Quality Benchmarks**: Performance standards and accuracy requirements  
- ✅ **Technical Context**: Domain-specific challenges and solutions
- ✅ **Development Freedom**: No constraints on tools, architectures, or approaches

## 📁 Repository Structure

```
intelengi-docs/
├── README.md                    # This overview and requirements
├── PROMPT_INDEX.md             # Quick reference to all prompts
├── 
├── legacy-approach/            # MGMS v2.0 reference implementation
│   ├── README.md              # Legacy approach overview
│   ├── LEGACY_TECHNICAL_SPECS.md  # Complete technical specifications
│   ├── stage1-extraction/     # Document extraction prompts
│   └── stage2-graph-construction/  # Graph construction prompts
├──
└── [new-development-docs]/     # Future: Your implementation docs
```

## 🚀 For New Development Teams

### What You Get
- **Proven Patterns**: Production-tested approaches that achieved 95%+ accuracy
- **Domain Knowledge**: Understanding of complex mortgage document requirements
- **Quality Standards**: Benchmarks for validation and performance
- **Technical Context**: Multi-tenant architecture and decision tree frameworks

### What You're NOT Constrained By
- **AI Models**: Use any provider (Claude, OpenAI, local models, etc.)
- **Architecture**: Single-stage, streaming, microservices, serverless, etc.
- **Databases**: Neo4j, PostgreSQL, MongoDB, vector DBs, or alternatives
- **Platforms**: Any deployment target or orchestration system
- **Output Formats**: JSON, XML, structured data, or custom formats

### Freedom to Innovate
- 🔄 **Different Processing Patterns**: Beyond the two-stage extraction → graph approach
- 🤖 **Alternative AI Approaches**: RAG, fine-tuning, agent frameworks, etc.
- 📊 **New Quality Frameworks**: Beyond schema validation to semantic validation
- 🏗️ **Modern Architectures**: Event-driven, real-time, or edge processing
- 📈 **Performance Trade-offs**: Speed vs accuracy optimization choices

## 📚 Legacy Reference: MGMS v2.0 Architecture

The legacy MGMS v2.0 system demonstrates one successful approach with a two-stage architecture:

- **Stage 1**: Document Extraction (Navigation & Entity Discovery) 
- **Stage 2**: Graph Construction (Neo4j Knowledge Graph Building)

**Document Types Processed:**
- **Guidelines**: Traditional mortgage guideline documents
- **Matrices**: Structured qualification matrices with decision trees

> **Note**: This represents the legacy approach. New implementations are free to use different architectures, processing stages, and document handling strategies.

## 🔍 Requirements and Standards

### Core Processing Requirements

**Document Analysis Capabilities:**
- Extract structured navigation from unstructured documents
- Identify and map complex decision trees with complete paths
- Handle multi-dimensional qualification matrices (FICO × LTV × DTI)
- Process both traditional policy documents and structured data tables

**Quality Standards:**
- **Accuracy**: 95%+ validation success rate
- **Completeness**: 100% decision tree coverage (no incomplete paths)
- **Performance**: Sub-10-minute processing per document
- **Consistency**: Repeatable results across document types

**Multi-Tenant Requirements:**
- Complete isolation between different mortgage categories
- Hierarchical organization for scalability
- Zero cross-contamination between tenant data
- Category-specific processing (NQM, SBC, RTL isolation)

### Decision Tree Framework Requirements

**Mandatory Structure for Mortgage Documents:**
```
ROOT Decision Points (1-3 per document)
├── BRANCH Criteria (5-15 per document)
│   ├── LEAF Outcome: APPROVE (final approval)
│   ├── LEAF Outcome: DECLINE (final decline)
│   └── TERMINAL Outcome: REFER (manual review)
```

**Required Outcomes:**
- **APPROVE**: When all qualification criteria are satisfied
- **DECLINE**: When minimum requirements are not met
- **REFER**: When manual underwriter review is needed

### Performance Benchmarks

**Processing Time Targets:**
- Document ingestion and validation: <30 seconds
- AI-powered extraction: <3 minutes per document  
- Graph construction: <10 minutes per document
- End-to-end pipeline: <15 minutes per document

**Scalability Requirements:**
- Concurrent processing: 100+ documents simultaneously
- Batch processing: Efficient handling of document sets
- Resource optimization: Minimize API calls and token usage
- Error recovery: Graceful handling of processing failures

## 📖 Legacy Implementation Details

For complete technical specifications of the proven MGMS v2.0 approach, see:

### 📁 Legacy Documentation
- **[Legacy Approach Overview](legacy-approach/README.md)** - High-level patterns and design decisions
- **[Legacy Technical Specs](legacy-approach/LEGACY_TECHNICAL_SPECS.md)** - Complete implementation details
- **[Prompt Index](PROMPT_INDEX.md)** - Quick reference to all system prompts

### 🔧 Legacy Stage 1: Document Extraction Prompts

The legacy implementation used 4 specialized prompts for different document types and processing stages:

1. **[Guidelines Navigation Extraction](legacy-approach/stage1-extraction/mgms-v2-guidelines-navigation-extraction.md)**
   - Extracts navigation structure and decision trees from policy documents
   - Creates ROOT → BRANCH → LEAF decision paths with mandatory outcomes

2. **[Guidelines Entity Discovery](legacy-approach/stage1-extraction/mgms-v2-guidelines-entity-discovery.md)**
   - Discovers mortgage entities and complete decision tree elements
   - Extracts loan programs, requirements, borrower types with relationships

3. **[Matrix Navigation Extraction](legacy-approach/stage1-extraction/mgms-v2-matrix-navigation-extraction.md)**
   - Processes qualification matrices with FICO/LTV/DTI criteria
   - Handles multi-dimensional analysis and tabular structures

4. **[Matrix Entity Discovery](legacy-approach/stage1-extraction/mgms-v2-matrix-entity-discovery.md)**
   - Extracts entities from matrix documents with decision tree elements
   - Processes range-based entities and qualification combinations

### 🔧 Legacy Stage 2: Graph Construction Prompts

The legacy implementation used 5 specialized prompts for Neo4j graph construction:

1. **[Guidelines Navigation Graph](legacy-approach/stage2-graph-construction/mgms-v2-guidelines-navigation-graph.md)**
   - Converts navigation data into Neo4j transaction batches
   - Creates hierarchical navigation graphs with proper relationships

2. **[Guidelines Entity Graph](legacy-approach/stage2-graph-construction/mgms-v2-guidelines-entity-graph.md)**
   - Transforms entity data into Neo4j graph structures
   - Implements advanced deduplication and semantic matching

3. **[Matrix Navigation Graph](legacy-approach/stage2-graph-construction/mgms-v2-matrix-navigation-graph.md)**
   - Builds matrix-specific graph structures with hierarchy
   - Handles matrix containment and cross-reference relationships

4. **[Matrix Entity Graph](legacy-approach/stage2-graph-construction/mgms-v2-matrix-entity-graph.md)**
   - Creates qualification criteria and threshold relationships
   - Maps matrix programs to defining criteria with proper isolation

5. **[Matrix Decision Trees](legacy-approach/stage2-graph-construction/mgms-v2-matrix-decision-trees.md)**
   - Builds traversable decision trees for underwriter guidance
   - Supports interactive querying and exception handling

## 🎯 Development Guidance

### Quality Standards to Meet or Exceed
- **95%+ Accuracy**: Validation success rate for extracted information
- **100% Decision Completeness**: All decision paths must have final outcomes
- **Sub-15 Minute Processing**: End-to-end document processing performance
- **Zero Cross-Contamination**: Multi-tenant isolation requirements

### Mortgage Domain Requirements
- **Decision Tree Framework**: ROOT → BRANCH → LEAF structure for qualification logic
- **Multi-Dimensional Analysis**: Handle FICO × LTV × DTI qualification matrices
- **Exception Handling**: Manual review pathways for complex scenarios
- **Category Isolation**: Separate processing for NQM, SBC, RTL mortgage types

### Architectural Considerations
- **Scalability**: Support for 100+ concurrent document processing
- **Error Recovery**: Graceful handling of processing failures
- **Quality Gates**: Validation checkpoints between processing stages
- **Resource Optimization**: Efficient use of AI tokens and API calls

## 🚀 Getting Started

1. **Review Requirements**: Start with the core processing requirements above
2. **Study Legacy Patterns**: Examine the [legacy approach](legacy-approach/README.md) for proven patterns
3. **Design Your Solution**: Choose your architecture, tools, and approaches
4. **Implement with Freedom**: Build using any technologies that meet the requirements
5. **Validate Quality**: Ensure your solution meets or exceeds the benchmarks

## 📞 Support and Context

This documentation provides the foundation for understanding mortgage document processing requirements. The legacy implementation demonstrates one successful approach, but new development teams are encouraged to innovate while maintaining the quality standards that ensure accurate, reliable document analysis.

---

**Remember**: The legacy prompts are provided as context and reference, not as constraints. Innovation and improvement are strongly encouraged as long as quality standards are maintained.