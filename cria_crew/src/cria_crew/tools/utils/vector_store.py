"""Vector store utility functions for Jira and Confluence data."""

import os
from .data_model import VectorStore


def get_jira_vectorstore() -> VectorStore:
    """Get or create Jira vector store instance."""
    return VectorStore(
        index_name=os.getenv("JIRA_INDEX_NAME", "jira-issues"),
        embedding_model_name=os.getenv("EMBEDDING_MODEL_NAME", "BAAI/bge-base-en-v1.5")
    )


def get_confluence_vectorstore() -> VectorStore:
    """Get or create Confluence vector store instance."""
    return VectorStore(
        index_name=os.getenv("CONFLUENCE_INDEX_NAME", "confluence-pages"),
        embedding_model_name=os.getenv("EMBEDDING_MODEL_NAME", "BAAI/bge-base-en-v1.5")
    )
