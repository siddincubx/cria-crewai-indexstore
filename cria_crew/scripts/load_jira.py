import os, requests, logging, json, base64
import urllib.parse
from tqdm import tqdm
from dotenv import load_dotenv
import sys
import logging
from datetime import datetime
from langchain.text_splitter import RecursiveCharacterTextSplitter
from llama_index.core.node_parser import SemanticSplitterNodeParser
from llama_index.core.schema import Document
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
# Add parent directory to path to import utils
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'src'))
from cria_crew.tools.utils.vector_store import get_jira_vectorstore

load_dotenv()

JIRA_BASE_URL = os.getenv("BASE_URL")
JIRA_TOKEN = os.getenv("API_TOKEN")
JIRA_EMAIL = os.getenv("USER_EMAIL")
JIRA_PROJECT_KEY = os.getenv("PROJECT_KEY")

# --- Constants ---
EMBEDDING_VERSION = "bge-v1.5"
SOURCE_NAME = "jira"
CHUNK_SIZE = 512
CHUNK_OVERLAP = 50

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
embedding_model_name = os.getenv("EMBEDDING_MODEL_NAME", "BAAI/bge-base-en-v1.5")
embed_model = HuggingFaceEmbedding(model_name="BAAI/bge-small-en-v1.5")
# Initialize vector store
vector_store = get_jira_vectorstore()

def fetch_all_issues():
    logging.info("🔐 Preparing authentication for Jira API...")

    auth_str = f"{JIRA_EMAIL}:{JIRA_TOKEN}"
    b64_auth = base64.b64encode(auth_str.encode()).decode()

    headers = {
        "Authorization": f"Basic {b64_auth}",
        "Content-Type": "application/json",
        "Accept": "application/json"
    }

    search_query = f'project={JIRA_PROJECT_KEY} ORDER BY created DESC'
    encoded_query = urllib.parse.quote(search_query)
    url = f"{JIRA_BASE_URL}/rest/api/3/search?jql={encoded_query}"

    logging.info(f"🌐 Fetching issues from URL: {url}")

    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            issues = response.json().get("issues", [])
            logging.info(f"✅ Successfully fetched {len(issues)} issues from Jira.")
            return issues
        else:
            logging.error(f"❌ Jira API returned status code {response.status_code}: {response.text}")
            return []
    except Exception as e:
        logging.exception(f"💥 Exception while calling Jira API: {e}")
        return []
def parse_adf_to_text(adf_node):
    """Recursively parses Atlassian Document Format (ADF) content into plain text."""
    if not adf_node:
        return ""

    node_type = adf_node.get("type")
    content = adf_node.get("content", [])
    text = ""

    if node_type == "text":
        return adf_node.get("text", "")

    if isinstance(content, list):
        for item in content:
            text += parse_adf_to_text(item)
            if item.get("type") in ("paragraph", "heading", "bulletList", "orderedList", "listItem"):
                text += "\n"

    return text.strip()


def extract_jira_description_and_comments(issue):
    """
    Extracts full text from Jira issue's ADF-based description and comments.
    Returns a combined string of description and all comments.
    """
    description_text = ""
    comment_texts = []

    # Parse description (ADF format)
    adf_description = issue.get("fields", {}).get("description")
    if adf_description:
        description_text = parse_adf_to_text(adf_description)

    # Parse comments (ADF format)
    comments = issue.get("fields", {}).get("comment", {}).get("comments", [])
    for comment in comments:
        adf_body = comment.get("body")
        if adf_body:
            parsed = parse_adf_to_text(adf_body)
            if parsed:
                comment_texts.append(parsed)

    # Combine and return
    full_content = description_text + "\n\n" + "\n\n".join(comment_texts)
    return full_content.strip()

def embed_and_store(issue):
    fields = issue.get("fields", {})
    summary = fields.get("summary", "")
    description_data = fields.get("description", {})
    full_text = extract_jira_description_and_comments(issue)
    logging.info(f"complete description issue {full_text }")
    # Safe extraction from nested Atlassian document content
    description = full_text

    components = [c.get("name", "") for c in fields.get("components", [])]
    status = fields.get("status", {}).get("name", "")
    priority = fields.get("priority", {}).get("name", "")
    assignee = fields.get("assignee", {}).get("displayName", "")
    created = fields.get("created", "")
    updated = fields.get("updated", "")
    labels = fields.get("labels", [])
    issue_type = fields.get("issuetype", {}).get("name", "")
    issue_id = issue.get("id", "")
    key = issue.get("key", "")
    # Convert timestamps to epoch (useful for numeric filters)
    def iso_to_ts(iso_str):
        try:
            return datetime.fromisoformat(iso_str.rstrip("Z")).timestamp()
        except Exception:
            return 0.0

    ticket_url = f"{JIRA_BASE_URL}/browse/{issue['key']}"

    # Semantic text for embedding — clean & minimal
    full_text = f"{summary}\n\n{description}\n\nLabels: {', '.join(labels)}"

    # Prepare LlamaIndex Document
    document = Document(text= full_text, metadata={"summary": summary,  "key": key, "id": issue_id})
   
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
            "id": f"{issue_id}-{i+1}",
            "text": node_text,
            "metadata": {
                "key": key,
                "status": status,
                "priority": priority,
                "text": node_text,
                "assignee": assignee,
                "created_ts": iso_to_ts(created),
                "updated_ts": iso_to_ts(updated),
                "labels": labels,
                "issue_type": issue_type,
                "components": components,
                "id": issue_id,
                "ticket_url": ticket_url,
                "source": SOURCE_NAME,
                "embedding_version": EMBEDDING_VERSION,
            }
        })
    logging.info(f"Indexing issue {issue['key']} with {len(documents)} chunks.")

    # Vector store upsert (batch if needed)
    vector_store.upsert_documents(documents)

def main():
    logging.info("🔍 Fetching Jira issues...")
    issues = fetch_all_issues()
    logging.info(f"📦 Retrieved {len(issues)} issues. Starting embedding and storage...")

    for issue in tqdm(issues, desc="🔄 Embedding issues"):
        try:
            embed_and_store(issue)
        except Exception as e:
            logging.warning(f"⚠️ Failed to process issue {issue.get('key')}: {e}")

    logging.info("✅ Done embedding and storing Jira issues.")
    
    # Print index statistics
    stats = vector_store.get_index_stats()
    logging.info(f"📊 Index statistics: {stats}")

if __name__ == "__main__":
    main()
