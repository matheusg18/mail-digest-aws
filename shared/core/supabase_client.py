from supabase import AsyncClient, acreate_client

from shared.core.settings import settings

url: str = settings.SUPABASE_URL
key: str = settings.SUPABASE_SERVICE_KEY


async def create_supabase_client() -> AsyncClient:
    return await acreate_client(url, key)
