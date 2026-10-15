"""JSON Schema for the interval definition editor in the documentation.

Adjustments that only serve the form editor are kept here, so that the runtime
models in ``interval_parser`` carry validation logic and documentation only.
"""

from __future__ import annotations

from typing import Any, get_args

from .interval_parser import RootConfig
from .sim2seis_class_definitions import KnownAttributes


def _strip_null_variants(definition: dict[str, Any]) -> None:
    # The form renders `anyOf: [X, null]` as a variant selector; null is rejected anyway
    for prop in definition.get("properties", {}).values():
        variants = prop.get("anyOf")
        if variants is None or len(variants) != 2:
            continue
        non_null = [v for v in variants if v.get("type") != "null"]
        if len(non_null) != 1:
            continue
        del prop["anyOf"]
        if prop.get("default") is None:
            prop.pop("default", None)
        prop.update(non_null[0])


def _expose_attribute_overrides(window: dict[str, Any]) -> None:
    overrides = window["properties"].pop("attribute_overrides")
    window["additionalProperties"] = overrides["additionalProperties"]
    # propertyNames constrains every key, so the declared fields must be listed too
    window["propertyNames"] = {
        "enum": [*window["properties"], *get_args(KnownAttributes)]
    }


def interval_definition_schema() -> dict[str, Any]:
    """Return the JSON Schema used by the interval definition editor.

    The schema is generated from ``RootConfig`` and adapted to the form editor:

    - optional fields are plain properties instead of ``anyOf`` with ``null``
      (``RootConfig`` rejects ``null`` values);
    - an error block's ``minimum`` has no schema default, so populating
      defaults does not create incomplete error blocks;
    - the developer docstring of ``ErrorConfig`` is not shown as help text;
    - attribute overrides are keys named after the attribute, next to the
      window fields, as written in the YAML file.
    """
    schema = RootConfig.model_json_schema()
    definitions = schema["$defs"]
    for definition in definitions.values():
        _strip_null_variants(definition)
    definitions["ErrorConfig"]["properties"]["minimum"].pop("default", None)
    definitions["ErrorConfig"].pop("description", None)
    _expose_attribute_overrides(definitions["WindowSettings"])
    return schema
