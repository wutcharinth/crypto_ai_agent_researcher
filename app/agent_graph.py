import os
from typing import TypedDict, List
from langgraph.graph import StateGraph, END
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage
from dotenv import load_dotenv
from app.tools import fetch_crypto_data, calculate_technicals, fetch_crypto_news

# Load env variables
load_dotenv()

# Define State
class AgentState(TypedDict):
    coins: List[str]
    market_data: dict      # Snapshot for AI
    chart_data: dict       # History for Frontend
    news: List[dict]
    final_report: str

# Node Functions

def fetch_data_node(state: AgentState):
    """
    Fetches price data and news. Prepares chart data.
    """
    coins = state['coins']
    market_data = {}
    chart_data = {}
    
    print(f"Fetching data for {coins}...")
    for coin in coins:
        df = fetch_crypto_data(coin, limit=100)
        df = calculate_technicals(df)
        
        if not df.empty:
            # Snapshot for AI
            last_row = df.iloc[-1].to_dict()
            market_data[coin] = last_row
            
            # History for Chart (serialize for JSON)
            # keeping it simple: dates, close prices, and rsi
            chart_data[coin] = {
                "dates": df['timestamp'].dt.strftime('%Y-%m-%d %H:%M').tolist(),
                "prices": df['close'].tolist(),
                "rsi": df['rsi'].fillna(0).tolist(),
                "macd": df['macd'].fillna(0).tolist()
            }
    
    # Fetch News
    news = fetch_crypto_news()
    
    return {"market_data": market_data, "chart_data": chart_data, "news": news}

def generate_report_node(state: AgentState):
    """
    Uses Gemini to synthesize data and news into a professional report.
    """
    market_data = state['market_data']
    news = state['news']
    
    # Construct Professional Prompt
    prompt = f"""
    You are a Senior Institutional Crypto Analyst at a top-tier firm (like Grayscale or Fidelity). 
    Your constituents are sophisticated investors who want deep, actionable "alpha" with rigorous sourcing.
    
    **Market Data Snapshot:**
    {market_data}
    
    **News Headlines & Sources:**
    {news}
    
    **Instructions:**
    1. **Executive Summary**: A high-level synthesis of the market regime (e.g., "Macro-Driven Selloff", "Structural Accumulation").
    2. **Deep Dive Analysis**:
       - For EACH coin, analyze the **Confluence** of Price Action, Technicals (RSI/MACD), and News.
       - **CRITICAL**: You MUST cite your sources. If you mention a news event, link it immediately.
         - Format: "News Event description [Source Name](url)".
       - Highlight key support/resistance levels derived from the data.
    3. **Institutional Outlook**:
       - Give a clear **Bias** (e.g., "Risk-Off", "Neutral-Bullish").
       - Provide a "Watchlist" or "Key Level to Watch".
    4. **References Section**:
       - At the very bottom, include a "📚 References" section.
       - Bullet points of: `[Title](Link) - Source`.
    
    **Style & Tone**:
    - **Comprehensive**: Do not be brief. Be thorough.
    - **Professional**: Use financial terminology (e.g., "liquidity", "divergence", "macro headwinds").
    - **Objective**: Back up logic with data.
    
    **Output Format**:
    Use Markdown. Use Bold for emphasis. Use H2/H3 for structure.
    """
    
    llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash-exp", google_api_key=os.getenv("GOOGLE_API_KEY"))
    response = llm.invoke([HumanMessage(content=prompt)])
    
    return {"final_report": response.content}

def dispatch_node(state: AgentState):
    """
    Returns state for API to pick up.
    """
    return {}

# Graph Definition
workflow = StateGraph(AgentState)

workflow.add_node("fetch_data", fetch_data_node)
workflow.add_node("generate_report", generate_report_node)
workflow.add_node("dispatch", dispatch_node)

workflow.set_entry_point("fetch_data")
workflow.add_edge("fetch_data", "generate_report")
workflow.add_edge("generate_report", "dispatch")
workflow.add_edge("dispatch", END)

app = workflow.compile()
