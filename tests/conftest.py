from unittest.mock import AsyncMock, MagicMock

import pytest

import shared.core.logger  # noqa: F401


@pytest.fixture
def fake_supabase_chain():
    def _make_chain(data=None, exception=None, eq_chain_count=1):
        execute_mock = AsyncMock()
        if exception:
            execute_mock.side_effect = exception
        else:
            execute_mock.return_value = execute_mock
            execute_mock.data = data

        chain = MagicMock()
        current = chain
        for _ in range(eq_chain_count):
            next_chain = MagicMock()
            current.eq.return_value = next_chain
            current = next_chain
        current.execute = execute_mock
        current.eq.return_value = current
        chain.select.return_value = chain

        insert_chain = MagicMock()
        insert_chain.execute = execute_mock
        chain.insert = MagicMock(return_value=insert_chain)

        return chain

    return _make_chain


@pytest.fixture
def fake_supabase_client(fake_supabase_chain):
    def _mock_client(mock_create_client, data=None, exception=None, eq_chain_count=1):
        chain = fake_supabase_chain(data=data, exception=exception, eq_chain_count=eq_chain_count)
        mock_client = MagicMock()
        mock_client.table.return_value = chain
        mock_create_client.return_value = mock_client
        return mock_client

    return _mock_client
