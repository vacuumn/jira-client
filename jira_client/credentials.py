"""
Credentials Provider

Usage:

1) Instantiate the CredentialsProvider service

    env = JiraEnvironment.Production
    provider = CredentialsProvider(env)

2) Call the load_credentials() method

    creds = provider.load_credentials()

3) Use the returned object

    print(creds.alias)
    client = JIRA(auth=creds.auth)

"""
import getpass
import os
from typing import Optional

from enums import (
    JiraEnvironment,
)


class Credentials:
    """
    An object concealing the contents of loaded credentials. The object is
    sealed with inaccessible members and will not accidentally print its
    "guts" when dumped into a stacktrace. Note this is for SAFETY, not
    security.
    """
    def __init__(self, username: str, password: str, alias: str):
        # The double underscores are intentional
        self.__username = username
        self.__password = password
        self._alias = alias

    def auth(self) -> (str, str):
        return self.__username, self.__password

    def alias(self) -> str:
        return self._alias

    def __repr__(self):
        return f'[[[ Jira Credentials, ({self._alias}) ]]]'

    def __str__(self):
        return f'[[[ Jira Credentials, ({self._alias}) ]]]'


class CredentialsProvider:
    PRODUCTION_USER = 'svc-user'
    PROD_USER_PATH = '/srv/airflow/jira_vm_username'
    PROD_PASSWD_PATH = '/srv/airflow/jira_vm_password'
    DEV_USER_PATH = '/home/{}/jira_user'
    DEV_PASSWD_PATH = '/home/{}/jira_passwd'

    def __init__(self, jira_environment: JiraEnvironment):
        self._env = jira_environment
        self._user = getpass.getuser()

    def load_credentials(self) -> Optional[Credentials]:
        """
        Returns the Credentials object given the provider's JiraEnvironment
        configuration.

        If no credentials can be found, returns None.
        """
        if self._env == JiraEnvironment.Prod:
            return self._load_production()

        # Compatibility with JiraClient--look in environment variables first
        # to support unit tests.
        creds = self._load_local_dev()
        if creds:
            return creds

        creds = self._load_env()
        if creds:
            return creds

        creds = self._load_dev(self._user)
        if creds:
            return creds

        return None

    @classmethod
    def _load_from_files(cls,
                         username_path,
                         password_path,
                         alias) -> Credentials:
        return Credentials(
            cls._read_file(username_path),
            cls._read_file(password_path),
            alias,
        )

    @classmethod
    def _load_production(cls) -> Credentials:
        # Load from known production files. These are controlled via Chef.
        return cls._load_from_files(
            cls.PROD_USER_PATH,
            cls.PROD_PASSWD_PATH,
            'Production',
        )

    @classmethod
    def _load_dev(cls, user: str) -> Optional[Credentials]:
        # Load from files in user's home directory.
        user_file = cls.DEV_USER_PATH.format(user)
        if not os.path.exists(user_file):
            return None
        pass_file = cls.DEV_PASSWD_PATH.format(user)
        if not os.path.exists(pass_file):
            return None

        return cls._load_from_files(
            user_file,
            pass_file,
            f'OneFlow, {user}',
        )

    @classmethod
    def _load_env(cls) -> Optional[Credentials]:
        # Load directly from these environment vars; they're raw creds, not
        # filepaths.
        if not os.environ.get('ENV_JIRA_USER'):
            return None
        if not os.environ.get('ENV_JIRA_PASS'):
            return None

        return Credentials(
            os.environ.get('ENV_JIRA_USER'),
            os.environ.get('ENV_JIRA_PASS'),
            'Local Env Vars'
        )

    @classmethod
    def _load_local_dev(cls) -> Optional[Credentials]:
        # Load from files on the local filesystem, specified in ENV vars.
        if not os.environ.get('LOCAL_JIRA_USER'):
            return None
        if not os.environ.get('LOCAL_JIRA_PASS'):
            return None

        return cls._load_from_files(
            os.environ.get('LOCAL_JIRA_USER'),
            os.environ.get('LOCAL_JIRA_PASS'),
            'Local Cred Files',
        )

    @staticmethod
    def _read_file(path) -> str:
        with open(path, 'r', encoding='utf-8') as file:
            return file.read().strip()
