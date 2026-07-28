"""Extract deterministic entities with an offline rule-based spaCy pipeline."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import cast

import spacy
from spacy.language import Language
from spacy.pipeline import EntityRuler
from spacy.pipeline.entityruler import PatternType
from spacy.tokens import Doc

__all__: list[str] = [
    "ExtractedEntity",
    "build_pipeline",
    "extract_entities",
    "load_summary",
]


@dataclass(frozen=True)
class ExtractedEntity:
    """One source-ordered entity extracted from the chapter summary."""

    text: str
    label: str
    sentence_index: int


PATTERNS: tuple[PatternType, ...] = (
    {
        "label": "METHOD",
        "pattern": [{"LOWER": "machine"}, {"LOWER": "learning"}],
    },
    {
        "label": "METHOD",
        "pattern": [
            {"LOWER": "natural"},
            {"LOWER": "language"},
            {"LOWER": "processing"},
        ],
    },
    {
        "label": "CHAPTER",
        "pattern": [{"LOWER": "chapter"}, {"TEXT": "16"}],
    },
    {"label": "LANGUAGE", "pattern": "Python"},
    {"label": "LIBRARY", "pattern": "spaCy"},
)


def build_pipeline() -> Language:
    """Build a local English tokenizer with deterministic entity rules."""

    pipeline: Language = spacy.blank("en")
    pipeline.add_pipe("sentencizer")
    ruler: EntityRuler = cast(EntityRuler, pipeline.add_pipe("entity_ruler"))
    ruler.add_patterns(list(PATTERNS))
    return pipeline


def load_summary(path: Path) -> str:
    """Load a nonblank UTF-8 chapter summary."""

    text: str = path.read_text(encoding="utf-8").strip()
    if not text:
        raise ValueError("chapter summary must not be blank")
    return text


def extract_entities(text: str) -> list[ExtractedEntity]:
    """Extract fixed entities in source order with zero-based sentence indexes."""

    if not text.strip():
        return []
    document: Doc = build_pipeline()(text)
    sentence_numbers: dict[int, int] = {
        token.i: sentence_index
        for sentence_index, sentence in enumerate(document.sents)
        for token in sentence
    }
    return [
        ExtractedEntity(
            text=entity.text,
            label=entity.label_,
            sentence_index=sentence_numbers[entity.start],
        )
        for entity in document.ents
    ]


def main() -> None:
    """Print entities from the committed local summary."""

    source: Path = Path(__file__).with_name("chapter_summary.txt")
    entities: list[ExtractedEntity] = extract_entities(load_summary(source))
    for entity in entities:
        print(f"{entity.label}\t{entity.text}\tsentence={entity.sentence_index}")


if __name__ == "__main__":
    main()
