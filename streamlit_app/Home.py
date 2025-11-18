import streamlit as st

st.set_page_config(
    page_title="ReBio AI Suite",
    page_icon="🧬",
    layout="wide"
)

st.title("🧬 ReBio AI Suite")
st.markdown("""
Welcome to **ReBio Multi-Agent System** powered by:

- LangGraph
- GPT-4o
- BioMistral
- Neo4j GraphDB
- ESMFold
- ChromaDB Vector Search

### Choose a module from left sidebar:
- **Graph Assistant** → Ask disease/drug/protein questions  
- **Protein Analyzer** → Enter sequence → Structure + redesign + report  
""")
