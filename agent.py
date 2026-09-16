import os
import pandas as pd
from typing import List, TypedDict
import typing
from langgraph.graph import StateGraph, END
from langchain_community.utilities import SQLDatabase
from langchain_openai import ChatOpenAI
from langchain_classic.chains import create_sql_query_chain
from sqlalchemy import create_engine

os.environ["OPENAI_API_KEY"] = "lm-studio"
os.environ["OPENAI_API_BASE"] = "http://localhost:1234/v1"
llm = ChatOpenAI(model="local-model", temperature=0)

class AgentState(TypedDict):
    question: str
    sql_query: str
    error: str
    result: typing.Any
    iterations: int
    history: List[str]
    db_uri: str

def write_sql(state: AgentState):
    print(f"[EXECUTING] write_sql | Iteration: {state.get('iterations', 0)}")
    
    db = SQLDatabase.from_uri(state["db_uri"])
    chain = create_sql_query_chain(llm, db)
    
    if state.get("error"):
        prompt = (
            f"Question: {state['question']}\n"
            f"Previous SQL: {state['sql_query']}\n"
            f"Database Error: {state['error']}\n"
            f"Fix the SQL query to resolve the error."
        )
    else:
        prompt = state["question"]
        
    response = chain.invoke({"question": prompt})
    clean_sql = response.replace("```sql", "").replace("```", "").strip()

    if "SELECT " in clean_sql.upper():
        start_idx = clean_sql.upper().find("SELECT ")
        clean_sql = clean_sql[start_idx:]
        
    if ";" in clean_sql:
        end_idx = clean_sql.find(";") + 1
        clean_sql = clean_sql[:end_idx]
        
    print(f"  -> Generated SQL: {clean_sql}")
    
    c_hist = state.get("history", [])
    new_msg = f"?? Iteration {state.get('iterations', 0)}: Generated SQL query"

    return {
        "sql_query": clean_sql, 
        "error": "", 
        "iterations": state.get("iterations", 0) + 1,
        "history": c_hist + [new_msg],
        "db_uri": state["db_uri"] 
    }

def execute_sql(state: AgentState):
    print("[EXECUTING] execute_sql | Executing query...")
    query = state["sql_query"].upper()
    
    if "DROP" in query or "DELETE" in query or "UPDATE" in query or "INSERT" in query or "ALTER" in query:
        print(f"Execution Failed: Unsafe operation")
        c_hist = state.get("history", [])
        return {
            "error": "Unsafe SQL operation detected. Only SELECT queries are allowed",
            "history": c_hist + ["?? Blocked unsafe SQL query!"],
            "db_uri": state["db_uri"]
        }
    
    try:
        engine = create_engine(state["db_uri"])
        result = pd.read_sql_query(state["sql_query"], engine)
        print("Query executed successfully.")
        
        c_hist = state.get("history", [])
        new_msg = "? Data collected successfully"
        return {
            "result": result, 
            "error": "", 
            "history": c_hist + [new_msg],
            "db_uri": state["db_uri"]
        }
    except Exception as e:
        error_msg = str(e)
        print(f"Execution Failed: {error_msg}")
        
        c_hist = state.get("history", [])
        new_msg = f"?? Database Error: {error_msg}. Attempting to fix..."
        return {
            "error": error_msg, 
            "history": c_hist + [new_msg],
            "db_uri": state["db_uri"]
        }

def should_continue(state: AgentState):
    if state.get("iterations", 0) >= 5:
        return "end"
    if state.get("error"):
        return "retry"
    return "end"

workflow = StateGraph(AgentState)
workflow.add_node("write_sql", write_sql)
workflow.add_node("execute_sql", execute_sql)
workflow.set_entry_point("write_sql")
workflow.add_edge("write_sql", "execute_sql")
workflow.add_conditional_edges("execute_sql", should_continue, {"retry": "write_sql", "end": END})

app = workflow.compile()

def process_query(user_question: str, db_uri: str) -> dict:
    final_state = app.invoke({
        "question": user_question,
        "sql_query": "",
        "error": "",
        "result": None,
        "iterations": 0,
        "history": [],
        "db_uri": db_uri
    })
    return final_state
