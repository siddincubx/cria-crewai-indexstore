import os
import json
from openai import OpenAI
from dotenv import load_dotenv
 
load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
 
def clarify_requirement_if_needed(requirement: str, context: list) -> dict:
    context_text = "\n".join(context)
 
    system_prompt = """
You are an AI assistant helping with software change requests.
 
Your job is to:
1. Determine if the requirement is clear or vague based on the user's intent AND the provided context/documentation.
2. If vague, list the missing information and ask clarifying questions.
3. If clear, indicate that no clarification is needed.
 
Return response in this exact JSON format:
{
  "is_clear": true or false,
  "clarification_questions": ["..."]  # Only present if is_clear is false
}
"""
 
    user_prompt = f"""Requirement: {requirement}
 
Context:
{context_text}
"""
 
    response = client.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
    )
 
    try:
        content = response.choices[0].message.content
        if content is None:
            return {
                "is_clear": True,
                "clarification_questions": [],
                "error": "LLM returned None content"
            }
        return json.loads(content)
    except Exception as e:
        return {
            "is_clear": True,
            "clarification_questions": [],
            "error": f"Failed to parse LLM output as JSON: {str(e)}"
        }
 
# Adde new
def finalize_requirement(requirement: str, clarification_response: str) -> str:
    prompt = f"""
You are an assistant refining user requirements based on clarification.
 
Original requirement: "{requirement}"
Clarification provided: "{clarification_response}"
 
Rewrite the requirement with all necessary details included. Keep it clear and complete.
Only return the new finalized requirement as plain text.
"""
    response = client.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "You are refining vague requirements using user clarification."},
            {"role": "user", "content": prompt}
        ]
    )
    content = response.choices[0].message.content
    return content.strip() if content is not None else ""
 
 