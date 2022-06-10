from unittest.mock import MagicMock

from jira_client.errors import (
    is_create_issue_component_error,
    is_create_issue_user_not_exist_error,
)


def test_is_create_issue_component_error():
    error = MagicMock(name='JIRAError')
    error.text = "Component name 'foobar' is not valid"

    assert is_create_issue_component_error(error)


def test_is_create_issue_user_not_exist_error():
    error = MagicMock(name='JIRAError')
    error.text = "User 'foobar' does not exist"

    assert is_create_issue_user_not_exist_error(error)
