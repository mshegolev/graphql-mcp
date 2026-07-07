from __future__ import annotations

import logging
from urllib.parse import quote

import httpx
from graphql import build_schema
from graphql.error import GraphQLError

from generic_graphql_mcp.domain.models import SchemaGraph

logger = logging.getLogger(__name__)


class GitLabSource:
    """Outbound adapter: fetch SDL from GitLab repository files API (raw endpoint)."""

    def __init__(
        self,
        gitlab_url: str,
        project_id: str,
        file_path: str,
        ref: str = "HEAD",
        token: str = "",
        timeout: float = 30.0,
        ssl_verify: bool = True,
    ) -> None:
        self._gitlab_url = gitlab_url.rstrip("/")
        self._project_id = project_id
        self._file_path = file_path
        self._ref = ref
        self._token = token
        self._timeout = timeout
        self._ssl_verify = ssl_verify

    @property
    def name(self) -> str:
        return "gitlab"

    def fetch_schema(self) -> SchemaGraph | None:
        encoded_path = quote(self._file_path, safe="")
        url = f"{self._gitlab_url}/api/v4/projects/{self._project_id}/repository/files/{encoded_path}/raw"
        headers: dict[str, str] = {}
        if self._token:
            headers["PRIVATE-TOKEN"] = self._token

        try:
            response = httpx.get(
                url,
                params={"ref": self._ref},
                headers=headers,
                timeout=self._timeout,
                verify=self._ssl_verify,
            )
            response.raise_for_status()
        except (httpx.HTTPError, OSError) as exc:
            logger.debug("GitLab source failed: %s", exc)
            return None

        sdl_text = response.text
        try:
            build_schema(sdl_text)  # validate SDL parses
        except GraphQLError as exc:
            logger.debug("GitLab SDL parse failed: %s", exc)
            return None

        return SchemaGraph(sdl=sdl_text, source_name="gitlab")
