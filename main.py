import os
import subprocess
from langchain_openai import ChatOpenAI
from langchain_core.tools import tool
from langchain.agents import create_agent
from pymongo import MongoClient
from langgraph.checkpoint.mongodb import MongoDBSaver


llm = ChatOpenAI(api_key=os.getenv("MISTRAL_API_KEY"),
             base_url="https://api.mistral.ai/v1",
             model="codestral-2508",
             temperature=0.2)

mongo_client = MongoClient(os.getenv("MONGO_URI"))

mongo_saver = MongoDBSaver(mongo_client,db_name="aca_db")

@tool
def write_file(file_path : str , content : str) -> str :
    """Creates a new directory structure and writes text content to a file."""

    main_path = os.path.abspath("/app/ai_workspace")
    full_path=os.path.join(main_path,file_path)
    os.makedirs(os.path.dirname(full_path),exist_ok=True)
    try:
        with open(full_path,"w",encoding="utf-8") as f:
            f.write(content)
            return f"SUCCESS: Wrote file to {file_path}"
    except Exception as e:
        return f"ERROR: Failed to write file: {str(e)}"        

@tool
def run_terminal(command : str) -> str:

    """Executes a shell command inside the system and returns output or errors."""   

    main_path = os.path.abspath("/app/ai_workspace")
    try:
        result = subprocess.run(command,capture_output=True,shell=True,text=True,timeout=30,cwd=main_path)

        if(result.returncode==0):
            return f"COMMAND SUCCESS:\n{result.stdout}"
        
        else: return f"COMMAND FAILED (Exit Code {result.returncode}):\n{result.stderr}"
    except subprocess.TimeoutExpired:
        return "ERROR: Command timed out after 30 seconds."
    except Exception as e:
        return f"ERROR: Execution exception: {str(e)}"
    
tools = [write_file,run_terminal]    

system_instructions = ("You are an elite, autonomous Senior Python Developer agent running inside an isolated Linux Docker container.\n"
    "Your objective is to build robust, highly optimized, and PEP 8 compliant Python scripts based on user demands.\n"
    "Plan your steps logically. Create clean directory structures and modular Python files.\n"
    "ENVIRONMENT RULES:\n"
    "- You are in a secure Linux sandbox. You have full access to bash utilities and the Python environment.\n"
    "- Always create separate directory for each project.\n"
    "- Run all terminal commands relative to the current workspace directory.\n"
    "- If a Python script or terminal command fails, study the traceback, fix your code, and try again.\n"
    "- Strongly prefer Python's standard library (`json`, `csv`, `os`, `re`, `sqlite3`, etc.) before installing third-party packages.\n"
    "- If you MUST install a third-party package, you MUST use `uv pip install <package>` instead of standard pip to prevent timeouts.\n"
    "- Once you have successfully executed the code and verified the logic works, stop.\n" 
    "- NEVER attempt to test the frontend applications like Streamlit, Gradio, Reflex, etc. as they will crash the execution thread, instead just write the code for these apps and stop.\n"
    "- NEVER attempt to run the backend servers like Fastapi, Flask, Django, etc. as they will crash the execution thread, instead just write the code for these apps and stop.\n" 
    "- NEVER attempt to install or use heavy machine learning libraries like PyTorch, TensorFlow, Scikit-learn or Keras.\n"
    "- If the user asks for AI or ML features, you MUST use external APIs via the `requests` library.")

ai_agent = create_agent(model=llm,
                     system_prompt=system_instructions,
                     tools=tools,
                     checkpointer=mongo_saver
                     ).with_config({"recursion_limit":50})




