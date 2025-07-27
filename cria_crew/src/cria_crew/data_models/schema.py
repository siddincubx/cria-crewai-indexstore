from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional, Union


class JiraTicket(BaseModel):
    """
    Represents a JIRA ticket with its details.
    """
    key: str = Field(..., description="The unique identifier for the JIRA ticket.")
    summary: str = Field(..., description="A brief summary of the JIRA ticket.")
    ticket_url: str = Field(..., description="The URL to access the JIRA ticket.")
    status: str = Field(..., description="The current status of the JIRA ticket.")
    assignee: str = Field(..., description="The user assigned to the JIRA ticket.")
    created: str = Field(..., description="The date and time when the JIRA ticket was created.")
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional metadata associated with the JIRA ticket."
    )

class JiraOutputSchema(BaseModel):
    """
    Schema for JIRA output.
    """
    results: List[JiraTicket] = Field(
        default_factory=list,
        description="List of JIRA issues returned by the search."
    )
    analysis: str = Field(
        default="",
        description="Analysis of the JIRA issues, if applicable."
    )

class ConfluencePage(BaseModel):
    """
    Represents a Confluence page with its details.
    """
    page_title: str = Field(..., description="The title of the Confluence page.")
    page_url: Optional[str] = Field(..., description="The URL to access the Confluence page. None if not present.")
    page_content: str = Field(..., description="The content of the Confluence page.")

class ConfluenceOutputSchema(BaseModel):
    """
    Schema for Confluence output.
    """
    results: List[ConfluencePage] = Field(
        default_factory=list,
        description="List of Confluence pages returned by the search."
    )
    analysis: str = Field(
        default="",
        description="Analysis of the Confluence pages, if applicable."
    )

class CodeBaseFile(BaseModel):
    """
    Represents a file in the codebase.
    """
    filename: str = Field(..., description="The name or full path of the file.")
    start: int = Field(..., description="The starting line number of the code snippet.")
    end: int = Field(..., description="The ending line number of the code snippet.")
    snippet: str = Field(..., description="The code snippet of the file.")

class CodeBaseAnalysis(BaseModel):
    """
    Represents the analysis of a codebase.
    """
    analysis: str = Field(..., description="Identification of issue and relationships between components")
    files: List[CodeBaseFile] = Field(default_factory=list, description="List of files analyzed in the codebase.")

class SourceItem(BaseModel):
    source: str = Field(..., description="The source of the item (e.g., 'JIRA', 'Confluence', 'Codebase').")
    content: List[Union[ConfluenceOutputSchema,JiraOutputSchema,CodeBaseAnalysis]] = Field(..., description="The content of the item.")


class FinalOutputSchema(BaseModel):
    """
    Final output schema that combines JIRA and Confluence outputs.
    """
    output: List[SourceItem] = Field(
        default_factory=list,
        description="Combined output from JIRA and Confluence searches."
    )
    analysis: str = Field(
        default="",
        description="Final analysis based on the combined outputs."
    )
    