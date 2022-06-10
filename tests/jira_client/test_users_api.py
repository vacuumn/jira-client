import pytest

from jira_client.enums import (
    JiraEnvironment,
)
from jira_client.jira_client_v2 import (
    JiraClient,
)
from jira_client.users_api import \
    JiraUsersAPI


@pytest.fixture(name='true_jira_client')
def _true_jira_client():
    return JiraClient(
        JiraEnvironment.Dev,
        local_execution=True,
    )


@pytest.fixture(name='true_jira_users_api')
def _jira_users_api(true_jira_client):
    return JiraUsersAPI(true_jira_client)


@pytest.mark.jira
@pytest.mark.integration
def test_get_user_by_email(true_jira_users_api):
    user = true_jira_users_api.get_user_by_email('derek.wang@airbnb.com')

    # Uncomment this to print out the raw user
    # import logging
    # logging.info(user.raw)

    assert user.displayName == 'Derek Wang'
    assert user.key == 'derek_wang'
    assert user.name == 'derek_wang'
    assert user.emailAddress == 'derek.wang@example.com'
    assert user.active
    assert not user.deleted
    assert user.timeZone == 'UTC'
    assert user.locale == 'en_US'
