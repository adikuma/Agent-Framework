class LongTermMemory:
    def add(self, document):
        # Store raw text
        doc_id = uuid.uuid4()
        self.doc_store[doc_id] = document
        
        # Create embedding
        embedding = embed_model.encode(document)
        self.vector_db.upsert(doc_id, embedding)

    def retrieve(self, query, top_k=5):
        query_embedding = embed_model.encode(query)
        return self.vector_db.search(query_embedding, top_k)