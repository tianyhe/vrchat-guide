"""Test dependencies and imports for the VRChat Guide project."""

import sys
import importlib
from typing import List, Dict
from dataclasses import dataclass

@dataclass
class DependencyTest:
    category: str
    modules: List[str]
    optional: bool = False

def test_import(module_name: str) -> bool:
    """Test importing a single module."""
    try:
        importlib.import_module(module_name)
        print(f"✓ Successfully imported {module_name}")
        return True
    except ImportError as e:
        print(f"✗ Failed to import {module_name}: {str(e)}")
        return False

def run_dependency_tests() -> Dict[str, Dict[str, bool]]:
    """Run all dependency tests and return results."""
    
    # Define test cases
    test_cases = [
        # Core Genie Worksheets Dependencies
        DependencyTest("Core Genie", [
            "worksheets.agent",
            "worksheets.knowledge",
            "worksheets.environment",
            "worksheets.llm",
        ]),
        
        # Core Data Processing
        DependencyTest("Data Processing", [
            "pandas",
            "numpy",
            "sympy",
            "pydantic",
            "yaml",
            "toml",
        ]),
        
        # Database and Knowledge Base
        DependencyTest("Database", [
            "psycopg2",
            "sql_metadata",
            "pymongo",
        ]),

        # SUQL Dependencies
        DependencyTest("SUQL", [
            "suql",
        ]),
        
        # LangChain and API
        DependencyTest("API Integration", [
            "langchain_openai",
            "langchain_together",
            "google.auth",
            "googleapiclient",
        ]),
        
        # Web Interface (Optional)
        DependencyTest("Web Interface", [
            "chainlit",
        ], optional=True),
        
        # Voice Processing (Optional)
        DependencyTest("Voice Processing", [
            "deepgram",
            "sounddevice",
            "speech_recognition",
            "playsound",
            "pydub",
            "vosk",
            "pyaudio",
            "soundfile",
        ], optional=True),
        
        # VRChat Integration
        DependencyTest("VRChat Integration", [
            "sentence_transformers",
            "unidecode",
        ]),
        
        # Cloud Services (Optional)
        DependencyTest("Cloud Services", [
            "boto3",
        ], optional=True),
    ]
    
    results = {}
    
    for test_case in test_cases:
        category_results = {}
        print(f"\nTesting {test_case.category} dependencies:")
        
        for module in test_case.modules:
            success = test_import(module)
            category_results[module] = success
            
        results[test_case.category] = category_results
    
    return results

def print_summary(results: Dict[str, Dict[str, bool]]):
    """Print a summary of test results."""
    print("\n=== Test Summary ===")
    
    total_tests = 0
    total_passed = 0
    
    for category, tests in results.items():
        category_total = len(tests)
        category_passed = sum(1 for success in tests.values() if success)
        total_tests += category_total
        total_passed += category_passed
        
        print(f"\n{category}:")
        print(f"Passed: {category_passed}/{category_total}")
        
        # Print failed tests for this category
        failed = [module for module, success in tests.items() if not success]
        if failed:
            print(f"Failed modules: {', '.join(failed)}")
    
    # Print overall results
    success_rate = (total_passed / total_tests) * 100 if total_tests > 0 else 0
    print(f"\nOverall Success Rate: {success_rate:.1f}% ({total_passed}/{total_tests})")

def main():
    """Main function to run tests."""
    print("Starting dependency tests...")
    
    try:
        results = run_dependency_tests()
        print_summary(results)
    except Exception as e:
        print(f"Test suite failed: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()