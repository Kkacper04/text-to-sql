# Autonomous Text-to-SQL Data Analyst

An intelligent agent built with LangGraph and Streamlit that interacts with a local SQLite database. The system features a self-correction loop - if a generated SQL query fails, the agent automatically captures the database error and attempts to rewrite the query until execution succeeds.

## Key Features
- **Self-Correction Loop**: Utilizes LangGraph state machines to handle syntax errors or hallucinated column names autonomously.
- **Local LLM Integration**: Fully compatible with local models running via LM Studio, ensuring data privacy.
- **Security Guardrails**: Includes built-in safety checks that block destructive SQL operations (DROP, DELETE, UPDATE, INSERT, ALTER).
- **Streamlit Frontend**: Provides a chat interface that renders query results as interactive Pandas DataFrames.
- **Data Integration**: Pre-configured to ingest the Hugging Face data_jobs dataset.

## Architecture
The system follows a cyclic directed graph pattern:
1. User provides a natural language question.
2. The agent generates a SQL query based on the database schema.
3. Guardrails verify the query is read-only.
4. The execution node attempts to run the query via Pandas.
   - On success: Data is returned to the UI.
   - On failure: The error message is routed back to the SQL generation node for correction.

## Getting Started

### Prerequisites
- Python 3.11 or higher
- LM Studio with a local server running on http://localhost:1234/v1

### Installation
Clone the repository and set up the environment:
```bash
git clone https://github.com/Kkacper04/text-to-sql.git
cd text-to-sql
python -m venv venv
venv\Scripts\activate
pip install langchain langchain-community langchain-openai langgraph streamlit pandas sqlalchemy datasets
```

### Setup Database
Initialize the local SQLite database using the provided script. This will download a sample dataset and create `data_jobs.sqlite`.
```bash
python create_db.py
```

### Usage
Start the Streamlit web application:
```bash
streamlit run app.py
```
Navigate to the URL provided in your terminal to interact with the application.