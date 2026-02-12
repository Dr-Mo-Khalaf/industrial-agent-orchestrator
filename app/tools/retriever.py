"""
Knowledge Retriever Tool (RAG)
Phase 1: Planning & Retrieval

Purpose: Interfaces with the Vector Database to retrieve technical context
from engineering manuals (PDFs).
"""

from typing import List, Optional
from langchain_community.vectorstores import Chroma
from langchain_openai import OpenAIEmbeddings
from app.infrastructure.config import settings # Assuming you have a config.py

class KnowledgeRetriever:
    """
    A wrapper class for the Vector Store.
    Abstracts the underlying database (Chroma vs Pinecone) from the Orchestrator.
    """
    
    def __init__(self, persist_directory: str = "./data/chroma_db"):
        """
        Initializes the connection to the Vector Database.
        """
        self.embeddings = OpenAIEmbeddings(openai_api_key=settings.OPENAI_API_KEY)
        
        # PROTOTYPE: Using ChromaDB for local agility
        self.db = Chroma(
            persist_directory=persist_directory, 
            embedding_function=self.embeddings
        )
        self.retriever = self.db.as_retriever(search_kwargs={"k": 3})

    def retrieve(self, query: str) -> str:
        """
        Searches the manuals for relevant context.
        
        Args:
            query (str): The user's technical question.
            
        Returns:
            str: A concatenated string of relevant document chunks.
        """
        try:
            docs = self.retriever.invoke(query)
            
            if not docs:
                return "No relevant manuals found."
            
            # Format the output for the LLM
            formatted_context = "\n\n---\n\n".join([d.page_content for d in docs])
            return formatted_context
            
        except Exception as e:
            return f"Error retrieving data: {str(e)}"

# --- Singleton Instance for the Orchestrator to use ---
# This prevents re-initializing the DB connection on every request
_retriever_instance = None

def get_retriever():
    global _retriever_instance
    if _retriever_instance is None:
        _retriever_instance = KnowledgeRetriever()
    return _retriever_instance

# Function signature expected by the Orchestrator
def rag_retriever(query: str) -> str:
    """
    Public interface function matching the Orchestrator's expectation.
    """
    instance = get_retriever()
    return instance.retrieve(query)

if __name__ == "__main__":
    # Test retrieval (Requires documents to be ingested first)
    print(rag_retriever("What is the H2S limit?"))