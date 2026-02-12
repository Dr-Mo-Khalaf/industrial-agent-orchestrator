"""
Main Application Entry Point
FastAPI Backend for the Industrial Agent Orchestrator.
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from app.agents.orchestrator import run_orchestrator
from app.infrastructure.logging.batch import batch_logger

# --- 1. API Models ---
class QueryRequest(BaseModel):
    query: str
    user_id: str = "engineer_01"  # In prod, this comes from Auth

class QueryResponse(BaseModel):
    status: str
    response: str
    audit_id: str

# --- 2. Initialize App ---
app = FastAPI(
    title="Industrial Agent Orchestrator",
    description="A multi-agent system for Field Engineers.",
    version="1.0.0"
)

# CORS Middleware (Allows Streamlit UI to talk to this backend)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- 3. Endpoints ---

@app.get("/")
def health_check():
    return {"status": "healthy", "service": "Industrial Orchestrator"}

@app.post("/query", response_model=QueryResponse)
def process_query(request: QueryRequest):
    """
    Main entry point for the Field Engineer's query.
    Triggers the Master Agent workflow.
    """
    try:
        # Invoke the Orchestrator (The Brain)
        result = run_orchestrator(request.query)
        
        # Generate Audit ID for traceability
        import uuid
        audit_id = str(uuid.uuid4())
        
        # Log the final result for Phase 4 (Governance)
        batch_logger.log({
            "audit_id": audit_id,
            "user_id": request.user_id,
            "query": request.query,
            "result_status": result.get("status")
        })

        return QueryResponse(
            status=result.get("status"),
            response=result.get("response"),
            audit_id=audit_id
        )
        
    except Exception as e:
        # Log the error internally
        print(f"Critical Error: {e}")
        raise HTTPException(status_code=500, detail="Internal Agent Error")

# To run: uvicorn main:app --reload


#### to display the graph
# ... (after the process_query function) ...
from fastapi.responses import HTMLResponse
@app.get("/graph", response_class=HTMLResponse)
def visualize_graph():
    """
    Generates a visual representation of the Master Agent's logic.
    """
    try:
        # Import the compiled graph from orchestrator
        from app.agents.orchestrator import app_graph
        
        # Generate Mermaid code
        mermaid_code = app_graph.get_graph().draw_mermaid()
        
        # Return HTML that renders the Mermaid code
        return f"""
        <html>
            <head>
                <script src="https://cdn.jsdelivr.net/npm/mermaid/dist/mermaid.min.js"></script>
            </head>
            <body>
                <h1>Industrial Agent Architecture</h1>
                <div class="mermaid">
                    {mermaid_code}
                </div>
                <script>mermaid.initialize({{'startOnLoad':true}});</script>
            </body>
        </html>
        """
    except Exception as e:
        return f"<html><body>Error generating graph: {str(e)}. <br> Ensure 'grandalf' is installed via pip.</body></html>"
    
#  Ensure you have installed the layout library: uv add grandalf
# Go to http://127.0.0.1:8000/graph