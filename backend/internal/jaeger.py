"""
Purpose: Interacts with the Jaeger API.
Functionality: Provides methods to query traces and services from Jaeger.
Connection: Used by responses.py and validation.py to gather trace data and validate configurations.

Wrapper around the internal Jaeger tracing API"""
from typing import Optional, Union

import requests
from requests.adapters import HTTPAdapter, Retry
import logging

from backend.internal.models.orchestrator import Orchestrator

from backend.internal.errors import JaegerException

logger = logging.getLogger(__name__)


# NOTE: jaeger timestamps wire format is microseconds since epoch in utc cf.
# https://github.com/jaegertracing/jaeger/pull/712


class Jaeger:
    """
    Wrapper around the undocumented Jaeger HTTP API.
    """

    def __init__(self, orchestrator: Orchestrator, jaeger_service_name: str = "jaeger"):
        assert orchestrator is not None
        self.orchestrator = orchestrator
        self.session = requests.Session()
        retries = Retry(
            total=5, backoff_factor=0.1, status_forcelist=[500, 502, 503, 504]
        )
        """Retry policy. Force retries on server errors"""
        self.session.mount("http://", HTTPAdapter(max_retries=retries))
        """Mount the retry adapter"""
        address = orchestrator.get_jaeger_address()
        assert address is not None
        self.base_url = f"http://{address}:16686/jaeger/ui/api/"
        """Jaeger base url"""
        self.endpoints = {
            "traces": "traces",
            "services": "services",
            "operations": "services/%s/operations",
            "dependencies": "dependencies",
            "trace": "traces/%s",
        }
        """Jaeger API endpoints"""

    def get_services(self) -> Union[list, None]:
        """Returns a list of all services"""
        endpoint = self.endpoints.get("services")
        if endpoint is None:
            raise JaegerException(
                message="Invalid Jaeger endpoint",
                explanation="The services endpoint is invalid",
            )
        url = self.base_url + endpoint
        try:
            response = self.session.get(
                url=url,
            )
            response.raise_for_status()
            response_json = response.json()
            try:
                return list(response_json["data"])
            except KeyError as error:
                logger.error("Received invalid response from Jaeger")
                raise JaegerException from error
        except requests.exceptions.HTTPError as error:
            logger.error(error)
            raise JaegerException from error
        except requests.exceptions.ConnectionError as error:
            logger.error(f"Could not connect to jaeger at {url}")
            raise JaegerException from error

    def search_traces(
        self,
        start=None,
        end=None,
        limit=None,
        lookback=None,
        max_duration=None,
        min_duration=None,
        service_name="adservice",
    ) -> Optional[dict]:
        """Search Jaeger traces"""
        traces = self.endpoints.get("traces")
        if traces is None:
            raise JaegerException(
                message="Invalid Jaeger endpoint",
                explanation="The traces endpoint is invalid",
            )
        endpoint = self.base_url + traces
        params = {
            "start": start,
            "end": end,
            "lookback": lookback,
            "maxDuration": max_duration,
            "minDuration": min_duration,
            "service": service_name,
            "limit": limit,
        }
        try:
            logger.info(f"Fetching jaeger traces from {start} to {end}")
            response = self.session.get(url=endpoint, params=params)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as error:
            raise JaegerException(
                message=f"Error while talking to Jaeger at {endpoint}",
                explanation=error,
            )

    def get_service_operations(self, service="adservice") -> [dict, None]:
        """Get all service operations for a given service from Jaeger"""
        operations = self.endpoints.get("operations")
        if operations is None:
            raise JaegerException(
                message="Invalid Jaeger endpoint",
                explanation="The operations endpoint is invalid",
            )
        endpoint = self.base_url + operations
        endpoint = endpoint % service
        try:
            response = self.session.get(endpoint)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as error:
            raise JaegerException(
                message=f"Error while talking to Jaeger at {endpoint}",
                explanation=error,
            )

    def get_dependencies(self, end_timestamp=None, lookback=604800000) -> [dict, None]:
        """Get a dependency graph from Jaeger"""
        dependencies = self.endpoints.get("dependencies")
        if dependencies is None:
            raise JaegerException(
                message="Invalid Jaeger endpoint",
                explanation="The dependencies endpoint is invalid",
            )
        endpoint = self.base_url + dependencies
        params = {"endTs": end_timestamp, "lookback": lookback}
        try:
            response = self.session.get(endpoint, params=params)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as error:
            raise JaegerException(
                message=f"Error while talking to Jaeger at {endpoint}",
                explanation=error,
            )

    def get_trace_by_id(self, trace_id) -> [dict, None]:
        """Get a single Jaeger trace by a trace id"""
        trace = self.endpoints.get("trace")
        if trace is None:
            raise JaegerException(
                message="Invalid Jaeger endpoint",
                explanation="The trace endpoint is invalid",
            )
        endpoint = self.base_url + trace % trace_id
        try:
            response = self.session.get(endpoint)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as error:
            raise JaegerException(
                message=f"Error while talking to Jaeger at {endpoint}",
                explanation=error,
            )
