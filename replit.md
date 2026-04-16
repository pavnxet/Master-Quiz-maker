# Workspace

## Overview

pnpm workspace monorepo using TypeScript. Each package manages its own dependencies.

## Stack

- **Monorepo tool**: pnpm workspaces
- **Node.js version**: 24
- **Package manager**: pnpm
- **TypeScript version**: 5.9
- **API framework**: Express 5
- **Database**: PostgreSQL + Drizzle ORM
- **Validation**: Zod (`zod/v4`), `drizzle-zod`
- **API codegen**: Orval (from OpenAPI spec)
- **Build**: esbuild (CJS bundle)

## Key Commands

- `pnpm run typecheck` — full typecheck across all packages
- `pnpm run build` — typecheck + build all packages
- `pnpm --filter @workspace/api-spec run codegen` — regenerate API hooks and Zod schemas from OpenAPI spec
- `pnpm --filter @workspace/db run push` — push DB schema changes (dev only)
- `pnpm --filter @workspace/api-server run dev` — run API server locally

See the `pnpm-workspace` skill for workspace structure, TypeScript setup, and package details.

## Quiz Generator (Python)

A standalone Python tool that converts a JSON quiz file into a rich self-contained HTML quiz page.

### Files
- `quiz_generator.py` — the main script (no external dependencies, uses Python stdlib only)
- `sample_quiz.html` — example output generated from the uploaded questions

### Usage
```bash
python3 quiz_generator.py <input_file.txt|json> [output_file.html]
```

### Input Format
JSON array of objects with fields:
- `qHindi`, `qEnglish` — question text
- `optionsHindi`, `optionsEnglish` — array of 4 option strings
- `correct` — 0-based index of correct answer
- `explanationHindi`, `explanationEnglish` — explanation text
- `subject`, `topic` — for filtering and stats

### Output Features
- Quiz mode with timer (60s/question, customizable, or no timer)
- Subject/topic filtering and random/sequential question order
- Question navigator with color-coded status dots
- Auto-reveal answers with explanations after each answer
- Detailed results page with subject-wise breakdown
- Review mode (filter by correct/wrong/skipped)
- Stats page with full session history (stored in browser localStorage)
- Hindi/English language toggle
- 100% self-contained (single .html file, no internet needed)
