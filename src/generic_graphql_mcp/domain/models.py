from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict


class ErrorClass(str, Enum):
    """Three-class error typing for GraphQL responses."""

    OK = "ok"
    GRAPHQL = "graphql"
    TRANSPORT = "transport"


class TypeSummary(BaseModel):
    """Lightweight summary of a GraphQL type."""

    model_config = ConfigDict(frozen=True)

    name: str
    kind: str = ""  # OBJECT, INTERFACE, ENUM, UNION, INPUT_OBJECT, SCALAR
    description: str = ""


class SchemaGraph(BaseModel):
    """Parsed GraphQL schema representation."""

    model_config = ConfigDict(frozen=True)

    sdl: str
    query_type_name: str = "Query"
    types: dict[str, TypeSummary] = {}
    source_name: str = ""


class FieldInfo(BaseModel):
    """Detail of a single field on a GraphQL type."""

    model_config = ConfigDict(frozen=True)

    name: str
    type_str: str = ""
    description: str = ""
    args: list[str] = []


class TypeInfo(BaseModel):
    """Detailed type information including optional federation ownership."""

    model_config = ConfigDict(frozen=True)

    name: str
    kind: str = ""
    description: str = ""
    fields: list[FieldInfo] = []
    subgraph: str | None = None


class Subgraph(BaseModel):
    """Federation subgraph descriptor."""

    model_config = ConfigDict(frozen=True)

    name: str
    url: str = ""
    owned_types: list[str] = []


class SchemaSummary(BaseModel):
    """Summary returned by introspect() — Query root fields + type list."""

    model_config = ConfigDict(frozen=True)

    query_fields: list[str] = []
    types: list[TypeSummary] = []


class QueryResult(BaseModel):
    """Result of a GraphQL query execution."""

    model_config = ConfigDict(frozen=True)

    data: dict[str, Any] | None = None
    errors: list[dict[str, Any]] = []
    error_class: ErrorClass = ErrorClass.OK
