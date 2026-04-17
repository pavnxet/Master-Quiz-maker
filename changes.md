# Project Change Audit Log

This document tracks significant changes and fixes applied to the `Quiz-Master-HTML` project by the AI coding assistant.

## 🟢 Current Session Audits (Conversation: 5bd06352)

### 1. Robust Deduplication Logic
**Timestamp:** 2026-04-16 | 10:52 PM
**Implementation:**
- Added `dedupKey(q)` utility to normalize English/Hindi text and create composite keys.
- Handles Hindi-only questions, English-only questions, and falls back to options hash.
- Fixes issue where duplicates slipped through if `qEnglish` was missing or slightly different.

### 2. Event Listener Stability & Navigation Fix
**Timestamp:** 2026-04-16 | 11:00 PM
**Implementation:**
- Wrapped all quiz-side listeners in `DOMContentLoaded`.
- Introduced `on()` safety helper to prevent script crashes if DOM elements are missing.
- Fixed the missing wiring for `next-btn` and `skip-btn`.
- Consolidated "Finish" vs "Next" logic into central listeners.

### 3. Generated HTML Syntax Error Fix (Escape Newlines)
**Timestamp:** 2026-04-16 | 11:19 PM
**Implementation:**
- Double-escaped newlines (`\n` -> `\\n`) inside `worker.js` template literals.
- Prevents browsers from seeing literal physical line breaks inside regexes (`/[,\n]/`) or strings (`join('\n')`), which previously caused fatal `SyntaxError` crashes.

---

## 📜 Last 5 Historical Audits

### 4. Repository Cleanup & GitHub Preparation
**Summary:** Sanitized the repository by removing unnecessary files and ensuring no sensitive information (API keys/secrets) was exposed before pushing to the new `Master-Quiz-maker` repository.
