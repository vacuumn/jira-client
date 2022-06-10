"""
Wrapper for using the JIRA API's issues api to query for Jira Issues

Usage:

1) Instantiate

    client = JiraClient()
    api = JiraIssuesAPI(client)

2) Send JQL

    res = api.fetch_all('project = PRODUCT AND ...', limit=25)

3) Iterate

    for issue in res:
        issue: Issue
        ...
"""
import logging
from typing import Iterator, Optional

# pylint: disable=import-error
from jira import Issue
from jira.client import ResultList
from jira.exceptions import JIRAError
# pylint: enable=import-error

from domain_alignment import DomainAligner
from jira_client_v2 import (
    JiraClient,
)
from errors import (
    is_issue_not_found_error,
    is_issue_does_not_exist_error,
)


class JiraIssuesAPI:

    def __init__(self,
                 jira_client: JiraClient,
                 domain_aligner: DomainAligner = None):
        self._jira_client = jira_client
        self._domain_aligner = domain_aligner

    def get_issues_by_label(self, label: str) -> Iterator[Issue]:
        """
        Convenience method that just queries and yields a generator for issues
        belonging to the given label.
        """
        return self.fetch_all(f'labels = "{label}" ORDER BY labels')

    def get_issue_by_issue_key(self, issue_key: str) -> Optional[Issue]:
        """
        Queries for a JIRA issue given its KEY.

        Returns the Issue, or None if no such issue is found
        """
        try:
            # Dear JIRA API:
            #   Why do you return an HTTP 400 for this query when the query
            #   returns nothing? Why can't you be a sane API and just return
            #   an HTTP 200 or 202 No Content with a response containing zero
            #   items?
            #
            #   My request isn't bad; YOU'RE BAD
            # with hate and anger:
            #   - disgruntled engineer
            res = self._jira_client.client.search_issues(
                f'issueKey = "{issue_key}"',
                maxResults=1,
            )
            issue = res[0] if len(res) > 0 else None
            if issue and self._domain_aligner:
                self._domain_aligner.realign_api_domain(issue)

            return issue
        except JIRAError as err:
            if is_issue_not_found_error(err):
                return None

            raise

    def get_issue_by_id(self, issue_id: str) -> Optional[Issue]:
        """
        Queries for a JIRA issue given the id (which is an integer, NOT to be
        confused with the issue KEY).

        Returns the Issue, or None if no such issue is found
        """
        try:
            issue = self._jira_client.client.issue(issue_id)
            if issue and self._domain_aligner:
                self._domain_aligner.realign_api_domain(issue)

            return issue
        except JIRAError as err:
            if is_issue_does_not_exist_error(err):
                return None

            raise

    def fetch_all(self,
                  jql: str,
                  limit: int = 0,
                  jira_kwargs: dict = None,
                  overscan: bool = False) -> Iterator[Issue]:
        """
        Executes a provided JQL statement (that is expected to return a lot of
        issues) and yields individual issues.

        Params:
            jql (str): The JQL statement
            limit (int):
                Set the maximum number of entries returned.
                Default 0 (no limit)
            jira_kwargs (dict): Pass arguments to the jira client
            overscan (bool):
                Pass True to perform overscanning. Overscanning will redundantly
                scan pages with overlap, reducing the chances for "missing" a
                newly created ticket during an interation cycle, but can be
                significantly slower.
                Note if you create ticket during iteration while overscan is
                True, this can cause an infinite loop of overscanning. Reserve
                overscanning for read-only operations.

        Returns:
            Iterator[Issue], for your convenience
        """
        default_jira_kwargs = {
            'maxResults': 50,
        }
        if jira_kwargs:
            default_jira_kwargs.update(jira_kwargs)

        page_size = default_jira_kwargs['maxResults']

        start_at = 0
        item_count = 0
        issue_ids = set()
        total = None
        done = False
        force_restart = False
        while not done:
            logging.info(
                'Searching "%s" for up to %d jira issues, OFFSET %d LIMIT %d',
                jql,
                limit,
                start_at,
                page_size,
            )
            results: ResultList = self._jira_client.client.search_issues(
                jql,
                startAt=start_at,
                **default_jira_kwargs,
            )
            logging.info(
                'Discovered total %d issues in ResultList',
                results.total,
            )

            if total is None:
                total = results.total
            elif overscan and results.total != total:
                logging.info(
                    'result.total has changed!!! overscan is required!!!'
                )
                force_restart = True

            for issue in results:
                if issue.id in issue_ids:
                    # Don't yield issues that we've already yielded
                    continue

                item_count += 1
                if limit and item_count > limit:
                    return

                issue_ids.add(issue.id)
                if self._domain_aligner:
                    self._domain_aligner.realign_api_domain(issue)

                yield issue

            start_at += page_size
            if start_at > total:
                if force_restart:
                    start_at = 0
                    force_restart = False
                    total = None
                else:
                    done = True

        logging.info('Done. Yielded %d issues', item_count)
