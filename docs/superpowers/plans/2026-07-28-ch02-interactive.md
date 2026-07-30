# Chapter 2 Interactive Python Implementation

**For agentic workers:** REQUIRED SUB-SKILL: Use `superpowers:subagent-driven-development` (recommended) or `superpowers:executing-plans` to implement this plan task-by-task.

**Goal:** Add offline, Python 3.10-compatible canonical solutions and headless tests for all five Chapter 2 interactive-Python exercises.

**Architecture:** Each exercise is an independent import-safe module with a small reusable API and a guarded demonstration. Exercise 1 vendors the minimum behavior of the book's pinned completer example and safely extends it; later exercises use public IPython, Jedi, Colorama, and ipywidgets APIs behind typed functions that can be tested without a terminal or notebook UI.

**Tech Stack:** Python 3.10, `rlcompleter`, IPython, Jedi, Colorama, ipywidgets, pytest.

---

## Exact Canonical File Map

Each Chapter 2 directory is new. Create these files in addition to the
exercise-specific support files named by later tasks:

- `CH_02_interactive_python/exercise_01/__init__.py`
- `CH_02_interactive_python/exercise_01/README.rst`
- `CH_02_interactive_python/exercise_01/solution_00.py`
- `CH_02_interactive_python/exercise_02/__init__.py`
- `CH_02_interactive_python/exercise_02/README.rst`
- `CH_02_interactive_python/exercise_02/solution_00.py`
- `CH_02_interactive_python/exercise_03/__init__.py`
- `CH_02_interactive_python/exercise_03/README.rst`
- `CH_02_interactive_python/exercise_03/solution_00.py`
- `CH_02_interactive_python/exercise_04/__init__.py`
- `CH_02_interactive_python/exercise_04/README.rst`
- `CH_02_interactive_python/exercise_04/solution_00.py`
- `CH_02_interactive_python/exercise_05/__init__.py`
- `CH_02_interactive_python/exercise_05/README.rst`
- `CH_02_interactive_python/exercise_05/solution_00.py`

## Scope and file map

Do not edit shared `pyproject.toml`, `uv.lock`, CI, Lefthook, or root documentation; the coordinator owns them. Create:

- `CH_02_interactive_python/exercise_01/{__init__.py,README.rst,solution_00.py,test_solution_00.py}` — mapping and sequence completion.
- `CH_02_interactive_python/exercise_02/{__init__.py,README.rst,solution_00.py,test_solution_00.py}` — ANSI-colored completion.
- `CH_02_interactive_python/exercise_03/{__init__.py,README.rst,solution_00.py,test_solution_00.py}` — Jedi static completion.
- `CH_02_interactive_python/exercise_04/{__init__.py,README.rst,solution_00.py,test_solution_00.py}` — editable greeting widget.
- `CH_02_interactive_python/exercise_05/{__init__.py,README.rst,solution_00.py,test_solution_00.py}` — all-session history search and CLI.
- Modify `CH_02_interactive_python/README.rst` only after all five exercise directories pass.

Use this immutable book source where the original completer/history examples inform the answer:

`https://github.com/mastering-python/code_2/blob/a012f6ce3f5bf11f5bf380d1c4e7f743355adb89/CH_02_interactive_python/T_02_modifying_autocompletion.py`

Exercise 5 additionally cites:

`https://github.com/mastering-python/code_2/blob/a012f6ce3f5bf11f5bf380d1c4e7f743355adb89/CH_02_interactive_python/session_filename.ipy`

## Task 1: Complete mappings and finite sequences

**Public API:** `Completer(namespace: Mapping[str, object] | None = None)`, `Completer.item_matches(text: str) -> Iterator[str]`, and inherited `complete(text: str, state: int) -> str | None`.

**Behavioral decisions:** Mapping completions use `repr(key)`; list, tuple, and string completions use numeric indexes; matches preserve container order and stop at 25 entries; numeric prefixes filter sequence indexes. Resolve only names, attributes, and constant subscripts—never execute calls from completion text.

- [ ] **Step 1: Write the failing contract tests**

Create `test_solution_00.py` with representative cases:

```python
from CH_02_interactive_python.exercise_01.solution_00 import Completer


def test_mapping_and_sequence_matches() -> None:
    completer: Completer = Completer(
        {"food": {"spam": 1, "eggs": 2}, "values": ["a", "b", "c"]}
    )
    assert list(completer.item_matches("food['s")) == ["food['spam']"]
    assert list(completer.item_matches("values[")) == [
        "values[0]",
        "values[1]",
        "values[2]",
    ]
    assert list(completer.item_matches("values[1")) == ["values[1]"]


def test_completion_does_not_execute_calls() -> None:
    called: list[bool] = []

    def dangerous() -> list[str]:
        called.append(True)
        return ["never"]

    completer: Completer = Completer({"dangerous": dangerous})
    assert list(completer.item_matches("dangerous()[")) == []
    assert called == []
```

Also cover tuple/string indexing, missing names, unsupported objects, a 26-item cap, and repeated `complete(..., state)` calls.

- [ ] **Step 2: Run the focused test and verify the red state**

Run: `uv run pytest CH_02_interactive_python/exercise_01/test_solution_00.py -v`

Expected: collection fails with `ModuleNotFoundError` because `exercise_01` does not exist.

- [ ] **Step 3: Implement the minimal safe completer**

Create empty `__init__.py`, then implement `Completer`. The resolver must recursively handle `ast.Name`, `ast.Attribute`, and `ast.Subscript` with `ast.literal_eval` keys and raise `ValueError` for every other node. The key branch is:

```python
class Completer(rlcompleter.Completer):
    MAX_MATCHES: int = 25

    def item_matches(self, text: str) -> Iterator[str]:
        match: re.Match[str] | None = ITEM_RE.fullmatch(text)
        if match is None:
            return
        expression: str = match.group("expression")
        prefix: str = match.group("key").strip()
        try:
            value: object = _resolve_expression(expression, self.namespace)
        except (AttributeError, KeyError, TypeError, ValueError):
            return
        if isinstance(value, Mapping):
            for key in itertools.islice(value, self.MAX_MATCHES):
                candidate: str = repr(key)
                if candidate.lstrip("'\"").startswith(prefix.lstrip("'\"")):
                    yield f"{expression}[{candidate}]"
        elif isinstance(value, (list, tuple, str)):
            for index in range(min(len(value), self.MAX_MATCHES)):
                if str(index).startswith(prefix):
                    yield f"{expression}[{index}]"
```

`complete()` must cache `item_matches()` at state zero and otherwise delegate to `rlcompleter.Completer.complete`. Keep `readline` installation in `main()` so imports do not alter global terminal state.

- [ ] **Step 4: Add exercise documentation**

`README.rst` must repeat Chapter 2 question 1 verbatim, describe safe expression resolution and finite sequence indexing, list no third-party dependency, show:

```console
uv run python -m CH_02_interactive_python.exercise_01.solution_00
uv run pytest CH_02_interactive_python/exercise_01 -v
```

Include the pinned book permalink above and its MIT attribution.

- [ ] **Step 5: Verify and commit**

Run: `uv run pytest CH_02_interactive_python/exercise_01 -v`

Expected: all tests pass.

```bash
git add CH_02_interactive_python/exercise_01
git commit -m "feat(ch02): complete container autocompletion"
```

## Task 2: Add colored completion

**Public API:** `ColorCompleter(Completer)` with keyword-only `color: str = Fore.CYAN`; `colorize(match: str, color: str) -> str`.

- [ ] **Step 1: Write the failing tests**

```python
from colorama import Fore, Style

from CH_02_interactive_python.exercise_02.solution_00 import (
    ColorCompleter,
    colorize,
)


def test_colorize_wraps_and_resets_match() -> None:
    assert colorize("values[0]", Fore.GREEN) == (
        f"{Fore.GREEN}values[0]{Style.RESET_ALL}"
    )


def test_color_completer_preserves_none_sentinel() -> None:
    completer: ColorCompleter = ColorCompleter({"values": [1]}, color=Fore.BLUE)
    assert completer.complete("values[", 0) == (
        f"{Fore.BLUE}values[0]{Style.RESET_ALL}"
    )
    assert completer.complete("values[", 1) is None
```

Also assert state zero returns colored text whose ANSI-stripped value is `values[0]`.

- [ ] **Step 2: Verify failure**

Run: `uv run pytest CH_02_interactive_python/exercise_02/test_solution_00.py -v`

Expected: `ModuleNotFoundError` for `exercise_02`.

- [ ] **Step 3: Implement**

Subclass Exercise 1's `Completer`; do not duplicate its parser:

```python
def colorize(match: str, color: str) -> str:
    return f"{color}{match}{Style.RESET_ALL}"


class ColorCompleter(Completer):
    def __init__(
        self,
        namespace: Mapping[str, object] | None = None,
        *,
        color: str = Fore.CYAN,
    ) -> None:
        super().__init__(namespace)
        self.color: str = color

    def complete(self, text: str, state: int) -> str | None:
        match: str | None = super().complete(text, state)
        return None if match is None else colorize(match, self.color)
```

Guard `colorama.just_fix_windows_console()` and readline setup in `main()`.

- [ ] **Step 4: Document, verify, and commit**

The exercise README repeats question 2, names Colorama as its dependency, documents reset behavior, includes the same pinned book reference, and shows module/test `uv run` commands.

Run: `uv run pytest CH_02_interactive_python/exercise_02 -v`

Expected: all tests pass.

```bash
git add CH_02_interactive_python/exercise_02
git commit -m "feat(ch02): color completion candidates"
```

## Task 3: Complete source with Jedi

**Public API:** `complete_source(source: str, *, line: int | None = None, column: int | None = None) -> list[str]`.

**Behavioral decisions:** Defaults target the end of the source; results are deduplicated and sorted; invalid coordinates raise `ValueError`; incomplete or invalid Python source uses Jedi's normal best-effort completion result.

- [ ] **Step 1: Write failing tests**

```python
import pytest

from CH_02_interactive_python.exercise_03.solution_00 import complete_source


def test_completes_static_source_without_execution() -> None:
    source: str = "import pathlib\npathlib.Pa"
    assert "Path" in complete_source(source)


def test_rejects_invalid_coordinates() -> None:
    with pytest.raises(ValueError, match="line"):
        complete_source("value = 1", line=0, column=0)
```

Also test an explicit middle-of-source coordinate, deterministic ordering, empty source, and source containing a function call that must not execute.

- [ ] **Step 2: Verify failure**

Run: `uv run pytest CH_02_interactive_python/exercise_03/test_solution_00.py -v`

Expected: `ModuleNotFoundError`.

- [ ] **Step 3: Implement**

```python
def complete_source(
    source: str,
    *,
    line: int | None = None,
    column: int | None = None,
) -> list[str]:
    lines: list[str] = source.splitlines() or [""]
    selected_line: int = len(lines) if line is None else line
    if selected_line < 1 or selected_line > len(lines):
        raise ValueError("line is outside the source")
    selected_column: int = (
        len(lines[selected_line - 1]) if column is None else column
    )
    if selected_column < 0 or selected_column > len(lines[selected_line - 1]):
        raise ValueError("column is outside the selected line")
    completions: list[jedi.api.classes.Completion] = jedi.Script(
        code=source
    ).complete(selected_line, selected_column)
    return sorted({completion.name_with_symbols for completion in completions})
```

Do not catch Jedi/internal exceptions: coordinate errors are validated locally, while dependency failures must propagate rather than masquerade as “no completions.”

- [ ] **Step 4: Document, verify, and commit**

README: exact question 3, Jedi dependency, static-analysis/no-execution guarantee, coordinate rules, and module/test commands.

Run: `uv run pytest CH_02_interactive_python/exercise_03 -v`

Expected: all tests pass.

```bash
git add CH_02_interactive_python/exercise_03
git commit -m "feat(ch02): add Jedi source completion"
```

## Task 4: Build an editable Hello widget

**Public API:** immutable `HelloWidget(name_input: widgets.Text, greeting: widgets.Label, container: widgets.VBox)` and `create_hello_widget(initial_name: str = "World") -> HelloWidget`.

- [ ] **Step 1: Write failing headless tests**

```python
from CH_02_interactive_python.exercise_04.solution_00 import (
    HelloWidget,
    create_hello_widget,
)


def test_name_edit_updates_greeting_without_running_code_again() -> None:
    hello: HelloWidget = create_hello_widget("Ada")
    assert hello.greeting.value == "Hello, Ada!"
    hello.name_input.value = "Grace"
    assert hello.greeting.value == "Hello, Grace!"
    assert hello.container.children == (hello.name_input, hello.greeting)
```

Also test empty input produces `Hello, World!` and two widget instances do not share state.

- [ ] **Step 2: Verify failure**

Run: `uv run pytest CH_02_interactive_python/exercise_04/test_solution_00.py -v`

Expected: `ModuleNotFoundError`.

- [ ] **Step 3: Implement**

```python
@dataclass(frozen=True)
class HelloWidget:
    name_input: widgets.Text
    greeting: widgets.Label
    container: widgets.VBox


def create_hello_widget(initial_name: str = "World") -> HelloWidget:
    name_input: widgets.Text = widgets.Text(value=initial_name, description="Name")
    greeting: widgets.Label = widgets.Label()

    def update(change: dict[str, object]) -> None:
        raw_name: object = change["new"]
        name: str = raw_name.strip() if isinstance(raw_name, str) else ""
        greeting.value = f"Hello, {name or 'World'}!"

    name_input.observe(update, names="value")
    update({"new": initial_name})
    container: widgets.VBox = widgets.VBox((name_input, greeting))
    return HelloWidget(name_input, greeting, container)
```

`main()` imports `IPython.display.display` locally and displays only `container`.

- [ ] **Step 4: Document, verify, and commit**

README: exact question 4, ipywidgets/IPython dependencies, headless behavior, notebook usage, and module/test commands.

Run: `uv run pytest CH_02_interactive_python/exercise_04 -v`

Expected: all tests pass without opening a browser.

```bash
git add CH_02_interactive_python/exercise_04
git commit -m "feat(ch02): add editable greeting widget"
```

## Task 5: Search all prior IPython sessions

**Public API:** immutable `HistoryMatch(session: int, line: int, source: str)`, `search_history(pattern: str, records: Iterable[tuple[int, int, str]]) -> list[HistoryMatch]`, `iter_ipython_history(accessor: HistoryAccessor | None = None) -> Iterator[tuple[int, int, str]]`, and `main(argv: Sequence[str] | None = None) -> int`.

**Behavioral decisions:** Pattern syntax is a compiled regular expression; invalid patterns raise `re.error`; search covers raw input from every stored session; ordering is `(session, line)`; CLI returns 0 with matches, 1 with no matches, and lets invalid regex errors surface with a clear message.

- [ ] **Step 1: Write failing pure and headless-adapter tests**

```python
from CH_02_interactive_python.exercise_05.solution_00 import (
    HistoryMatch,
    search_history,
)


def test_searches_across_sessions_in_order() -> None:
    records: list[tuple[int, int, str]] = [
        (2, 4, "print('spam')"),
        (1, 3, "value = 'spam'"),
        (1, 2, "eggs = 1"),
    ]
    assert search_history(r"spam", records) == [
        HistoryMatch(1, 3, "value = 'spam'"),
        HistoryMatch(2, 4, "print('spam')"),
    ]
```

Add tests for no matches, multiline input, invalid regex, CLI output/exit codes, and an actual `IPython.core.history.HistoryAccessor` backed by `tmp_path / "history.sqlite"` so no user profile is read or written.

- [ ] **Step 2: Verify failure**

Run: `uv run pytest CH_02_interactive_python/exercise_05/test_solution_00.py -v`

Expected: `ModuleNotFoundError`.

- [ ] **Step 3: Implement**

```python
@dataclass(frozen=True, order=True)
class HistoryMatch:
    session: int
    line: int
    source: str = field(compare=False)


def search_history(
    pattern: str,
    records: Iterable[tuple[int, int, str]],
) -> list[HistoryMatch]:
    regex: re.Pattern[str] = re.compile(pattern)
    matches: list[HistoryMatch] = [
        HistoryMatch(session, line, source)
        for session, line, source in records
        if regex.search(source) is not None
    ]
    return sorted(matches)


def iter_ipython_history(
    accessor: HistoryAccessor | None = None,
) -> Iterator[tuple[int, int, str]]:
    history: HistoryAccessor = accessor or HistoryAccessor()
    yield from history.search("*", raw=True, search_raw=True, unique=False)
```

The CLI formats each hit as `session:line: source`. Close only an accessor created by this module; never close an injected object.

- [ ] **Step 4: Document and update the chapter index**

README: exact question 5, regex choice, IPython dependency, privacy note that the default CLI reads local IPython history, headless temporary-database test strategy, module/test commands, and the full pinned `session_filename.ipy` permalink listed above.

Replace the chapter README's bare list with five numbered RST links to the exercise READMEs while keeping each one-line question recognizable.

- [ ] **Step 5: Run packet quality gates**

```bash
uv run ruff format --check CH_02_interactive_python
uv run ruff check CH_02_interactive_python
uv run pyrefly check CH_02_interactive_python
uv run mypy CH_02_interactive_python
uv run pyright CH_02_interactive_python
uv run pytest CH_02_interactive_python -v
```

Expected: every command exits 0; tests use only temporary history storage and open no UI.

- [ ] **Step 6: Commit**

```bash
git add CH_02_interactive_python
git commit -m "feat(ch02): search IPython session history"
```
