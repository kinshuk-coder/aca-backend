from pydantic import BaseModel
from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from langchain_core.messages import HumanMessage,AIMessage,ToolMessage
from fastapi.middleware.cors import CORSMiddleware
import json
import asyncio

from main import ai_agent

app = FastAPI(title="FastAPI AI-Coding Agent API")

app.add_middleware(
    CORSMiddleware,
    allow_origins = ["http://localhost:5173"],
    allow_credentials = True,
    allow_headers = ["*"],
    allow_methods = ["*"]
)

class user_query(BaseModel):
    message : str
    thread_id : str

@app.post("/api/chat")
async def chat(query : user_query):
    input = query.message

    config = {
        "configurable": {
            "thread_id":query.thread_id
        }
    }

    async def streaming_event():

        try:

            for event in ai_agent.stream({"messages":[HumanMessage(input)]},config=config):

                for node_name,state_update in event.items():
                    new_message = state_update.get("messages",[])
                    if not isinstance(new_message, list):
                        new_message = [new_message]

                    for msg in new_message:

                        await asyncio.sleep(0.5)

                        if isinstance(msg,AIMessage) and hasattr(msg,"tool_calls") and msg.tool_calls:
                            yield f"data: {json.dumps({'type' : 'action','content':msg.tool_calls })}\n\n"

                        elif isinstance(msg,AIMessage) and hasattr(msg,"content"):
                            yield f"data: {json.dumps({'type':'message','content':msg.content})}\n\n"  

                        elif isinstance(msg,ToolMessage):
                            yield f"data: {json.dumps({'type':'tool_result','name':msg.name,'content':msg.content})}\n\n"

        except Exception as e:
            yield f"data: {json.dumps({'type':'error','content':str(e)})}\n\n"                    

        

    return StreamingResponse(streaming_event(),media_type="text/event-stream")                    


