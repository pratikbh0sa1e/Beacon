"""Test document upload and processing"""
import requests
import os
from pathlib import Path

BASE_URL = "http://localhost:8000"

def test_upload_pdf():
    """Test PDF upload"""
    print("\n=== Testing PDF Upload ===")
    
    # Create a test PDF if needed
    test_file = Path("tests/test_data/sample.pdf")
    if not test_file.exists():
        print("⚠️  No test PDF found. Please add a PDF to tests/test_data/sample.pdf")
        return
    
    with open(test_file, "rb") as f:
        files = {"files": ("sample.pdf", f, "application/pdf")}
        response = requests.post(
            f"{BASE_URL}/documents/upload?source_department=TestDept",
            files=files
        )
    
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    
    if response.status_code == 200:
        print("✅ PDF upload successful")
        return response.json()
    else:
        print("❌ PDF upload failed")
        return None


def test_upload_docx():
    """Test DOCX upload"""
    print("\n=== Testing DOCX Upload ===")
    
    test_file = Path("tests/test_data/sample.docx")
    if not test_file.exists():
        print("⚠️  No test DOCX found. Please add a DOCX to tests/test_data/sample.docx")
        return
    
    with open(test_file, "rb") as f:
        files = {"files": ("sample.docx", f, "application/vnd.openxmlformats-officedocument.wordprocessingml.document")}
        response = requests.post(
            f"{BASE_URL}/documents/upload?source_department=TestDept",
            files=files
        )
    
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    
    if response.status_code == 200:
        print("✅ DOCX upload successful")
        return response.json()
    else:
        print("❌ DOCX upload failed")
        return None


def test_list_documents():
    """Test listing all documents"""
    print("\n=== Testing List Documents ===")
    
    response = requests.get(f"{BASE_URL}/documents/list")
    
    print(f"Status: {response.status_code}")
    data = response.json()
    print(f"Total documents: {len(data.get('documents', []))}")
    
    if response.status_code == 200:
        print("✅ List documents successful")
        return data
    else:
        print("❌ List documents failed")
        return None


def test_get_document(document_id: int):
    """Test getting specific document"""
    print(f"\n=== Testing Get Document {document_id} ===")
    
    response = requests.get(f"{BASE_URL}/documents/{document_id}")
    
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"Filename: {data.get('filename')}")
        print(f"File type: {data.get('file_type')}")
        print(f"Text length: {len(data.get('extracted_text', ''))}")
        print("✅ Get document successful")
        return data
    else:
        print("❌ Get document failed")
        return None


def test_vector_stats():
    """Test vector store statistics"""
    print("\n=== Testing Vector Stats ===")
    
    response = requests.get(f"{BASE_URL}/documents/vector-stats")
    
    print(f"Status: {response.status_code}")
    data = response.json()
    print(f"Response: {data}")
    
    if response.status_code == 200:
        print("✅ Vector stats successful")
        return data
    else:
        print("❌ Vector stats failed")
        return None


def test_document_vector_stats(document_id: int):
    """Test document-specific vector stats"""
    print(f"\n=== Testing Document {document_id} Vector Stats ===")
    
    response = requests.get(f"{BASE_URL}/documents/vector-stats/{document_id}")
    
    print(f"Status: {response.status_code}")
    data = response.json()
    print(f"Response: {data}")
    
    if response.status_code == 200:
        print("✅ Document vector stats successful")
        return data
    else:
        print("❌ Document vector stats failed")
        return None


if __name__ == "__main__":
    print("🚀 Starting Document Upload Tests")
    print("=" * 50)
    
    # Test uploads
    # test_upload_pdf()
    # test_upload_docx()
    
    # Test listing
    docs = test_list_documents()
    
    # Test getting specific document
    if docs and docs.get('documents'):
        doc_id = docs['documents'][0]['id']
        test_get_document(doc_id)
        test_document_vector_stats(doc_id)
    
    # Test vector stats
    test_vector_stats()
    
    print("\n" + "=" * 50)
    print("✅ All tests completed!")
