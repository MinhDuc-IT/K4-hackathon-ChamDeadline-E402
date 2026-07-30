# Skill: Refactoring

## 1. Purpose
This skill teaches the agent how to restructure existing code safely. Refactoring improves readability, reduces complexity, and enhances maintainability without altering the external behavior of the software.

## 2. Responsibilities
- Simplifying complex functions and deep nesting (reducing cyclomatic complexity).
- Eliminating code duplication (DRY principle).
- Improving modularity by separating concerns (e.g., separating Discord UI from RAG logic).
- Renaming variables and functions for better clarity.
- Enforcing Clean Architecture patterns.
- Ensuring that behavior is perfectly preserved during code transformations.

## 3. When to use
- When a file becomes too large (e.g., `bot.py` is 1000 lines).
- When a function handles multiple unrelated responsibilities.
- When preparing the codebase for a new feature that doesn't easily fit into the current structure.
- When unit tests are difficult to write due to tight coupling.

## 4. When NOT to use
- Do not refactor code that lacks test coverage if the logic is highly critical, unless you write tests first.
- Do not combine feature additions with refactoring in the same step/commit; keep them separate.

## 5. Workflow
1. **Ensure Test Coverage**: Run existing tests. If tests don't exist for the targeted code, write them.
2. **Identify Code Smells**: Look for long functions, duplicate code blocks, or classes that know too much (God Classes).
3. **Execute Small Steps**: Extract a function, rename a variable, or move a class.
4. **Test Continually**: Run tests after every minor change.
5. **Review**: Ensure the new structure is actually cleaner and easier to read.

## 6. Best practices
- **Extract Method/Function**: Take a large block of code inside a command and move it to a beautifully named helper function.
- **Decouple the UI**: The Discord command function should only parse the user input, call a business logic function, and return the result. It should NOT contain database queries or API logic directly.
- **Boy Scout Rule**: Always leave the code slightly cleaner than you found it.

## 7. Coding conventions
- Follow standard design patterns where applicable (e.g., Repository pattern for Vector DB, Strategy pattern for Prompts).
- Strive for single-responsibility functions (a function should do one thing and do it well).

## 8. Example prompts
- "Refactor this 100-line Discord command into smaller, testable functions, separating the RAG logic from the Discord Embed generation."
- "Extract all the hardcoded string prompts in `app.py` into a dedicated `prompts` module."

## 9. Example tasks
- "Refactor the database connection logic so it uses Dependency Injection instead of creating global instances."
- "Break down the `ingest_documents` function into `read_files`, `chunk_text`, and `upsert_to_db`."

## 10. Common pitfalls
- **Scope Creep**: Starting a refactor to fix a variable name and ending up rewriting the entire application architecture.
- **Breaking Behavior**: Accidentally changing the output format or logic flow because tests weren't run.
- **Over-engineering**: Creating 15 abstract classes and interfaces for a script that just needs to run a simple cron job. Keep it simple.

## 11. Directory structure
*(Refactoring applies to all files, moving them towards a cleaner structure like this:)*
```
src/
├── presentation/ (Discord UI)
├── application/ (RAG workflows, services)
├── domain/ (Data models, Prompts)
└── infrastructure/ (VectorDB clients, LLM API clients)
```

## 12. Suggested libraries
- `sourcery` or `ruff` (for static analysis and code smell detection)

## 13. References
- [Refactoring Guru](https://refactoring.guru/)
- [Clean Code by Robert C. Martin](https://www.oreilly.com/library/view/clean-code-a/9780136083238/)
