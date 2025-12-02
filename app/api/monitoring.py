"""Server-Sent Events (SSE) endpoint for real-time email notifications."""
import asyncio
import json
from fastapi import APIRouter, Depends, HTTPException, status
from sse_starlette.sse import EventSourceResponse
from typing import AsyncGenerator
from app.models.user import User
from app.core.deps import get_current_user
import redis.asyncio as aioredis
from app.core.config import get_settings

settings = get_settings()

router = APIRouter(prefix="/monitoring", tags=["Monitoring"])


async def get_redis_client():
    """Get Redis client for pub/sub."""
    return await aioredis.from_url(settings.REDIS_URL, decode_responses=True)


async def event_generator(user_id: int) -> AsyncGenerator:
    """
    Generate SSE events for a specific user.
    
    Listens to Redis pub/sub channel for email events.
    """
    redis_client = await get_redis_client()
    pubsub = redis_client.pubsub()
    
    # Subscribe to user-specific channel
    channel_name = f"email_events:user:{user_id}"
    await pubsub.subscribe(channel_name)
    
    try:
        # Send initial connection event
        yield {
            "event": "connected",
            "data": json.dumps({
                "message": "Connected to email monitoring",
                "user_id": user_id
            })
        }
        
        # Listen for events
        async for message in pubsub.listen():
            if message["type"] == "message":
                # Forward the event data to the client
                yield {
                    "event": "email_event",
                    "data": message["data"]
                }
            
            # Keep alive ping every 15 seconds
            await asyncio.sleep(0.1)
    
    except asyncio.CancelledError:
        # Client disconnected
        await pubsub.unsubscribe(channel_name)
        await redis_client.close()
    
    except Exception as e:
        # Error occurred
        yield {
            "event": "error",
            "data": json.dumps({"error": str(e)})
        }
    
    finally:
        await pubsub.unsubscribe(channel_name)
        await redis_client.close()


@router.get("/sse")
async def sse_endpoint(current_user: User = Depends(get_current_user)):
    """
    Server-Sent Events endpoint for real-time email notifications.
    
    Clients connect to this endpoint to receive real-time updates about:
    - New emails detected
    - Spam emails identified and moved
    - Email processing status
    
    Events are user-specific and require authentication.
    """
    if not current_user.is_monitoring:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Email monitoring is not active for this user"
        )
    
    return EventSourceResponse(event_generator(current_user.id))


@router.get("/status")
async def monitoring_status(current_user: User = Depends(get_current_user)):
    """
    Get current monitoring status for the user.
    """
    return {
        "is_monitoring": current_user.is_monitoring,
        "last_sync_time": current_user.last_sync_time.isoformat() if current_user.last_sync_time else None,
        "email": current_user.email
    }
