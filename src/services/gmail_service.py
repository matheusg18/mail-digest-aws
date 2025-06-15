import httpx


async def list_messages(
    user_id: str, access_token: str, query: str = ''
) -> list:
    url = f'https://gmail.googleapis.com/gmail/v1/users/{user_id}/messages'
    params = {'q': query}

    headers = {
        'Authorization': f'Bearer {access_token}',
        'Accept': 'application/json',
    }

    async with httpx.AsyncClient() as client:
        response = await client.get(url, headers=headers, params=params)
        response.raise_for_status()
        return response.json().get('messages', [])


async def get_message(
    user_id: str, access_token: str, message_id: str
) -> dict:
    url = f'https://gmail.googleapis.com/gmail/v1/users/{user_id}/messages/{message_id}'

    headers = {
        'Authorization': f'Bearer {access_token}',
        'Accept': 'application/json',
    }

    async with httpx.AsyncClient() as client:
        response = await client.get(url, headers=headers)
        response.raise_for_status()
        return response.json()
