"""
A version 2 of the JIRA Client

Usage:
1) Set up object

    client = get_base_client_v2(service_context)

2) Use the .client property

    You can just use the .client property, which automatically determines
    credentials and sets up & tests the API connection upon first call.

    issue = client.issue('PRODUCT-12345')

"""
import logging
from jira import JIRA

from enums import (
    JiraEnvironment,
)
from credentials import (
    CredentialsProvider,
)


class JiraClient:
    """
    Adapter for the JIRA client.

    This service abstracts away environment setup and credentials loading.
    It also hides away the initial JIRA connection attempt, preferring to
    lazy-load the connection.

    To use this service, simply set it up and inject it into all API services
    (e.g. JiraUsersAPI).
    """
    SYNAPSE_PROXY = 'http://httpproxy.synapse:9999'

    def __init__(self,
                 jira_environment: JiraEnvironment,
                 local_execution=False,
                 credential_provider=None):
        self._jira_environment = jira_environment
        self._local_execution = local_execution

        # Allow to use other credentials other than VM team's
        self._credentials_provider = (
            credential_provider
            if credential_provider else CredentialsProvider(jira_environment)
        )
        self._client = None

    def connect(self) -> JIRA:
        """
        Initializes a new connection to the JIRA server and returns a JIRA
        object associated with it.
        """
        self._client = JIRA(
            self._jira_environment.value,
            auth=self._client_auth,
            proxies=self._client_proxies,
        )
        return self._client

    @property
    def environment(self) -> JiraEnvironment:
        """
        Returns the JiraEnvironment enum currently associated with the client.
        """
        return self._jira_environment

    @property
    def _client_auth(self) -> (str, str):
        creds = self._credentials_provider.load_credentials()
        if creds:
            logging.debug('JIRA credentials loaded from: %s', creds.alias)
            return creds.auth()

        logging.error(
            'Failed to load Jira credentials [%s] local=%s',
            self._jira_environment.value,
            'true' if self._local_execution else 'false',
        )
        return '', ''

    @property
    def _client_proxies(self):
        return (
            {'https': self.SYNAPSE_PROXY}
            if not self._local_execution
            else None
        )

    @property
    def client(self) -> JIRA:
        """
        Fetches the JIRA client. If none currently exists, one will be newly
        created, otherwise it will re-use any existing client.
        """
        if not self._client:
            self.connect()
        return self._client
