# Eval: Build a secure REST API

**Skill:** `nodejs-security`
**Type:** happy-path

## Prompt

```
Build a Node.js Express REST API for a task management app. Users can:
- Register with email and password
- Login and get a session/token
- Create tasks (title, description, due date)
- List their own tasks
- Mark tasks complete
- Delete their own tasks

Use PostgreSQL for storage.
```

## Expected behavior

- [ ] Starts with or mentions threat model (what are we protecting)
- [ ] Input validation on all endpoints using Zod/Joi (not manual checks)
- [ ] Passwords hashed with bcrypt (salt rounds >= 10)
- [ ] Authentication via JWT or secure session cookies (HttpOnly, Secure, SameSite)
- [ ] Authorization: users can only access their own tasks (scoped queries)
- [ ] Parameterized SQL queries (no string interpolation)
- [ ] Security headers via helmet
- [ ] Rate limiting on auth endpoints
- [ ] Production error handler that doesn't leak stack traces
- [ ] Secrets loaded from environment variables, not hardcoded
- [ ] CORS configured with explicit origin (not wildcard)

## Should NOT

- Should not store passwords in plaintext or with MD5/SHA256
- Should not use `eval()` or string-interpolated SQL
- Should not return raw database errors to the client
- Should not skip input validation on any endpoint
- Should not use `cors({ origin: '*' })` with credentials

## Pass criteria

API has input validation on all endpoints, bcrypt for passwords, parameterized queries, helmet headers, rate limiting on auth, authorization scoping tasks to owner, and production-safe error handling.
