import asyncio
from motor.motor_asyncio import AsyncIOMotorClient

async def test():
    """
    Tests the local MongoDB connection.
    Properly wraps the client initialization and execution in an async function.
    """
    uri = "mongodb://localhost:27017"
    client = AsyncIOMotorClient(uri)
    try:
        await client.admin.command('ping')
        print("Success! Local MongoDB is running.")
    except Exception as e:
        print(f"Local MongoDB is not running: {e}")
    finally:
        # Best practice: close the client to avoid unclosed socket warnings on exit
        # This properly belongs inside the async function wrapper.
        client.close()

if __name__ == "__main__":
    # Safely executes the async function in the main block
    asyncio.run(test())
