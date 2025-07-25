import os
from typing import Type, List, Dict, Any, Optional

from crewai.tools import BaseTool
from pydantic import BaseModel, Field
from pinecone import Pinecone
from vertexai.language_models import TextEmbeddingModel
import vertexai
import cocoindex
from psycopg_pool import ConnectionPool
import numpy as np
from numpy.typing import NDArray
from pgvector.psycopg import register_vector



@cocoindex.op.function()
def extract_extension(filename: str) -> str:
    """Extract the extension of a filename."""
    return os.path.splitext(filename)[1]

@cocoindex.transform_flow()
def code_to_embedding(
    text: cocoindex.DataSlice[str],
) -> cocoindex.DataSlice[NDArray[np.float32]]:
    """
    Embed the text using a SentenceTransformer model.
    """
    # You can also switch to Voyage embedding model:
    #    return text.transform(
    #        cocoindex.functions.EmbedText(
    #            api_type=cocoindex.LlmApiType.VOYAGE,
    #            model="voyage-code-3",
    #        )
    #    )
    return text.transform(
        cocoindex.functions.SentenceTransformerEmbed(
            model="sentence-transformers/all-MiniLM-L6-v2"
        )
    )

@cocoindex.flow_def(name="CodeEmbedding")
def code_embedding_flow(
    flow_builder: cocoindex.FlowBuilder, data_scope: cocoindex.DataScope
) -> None:
    """
    Define an example flow that embeds files into a vector database.
    """
    data_scope["files"] = flow_builder.add_source(
        cocoindex.sources.LocalFile(
            path="C:/Projects/hackathon_cria/training-management-system",
            included_patterns=["*.js", "*.py", "*.json", "*.ts", "*.tsx", "*.rs", "*.toml", "*.md", "*.mdx"],
            excluded_patterns=[".*", "*.config.json", "target", "**/node_modules"])
    )
    code_embeddings = data_scope.add_collector()

    with data_scope["files"].row() as file:
        file["extension"] = file["filename"].transform(extract_extension)
        file["chunks"] = file["content"].transform(
            cocoindex.functions.SplitRecursively(),
            language=file["extension"],
            chunk_size=1000,
            min_chunk_size=300,
            chunk_overlap=300,
        )
        with file["chunks"].row() as chunk:
            chunk["embedding"] = chunk["text"].call(code_to_embedding)
            code_embeddings.collect(
                filename=file["filename"],
                location=chunk["location"],
                code=chunk["text"],
                embedding=chunk["embedding"],
                start=chunk["start"],
                end=chunk["end"],
            )

    code_embeddings.export(
        "code_embeddings",
        cocoindex.targets.Postgres(),
        primary_key_fields=["filename", "location"],
        vector_indexes=[
            cocoindex.VectorIndexDef(
                field_name="embedding",
                metric=cocoindex.VectorSimilarityMetric.COSINE_SIMILARITY,
            )
        ],
    )


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
        

class CodeBaseSearchTool(BaseTool):
    name: str = "Code Base Search"
    description: str = (
        "Search for relevant code snippets from a codebase using semantic similarity. "
        "This tool uses a pre-trained embedding model to find code that is semantically similar to your query. "
        "Perfect for finding related functions, classes, or code patterns."
    )
    # args_schema: Type[BaseModel] = JiraTicketSearchInput  # Reusing the same input schema for simplicity

    
    def _search(self, query: str, top_k: int = 5) -> list[dict[str, Any]]:
        cocoindex.init(
            cocoindex.Settings(
                database=cocoindex.DatabaseConnectionSpec(
                    url="postgres://cocoindex:cocoindex@localhost/cocoindex"
                )
            )
        )
        # Get the table name, for the export target in the code_embedding_flow above.
        table_name = cocoindex.utils.get_target_default_name(
            code_embedding_flow, "code_embeddings"
        )
        pool = ConnectionPool("postgres://cocoindex:cocoindex@localhost/cocoindex")
        # Evaluate the transform flow defined above with the input query, to get the embedding.
        query_vector = code_to_embedding.eval(query)
        # Run the query and get the results.
        with pool.connection() as conn:
            register_vector(conn)
            with conn.cursor() as cur:
                cur.execute(
                    f"""
                    SELECT filename, code, embedding <=> %s AS distance, start, "end"
                    FROM {table_name} ORDER BY distance LIMIT %s
                """,
                    (query_vector, top_k),
                )
                results = [
                    {
                        "filename": row[0],
                        "code": row[1],
                        "score": 1.0 - row[2],
                        "start": row[3],
                        "end": row[4],
                    }
                    for row in cur.fetchall()
                ]
                return results


    def _run(self, query: str, top_k: int = 5) -> str:
        """Execute the code base search."""
        # Placeholder for actual implementation
        results = self._search(query, top_k)
        if not results:
            return "No relevant code snippets found for the given query."
        formatted_results = []
        final_result = "\n".join(
                    [
                        (
                            f"[{result['score']:.3f}] {result['filename']} (L{result['start']['line']}-L{result['end']['line']})"
                            f"\n    {result['code']}\n---"
                            f"---"
                        )
                        for result in results
                    ])
        return final_result