#!/usr/bin/env python3
"""
Sample script demonstrating how to use the JIRA Ticket Search tool directly.
This can be useful for testing the tool functionality before integrating with the crew.
"""

import os
from dotenv import load_dotenv
from src.cria_crew.tools.custom_tool import JiraTicketSearchTool

def main():
    # Load environment variables
    load_dotenv()
    
    # Check if required environment variables are set
    required_vars = ["PINECONE_API_KEY", "GOOGLE_CLOUD_PROJECT"]
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        print(f"Error: Missing required environment variables: {', '.join(missing_vars)}")
        print("Please ensure your .env file is properly configured.")
        return
    
    # Initialize the tool
    jira_tool = JiraTicketSearchTool()
    
    # Example queries
    test_queries = [
        "login authentication issues",
        "database performance problems",
        "UI bugs in mobile app",
        "API endpoint errors",
        "security vulnerabilities"
    ]
    
    print("JIRA Ticket Search Tool Demo")
    print("=" * 40)
    
    for query in test_queries:
        print(f"\nSearching for: '{query}'")
        print("-" * 30)
        
        try:
            results = jira_tool._run(query=query, top_k=3)
            print(results)
        except Exception as e:
            print(f"Error: {e}")
        
        print()

if __name__ == "__main__":
    main()
