import streamlit as st

st.set_page_config(
    page_title="ReBio AI Suite",
    page_icon="🧬",
    layout="wide"
)

st.title("🧬 ReBio AI Suite")
st.markdown("""
Welcome to **ReBio Multi-Agent System**, powered by:

- **LangGraph Multi-Agent Workflow**
- **GPT-4o** reasoning & summarization
- **BioMistral** scientific reasoning
- **Neo4j GraphDB** (Protein–Disease–TherapeuticProtein Knowledge Graph)
- **ESMFold** structure prediction
- **ChromaDB** vector-based embedding search

### Choose a module from the left sidebar:

- **Graph Assistant** → Ask questions about proteins, diseases, therapeutic proteins  
- **Protein Analyzer** → Input protein sequence → Structure + redesign + functional analysis  

---
This system supports **therapeutic protein–centric** workflows:
- Monoclonal antibodies  
- Cytokines  
- Fusion proteins  
- Enzyme replacement proteins  
- Peptide therapeutics  

""")

