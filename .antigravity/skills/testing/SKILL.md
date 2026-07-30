# Skill: Software Testing

## 1. Purpose
This skill imparts the strategies and methodologies for ensuring the Discord bot and RAG pipeline are reliable, stable, and function as expected. It covers writing unit tests, integration tests, and mocking external APIs.

## 2. Responsibilities
- Writing comprehensive unit tests using `pytest`.
- Mocking the Discord API, LLM API, and Vector Database for isolated testing.
- Testing the accuracy and reliability of the retrieval component.
- Testing prompt templating and LLM pipeline behavior.
- Designing regression test suites to ensure new changes don't break existing features.

## 3. When to use
- Whenever a new feature, command, or data pipeline is introduced.
- Before a pull request is merged to ensure stability.

## 4. When NOT to use
- Avoid executing live LLM API calls or live database mutations in standard automated CI pipelines due to cost, latency, and instability.

## 5. Workflow
1. **Identify Logic**: Separate the business logic from the Discord/API wrapper.
2. **Setup Mocks**: Use `unittest.mock.patch` or `pytest-mock` to intercept external calls (e.g., simulating a Discord interaction or an OpenAI API response).
3. **Write Cases**: Write the "Happy Path", "Edge Cases", and "Error States".
4. **Run Pytest**: Execute the test suite and check code coverage.
5. **Continuous Integration**: Ensure tests run automatically on every code push (e.g., via GitHub Actions).

## 6. Best practices
- **Mock External Services**: Never make actual network requests to OpenAI or Discord during standard testing.
- **Fixture Reusability**: Use `pytest` fixtures for common mock setups, like creating a fake Discord Context or a dummy User.
- **Test the Pipeline**: For RAG, write offline evaluation tests that assert if a fixed query retrieves a specific expected chunk from the DB.

## 7. Coding conventions
- Name test files starting with `test_` (e.g., `test_rag.py`).
- Name test functions clearly describing the scenario (e.g., `test_ask_command_defers_and_responds()`).
- Use the `Arrange, Act, Assert` (AAA) pattern within test bodies.

## 8. Example prompts
- "Write a pytest suite for the `retrieve_chunks` function, mocking the FAISS vector store to return a predefined list of text chunks."
- "Create a mock Discord Interaction object to test our `SlashCommand` handler without needing a live bot."

## 9. Example tasks
- "Set up `pytest` and `pytest-asyncio` to test the async `generate_answer()` function."
- "Write an evaluation script that runs 50 fixed questions against the RAG pipeline and checks if the correct source document was cited."

## 10. Common pitfalls
- **Flaky Tests**: Tests that pass or fail randomly, usually caused by not mocking async delays, timers, or relying on external network states.
- **Over-mocking**: Mocking so much of the internal logic that the test no longer verifies the actual code behavior.
- **Async Test Failures**: Forgetting to decorate async test functions with `@pytest.mark.asyncio`.

## 11. Directory structure
```
tests/
├── conftest.py
├── test_bot/
│   ├── test_commands.py
│   └── test_events.py
└── test_rag/
    ├── test_retrieval.py
    └── test_generation.py
```

## 12. Suggested libraries
- `pytest`
- `pytest-asyncio`
- `pytest-mock`
- `dpytest` (for Discord bot specific testing)

## 13. References
- [Pytest Documentation](https://docs.pytest.org/)
- [Discord.py Testing Guide (dpytest)](https://dpytest.readthedocs.io/)
