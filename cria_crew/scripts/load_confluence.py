from bs4 import BeautifulSoup
import os, requests, logging
import logging
from datetime import datetime
from langchain.text_splitter import RecursiveCharacterTextSplitter
import sys
from sentence_transformers import SentenceTransformer
from tqdm import tqdm
from llama_index.core.node_parser import SemanticSplitterNodeParser
from llama_index.core.schema import Document
from llama_index.embeddings.huggingface import HuggingFaceEmbedding

# Add parent directory to path to import utils
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'src'))
from scripts.clients import ConfluenceClient
from cria_crew.tools.utils.vector_store import get_confluence_vectorstore


# --- Constants ---
EMBEDDING_VERSION = "bge-v1.5"
SOURCE_NAME = "confluence"

# Initialize vector store
vector_store = get_confluence_vectorstore()
confluence = ConfluenceClient()
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
embedding_model_name = os.getenv("EMBEDDING_MODEL_NAME", "BAAI/bge-base-en-v1.5")
embed_model = HuggingFaceEmbedding(model_name="BAAI/bge-small-en-v1.5")

def embed_and_store(page):
    title = page["title"]
    html = page["body"]["storage"]["value"]
    text = BeautifulSoup(html, "html.parser").get_text()
    page_id = page["id"]

    # Semantic text for embedding
    full_text = text.strip()

    # Prepare LlamaIndex Document
    document = Document(text=full_text, metadata={"title": title, "page_id": page_id})
   
    # Semantic chunking (replace character-based splitter)
    semantic_parser = SemanticSplitterNodeParser(
        embed_model=embed_model,
        buffer_size=1,
        breakpoint_percentile_threshold=85
    )
    nodes = semantic_parser.get_nodes_from_documents([document])

    documents = []
    for i, node in enumerate(nodes):
        # Access node content correctly for llama_index
        node_text = getattr(node, 'text', '') if hasattr(node, 'text') else str(node)
        if not node_text and hasattr(node, 'get_content'):
            node_text = node.get_content()
        documents.append({
            "id": f"{page_id}-{i}",
            "text": node_text,
            "metadata": {
                "title": title,
                "page_id": page_id,
                "text": node_text,
                "source": SOURCE_NAME,
                "embedding_version": EMBEDDING_VERSION
            }
        })

    logging.info(f"Indexing Confluence page {page_id} with {len(documents)} semantic chunks.")

    # Vector store upsert
    vector_store.upsert_documents(documents)
def main():
    logging.info("🔍 Fetching Confluence pages...")
    pages = confluence.get_pages()
    logging.info(f"📦 Retrieved {len(pages)} pages. Starting embedding and storage...")

    for page in tqdm(pages, desc="🔄 Embedding pages"):
        try:
            embed_and_store(page)
        except Exception as e:
            logging.warning(f"⚠️ Failed to process page {page.get('id')}: {e}")

    logging.info("✅ Done embedding and storing Confluence pages.")

if __name__ == "__main__":
    main()

