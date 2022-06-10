from unittest.mock import (
    ANY,
    call,
    MagicMock,
    patch,
)

import pytest
from jira import Issue

from jira_client.enums import (
    JiraEnvironment,
)
from jira_client.jira_client_v2 import (
    JiraClient,
)
from jira_client.issues_api import (
    JiraIssuesAPI,
)
from ..utils.data import dotdict


@pytest.fixture(name='true_jira_client')
def _true_jira_client():
    return JiraClient(
        JiraEnvironment.Dev,
        local_execution=True,
    )


@pytest.fixture(name='true_jira_issues_api')
def _true_jira_issues_api(true_jira_client):
    return JiraIssuesAPI(true_jira_client)


@pytest.fixture(name='logging_mock')
def _logging_mock():
    name = (
       'teams.contrib.jira_client.issues_api.logging'
    )
    logging_mock = MagicMock(name='logging')
    with patch(name, logging_mock):
        yield logging_mock


@pytest.mark.jira
@pytest.mark.integration
def test_fetch_all(true_jira_issues_api):
    issues = true_jira_issues_api.fetch_all(
        'project = PRODUCT',
        limit=4,
        jira_kwargs={
            'maxResults': 5,
        },
    )

    issues = list(issues)  # materialize the generator
    assert len(issues) == 4

    issue: Issue = issues[0]
    assert 'PRODUCT' in issue.key


@pytest.mark.jira
@pytest.mark.integration
def test_get_issue_by_issue_key(true_jira_issues_api):
    issue: Issue
    issue = true_jira_issues_api.get_issue_by_issue_key('PRODUCT-186262')

    assert issue is not None
    assert issue.id == '3186049'
    assert issue.key == 'PRODUCT-186262'


@pytest.mark.jira
@pytest.mark.integration
def test_get_issue_by_id(true_jira_issues_api):
    issue: Issue
    issue = true_jira_issues_api.get_issue_by_id('3186049')

    assert issue is not None
    assert issue.id == '3186049'
    assert issue.key == 'PRODUCT-186262'


@pytest.mark.jira
@pytest.mark.integration
def test_get_issue_by_issue_key_no_issue(true_jira_issues_api):
    issue: Issue
    issue = true_jira_issues_api.get_issue_by_issue_key('PRODUCT-99999999')

    assert issue is None


@pytest.mark.jira
@pytest.mark.integration
def test_get_issue_by_id_no_issue(true_jira_issues_api):
    issue: Issue
    issue = true_jira_issues_api.get_issue_by_id('12847238439')

    assert issue is None


@pytest.mark.jira
@pytest.mark.integration
def test_fetch_all_overscan(true_jira_issues_api, logging_mock):
    issues = true_jira_issues_api.fetch_all(
        'project = PRODUCT',
        limit=16,
        overscan=True,
        jira_kwargs={
            'maxResults': 10,
        },
    )

    issues = list(issues)  # materialize the generator
    assert len(issues) == 16

    keys = set()
    issue: Issue
    for issue in issues:
        keys.add(issue.id)

    assert len(keys) == 16, '16 unique jira keys; no overscan'

    calls = [
        call(ANY, 'project = PRODUCT', 16, 0, 10),
        call('Discovered total %d issues in ResultList', ANY),
        call(ANY, 'project = PRODUCT', 16, 10, 10),
        call('Discovered total %d issues in ResultList', ANY),
    ]
    logging_mock.info.assert_has_calls(calls)


@pytest.mark.jira
@pytest.mark.integration
def test_fetch_all_no_issues(true_jira_issues_api):
    issues = true_jira_issues_api.fetch_all(
        'label = "akdjfasdf"',
        limit=1,
        jira_kwargs={
            'maxResults': 10,
        },
    )

    issues = list(issues)  # materialize the generator
    assert len(issues) == 0


@pytest.mark.jira
@pytest.mark.integration
def test_get_issues_by_label_works_base64(true_jira_issues_api):
    """
    Since some of our labels are base64, ensure that the labels are properly
    wrapped in quotes so that any label ending in "=" won't cause it to error.
    """
    issues = true_jira_issues_api.get_issues_by_label("b280acBE20a=")
    issues = list(issues)  # materialize the generator
    assert len(issues) == 0


#
# Unit tests
#
@pytest.fixture(name='mock_jira')
def _mock_jira():
    return MagicMock(name='JIRA')


@pytest.fixture(name='mock_jira_client')
def _mock_jira_client(mock_jira):
    client = MagicMock(spec=JiraClient)
    client.client = mock_jira

    return client


@pytest.fixture(name='jira_issues_api')
def _jira_issues_api(mock_jira_client):
    return JiraIssuesAPI(mock_jira_client)


class MockResultList:
    def __init__(self, results: list, total=10):
        self._results = results
        self.total = total
        self._idx = 0

    def __iter__(self):
        return (row for row in self._results)


def test_fetch_all_unit_defaults(jira_issues_api, mock_jira):
    result_list = MockResultList([])
    mock_jira.search_issues.return_value = result_list

    generator = jira_issues_api.fetch_all('SOME JQL STATEMENT')
    list(generator)  # materialize the generator

    mock_jira.search_issues.assert_called_with(
        'SOME JQL STATEMENT',
        startAt=0,
        maxResults=50,
    )


def test_fetch_all_unit_kwargs(jira_issues_api, mock_jira):
    result_list = MockResultList([
        dotdict({
            'id': 'ID-1',
        }),
        dotdict({
            'id': 'ID-2',
        }),
        dotdict({
            'id': 'ID-3',
        }),
    ])
    mock_jira.search_issues.return_value = result_list

    generator = jira_issues_api.fetch_all(
        'SOME JQL STATEMENT',
        limit=1,
        jira_kwargs={
            'maxResults': 11,
        },
    )
    list(generator)

    mock_jira.search_issues.assert_called_with(
        'SOME JQL STATEMENT',
        startAt=0,
        maxResults=11,
    )


def test_fetch_all_unit_limit(jira_issues_api, mock_jira):
    result_list = MockResultList([
        dotdict({
            'id': 'ID-1',
        }),
        dotdict({
            'id': 'ID-2',
        }),
        dotdict({
            'id': 'ID-3',
        }),
    ])
    mock_jira.search_issues.return_value = result_list

    issues = jira_issues_api.fetch_all('SOME JQL STATEMENT', limit=1)

    assert len(list(issues)) == 1, 'Because limit 1'


def test_fetch_all_unit_deduplicate(jira_issues_api, mock_jira):
    mock_jira.search_issues.side_effect = [
        MockResultList([
            dotdict({'id': 'ID-0'}),
            dotdict({'id': 'ID-1'}),
            dotdict({'id': 'ID-2'}),
            dotdict({'id': 'ID-3'}),
            dotdict({'id': 'ID-4'}),
            dotdict({'id': 'ID-5'}),
            dotdict({'id': 'ID-6'}),
            dotdict({'id': 'ID-7'}),
            dotdict({'id': 'ID-8'}),
            dotdict({'id': 'ID-9'}),
        ], total=11),
        MockResultList([
            dotdict({'id': 'ID-5'}),
            dotdict({'id': 'ID-6'}),
            dotdict({'id': 'ID-7'}),
            dotdict({'id': 'ID-8'}),
            dotdict({'id': 'ID-9'}),
            dotdict({'id': 'ID-10'}),
            dotdict({'id': 'ID-11'}),
        ], total=11),
    ]

    issues = jira_issues_api.fetch_all(
        'SOME JQL STATEMENT',
        jira_kwargs={
            'maxResults': 10,
        },
        overscan=True,
    )

    assert len(list(issues)) == 12, 'deduplicate items'

    calls = [
        call(ANY, startAt=0, maxResults=10),
        call(ANY, startAt=10, maxResults=10),
    ]
    mock_jira.search_issues.assert_has_calls(calls)


def test_fetch_all_unit_overscan(jira_issues_api, mock_jira):
    """
    This case tests for when a jira issue is inserted in the middle of an
    iteration, and overscan is enabled.
    """
    mock_jira.search_issues.side_effect = [
        MockResultList([
            dotdict({'id': 'ID-0'}),
            dotdict({'id': 'ID-1'}),
            dotdict({'id': 'ID-2'}),
            dotdict({'id': 'ID-3'}),
            dotdict({'id': 'ID-4'}),

        ], total=10),
        MockResultList([
            dotdict({'id': 'ID-5'}),
            dotdict({'id': 'ID-6'}),
            dotdict({'id': 'ID-7'}),
            dotdict({'id': 'ID-8'}),
            dotdict({'id': 'ID-9'}),
        ], total=11),
        MockResultList([
        ], total=11),
        MockResultList([
            dotdict({'id': 'ID-0'}),
            dotdict({'id': 'ID-1'}),
            dotdict({'id': 'ID-2'}),
            dotdict({'id': 'ID-3'}),
            dotdict({'id': 'ID-4'}),
        ], total=11),
        MockResultList([
            dotdict({'id': 'ID-5'}),
            dotdict({'id': 'ID-6'}),
            dotdict({'id': 'ID-7'}),
            dotdict({'id': 'ID-8'}),
            dotdict({'id': 'ID-9'}),
        ], total=11),
        MockResultList([
            dotdict({'id': 'ID-10'}),
        ], total=11),
    ]

    issues = jira_issues_api.fetch_all(
        'SOME JQL STATEMENT',
        jira_kwargs={
            'maxResults': 5,
        },
        overscan=True,
    )

    assert len(list(issues)) == 11, 'catch changing response during overscan'

    calls = [
        call(ANY, startAt=0, maxResults=5),
        call(ANY, startAt=5, maxResults=5),
        call(ANY, startAt=10, maxResults=5),
        # Due to overscan, start over from beginning
        call(ANY, startAt=0, maxResults=5),
        call(ANY, startAt=5, maxResults=5),
        call(ANY, startAt=10, maxResults=5),
    ]
    mock_jira.search_issues.assert_has_calls(calls)
