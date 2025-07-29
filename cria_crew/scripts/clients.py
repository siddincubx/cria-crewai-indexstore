import base64
import os
import sys
import logging
from typing import List, Dict, Any
from dotenv import load_dotenv
import urllib.parse

import requests
load_dotenv()

# Add parent directory to path to import from src
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'src'))

class JiraClient:
    def __init__(self):
        self.base_url = os.getenv("BASE_URL")
        self.project_key = os.getenv("PROJECT_KEY")
        self.email = os.getenv("USER_EMAIL")
        self.token = os.getenv("API_TOKEN")
        auth_str = f"{self.email}:{self.token}"
        self.headers = {
            "Authorization": f"Basic {base64.b64encode(auth_str.encode()).decode()}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }

    def get_issues(self) -> List[dict]:
        logging.info("🌐 Fetching Jira issues via API...")
        all_issues = []
        start_at = 0
        max_results = 500

        while True:
            jql = f"project={self.project_key} ORDER BY updated DESC"
            url = (
                f"{self.base_url}/rest/api/3/search?"
                f"jql={urllib.parse.quote(jql)}"
                f"&startAt={start_at}&maxResults={max_results}"
            )
            resp = requests.get(url, headers=self.headers)

            if resp.status_code != 200:
                logging.error(f"❌ Jira API error {resp.status_code}: {resp.text}")
                break

            data = resp.json()
            issues = data.get("issues", [])
            all_issues.extend(issues)

            if start_at + max_results >= data.get("total", 0):
                break

            start_at += max_results

        logging.info(f"✅ Retrieved {len(all_issues)} total issues.")
        return self._transform_issues(all_issues)

    def _transform_issues(self, raw_issues: List[dict]) -> List[dict]:
        """Converts raw Jira issues into simplified vector-ready format."""
        transformed = []

        for issue in raw_issues:
            fields = issue.get("fields", {})
            summary = fields.get("summary", "")
            description = ""

            try:
                description = fields.get("description", {}).get("content", [])[0].get("content", [])[0].get("text", "")
            except Exception:
                description = ""

            full_text = f"{summary}\n\n{description}".strip()

            transformed.append({
                "id": issue.get("id", ""),
                "text": full_text,
                "metadata": {
                    "key": issue.get("key", ""),
                    "status": fields.get("status", {}).get("name", ""),
                    "priority": fields.get("priority", {}).get("name", ""),
                    "issue_type": fields.get("issuetype", {}).get("name", ""),
                    "assignee": fields.get("assignee", {}).get("displayName", "") if fields.get("assignee") else "",
                    "created": fields.get("created", ""),
                    "updated": fields.get("updated", ""),
                    "labels": fields.get("labels", []),
                    "ticket_url": f"{self.base_url}/browse/{issue.get('key')}",
                    "source": "jira",
                    "embedding_version": "bge-v1.5"
                }
            })

        return transformed



BASE_URL = os.getenv("BASE_URL")
TOKEN = os.getenv("API_TOKEN")
EMAIL = os.getenv("USER_EMAIL")

class ConfluenceClient:
    
    def __init__(self):
        auth_str = f"{EMAIL}:{TOKEN}"
        self.headers = {
            "Authorization": f"Basic {base64.b64encode(auth_str.encode()).decode()}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }

    def get_pages(self, limit: int = 5000) -> List[Dict]:
        logging.info("🌐 Fetching Confluence pages...")

        url = f"{BASE_URL}/wiki/rest/api/content"
        params = {
            "type": "page",
            "expand": "body.storage,version,metadata, history",
            "limit": limit,
        }
        

        try:
            response = requests.get(url, headers=self.headers, params=params)
            response.raise_for_status()
            results = response.json().get("results", [])
        except Exception as e:
            logging.error(f"❌ Failed to fetch Confluence pages: {e}")
            return []

        pages = []
        filtered_results = []
        for page in results:

            title = page.get("title", "").lower()
            labels = [label.get("name", "").lower() for label in page.get("metadata", {}).get("labels", [])]
            creator = page.get("history", {}).get("createdBy", {}).get("email", "")
            
            if creator.endswith("@atlassian.com") or "noreply" in creator:
                logging.info(f"🛑 Skipping system/auto page: {title}")
                continue
            
            # Additional filtering if needed
            if (
                title == 'overview' or title == 'project plan' 
                or title == 'software development' or title == 'template - decision documentation'
                or title == 'template - product requirements' or title == 'template - meeting notes'
                or title.startswith("project plan") or "system" in labels or "auto-generated" in labels
            ):
                logging.info(f"🛑 Skipping filtered page: {title}")
                continue
            logging.info(f"Processing page: {title}")
            filtered_results.append(page)
        # ✅ Only keep meaningful pages
        pages.extend(filtered_results)
        
        return self._transform_pages(pages)
    
    def _transform_pages(self, raw_pages: List[dict]) -> List[dict]:
        """Converts raw Confluence pages into simplified vector-ready format."""
        transformed = []
        
        for page in raw_pages:
            title = page.get("title", "")
            page_id = page.get("id", "")
            
            # Extract text content from HTML
            html_content = ""
            try:
                html_content = page.get("body", {}).get("storage", {}).get("value", "")
            except Exception:
                html_content = ""
            
            text_content = strip_html(html_content) if html_content else ""
            full_text = f"{title}\n\n{text_content}".strip()
            
            transformed.append({
                "id": page_id,
                "text": full_text,
                "metadata": {
                    "title": title,
                    "page_id": page_id,
                    "url": page.get("_links", {}).get("webui", ""),
                    "type": page.get("type", ""),
                    "status": page.get("status", ""),
                    "created": page.get("history", {}).get("createdDate", ""),
                    "creator": page.get("history", {}).get("createdBy", {}).get("displayName", ""),
                    "version": page.get("version", {}).get("number", 0),
                    "source": "confluence",
                    "embedding_version": "bge-v1.5"
                }
            })
        
        return transformed

def strip_html(html: str) -> str:
    """Very basic HTML tag stripper."""
    from bs4 import BeautifulSoup
    return BeautifulSoup(html, "html.parser").get_text(separator="\n").strip()
