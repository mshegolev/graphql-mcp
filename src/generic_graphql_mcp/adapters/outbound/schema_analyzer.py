from __future__ import annotations

import hashlib
import logging
from typing import Any

from graphql import (
    GraphQLEnumType,
    GraphQLInputObjectType,
    GraphQLInterfaceType,
    GraphQLObjectType,
    GraphQLScalarType,
    GraphQLSchema,
    GraphQLUnionType,
    build_schema,
)
from graphql import parse as gql_parse
from graphql.language.ast import (
    EnumTypeDefinitionNode,
    EnumValueNode,
    StringValueNode,
)

from generic_graphql_mcp.domain.models import (
    FieldInfo,
    SchemaSummary,
    Subgraph,
    TypeInfo,
    TypeSummary,
)

logger = logging.getLogger(__name__)

_GRAPHQL_TYPE_MAP: dict[type, str] = {
    GraphQLObjectType: "OBJECT",
    GraphQLInterfaceType: "INTERFACE",
    GraphQLEnumType: "ENUM",
    GraphQLUnionType: "UNION",
    GraphQLInputObjectType: "INPUT_OBJECT",
    GraphQLScalarType: "SCALAR",
}


class SchemaAnalyzer:
    """Outbound adapter: parse SDL into domain model objects.

    Wraps graphql-core ``build_schema`` / ``parse`` so that domain and
    port layers remain free of external library imports.  Caches the
    built ``GraphQLSchema`` keyed on SDL SHA-256 hash.
    """

    def __init__(self) -> None:
        self._cache_key: str = ""
        self._cached_schema: Any = None

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def build_summary(self, sdl: str) -> SchemaSummary:
        """Return a :class:`SchemaSummary` with query fields and types."""
        schema = self._get_or_build_schema(sdl)

        query_fields: list[str] = list(schema.query_type.fields.keys()) if schema.query_type else []

        types: list[TypeSummary] = []
        for name, obj in schema.type_map.items():
            if name.startswith("__"):
                continue
            kind = _GRAPHQL_TYPE_MAP.get(type(obj), "")
            types.append(
                TypeSummary(
                    name=name,
                    kind=kind,
                    description=obj.description or "",
                )
            )

        return SchemaSummary(query_fields=query_fields, types=types)

    def describe_type(self, sdl: str, type_name: str) -> TypeInfo | None:
        """Return detailed :class:`TypeInfo` for *type_name*, or ``None``."""
        schema = self._get_or_build_schema(sdl)
        type_obj = schema.type_map.get(type_name)
        if type_obj is None:
            return None

        kind = _GRAPHQL_TYPE_MAP.get(type(type_obj), "")

        fields: list[FieldInfo] = []
        if hasattr(type_obj, "fields"):
            for fname, fobj in type_obj.fields.items():
                args: list[str] = []
                if hasattr(fobj, "args") and fobj.args:
                    args = [f"{aname}: {aobj.type}" for aname, aobj in fobj.args.items()]
                fields.append(
                    FieldInfo(
                        name=fname,
                        type_str=str(fobj.type),
                        description=fobj.description or "",
                        args=args,
                    )
                )

        subgraph = self._find_subgraph_for_type(sdl, type_name)

        return TypeInfo(
            name=type_name,
            kind=kind,
            description=type_obj.description or "",
            fields=fields,
            subgraph=subgraph,
        )

    def list_subgraphs(self, sdl: str) -> list[Subgraph]:
        """Extract :class:`Subgraph` list from supergraph SDL.

        Returns an empty list when the SDL is not a supergraph
        (no ``join__Graph`` enum or no ``@join__graph`` directives).
        """
        doc = gql_parse(sdl)

        # Step 1: find join__Graph enum
        graph_enum = None
        for defn in doc.definitions:
            if isinstance(defn, EnumTypeDefinitionNode) and defn.name.value == "join__Graph":
                graph_enum = defn
                break

        if graph_enum is None:
            return []

        # Step 2: extract subgraph metadata from enum values
        subgraph_map: dict[str, dict[str, Any]] = {}
        for val in graph_enum.values or []:
            enum_key = val.name.value
            sg_name, sg_url = "", ""
            for directive in val.directives or []:
                if directive.name.value == "join__graph":
                    for arg in directive.arguments:
                        if arg.name.value == "name" and isinstance(arg.value, StringValueNode):
                            sg_name = arg.value.value
                        elif arg.name.value == "url" and isinstance(arg.value, StringValueNode):
                            sg_url = arg.value.value
            if sg_name:
                subgraph_map[enum_key] = {
                    "name": sg_name,
                    "url": sg_url,
                    "owned_types": [],
                }

        # Step 3: validate — require both enum AND at least one directive
        if not subgraph_map:
            return []

        # Step 4: map type ownership via @join__type(graph: X)
        for defn in doc.definitions:
            if not hasattr(defn, "name") or defn.name is None:
                continue
            for directive in getattr(defn, "directives", None) or []:
                if directive.name.value == "join__type":
                    for arg in directive.arguments:
                        if arg.name.value == "graph" and isinstance(arg.value, EnumValueNode):
                            graph_key = arg.value.value
                            if graph_key in subgraph_map:
                                subgraph_map[graph_key]["owned_types"].append(defn.name.value)

        return [
            Subgraph(
                name=info["name"],
                url=info["url"],
                owned_types=info["owned_types"],
            )
            for info in subgraph_map.values()
        ]

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _get_or_build_schema(self, sdl: str) -> GraphQLSchema:
        """Return cached or freshly-built ``GraphQLSchema``."""
        sha = hashlib.sha256(sdl.encode()).hexdigest()
        if self._cache_key == sha:
            return self._cached_schema

        try:
            schema = build_schema(sdl)
        except Exception:  # noqa: BLE001
            # Supergraph SDL may contain unknown directives; retry
            schema = build_schema(sdl, assume_valid_sdl=True)

        self._cache_key = sha
        self._cached_schema = schema
        return schema

    def _find_subgraph_for_type(self, sdl: str, type_name: str) -> str | None:
        """Return the owning subgraph name for *type_name*, or ``None``."""
        doc = gql_parse(sdl)

        # Build enum-key → subgraph-name mapping
        enum_to_name: dict[str, str] = {}
        for defn in doc.definitions:
            if isinstance(defn, EnumTypeDefinitionNode) and defn.name.value == "join__Graph":
                for val in defn.values or []:
                    for directive in val.directives or []:
                        if directive.name.value == "join__graph":
                            for arg in directive.arguments:
                                if arg.name.value == "name" and isinstance(arg.value, StringValueNode):
                                    enum_to_name[val.name.value] = arg.value.value
                break

        if not enum_to_name:
            return None

        # Find the type definition and its @join__type directive
        for defn in doc.definitions:
            if hasattr(defn, "name") and defn.name is not None and defn.name.value == type_name:
                for directive in getattr(defn, "directives", None) or []:
                    if directive.name.value == "join__type":
                        for arg in directive.arguments:
                            if arg.name.value == "graph" and isinstance(arg.value, EnumValueNode):
                                return enum_to_name.get(arg.value.value)

        return None
