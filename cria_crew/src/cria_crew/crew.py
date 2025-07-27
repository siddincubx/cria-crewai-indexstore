import os
from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from crewai.agents.agent_builder.base_agent import BaseAgent
from typing import List
from datetime import datetime
from cria_crew.data_models.schema import ConfluenceOutputSchema, FinalOutputSchema, JiraOutputSchema
from cria_crew.tools.file_writer import FileWriterTool
from .tools.jira_rag_tool import JiraSearchTool
from .tools.custom_tool import CodeBaseSearchTool
from .tools.confluence_rag_tool import ConfluenceRAGTool
# If you want to run a snippet of code before or after the crew starts,
# you can use the @before_kickoff and @after_kickoff decorators
# https://docs.crewai.com/concepts/crews#example-crew-class-with-decorators

from dotenv import load_dotenv
load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
CLAUDE_API_KEY = os.getenv("CLAUDE_API_KEY")
if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY environment variable is not set.")

from crewai import LLM

gem_llm = LLM(
    model="gemini/gemini-2.0-flash-lite",
    api_key=GEMINI_API_KEY
)
# from langfuse._client.get_client import get_client

# langfuse = get_client()

# import openlit
# openlit.init(tracer=langfuse.get_trace_url())
# openlit.init(disable_batch=True)

# Verify connection
# if langfuse.auth_check():
#     print("Langfuse client is authenticated and ready!")
# else:
#     print("Authentication failed. Please check your credentials and host.")

import panel as pn

chat_interface = pn.chat.ChatInterface()

from crewai.tasks.task_output import TaskOutput
def print_output(output: TaskOutput):
    message = output.raw
    chat_interface.send(message, user=output.agent, respond=False)

@CrewBase
class CriaCrew():
    """CriaCrew crew"""

    agents: List[BaseAgent]
    tasks: List[Task]

    # Learn more about YAML configuration files here:
    # Agents: https://docs.crewai.com/concepts/agents#yaml-configuration-recommended
    # Tasks: https://docs.crewai.com/concepts/tasks#yaml-configuration-recommended
    
    # If you would like to add tools to your agents, you can learn more about it here:
    # https://docs.crewai.com/concepts/agents#agent-tools
    
    @agent
    def jira_specialist(self) -> Agent:
        return Agent(
            config=self.agents_config['jira_specialist'], # type: ignore[index]
            tools=[JiraSearchTool()],
            verbose=True
        )

    @agent
    def confluence_specialist(self) -> Agent:
        return Agent(
            config=self.agents_config['confluence_specialist'], # type: ignore[index]
            tools=[ConfluenceRAGTool()],
            verbose=True
        )

    # @agent
    # def codebase_specialist(self) -> Agent:
    #     return Agent(
    #         config=self.agents_config['codebase_specialist'], # type: ignore[index]
    #         tools=[CodeBaseSearchTool()],
    #         verbose=True
    #     )

    @agent
    def reporting_analyst(self) -> Agent:
        return Agent(
            config=self.agents_config['reporting_analyst'], # type: ignore[index]
            verbose=True
        )

    @task
    def jira_search_task(self) -> Task:
        return Task(
            config=self.tasks_config['jira_search_task'], # type: ignore[index]
            output_pydantic=JiraOutputSchema
            # callback=print_output
        )

    @task
    def confluence_search_task(self) -> Task:
        return Task(
            config=self.tasks_config['confluence_search_task'], # type: ignore[index]
            output_pydantic=ConfluenceOutputSchema
            # callback=print_output
        )

    # @task
    # def codebase_analysis_task(self) -> Task:
    #     return Task(
    #         config=self.tasks_config['codebase_analysis_task'], # type: ignore[index]
    #         callback=print_output,
    #     )

    @task
    def reporting_task(self) -> Task:
        return Task(
            config=self.tasks_config['reporting_task'], # type: ignore[index]
            context=[self.jira_search_task(), self.confluence_search_task()], # type: ignore[index]
            output_pydantic=FinalOutputSchema         
        )

    @crew
    def crew(self) -> Crew:
        """Creates the CriaCrew crew"""
        # To learn how to add knowledge sources to your crew, check out the documentation:
        # https://docs.crewai.com/concepts/knowledge#what-is-knowledge

        return Crew(
            agents=self.agents, # Automatically created by the @agent decorator
            tasks=self.tasks, # Automatically created by the @task decorator
            process=Process.sequential,
            verbose=True,
            chat_llm=LLM(
                model="gpt-4o",
                api_key=OPENAI_API_KEY
            )
        )
