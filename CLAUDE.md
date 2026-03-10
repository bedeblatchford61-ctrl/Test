# CLAUDE.md

This file provides guidance for AI assistants (including Claude) working in this repository.

## Project Overview

This is the **Test** repository. It is currently in its initial setup phase.

## Repository Structure

```
/
├── CLAUDE.md          # AI assistant guidance (this file)
└── (project files)    # To be added as the project develops
```

## Development Workflow

### Branch Conventions

- **Main branch**: `main` (or `master`)
- **Feature branches**: Use descriptive names prefixed by category (e.g., `feature/`, `fix/`, `docs/`)
- Keep commits atomic and well-described

### Commit Messages

Follow conventional commit style:

```
<type>: <short summary>

<optional body with more detail>
```

Types: `feat`, `fix`, `docs`, `refactor`, `test`, `chore`, `style`, `ci`

### Code Quality

- Write clear, readable code with meaningful variable and function names
- Prefer simplicity over cleverness
- Add comments only where the intent is non-obvious
- Do not leave dead code or commented-out blocks

### Testing

- Write tests for new functionality
- Run the full test suite before pushing changes
- Ensure all tests pass before creating pull requests

### Security

- Never commit secrets, API keys, or credentials
- Use environment variables or secret management for sensitive configuration
- Validate all external input at system boundaries

## Key Conventions

1. **Keep changes minimal** — only modify what is necessary for the task at hand
2. **Read before writing** — understand existing code before making changes
3. **No over-engineering** — solve the current problem, not hypothetical future ones
4. **Preserve existing patterns** — follow the conventions already established in the codebase
