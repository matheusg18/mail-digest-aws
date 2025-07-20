import uuid
from http import HTTPStatus
from unittest.mock import AsyncMock, patch

import pytest

from shared.domain.user import User
from shared.exceptions.sumio_exception import SumioException
from shared.services import user_service
from tests.factories import UserFactory


@pytest.mark.asyncio
@patch("shared.services.user_service.create_supabase_client", new_callable=AsyncMock)
async def test_get_user_found(mock_create_client, fake_supabase_client):
    user = UserFactory()

    fake_supabase_client(mock_create_client, data=[user.model_dump()])

    result = await user_service.get_user(user.id)

    assert isinstance(result, User)
    assert result == user


@pytest.mark.asyncio
@patch("shared.services.user_service.create_supabase_client", new_callable=AsyncMock)
async def test_get_user_not_found(mock_create_client, fake_supabase_client):
    fake_supabase_client(mock_create_client, data=[])

    result = await user_service.get_user(uuid.uuid4())

    assert result is None


@pytest.mark.asyncio
@patch("shared.services.user_service.create_supabase_client", new_callable=AsyncMock)
async def test_get_user_error(mock_create_client, fake_supabase_client):
    fake_supabase_client(mock_create_client, exception=Exception("test error"))

    with pytest.raises(SumioException) as exc_info:
        await user_service.get_user(uuid.uuid4())

    assert exc_info.value.message == "Error fetching user"
    assert exc_info.value.code == HTTPStatus.INTERNAL_SERVER_ERROR


@pytest.mark.asyncio
@patch("shared.services.user_service.create_supabase_client", new_callable=AsyncMock)
async def test_get_users_with_active_mail_digest_at_success(mock_create_client, fake_supabase_client):
    digest_hour = 8
    user = UserFactory()

    fake_supabase_client(mock_create_client, data=[user.model_dump()], eq_chain_count=2)

    result = await user_service.get_users_with_active_mail_digest_at(digest_hour)

    assert isinstance(result, list)
    assert isinstance(result[0], User)
    assert result[0] == user


@pytest.mark.asyncio
@patch("shared.services.user_service.create_supabase_client", new_callable=AsyncMock)
async def test_get_users_with_active_mail_digest_at_no_users(mock_create_client, fake_supabase_client):
    digest_hour = 8

    fake_supabase_client(mock_create_client, data=[], eq_chain_count=2)

    result = await user_service.get_users_with_active_mail_digest_at(digest_hour)

    assert isinstance(result, list)
    assert len(result) == 0


@pytest.mark.asyncio
@patch("shared.services.user_service.create_supabase_client", new_callable=AsyncMock)
async def test_get_users_with_active_mail_digest_at_error(mock_create_client, fake_supabase_client):
    digest_hour = 8

    fake_supabase_client(mock_create_client, exception=Exception("test error"), eq_chain_count=2)

    with pytest.raises(SumioException) as exc_info:
        await user_service.get_users_with_active_mail_digest_at(digest_hour)

    assert exc_info.value.message == "Error fetching users with active mail digest"
    assert exc_info.value.code == HTTPStatus.INTERNAL_SERVER_ERROR
