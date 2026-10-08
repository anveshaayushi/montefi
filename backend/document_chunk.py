# document_chunk.py — stores RAG document chunks + their embeddings
import peewee as pw
import json
from database import db


class DocumentChunk(pw.Model):
    id          = pw.AutoField()
    ticker      = pw.CharField(max_length=10)
    title       = pw.CharField(max_length=200)
    section     = pw.CharField(max_length=100, default="General")
    chunk_text  = pw.TextField()
    embedding   = pw.TextField()   # JSON-encoded list of floats
    created_at  = pw.DateTimeField()

    class Meta:
        database   = db
        table_name = "document_chunks"

    def get_embedding(self):
        return json.loads(self.embedding)

    def set_embedding(self, vec):
        self.embedding = json.dumps(vec)