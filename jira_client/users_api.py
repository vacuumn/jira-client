import logging
from typing import Dict, Optional

from jira import User
from jira import JIRAError

from jira_client_v2 import (
    JiraClient,
)

LOGGER = logging.getLogger(__name__)


class JiraUsersAPI:

    def __init__(self, jira_client: JiraClient):
        self._jira_client = jira_client

    def get_user_by_key(self, key: str) -> Optional[User]:
        try:
            return self._jira_client.client.user(key)
        except JIRAError as e:
            LOGGER.info(e.text)
            return None

    def get_user_by_email(self, user_email: str) -> Optional[User]:
        """
        Queries the JIRA API with the given Airbnb email address for a matching
        JIRA user, and returns it. If no matching user is found, None is
        returned.
        """
        results = self._jira_client.client.search_users(
            user_email,
            maxResults=1,
        )
        if len(results) > 0:
            return results[0]

        return None


class JiraUsersCache:
    CACHE = {}

    def __init__(self, users_api: JiraUsersAPI, global_cache=True):
        self._users_api = users_api

        # FYI: The caches are keyed by the email, not by the key.
        self._cache: Dict[str, Optional[User]] = {}
        self._global_cache = global_cache

    def get_user_by_key(self, key: str) -> Optional[User]:
        if not key:
            return None

        if self._global_cache:
            for user in self.CACHE.values():
                if user and user.key == key:
                    return user

            user = self._users_api.get_user_by_key(key)
            if user:
                assert isinstance(user, User)
                self.CACHE[user.emailAddress] = user

            return user

        for user in self._cache.values():
            if user and user.key == key:
                return user

        user = self._users_api.get_user_by_key(key)
        if user:
            assert isinstance(user, User)
            self._cache[user.emailAddress] = user

        return user

    def get_user_by_email(self, user_email: str) -> Optional[User]:
        """
        Queries the JIRA API with the given Airbnb email address for a matching
        JIRA user, and returns it. If no matching user is found, None is
        returned.
        """
        if not user_email:
            return None

        if self._global_cache:
            if user_email not in self.CACHE:
                self.CACHE[user_email] = self._users_api.get_user_by_email(
                    user_email
                )

            return self.CACHE[user_email]

        if user_email not in self._cache:
            self._cache[user_email] = self._users_api.get_user_by_email(
                user_email
            )

        return self._cache[user_email]
