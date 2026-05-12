from apscheduler.schedulers.asyncio import AsyncIOScheduler

# Singleton scheduler instance to prevent resource leaks
scheduler = AsyncIOScheduler()
