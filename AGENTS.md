# AGENTS.md

You are working on a local technical project that needs to be prepared as a clean GitHub repository with strong documentation.

The project may include n8n workflows, GLPI integration, Docker services, a dashboard, API calls, local configuration, and supporting scripts.

Your job is to inspect the project, understand how it works, and create documentation that is accurate, practical, and human-written. Do not invent details. If something is unclear, write it as an assumption or a TODO.

## Main goal

Prepare this local project for GitHub by creating:

- a clear README.md
- a safe .gitignore
- a sanitized .env.example if configuration is needed
- docs/ with architecture, setup, workflows, integration notes, dashboard notes, Docker notes, and troubleshooting
- component-level README files where useful
- Mermaid diagrams where they help explain the system

## Non-negotiable rules

1. Do not delete source files.
2. Do not move source files unless the user explicitly asks.
3. Do not run destructive commands.
4. Do not run:
   - docker rm
   - docker rmi
   - docker volume rm
   - docker system prune
   - git reset --hard
   - git clean -fd
   - database deletion commands
5. Do not expose secrets in documentation.
6. Do not copy real tokens, passwords, API keys, cookies, database passwords, n8n credentials, GLPI app tokens, GLPI user tokens, or session tokens into any committed file.
7. If a file contains secrets, document only the variable names and purpose, not the values.
8. Prefer creating documentation and safe example files over changing application logic.
9. Before editing, inspect the project structure and summarize what exists.
10. Every important claim in documentation should be grounded in actual project files, config, exported workflows, or observed Docker/service names.
11. Do not make the writing sound like generic AI marketing copy.
12. Avoid phrases like:
    - seamless
    - robust solution
    - cutting-edge
    - leverage
    - powerful platform
    - unlock productivity
    - end-to-end ecosystem
13. Write like a developer documenting a real project after building/debugging it.

## Documentation style

Use practical, direct writing.

Good style:

> This project connects n8n to GLPI so ticket data can be collected, processed, and shown in a dashboard. The local environment uses Docker containers for GLPI, MySQL, n8n, and monitoring services.

Bad style:

> This innovative solution leverages automation to deliver a seamless and robust ITSM experience.

Documentation should explain:

- what the project does
- why each component exists
- how the services talk to each other
- what needs to be configured
- how to run it locally
- how to troubleshoot common failures
- which parts are still manual or incomplete

## Repository safety

Create or update `.gitignore` to exclude at least:

- `.env`
- `.env.*`
- `!.env.example`
- `node_modules/`
- `vendor/`
- `dist/`
- `build/`
- `.DS_Store`
- `Thumbs.db`
- `*.log`
- `logs/`
- `tmp/`
- `.cache/`
- database dumps
- n8n credential exports
- GLPI tokens
- Docker volume data
- local backups
- screenshots containing secrets

If unsure whether a file contains secrets, do not include its content in docs. Describe it generically.

## Expected documentation files

Create these files if they do not already exist:

```txt
README.md
docs/00-project-overview.md
docs/01-architecture.md
docs/02-installation.md
docs/03-configuration.md
docs/04-n8n-workflows.md
docs/05-glpi-integration.md
docs/06-dashboard.md
docs/07-docker-services.md
docs/08-troubleshooting.md
docs/09-security-and-secrets.md
n8n/workflows/README.md
glpi/README.md
dashboard/README.md
infra/README.md