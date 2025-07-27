from .utils.data_model import VectorStore
from crewai.tools import BaseTool
import os
class JiraSearchTool(BaseTool):
    name: str = "JIRA Search"
    description: str = (
        "Search for relevant JIRA tickets using semantic similarity. "
        "This tool uses a pre-trained embedding model to find tickets that are semantically similar to your query. "
        "Perfect for finding related issues, bugs, and feature requests."
    )
    
    def _get_vector_store(self, index_name, model_name) -> VectorStore:
        """Get or create vector store instance."""
        return VectorStore(
            index_name=index_name,
            embedding_model_name=model_name
        )
    
    def _run(self, query: str) -> str:
        vs = self._get_vector_store(
            index_name=os.getenv("JIRA_INDEX_NAME", "jira-issues"),
            model_name=os.getenv("EMBEDDING_MODEL_NAME", "BAAI/bge-base-en-v1.5")
        )
        search_results = vs.search(query)
        context_texts = []
        for result in search_results:
            metadata = result.get('metadata', {})
            # Reconstruct text from metadata
            text_parts = []
            if metadata.get('summary'):
                text_parts.append(f"Summary: {metadata['summary']}")
            if metadata.get('text'):
                text_parts.append(f"Text: {metadata['text']}")
            if metadata.get('status'):
                text_parts.append(f"Status: {metadata['status']}")
            if metadata.get('priority'):
                text_parts.append(f"Priority: {metadata['priority']}")
            if metadata.get('assignee'):
                text_parts.append(f"Assignee: {metadata['assignee']}")
            if metadata.get('issue_type'):
                text_parts.append(f"Type: {metadata['issue_type']}")
            if metadata.get('ticket_url'):
                text_parts.append(f"URL: {metadata['ticket_url']}")
            
            context_text = f"Issue {metadata.get('key', 'Unknown')}: " + " | ".join(text_parts)
            context_texts.append(context_text)
        if not context_texts:
            return ""
        return "\n\n".join(context_texts)