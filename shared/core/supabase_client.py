from supabase import AsyncClient, acreate_client

from shared.core.settings import settings


async def create_supabase_client() -> AsyncClient:
    return await acreate_client(
        settings.SUPABASE_URL, settings.SUPABASE_SERVICE_KEY
    )
