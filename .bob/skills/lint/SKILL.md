---
name: lint
description: Focused code review of the current file or specified code. Identifies bugs, security vulnerabilities, anti-patterns, and performance issues. Output is direct and minimal — issue, location, fix. No preamble, no praise.
---

When /lint is activated, review the specified code or current file using the rules below.

## Review Priority Order

Check in this order — stop at CRITICAL issues and report them first:

1. **CRITICAL — Security**
   - Hardcoded credentials, API keys, or secrets
   - SQL injection vectors (string concatenation in queries)
   - Command injection (unsanitised input passed to shell)
   - Unvalidated user input at API boundaries
   - Exposed stack traces or internal errors to clients
   - Insecure deserialization

2. **HIGH — Bugs**
   - Logic errors and incorrect conditionals
   - Unhandled exceptions and missing error paths
   - Null / None access without guard
   - Off-by-one errors in loops or slices
   - Race conditions in async code
   - Mutable default arguments in Python functions

3. **MEDIUM — Anti-patterns**
   - Blocking I/O calls inside async functions
   - Circular imports or inappropriate cross-module dependencies
   - God functions (>50 lines doing unrelated things)
   - Missing resource cleanup (unclosed files, connections, cursors)
   - Silent exception swallowing (`except: pass`)

4. **LOW — Performance and Style**
   - N+1 query patterns
   - Unnecessary synchronous waits in async context
   - Naming convention violations (should be snake_case in Python)
   - Dead code or unreachable branches
   - Overly complex boolean expressions that could be simplified

## Output Format

```
[SEVERITY] Line X — Short description of the issue.
Fix: One-line description of the correct approach.
```

One entry per issue. Severity: CRITICAL / HIGH / MEDIUM / LOW.

## Rules

- No preamble. Start directly with the first issue found.
- No praise, no "overall this is good code".
- If no issues are found, output exactly: `No issues found.`
- Do not suggest refactors unless they directly fix a bug or security issue.
- Do not rewrite entire files — flag and suggest targeted fixes only.
- If reviewing Python: enforce snake_case, type hints at function boundaries, and `async` correctness.
- If reviewing FastAPI routes: check for missing input validation (Pydantic models), missing status codes, and unhandled exceptions leaking to the client.
