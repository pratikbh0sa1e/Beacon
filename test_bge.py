from Agent.embeddings.bge_embedder import BGEEmbedder

print("Testing BGE Embedder...")
embedder = BGEEmbedder()
print(f"Embedding dimension: {embedder.get_dimension()}")

test_text = "Hello world, this is a test."
embedding = embedder.embed_text(test_text)
print(f"Test embedding length: {len(embedding)}")
print("✅ BGE Embedder working successfully!")
