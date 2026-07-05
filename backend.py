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
                    if not state_update or not isinstance(state_update, dict):
                        continue
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

class HistoryQuery(BaseModel):
    thread_id : str

@app.post("/api/get_history")
def get_history(query : HistoryQuery):

    config = {
        "configurable":{
            "thread_id":query.thread_id
        }
    }

    try:

        state = ai_agent.get_state(config=config)

        # FIX: Safely catch if state or state.values is completely None
        if not state or not getattr(state, "values", None):
            return {"messages": []}
                
        messages = state.values["messages"]

        formatted_messages = []

        for msg in messages:

            if isinstance(msg,HumanMessage):
                formatted_messages.append({
                    "role":"user",
                    "type":"message",
                    "content":msg.content
                })
            elif isinstance(msg,AIMessage):

                if(msg.content):
                    formatted_messages.append({
                        "role":"assistant",
                        "type":"message",
                        "content":msg.content
                    })

                if hasattr(msg,"tool_calls") and msg.tool_calls:
                    formatted_messages.append({
                        "role":"assistant",
                        "type":"action",
                        "content":msg.tool_calls
                    })

                    

            elif isinstance(msg,ToolMessage):

                formatted_messages.append({
                    "role":"assistant",
                    "type":"tool_result",
                    "name":msg.name,
                    "content":msg.content
                })

        return {"messages":formatted_messages}                
                
    except Exception as e:
        print("Error generating history : ",str(e))
        return ({"error":str(e)})


@app.get("/api/ping")    
def ping():
    return {"status":"ok"}

