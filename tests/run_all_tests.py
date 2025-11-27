"""Run all tests"""
import subprocess
import sys

def run_test(test_file: str):
    """Run a test file"""
    print(f"\n{'='*60}")
    print(f"Running: {test_file}")
    print(f"{'='*60}")
    
    result = subprocess.run([sys.executable, test_file], capture_output=False)
    return result.returncode == 0


if __name__ == "__main__":
    print("🚀 Running All Tests for Government Policy Intelligence Platform")
    print("="*60)
    
    tests = [
        "tests/test_embeddings.py",
        "tests/test_retrieval.py",
        "tests/test_document_upload.py",
        "tests/test_agent.py",
        "tests/test_citations.py"
    ]
    
    results = {}
    
    for test in tests:
        try:
            success = run_test(test)
            results[test] = "✅ PASSED" if success else "❌ FAILED"
        except Exception as e:
            results[test] = f"❌ ERROR: {str(e)}"
    
    # Summary
    print("\n" + "="*60)
    print("📊 TEST SUMMARY")
    print("="*60)
    
    for test, result in results.items():
        print(f"{test}: {result}")
    
    print("\n" + "="*60)
    
    passed = sum(1 for r in results.values() if "PASSED" in r)
    total = len(results)
    
    print(f"✅ {passed}/{total} test suites passed")
    
    if passed == total:
        print("🎉 All tests passed!")
        sys.exit(0)
    else:
        print("⚠️  Some tests failed")
        sys.exit(1)
