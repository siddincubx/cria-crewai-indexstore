#!/usr/bin/env python3
"""
Script to test JIRA ticket retrieval from an existing Pinecone index using VertexRAG.
This demonstrates how to query and retrieve similar JIRA tickets from your existing index.
Connects to an existing Pinecone index specified in the .env file.
"""

import os
import json
from typing import List, Dict, Any
from dotenv import load_dotenv
from pinecone import Pinecone
import vertexai
from vertexai.language_models import TextEmbeddingModel

def initialize_clients():
    """Initialize Pinecone and Vertex AI clients."""
    load_dotenv()
    
    # Initialize Vertex AI
    project_id = os.getenv("GOOGLE_CLOUD_PROJECT")
    if not project_id:
        raise ValueError("GOOGLE_CLOUD_PROJECT environment variable is required")
    
    vertexai.init(project=project_id)
    embedding_model = TextEmbeddingModel.from_pretrained("text-embedding-005")
    
    # Initialize Pinecone
    pinecone_api_key = os.getenv("PINECONE_API_KEY")
    if not pinecone_api_key:
        raise ValueError("PINECONE_API_KEY environment variable is required")
    
    pc = Pinecone(api_key=pinecone_api_key)
    
    return pc, embedding_model

def connect_to_existing_index(pc: Pinecone, index_name: str):
    """Connect to an existing Pinecone index for JIRA tickets."""
    try:
        # Check if index exists
        existing_indexes = [index.name for index in pc.list_indexes()]
        
        if index_name not in existing_indexes:
            raise ValueError(f"Index '{index_name}' does not exist. Please create it first in your Pinecone dashboard.")
        
        print(f"Connecting to existing index '{index_name}'...")
        index = pc.Index(index_name)
        
        # Get index stats to verify connection
        stats = index.describe_index_stats()
        print(f"Successfully connected to index '{index_name}'")
        print(f"Index stats: {stats.total_vector_count} vectors stored")
        
        return index
        
    except Exception as e:
        print(f"Error connecting to index: {e}")
        raise

def query_similar_tickets(index, embedding_model, query_text: str, top_k: int = 5):
    """Query the Pinecone index for tickets similar to the given query."""
    print(f"Searching for tickets similar to: '{query_text}'")
    print("-" * 60)
    
    try:
        # Generate embedding for the query
        embeddings = embedding_model.get_embeddings([query_text])
        query_vector = embeddings[0].values
        
        # Query Pinecone index
        results = index.query(
            vector=query_vector,
            top_k=top_k,
            include_metadata=True
        )
        
        if not results.matches:
            print("No similar tickets found.")
            return []
        
        # Display results
        similar_tickets = []
        for i, match in enumerate(results.matches, 1):
            score = match.score
            metadata = match.metadata
            
            print(f"\n{i}. Ticket ID: {metadata.get('ticket_id', 'N/A')}")
            print(f"   Similarity Score: {score:.4f}")
            print(f"   Summary: {metadata.get('summary', 'N/A')}")
            print(f"   Status: {metadata.get('status', 'N/A')}")
            print(f"   Priority: {metadata.get('priority', 'N/A')}")
            print(f"   Type: {metadata.get('type', 'N/A')}")
            print(f"   Components: {metadata.get('components', 'N/A')}")
            print(f"   Assignee: {metadata.get('assignee', 'N/A')}")
            print(f"   Description: {metadata.get('description', 'N/A')[:100]}...")
            
            similar_tickets.append({
                'ticket_id': metadata.get('ticket_id'),
                'score': score,
                'summary': metadata.get('summary'),
                'status': metadata.get('status'),
                'priority': metadata.get('priority'),
                'type': metadata.get('type'),
                'components': metadata.get('components'),
                'assignee': metadata.get('assignee'),
                'description': metadata.get('description')
            })
        
        return similar_tickets
        
    except Exception as e:
        print(f"Error querying tickets: {e}")
        return []

def run_sample_queries(index, embedding_model):
    """Run sample queries to demonstrate JIRA ticket retrieval."""
    sample_queries = [
        "authentication login issues SSO",
        "database performance slow queries",
        "mobile UI overlapping buttons",
        "API errors 500 server",
        "security file upload vulnerability"
    ]
    
    print("Running sample queries to demonstrate ticket retrieval:")
    print("=" * 60)
    
    for i, query in enumerate(sample_queries, 1):
        print(f"\nSample Query {i}:")
        similar_tickets = query_similar_tickets(index, embedding_model, query, top_k=3)
        
        if similar_tickets:
            print(f"Found {len(similar_tickets)} similar tickets")
        else:
            print("No similar tickets found")
        
        print("\n" + "="*60)

def main():
    """Main function to test JIRA ticket retrieval from existing index."""
    print("Testing JIRA Ticket Retrieval from Existing Pinecone Index")
    print("=" * 60)
    
    try:
        # Initialize clients
        pc, embedding_model = initialize_clients()
        
        # Connect to existing index
        index_name = os.getenv("PINECONE_INDEX_NAME", "jira-tickets")
        index = connect_to_existing_index(pc, index_name)
        
        # Run sample queries to demonstrate retrieval
        run_sample_queries(index, embedding_model)
        
        # Optional: Interactive query mode
        print("\n" + "="*60)
        print("Interactive Query Mode (Press Enter to skip)")
        print("="*60)
        
        while True:
            user_query = input("\nEnter your JIRA ticket query (or 'quit' to exit): ").strip()
            
            if not user_query or user_query.lower() == 'quit':
                break
                
            similar_tickets = query_similar_tickets(index, embedding_model, user_query, top_k=3)
            
            if similar_tickets:
                print(f"\nFound {len(similar_tickets)} similar tickets for your query.")
            else:
                print("\nNo similar tickets found for your query.")
        
        print(f"\nTesting complete! Your JIRA Agent can now query index '{index_name}' for similar tickets.")
        print("The JIRA Ticket Search tool uses the same VertexRAG Engine and Pinecone index.")
        
    except Exception as e:
        print(f"Testing failed: {e}")
        print("Please check your environment variables, API keys, and ensure your Pinecone index exists and has data.")

if __name__ == "__main__":
    main()
