import re

# pylint: disable=import-error
from jira.exceptions import JIRAError
# pylint: enable=import-error


COMPONENT_ERROR = re.compile("Component name \'(.*)\' is not valid")
NONEXISTENT_USER_ERROR = re.compile("User \'(.*)\' does not exist")


def is_issue_not_found_error(err: JIRAError) -> bool:
    return 'An issue with key' in err.text and 'does not exist' in err.text


def is_issue_does_not_exist_error(err: JIRAError) -> bool:
    return 'Issue Does Not Exist' in err.text


def is_create_issue_component_error(err: JIRAError) -> bool:
    return bool(COMPONENT_ERROR.match(err.text))


def is_create_issue_user_not_exist_error(err: JIRAError) -> bool:
    return bool(NONEXISTENT_USER_ERROR.match(err.text))
