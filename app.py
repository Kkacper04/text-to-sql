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

if user_prompt := st.chat_input("Ask a question in simple text"):
    with st.chat_message("user"):
        st.markdown(user_prompt)
    st.session_state.messages.append({"role": "user", "content": user_prompt})

    with st.chat_message("assistant"):
        with st.status("Processing query") as status:
            result_dict = process_query(user_prompt)

            for msg in result_dict.get("history", []):
                st.write(msg)
            status.update(label="Processing query... Done",state="complete",expanded=False)
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
