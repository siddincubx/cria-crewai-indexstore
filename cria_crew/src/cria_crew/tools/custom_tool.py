import os
from typing import Type, List, Dict, Any, Optional

from crewai.tools import BaseTool
from pydantic import BaseModel, Field
from pinecone import Pinecone
from vertexai.language_models import TextEmbeddingModel
import vertexai


class JiraTicketSearchInput(BaseModel):
    """Input schema for JiraTicketSearchTool."""
    query: str = Field(..., description="The search query to find relevant JIRA tickets.")
    top_k: int = Field(default=5, description="Number of most relevant tickets to return.")


class JiraTicketSearchTool(BaseTool):
    name: str = "JIRA Ticket Search"
    description: str = (
        "Search for relevant JIRA tickets from a Pinecone vector database using semantic similarity. "
        "This tool uses Vertex AI embeddings to find tickets that are semantically similar to your query. "
        "Perfect for finding related issues, bugs, or feature requests."
    )
    args_schema: Type[BaseModel] = JiraTicketSearchInput
    
    # Initialize these as class attributes to avoid Pydantic field validation issues
    _embedding_model: Optional[Any] = None
    _pc: Optional[Any] = None
    _index: Optional[Any] = None
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._initialize_clients()

    def _initialize_clients(self):
        """Initialize Pinecone and Vertex AI clients."""
        try:
            # Initialize Vertex AI
            project_id = os.getenv("GOOGLE_CLOUD_PROJECT")
            if project_id:
                vertexai.init(project=project_id)
            
            # Initialize embedding model
            self._embedding_model = TextEmbeddingModel.from_pretrained("text-embedding-005")
            
            # Initialize Pinecone
            pinecone_api_key = os.getenv("PINECONE_API_KEY")
            if not pinecone_api_key:
                raise ValueError("PINECONE_API_KEY environment variable is required")
            
            self._pc = Pinecone(api_key=pinecone_api_key)
            
            # Connect to index
            index_name = os.getenv("PINECONE_INDEX_NAME", "jira-tickets")
            self._index = self._pc.Index(index_name)
            
        except Exception as e:
            print(f"Warning: Failed to initialize Pinecone/Vertex AI clients: {e}")
            self._embedding_model = None
            self._index = None

    def _get_query_embedding(self, query: str) -> List[float]:
        """Generate embedding for the query using Vertex AI."""
        try:
            if not self._embedding_model:
                raise Exception("Embedding model not initialized")
            embeddings = self._embedding_model.get_embeddings([query])
            return embeddings[0].values
        except Exception as e:
            raise Exception(f"Failed to generate embeddings: {e}")

    def _search_pinecone(self, query_embedding: List[float], top_k: int = 5) -> List[Dict[str, Any]]:
        """Search Pinecone index for similar vectors."""
        try:
            if not self._index:
                raise Exception("Pinecone index not initialized")
            results = self._index.query(
                vector=query_embedding,
                top_k=top_k,
                include_metadata=True,
                include_values=False
            )
            
            return [
                {
                    "id": match["id"],
                    "score": match["score"],
                    "metadata": match.get("metadata", {})
                }
                for match in results["matches"]
            ]
        except Exception as e:
            raise Exception(f"Failed to search Pinecone: {e}")

    def _format_results(self, search_results: List[Dict[str, Any]]) -> str:
        """Format search results into a readable string."""
        if not search_results:
            return "No relevant JIRA tickets found for the given query."
        
        formatted_results = []
        formatted_results.append("Found the following relevant JIRA tickets:\n")
        
        for i, result in enumerate(search_results, 1):
            metadata = result["metadata"]
            score = result["score"]
            
            # Extract common JIRA fields from metadata
            ticket_id = metadata.get("ticket_id", result["id"])
            summary = metadata.get("summary", "No summary available")
            description = metadata.get("description", "No description available")
            status = metadata.get("status", "Unknown")
            priority = metadata.get("priority", "Unknown")
            assignee = metadata.get("assignee", "Unassigned")
            created = metadata.get("created", "Unknown")
            
            formatted_results.append(f"{i}. **{ticket_id}** (Similarity: {score:.3f})")
            formatted_results.append(f"   Summary: {summary}")
            formatted_results.append(f"   Status: {status} | Priority: {priority} | Assignee: {assignee}")
            formatted_results.append(f"   Created: {created}")
            formatted_results.append(f"   Description: {description[:200]}{'...' if len(description) > 200 else ''}")
            formatted_results.append("")
        
        return "\n".join(formatted_results)

    def _run(self, query: str, top_k: int = 5) -> str:
        """Execute the JIRA ticket search."""
        try:
            if not self._embedding_model or not self._index:
                return "Error: Pinecone or Vertex AI not properly initialized. Please check your API keys and configuration."
            
            # Generate query embedding
            query_embedding = self._get_query_embedding(query)
            
            # Search Pinecone
            search_results = self._search_pinecone(query_embedding, top_k)
            
            # Format and return results
            return self._format_results(search_results)
            
        except Exception as e:
            return f"Error searching for JIRA tickets: {str(e)}"