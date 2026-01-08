import os
import asyncio
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from app.agent_graph import app
from dotenv import load_dotenv

load_dotenv()

async def run_agent():
    print("⏰ Triggering Agent Run...")
    inputs = {"coins": ["BTC", "ETH", "SOL"]}
    # LangGraph invoke is sync or async depending on configuration, 
    # but the compiled app supports .invoke() which is sync.
    # For async environments, we should check if we need ainvoke.
    # Here we stick to simple invocation for the scheduler.
    try:
        result = await app.ainvoke(inputs)
        print("✅ Run Complete.")
    except Exception as e:
        print(f"❌ Error during run: {e}")

async def main():
    scheduler = AsyncIOScheduler()
    
    # Schedule: 9 AM and 9 PM
    scheduler.add_job(run_agent, 'cron', hour=9)
    scheduler.add_job(run_agent, 'cron', hour=21)
    
    print("🚀 Crypto Analysis Agent Started.")
    
    # Start the scheduler
    scheduler.start()
    
    # Run once immediately for verification/startup
    print("running immediate startup check...")
    await run_agent()
    
    # Keep the process alive
    while True:
        await asyncio.sleep(3600)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        print("Stopping agent...")
