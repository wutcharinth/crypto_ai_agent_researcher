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
    market_data: dict
    news: List[dict]
    final_report: str

# Node Functions

def fetch_data_node(state: AgentState):
    """
    Fetches price data and news in parallel (conceptually, though sequential here for simplicity).
    """
    coins = state['coins']
    market_data = {}
    
    print(f"Fetching data for {coins}...")
    for coin in coins:
        df = fetch_crypto_data(coin)
        df = calculate_technicals(df)
        # Store last row as dict for the prompt
        if not df.empty:
            last_row = df.iloc[-1].to_dict()
            market_data[coin] = last_row
    
    # Fetch News
    news = fetch_crypto_news()
    
    return {"market_data": market_data, "news": news}

def generate_report_node(state: AgentState):
    """
    Uses Gemini to synthesize data and news into a report.
    """
    market_data = state['market_data']
    news = state['news']
    
    # Construct Prompt
    prompt = f"""
    You are a professional Crypto Market Analyst.
    
    **Market Data:**
    {market_data}
    
    **Top News Headlines:**
    {news}
    
    **Task:**
    Write a concise but insightful market briefing for Telegram.
    1. Summarize the price action and key technicals (RSI, MACD) for each coin.
    2. Correlate any price moves with the news headlines if possible.
    3. Provide a 'Sentiment Score' (1-10) and a brief outlook (Bullish/Bearish/Neutral).
    4. Keep it engaging but professional. Use emojis.
    
    **Format:**
    start with "🚀 Crypto Update [Morning/Evening]"
    """
    
    llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash-exp", google_api_key=os.getenv("GOOGLE_API_KEY"))
    response = llm.invoke([HumanMessage(content=prompt)])
    
    return {"final_report": response.content}

def dispatch_node(state: AgentState):
    """
    Placeholder for sending to Telegram.
    """
    report = state['final_report']
    print("\n--- FINAL REPORT ---")
    print(report)
    print("--------------------")
    # In production, this would call syntax to send to Telegram API
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
