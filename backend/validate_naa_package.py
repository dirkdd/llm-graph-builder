#!/usr/bin/env python3
# Quick validation of real-world NQM NAA package structure

from pathlib import Path

def validate_naa_package():
    """Validate the real NQM NAA package structure"""
    sample_path = Path("/mnt/c/Users/dirkd/OneDrive/Documents/GitHub/llm-graph-builder/implementation-plan/sample-documents")
    nqm_naa_path = sample_path / "NQM" / "NAA"
    
    print("🔍 Validating NQM NAA Package Structure...")
    
    # Check main directories
    if not nqm_naa_path.exists():
        print("❌ NQM NAA package directory not found")
        return False
    
    guidelines_path = nqm_naa_path / "guidelines"
    matrices_path = nqm_naa_path / "matrices"
    
    if not guidelines_path.exists():
        print("❌ Guidelines directory not found")
        return False
        
    if not matrices_path.exists():
        print("❌ Matrices directory not found") 
        return False
    
    # Check for files
    guideline_files = list(guidelines_path.glob("*.pdf"))
    matrix_files = list(matrices_path.glob("*.pdf"))
    
    print(f"✅ Found guidelines directory with {len(guideline_files)} PDF files")
    for file in guideline_files:
        print(f"   - {file.name}")
    
    print(f"✅ Found matrices directory with {len(matrix_files)} PDF files")
    for file in matrix_files:
        print(f"   - {file.name}")
    
    # Check for expected patterns
    expected_matrices = [
        "Cash Flow Advantage",
        "Investor Advantage", 
        "Non-Agency Advantage",
        "Professional Investor",
        "Titanium Advantage"
    ]
    
    detected_patterns = []
    for pattern in expected_matrices:
        matching_files = [f.name for f in matrix_files if pattern in f.name]
        if matching_files:
            detected_patterns.append(pattern)
            print(f"✅ Found {pattern} matrix: {matching_files[0]}")
    
    print(f"\n📊 Package Structure Summary:")
    print(f"   - Guidelines: {len(guideline_files)} files")
    print(f"   - Matrices: {len(matrix_files)} files")
    print(f"   - Matrix Types: {len(detected_patterns)}/{len(expected_matrices)} detected")
    
    if len(guideline_files) > 0 and len(matrix_files) > 0:
        print("\n🎉 Real-world NQM NAA package structure validated successfully!")
        print("📋 This structure is perfect for testing our navigation extractor and semantic chunker!")
        return True
    else:
        print("\n❌ Package structure validation failed")
        return False

if __name__ == "__main__":
    validate_naa_package()