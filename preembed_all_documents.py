"""
Pre-embed ALL documents in the database
This will generate embeddings for all documents that don't have them yet
"""
import sys
sys.path.insert(0, '.')

from backend.database import SessionLocal, Document, DocumentEmbedding, DocumentMetadata
from Agent.lazy_rag.lazy_embedder import LazyEmbedder
from datetime import datetime
import time

def get_documents_without_embeddings(db):
    """Get all documents that don't have embeddings yet"""
    # Find documents that have no embeddings
    docs_with_embeddings = db.query(DocumentEmbedding.document_id).distinct().all()
    embedded_ids = {doc_id for (doc_id,) in docs_with_embeddings}
    
    # Get all documents
    all_docs = db.query(Document).filter(
        Document.extracted_text.isnot(None),
        Document.extracted_text != ''
    ).all()
    
    # Filter out already embedded
    docs_without_embeddings = [
        doc for doc in all_docs 
        if doc.id not in embedded_ids
    ]
    
    return docs_without_embeddings, len(embedded_ids)


def preembed_all_documents():
    """Pre-embed all documents in the database"""
    print("="*80)
    print("PRE-EMBEDDING ALL DOCUMENTS")
    print("="*80)
    
    db = SessionLocal()
    embedder = LazyEmbedder()
    
    try:
        # Step 1: Get documents without embeddings
        print("\nStep 1: Finding documents without embeddings...")
        docs_to_embed, already_embedded = get_documents_without_embeddings(db)
        
        total_docs = db.query(Document).count()
        
        print(f"\nDocument Status:")
        print(f"  Total documents: {total_docs}")
        print(f"  Already embedded: {already_embedded}")
        print(f"  Need embedding: {len(docs_to_embed)}")
        
        if len(docs_to_embed) == 0:
            print("\n✅ All documents are already embedded!")
            return
        
        # Step 2: Confirm
        print("\n" + "="*80)
        print(f"This will embed {len(docs_to_embed)} documents.")
        print(f"Estimated time: {len(docs_to_embed) * 2} seconds (~2 sec per document)")
        print("="*80)
        
        response = input("\nProceed with embedding? (yes/no): ")
        if response.lower() not in ['yes', 'y']:
            print("❌ Cancelled")
            return
        
        # Step 3: Embed documents
        print("\n" + "="*80)
        print("EMBEDDING DOCUMENTS")
        print("="*80)
        
        start_time = time.time()
        successful = 0
        failed = 0
        
        for i, doc in enumerate(docs_to_embed, 1):
            print(f"\n[{i}/{len(docs_to_embed)}] Embedding: {doc.filename[:60]}...")
            print(f"  Document ID: {doc.id}")
            print(f"  Text length: {len(doc.extracted_text) if doc.extracted_text else 0} chars")
            
            try:
                result = embedder.embed_document(
                    doc_id=doc.id,
                    text=doc.extracted_text,
                    filename=doc.filename
                )
                
                if result['status'] == 'success':
                    successful += 1
                    print(f"  ✓ Success: {result['num_chunks']} chunks, {result['num_embeddings']} embeddings")
                else:
                    failed += 1
                    print(f"  ✗ Failed: {result.get('message', 'Unknown error')}")
            
            except Exception as e:
                failed += 1
                print(f"  ✗ Error: {str(e)}")
            
            # Progress update every 10 documents
            if i % 10 == 0:
                elapsed = time.time() - start_time
                avg_time = elapsed / i
                remaining = (len(docs_to_embed) - i) * avg_time
                print(f"\n  Progress: {i}/{len(docs_to_embed)} ({i/len(docs_to_embed)*100:.1f}%)")
                print(f"  Elapsed: {elapsed:.1f}s | Remaining: {remaining:.1f}s")
        
        # Step 4: Summary
        elapsed_time = time.time() - start_time
        
        print("\n" + "="*80)
        print("EMBEDDING COMPLETE")
        print("="*80)
        print(f"\nResults:")
        print(f"  ✓ Successful: {successful}")
        print(f"  ✗ Failed: {failed}")
        print(f"  Total time: {elapsed_time:.1f} seconds")
        print(f"  Average: {elapsed_time/len(docs_to_embed):.2f} sec/document")
        
        # Step 5: Verify
        print("\n" + "="*80)
        print("VERIFICATION")
        print("="*80)
        
        docs_still_missing, now_embedded = get_documents_without_embeddings(db)
        
        print(f"\nFinal Status:")
        print(f"  Total documents: {total_docs}")
        print(f"  Embedded: {now_embedded}")
        print(f"  Still missing: {len(docs_still_missing)}")
        print(f"  Coverage: {now_embedded/total_docs*100:.1f}%")
        
        if len(docs_still_missing) > 0:
            print(f"\n⚠ {len(docs_still_missing)} documents still need embedding")
            print("Documents without embeddings:")
            for doc in docs_still_missing[:5]:
                print(f"  - ID {doc.id}: {doc.filename[:60]}")
            if len(docs_still_missing) > 5:
                print(f"  ... and {len(docs_still_missing) - 5} more")
        else:
            print("\n✅ All documents are now embedded!")
        
    finally:
        db.close()


def check_embedding_status():
    """Quick check of embedding status"""
    print("="*80)
    print("EMBEDDING STATUS CHECK")
    print("="*80)
    
    db = SessionLocal()
    
    try:
        total_docs = db.query(Document).filter(
            Document.extracted_text.isnot(None),
            Document.extracted_text != ''
        ).count()
        
        docs_with_embeddings = db.query(DocumentEmbedding.document_id).distinct().count()
        
        total_embeddings = db.query(DocumentEmbedding).count()
        
        print(f"\nStatus:")
        print(f"  Documents with text: {total_docs}")
        print(f"  Documents embedded: {docs_with_embeddings}")
        print(f"  Total embedding chunks: {total_embeddings}")
        print(f"  Coverage: {docs_with_embeddings/total_docs*100:.1f}%" if total_docs > 0 else "  Coverage: 0%")
        
        if docs_with_embeddings < total_docs:
            print(f"\n⚠ {total_docs - docs_with_embeddings} documents need embedding")
        else:
            print("\n✅ All documents are embedded!")
        
    finally:
        db.close()


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Pre-embed all documents")
    parser.add_argument('--check', action='store_true', help='Just check status, don\'t embed')
    parser.add_argument('--force', action='store_true', help='Skip confirmation prompt')
    
    args = parser.parse_args()
    
    if args.check:
        check_embedding_status()
    else:
        preembed_all_documents()
