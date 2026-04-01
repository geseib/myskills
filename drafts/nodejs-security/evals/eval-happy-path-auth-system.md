# Eval: Authentication system with JWT

**Skill:** `nodejs-security`
**Type:** happy-path

## Prompt

```
Build a complete authentication system for my Express API:
- User registration
- Login (returns tokens)
- Token refresh
- Password reset via email
- Logout

Use JWT for authentication.
```

## Expected behavior

- [ ] Passwords stored with bcrypt (salt rounds >= 10)
- [ ] Short-lived access tokens (<=15 min) and longer refresh tokens
- [ ] Refresh token rotation (old refresh token invalidated on use)
- [ ] JWT includes `iss`, `aud`, or `sub` claims for validation
- [ ] Password reset tokens are time-limited and single-use
- [ ] Rate limiting on login, register, and password reset endpoints
- [ ] Logout invalidates or blacklists the refresh token
- [ ] Secure cookie settings if cookies are used (HttpOnly, Secure, SameSite)
- [ ] No secrets hardcoded — JWT secret from environment variable
- [ ] Input validation on email, password strength requirements

## Should NOT

- Should not use HS256 without mentioning RS256 as better for multi-service
- Should not store tokens in localStorage (if client guidance given)
- Should not have password reset tokens that never expire
- Should not skip rate limiting on auth endpoints
- Should not log passwords or tokens

## Pass criteria

Bcrypt password storage, short-lived access tokens with refresh rotation, time-limited password reset, rate limiting on all auth endpoints, JWT secret from env, input validation on all fields.
