import logging
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from pinecone import Pinecone, PineconeException
from sentence_transformers import SentenceTransformer
import os
class VectorStore:
    def __init__(self, index_name: str, embedding_model_name: Optional[str] = None):
        self.index_name = index_name
        self.embedding_model_name = embedding_model_name or os.getenv("EMBEDDING_MODEL_NAME", "BAAI/bge-base-en-v1.5")
        logging.info(f"🔎 Loading embedding model: {self.embedding_model_name}")
        self.embedding_model = SentenceTransformer(self.embedding_model_name)
        self.pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
        try:
            self.index = self.pc.Index(self.index_name)
            logging.info(f"✅ Connected to Pinecone index: {self.index_name}")
        except PineconeException as e:
            logging.error(f"❌ Failed to connect to Pinecone index '{self.index_name}': {e}")
            raise

    def embed_text(self, text: str) -> List[float]:
        """Generate dense vector for a single text input."""
        return self.embedding_model.encode(text, convert_to_numpy=True).tolist()

    def _sanitize_metadata(self, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Ensure metadata values are primitive types."""
        def sanitize(value):
            if isinstance(value, (str, int, float, bool)) or value is None:
                return value
            elif isinstance(value, list):
                return [str(v) for v in value if v is not None]
            elif isinstance(value, dict):
                return str(value)
            return str(value)

        return {k: sanitize(v) for k, v in metadata.items()}

    def search(self, query: str, top_k: int = 10, filter_dict: Optional[Dict] = None) -> List[Dict[str, Any]]:
        """Semantic search with optional metadata filter."""
        try:
            query_vector = self.embed_text(query)
            kwargs = {
                "vector": query_vector,
                "top_k": top_k,
                "include_metadata": True,
                "include_values": False
            }
            if filter_dict:
                kwargs["filter"] = filter_dict

            results = self.index.query(**kwargs)
        
            return [
                {
                    "id": match["id"],
                    "score": match["score"],
                    "metadata": match.get("metadata", {})
                }
                for match in results.get("matches", [])
            ]
        except Exception as e:
            logging.error(f"❌ Search failed: {e}")
            return []
