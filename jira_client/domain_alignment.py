import logging
from typing import Dict, Union

# pylint: disable=import-error
from jira.resources import Resource
# pylint: enable=import-error

from enums import JiraEnvironment

LOGGER = logging.getLogger(__name__)


class DomainAligner:

    # Maps the hostname of "incorrect" domains to the "correct" domains.
    # Make sure the values do not have protocols or paths.
    # These mappings are applied as direct string replacements.
    DEFAULT_MAPPINGS = {
        'jira-dev.example.com': (
            JiraEnvironment.Dev.value.replace('https://', '')
        ),
        'jira-stage.example.com': (
            JiraEnvironment.Staging.value.replace('https://', '')
        ),
        'jira.example.com': (
            JiraEnvironment.Prod.value.replace('https://', '')
        ),
    }

    def __init__(self, mappings: Dict[str, str] = None):
        self._mappings = mappings or self.DEFAULT_MAPPINGS

    def realign_api_domain(self, resource: Union[Resource, dict]):
        """
        Monkeypatch jira issues to point to the correct domain
        The python jira library we use (https://pypi.org/project/jira/2.0.0/)
        reconfigures resource's API endpoints based on the server's returned
        data instead of the domain we configured the client with. This will
        break things when you authenticate with a proxy gateway.

        We should ultimately PR to fix the library at the source, but there's
        not a lot of recent changes and their CI is broken
        Culprit line: https://github.com/pycontribs/jira/blob/
            91461fd736cd9a37cc136e07402c6f0b1e60170b/jira/resources.py#L281

        Arguments:
            issue_object {jira.Resource or dict} -- the resource we need to
                reconfigure the domain for
        Returns:
            issue_object {jira.Resource} -- monkeypatch'ed resource
        """
        assert isinstance(resource, (Resource, dict))

        is_obj = isinstance(resource, Resource) or hasattr(resource, 'self')
        if is_obj:
            resource_uri = resource.self
        elif isinstance(resource, dict) and 'self' in resource:
            resource_uri = resource['self']
        else:
            raise RuntimeError(
                "Cannot realign API domain; Invalid argument of "
                f"type {type(resource)}: {resource}"
            )

        if self._is_aligned(resource_uri):
            LOGGER.debug('Resource with uri %s already aligned', resource_uri)
            return resource

        proper_uri = self._get_aligned_uri(resource_uri)

        if is_obj:
            resource.self = proper_uri
        else:
            resource['self'] = proper_uri

        return resource

    def _is_aligned(self, resource_uri: str) -> bool:
        return any(
            mapped_value in resource_uri
            for mapped_value
            in self._mappings.values()
        )

    def _get_aligned_uri(self, resource_uri: str):
        for base_uri, aligned_uri in self._mappings.items():
            if base_uri in resource_uri:
                return resource_uri.replace(base_uri, aligned_uri)

        LOGGER.warning(
            'JIRA Resource Alignment Failed: %s has no valid uri mapping',
            resource_uri,
        )

        return resource_uri
