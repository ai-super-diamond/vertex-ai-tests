# AGENTS.md

This document provides instructions for AI agents working on this project. By following these guidelines, you can ensure that your contributions are consistent with the project's standards and best practices.

## Coding Conventions

- **Style Guide:** All Python code should adhere to the [PEP 8 style guide](https://www.python.org/dev/peps/pep-0008/). We use `flake8` to enforce these standards.
- **Docstrings:** All modules, classes, and functions should have docstrings that follow the [Google Python Style Guide](https://google.github.io/styleguide/pyguide.html#38-comments-and-docstrings).
- **Type Hinting:** Use type hints for all function signatures. This helps with static analysis and improves code readability.

## Testing

- **Framework:** We use `pytest` for our testing framework. All tests should be placed in the `tests/` directory.
- **Test Coverage:** Aim for high test coverage. Every new feature should be accompanied by corresponding tests.
- **Running Tests:** To run the entire test suite, use the following command:
  ```bash
  pytest
  ```

## Dependencies

- **Dependency Management:** All project dependencies are managed in the `requirements.txt` file.
- **Adding a Dependency:** If you need to add a new dependency, add it to `requirements.txt` and then run:
  ```bash
  pip install -r requirements.txt
  ```

## Verifying Your Work

Before submitting any changes, you must run the following checks to ensure your work meets the project's quality standards:

1. **Linting:**
   ```bash
   flake8 .
   ```

2. **Testing:**
   ```bash
   pytest
   ```

Make sure all checks pass before you request a review.
