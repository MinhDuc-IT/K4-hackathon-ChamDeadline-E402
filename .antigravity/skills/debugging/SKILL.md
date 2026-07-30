# Skill: Debugging and Troubleshooting

## 1. Purpose
This skill equips the agent with systematic methods to diagnose, trace, and resolve issues within the Discord bot, the RAG pipeline, async execution, and production deployments.

## 2. Responsibilities
- Diagnosing errors in Discord bot event loops and slash commands.
- Troubleshooting asynchronous bugs (race conditions, deadlocks, blocking code).
- Tracing data loss or poor performance in retrieval pipelines and Vector DBs.
- Identifying prompt engineering failures (e.g., model hallucinations).
- Reading, parsing, and understanding production error logs and stack traces.

## 3. When to use
- When the bot crashes, throws an exception, or hangs unexpectedly.
- When the LLM outputs poor, incorrect, or unformatted responses.
- When performance degrades (e.g., the bot takes 10 seconds to respond).

## 4. When NOT to use
- Do not apply 'quick fixes' or patch symptoms without understanding the root cause (e.g., wrapping everything in a blanket `try-except` block).

## 5. Workflow
1. **Reproduce the Bug**: Understand the exact inputs and conditions that trigger the error.
2. **Examine Logs & Tracebacks**: Look at the Python stack trace to find the exact file and line number where the failure originated.
3. **Isolate the Component**: Is it a Discord issue (API limit), a Vector DB issue (empty result), an LLM issue (timeout), or a code logic bug?
4. **Formulate Hypothesis**: Propose a reason for the failure.
5. **Test the Fix**: Implement a targeted fix, run tests, and verify the bug is resolved without breaking other features.

## 6. Best practices
- **Verbose Logging**: When debugging, temporarily increase log levels to `DEBUG` to see data flow.
- **Trace the Data**: For RAG, log the exact query embedded, the exact chunks retrieved, and the exact prompt sent to the LLM. Often, the bug is just bad retrieved data, not bad code.
- **Use Debuggers**: Use `pdb` or IDE debuggers to step through code execution rather than relying solely on `print()` statements.

## 7. Coding conventions
- Always log the caught exception's traceback using `logger.error("Error message", exc_info=True)`.
- Write tests that specifically reproduce the bug before fixing it, ensuring it never regressions.

## 8. Example prompts
- "The Discord bot is raising a `discord.errors.InteractionResponded` error. Analyze this code and fix the duplicate response handling."
- "The RAG pipeline is returning 'I don't know' for a question that is clearly in the document. How should we debug the retrieval step?"

## 9. Example tasks
- "Implement a global error handler for the Discord bot that catches unhandled exceptions, logs them to a file, and sends a polite error message to the user."
- "Set up an APM (Application Performance Monitoring) tool or detailed timing logs to figure out why the `/ask` command sometimes times out."

## 10. Common pitfalls
- **Silent Failures**: Swallowing exceptions with `except:` and not logging them, making it impossible to know a bug occurred.
- **Misinterpreting Async Errors**: Confusing a coroutine object with its result (forgetting `await`), which causes obscure `RuntimeWarning: coroutine was never awaited`.
- **Assuming the LLM is broken**: Often, poor LLM answers are due to the Vector DB returning garbage chunks, not the model failing.

## 11. Directory structure
*(Debugging concepts apply globally across the repository)*

## 12. Suggested libraries
- `pdb` / `ipdb`
- `logging`
- `sentry-sdk` (for production error tracking)

## 13. References
- [Python Debugging with Pdb](https://docs.python.org/3/library/pdb.html)
- [Discord.py Error Handling](https://discordpy.readthedocs.io/en/stable/ext/commands/api.html#discord.ext.commands.on_command_error)
