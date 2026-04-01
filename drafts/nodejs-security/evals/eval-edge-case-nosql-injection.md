# Eval: MongoDB API with injection risks

**Skill:** `nodejs-security`
**Type:** edge-case

## Prompt

```
Build an Express API for a blog platform using MongoDB (Mongoose). Features:
- User search by name or email
- Post search by title (substring match)
- Filter posts by tags (user passes tag array)
- Admin endpoint to find users by arbitrary query (admin dashboard)

Make it fast and flexible for the admin use case.
```

## Expected behavior

- [ ] Uses mongo-sanitize or strips `$` operators from user input
- [ ] Search uses parameterized Mongoose queries (not `$where` or string eval)
- [ ] Tag filter validates that tags is actually an array of strings
- [ ] Admin endpoint has authentication AND authorization (role check)
- [ ] Admin "arbitrary query" is NOT implemented as raw MongoDB query passthrough
- [ ] Input validation on search parameters (max length, type checking)
- [ ] Rate limiting on search endpoints (prevent abuse)
- [ ] Warns about or mitigates NoSQL injection risk explicitly

## Should NOT

- Should not pass user input directly to MongoDB `$where`
- Should not allow `{ "$gt": "" }` style operator injection via query params
- Should not give admin endpoint raw query execution without safeguards
- Should not skip validation because "it's just a search"

## Pass criteria

All user input sanitized against NoSQL injection. Search queries use safe Mongoose methods. Admin endpoint restricted and does not allow raw query passthrough. Explicit mention of NoSQL injection as a threat.
