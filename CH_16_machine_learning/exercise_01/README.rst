Exercise 1: deterministic offline entity extraction
===================================================

Question
--------

.. code-block:: text

   1. Extract data or information from this chapter’s summary by applying one of the NLP algorithms.

Solution
--------

``chapter_summary.txt`` is a fixed local exercise fixture. ``load_summary``
reads it as UTF-8 and rejects blank input. ``extract_entities`` returns frozen
``ExtractedEntity`` values in source order with zero-based sentence indexes;
empty input returns an empty list.

The pipeline uses ``spacy.blank("en")`` with only a sentencizer and an
``EntityRuler`` containing fixed patterns. It never calls ``spacy.load``,
``spacy.cli.download``, a network API, or an external dataset. Consequently,
the ``en_core_web_sm`` model is neither required nor downloaded.

Dependencies
------------

Python 3.10 or newer is required. The repository's ``nlp`` dependency group
supplies spaCy without a language-model wheel. Tests use only the committed
summary.

Run
---

Run the guarded demonstration from the repository root:

.. code-block:: console

   $ uv run --group nlp python -m CH_16_machine_learning.exercise_01.solution_00

Run the focused tests:

.. code-block:: console

   $ uv run --group nlp pytest CH_16_machine_learning/exercise_01/test_solution_00.py -vv

Reference
---------

The implementation is informed by the chapter's immutable
`spaCy extraction lesson
<https://github.com/mastering-python/code_2/blob/a012f6ce3f5bf11f5bf380d1c4e7f743355adb89/CH_16_machine_learning/T_03_spacy_extract.rst>`_.
The upstream material is MIT licensed; this exercise solution is
self-contained.
