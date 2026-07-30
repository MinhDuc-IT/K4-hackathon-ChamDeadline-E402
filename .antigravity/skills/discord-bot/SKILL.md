# Skill: Discord Bot Development

## 1. Purpose
This skill equips the agent with the knowledge and patterns to build, maintain, and extend robust Discord bots using `discord.py`. It provides guidelines on handling asynchronous events, structuring bot commands, and designing responsive chat interfaces.

## 2. Responsibilities
- Implementing and managing Discord bot lifecycle and connection.
- Creating and routing slash commands (application commands).
- Registering and handling Discord events (e.g., `on_message`, `on_ready`).
- Designing rich interactive messages using Embeds, Buttons, and Views.
- Managing Discord threads for extended conversations or context.
- Handling rate limits and async execution effectively.

## 3. When to use
- When creating a new Discord bot integration.
- When adding new slash commands or interactive UI components to an existing bot.
- When needing to parse Discord messages or user interactions for downstream tasks like RAG.

## 4. When NOT to use
- For non-Discord messaging platforms.
- For core business logic or complex state management not directly related to Discord UI (decouple these into separate modules).

## 5. Workflow
1. **Define Intent**: Determine the command or event you are responding to.
2. **Setup Cogs**: Use discord.ext.commands.Cog to logically group related commands and listeners.
3. **Handle Async Properly**: Ensure all Discord API interactions use `await`. Do not block the event loop with synchronous long-running code (use `asyncio.to_thread` if needed).
4. **Implement UI**: Use `discord.Embed` for structured responses and `discord.ui.View` for interactivity.
5. **Acknowledge Quickly**: Discord requires interactions to be acknowledged within 3 seconds. Use `await interaction.response.defer()` for tasks that take longer.

## 6. Best practices
- **Use Cogs**: Always organize commands into Cogs rather than dumping everything in the main file.
- **Defer Long Tasks**: For operations like RAG or API calls, immediately defer the interaction and use `followup.send()`.
- **Error Handling**: Implement `on_command_error` and `on_application_command_error` globally to catch and notify users of failures gracefully.
- **Environment Variables**: Never hardcode tokens; load them via `.env`.

## 7. Coding conventions
- Use Python's Type Hinting for all command parameters.
- Use `discord.app_commands` for slash commands.
- Keep the Cog classes stateless where possible; inject dependencies (like DB or Search clients) during initialization.

## 8. Example prompts
- "Create a new Discord slash command `/ask` that takes a query string, defers the response, queries our RAG pipeline, and returns an Embed with the answer."
- "Implement a Button view that allows a user to thumbs-up or thumbs-down a bot response."

## 9. Example tasks
- "Set up the main `bot.py` using `discord.ext.commands.Bot` and load a `QA_Cog`."
- "Create an event listener that creates a thread automatically when a user asks a question in a specific channel."

## 10. Common pitfalls
- **Blocking the Event Loop**: Running synchronous DB queries or heavy computation inside a command.
- **Missing Intents**: Not enabling `Message Content Intent` on the Discord Developer Portal while trying to read messages.
- **Token Leakage**: Accidentally committing `.env` or hardcoding the bot token.
- **Interaction Expiration**: Taking more than 3 seconds to respond without deferring.

## 11. Directory structure
```
bot/
├── cogs/
│   ├── __init__.py
│   ├── qa_cog.py
│   └── admin_cog.py
├── core/
│   ├── __init__.py
│   └── bot_setup.py
└── main.py
```

## 12. Suggested libraries
- `discord.py` (Main library)
- `python-dotenv` (For config)

## 13. References
- [discord.py Documentation](https://discordpy.readthedocs.io/en/stable/)
- [Discord Developer Portal](https://discord.com/developers/docs/intro)
