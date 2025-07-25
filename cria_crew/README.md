# CriaCrew Crew

Welcome to the CriaCrew Crew project, powered by [crewAI](https://crewai.com). This template is designed to help you set up a multi-agent AI system with ease, leveraging the powerful and flexible framework provided by crewAI. Our goal is to enable your agents to collaborate effectively on complex tasks, maximizing their collective intelligence and capabilities.

## Features

- **Research Agent**: Conducts thorough research on specified topics
- **Reporting Analyst**: Creates detailed reports based on research findings
- **JIRA Specialist**: Searches and analyzes JIRA tickets using vector embeddings and RAG (Retrieval-Augmented Generation)

## Installation

Ensure you have Python >=3.10 <3.14 installed on your system. This project uses [UV](https://docs.astral.sh/uv/) for dependency management and package handling, offering a seamless setup and execution experience.

First, if you haven't already, install uv:

```bash
pip install uv
```

Next, navigate to your project directory and install the dependencies:

(Optional) Lock the dependencies and install them by using the CLI command:
```bash
crewai install
```

## JIRA Ticket Search Setup

The JIRA Specialist agent uses Vertex AI and Pinecone to perform semantic search on JIRA tickets. To set this up:

1. **Copy the environment file**:
   ```bash
   cp .env.example .env
   ```

2. **Configure Pinecone**:
   - Sign up for a [Pinecone account](https://www.pinecone.io/)
   - Create a new index for your JIRA tickets (recommended: 768 dimensions for Vertex AI embeddings)
   - Add your API key and index name to the `.env` file

3. **Configure Vertex AI**:
   - Set up a Google Cloud Project with Vertex AI API enabled
   - Create a service account and download the JSON key file
   - Set the `GOOGLE_CLOUD_PROJECT` and `GOOGLE_APPLICATION_CREDENTIALS` in your `.env` file

4. **Prepare your JIRA data**:
   - Export your JIRA tickets and create embeddings using Vertex AI's `textembedding-gecko@003` model
   - Store the embeddings in your Pinecone index with metadata including ticket ID, summary, description, status, priority, etc.

### Environment Variables

Required environment variables (add to `.env` file):

```env
# Pinecone Configuration
PINECONE_API_KEY=your_pinecone_api_key_here
PINECONE_INDEX_NAME=jira-tickets

# Google Cloud / Vertex AI Configuration
GOOGLE_CLOUD_PROJECT=your_gcp_project_id_here
GOOGLE_APPLICATION_CREDENTIALS=path/to/your/service-account-key.json
```

### Customizing

**Add your `OPENAI_API_KEY` into the `.env` file**

- Modify `src/cria_crew/config/agents.yaml` to define your agents
- Modify `src/cria_crew/config/tasks.yaml` to define your tasks
- Modify `src/cria_crew/crew.py` to add your own logic, tools and specific args
- Modify `src/cria_crew/main.py` to add custom inputs for your agents and tasks

## Running the Project

To kickstart your crew of AI agents and begin task execution, run this from the root folder of your project:

```bash
$ crewai run
```

This command initializes the cria_crew Crew, assembling the agents and assigning them tasks as defined in your configuration.

This example, unmodified, will run the create a `report.md` file with the output of a research on LLMs in the root folder.

## Understanding Your Crew

The cria_crew Crew is composed of multiple AI agents, each with unique roles, goals, and tools. These agents collaborate on a series of tasks, defined in `config/tasks.yaml`, leveraging their collective skills to achieve complex objectives. The `config/agents.yaml` file outlines the capabilities and configurations of each agent in your crew.

### Available Agents

1. **Researcher**: Conducts thorough research on specified topics
2. **Reporting Analyst**: Creates detailed reports based on research findings  
3. **JIRA Specialist**: Uses the JIRA Ticket Search tool to find relevant tickets using semantic similarity

### JIRA Ticket Search Tool

The JIRA Specialist agent has access to a custom tool that:
- Uses Vertex AI embeddings to understand query semantics
- Searches Pinecone vector database for similar JIRA tickets
- Returns formatted results with ticket details, priorities, and relevance scores
- Provides insights about ticket patterns and relationships

## Support

For support, questions, or feedback regarding the CriaCrew Crew or crewAI.
- Visit our [documentation](https://docs.crewai.com)
- Reach out to us through our [GitHub repository](https://github.com/joaomdmoura/crewai)

## Support

For support, questions, or feedback regarding the CriaCrew Crew or crewAI.
- Visit our [documentation](https://docs.crewai.com)
- Reach out to us through our [GitHub repository](https://github.com/joaomdmoura/crewai)
- [Join our Discord](https://discord.com/invite/X4JWnZnxPb)
- [Chat with our docs](https://chatg.pt/DWjSBZn)

Let's create wonders together with the power and simplicity of crewAI.
