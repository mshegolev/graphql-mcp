from __future__ import annotations

import logging
import time
from typing import TYPE_CHECKING

from graphql_mcp.domain.errors import SchemaResolutionError

if TYPE_CHECKING:
    from collections.abc import Sequence

    from graphql_mcp.domain.models import SchemaGraph
    from graphql_mcp.ports.schema_source import SchemaSource

logger = logging.getLogger(__name__)


from mutmut.mutation.trampoline import wrap_in_trampoline as _mutmut_mutated, MutantDict
mutants_xǁSchemaServiceǁ__init____mutmut: MutantDict = {}  # type: ignore
mutants_xǁSchemaServiceǁresolve__mutmut: MutantDict = {}  # type: ignore
mutants_xǁSchemaServiceǁinvalidate__mutmut: MutantDict = {}  # type: ignore


class SchemaService:
    """Resolves schema through a cascade of sources with TTL cache.

    Sources are tried in priority order. The first source that returns
    a non-None SchemaGraph wins. The result is cached for ``ttl_seconds``.
    """

    @_mutmut_mutated(mutants_xǁSchemaServiceǁ__init____mutmut)
    def __init__(
        self,
        sources: Sequence[SchemaSource],
        ttl_seconds: float = 300.0,
    ) -> None:
        self._sources = sources
        self._ttl = ttl_seconds
        self._cached: SchemaGraph | None = None
        self._cached_at: float = 0.0

    def xǁSchemaServiceǁ__init____mutmut_orig(
        self,
        sources: Sequence[SchemaSource],
        ttl_seconds: float = 300.0,
    ) -> None:
        self._sources = sources
        self._ttl = ttl_seconds
        self._cached: SchemaGraph | None = None
        self._cached_at: float = 0.0

    def xǁSchemaServiceǁ__init____mutmut_1(
        self,
        sources: Sequence[SchemaSource],
        ttl_seconds: float = 301.0,
    ) -> None:
        self._sources = sources
        self._ttl = ttl_seconds
        self._cached: SchemaGraph | None = None
        self._cached_at: float = 0.0

    def xǁSchemaServiceǁ__init____mutmut_2(
        self,
        sources: Sequence[SchemaSource],
        ttl_seconds: float = 300.0,
    ) -> None:
        self._sources = None
        self._ttl = ttl_seconds
        self._cached: SchemaGraph | None = None
        self._cached_at: float = 0.0

    def xǁSchemaServiceǁ__init____mutmut_3(
        self,
        sources: Sequence[SchemaSource],
        ttl_seconds: float = 300.0,
    ) -> None:
        self._sources = sources
        self._ttl = None
        self._cached: SchemaGraph | None = None
        self._cached_at: float = 0.0

    def xǁSchemaServiceǁ__init____mutmut_4(
        self,
        sources: Sequence[SchemaSource],
        ttl_seconds: float = 300.0,
    ) -> None:
        self._sources = sources
        self._ttl = ttl_seconds
        self._cached: SchemaGraph | None = ""
        self._cached_at: float = 0.0

    def xǁSchemaServiceǁ__init____mutmut_5(
        self,
        sources: Sequence[SchemaSource],
        ttl_seconds: float = 300.0,
    ) -> None:
        self._sources = sources
        self._ttl = ttl_seconds
        self._cached: SchemaGraph | None = None
        self._cached_at: float = None

    def xǁSchemaServiceǁ__init____mutmut_6(
        self,
        sources: Sequence[SchemaSource],
        ttl_seconds: float = 300.0,
    ) -> None:
        self._sources = sources
        self._ttl = ttl_seconds
        self._cached: SchemaGraph | None = None
        self._cached_at: float = 1.0

    @_mutmut_mutated(mutants_xǁSchemaServiceǁresolve__mutmut)
    def resolve(self) -> SchemaGraph:
        """Return cached schema or resolve through the cascade.

        Raises:
            SchemaResolutionError: When all sources fail.
        """
        now = time.monotonic()
        if self._cached is not None and (now - self._cached_at) < self._ttl:
            logger.debug("Returning cached schema (age=%.1fs)", now - self._cached_at)
            return self._cached

        for source in self._sources:
            try:
                schema = source.fetch_schema()
                if schema is not None:
                    logger.info("Schema resolved from %s", source.name)
                    self._cached = schema
                    self._cached_at = time.monotonic()
                    return schema
            except Exception:
                logger.debug("Source %s failed, trying next", source.name, exc_info=True)
                continue

        raise SchemaResolutionError("All schema sources failed")

    def xǁSchemaServiceǁresolve__mutmut_orig(self) -> SchemaGraph:
        """Return cached schema or resolve through the cascade.

        Raises:
            SchemaResolutionError: When all sources fail.
        """
        now = time.monotonic()
        if self._cached is not None and (now - self._cached_at) < self._ttl:
            logger.debug("Returning cached schema (age=%.1fs)", now - self._cached_at)
            return self._cached

        for source in self._sources:
            try:
                schema = source.fetch_schema()
                if schema is not None:
                    logger.info("Schema resolved from %s", source.name)
                    self._cached = schema
                    self._cached_at = time.monotonic()
                    return schema
            except Exception:
                logger.debug("Source %s failed, trying next", source.name, exc_info=True)
                continue

        raise SchemaResolutionError("All schema sources failed")

    def xǁSchemaServiceǁresolve__mutmut_1(self) -> SchemaGraph:
        """Return cached schema or resolve through the cascade.

        Raises:
            SchemaResolutionError: When all sources fail.
        """
        now = None
        if self._cached is not None and (now - self._cached_at) < self._ttl:
            logger.debug("Returning cached schema (age=%.1fs)", now - self._cached_at)
            return self._cached

        for source in self._sources:
            try:
                schema = source.fetch_schema()
                if schema is not None:
                    logger.info("Schema resolved from %s", source.name)
                    self._cached = schema
                    self._cached_at = time.monotonic()
                    return schema
            except Exception:
                logger.debug("Source %s failed, trying next", source.name, exc_info=True)
                continue

        raise SchemaResolutionError("All schema sources failed")

    def xǁSchemaServiceǁresolve__mutmut_2(self) -> SchemaGraph:
        """Return cached schema or resolve through the cascade.

        Raises:
            SchemaResolutionError: When all sources fail.
        """
        now = time.monotonic()
        if self._cached is not None or (now - self._cached_at) < self._ttl:
            logger.debug("Returning cached schema (age=%.1fs)", now - self._cached_at)
            return self._cached

        for source in self._sources:
            try:
                schema = source.fetch_schema()
                if schema is not None:
                    logger.info("Schema resolved from %s", source.name)
                    self._cached = schema
                    self._cached_at = time.monotonic()
                    return schema
            except Exception:
                logger.debug("Source %s failed, trying next", source.name, exc_info=True)
                continue

        raise SchemaResolutionError("All schema sources failed")

    def xǁSchemaServiceǁresolve__mutmut_3(self) -> SchemaGraph:
        """Return cached schema or resolve through the cascade.

        Raises:
            SchemaResolutionError: When all sources fail.
        """
        now = time.monotonic()
        if self._cached is None and (now - self._cached_at) < self._ttl:
            logger.debug("Returning cached schema (age=%.1fs)", now - self._cached_at)
            return self._cached

        for source in self._sources:
            try:
                schema = source.fetch_schema()
                if schema is not None:
                    logger.info("Schema resolved from %s", source.name)
                    self._cached = schema
                    self._cached_at = time.monotonic()
                    return schema
            except Exception:
                logger.debug("Source %s failed, trying next", source.name, exc_info=True)
                continue

        raise SchemaResolutionError("All schema sources failed")

    def xǁSchemaServiceǁresolve__mutmut_4(self) -> SchemaGraph:
        """Return cached schema or resolve through the cascade.

        Raises:
            SchemaResolutionError: When all sources fail.
        """
        now = time.monotonic()
        if self._cached is not None and (now + self._cached_at) < self._ttl:
            logger.debug("Returning cached schema (age=%.1fs)", now - self._cached_at)
            return self._cached

        for source in self._sources:
            try:
                schema = source.fetch_schema()
                if schema is not None:
                    logger.info("Schema resolved from %s", source.name)
                    self._cached = schema
                    self._cached_at = time.monotonic()
                    return schema
            except Exception:
                logger.debug("Source %s failed, trying next", source.name, exc_info=True)
                continue

        raise SchemaResolutionError("All schema sources failed")

    def xǁSchemaServiceǁresolve__mutmut_5(self) -> SchemaGraph:
        """Return cached schema or resolve through the cascade.

        Raises:
            SchemaResolutionError: When all sources fail.
        """
        now = time.monotonic()
        if self._cached is not None and (now - self._cached_at) <= self._ttl:
            logger.debug("Returning cached schema (age=%.1fs)", now - self._cached_at)
            return self._cached

        for source in self._sources:
            try:
                schema = source.fetch_schema()
                if schema is not None:
                    logger.info("Schema resolved from %s", source.name)
                    self._cached = schema
                    self._cached_at = time.monotonic()
                    return schema
            except Exception:
                logger.debug("Source %s failed, trying next", source.name, exc_info=True)
                continue

        raise SchemaResolutionError("All schema sources failed")

    def xǁSchemaServiceǁresolve__mutmut_6(self) -> SchemaGraph:
        """Return cached schema or resolve through the cascade.

        Raises:
            SchemaResolutionError: When all sources fail.
        """
        now = time.monotonic()
        if self._cached is not None and (now - self._cached_at) < self._ttl:
            logger.debug(None, now - self._cached_at)
            return self._cached

        for source in self._sources:
            try:
                schema = source.fetch_schema()
                if schema is not None:
                    logger.info("Schema resolved from %s", source.name)
                    self._cached = schema
                    self._cached_at = time.monotonic()
                    return schema
            except Exception:
                logger.debug("Source %s failed, trying next", source.name, exc_info=True)
                continue

        raise SchemaResolutionError("All schema sources failed")

    def xǁSchemaServiceǁresolve__mutmut_7(self) -> SchemaGraph:
        """Return cached schema or resolve through the cascade.

        Raises:
            SchemaResolutionError: When all sources fail.
        """
        now = time.monotonic()
        if self._cached is not None and (now - self._cached_at) < self._ttl:
            logger.debug("Returning cached schema (age=%.1fs)", None)
            return self._cached

        for source in self._sources:
            try:
                schema = source.fetch_schema()
                if schema is not None:
                    logger.info("Schema resolved from %s", source.name)
                    self._cached = schema
                    self._cached_at = time.monotonic()
                    return schema
            except Exception:
                logger.debug("Source %s failed, trying next", source.name, exc_info=True)
                continue

        raise SchemaResolutionError("All schema sources failed")

    def xǁSchemaServiceǁresolve__mutmut_8(self) -> SchemaGraph:
        """Return cached schema or resolve through the cascade.

        Raises:
            SchemaResolutionError: When all sources fail.
        """
        now = time.monotonic()
        if self._cached is not None and (now - self._cached_at) < self._ttl:
            logger.debug(now - self._cached_at)
            return self._cached

        for source in self._sources:
            try:
                schema = source.fetch_schema()
                if schema is not None:
                    logger.info("Schema resolved from %s", source.name)
                    self._cached = schema
                    self._cached_at = time.monotonic()
                    return schema
            except Exception:
                logger.debug("Source %s failed, trying next", source.name, exc_info=True)
                continue

        raise SchemaResolutionError("All schema sources failed")

    def xǁSchemaServiceǁresolve__mutmut_9(self) -> SchemaGraph:
        """Return cached schema or resolve through the cascade.

        Raises:
            SchemaResolutionError: When all sources fail.
        """
        now = time.monotonic()
        if self._cached is not None and (now - self._cached_at) < self._ttl:
            logger.debug("Returning cached schema (age=%.1fs)", )
            return self._cached

        for source in self._sources:
            try:
                schema = source.fetch_schema()
                if schema is not None:
                    logger.info("Schema resolved from %s", source.name)
                    self._cached = schema
                    self._cached_at = time.monotonic()
                    return schema
            except Exception:
                logger.debug("Source %s failed, trying next", source.name, exc_info=True)
                continue

        raise SchemaResolutionError("All schema sources failed")

    def xǁSchemaServiceǁresolve__mutmut_10(self) -> SchemaGraph:
        """Return cached schema or resolve through the cascade.

        Raises:
            SchemaResolutionError: When all sources fail.
        """
        now = time.monotonic()
        if self._cached is not None and (now - self._cached_at) < self._ttl:
            logger.debug("XXReturning cached schema (age=%.1fs)XX", now - self._cached_at)
            return self._cached

        for source in self._sources:
            try:
                schema = source.fetch_schema()
                if schema is not None:
                    logger.info("Schema resolved from %s", source.name)
                    self._cached = schema
                    self._cached_at = time.monotonic()
                    return schema
            except Exception:
                logger.debug("Source %s failed, trying next", source.name, exc_info=True)
                continue

        raise SchemaResolutionError("All schema sources failed")

    def xǁSchemaServiceǁresolve__mutmut_11(self) -> SchemaGraph:
        """Return cached schema or resolve through the cascade.

        Raises:
            SchemaResolutionError: When all sources fail.
        """
        now = time.monotonic()
        if self._cached is not None and (now - self._cached_at) < self._ttl:
            logger.debug("returning cached schema (age=%.1fs)", now - self._cached_at)
            return self._cached

        for source in self._sources:
            try:
                schema = source.fetch_schema()
                if schema is not None:
                    logger.info("Schema resolved from %s", source.name)
                    self._cached = schema
                    self._cached_at = time.monotonic()
                    return schema
            except Exception:
                logger.debug("Source %s failed, trying next", source.name, exc_info=True)
                continue

        raise SchemaResolutionError("All schema sources failed")

    def xǁSchemaServiceǁresolve__mutmut_12(self) -> SchemaGraph:
        """Return cached schema or resolve through the cascade.

        Raises:
            SchemaResolutionError: When all sources fail.
        """
        now = time.monotonic()
        if self._cached is not None and (now - self._cached_at) < self._ttl:
            logger.debug("RETURNING CACHED SCHEMA (AGE=%.1FS)", now - self._cached_at)
            return self._cached

        for source in self._sources:
            try:
                schema = source.fetch_schema()
                if schema is not None:
                    logger.info("Schema resolved from %s", source.name)
                    self._cached = schema
                    self._cached_at = time.monotonic()
                    return schema
            except Exception:
                logger.debug("Source %s failed, trying next", source.name, exc_info=True)
                continue

        raise SchemaResolutionError("All schema sources failed")

    def xǁSchemaServiceǁresolve__mutmut_13(self) -> SchemaGraph:
        """Return cached schema or resolve through the cascade.

        Raises:
            SchemaResolutionError: When all sources fail.
        """
        now = time.monotonic()
        if self._cached is not None and (now - self._cached_at) < self._ttl:
            logger.debug("Returning cached schema (age=%.1fs)", now + self._cached_at)
            return self._cached

        for source in self._sources:
            try:
                schema = source.fetch_schema()
                if schema is not None:
                    logger.info("Schema resolved from %s", source.name)
                    self._cached = schema
                    self._cached_at = time.monotonic()
                    return schema
            except Exception:
                logger.debug("Source %s failed, trying next", source.name, exc_info=True)
                continue

        raise SchemaResolutionError("All schema sources failed")

    def xǁSchemaServiceǁresolve__mutmut_14(self) -> SchemaGraph:
        """Return cached schema or resolve through the cascade.

        Raises:
            SchemaResolutionError: When all sources fail.
        """
        now = time.monotonic()
        if self._cached is not None and (now - self._cached_at) < self._ttl:
            logger.debug("Returning cached schema (age=%.1fs)", now - self._cached_at)
            return self._cached

        for source in self._sources:
            try:
                schema = None
                if schema is not None:
                    logger.info("Schema resolved from %s", source.name)
                    self._cached = schema
                    self._cached_at = time.monotonic()
                    return schema
            except Exception:
                logger.debug("Source %s failed, trying next", source.name, exc_info=True)
                continue

        raise SchemaResolutionError("All schema sources failed")

    def xǁSchemaServiceǁresolve__mutmut_15(self) -> SchemaGraph:
        """Return cached schema or resolve through the cascade.

        Raises:
            SchemaResolutionError: When all sources fail.
        """
        now = time.monotonic()
        if self._cached is not None and (now - self._cached_at) < self._ttl:
            logger.debug("Returning cached schema (age=%.1fs)", now - self._cached_at)
            return self._cached

        for source in self._sources:
            try:
                schema = source.fetch_schema()
                if schema is None:
                    logger.info("Schema resolved from %s", source.name)
                    self._cached = schema
                    self._cached_at = time.monotonic()
                    return schema
            except Exception:
                logger.debug("Source %s failed, trying next", source.name, exc_info=True)
                continue

        raise SchemaResolutionError("All schema sources failed")

    def xǁSchemaServiceǁresolve__mutmut_16(self) -> SchemaGraph:
        """Return cached schema or resolve through the cascade.

        Raises:
            SchemaResolutionError: When all sources fail.
        """
        now = time.monotonic()
        if self._cached is not None and (now - self._cached_at) < self._ttl:
            logger.debug("Returning cached schema (age=%.1fs)", now - self._cached_at)
            return self._cached

        for source in self._sources:
            try:
                schema = source.fetch_schema()
                if schema is not None:
                    logger.info(None, source.name)
                    self._cached = schema
                    self._cached_at = time.monotonic()
                    return schema
            except Exception:
                logger.debug("Source %s failed, trying next", source.name, exc_info=True)
                continue

        raise SchemaResolutionError("All schema sources failed")

    def xǁSchemaServiceǁresolve__mutmut_17(self) -> SchemaGraph:
        """Return cached schema or resolve through the cascade.

        Raises:
            SchemaResolutionError: When all sources fail.
        """
        now = time.monotonic()
        if self._cached is not None and (now - self._cached_at) < self._ttl:
            logger.debug("Returning cached schema (age=%.1fs)", now - self._cached_at)
            return self._cached

        for source in self._sources:
            try:
                schema = source.fetch_schema()
                if schema is not None:
                    logger.info("Schema resolved from %s", None)
                    self._cached = schema
                    self._cached_at = time.monotonic()
                    return schema
            except Exception:
                logger.debug("Source %s failed, trying next", source.name, exc_info=True)
                continue

        raise SchemaResolutionError("All schema sources failed")

    def xǁSchemaServiceǁresolve__mutmut_18(self) -> SchemaGraph:
        """Return cached schema or resolve through the cascade.

        Raises:
            SchemaResolutionError: When all sources fail.
        """
        now = time.monotonic()
        if self._cached is not None and (now - self._cached_at) < self._ttl:
            logger.debug("Returning cached schema (age=%.1fs)", now - self._cached_at)
            return self._cached

        for source in self._sources:
            try:
                schema = source.fetch_schema()
                if schema is not None:
                    logger.info(source.name)
                    self._cached = schema
                    self._cached_at = time.monotonic()
                    return schema
            except Exception:
                logger.debug("Source %s failed, trying next", source.name, exc_info=True)
                continue

        raise SchemaResolutionError("All schema sources failed")

    def xǁSchemaServiceǁresolve__mutmut_19(self) -> SchemaGraph:
        """Return cached schema or resolve through the cascade.

        Raises:
            SchemaResolutionError: When all sources fail.
        """
        now = time.monotonic()
        if self._cached is not None and (now - self._cached_at) < self._ttl:
            logger.debug("Returning cached schema (age=%.1fs)", now - self._cached_at)
            return self._cached

        for source in self._sources:
            try:
                schema = source.fetch_schema()
                if schema is not None:
                    logger.info("Schema resolved from %s", )
                    self._cached = schema
                    self._cached_at = time.monotonic()
                    return schema
            except Exception:
                logger.debug("Source %s failed, trying next", source.name, exc_info=True)
                continue

        raise SchemaResolutionError("All schema sources failed")

    def xǁSchemaServiceǁresolve__mutmut_20(self) -> SchemaGraph:
        """Return cached schema or resolve through the cascade.

        Raises:
            SchemaResolutionError: When all sources fail.
        """
        now = time.monotonic()
        if self._cached is not None and (now - self._cached_at) < self._ttl:
            logger.debug("Returning cached schema (age=%.1fs)", now - self._cached_at)
            return self._cached

        for source in self._sources:
            try:
                schema = source.fetch_schema()
                if schema is not None:
                    logger.info("XXSchema resolved from %sXX", source.name)
                    self._cached = schema
                    self._cached_at = time.monotonic()
                    return schema
            except Exception:
                logger.debug("Source %s failed, trying next", source.name, exc_info=True)
                continue

        raise SchemaResolutionError("All schema sources failed")

    def xǁSchemaServiceǁresolve__mutmut_21(self) -> SchemaGraph:
        """Return cached schema or resolve through the cascade.

        Raises:
            SchemaResolutionError: When all sources fail.
        """
        now = time.monotonic()
        if self._cached is not None and (now - self._cached_at) < self._ttl:
            logger.debug("Returning cached schema (age=%.1fs)", now - self._cached_at)
            return self._cached

        for source in self._sources:
            try:
                schema = source.fetch_schema()
                if schema is not None:
                    logger.info("schema resolved from %s", source.name)
                    self._cached = schema
                    self._cached_at = time.monotonic()
                    return schema
            except Exception:
                logger.debug("Source %s failed, trying next", source.name, exc_info=True)
                continue

        raise SchemaResolutionError("All schema sources failed")

    def xǁSchemaServiceǁresolve__mutmut_22(self) -> SchemaGraph:
        """Return cached schema or resolve through the cascade.

        Raises:
            SchemaResolutionError: When all sources fail.
        """
        now = time.monotonic()
        if self._cached is not None and (now - self._cached_at) < self._ttl:
            logger.debug("Returning cached schema (age=%.1fs)", now - self._cached_at)
            return self._cached

        for source in self._sources:
            try:
                schema = source.fetch_schema()
                if schema is not None:
                    logger.info("SCHEMA RESOLVED FROM %S", source.name)
                    self._cached = schema
                    self._cached_at = time.monotonic()
                    return schema
            except Exception:
                logger.debug("Source %s failed, trying next", source.name, exc_info=True)
                continue

        raise SchemaResolutionError("All schema sources failed")

    def xǁSchemaServiceǁresolve__mutmut_23(self) -> SchemaGraph:
        """Return cached schema or resolve through the cascade.

        Raises:
            SchemaResolutionError: When all sources fail.
        """
        now = time.monotonic()
        if self._cached is not None and (now - self._cached_at) < self._ttl:
            logger.debug("Returning cached schema (age=%.1fs)", now - self._cached_at)
            return self._cached

        for source in self._sources:
            try:
                schema = source.fetch_schema()
                if schema is not None:
                    logger.info("Schema resolved from %s", source.name)
                    self._cached = None
                    self._cached_at = time.monotonic()
                    return schema
            except Exception:
                logger.debug("Source %s failed, trying next", source.name, exc_info=True)
                continue

        raise SchemaResolutionError("All schema sources failed")

    def xǁSchemaServiceǁresolve__mutmut_24(self) -> SchemaGraph:
        """Return cached schema or resolve through the cascade.

        Raises:
            SchemaResolutionError: When all sources fail.
        """
        now = time.monotonic()
        if self._cached is not None and (now - self._cached_at) < self._ttl:
            logger.debug("Returning cached schema (age=%.1fs)", now - self._cached_at)
            return self._cached

        for source in self._sources:
            try:
                schema = source.fetch_schema()
                if schema is not None:
                    logger.info("Schema resolved from %s", source.name)
                    self._cached = schema
                    self._cached_at = None
                    return schema
            except Exception:
                logger.debug("Source %s failed, trying next", source.name, exc_info=True)
                continue

        raise SchemaResolutionError("All schema sources failed")

    def xǁSchemaServiceǁresolve__mutmut_25(self) -> SchemaGraph:
        """Return cached schema or resolve through the cascade.

        Raises:
            SchemaResolutionError: When all sources fail.
        """
        now = time.monotonic()
        if self._cached is not None and (now - self._cached_at) < self._ttl:
            logger.debug("Returning cached schema (age=%.1fs)", now - self._cached_at)
            return self._cached

        for source in self._sources:
            try:
                schema = source.fetch_schema()
                if schema is not None:
                    logger.info("Schema resolved from %s", source.name)
                    self._cached = schema
                    self._cached_at = time.monotonic()
                    return schema
            except Exception:
                logger.debug(None, source.name, exc_info=True)
                continue

        raise SchemaResolutionError("All schema sources failed")

    def xǁSchemaServiceǁresolve__mutmut_26(self) -> SchemaGraph:
        """Return cached schema or resolve through the cascade.

        Raises:
            SchemaResolutionError: When all sources fail.
        """
        now = time.monotonic()
        if self._cached is not None and (now - self._cached_at) < self._ttl:
            logger.debug("Returning cached schema (age=%.1fs)", now - self._cached_at)
            return self._cached

        for source in self._sources:
            try:
                schema = source.fetch_schema()
                if schema is not None:
                    logger.info("Schema resolved from %s", source.name)
                    self._cached = schema
                    self._cached_at = time.monotonic()
                    return schema
            except Exception:
                logger.debug("Source %s failed, trying next", None, exc_info=True)
                continue

        raise SchemaResolutionError("All schema sources failed")

    def xǁSchemaServiceǁresolve__mutmut_27(self) -> SchemaGraph:
        """Return cached schema or resolve through the cascade.

        Raises:
            SchemaResolutionError: When all sources fail.
        """
        now = time.monotonic()
        if self._cached is not None and (now - self._cached_at) < self._ttl:
            logger.debug("Returning cached schema (age=%.1fs)", now - self._cached_at)
            return self._cached

        for source in self._sources:
            try:
                schema = source.fetch_schema()
                if schema is not None:
                    logger.info("Schema resolved from %s", source.name)
                    self._cached = schema
                    self._cached_at = time.monotonic()
                    return schema
            except Exception:
                logger.debug("Source %s failed, trying next", source.name, exc_info=None)
                continue

        raise SchemaResolutionError("All schema sources failed")

    def xǁSchemaServiceǁresolve__mutmut_28(self) -> SchemaGraph:
        """Return cached schema or resolve through the cascade.

        Raises:
            SchemaResolutionError: When all sources fail.
        """
        now = time.monotonic()
        if self._cached is not None and (now - self._cached_at) < self._ttl:
            logger.debug("Returning cached schema (age=%.1fs)", now - self._cached_at)
            return self._cached

        for source in self._sources:
            try:
                schema = source.fetch_schema()
                if schema is not None:
                    logger.info("Schema resolved from %s", source.name)
                    self._cached = schema
                    self._cached_at = time.monotonic()
                    return schema
            except Exception:
                logger.debug(source.name, exc_info=True)
                continue

        raise SchemaResolutionError("All schema sources failed")

    def xǁSchemaServiceǁresolve__mutmut_29(self) -> SchemaGraph:
        """Return cached schema or resolve through the cascade.

        Raises:
            SchemaResolutionError: When all sources fail.
        """
        now = time.monotonic()
        if self._cached is not None and (now - self._cached_at) < self._ttl:
            logger.debug("Returning cached schema (age=%.1fs)", now - self._cached_at)
            return self._cached

        for source in self._sources:
            try:
                schema = source.fetch_schema()
                if schema is not None:
                    logger.info("Schema resolved from %s", source.name)
                    self._cached = schema
                    self._cached_at = time.monotonic()
                    return schema
            except Exception:
                logger.debug("Source %s failed, trying next", exc_info=True)
                continue

        raise SchemaResolutionError("All schema sources failed")

    def xǁSchemaServiceǁresolve__mutmut_30(self) -> SchemaGraph:
        """Return cached schema or resolve through the cascade.

        Raises:
            SchemaResolutionError: When all sources fail.
        """
        now = time.monotonic()
        if self._cached is not None and (now - self._cached_at) < self._ttl:
            logger.debug("Returning cached schema (age=%.1fs)", now - self._cached_at)
            return self._cached

        for source in self._sources:
            try:
                schema = source.fetch_schema()
                if schema is not None:
                    logger.info("Schema resolved from %s", source.name)
                    self._cached = schema
                    self._cached_at = time.monotonic()
                    return schema
            except Exception:
                logger.debug("Source %s failed, trying next", source.name, )
                continue

        raise SchemaResolutionError("All schema sources failed")

    def xǁSchemaServiceǁresolve__mutmut_31(self) -> SchemaGraph:
        """Return cached schema or resolve through the cascade.

        Raises:
            SchemaResolutionError: When all sources fail.
        """
        now = time.monotonic()
        if self._cached is not None and (now - self._cached_at) < self._ttl:
            logger.debug("Returning cached schema (age=%.1fs)", now - self._cached_at)
            return self._cached

        for source in self._sources:
            try:
                schema = source.fetch_schema()
                if schema is not None:
                    logger.info("Schema resolved from %s", source.name)
                    self._cached = schema
                    self._cached_at = time.monotonic()
                    return schema
            except Exception:
                logger.debug("XXSource %s failed, trying nextXX", source.name, exc_info=True)
                continue

        raise SchemaResolutionError("All schema sources failed")

    def xǁSchemaServiceǁresolve__mutmut_32(self) -> SchemaGraph:
        """Return cached schema or resolve through the cascade.

        Raises:
            SchemaResolutionError: When all sources fail.
        """
        now = time.monotonic()
        if self._cached is not None and (now - self._cached_at) < self._ttl:
            logger.debug("Returning cached schema (age=%.1fs)", now - self._cached_at)
            return self._cached

        for source in self._sources:
            try:
                schema = source.fetch_schema()
                if schema is not None:
                    logger.info("Schema resolved from %s", source.name)
                    self._cached = schema
                    self._cached_at = time.monotonic()
                    return schema
            except Exception:
                logger.debug("source %s failed, trying next", source.name, exc_info=True)
                continue

        raise SchemaResolutionError("All schema sources failed")

    def xǁSchemaServiceǁresolve__mutmut_33(self) -> SchemaGraph:
        """Return cached schema or resolve through the cascade.

        Raises:
            SchemaResolutionError: When all sources fail.
        """
        now = time.monotonic()
        if self._cached is not None and (now - self._cached_at) < self._ttl:
            logger.debug("Returning cached schema (age=%.1fs)", now - self._cached_at)
            return self._cached

        for source in self._sources:
            try:
                schema = source.fetch_schema()
                if schema is not None:
                    logger.info("Schema resolved from %s", source.name)
                    self._cached = schema
                    self._cached_at = time.monotonic()
                    return schema
            except Exception:
                logger.debug("SOURCE %S FAILED, TRYING NEXT", source.name, exc_info=True)
                continue

        raise SchemaResolutionError("All schema sources failed")

    def xǁSchemaServiceǁresolve__mutmut_34(self) -> SchemaGraph:
        """Return cached schema or resolve through the cascade.

        Raises:
            SchemaResolutionError: When all sources fail.
        """
        now = time.monotonic()
        if self._cached is not None and (now - self._cached_at) < self._ttl:
            logger.debug("Returning cached schema (age=%.1fs)", now - self._cached_at)
            return self._cached

        for source in self._sources:
            try:
                schema = source.fetch_schema()
                if schema is not None:
                    logger.info("Schema resolved from %s", source.name)
                    self._cached = schema
                    self._cached_at = time.monotonic()
                    return schema
            except Exception:
                logger.debug("Source %s failed, trying next", source.name, exc_info=False)
                continue

        raise SchemaResolutionError("All schema sources failed")

    def xǁSchemaServiceǁresolve__mutmut_35(self) -> SchemaGraph:
        """Return cached schema or resolve through the cascade.

        Raises:
            SchemaResolutionError: When all sources fail.
        """
        now = time.monotonic()
        if self._cached is not None and (now - self._cached_at) < self._ttl:
            logger.debug("Returning cached schema (age=%.1fs)", now - self._cached_at)
            return self._cached

        for source in self._sources:
            try:
                schema = source.fetch_schema()
                if schema is not None:
                    logger.info("Schema resolved from %s", source.name)
                    self._cached = schema
                    self._cached_at = time.monotonic()
                    return schema
            except Exception:
                logger.debug("Source %s failed, trying next", source.name, exc_info=True)
                break

        raise SchemaResolutionError("All schema sources failed")

    def xǁSchemaServiceǁresolve__mutmut_36(self) -> SchemaGraph:
        """Return cached schema or resolve through the cascade.

        Raises:
            SchemaResolutionError: When all sources fail.
        """
        now = time.monotonic()
        if self._cached is not None and (now - self._cached_at) < self._ttl:
            logger.debug("Returning cached schema (age=%.1fs)", now - self._cached_at)
            return self._cached

        for source in self._sources:
            try:
                schema = source.fetch_schema()
                if schema is not None:
                    logger.info("Schema resolved from %s", source.name)
                    self._cached = schema
                    self._cached_at = time.monotonic()
                    return schema
            except Exception:
                logger.debug("Source %s failed, trying next", source.name, exc_info=True)
                continue

        raise SchemaResolutionError(None)

    def xǁSchemaServiceǁresolve__mutmut_37(self) -> SchemaGraph:
        """Return cached schema or resolve through the cascade.

        Raises:
            SchemaResolutionError: When all sources fail.
        """
        now = time.monotonic()
        if self._cached is not None and (now - self._cached_at) < self._ttl:
            logger.debug("Returning cached schema (age=%.1fs)", now - self._cached_at)
            return self._cached

        for source in self._sources:
            try:
                schema = source.fetch_schema()
                if schema is not None:
                    logger.info("Schema resolved from %s", source.name)
                    self._cached = schema
                    self._cached_at = time.monotonic()
                    return schema
            except Exception:
                logger.debug("Source %s failed, trying next", source.name, exc_info=True)
                continue

        raise SchemaResolutionError("XXAll schema sources failedXX")

    def xǁSchemaServiceǁresolve__mutmut_38(self) -> SchemaGraph:
        """Return cached schema or resolve through the cascade.

        Raises:
            SchemaResolutionError: When all sources fail.
        """
        now = time.monotonic()
        if self._cached is not None and (now - self._cached_at) < self._ttl:
            logger.debug("Returning cached schema (age=%.1fs)", now - self._cached_at)
            return self._cached

        for source in self._sources:
            try:
                schema = source.fetch_schema()
                if schema is not None:
                    logger.info("Schema resolved from %s", source.name)
                    self._cached = schema
                    self._cached_at = time.monotonic()
                    return schema
            except Exception:
                logger.debug("Source %s failed, trying next", source.name, exc_info=True)
                continue

        raise SchemaResolutionError("all schema sources failed")

    def xǁSchemaServiceǁresolve__mutmut_39(self) -> SchemaGraph:
        """Return cached schema or resolve through the cascade.

        Raises:
            SchemaResolutionError: When all sources fail.
        """
        now = time.monotonic()
        if self._cached is not None and (now - self._cached_at) < self._ttl:
            logger.debug("Returning cached schema (age=%.1fs)", now - self._cached_at)
            return self._cached

        for source in self._sources:
            try:
                schema = source.fetch_schema()
                if schema is not None:
                    logger.info("Schema resolved from %s", source.name)
                    self._cached = schema
                    self._cached_at = time.monotonic()
                    return schema
            except Exception:
                logger.debug("Source %s failed, trying next", source.name, exc_info=True)
                continue

        raise SchemaResolutionError("ALL SCHEMA SOURCES FAILED")

    @_mutmut_mutated(mutants_xǁSchemaServiceǁinvalidate__mutmut)
    def invalidate(self) -> None:
        """Clear cache, forcing next resolve() to re-fetch."""
        self._cached = None
        self._cached_at = 0.0

    def xǁSchemaServiceǁinvalidate__mutmut_orig(self) -> None:
        """Clear cache, forcing next resolve() to re-fetch."""
        self._cached = None
        self._cached_at = 0.0

    def xǁSchemaServiceǁinvalidate__mutmut_1(self) -> None:
        """Clear cache, forcing next resolve() to re-fetch."""
        self._cached = ""
        self._cached_at = 0.0

    def xǁSchemaServiceǁinvalidate__mutmut_2(self) -> None:
        """Clear cache, forcing next resolve() to re-fetch."""
        self._cached = None
        self._cached_at = None

    def xǁSchemaServiceǁinvalidate__mutmut_3(self) -> None:
        """Clear cache, forcing next resolve() to re-fetch."""
        self._cached = None
        self._cached_at = 1.0

mutants_xǁSchemaServiceǁ__init____mutmut['_mutmut_orig'] = SchemaService.xǁSchemaServiceǁ__init____mutmut_orig # type: ignore # mutmut generated
mutants_xǁSchemaServiceǁ__init____mutmut['xǁSchemaServiceǁ__init____mutmut_1'] = SchemaService.xǁSchemaServiceǁ__init____mutmut_1 # type: ignore # mutmut generated
mutants_xǁSchemaServiceǁ__init____mutmut['xǁSchemaServiceǁ__init____mutmut_2'] = SchemaService.xǁSchemaServiceǁ__init____mutmut_2 # type: ignore # mutmut generated
mutants_xǁSchemaServiceǁ__init____mutmut['xǁSchemaServiceǁ__init____mutmut_3'] = SchemaService.xǁSchemaServiceǁ__init____mutmut_3 # type: ignore # mutmut generated
mutants_xǁSchemaServiceǁ__init____mutmut['xǁSchemaServiceǁ__init____mutmut_4'] = SchemaService.xǁSchemaServiceǁ__init____mutmut_4 # type: ignore # mutmut generated
mutants_xǁSchemaServiceǁ__init____mutmut['xǁSchemaServiceǁ__init____mutmut_5'] = SchemaService.xǁSchemaServiceǁ__init____mutmut_5 # type: ignore # mutmut generated
mutants_xǁSchemaServiceǁ__init____mutmut['xǁSchemaServiceǁ__init____mutmut_6'] = SchemaService.xǁSchemaServiceǁ__init____mutmut_6 # type: ignore # mutmut generated

mutants_xǁSchemaServiceǁresolve__mutmut['_mutmut_orig'] = SchemaService.xǁSchemaServiceǁresolve__mutmut_orig # type: ignore # mutmut generated
mutants_xǁSchemaServiceǁresolve__mutmut['xǁSchemaServiceǁresolve__mutmut_1'] = SchemaService.xǁSchemaServiceǁresolve__mutmut_1 # type: ignore # mutmut generated
mutants_xǁSchemaServiceǁresolve__mutmut['xǁSchemaServiceǁresolve__mutmut_2'] = SchemaService.xǁSchemaServiceǁresolve__mutmut_2 # type: ignore # mutmut generated
mutants_xǁSchemaServiceǁresolve__mutmut['xǁSchemaServiceǁresolve__mutmut_3'] = SchemaService.xǁSchemaServiceǁresolve__mutmut_3 # type: ignore # mutmut generated
mutants_xǁSchemaServiceǁresolve__mutmut['xǁSchemaServiceǁresolve__mutmut_4'] = SchemaService.xǁSchemaServiceǁresolve__mutmut_4 # type: ignore # mutmut generated
mutants_xǁSchemaServiceǁresolve__mutmut['xǁSchemaServiceǁresolve__mutmut_5'] = SchemaService.xǁSchemaServiceǁresolve__mutmut_5 # type: ignore # mutmut generated
mutants_xǁSchemaServiceǁresolve__mutmut['xǁSchemaServiceǁresolve__mutmut_6'] = SchemaService.xǁSchemaServiceǁresolve__mutmut_6 # type: ignore # mutmut generated
mutants_xǁSchemaServiceǁresolve__mutmut['xǁSchemaServiceǁresolve__mutmut_7'] = SchemaService.xǁSchemaServiceǁresolve__mutmut_7 # type: ignore # mutmut generated
mutants_xǁSchemaServiceǁresolve__mutmut['xǁSchemaServiceǁresolve__mutmut_8'] = SchemaService.xǁSchemaServiceǁresolve__mutmut_8 # type: ignore # mutmut generated
mutants_xǁSchemaServiceǁresolve__mutmut['xǁSchemaServiceǁresolve__mutmut_9'] = SchemaService.xǁSchemaServiceǁresolve__mutmut_9 # type: ignore # mutmut generated
mutants_xǁSchemaServiceǁresolve__mutmut['xǁSchemaServiceǁresolve__mutmut_10'] = SchemaService.xǁSchemaServiceǁresolve__mutmut_10 # type: ignore # mutmut generated
mutants_xǁSchemaServiceǁresolve__mutmut['xǁSchemaServiceǁresolve__mutmut_11'] = SchemaService.xǁSchemaServiceǁresolve__mutmut_11 # type: ignore # mutmut generated
mutants_xǁSchemaServiceǁresolve__mutmut['xǁSchemaServiceǁresolve__mutmut_12'] = SchemaService.xǁSchemaServiceǁresolve__mutmut_12 # type: ignore # mutmut generated
mutants_xǁSchemaServiceǁresolve__mutmut['xǁSchemaServiceǁresolve__mutmut_13'] = SchemaService.xǁSchemaServiceǁresolve__mutmut_13 # type: ignore # mutmut generated
mutants_xǁSchemaServiceǁresolve__mutmut['xǁSchemaServiceǁresolve__mutmut_14'] = SchemaService.xǁSchemaServiceǁresolve__mutmut_14 # type: ignore # mutmut generated
mutants_xǁSchemaServiceǁresolve__mutmut['xǁSchemaServiceǁresolve__mutmut_15'] = SchemaService.xǁSchemaServiceǁresolve__mutmut_15 # type: ignore # mutmut generated
mutants_xǁSchemaServiceǁresolve__mutmut['xǁSchemaServiceǁresolve__mutmut_16'] = SchemaService.xǁSchemaServiceǁresolve__mutmut_16 # type: ignore # mutmut generated
mutants_xǁSchemaServiceǁresolve__mutmut['xǁSchemaServiceǁresolve__mutmut_17'] = SchemaService.xǁSchemaServiceǁresolve__mutmut_17 # type: ignore # mutmut generated
mutants_xǁSchemaServiceǁresolve__mutmut['xǁSchemaServiceǁresolve__mutmut_18'] = SchemaService.xǁSchemaServiceǁresolve__mutmut_18 # type: ignore # mutmut generated
mutants_xǁSchemaServiceǁresolve__mutmut['xǁSchemaServiceǁresolve__mutmut_19'] = SchemaService.xǁSchemaServiceǁresolve__mutmut_19 # type: ignore # mutmut generated
mutants_xǁSchemaServiceǁresolve__mutmut['xǁSchemaServiceǁresolve__mutmut_20'] = SchemaService.xǁSchemaServiceǁresolve__mutmut_20 # type: ignore # mutmut generated
mutants_xǁSchemaServiceǁresolve__mutmut['xǁSchemaServiceǁresolve__mutmut_21'] = SchemaService.xǁSchemaServiceǁresolve__mutmut_21 # type: ignore # mutmut generated
mutants_xǁSchemaServiceǁresolve__mutmut['xǁSchemaServiceǁresolve__mutmut_22'] = SchemaService.xǁSchemaServiceǁresolve__mutmut_22 # type: ignore # mutmut generated
mutants_xǁSchemaServiceǁresolve__mutmut['xǁSchemaServiceǁresolve__mutmut_23'] = SchemaService.xǁSchemaServiceǁresolve__mutmut_23 # type: ignore # mutmut generated
mutants_xǁSchemaServiceǁresolve__mutmut['xǁSchemaServiceǁresolve__mutmut_24'] = SchemaService.xǁSchemaServiceǁresolve__mutmut_24 # type: ignore # mutmut generated
mutants_xǁSchemaServiceǁresolve__mutmut['xǁSchemaServiceǁresolve__mutmut_25'] = SchemaService.xǁSchemaServiceǁresolve__mutmut_25 # type: ignore # mutmut generated
mutants_xǁSchemaServiceǁresolve__mutmut['xǁSchemaServiceǁresolve__mutmut_26'] = SchemaService.xǁSchemaServiceǁresolve__mutmut_26 # type: ignore # mutmut generated
mutants_xǁSchemaServiceǁresolve__mutmut['xǁSchemaServiceǁresolve__mutmut_27'] = SchemaService.xǁSchemaServiceǁresolve__mutmut_27 # type: ignore # mutmut generated
mutants_xǁSchemaServiceǁresolve__mutmut['xǁSchemaServiceǁresolve__mutmut_28'] = SchemaService.xǁSchemaServiceǁresolve__mutmut_28 # type: ignore # mutmut generated
mutants_xǁSchemaServiceǁresolve__mutmut['xǁSchemaServiceǁresolve__mutmut_29'] = SchemaService.xǁSchemaServiceǁresolve__mutmut_29 # type: ignore # mutmut generated
mutants_xǁSchemaServiceǁresolve__mutmut['xǁSchemaServiceǁresolve__mutmut_30'] = SchemaService.xǁSchemaServiceǁresolve__mutmut_30 # type: ignore # mutmut generated
mutants_xǁSchemaServiceǁresolve__mutmut['xǁSchemaServiceǁresolve__mutmut_31'] = SchemaService.xǁSchemaServiceǁresolve__mutmut_31 # type: ignore # mutmut generated
mutants_xǁSchemaServiceǁresolve__mutmut['xǁSchemaServiceǁresolve__mutmut_32'] = SchemaService.xǁSchemaServiceǁresolve__mutmut_32 # type: ignore # mutmut generated
mutants_xǁSchemaServiceǁresolve__mutmut['xǁSchemaServiceǁresolve__mutmut_33'] = SchemaService.xǁSchemaServiceǁresolve__mutmut_33 # type: ignore # mutmut generated
mutants_xǁSchemaServiceǁresolve__mutmut['xǁSchemaServiceǁresolve__mutmut_34'] = SchemaService.xǁSchemaServiceǁresolve__mutmut_34 # type: ignore # mutmut generated
mutants_xǁSchemaServiceǁresolve__mutmut['xǁSchemaServiceǁresolve__mutmut_35'] = SchemaService.xǁSchemaServiceǁresolve__mutmut_35 # type: ignore # mutmut generated
mutants_xǁSchemaServiceǁresolve__mutmut['xǁSchemaServiceǁresolve__mutmut_36'] = SchemaService.xǁSchemaServiceǁresolve__mutmut_36 # type: ignore # mutmut generated
mutants_xǁSchemaServiceǁresolve__mutmut['xǁSchemaServiceǁresolve__mutmut_37'] = SchemaService.xǁSchemaServiceǁresolve__mutmut_37 # type: ignore # mutmut generated
mutants_xǁSchemaServiceǁresolve__mutmut['xǁSchemaServiceǁresolve__mutmut_38'] = SchemaService.xǁSchemaServiceǁresolve__mutmut_38 # type: ignore # mutmut generated
mutants_xǁSchemaServiceǁresolve__mutmut['xǁSchemaServiceǁresolve__mutmut_39'] = SchemaService.xǁSchemaServiceǁresolve__mutmut_39 # type: ignore # mutmut generated

mutants_xǁSchemaServiceǁinvalidate__mutmut['_mutmut_orig'] = SchemaService.xǁSchemaServiceǁinvalidate__mutmut_orig # type: ignore # mutmut generated
mutants_xǁSchemaServiceǁinvalidate__mutmut['xǁSchemaServiceǁinvalidate__mutmut_1'] = SchemaService.xǁSchemaServiceǁinvalidate__mutmut_1 # type: ignore # mutmut generated
mutants_xǁSchemaServiceǁinvalidate__mutmut['xǁSchemaServiceǁinvalidate__mutmut_2'] = SchemaService.xǁSchemaServiceǁinvalidate__mutmut_2 # type: ignore # mutmut generated
mutants_xǁSchemaServiceǁinvalidate__mutmut['xǁSchemaServiceǁinvalidate__mutmut_3'] = SchemaService.xǁSchemaServiceǁinvalidate__mutmut_3 # type: ignore # mutmut generated
