#!/usr/bin/env python3
"""
Test script to validate enhanced chunking changes work with NAA-Guidelines.pdf
"""

import sys
import os
sys.path.append('.')

from src.enhanced_chunking import enhanced_pipeline
import fitz
from langchain.docstore.document import Document

def test_enhanced_chunking():
    """Test enhanced chunking with NAA-Guidelines.pdf"""
    
    print("=== TESTING ENHANCED CHUNKING CHANGES ===\n")
    
    # Check configuration
    print(f"✅ Configuration Updates:")
    print(f"   MAX_DOCUMENT_SIZE_FOR_HIERARCHICAL: {enhanced_pipeline.max_doc_size_hierarchical:,}")
    print(f"   MAX_PROCESSING_TIME_HIERARCHICAL: {enhanced_pipeline.max_processing_time}")
    
    # Test document type thresholds
    print(f"\n✅ Document Type Thresholds:")
    test_cases = [
        ("Guidelines document", "non-agency loan eligibility guidelines"),
        ("Matrix document", "pricing matrix rate sheet"),
        ("Procedure document", "underwriting procedure manual"),
        ("Unknown document", "some random document text")
    ]
    
    for doc_type, content in test_cases:
        threshold = enhanced_pipeline._get_document_type_threshold(content)
        print(f"   {doc_type}: {threshold:,} characters")
    
    # Test NAA-Guidelines.pdf if available
    pdf_path = 'merged_files/NAA-Guidelines.pdf'
    if os.path.exists(pdf_path):
        print(f"\n✅ Testing with NAA-Guidelines.pdf:")
        
        try:
            # Load PDF
            doc = fitz.open(pdf_path)
            page_count = doc.page_count
            print(f"   Pages: {page_count}")
            
            # Sample first few pages to avoid timeout
            sample_pages = []
            total_sample_chars = 0
            
            for i in range(min(5, page_count)):
                page = doc[i]
                text = page.get_text()
                sample_pages.append(Document(page_content=text, metadata={'page': i+1}))
                total_sample_chars += len(text)
            
            doc.close()
            
            # Estimate full document size
            estimated_size = total_sample_chars * (page_count / len(sample_pages))
            print(f"   Estimated size: {estimated_size:,.0f} characters")
            
            # Test type detection
            sample_content = '\n'.join([p.page_content for p in sample_pages])
            doc_threshold = enhanced_pipeline._get_document_type_threshold(sample_content)
            print(f"   Document type threshold: {doc_threshold:,}")
            
            # Test structure detection
            has_structure = enhanced_pipeline._detect_document_structure(sample_content)
            print(f"   Structure detected: {has_structure}")
            
            # Final assessment
            would_qualify = estimated_size <= doc_threshold and has_structure
            print(f"   Would use hierarchical chunking: {would_qualify}")
            
            if would_qualify:
                print(f"\n🎉 SUCCESS: NAA-Guidelines.pdf will now use enhanced chunking!")
            else:
                print(f"\n❌ ISSUE: Document still wouldn't qualify")
                
        except Exception as e:
            print(f"   Error testing PDF: {e}")
    else:
        print(f"\n⚠️  NAA-Guidelines.pdf not found at {pdf_path}")
    
    print(f"\n=== TEST COMPLETE ===")

if __name__ == "__main__":
    test_enhanced_chunking()