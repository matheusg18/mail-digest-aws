import uuid
from http import HTTPStatus
from unittest.mock import AsyncMock, patch

import pytest

from shared.domain.delivery_channel import DeliveryChannel, DeliveryChannelEnum
from shared.exceptions.sumio_exception import SumioException
from shared.services import delivery_channel_service
from tests.factories import DeliveryChannelFactory


@pytest.mark.asyncio
@patch("shared.services.delivery_channel_service.create_supabase_client", new_callable=AsyncMock)
async def test_list_user_delivery_channels_success(mock_create_client, fake_supabase_client):
    user_id = uuid.uuid4()
    delivery_channel = DeliveryChannelFactory(user_id=user_id)

    fake_supabase_client(mock_create_client, data=[delivery_channel.model_dump()])

    result = await delivery_channel_service.list_user_delivery_channels(user_id)

    assert isinstance(result, list)
    assert isinstance(result[0], DeliveryChannel)
    assert result[0] == delivery_channel


@pytest.mark.asyncio
@patch("shared.services.delivery_channel_service.create_supabase_client", new_callable=AsyncMock)
async def test_list_user_delivery_channels_empty(mock_create_client, fake_supabase_client):
    user_id = uuid.uuid4()

    fake_supabase_client(mock_create_client, data=[])

    result = await delivery_channel_service.list_user_delivery_channels(user_id)

    assert isinstance(result, list)
    assert len(result) == 0


@pytest.mark.asyncio
@patch("shared.services.delivery_channel_service.create_supabase_client", new_callable=AsyncMock)
async def test_list_user_delivery_channels_error(mock_create_client, fake_supabase_client):
    user_id = uuid.uuid4()

    fake_supabase_client(mock_create_client, exception=Exception("test error"))

    with pytest.raises(SumioException) as exc_info:
        await delivery_channel_service.list_user_delivery_channels(user_id)

    assert exc_info.value.message == "Error fetching active delivery channels"
    assert exc_info.value.code == HTTPStatus.INTERNAL_SERVER_ERROR


@pytest.mark.asyncio
@patch("shared.services.delivery_channel_service.create_supabase_client", new_callable=AsyncMock)
async def test_add_delivery_channel_success(mock_create_client, fake_supabase_client):
    user_id = uuid.uuid4()
    chat_id = 123456
    channel_type = DeliveryChannelEnum.TELEGRAM
    delivery_channel = DeliveryChannelFactory(user_id=user_id, address=str(chat_id), channel_type=channel_type)

    fake_supabase_client(mock_create_client, data=[delivery_channel.model_dump()])

    result = await delivery_channel_service.add_delivery_channel(user_id, chat_id, channel_type)

    assert isinstance(result, DeliveryChannel)
    insert_mock = mock_create_client.return_value.table.return_value.insert
    insert_mock.assert_called_once()
    insert_args = insert_mock.call_args[0][0]
    assert insert_args["user_id"] == user_id
    assert insert_args["address"] == str(chat_id)
    assert insert_args["channel_type"] == channel_type
    assert insert_args["is_active"] is True
    assert "id" in insert_args
    assert "created_at" in insert_args
    assert "updated_at" in insert_args
    assert result.user_id == user_id
    assert result.address == str(chat_id)
    assert result.channel_type == channel_type


@pytest.mark.asyncio
@patch("shared.services.delivery_channel_service.create_supabase_client", new_callable=AsyncMock)
async def test_add_delivery_channel_error(mock_create_client, fake_supabase_client):
    user_id = uuid.uuid4()
    chat_id = 123456
    channel_type = DeliveryChannelEnum.TELEGRAM
    fake_supabase_client(mock_create_client, exception=Exception("test error"))

    with pytest.raises(SumioException) as exc_info:
        await delivery_channel_service.add_delivery_channel(user_id, chat_id, channel_type)

    assert exc_info.value.message == "Error adding delivery channel"
    assert exc_info.value.code == HTTPStatus.INTERNAL_SERVER_ERROR
