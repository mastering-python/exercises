# Chapters 15 and 16 Scientific Plotting and NLP Implementation

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add deterministic Datashader plotting, a headlessly executable interactive notebook, and offline rule-based NLP extraction.

**Architecture:** Chapter 15 exercise 1 owns a tiny local point fixture and pure load/aggregate/render functions. Exercise 2 reuses those functions behind ipywidgets and a committed notebook. Chapter 16 uses `spacy.blank("en")`, a sentencizer, and an `EntityRuler` over committed chapter-summary text, so no model or dataset download occurs.

**Tech Stack:** Python 3.10, pandas, Datashader, Pillow, ipywidgets, nbformat, nbclient, ipykernel, spaCy, pytest, pytest-timeout, uv.

---

## Coordinator dependency handoff

Do not modify shared `pyproject.toml` or `uv.lock` in this packet. Tell the coordinator that:

- `scientific` needs pandas, Datashader, Pillow, ipywidgets, nbformat, nbclient, ipykernel, and jupyter-client;
- `nlp` needs spaCy but no language-model wheel.

## File map

- Create `exercise_01/` and `exercise_02/` under `CH_15_scientific_python/`, each with the directory-contract files.
- Add `CH_15_scientific_python/exercise_01/points.csv`.
- Add `CH_15_scientific_python/exercise_02/datashader_interactive.ipynb`.
- Create `CH_16_machine_learning/exercise_01/` with the directory-contract files and `chapter_summary.txt`.
- Modify the Chapter 15 and 16 READMEs only to link exercises.

### Task 1: Deterministic headless Datashader plot

**Files:**
- Create: `CH_15_scientific_python/exercise_01/__init__.py`
- Create: `CH_15_scientific_python/exercise_01/points.csv`
- Create: `CH_15_scientific_python/exercise_01/solution_00.py`
- Create: `CH_15_scientific_python/exercise_01/test_solution_00.py`

- [ ] **Step 1: Add the fixed local data fixture**

Write exactly:

```csv
x,y,category
-1.0,-1.0,a
-0.5,0.5,a
0.0,0.0,b
0.5,-0.5,b
1.0,1.0,c
1.0,1.0,c
```

- [ ] **Step 2: Write failing load, aggregate, render, and validation tests**

```python
from __future__ import annotations

from pathlib import Path

import pytest

from .solution_00 import aggregate_points, load_points, render_points, save_plot


FIXTURE: Path = Path(__file__).with_name("points.csv")


def test_load_and_aggregate_fixed_points() -> None:
    frame = load_points(FIXTURE)
    aggregate = aggregate_points(frame, width=8, height=6)
    assert list(frame.columns) == ["x", "y", "category"]
    assert aggregate.shape == (6, 8)
    assert int(aggregate.sum()) == 6


def test_render_is_deterministic() -> None:
    frame = load_points(FIXTURE)
    first = render_points(frame, width=16, height=12).to_pil()
    second = render_points(frame, width=16, height=12).to_pil()
    assert first.size == (16, 12)
    assert first.tobytes() == second.tobytes()


def test_save_plot_writes_png(tmp_path: Path) -> None:
    destination: Path = tmp_path / "plot.png"
    save_plot(FIXTURE, destination, width=16, height=12)
    assert destination.read_bytes().startswith(b"\x89PNG\r\n\x1a\n")


@pytest.mark.parametrize(("width", "height"), [(0, 8), (8, 0), (-1, 8)])
def test_dimensions_must_be_positive(width: int, height: int) -> None:
    frame = load_points(FIXTURE)
    with pytest.raises(ValueError, match="positive"):
        aggregate_points(frame, width=width, height=height)
```

- [ ] **Step 3: Run the tests and verify the implementation is absent**

Run `uv run --group scientific pytest CH_15_scientific_python/exercise_01/test_solution_00.py -vv`.

Expected: FAIL during import because `solution_00.py` does not exist.

- [ ] **Step 4: Implement the plotting pipeline**

Expose this API and fixed rendering choices:

```python
from __future__ import annotations

from pathlib import Path

import datashader as ds
import datashader.transfer_functions as tf
import pandas as pd
import xarray as xr


X_RANGE: tuple[float, float] = (-1.1, 1.1)
Y_RANGE: tuple[float, float] = (-1.1, 1.1)
COLOR_MAP: tuple[str, ...] = ("#0b132b", "#3a86ff", "#ffbe0b")


def load_points(path: Path) -> pd.DataFrame:
    frame: pd.DataFrame = pd.read_csv(path)
    required: set[str] = {"x", "y", "category"}
    if set(frame.columns) != required:
        raise ValueError("point data must contain x, y, and category columns")
    if frame.empty:
        raise ValueError("point data must not be empty")
    return frame.loc[:, ["x", "y", "category"]]


def aggregate_points(
    frame: pd.DataFrame,
    *,
    width: int = 256,
    height: int = 256,
) -> xr.DataArray:
    if width < 1 or height < 1:
        raise ValueError("plot dimensions must be positive")
    canvas: ds.Canvas = ds.Canvas(
        plot_width=width,
        plot_height=height,
        x_range=X_RANGE,
        y_range=Y_RANGE,
    )
    return canvas.points(frame, "x", "y", agg=ds.count())


def render_points(
    frame: pd.DataFrame,
    *,
    width: int = 256,
    height: int = 256,
) -> tf.Image:
    aggregate: xr.DataArray = aggregate_points(frame, width=width, height=height)
    return tf.shade(aggregate, cmap=list(COLOR_MAP), how="linear")


def save_plot(
    source: Path,
    destination: Path,
    *,
    width: int = 256,
    height: int = 256,
) -> Path:
    image: tf.Image = render_points(
        load_points(source),
        width=width,
        height=height,
    )
    destination.parent.mkdir(parents=True, exist_ok=True)
    image.to_pil().save(destination, format="PNG")
    return destination


def main() -> None:
    source: Path = Path(__file__).with_name("points.csv")
    destination: Path = Path(__file__).with_name("datashader_plot.png")
    print(save_plot(source, destination))


if __name__ == "__main__":
    main()
```

If a type checker lacks Datashader return types, add one narrow suppression on the exact `Canvas.points` or `tf.shade` line with the checker error code and a comment; do not suppress missing imports globally.

- [ ] **Step 5: Run focused verification and commit**

```bash
uv run --group scientific pytest CH_15_scientific_python/exercise_01/test_solution_00.py -vv
uv run ruff format --check CH_15_scientific_python/exercise_01
uv run ruff check CH_15_scientific_python/exercise_01
uv run pyrefly check CH_15_scientific_python/exercise_01
uv run mypy CH_15_scientific_python/exercise_01
uv run pyright CH_15_scientific_python/exercise_01
git add CH_15_scientific_python/exercise_01
git commit -m "feat: add deterministic datashader exercise"
```

Expected: all quality commands exit 0 and pytest reports 6 parameterized cases/tests passing.

### Task 2: Interactive and headlessly executable notebook

**Files:**
- Create: `CH_15_scientific_python/exercise_02/__init__.py`
- Create: `CH_15_scientific_python/exercise_02/solution_00.py`
- Create: `CH_15_scientific_python/exercise_02/datashader_interactive.ipynb`
- Create: `CH_15_scientific_python/exercise_02/test_solution_00.py`

- [ ] **Step 1: Write failing widget and notebook execution tests**

```python
from __future__ import annotations

from pathlib import Path

import ipywidgets as widgets
import nbformat
import pandas as pd
import pytest
from nbclient import NotebookClient
from nbformat import NotebookNode

from .solution_00 import build_interactive_plot, render_resolution


POINTS: Path = Path(__file__).parents[1] / "exercise_01" / "points.csv"
NOTEBOOK: Path = Path(__file__).with_name("datashader_interactive.ipynb")
REPOSITORY: Path = Path(__file__).parents[2]


def test_render_resolution_changes_image_dimensions() -> None:
    frame: pd.DataFrame = pd.read_csv(POINTS)
    assert render_resolution(frame, 32).to_pil().size == (32, 32)
    assert render_resolution(frame, 64).to_pil().size == (64, 64)


def test_widget_has_bounded_resolution_control() -> None:
    frame: pd.DataFrame = pd.read_csv(POINTS)
    widget: widgets.VBox = build_interactive_plot(frame)
    assert isinstance(widget.children[0], widgets.IntSlider)
    slider: widgets.IntSlider = widget.children[0]
    assert (slider.min, slider.max, slider.step, slider.value) == (32, 256, 32, 64)


@pytest.mark.timeout(90)
def test_notebook_executes_headlessly(tmp_path: Path) -> None:
    notebook: NotebookNode = nbformat.read(NOTEBOOK, as_version=4)
    client: NotebookClient = NotebookClient(
        notebook,
        timeout=60,
        kernel_name="python3",
    )
    executed: NotebookNode = client.execute(cwd=str(REPOSITORY))
    assert all(
        output.get("output_type") != "error"
        for cell in executed.cells
        for output in cell.get("outputs", [])
    )
```

- [ ] **Step 2: Run tests and verify both artifacts are missing**

Run `uv run --group scientific pytest CH_15_scientific_python/exercise_02/test_solution_00.py -vv`.

Expected: FAIL during import because the interactive API and notebook do not exist.

- [ ] **Step 3: Implement the widget adapter**

```python
from __future__ import annotations

import datashader.transfer_functions as tf
import ipywidgets as widgets
import pandas as pd

from CH_15_scientific_python.exercise_01.solution_00 import render_points


def render_resolution(frame: pd.DataFrame, resolution: int) -> tf.Image:
    if resolution < 1:
        raise ValueError("resolution must be positive")
    return render_points(frame, width=resolution, height=resolution)


def build_interactive_plot(frame: pd.DataFrame) -> widgets.VBox:
    slider: widgets.IntSlider = widgets.IntSlider(
        value=64,
        min=32,
        max=256,
        step=32,
        description="Resolution",
    )
    output: widgets.Output = widgets.Output()

    def update(change: dict[str, object]) -> None:
        resolution_value: object = change["new"]
        if not isinstance(resolution_value, int):
            raise TypeError("resolution widget returned a non-integer")
        with output:
            output.clear_output(wait=True)
            display(render_resolution(frame, resolution_value).to_pil())

    slider.observe(update, names="value")
    with output:
        display(render_resolution(frame, slider.value).to_pil())
    return widgets.VBox((slider, output))
```

Import `display` from `IPython.display`. The nested callback has an explicit `dict[str, object]` parameter and `None` return annotation in the actual file.

- [ ] **Step 4: Create the notebook with exact reproducible cells**

Create nbformat 4 JSON with a Python 3 kernelspec and these code cells:

```python
from pathlib import Path
import pandas as pd
from IPython.display import display
from CH_15_scientific_python.exercise_02.solution_00 import build_interactive_plot
```

```python
points = Path("CH_15_scientific_python/exercise_01/points.csv")
frame = pd.read_csv(points)
widget = build_interactive_plot(frame)
display(widget)
```

```python
assert tuple(frame.shape) == (6, 3)
assert widget.children[0].value == 64
```

Clear execution counts and outputs before committing. Do not embed a generated PNG or widget state.

- [ ] **Step 5: Run verification and commit**

```bash
uv run --group scientific pytest CH_15_scientific_python/exercise_02/test_solution_00.py -vv
uv run ruff format --check CH_15_scientific_python/exercise_02/solution_00.py CH_15_scientific_python/exercise_02/test_solution_00.py
uv run ruff check CH_15_scientific_python/exercise_02/solution_00.py CH_15_scientific_python/exercise_02/test_solution_00.py
uv run pyrefly check CH_15_scientific_python/exercise_02/solution_00.py CH_15_scientific_python/exercise_02/test_solution_00.py
uv run mypy CH_15_scientific_python/exercise_02/solution_00.py CH_15_scientific_python/exercise_02/test_solution_00.py
uv run pyright CH_15_scientific_python/exercise_02/solution_00.py CH_15_scientific_python/exercise_02/test_solution_00.py
git diff --exit-code -- CH_15_scientific_python/exercise_02/datashader_interactive.ipynb
```

The pytest notebook test executes an in-memory copy through nbclient, so the committed notebook remains clean. Expected: pytest reports 3 passed, the notebook has no error output, static checks exit 0, and `git diff` emits no notebook changes.

```bash
git add CH_15_scientific_python/exercise_02
git commit -m "feat: add interactive datashader notebook"
```

### Task 3: Deterministic offline entity extraction

**Files:**
- Create: `CH_16_machine_learning/exercise_01/__init__.py`
- Create: `CH_16_machine_learning/exercise_01/chapter_summary.txt`
- Create: `CH_16_machine_learning/exercise_01/solution_00.py`
- Create: `CH_16_machine_learning/exercise_01/test_solution_00.py`

- [ ] **Step 1: Add local chapter-summary text**

Use this deterministic, attributed exercise fixture:

```text
Machine learning turns examples into predictions instead of encoding every rule by hand.
Chapter 16 surveys image processing, natural language processing, neural networks, and model selection in Python.
The natural language processing example uses spaCy to identify named concepts in local text.
Reproducible exercises keep their data local and avoid downloading models during a test run.
```

- [ ] **Step 2: Write failing extraction tests**

```python
from __future__ import annotations

from pathlib import Path

import pytest

from .solution_00 import ExtractedEntity, extract_entities, load_summary


SUMMARY: Path = Path(__file__).with_name("chapter_summary.txt")


def test_extracts_expected_entities_in_source_order() -> None:
    entities: list[ExtractedEntity] = extract_entities(load_summary(SUMMARY))
    assert [(entity.text, entity.label) for entity in entities] == [
        ("Machine learning", "METHOD"),
        ("Chapter 16", "CHAPTER"),
        ("natural language processing", "METHOD"),
        ("Python", "LANGUAGE"),
        ("natural language processing", "METHOD"),
        ("spaCy", "LIBRARY"),
    ]


def test_extraction_is_repeatable() -> None:
    text: str = load_summary(SUMMARY)
    assert extract_entities(text) == extract_entities(text)


def test_empty_text_returns_no_entities() -> None:
    assert extract_entities("") == []


def test_load_summary_rejects_blank_fixture(tmp_path: Path) -> None:
    path: Path = tmp_path / "blank.txt"
    path.write_text(" \n", encoding="utf-8")
    with pytest.raises(ValueError, match="blank"):
        load_summary(path)
```

- [ ] **Step 3: Run tests and verify the module is absent**

Run `uv run --group nlp pytest CH_16_machine_learning/exercise_01/test_solution_00.py -vv`.

Expected: FAIL during import because the NLP implementation does not exist.

- [ ] **Step 4: Implement a local blank spaCy pipeline**

```python
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import spacy
from spacy.language import Language
from spacy.tokens import Doc


@dataclass(frozen=True)
class ExtractedEntity:
    text: str
    label: str
    sentence_index: int


PATTERNS: tuple[dict[str, object], ...] = (
    {"label": "METHOD", "pattern": [{"LOWER": "machine"}, {"LOWER": "learning"}]},
    {
        "label": "METHOD",
        "pattern": [
            {"LOWER": "natural"},
            {"LOWER": "language"},
            {"LOWER": "processing"},
        ],
    },
    {"label": "CHAPTER", "pattern": [{"LOWER": "chapter"}, {"TEXT": "16"}]},
    {"label": "LANGUAGE", "pattern": "Python"},
    {"label": "LIBRARY", "pattern": "spaCy"},
)


def build_pipeline() -> Language:
    pipeline: Language = spacy.blank("en")
    pipeline.add_pipe("sentencizer")
    ruler = pipeline.add_pipe("entity_ruler")
    ruler.add_patterns(list(PATTERNS))
    return pipeline


def load_summary(path: Path) -> str:
    text: str = path.read_text(encoding="utf-8").strip()
    if not text:
        raise ValueError("chapter summary must not be blank")
    return text


def extract_entities(text: str) -> list[ExtractedEntity]:
    if not text:
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
```

Add a guarded `main()` that prints `label`, `text`, and sentence index. Do not call `spacy.load`, `spacy.cli.download`, or a network API.

- [ ] **Step 5: Verify and commit**

```bash
uv run --group nlp pytest CH_16_machine_learning/exercise_01/test_solution_00.py -vv
uv run ruff format --check CH_16_machine_learning/exercise_01
uv run ruff check CH_16_machine_learning/exercise_01
uv run pyrefly check CH_16_machine_learning/exercise_01
uv run mypy CH_16_machine_learning/exercise_01
uv run pyright CH_16_machine_learning/exercise_01
git add CH_16_machine_learning/exercise_01
git commit -m "feat: add deterministic chapter NLP extraction"
```

Expected: all commands exit 0 and pytest reports 4 passed.

### Task 4: Exercise READMEs and chapter indexes

**Files:**
- Create: `CH_15_scientific_python/exercise_01/README.rst`
- Create: `CH_15_scientific_python/exercise_02/README.rst`
- Modify: `CH_15_scientific_python/README.rst`
- Create: `CH_16_machine_learning/exercise_01/README.rst`
- Modify: `CH_16_machine_learning/README.rst`

- [ ] **Step 1: Document Chapter 15 exercise 1**

Repeat “Create a datashader plot.” exactly. Explain fixed ranges, `ds.count`, fixed color map, local six-row data, PNG output, and the `scientific` dependency group. Include run/test commands and:

`https://github.com/mastering-python/code_2/blob/a012f6ce3f5bf11f5bf380d1c4e7f743355adb89/CH_15_scientific_python/T_17_datashader.ipynb`

- [ ] **Step 2: Document Chapter 15 exercise 2**

Repeat the exact interactive-notebook question. Explain the bounded resolution slider, reuse of exercise 1, headless nbclient execution, and clean committed outputs. Include:

```console
uv run --group scientific jupyter lab CH_15_scientific_python/exercise_02/datashader_interactive.ipynb
uv run --group scientific pytest CH_15_scientific_python/exercise_02/test_solution_00.py -vv
```

Cite the same immutable Datashader notebook.

- [ ] **Step 3: Document Chapter 16 exercise 1**

Repeat the exact question. Explain rule-based entity extraction, fixed local summary, deterministic order, empty-input behavior, spaCy dependency, and why no `en_core_web_sm` model is downloaded. Include run/test commands and:

`https://github.com/mastering-python/code_2/blob/a012f6ce3f5bf11f5bf380d1c4e7f743355adb89/CH_16_machine_learning/T_03_spacy_extract.rst`

- [ ] **Step 4: Link chapter indexes and run packet verification**

Retain the exact question text and link Chapter 15 items to `exercise_01/` and `exercise_02/`, and Chapter 16 item 1 to `exercise_01/`.

```bash
uv run --all-groups pytest CH_15_scientific_python CH_16_machine_learning -vv
uv run ruff format --check CH_15_scientific_python CH_16_machine_learning
uv run ruff check CH_15_scientific_python CH_16_machine_learning
uv run pyrefly check CH_15_scientific_python CH_16_machine_learning
uv run mypy CH_15_scientific_python CH_16_machine_learning
uv run pyright CH_15_scientific_python CH_16_machine_learning
```

Expected: every command exits 0 without network access.

- [ ] **Step 5: Commit documentation**

```bash
git add CH_15_scientific_python/README.rst CH_15_scientific_python/exercise_01/README.rst CH_15_scientific_python/exercise_02/README.rst CH_16_machine_learning/README.rst CH_16_machine_learning/exercise_01/README.rst
git commit -m "docs: document scientific and NLP exercises"
```

## Packet acceptance

- [ ] Execute the notebook from a clean checkout with all outputs initially cleared.
- [ ] Confirm tests do not access the network, external datasets, or downloaded spaCy models.
- [ ] Confirm the PNG render is deterministic on Python 3.10 and 3.14.
- [ ] Confirm all third-party untyped boundaries use typed local values or narrow checker-specific suppressions.
