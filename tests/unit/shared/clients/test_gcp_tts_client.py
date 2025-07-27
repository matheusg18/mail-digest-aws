import base64
import json
from http import HTTPStatus
from unittest.mock import AsyncMock, patch

import httpx
import pytest
import respx
from httpx import Response

from shared.clients import gcp_tts_client

TTS_API_URL = "https://texttospeech.googleapis.com/v1/text:synthesize"


@pytest.mark.asyncio
@respx.mock
@patch(
    "shared.clients.gcp_tts_client.google_auth_service.get_service_account_token",
    new_callable=AsyncMock,
    return_value="fake-token",
)
async def test_generate_audio_with_success(mock_get_service_account_token):
    fake_audio_content = base64.b64encode(b"audio-bytes").decode()

    route = respx.post(TTS_API_URL).mock(
        return_value=Response(HTTPStatus.OK, json={"audioContent": fake_audio_content})
    )

    result = await gcp_tts_client.generate_audio(
        "hello", language_code="en-US", gender="FEMALE", voice_name="en-US-Voice"
    )

    assert route.called
    assert route.call_count == 1
    request_body = json.loads(route.calls[0][0].content.decode())
    assert request_body == {
        "input": {"text": "hello"},
        "voice": {"languageCode": "en-US", "ssmlGender": "FEMALE", "name": "en-US-Voice"},
        "audioConfig": {"audioEncoding": "OGG_OPUS"},
    }
    request_headers = route.calls[0][0].headers
    assert request_headers["Authorization"] == "Bearer fake-token"
    assert request_headers["x-goog-user-project"] == "sumio"

    assert isinstance(result, bytes)
    assert result == b"audio-bytes"

    mock_get_service_account_token.assert_awaited_once_with(["https://www.googleapis.com/auth/texttospeech"])


@pytest.mark.asyncio
@respx.mock
@patch(
    "shared.clients.gcp_tts_client.google_auth_service.get_service_account_token",
    new_callable=AsyncMock,
    side_effect=httpx.ConnectError("Connection failed"),
)
async def test_generate_audio_with_get_token_error(mock_get_service_account_token):
    route = respx.post(TTS_API_URL).mock()

    with pytest.raises(httpx.ConnectError, match="Connection failed"):
        await gcp_tts_client.generate_audio("hello")

    assert not route.called
    mock_get_service_account_token.assert_awaited_once_with(["https://www.googleapis.com/auth/texttospeech"])


@pytest.mark.asyncio
@respx.mock
@patch(
    "shared.clients.gcp_tts_client.google_auth_service.get_service_account_token",
    new_callable=AsyncMock,
    return_value="fake-token",
)
async def test_generate_audio_with_no_audio_content(mock_get_service_account_token):
    route = respx.post(TTS_API_URL).mock(return_value=Response(HTTPStatus.OK, json={}))

    with pytest.raises(Exception, match="No audio content received from TTS API"):
        await gcp_tts_client.generate_audio("hello")

    assert route.called
    assert route.call_count == 1
    request_body = json.loads(route.calls[0][0].content.decode())
    assert request_body == {
        "input": {"text": "hello"},
        "voice": {"languageCode": "en-US", "ssmlGender": "FEMALE", "name": "en-US-Chirp3-HD-Achernar"},
        "audioConfig": {"audioEncoding": "OGG_OPUS"},
    }
    request_headers = route.calls[0][0].headers
    assert request_headers["Authorization"] == "Bearer fake-token"
    assert request_headers["x-goog-user-project"] == "sumio"

    mock_get_service_account_token.assert_awaited_once_with(["https://www.googleapis.com/auth/texttospeech"])


@pytest.mark.asyncio
@respx.mock
@patch(
    "shared.clients.gcp_tts_client.google_auth_service.get_service_account_token",
    new_callable=AsyncMock,
    return_value="fake-token",
)
async def test_generate_audio_with_http_error(mock_get_service_account_token):
    route = respx.post(TTS_API_URL).mock(
        return_value=Response(HTTPStatus.INTERNAL_SERVER_ERROR, json={"error": "Internal Server Error"})
    )

    with pytest.raises(httpx.HTTPStatusError) as exc_info:
        await gcp_tts_client.generate_audio("hello")

    assert route.called
    assert route.call_count == 1
    request_body = json.loads(route.calls[0][0].content.decode())
    assert request_body == {
        "input": {"text": "hello"},
        "voice": {"languageCode": "en-US", "ssmlGender": "FEMALE", "name": "en-US-Chirp3-HD-Achernar"},
        "audioConfig": {"audioEncoding": "OGG_OPUS"},
    }
    request_headers = route.calls[0][0].headers
    assert request_headers["Authorization"] == "Bearer fake-token"
    assert request_headers["x-goog-user-project"] == "sumio"

    assert exc_info.value.response.status_code == HTTPStatus.INTERNAL_SERVER_ERROR
    assert exc_info.value.response.json() == {"error": "Internal Server Error"}

    mock_get_service_account_token.assert_awaited_once_with(["https://www.googleapis.com/auth/texttospeech"])


@pytest.mark.asyncio
@respx.mock
@patch(
    "shared.clients.gcp_tts_client.google_auth_service.get_service_account_token",
    new_callable=AsyncMock,
    return_value="fake-token",
)
async def test_generate_audio_with_unexpected_error(mock_get_service_account_token):
    def raise_connect_error(request):
        raise httpx.ConnectError("Connection failed", request=request)

    route = respx.post(TTS_API_URL).mock(side_effect=raise_connect_error)

    with pytest.raises(httpx.ConnectError) as exc_info:
        await gcp_tts_client.generate_audio("hello")

    assert route.called
    assert route.call_count == 1
    request_body = json.loads(route.calls[0][0].content.decode())
    assert request_body == {
        "input": {"text": "hello"},
        "voice": {"languageCode": "en-US", "ssmlGender": "FEMALE", "name": "en-US-Chirp3-HD-Achernar"},
        "audioConfig": {"audioEncoding": "OGG_OPUS"},
    }
    request_headers = route.calls[0][0].headers
    assert request_headers["Authorization"] == "Bearer fake-token"
    assert request_headers["x-goog-user-project"] == "sumio"

    assert "Connection failed" in str(exc_info.value)

    mock_get_service_account_token.assert_awaited_once_with(["https://www.googleapis.com/auth/texttospeech"])
