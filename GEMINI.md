---
description: General guidelines and context for the DashBoardD project.
trigger: always_on
---

# DashBoardD Project Context & Rules

## Project Overview
DashBoardD is a full-stack dashboard application managing ticket and callog metrics for FPT Shop and Long Châu.
- **Frontend**: React, TypeScript, Vite, Tailwind CSS, Lucide Icons (`dashboard-app/`).
- **Backend**: FastAPI, Python 3.12, SQLite (`backend/`).
- **Browser Automation**: Selenium with ChromeDriver (used for Long Chau and FPT Shop authentication/scraping).

## Coding Guidelines

### 1. Frontend (React/TypeScript)
- **Encoding**: Always ensure strings containing Vietnamese characters are saved correctly in UTF-8. Avoid regex string replacements that might break TSX/JSX syntax.
- **State Management**: Use React hooks (`useState`, `useEffect`). Handle pending promises and loading states carefully to avoid UI freezes ("trang bị đứng").
- **Components**: Use Tailwind CSS for styling. Keep components modular.

### 2. Backend (FastAPI/Python)
- **Database**: Use SQLAlchemy ORM with SQLite.
- **Concurrency**: Use multithreading safely (e.g., `threading.RLock`) when managing browser sessions.
- **External APIs**: When interacting with Budibase or other FRT APIs, ensure payloads respect schema requirements (e.g., use `sort` instead of `sortColumn` for Budibase search). Prevent infinite pagination loops by enforcing limits (e.g., breaking after 5000 rows).

## Known Issues to Watch Out For
- **Connection Exhaustion**: Do not spam login tabs using Selenium or poll APIs uncontrollably, as it exhausts Chrome's connection pool.
- **Mojibake**: Watch out for double-encoding when reading/writing files via PowerShell `Get-Content`. Use proper Python scripts with `utf-8` encoding when modifying codebase text.