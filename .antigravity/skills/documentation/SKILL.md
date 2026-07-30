# Skill: Documentation

## 1. Purpose
This skill ensures the agent understands the importance of clear, accessible, and maintainable project documentation. It teaches how to write project overviews, API documentation, architectural guidelines, and setup instructions.

## 2. Responsibilities
- Maintaining and updating the main `README.md`.
- Documenting internal Python APIs, classes, and complex algorithms using docstrings.
- Explaining the high-level architecture (e.g., how the RAG pipeline interacts with Discord).
- Creating step-by-step local setup and installation instructions for new developers.
- Establishing Contribution Guidelines (`CONTRIBUTING.md`).

## 3. When to use
- When setting up a new repository.
- After implementing a major new feature, dependency, or architectural change.
- When refactoring code to ensure internal comments remain accurate.

## 4. When NOT to use
- Avoid documenting standard library features or basic Python syntax; assume the reader knows Python.

## 5. Workflow
1. **Identify the Audience**: Are you writing for an end-user, a contributor, or another AI agent?
2. **Draft the Content**: Write clear, concise markdown. Use code blocks, lists, and bold text for readability.
3. **Include Examples**: For APIs or commands, provide "Before & After" or "Input & Output" examples.
4. **Review and Format**: Ensure the markdown renders correctly and follows standard conventions.
5. **Keep it Updated**: Treat documentation as code. If the code changes, update the docs in the same PR.

## 6. Best practices
- **The README is the Homepage**: A good README answers: What is this? How do I install it? How do I use it?
- **Docstrings**: Use a consistent format (like Google Docstrings) for functions, detailing `Args`, `Returns`, and `Raises`.
- **Diagrams**: Use Mermaid.js markdown blocks to visualize complex flows (like RAG data flow) directly in the docs.

## 7. Coding conventions
- **Markdown**: Use `#` for Title, `##` for Major Sections, `###` for Sub-sections.
- **Python Docstrings**: Use triple quotes `"""` directly below the function/class definition.

## 8. Example prompts
- "Write a comprehensive README.md for our Discord Student FAQ bot, including a Mermaid diagram of the architecture."
- "Generate Google-style docstrings for this `Retriever` class and its methods."

## 9. Example tasks
- "Create a `docs/setup.md` file detailing how to install Qdrant, set up OpenAI API keys, and run the bot locally."
- "Write a `CONTRIBUTING.md` outlining our Git branching strategy and how to run tests before submitting a PR."

## 10. Common pitfalls
- **Stale Docs**: Documentation that references old, deleted files or outdated commands.
- **Over-commenting**: Writing comments that just repeat what the code obviously does (e.g., `x = x + 1 # increments x`).
- **Wall of Text**: Writing huge unformatted paragraphs instead of using bullet points and code blocks.

## 11. Directory structure
```
.
├── README.md
├── CONTRIBUTING.md
└── docs/
    ├── architecture.md
    └── local_setup.md
```

## 12. Suggested libraries
- `Sphinx` or `MkDocs` (for generating static documentation sites from docstrings)

## 13. References
- [Google Python Style Guide (Docstrings)](https://google.github.io/styleguide/pyguide.html#38-comments-and-docstrings)
- [Mermaid JS for Markdown diagrams](https://mermaid.js.org/)
