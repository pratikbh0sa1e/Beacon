"""Batch embed all documents into pgvector"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from Agent.lazy_rag.lazy_embedder import LazyEmbedder
from backend.database import SessionLocal, Document, DocumentMetadata
from sqlalchemy import and_

def batch_embed_all_documents():
    """Embed all documents that haven't been embedded yet"""
    print("🚀 Starting batch embedding process...")
    print("=" * 50)
    
    embedder = LazyEmbedder()
    db = SessionLocal()
    
    try:
        # Get all documents that need embedding
        docs_to_embed = db.query(Document).join(
            DocumentMetadata, Document.id == DocumentMetadata.document_id
        ).filter(
            and_(
                DocumentMetadata.embedding_status != 'embedded',
                Document.approval_status.in_(['approved', 'pending'])
            )
        ).all()
        
        if not docs_to_embed:
            print("✅ All documents are already embedded!")
            return
        
        print(f"📄 Found {len(docs_to_embed)} documents to embed")
        print("")
        
        successful = 0
        failed = 0
        
        for i, doc in enumerate(docs_to_embed, 1):
            print(f"[{i}/{len(docs_to_embed)}] Embedding document {doc.id}: {doc.filename}")
            
            result = embedder.embed_document(doc.id)
            
            if result['status'] == 'success':
                successful += 1
                print(f"  ✅ Success: {result['num_chunks']} chunks embedded")
            else:
                failed += 1
                print(f"  ❌ Failed: {result.get('message', 'Unknown error')}")
            
            print("")
        
        print("=" * 50)
        print(f"📊 Batch embedding complete!")
        print(f"  ✅ Successful: {successful}")
        print(f"  ❌ Failed: {failed}")
        print(f"  📈 Total: {len(docs_to_embed)}")
        
    except Exception as e:
        print(f"❌ Error during batch embedding: {str(e)}")
        sys.exit(1)
    finally:
        db.close()

def embed_specific_documents(doc_ids: list):
    """Embed specific documents by ID"""
    print(f"🚀 Embedding {len(doc_ids)} specific documents...")
    print("=" * 50)
    
    embedder = LazyEmbedder()
    db = SessionLocal()
    
    try:
        successful = 0
        failed = 0
        
        for i, doc_id in enumerate(doc_ids, 1):
            doc = db.query(Document).filter(Document.id == doc_id).first()
            if not doc:
                print(f"[{i}/{len(doc_ids)}] ❌ Document {doc_id} not found")
                failed += 1
                continue
            
            print(f"[{i}/{len(doc_ids)}] Embedding document {doc_id}: {doc.filename}")
            
            result = embedder.embed_document(doc_id)
            
            if result['status'] == 'success':
                successful += 1
                print(f"  ✅ Success: {result['num_chunks']} chunks embedded")
            else:
                failed += 1
                print(f"  ❌ Failed: {result.get('message', 'Unknown error')}")
            
            print("")
        
        print("=" * 50)
        print(f"📊 Embedding complete!")
        print(f"  ✅ Successful: {successful}")
        print(f"  ❌ Failed: {failed}")
        
    except Exception as e:
        print(f"❌ Error during embedding: {str(e)}")
        sys.exit(1)
    finally:
        db.close()

if __name__ == "__main__":
    if len(sys.argv) > 1:
        # Embed specific documents
        doc_ids = [int(x) for x in sys.argv[1:]]
        embed_specific_documents(doc_ids)
    else:
        # Embed all documents
        batch_embed_all_documents()
