from unittest.mock import MagicMock

import pytest

from jira_client.credentials import (
 CredentialsProvider,
)
from jira_client.enums import (
    JiraEnvironment,
)


@pytest.fixture(name='mock_reader')
def _mock_reader():
    return MagicMock(name='reader')


@pytest.fixture(name='credentials_provider')
def _credentials_provider(mock_reader, monkeypatch):
    monkeypatch.setenv('LOCAL_JIRA_USER', '')
    monkeypatch.setenv('LOCAL_JIRA_PASS', '')
    monkeypatch.setenv('ENV_JIRA_USER', 'test_user')
    monkeypatch.setenv('ENV_JIRA_PASS', 'test_password')

    provider = CredentialsProvider(JiraEnvironment.Dev)

    monkeypatch.setattr(CredentialsProvider, '_read_file', mock_reader)

    return provider


def test_load_local_dev_none(credentials_provider):
    # pylint: disable=protected-access
    assert credentials_provider._load_local_dev() is None


def test_load_local_dev_read(monkeypatch, credentials_provider, mock_reader):
    monkeypatch.setenv('LOCAL_JIRA_USER', '/path/to/user')
    monkeypatch.setenv('LOCAL_JIRA_PASS', '/path/to/pass')

    # pylint: disable=protected-access
    credentials_provider._load_local_dev()

    mock_reader.assert_any_call('/path/to/user')
    mock_reader.assert_any_call('/path/to/pass')


def test_load_env(credentials_provider):
    # pylint: disable=protected-access
    creds = credentials_provider._load_env()
    user, password = creds.auth()

    assert user == 'test_user'
    assert password == 'test_password'


def test_load_production(credentials_provider, mock_reader):
    # pylint: disable=protected-access
    credentials_provider._load_production()

    mock_reader.assert_any_call(
        '/srv/airflow/jira_vm_username'
    )
    mock_reader.assert_any_call(
        '/srv/airflow/jira_vm_password'
    )
