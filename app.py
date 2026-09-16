import streamlit as st
import pandas as pd
from agent import process_query

st.set_page_config(page_title="Text-to-SQL Agent", layout="wide")
st.title("Text-to-SQL Agent")

if "messages" not in st.session_state:
    st.session_state.messages = []

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        if "dataframe" in msg:
            st.dataframe(msg["dataframe"])
            if "sql_query" in msg:
                with st.expander("View generated SQL"):
                    st.code(msg["sql_query"], language="sql")
        else:
            st.markdown(msg["content"])

with st.sidebar:
    db_path = ""
    host = ""
    port = ""
    user = ""
    password = ""
    db_name = ""
    uri = ""
    selected_db = st.selectbox("Select database",["SQLite", "MySQL", "PostgreSQL"])
    if selected_db == "SQLite":
        db_path = st.text_input("Path to SQLite database file", value="data_jobs.sqlite")
    else:
        host = st.text_input("Host", value="localhost")
        default_port = "3306" if selected_db == "MySQL" else "5432"
        port = st.text_input("Port", value=default_port)
        user = st.text_input("User", value="root")
        password = st.text_input("Password", type="password") 
        db_name = st.text_input("Database Name")
    
    if st.button("Connect"):
        if selected_db == "SQLite":
            uri = f"sqlite:///{db_path}"
        elif selected_db == "MySQL":
            uri = f"mysql+pymysql://{user}:{password}@{host}:{port}/{db_name}"
        elif selected_db == "PostgreSQL":
            uri = f"postgresql+psycopg2://{user}:{password}@{host}:{port}/{db_name}"

        st.session_state.db_uri = uri
        st.success("Db connected")

if "db_uri" in st.session_state:
    if user_prompt := st.chat_input("Ask a question in simple text"):
        
        with st.chat_message("user"):
            st.markdown(user_prompt)
        
        st.session_state.messages.append({"role": "user", "content": user_prompt})
        
        with st.chat_message("assistant"):
            with st.status("Processing query") as status:
                result_dict = process_query(user_prompt, st.session_state.db_uri)

                for msg in result_dict.get("history", []):
                    st.write(msg)
                
                status.update(label="Processing query... Done", state="complete", expanded=False)
            
            if result_dict.get("error"):
                er_text = f"Error: {result_dict['error']}"
                st.error(er_text)
                st.session_state.messages.append({"role": "assistant", "content": er_text})
            else:
                df = result_dict.get("result")
                st.dataframe(df)

                st.session_state.messages.append({
                    "role": "assistant", 
                    "dataframe": df,
                    "sql_query": result_dict.get("sql_query")
                })
                
                with st.expander("View generated SQL"):
                    st.code(result_dict.get("sql_query"), language="sql")
else:
    st.info("Configure your database in the sidebar and click Connect.")
