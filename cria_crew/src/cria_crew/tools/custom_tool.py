import os
from typing import Any
import cocoindex
from psycopg_pool import ConnectionPool
import numpy as np
from numpy.typing import NDArray
from pgvector.psycopg import register_vector
from crewai.tools import BaseTool
from sqlalchemy import text

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
    # return text.transform(
    #     cocoindex.functions.EmbedText(
    #         api_type=cocoindex.LlmApiType.VOYAGE,
    #         model="voyage-code-3",
    #     )
    # )
    # return text.transform(
    #     cocoindex.functions.SentenceTransformerEmbed(
    #         model="sentence-transformers/all-MiniLM-L6-v2"
    #     )
    # )
    return text.transform(
        cocoindex.functions.SentenceTransformerEmbed(
            model="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
        )
    )

@cocoindex.flow_def(name="CodeEmbedding")
def code_embedding_flow(
    flow_builder: cocoindex.FlowBuilder, data_scope: cocoindex.DataScope
) -> None:
    """
    Define an example flow that embeds files into a vector database.
    """
    my_file_path = "C:/Projects/hackathon_cria/training-management-system"
    ec2_file_path = "~/cria-crew-indexstore/training-management-system"
    data_scope["files"] = flow_builder.add_source(
        cocoindex.sources.LocalFile(
            path=ec2_file_path,
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
                    url="postgres://postgres:postgresDoctor@cria-cocoindex-cluster.c5o4mgsmkcvz.us-east-2.rds.amazonaws.com/master"
                )
            )
        )
        # Get the table name, for the export target in the code_embedding_flow above.
        table_name = cocoindex.utils.get_target_default_name(
            code_embedding_flow, "code_embeddings"
        )
        pool = ConnectionPool("postgres://postgres:postgresDoctor@cria-cocoindex-cluster.c5o4mgsmkcvz.us-east-2.rds.amazonaws.com/master")
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