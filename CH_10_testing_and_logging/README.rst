Chapter 10 - testing and logging
=======================================================================================================================

1. Create a function that tests the doctests of a given function/class.
2. For a greater challenge, create a function that recursively tests all doctests of every function and class in a given module.
3. Create a `py.test` plugin that checks if all tested files have file-level documentation. Hint: use `pytest_collect_file`.
4. Create a custom `tox` environment to run `flake8` or `mypy` on your project.
5. Create a `LoggerAdapter` that combines multiple messages into a single message based on some task ID.
