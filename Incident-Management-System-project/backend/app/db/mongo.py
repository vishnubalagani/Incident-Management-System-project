from motor.motor_asyncio import AsyncIOMotorClient
from app.config import settings

client: AsyncIOMotorClient = None

def get_mongo_client() -> AsyncIOMotorClient:
    return client

def get_signals_collection():
    return client[settings.mongo_db]["signals"]

async def connect_mongo():
    global client
    client = AsyncIOMotorClient(settings.mongo_url)
    # Create index for fast component lookups
    await client[settings.mongo_db]["signals"].create_index("component_id")
    await client[settings.mongo_db]["signals"].create_index("work_item_id")
    await client[settings.mongo_db]["signals"].create_index("timestamp")

async def close_mongo():
    global client
    if client:
        client.close()
