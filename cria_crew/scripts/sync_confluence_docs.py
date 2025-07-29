import os
import sys
import logging
import hashlib
from typing import List
from tqdm import tqdm

# Add parent directory to path to import utils
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'src'))

from cria_crew.tools.utils.vector_store import get_confluence_vectorstore
from scripts.clients import ConfluenceClient

logging.basicConfig(level=logging.INFO)

def compute_content_hash(text: str) -> str:
    return hashlib.md5(text.encode("utf-8")).hexdigest()

def sync_confluence_pages():
    store = get_confluence_vectorstore()
    confluence = ConfluenceClient()

    pages = confluence.get_pages()
    docs_to_upsert = []

    logging.info(f"📥 Retrieved {len(pages)} Confluence pages.")

    # Step 1: Fetch existing vectors
    try:
        index_stats = store.index.fetch([page["id"] for page in pages])
        existing_metadata = {
            match_id: match["metadata"]
            for match_id, match in index_stats.vectors.items()
        }
    except Exception as e:
        logging.error(f"⚠️ Failed to fetch existing vector metadata: {e}")
        existing_metadata = {}

    # Step 2: Compare hashes
    new_count = 0
    updated_count = 0
    skipped_count = 0

    logging.info("🔍 Comparing page content hashes...")

    for page in tqdm(pages, desc="🔄 Syncing Confluence pages"):
        content_hash = compute_content_hash(page["text"])
        page["metadata"]["hash"] = content_hash

        existing = existing_metadata.get(page["id"])
        existing_hash = existing.get("hash") if existing else None

        if existing_hash != content_hash:
            docs_to_upsert.append({
                "id": page["id"],
                "text": page["text"],
                "metadata": page["metadata"]
            })
            if existing_hash is None:
                new_count += 1
            else:
                updated_count += 1
        else:
            skipped_count += 1

    # Step 3: Upsert
    if docs_to_upsert:
        logging.info(f"📤 Upserting {len(docs_to_upsert)} new/updated pages...")
        store.upsert_documents(docs_to_upsert)
    else:
        logging.info("✅ No new or updated Confluence pages to upsert.")

    # Summary
    logging.info("📝 Sync summary:")
    logging.info(f"   🆕 New pages added:   {new_count}")
    logging.info(f"   🔁 Pages updated:     {updated_count}")
    logging.info(f"   ✅ Pages unchanged:   {skipped_count}")
    logging.info("🎉 Confluence sync complete.")

if __name__ == "__main__":
    sync_confluence_pages()
