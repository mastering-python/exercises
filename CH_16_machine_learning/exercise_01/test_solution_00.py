"""Tests for deterministic offline entity extraction."""

from __future__ import annotations

from dataclasses import FrozenInstanceError
from pathlib import Path

import pytest

from .solution_00 import (
    ExtractedEntity,
    build_pipeline,
    extract_entities,
    load_summary,
)

SUMMARY: Path = Path(__file__).with_name("chapter_summary.txt")


def test_extracts_expected_entities_in_source_order_with_sentence_indexes() -> None:
    entities: list[ExtractedEntity] = extract_entities(load_summary(SUMMARY))

    assert [
        (entity.text, entity.label, entity.sentence_index) for entity in entities
    ] == [
        ("Machine learning", "METHOD", 0),
        ("Chapter 16", "CHAPTER", 1),
        ("natural language processing", "METHOD", 1),
        ("Python", "LANGUAGE", 1),
        ("natural language processing", "METHOD", 2),
        ("spaCy", "LIBRARY", 2),
    ]


def test_pipeline_is_local_rule_based_and_repeatable() -> None:
    text: str = load_summary(SUMMARY)

    assert build_pipeline().pipe_names == ["sentencizer", "entity_ruler"]
    assert extract_entities(text) == extract_entities(text)


def test_extracted_entities_are_frozen() -> None:
    entity: ExtractedEntity = ExtractedEntity("Python", "LANGUAGE", 0)

    with pytest.raises(FrozenInstanceError):
        setattr(entity, "label", "CHANGED")  # noqa: B010


def test_empty_text_returns_no_entities() -> None:
    assert extract_entities("") == []
    assert extract_entities(" \n") == []


def test_load_summary_rejects_blank_fixture(tmp_path: Path) -> None:
    path: Path = tmp_path / "blank.txt"
    path.write_text(" \n", encoding="utf-8")

    with pytest.raises(ValueError, match=r"^chapter summary must not be blank$"):
        load_summary(path)
