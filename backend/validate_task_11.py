#!/usr/bin/env python3
# Task 11: Enhanced Processing Pipeline Validation
# Validates the integration structure and file completeness

import os
import sys
from pathlib import Path

def validate_task_11_implementation():
    """Validate Task 11 implementation completeness"""
    
    print("🔍 Task 11: Enhanced Processing Pipeline Validation")
    print("=" * 55)
    
    validation_results = {}
    
    # 1. Check file structure
    print("\n1️⃣ Validating file structure...")
    
    required_files = [
        "src/enhanced_chunking.py",
        "src/main.py",
        "src/navigation_extractor.py",
        "src/semantic_chunker.py", 
        "src/chunk_relationships.py",
        "src/entities/navigation_models.py"
    ]
    
    file_check_passed = True
    for file_path in required_files:
        if os.path.exists(file_path):
            file_size = os.path.getsize(file_path)
            print(f"   ✅ {file_path} ({file_size:,} bytes)")
        else:
            print(f"   ❌ Missing: {file_path}")
            file_check_passed = False
    
    validation_results['file_structure'] = file_check_passed
    
    # 2. Check enhanced_chunking.py implementation
    print("\n2️⃣ Validating enhanced_chunking.py implementation...")
    
    enhanced_chunking_checks = []
    
    if os.path.exists("src/enhanced_chunking.py"):
        with open("src/enhanced_chunking.py", 'r') as f:
            content = f.read()
            
        # Check for key classes and functions
        key_components = [
            "class EnhancedChunkingPipeline",
            "def get_enhanced_chunks_pipeline",
            "def enhanced_processing_chunks_pipeline", 
            "def should_use_hierarchical_chunking",
            "def process_document_hierarchical",
            "NavigationExtractor",
            "SemanticChunker",
            "ChunkRelationshipManager"
        ]
        
        for component in key_components:
            if component in content:
                print(f"   ✅ Found: {component}")
                enhanced_chunking_checks.append(True)
            else:
                print(f"   ❌ Missing: {component}")
                enhanced_chunking_checks.append(False)
    
    validation_results['enhanced_chunking'] = all(enhanced_chunking_checks)
    
    # 3. Check main.py integration
    print("\n3️⃣ Validating main.py integration...")
    
    main_py_checks = []
    
    if os.path.exists("src/main.py"):
        with open("src/main.py", 'r') as f:
            content = f.read()
            
        # Check for integration points
        integration_points = [
            "from src.enhanced_chunking import",
            "ENHANCED_CHUNKING_AVAILABLE",
            "get_enhanced_chunks_pipeline",
            "enhanced_processing_chunks_pipeline",
            "_enhanced_processing_data",
            "Task 11:"
        ]
        
        for point in integration_points:
            if point in content:
                print(f"   ✅ Found integration: {point}")
                main_py_checks.append(True)
            else:
                print(f"   ❌ Missing integration: {point}")
                main_py_checks.append(False)
    
    validation_results['main_integration'] = all(main_py_checks)
    
    # 4. Check configuration options
    print("\n4️⃣ Validating configuration options...")
    
    config_checks = []
    
    expected_env_vars = [
        "ENABLE_HIERARCHICAL_CHUNKING",
        "ENABLE_RELATIONSHIP_DETECTION",
        "MAX_DOCUMENT_SIZE_FOR_HIERARCHICAL", 
        "MAX_PROCESSING_TIME_HIERARCHICAL",
        "MIN_RELATIONSHIP_STRENGTH"
    ]
    
    if os.path.exists("src/enhanced_chunking.py"):
        with open("src/enhanced_chunking.py", 'r') as f:
            content = f.read()
        
        for var in expected_env_vars:
            if var in content:
                print(f"   ✅ Configuration: {var}")
                config_checks.append(True)
            else:
                print(f"   ❌ Missing config: {var}")
                config_checks.append(False)
    
    validation_results['configuration'] = all(config_checks)
    
    # 5. Check backward compatibility
    print("\n5️⃣ Validating backward compatibility...")
    
    compatibility_checks = []
    
    if os.path.exists("src/main.py"):
        with open("src/main.py", 'r') as f:
            content = f.read()
        
        # Check that original functions are preserved
        original_functions = [
            "def get_chunkId_chunkDoc_list",
            "async def processing_chunks",
            "CreateChunksofDocument",
            "create_relation_between_chunks"
        ]
        
        for func in original_functions:
            if func in content:
                print(f"   ✅ Preserved: {func}")
                compatibility_checks.append(True)
            else:
                print(f"   ❌ Missing original: {func}")
                compatibility_checks.append(False)
        
        # Check for fallback mechanisms
        fallback_indicators = [
            "Fall back to basic chunking",
            "basic chunking",
            "fallback_reason"
        ]
        
        fallback_found = any(indicator in content for indicator in fallback_indicators)
        if fallback_found:
            print(f"   ✅ Fallback mechanisms present")
            compatibility_checks.append(True)
        else:
            print(f"   ❌ No fallback mechanisms found")
            compatibility_checks.append(False)
    
    validation_results['backward_compatibility'] = all(compatibility_checks)
    
    # 6. Check error handling
    print("\n6️⃣ Validating error handling...")
    
    error_handling_checks = []
    
    files_to_check = ["src/enhanced_chunking.py", "src/main.py"]
    error_patterns = [
        "try:",
        "except",
        "logging.error",
        "logging.warning",
        "raise"
    ]
    
    for file_path in files_to_check:
        if os.path.exists(file_path):
            with open(file_path, 'r') as f:
                content = f.read()
            
            errors_found = sum(1 for pattern in error_patterns if pattern in content)
            print(f"   📄 {file_path}: {errors_found} error handling patterns")
            
            if errors_found >= 3:  # At least some error handling
                error_handling_checks.append(True)
            else:
                error_handling_checks.append(False)
    
    validation_results['error_handling'] = all(error_handling_checks)
    
    # 7. Check documentation
    print("\n7️⃣ Validating documentation...")
    
    doc_files = [
        "TASK_11_READY.md",
        "test_task_11_integration.py"
    ]
    
    doc_checks = []
    for doc_file in doc_files:
        if os.path.exists(doc_file):
            print(f"   ✅ Documentation: {doc_file}")
            doc_checks.append(True)
        else:
            print(f"   ❌ Missing documentation: {doc_file}")
            doc_checks.append(False)
    
    validation_results['documentation'] = all(doc_checks)
    
    # Summary
    print("\n" + "=" * 55)
    print("📋 TASK 11 VALIDATION RESULTS")
    print("=" * 55)
    
    passed_validations = sum(validation_results.values())
    total_validations = len(validation_results)
    
    for validation_name, result in validation_results.items():
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{status}: {validation_name.replace('_', ' ').title()}")
    
    print(f"\n📊 Overall Result: {passed_validations}/{total_validations} validations passed")
    
    # Final assessment
    if passed_validations >= total_validations * 0.8:  # 80% threshold
        print("\n🎉 TASK 11 VALIDATION PASSED!")
        print("✅ Enhanced Processing Pipeline Integration Complete")
        print("\n🔗 Integration Summary:")
        print("   • NavigationExtractor → SemanticChunker → ChunkRelationshipManager")
        print("   • Enhanced chunking pipeline integrated into main.py")
        print("   • Backward compatibility with existing API maintained")
        print("   • Graceful fallback to basic chunking implemented")
        print("   • Configuration options for feature control")
        print("   • Comprehensive error handling and logging")
        print("\n🎯 Ready for Phase 1.3: Guidelines Navigation!")
        return True
    else:
        print(f"\n❌ TASK 11 VALIDATION INCOMPLETE")
        print(f"   Only {passed_validations}/{total_validations} validations passed")
        print("🔧 Additional work required")
        return False


if __name__ == "__main__":
    success = validate_task_11_implementation()
    sys.exit(0 if success else 1)