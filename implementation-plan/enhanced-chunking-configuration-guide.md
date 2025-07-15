# Enhanced Chunking Configuration and Troubleshooting Guide

**Last Updated**: July 15, 2025  
**Version**: 1.0

## Overview

This guide provides comprehensive documentation for the Enhanced Chunking system in the LLM Graph Builder, including configuration options, troubleshooting procedures, and optimization strategies.

## Table of Contents

1. [Configuration Overview](#configuration-overview)
2. [Document Type Thresholds](#document-type-thresholds)
3. [Structure Detection Patterns](#structure-detection-patterns)
4. [Troubleshooting Common Issues](#troubleshooting-common-issues)
5. [Performance Optimization](#performance-optimization)
6. [Monitoring and Debugging](#monitoring-and-debugging)
7. [Future Considerations](#future-considerations)

## Configuration Overview

### Environment Variables

The Enhanced Chunking system is configured through environment variables that control processing behavior:

```bash
# Core Configuration
ENABLE_HIERARCHICAL_CHUNKING=true              # Enable/disable enhanced chunking
ENABLE_RELATIONSHIP_DETECTION=true             # Enable entity relationship detection
MAX_DOCUMENT_SIZE_FOR_HIERARCHICAL=600000      # Global size threshold (characters)
MAX_PROCESSING_TIME_HIERARCHICAL=900           # Timeout in seconds (15 minutes)

# Quality Thresholds
MIN_RELATIONSHIP_STRENGTH=0.3                  # Minimum relationship confidence
MIN_EVIDENCE_CONFIDENCE=0.5                    # Minimum evidence confidence
```

### Key Configuration Changes (July 2025)

**Critical Update**: Size thresholds have been significantly increased to support real-world mortgage documents:

- **Previous**: 50,000 characters maximum
- **Current**: 600,000 characters maximum (12x increase)
- **Rationale**: Mortgage guidelines typically contain 100-500 pages (~500k-600k characters)

## Document Type Thresholds

The system applies different size thresholds based on document content analysis:

### Threshold Matrix

| Document Type | Size Threshold | Typical Page Count | Examples |
|---------------|----------------|-------------------|----------|
| **Guidelines** | 600,000 chars | 100-500 pages | Eligibility guidelines, underwriting policies |
| **Matrix** | 300,000 chars | 50-150 pages | Pricing matrices, rate sheets |
| **Procedures** | 200,000 chars | 20-100 pages | Process workflows, manuals |
| **Default** | 600,000 chars | Variable | All other document types |

### Content Detection Keywords

The system detects document types using these keyword patterns:

```python
# Guidelines Documents
guidelines_keywords = [
    'guidelines', 'eligibility', 'underwriting', 
    'policy manual', 'lending policy'
]

# Matrix Documents  
matrix_keywords = [
    'matrix', 'pricing', 'rate sheet', 'pricing sheet'
]

# Procedure Documents
procedure_keywords = [
    'procedure', 'process', 'workflow', 'manual'
]
```

## Structure Detection Patterns

### Enhanced Pattern Set (Updated July 2025)

The structure detection system uses enhanced regex patterns optimized for mortgage documents:

#### Core Patterns (Original)
```regex
^\s*\d+\.\s+[A-Z]                    # Numbered sections (1. SECTION)
^\s*CHAPTER\s+\d+                    # Chapter headings
^\s*Section\s+\d+                    # Section headings
^\s*\d+\.\d+\s+                      # Subsection numbering (1.1, 2.3)
^\s*[A-Z]{2,}\s*$                    # All caps headings
```

#### Mortgage-Specific Patterns (New)
```regex
^\s*\d+\.\d+\.\d+\s+                 # Three-level numbering (11.8.17)
^\s*\d+\s+[A-Z][A-Z\s&/\-]+[A-Z]$   # Spaced major sections (2   GENERAL PROGRAM)
^\s*\d+\.\d+\s+[A-Z][A-Z\s&/\-]+[A-Z]$ # Subsection headers (2.1 LOAN PROGRAMS)
^\s*PART\s+[IVX]+                    # Roman numeral parts
^\s*APPENDIX\s+[A-Z]                 # Appendices
^\s*[A-Z]{3,}(\s+[A-Z]{3,})*\s*$    # Enhanced all caps (3+ char words)
^\s*\d+\s+[A-Z][A-Z\s]+$            # Simple major sections (1   LENDING POLICY)
```

### Dynamic Threshold Logic

The system uses dynamic thresholds based on document size:

```python
def calculate_structure_threshold(total_lines: int) -> int:
    if total_lines > 1000:      # Large documents (guidelines)
        return max(5, min(15, total_lines // 100))
    elif total_lines > 500:     # Medium documents  
        return max(3, min(8, total_lines // 50))
    else:                       # Small documents
        return 3
```

### Structure Detection Algorithm

1. **Content Analysis**: Extract first 200 lines (increased from 100)
2. **Pattern Matching**: Apply all regex patterns to each line
3. **Count Indicators**: Sum unique pattern matches
4. **Dynamic Threshold**: Calculate threshold based on document size
5. **Decision**: Compare indicators found vs. threshold required

## Troubleshooting Common Issues

### Issue 1: Large Documents Still Using Basic Chunking

**Symptoms**:
- Guidelines documents (>100 pages) fall back to basic chunking
- Log shows "Document size exceeds threshold"

**Diagnosis**:
```bash
# Check current configuration
python3 -c "from src.enhanced_chunking import MAX_DOCUMENT_SIZE_FOR_HIERARCHICAL; print(f'Threshold: {MAX_DOCUMENT_SIZE_FOR_HIERARCHICAL:,}')"

# Test document size
python3 -c "
import fitz
doc = fitz.open('path/to/document.pdf')
total_chars = sum(len(doc[i].get_text()) for i in range(doc.page_count))
print(f'Document size: {total_chars:,} characters')
doc.close()
"
```

**Solutions**:
1. **Increase Global Threshold**:
   ```bash
   export MAX_DOCUMENT_SIZE_FOR_HIERARCHICAL=800000
   ```

2. **Verify Document Type Detection**:
   ```python
   from src.enhanced_chunking import enhanced_pipeline
   content = "sample document content..."
   threshold = enhanced_pipeline._get_document_type_threshold(content)
   print(f"Detected threshold: {threshold:,}")
   ```

### Issue 2: Structure Not Detected in Well-Structured Documents

**Symptoms**:
- Document has clear sections but structure detection fails
- Log shows "No clear document structure detected"

**Diagnosis**:
```python
# Test structure detection manually
from src.enhanced_chunking import enhanced_pipeline
content = "your document content..."
structure_found = enhanced_pipeline._detect_document_structure(content)
print(f"Structure detected: {structure_found}")
```

**Solutions**:
1. **Check Pattern Matching**:
   ```python
   import re
   
   # Test specific patterns
   test_content = """
   1   LENDING POLICY
   1.1 LOAN APPROVAL & ELIGIBILITY PHILOSOPHY
   1.2 FAIR LENDING STATEMENT
   """
   
   patterns = [
       r'^\s*\d+\s+[A-Z][A-Z\s]+$',              # Major sections
       r'^\s*\d+\.\d+\s+[A-Z][A-Z\s&/\-]+[A-Z]$' # Subsections
   ]
   
   for line in test_content.split('\n'):
       line = line.strip()
       for i, pattern in enumerate(patterns):
           if re.search(pattern, line):
               print(f"Pattern {i} matched: {line}")
   ```

2. **Lower Structure Threshold Temporarily**:
   ```python
   # In enhanced_chunking.py, modify temporarily for testing
   return structure_count >= 1  # Instead of dynamic threshold
   ```

### Issue 3: Processing Timeouts

**Symptoms**:
- Large documents timeout during processing
- Error: "Hierarchical processing took X seconds, exceeding threshold"

**Solutions**:
1. **Increase Processing Timeout**:
   ```bash
   export MAX_PROCESSING_TIME_HIERARCHICAL=1800  # 30 minutes
   ```

2. **Process in Batches**:
   ```python
   # Split large documents into sections for processing
   # This may require custom implementation
   ```

### Issue 4: Memory Issues with Large Documents

**Symptoms**:
- Out of memory errors
- Process killed during large document processing

**Solutions**:
1. **Implement Streaming Processing**:
   ```python
   # Process documents in chunks rather than loading entirely
   # This is a future enhancement
   ```

2. **Increase System Resources**:
   ```bash
   # Adjust Docker memory limits or system allocation
   ```

## Performance Optimization

### Monitoring Performance

Track these key metrics for optimal performance:

```python
# Key metrics to monitor
metrics = {
    'document_size': 'Character count of input document',
    'structure_indicators_found': 'Number of pattern matches',
    'structure_threshold': 'Required threshold for document size',
    'processing_time': 'Total hierarchical processing time',
    'chunk_count': 'Number of chunks created',
    'entity_count': 'Number of entities extracted',
    'relationship_count': 'Number of relationships detected'
}
```

### Optimization Strategies

1. **Document Size Optimization**:
   - Pre-process documents to remove unnecessary content
   - Split extremely large documents (>1M characters) if possible

2. **Pattern Optimization**:
   - Add document-specific patterns for better structure detection
   - Monitor false positives and refine regex patterns

3. **Processing Optimization**:
   - Use parallel processing for independent operations
   - Implement caching for repeated operations

## Monitoring and Debugging

### Logging Configuration

Enable detailed logging for enhanced chunking:

```python
import logging

# Set debug level for enhanced chunking
logging.getLogger('src.enhanced_chunking').setLevel(logging.DEBUG)
logging.getLogger('src.navigation_extractor').setLevel(logging.DEBUG)
logging.getLogger('src.semantic_chunker').setLevel(logging.DEBUG)
```

### Debug Output Examples

**Successful Processing**:
```
INFO - Document qualifies for hierarchical chunking: size=557911, threshold=600000, structured=True
INFO - Structure detection: 57 indicators found, threshold: 5, total_lines: 3142, result: True
INFO - Hierarchical chunking completed in 45.23s, created 342 chunks
INFO - Relationship detection completed in 12.34s, found 178 relationships
```

**Failed Processing**:
```
INFO - Document size 758912 exceeds type-specific threshold 600000, using basic chunking
INFO - Structure detection: 2 indicators found, threshold: 8, total_lines: 1823, result: False
WARNING - Hierarchical processing took 920.45s, exceeding threshold 900s
```

### Validation Scripts

Use the provided validation script to test configuration:

```bash
# Run validation script
python3 test_enhanced_chunking_changes.py

# Expected output for working configuration:
# ✅ Configuration Updates: MAX_DOCUMENT_SIZE_FOR_HIERARCHICAL: 600,000
# ✅ Document Type Thresholds: Guidelines document: 600,000 characters
# 🎉 SUCCESS: NAA-Guidelines.pdf will now use enhanced chunking!
```

## Future Considerations

### Planned Enhancements

1. **Adaptive Thresholds**: Dynamic thresholds based on document complexity
2. **Streaming Processing**: Process very large documents without full memory loading
3. **ML-Based Structure Detection**: Replace regex patterns with trained models
4. **Document Type Classification**: Automatic classification using NLP models
5. **Performance Auto-Tuning**: Automatic optimization based on processing metrics

### Configuration Migration

When upgrading the system:

1. **Backup Current Configuration**:
   ```bash
   # Save current environment variables
   env | grep HIERARCHICAL > enhanced_chunking_backup.env
   ```

2. **Test with Sample Documents**:
   ```bash
   # Test new configuration with known documents
   python3 test_enhanced_chunking_changes.py
   ```

3. **Monitor Performance Metrics**:
   - Processing success rates
   - Average processing times
   - Memory usage patterns
   - Error frequencies

### Troubleshooting Checklist

Before reporting issues, verify:

- [ ] Environment variables are correctly set
- [ ] Document size is within configured thresholds
- [ ] Document contains detectable structure patterns
- [ ] Sufficient system resources are available
- [ ] Log files show detailed processing information
- [ ] Validation script passes successfully

### Support Resources

1. **Configuration Files**: `src/enhanced_chunking.py`
2. **Test Scripts**: `test_enhanced_chunking_changes.py`
3. **Documentation**: `implementation-plan/technical-specs/02-processing-pipeline.md`
4. **Issue Tracking**: Create issues with full debug logs and document samples

---

**Document Maintenance**: This guide should be updated whenever configuration parameters or processing logic changes. Include timestamps and version information for all updates.