import asyncio
import os
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

async def test_conn():
    load_dotenv()
    uri = os.getenv("MONGODB_URI")
    print(f"Testing URI: {uri[:20]}...")
    client = AsyncIOMotorClient(uri)
    try:
        # The ismaster command is cheap and does not require auth.
        # But we want to check if we can actually access the DB.
        await client.admin.command('ping')
        print("Ping successful!")
        db = client.get_default_database()
        print(f"Connected to DB: {db.name}")
        # Try a simple operation
        await db.command("dbstats")
        print("DB Stats successful!")
    except Exception as e:
        print(f"Connection failed: {e}")
    finally:
        client.close()

if __name__ == "__main__":
    asyncio.run(test_conn())
