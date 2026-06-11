# Agent Instructions

## Working Style

- Think before coding. State assumptions, surface tradeoffs, and ask when the task is genuinely unclear.
- Prefer the minimum code that solves the request. Do not add speculative flexibility, broad refactors, or unrelated cleanup.
- Make surgical changes. Every changed line should trace back to the user request.
- Turn work into verifiable goals and loop until the result is checked.

## Project Memory

- Durable project memory lives in `_docs/agent-memory/`.
- Temporary task handoffs belong in `_docs/handoff/`, not in `AGENTS.md`.
- Do not paste raw chat history into `AGENTS.md`; curate long-lived rules and link to memory notes.
- Do not copy secrets, tokens, cookies, passwords, private server credentials, or full authorization headers from historical conversations into project files.

## AI Work Split

- Use higher-reasoning sessions for understanding, task decomposition, architecture decisions, and review.
- Use execution-focused sessions for narrow implementation tasks based on written handoffs or specs.
- Use `git diff`, task files, and durable memory as the shared context between sessions instead of relying on full chat history.
