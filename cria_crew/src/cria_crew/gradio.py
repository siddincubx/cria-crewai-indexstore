import gradio as gr
import threading
import time
from datetime import datetime
from typing import List, Tuple, Optional
import os

try:
    from cria_crew.crew import CriaCrew
    from crewai.agents.agent_builder.base_agent_executor_mixin import CrewAgentExecutorMixin
except ImportError:
    # For standalone execution
    import sys
    sys.path.append(os.path.dirname(os.path.dirname(__file__)))
    from cria_crew.crew import CriaCrew
    from crewai.agents.agent_builder.base_agent_executor_mixin import CrewAgentExecutorMixin

class CrewChatbot:
    def __init__(self):
        self.crew = CriaCrew()
        self.user_input = None
        self.crew_started = False
        self.pending_responses = []
        self.setup_human_input_patch()
    
    def setup_human_input_patch(self):
        """Setup the human input patch for interactive tasks"""
        def custom_ask_human_input(self, final_answer: str) -> str:
            # Store the final answer for display
            chatbot.pending_responses.append(("assistant", final_answer))
            
            prompt = "🔄 Please provide feedback on the Final Result and the Agent's actions:"
            chatbot.pending_responses.append(("system", prompt))
            
            # Wait for user input
            while chatbot.user_input is None:
                time.sleep(0.5)
            
            human_comments = chatbot.user_input
            chatbot.user_input = None
            return human_comments
        
        # Apply the patch
        CrewAgentExecutorMixin._ask_human_input = custom_ask_human_input
        
        # Store reference for the patch
        global chatbot
        chatbot = self

def create_chatbot_interface():
    """Create and configure the Gradio chatbot interface"""
    
    chatbot_instance = CrewChatbot()
    
    def process_crew_request(message: str):
        """Process message with CrewAI in background thread"""
        chatbot_instance.crew_started = True
        chatbot_instance.pending_responses = []
        
        try:
            # Prepare inputs for the crew
            inputs = {
                'query': message
            }
            
            # Create crew instance and run
            crew_instance = chatbot_instance.crew.crew()
            result = crew_instance.kickoff(inputs=inputs)
            
            # Process the final result
            try:
                if hasattr(result, 'raw') and result.raw:
                    response = str(result.raw)
                elif hasattr(result, 'tasks_output') and result.tasks_output:
                    last_task = result.tasks_output[-1]
                    if hasattr(last_task, 'raw'):
                        response = str(last_task.raw)
                    else:
                        response = str(last_task)
                else:
                    response = str(result)
                    
                if not response or response.strip() == "":
                    response = "✅ Task completed successfully! Check the output folder for any generated files."
                
                chatbot_instance.pending_responses.append(("assistant", f"🎯 Final Result:\n{response}"))
                
            except Exception as e:
                error_msg = f"⚠️ Task completed with some processing issues: {str(e)[:200]}..."
                chatbot_instance.pending_responses.append(("assistant", error_msg))
            
        except Exception as e:
            error_message = f"❌ Sorry, I encountered an error: {str(e)}"
            chatbot_instance.pending_responses.append(("assistant", error_message))
        
        finally:
            chatbot_instance.crew_started = False
    
    def chat_fn(message, history):
        """Function to handle chat interactions"""
        if not message.strip():
            return history, ""
        
        # If crew is not running, start new request
        if not chatbot_instance.crew_started:
            # Start crew processing in background thread
            thread = threading.Thread(target=process_crew_request, args=(message,))
            thread.daemon = True
            thread.start()
            
            # Add user message and initial response
            history.append((message, "🤖 Processing your request with CRIA Crew... This may take a moment."))
            return history, ""
        
        else:
            # Crew is running and waiting for human input
            chatbot_instance.user_input = message
            history.append((message, "✅ Feedback received. Continuing processing..."))
            return history, ""
    
    def update_chat(history):
        """Update chat with pending responses from crew"""
        if chatbot_instance.pending_responses:
            for role, response in chatbot_instance.pending_responses:
                if role == "assistant":
                    # Update the last "Processing..." message or add new response
                    if history and "Processing your request" in history[-1][1]:
                        history[-1] = (history[-1][0], response)
                    else:
                        history.append(("", response))
                elif role == "system":
                    history.append(("", response))
            
            chatbot_instance.pending_responses = []
        
        return history
    
    def clear_chat():
        """Clear the chat history"""
        chatbot_instance.user_input = None
        chatbot_instance.pending_responses = []
        return []
    
    # Create the Gradio interface
    with gr.Blocks(
        title="CRIA Crew AI Assistant",
        css="""
        .gradio-container {
            max-width: 1200px !important;
        }
        .chat-message {
            border-radius: 10px;
            padding: 10px;
            margin: 5px 0;
        }
        """
    ) as demo:
        
        gr.Markdown(
            """
            # 🤖 CRIA Crew AI Assistant
            
            Welcome to your intelligent assistant powered by CrewAI! I can help you with:
            - 🎫 **JIRA Search**: Find and analyze JIRA tickets and issues
            - 📚 **Confluence Knowledge**: Search through Confluence documentation  
            - 💻 **Codebase Analysis**: Analyze and understand your codebase
            - 📊 **Reporting**: Generate comprehensive reports combining all sources
            
            Simply ask me anything and I'll coordinate with my specialized agents to provide you with the best answer!
            
            ---
            ### 🚀 Quick Start Tips:
            - Be specific in your queries for better results
            - If I ask for feedback during processing, provide your input to continue
            - Check the output folder for any generated reports or files
            """
        )
        
        with gr.Row():
            with gr.Column(scale=3):
                chatbot = gr.Chatbot(
                    label="💬 Chat with CRIA Crew",
                    height=600,
                    show_label=True,
                    avatar_images=("👤", "🤖"),
                    bubble_full_width=False,
                    show_copy_button=True
                )
                
                with gr.Row():
                    msg = gr.Textbox(
                        placeholder="Ask me about JIRA tickets, Confluence docs, codebase analysis, or request a report...",
                        container=False,
                        scale=4,
                        lines=2,
                        max_lines=5,
                        show_label=False
                    )
                    send_btn = gr.Button("Send 📤", variant="primary", scale=1)
                
                with gr.Row():
                    clear_btn = gr.Button("Clear Chat 🗑️", variant="secondary")
                    refresh_btn = gr.Button("Refresh 🔄", variant="secondary")
                    
            with gr.Column(scale=1):
                gr.Markdown(
                    """
                    ### 💡 Example Queries:
                    
                    **🎫 JIRA Related:**
                    ```
                    Find all open bugs in the training system
                    Show me tickets about seat limits
                    What are recent feature requests?
                    ```
                    
                    **📚 Confluence:**
                    ```
                    Find user management documentation
                    Search for API guidelines
                    Show training procedures
                    ```
                    
                    **💻 Codebase:**
                    ```
                    Analyze the authentication system
                    Find enrollment-related functions
                    Review the database schema
                    ```
                    
                    **📊 Reports:**
                    ```
                    Create a training system analysis report
                    Generate development activity summary
                    Analyze recent system changes
                    ```
                    
                    ---
                    ### 🔄 Status:
                    - **Green**: Ready for new requests
                    - **Yellow**: Processing your request
                    - **Blue**: Waiting for your feedback
                    """
                )
        
        # Event handlers
        msg.submit(chat_fn, [msg, chatbot], [chatbot, msg])
        send_btn.click(chat_fn, [msg, chatbot], [chatbot, msg])
        clear_btn.click(clear_chat, outputs=[chatbot])
        refresh_btn.click(update_chat, [chatbot], [chatbot])
        
        # Auto-refresh to show pending responses
        demo.load(lambda: None, every=2).then(
            update_chat, [chatbot], [chatbot]
        )
        
        # Example buttons for quick access
        with gr.Row():
            example_btns = [
                gr.Button("🎫 Find JIRA Issues", size="sm"),
                gr.Button("📚 Search Confluence", size="sm"), 
                gr.Button("💻 Analyze Code", size="sm"),
                gr.Button("📊 Generate Report", size="sm")
            ]
        
        # Example button handlers
        example_btns[0].click(
            lambda: "Find all open JIRA tickets related to the training management system",
            outputs=[msg]
        )
        example_btns[1].click(
            lambda: "Search Confluence for user management and authentication documentation",
            outputs=[msg]
        )
        example_btns[2].click(
            lambda: "Analyze the codebase for authentication, enrollment, and user management patterns",
            outputs=[msg]
        )
        example_btns[3].click(
            lambda: "Generate a comprehensive analysis report on the current state of the training management system",
            outputs=[msg]
        )
        
        # Welcome message
        demo.load(
            lambda: [[("", "👋 Welcome! I'm CRIA, your AI Impact Analyzer. What topic would you like me to research today?")]],
            outputs=[chatbot]
        )
    
    return demo

def launch_chatbot(share=False, server_port=7860, server_name="127.0.0.1", debug=False):
    """Launch the Gradio chatbot interface"""
    
    print("🚀 Starting CRIA Crew AI Chatbot...")
    print(f"📍 Server will be available at: http://{server_name}:{server_port}")
    print("💡 Tip: Use Ctrl+C to stop the server")
    
    demo = create_chatbot_interface()
    
    try:
        demo.launch(
            share=share,
            server_port=server_port,
            server_name=server_name,
            show_error=True,
            debug=debug,
            inbrowser=True,
            favicon_path=None
        )
    except Exception as e:
        print(f"❌ Error launching chatbot: {e}")
        print("💡 Try changing the port with: launch_chatbot(server_port=7861)")
        raise

def main():
    """Main function to run the chatbot"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Launch CRIA Crew AI Chatbot")
    parser.add_argument("--port", type=int, default=7860, help="Port to run the server on")
    parser.add_argument("--host", type=str, default="127.0.0.1", help="Host to run the server on")
    parser.add_argument("--share", action="store_true", help="Create a public link")
    parser.add_argument("--debug", action="store_true", help="Enable debug mode")
    
    args = parser.parse_args()
    
    launch_chatbot(
        share=args.share,
        server_port=args.port,
        server_name=args.host,
        debug=args.debug
    )

if __name__ == "__main__":
    main()
