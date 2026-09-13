import os
import pandas as pd
import sqlite3
from typing import List, TypedDict
import typing
from langgraph.graph import StateGraph, END
from langchain_community.utilities import SQLDatabase
from langchain_openai import ChatOpenAI
from langchain_classic.chains import create_sql_query_chain

db_path = "data_jobs.sqlite"
db = SQLDatabase.from_uri(f"sqlite:///{db_path}")

os.environ["OPENAI_API_KEY"] = "lm-studio"
os.environ["OPENAI_API_BASE"] = "http://localhost:1234/v1"
llm = ChatOpenAI(model="local-model", temperature=0)

class AgentState(TypedDict):
    question: str
    sql_query: str
    error: str
    result: typing.Any
    iterations: int
    history : List[str]

def write_sql(state: AgentState):
    print(f"[EXECUTING] write_sql | Iteration: {state.get('iterations', 0)}")
    
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
    new_msg = f"Iteration{state.get('iterations', 0)} : Generated sql query"

   
    
    return {
        "sql_query": clean_sql, 
        "error": "", 
        "iterations": state.get("iterations", 0) + 1,
        "history": c_hist + [new_msg]
    }

def execute_sql(state: AgentState):
    print("[EXECUTING] execute_sql | Executing query...")
    query = state["sql_query"].upper()
    if "DROP" in query or "DELETE" in query or "UPDATE" in query or "INSERT"  in query or "ALTER" in query :
        print(f"Execution Failed: ")
        return {"error" : "Unsafe SQL operation detected. Only SELECT queries are allowed"}
    
    
    try:
        connection = sqlite3.connect(db_path)
        result = pd.read_sql_query(state["sql_query"], connection)
        connection.close()
        print("Query executed successfully.")
        c_hist = state.get("history", [])
        new_msg = "Data collected successfully"
        return {"result": result, "error": "", "history": c_hist + [new_msg]}
    except Exception as e:
        error_msg = str(e)
        c_hist = state.get("history", [])
        new_msg = f"Execution Failed: {error_msg}"
        return {"error": error_msg, "history": c_hist + [new_msg]}

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

workflow.add_conditional_edges(
    "execute_sql",
    should_continue,
    {
        "retry": "write_sql",
        "end": END            
    }
)

app = workflow.compile()
def process_query(user_question: str) ->dict:
    final_state = app.invoke ({
        "question": user_question,
        "sql_query": "",
        "error": "",
        "result": "",
        "iterations": 0,
        "history": [],

    })

    return final_state
    
    
if __name__ == "__main__":
    question = "What are the 3 most common job titles in the 'United States'?"
    print(f"Querying: {question}\n")
    
    result = app.invoke({"question": question, "sql_query": "", "error": "", "result": "", "iterations": 0, "history": []})
    
    print("\n[FINAL RESULT]")
    print(result.get("result", "No result (Iteration limit exceeded)"))
