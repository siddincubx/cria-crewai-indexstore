from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, Any, Optional
import asyncio
from datetime import datetime
import uvicorn
from cria_crew.crew import CriaCrew


app = FastAPI(title="CRIA API", description="API for the CRIA Crew")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

class QueryRequest(BaseModel):
    query: str
    additional_inputs: Optional[Dict[str, Any]] = {}

class QueryResponse(BaseModel):
    result: Dict[str, Any]

@app.post("/api/query", response_model=QueryResponse)
async def process_query(request: QueryRequest):
    try:
        # Prepare inputs
        inputs = {
            "query": request.query,
        }
        
        # Run the crew in a non-blocking way
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(None, lambda: CriaCrew().crew().kickoff(inputs=inputs))
        
        # Convert result to dictionary
        dict_result = result.to_dict()
        return {"result": dict_result}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

def start_server(host="0.0.0.0", port=80):
    uvicorn.run(app, host=host, port=port)

if __name__ == "__main__":
    start_server()










##### RUN LOCALLY WITH `crewai run` #####
# #!/usr/bin/env python
# import sys
# import warnings

# from datetime import datetime

# from cria_crew.crew import CriaCrew

# warnings.filterwarnings("ignore", category=SyntaxWarning, module="pysbd")

# # This main file is intended to be a way for you to run your
# # crew locally, so refrain from adding unnecessary logic into this file.
# # Replace with inputs you want to test with, it will automatically
# # interpolate any tasks and agents information

# def run():
#     """
#     Run the crew.
#     """
#     inputs = {
#         'query': 'update training mode',
#         'current_year': str(datetime.now().year)
#     }
    
#     try:
#         result = CriaCrew().crew().kickoff(inputs=inputs)
#         print(f"type of result: {type(result)}")
#         dict_result = result.to_dict()
#         print(dict_result)
#     except Exception as e:
#         raise Exception(f"An error occurred while running the crew: {e}")


# def train():
#     """
#     Train the crew for a given number of iterations.
#     """
#     inputs = {
#         "query": "AI LLMs",
#         'current_year': str(datetime.now().year)
#     }
#     try:
#         CriaCrew().crew().train(n_iterations=int(sys.argv[1]), filename=sys.argv[2], inputs=inputs)

#     except Exception as e:
#         raise Exception(f"An error occurred while training the crew: {e}")

# def replay():
#     """
#     Replay the crew execution from a specific task.
#     """
#     try:
#         CriaCrew().crew().replay(task_id=sys.argv[1])

#     except Exception as e:
#         raise Exception(f"An error occurred while replaying the crew: {e}")

# def test():
#     """
#     Test the crew execution and returns the results.
#     """
#     inputs = {
#         "topic": "AI LLMs",
#         "query": "AI LLMs",
#         "current_year": str(datetime.now().year)
#     }
    
#     try:
#         CriaCrew().crew().test(n_iterations=int(sys.argv[1]), eval_llm=sys.argv[2], inputs=inputs)

#     except Exception as e:
#         raise Exception(f"An error occurred while testing the crew: {e}")


######### PANEL INTERFACE #########
# import os
# from dotenv import load_dotenv
# import panel as pn

# load_dotenv()

# pn.extension(design="material")

# from cria_crew.crew import CriaCrew
# from cria_crew.crew import chat_interface
# import threading

# from crewai.agents.agent_builder.base_agent_executor_mixin import CrewAgentExecutorMixin
# import time

# def custom_ask_human_input(self, final_answer: str) -> str:
      
#     global user_input

#     chat_interface.send(final_answer, user="Assistant", respond=False)

#     prompt = "Please provide feedback on the Final Result and the Agent's actions: "
#     chat_interface.send(prompt, user="System", respond=False)

#     while user_input is None:
#         time.sleep(1)  

#     human_comments = user_input
#     user_input = None

#     return human_comments


# CrewAgentExecutorMixin._ask_human_input = custom_ask_human_input

# user_input = None
# crew_started = False

# def initiate_chat(message):
#     global crew_started
#     crew_started = True
    
#     try:
#         # Initialize crew with inputs
#         inputs = {"query": message}
#         crew = CriaCrew().crew()
#         result = crew.kickoff(inputs=inputs)
        
#         # Send results back to chat
#     except Exception as e:
#         chat_interface.send(f"An error occurred: {e}", user="Assistant", respond=False)
#     crew_started = False

# def callback(contents: str, user: str, instance: pn.chat.ChatInterface):
#     global crew_started
#     global user_input

#     if not crew_started:
#         thread = threading.Thread(target=initiate_chat, args=(contents,))
#         thread.start()

#     else:
#         user_input = contents

# chat_interface.callback = callback 

# # Send welcome message
# chat_interface.send(
#     "Welcome! I'm your AI Impact Analyzer, CRIA. What topic would you like me to research?",
#     user="Assistant",
#     respond=False
# )

# # Make it servable
# chat_interface.servable()