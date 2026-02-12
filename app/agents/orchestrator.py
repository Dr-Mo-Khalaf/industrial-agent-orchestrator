"""
Industrial Agent Orchestrator (The Master Agent)

This module defines the central state machine using LangGraph.
It manages the flow: Query -> Planning -> Tool Execution -> Draft -> Safety Check.
"""

from typing import TypedDict, Annotated, List, Optional
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode

# Internal Imports (Assuming these exist based on file structure)
from app.tools.simulator import calc_pressure_flow  # The Physics Tool
from app.tools.retriever import rag_retriever        # The Knowledge Tool
from app.agents.safety import SafetyCritic           # The Critic
from app.infrastructure.logging.stream import stream_logger
from app.infrastructure.logging.batch import batch_logger

# --- 1. Define the State ---
# This is the "Memory" of the workflow. It holds all data as it moves through the graph.

class AgentState(TypedDict):
    messages: Annotated[List[BaseMessage], "The conversation history"]
    query: str
    intent: str  # 'retrieval', 'calculation', or 'hybrid'
    retrieved_context: Optional[str]
    calculation_result: Optional[dict]
    draft_response: str
    safety_feedback: str
    is_safe: bool
    retries: int

# --- 2. Define the Nodes (The Workers) ---

def node_planner(state: AgentState):
    """
    The Master Agent. Analyzes intent and routes the query.
    """
    query = state["query"]
    stream_logger.log(f"[Master Agent] Analyzing query: {query}")

    # Initialize LLM (High reasoning model)
    llm = ChatOpenAI(model="gpt-4o", temperature=0)
    
    # Simple Routing Logic (In production, use structured output/function calling)
    # Heuristic: If numbers/units present -> Calculation needed
    if any(char.isdigit() for char in query) and ("psi" in query.lower() or "m3" in query.lower()):
        intent = "calculation"
    elif "safety" in query.lower() or "manual" in query.lower():
        intent = "retrieval"
    else:
        intent = "hybrid"

    stream_logger.log(f"[Master Agent] Intent classified as: {intent}")
    return {"intent": intent, "retries": state.get("retries", 0)}

def node_retriever(state: AgentState):
    """
    Worker: Handles Knowledge Retrieval (RAG).
    """
    query = state["query"]
    stream_logger.log(f"[RAG Tool] Searching manuals for: {query}")
    
    # Call the RAG interface (Mocked here for logic flow)
    context = rag_retriever(query)
    
    return {"retrieved_context": context}

def node_simulator(state: AgentState):
    """
    Worker: Handles Engineering Calculation (Physics).
    """
    query = state["query"]
    stream_logger.log(f"[Sim Tool] Running physics simulation...")
    
    # In a real app, we would extract params from the query using LLM
    # Mocking a result for the flow
    result = calc_pressure_flow(flow_rate=200) 
    
    return {"calculation_result": result}

def node_synthesizer(state: AgentState):
    """
    Worker: Combines Tool Outputs into a Coherent Draft Response.
    """
    stream_logger.log("[Synthesizer] Generating draft response...")
    
    # Construct the prompt based on available data
    prompt = f"""
    You are an Engineering Assistant. Answer the user query based on the following data:
    
    User Query: {state['query']}
    Retrieved Manual Context: {state.get('retrieved_context', 'N/A')}
    Simulation Result: {state.get('calculation_result', 'N/A')}
    
    Formulate a clear recommendation.
    """
    
    llm = ChatOpenAI(model="gpt-4o", temperature=0)
    response = llm.invoke(prompt)
    
    return {"draft_response": response.content}

def node_critic(state: AgentState):
    """
    Worker: The Safety Validator. Runs the 'Guardrails' logic.
    """
    draft = state["draft_response"]
    stream_logger.log("[Critic] Validating safety constraints...")
    
    # Call the Safety Agent (Imported from safety.py)
    is_safe, feedback = SafetyCritic().validate(draft)
    
    batch_logger.log({
        "event": "safety_check",
        "draft": draft,
        "is_safe": is_safe,
        "feedback": feedback
    })
    
    return {"is_safe": is_safe, "safety_feedback": feedback}

# --- 3. Define the Graph Logic (The Arrows) ---

def decide_path(state: AgentState):
    """
    Conditional Edge: Where do we go after Planning?
    """
    intent = state["intent"]
    if intent == "retrieval":
        return "retriever"
    elif intent == "calculation":
        return "simulator"
    else:
        return "retriever" # Hybrid defaults to retrieval first for context

def check_safety(state: AgentState):
    """
    Conditional Edge: Did we pass the Safety Check?
    """
    if state["is_safe"]:
        return "approved"
    else:
        # Check if we are stuck in a loop (max retries = 2)
        if state["retries"] >= 2:
            return "max_retries_exceeded"
        
        # Increment retry counter
        state["retries"] += 1
        return "rejected"

# --- 4. Build the Graph ---

workflow = StateGraph(AgentState)

# Add Nodes
workflow.add_node("planner", node_planner)
workflow.add_node("retriever", node_retriever)
workflow.add_node("simulator", node_simulator)
workflow.add_node("synthesizer", node_synthesizer)
workflow.add_node("critic", node_critic)

# Set Entry Point
workflow.set_entry_point("planner")

# Add Edges
# Planner -> (Conditional) -> Tools
workflow.add_conditional_edges(
    "planner",
    decide_path,
    {
        "retriever": "retriever",
        "simulator": "simulator"
    }
)

# Tools -> Synthesizer
workflow.add_edge("retriever", "synthesizer")
workflow.add_edge("simulator", "synthesizer")

# Synthesizer -> Critic
workflow.add_edge("synthesizer", "critic")

# Critic -> (Conditional) -> End OR Loop
workflow.add_conditional_edges(
    "critic",
    check_safety,
    {
        "approved": END,
        "rejected": "planner", # Loop back to planner with feedback
        "max_retries_exceeded": END
    }
)

# Compile the Graph
app_graph = workflow.compile()

# --- 5. Runner Function (The Interface for FastAPI) ---

def run_orchestrator(query: str):
    """
    Main function called by the API layer.
    """
    initial_state = {
        "messages": [HumanMessage(content=query)],
        "query": query
    }
    
    # Invoke the graph
    final_state = app_graph.invoke(initial_state)
    
    # Format Output for API
    if final_state.get("is_safe"):
        return {
            "status": "SUCCESS",
            "response": final_state["draft_response"],
            "audit_trail": final_state["messages"]
        }
    else:
        return {
            "status": "BLOCKED_BY_SAFETY",
            "reason": final_state["safety_feedback"],
            "response": final_state["draft_response"]
        }