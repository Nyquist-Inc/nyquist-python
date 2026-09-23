"""The generated ontology types ship with the SDK and import standalone."""
from __future__ import annotations

import typing

from nyquist import ontology_types as ot


def test_object_kinds_are_a_closed_literal_union():
    assert len(ot.OBJECT_KINDS) > 20
    assert set(typing.get_args(ot.ObjectKind)) == set(ot.OBJECT_KINDS)
    assert set(ot.OBJECT_TYPES) == set(ot.OBJECT_KINDS)


def test_each_object_type_is_a_typed_dict_carrying_its_kind():
    for kind, cls in ot.OBJECT_TYPES.items():
        hints = typing.get_type_hints(cls, include_extras=True)
        assert "kind" in hints, kind
    # Analytics objects carry an id; a few registry-style kinds (check,
    # scenario) do not — the generated shapes follow the backend, not a rule.
    assert "object_id" in typing.get_type_hints(ot.VarReport, include_extras=True)


def test_link_types_cover_every_link_kind():
    assert set(ot.LINK_TYPES) == set(ot.LINK_KINDS)
    assert set(typing.get_args(ot.LinkKind)) == set(ot.LINK_KINDS)
