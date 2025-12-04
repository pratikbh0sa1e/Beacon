"""Test Upstash Redis connection"""
import asyncio
import os
from dotenv import load_dotenv

load_dotenv()

async def test_redis():
    try:
        from redis import asyncio as aioredis
        
        redis_url = os.getenv("REDIS_URL")
        print(f"Testing connection to: {redis_url[:30]}...")
        
        # Upstash requires rediss:// (Redis with SSL)
        if "upstash.io" in redis_url and redis_url.startswith("redis://"):
            redis_url = redis_url.replace("redis://", "rediss://", 1)
            print("Using SSL connection (rediss://)")
        
        # Connect to Upstash
        redis = await aioredis.from_url(
            redis_url,
            encoding="utf8",
            decode_responses=True
        )
        
        # Test ping
        result = await redis.ping()
        print(f"✓ Ping successful: {result}")
        
        # Test set/get
        await redis.set("test_key", "Hello from BEACON!")
        value = await redis.get("test_key")
        print(f"✓ Set/Get successful: {value}")
        
        # Clean up
        await redis.delete("test_key")
        await redis.close()
        
        print("\n✓ Upstash Redis connection successful!")
        return True
        
    except Exception as e:
        print(f"\n✗ Redis connection failed: {str(e)}")
        return False

if __name__ == "__main__":
    asyncio.run(test_redis())
