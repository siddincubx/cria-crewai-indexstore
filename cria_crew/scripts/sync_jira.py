import os
import sys
import logging
import hashlib
from typing import List
from tqdm import tqdm

# Add parent directory to path to import utils
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'src'))

from cria_crew.tools.utils.vector_store import get_jira_vectorstore
from scripts.clients import JiraClient

logging.basicConfig(level=logging.INFO)

def sync_jira_issues():
    logging.info(f"📥 Request come inside sync jira Jira.")
    store = get_jira_vectorstore()
    jira = JiraClient()

    issues = jira.get_issues()
    docs_to_upsert = []

    logging.info(f"📥 Retrieved {len(issues)} issues from Jira.")

    # Step 1: Build a map of existing vectors from index
    try:
        index_stats = store.index.fetch([issue["id"] for issue in issues])
        existing_metadata = {
            match_id: match["metadata"]
            for match_id, match in index_stats.vectors.items()
        }
    except Exception as e:
        logging.error(f"⚠️ Failed to fetch existing vector metadata: {e}")
        existing_metadata = {}

    # Step 2: Compare hash of each issue
    new_count = 0
    updated_count = 0
    skipped_count = 0

    logging.info("🔍 Comparing issue content hashes...")

    for issue in tqdm(issues, desc="🔄 Syncing issues"):
        content_hash = compute_content_hash(issue["text"])
        issue["metadata"]["hash"] = content_hash

        existing = existing_metadata.get(issue["id"])
        existing_hash = existing.get("hash") if existing else None

        if existing_hash != content_hash:
            docs_to_upsert.append({
                "id": issue["id"],
                "text": issue["text"],
                "metadata": issue["metadata"]
            })
            if existing_hash is None:
                new_count += 1
            else:
                updated_count += 1
        else:
            skipped_count += 1

    # Step 3: Upsert only the changed or new ones
    if docs_to_upsert:
        logging.info(f"📤 Upserting {len(docs_to_upsert)} issues...")
        store.upsert_documents(docs_to_upsert)
    else:
        logging.info("✅ No new or updated Jira issues to upsert")

    # Final log summary
    logging.info("📝 Sync summary:")
    logging.info(f"   🆕 New issues added: {new_count}")
    logging.info(f"   🔁 Issues updated:   {updated_count}")
    logging.info(f"   ✅ Issues skipped:   {skipped_count}")
    logging.info("🎉 Sync complete.")

def compute_content_hash(text: str) -> str:
    return hashlib.md5(text.encode("utf-8")).hexdigest()
