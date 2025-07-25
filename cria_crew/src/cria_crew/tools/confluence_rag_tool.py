from .utils.data_model import VectorStore
import os
from crewai.tools import BaseTool


class ConfluenceRAGTool(BaseTool):
    name: str = "Confluence Search"
    description: str = "Search for relevant documentation and knowledge articles from Confluence using semantic similarity."
    
    # def __init__(self):
    #     super().__init__(
    #         name=self.name,
    #         description=self.description
    #     )
    
    def _get_vector_store(self, index_name, model_name) -> VectorStore:
        """Get or create vector store instance."""
        return VectorStore(
            index_name=index_name,
            embedding_model_name=model_name
        )

    def _run(self, query: str) -> str:
        """Run the tool to search Confluence for relevant pages."""
        vs = self._get_vector_store(
            index_name=os.getenv("CONFLUENCE_INDEX_NAME", "confluence-pages"),
            model_name=os.getenv("EMBEDDING_MODEL_NAME", "BAAI/bge-base-en-v1.5")
        )
        rag_context = vs.search(query)
        if not rag_context:
            return "No relevant Confluence pages found."
        
        context_texts = []
        for item in rag_context:
            text_content = None
            
            if 'metadata' in item and 'text' in item['metadata']:
                text_content = item['metadata']['text']
            elif 'metadata' in item and 'content' in item['metadata']:
                text_content = item['metadata']['content']
            elif isinstance(item, str):
                text_content = item
            
            # Handle the case where text_content might be a list
            if text_content is not None:
                if isinstance(text_content, list):
                    # If it's a list, join the items with spaces
                    context_texts.append(" ".join(str(x) for x in text_content))
                else:
                    # If it's a string or other type, convert to string
                    context_texts.append(str(text_content))
        
        return "\n\n".join(context_texts)
        