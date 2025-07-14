# System Prompts Quick Reference Index

## Overview

This directory contains documentation for AI-powered document processing systems, with legacy MGMS v2.0 prompts as reference examples. These materials provide context and proven patterns for new development without constraining implementation approaches.

## Directory Structure

```
intelengi-docs/
├── README.md                              # Requirements and overview
├── PROMPT_INDEX.md                        # This quick reference
├── DEVELOPMENT_FREEDOM_GUIDELINES.md      # Innovation guidance
├── legacy-approach/                       # MGMS v2.0 reference implementation
│   ├── README.md                         # Legacy approach overview
│   ├── LEGACY_TECHNICAL_SPECS.md         # Complete technical specs
│   ├── stage1-extraction/                # Document extraction prompts
│   │   ├── mgms-v2-guidelines-navigation-extraction.md
│   │   ├── mgms-v2-guidelines-entity-discovery.md
│   │   ├── mgms-v2-matrix-navigation-extraction.md
│   │   └── mgms-v2-matrix-entity-discovery.md
│   └── stage2-graph-construction/         # Graph construction prompts
│       ├── mgms-v2-guidelines-navigation-graph.md
│       ├── mgms-v2-guidelines-entity-graph.md
│       ├── mgms-v2-matrix-navigation-graph.md
│       ├── mgms-v2-matrix-entity-graph.md
│       └── mgms-v2-matrix-decision-trees.md
```

## 🔍 Quick Reference Guide

### For New Development Teams
1. **Start Here**: [README.md](README.md) - Requirements and development guidance
2. **Design Freedom**: [DEVELOPMENT_FREEDOM_GUIDELINES.md](DEVELOPMENT_FREEDOM_GUIDELINES.md) - Innovation opportunities
3. **Legacy Context**: [legacy-approach/README.md](legacy-approach/README.md) - Proven patterns and benchmarks

### For Technical Implementation
- **Complete Technical Specs**: [legacy-approach/LEGACY_TECHNICAL_SPECS.md](legacy-approach/LEGACY_TECHNICAL_SPECS.md)
- **Individual Prompts**: See legacy-approach directories for specific prompt files

## 📚 Legacy MGMS v2.0 Prompts (Reference Only)

### Stage 1: Document Extraction (4 Prompts)

**Guidelines Processing:**
- **[Navigation Extraction](legacy-approach/stage1-extraction/mgms-v2-guidelines-navigation-extraction.md)** - Extract navigation structure and decision trees from policy documents
- **[Entity Discovery](legacy-approach/stage1-extraction/mgms-v2-guidelines-entity-discovery.md)** - Discover mortgage entities and decision tree elements

**Matrix Processing:**
- **[Matrix Navigation](legacy-approach/stage1-extraction/mgms-v2-matrix-navigation-extraction.md)** - Process qualification matrices with FICO/LTV/DTI criteria
- **[Matrix Entities](legacy-approach/stage1-extraction/mgms-v2-matrix-entity-discovery.md)** - Extract entities from matrix documents with decision trees

### Stage 2: Graph Construction (5 Prompts)

**Guidelines Graph Construction:**
- **[Navigation Graph](legacy-approach/stage2-graph-construction/mgms-v2-guidelines-navigation-graph.md)** - Convert navigation data into Neo4j transaction batches
- **[Entity Graph](legacy-approach/stage2-graph-construction/mgms-v2-guidelines-entity-graph.md)** - Transform entity data into Neo4j graph structures

**Matrix Graph Construction:**
- **[Matrix Navigation Graph](legacy-approach/stage2-graph-construction/mgms-v2-matrix-navigation-graph.md)** - Build matrix-specific graph structures with hierarchy
- **[Matrix Entity Graph](legacy-approach/stage2-graph-construction/mgms-v2-matrix-entity-graph.md)** - Create qualification criteria and threshold relationships
- **[Matrix Decision Trees](legacy-approach/stage2-graph-construction/mgms-v2-matrix-decision-trees.md)** - Build traversable decision trees for underwriter guidance

## 🎯 Legacy Implementation Patterns (Reference)

### Key Technical Achievements
- **95%+ Accuracy**: Production-validated success rates
- **100% Decision Completeness**: Complete ROOT → BRANCH → LEAF paths
- **Multi-Tenant Isolation**: Zero cross-contamination between categories
- **Sub-10 Minute Processing**: Performance benchmarks achieved

### Decision Tree Framework Pattern
```
ROOT Decision Points (1-3 per document, precedence 1-5)
├── BRANCH Criteria (5-15 per document, precedence 6-89)
│   ├── LEAF Outcome: APPROVE (precedence 90-99)
│   ├── LEAF Outcome: DECLINE (precedence 90-99)
│   └── TERMINAL Outcome: REFER (precedence 90-99)
```

### Multi-Tenant Architecture Pattern
- **ID Format**: `{tenant}_{category}_{product}_{type}_{sequence}`
- **Categories**: NQM, SBC, RTL with complete isolation
- **Example**: `the_g1_group_NQM_naa_nav_001`

### Processing Pipeline Pattern
```
Document Input → Category Validation → Parallel Extraction (1A+1B) → 
Quality Gates → Graph Construction (2A+2B+2C) → Neo4j Deployment
```

## 🚀 For New Development

### What to Study
- **Quality Standards**: 95%+ accuracy benchmarks to meet or exceed
- **Decision Framework**: Complete decision tree requirements
- **Multi-Tenant Patterns**: Category isolation strategies
- **Performance Targets**: Sub-15 minute processing goals

### What NOT to Copy
- **Technology Stack**: Use any AI models, databases, platforms
- **Architecture**: Single-stage, streaming, or alternative patterns
- **Processing Flow**: Event-driven, real-time, or custom workflows
- **Output Format**: JSON, XML, APIs, or custom structures

## 📞 Quick Start for New Teams

1. **Understand Requirements**: Review [README.md](README.md) for quality standards
2. **Study Proven Patterns**: Examine [legacy-approach/](legacy-approach/) for context
3. **Design Your Solution**: Use [DEVELOPMENT_FREEDOM_GUIDELINES.md](DEVELOPMENT_FREEDOM_GUIDELINES.md) for innovation guidance
4. **Build with Confidence**: Implement using your preferred technologies and approaches

---

## 💡 Remember

> **These legacy prompts demonstrate one successful path, not the only path.**
> 
> Use them as context and inspiration, not as implementation requirements. The goal is building systems that meet or exceed the quality standards, regardless of the approach taken.

**Innovation encouraged. Quality required.**