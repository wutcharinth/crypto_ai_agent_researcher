from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from typing import List
import uvicorn
import os
from dotenv import load_dotenv

from app.agent_graph import app as agent_app

load_dotenv()

# Setup FastAPI
app = FastAPI(title="Crypto AI Agent")
templates = Jinja2Templates(directory="app/templates")

# Request Model
class AnalyzeRequest(BaseModel):
    coins: List[str]

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/api/analyze")
async def run_analysis(request: AnalyzeRequest):
    print(f"Received analysis request for: {request.coins}")
    
    inputs = {"coins": request.coins}
    
    # Run Agent
    # Note: agent_app.invoke is synchronous usually, unless compiled with async
    # Since we are in an async FastAPI route, running blocking code might be an issue.
    # However, for this MVP we'll try direct invocation. If it blocks, we'd wrap in run_in_executor.
    formatted_coins = request.coins if request.coins else ["BTC"]
    inputs = {"coins": formatted_coins}
    
    try:
        # LangGraph invoke returns the final state
        result = await agent_app.ainvoke(inputs)
        final_report = result.get("final_report", "No report generated.")
        return {"status": "success", "report": final_report}
    except Exception as e:
        print(f"Error: {e}")
        return {"status": "error", "report": f"Analysis failed: {str(e)}"}

if __name__ == "__main__":
    # Get port from environment variable for Railway (default to 8000)
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("app.main:app", host="0.0.0.0", port=port, reload=True)
