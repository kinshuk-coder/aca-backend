import json
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage

# Import your compiled LangGraph agent from main.py
from main import ai_agent 

app = FastAPI(title="Autonomous Coding Agent API")

# 1. CORS Configuration
# This allows your React frontend (on Vercel or Localhost) to talk to this backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "https://your-vercel-app.vercel.app"], # Add your domains here
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 2. Define the expected request payload
class ChatRequest(BaseModel):
    message: str
    # In a production app, you would also pass a thread_id or message history here
    # to maintain state across different HTTP requests.

# 3. The Streaming Endpoint
@app.post("/api/chat")
async def chat_endpoint(request: ChatRequest):
    
    async def event_generator():
        # Initialize the input for the agent
        inputs = {"messages": [HumanMessage(content=request.message)]}
        
        try:
            # Stream events from LangGraph
            for event in ai_agent.stream(inputs):
                for node_name, state_update in event.items():
                    
                    # Handle both single messages and lists of messages safely
                    new_messages = state_update.get("messages", [])
                    if not isinstance(new_messages, list):
                        new_messages = [new_messages]
                        
                    for msg in new_messages:
                        # EVENT TYPE 1: The Agent decides to run a tool
                        if isinstance(msg, AIMessage) and hasattr(msg, 'tool_calls') and msg.tool_calls:
                            yield f"data: {json.dumps({'type': 'action', 'content': msg.tool_calls})}\n\n"
                        
                        # EVENT TYPE 2: The Agent sends a conversational message
                        elif isinstance(msg, AIMessage) and msg.content:
                            yield f"data: {json.dumps({'type': 'message', 'content': msg.content})}\n\n"
                                
                        # EVENT TYPE 3: The Tool finishes executing and returns results
                        elif isinstance(msg, ToolMessage):
                            yield f"data: {json.dumps({'type': 'tool_result', 'name': msg.name, 'content': msg.content})}\n\n"
            
            # Signal the React frontend that the stream is completely finished
            yield "data: [DONE]\n\n"
            
        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'content': str(e)})}\n\n"

    # Return the generator as a Server-Sent Events (SSE) stream
    return StreamingResponse(event_generator(), media_type="text/event-stream")