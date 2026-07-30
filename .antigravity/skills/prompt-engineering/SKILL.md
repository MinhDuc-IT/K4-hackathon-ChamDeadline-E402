# Skill: Prompt Engineering

## 1. Purpose
This skill provides strategies for crafting effective, deterministic, and secure prompts for Large Language Models (LLMs). It emphasizes designing system prompts, RAG instructions, and enforcing output formats.

## 2. Responsibilities
- Designing system prompts that establish persona, tone, and constraints.
- Writing RAG prompts that seamlessly integrate retrieved context.
- Implementing citation rules forcing the model to cite its sources.
- Iteratively refining prompts to improve answer quality and reduce hallucinations.
- Structuring prompts for structured outputs (e.g., JSON validation).

## 3. When to use
- When calling an LLM via API for generation, summarization, or reasoning.
- Whenever the bot’s response quality needs tweaking without changing code logic.

## 4. When NOT to use
- For strict algorithmic tasks (e.g., sorting, exact math) where standard code is more reliable and faster.

## 5. Workflow
1. **Define Objective**: What exactly should the LLM output?
2. **Draft System Prompt**: Assign a role and set strict boundaries.
3. **Format Context**: Inject variables (like retrieved context, user query) using a templating engine (like Jinja2 or simple f-strings).
4. **Test and Refine**: Run edge cases. If the LLM hallucinates, add a negative constraint (e.g., "If you do not know, say 'I don't know'").

## 6. Best practices
- **Separation of Instructions and Context**: Clearly demarcate sections (e.g., using `### Context ###` or XML tags `<context>`).
- **Few-Shot Prompting**: Provide 1-2 examples of good inputs and expected outputs within the prompt to dramatically improve formatting.
- **Fail-Safes**: Always instruct the LLM on what to do if the context is insufficient.

## 7. Coding conventions
- Store large prompts in separate `.txt`, `.yaml`, or template files rather than inline strings in Python files.
- Use explicit Pydantic models with libraries like `instructor` or LangChain to enforce JSON output structures.

## 8. Example prompts
- "Draft a System Prompt for a Student Support Bot that strictly uses only the provided context and returns answers with inline citations [Source 1]."
- "Create a prompt template that classifies a user's question into one of 3 categories: FAQ, Technical Issue, or General Chat."

## 9. Example tasks
- "Refactor the hardcoded RAG prompt into a dedicated `prompts.py` file with a `build_qa_prompt(context, query)` function."
- "Update the prompt to explicitly prevent the LLM from executing malicious code injections."

## 10. Common pitfalls
- **Vague Instructions**: Asking the LLM to "be helpful" without defining what helpful means in context.
- **Prompt Injection**: Failing to sanitize user inputs, leading to users overriding the system prompt (e.g., "Ignore previous instructions").
- **Overloading the Prompt**: Giving the LLM too many conflicting rules, which degrades performance.

## 11. Directory structure
```
src/
├── prompts/
│   ├── __init__.py
│   ├── system_prompts.py
│   └── templates/
│       └── rag_qa.jinja
```

## 12. Suggested libraries
- `jinja2`
- `instructor` (for structured output)

## 13. References
- [OpenAI Prompt Engineering Guide](https://platform.openai.com/docs/guides/prompt-engineering)
- [Anthropic Prompt Engineering](https://docs.anthropic.com/en/docs/prompt-engineering)
