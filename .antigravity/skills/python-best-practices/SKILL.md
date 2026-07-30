# Skill: Python Best Practices

## 1. Purpose
This skill establishes the foundational guidelines for writing robust, maintainable, and scalable Python code. It teaches the agent how to structure projects, enforce typing, handle asynchronous workflows, and manage configuration safely.

## 2. Responsibilities
- Organizing project structure (e.g., `src/`, `tests/`, `docs/`).
- Writing clean, readable, and modular code.
- Utilizing Python's type hinting system effectively.
- Using `async/await` appropriately, especially for networking and Discord bots.
- Setting up uniform logging instead of using print statements.
- Implementing dependency injection and interface-based design.
- Creating comprehensive and graceful error handling.

## 3. When to use
- At all times when writing or refactoring Python code in this repository.

## 4. When NOT to use
- N/A. Best practices should always be applied unless a specific library strictly forbids it.

## 5. Workflow
1. **Design**: Structure modules by feature (e.g., `rag`, `bot`, `db`).
2. **Type Hints**: Define Data Classes or Pydantic models for data passing.
3. **Config**: Load environment variables via `pydantic-settings` or `.env` rather than hardcoding.
4. **Log**: Use Python's `logging` module to track application flow and errors.
5. **Format**: Adhere to PEP 8 standards, enforced via Black or Ruff.

## 6. Best practices
- **Dependency Injection**: Pass dependencies (like a DB client) to classes rather than instantiating them globally. This makes testing vastly easier.
- **Async Safety**: Do not mix heavy CPU-bound synchronous code inside async loops. Offload them to `asyncio.to_thread` or an executor.
- **Fail Fast**: Catch specific exceptions and handle them at the appropriate level. Avoid bare `except Exception:`.

## 7. Coding conventions
- Use `snake_case` for variables/functions and `PascalCase` for classes.
- Always include type hints for function arguments and return types.
- Use `isort` for import sorting and `black`/`ruff` for code formatting.
- Include docstrings (Google or Sphinx style) for public modules and complex functions.

## 8. Example prompts
- "Refactor this script to use Dependency Injection for the VectorDB client and add full type hinting."
- "Replace all `print()` statements in this module with a properly configured `logging` setup."

## 9. Example tasks
- "Set up a global logger in `core/logger.py` that writes to both console and a rotating file."
- "Implement a centralized configuration manager using Pydantic to validate `.env` inputs on startup."

## 10. Common pitfalls
- **Circular Imports**: Poor project architecture leading to files importing each other.
- **Blocking Async**: Forgetting an `await` or running a blocking `requests.get` inside a discord command.
- **Global State**: Relying heavily on global variables, making the code hard to test and prone to race conditions.

## 11. Directory structure
```
src/
├── core/
│   ├── __init__.py
│   ├── config.py
│   ├── logger.py
│   └── exceptions.py
└── ...
```

## 12. Suggested libraries
- `pydantic` / `pydantic-settings`
- `ruff` (linter/formatter)
- `mypy` (static type checking)
- `python-dotenv`

## 13. References
- [PEP 8 - Style Guide](https://peps.python.org/pep-0008/)
- [Python Asyncio Docs](https://docs.python.org/3/library/asyncio.html)
- [Pydantic Documentation](https://docs.pydantic.dev/)
