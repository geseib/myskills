# Eval: Multi-tenant API with data isolation

**Skill:** `nodejs-security`
**Type:** edge-case

## Prompt

```
I'm building a multi-tenant SaaS API in Express with PostgreSQL. Each customer
(organization) has users, and users should only see data from their own org.
We need:
- Org admin can invite users
- Users can CRUD projects within their org
- Org admin can manage billing
- Super admin can view all orgs (support dashboard)

How should I structure the API and database queries to ensure tenant isolation?
```

## Expected behavior

- [ ] Every database query scoped to the authenticated user's org_id
- [ ] Middleware or helper that automatically injects tenant context
- [ ] Authorization model with at least 3 roles: user, org-admin, super-admin
- [ ] Super-admin access is explicitly gated (not just "no org filter")
- [ ] Input validation on all endpoints
- [ ] IDOR prevention: can't access another org's resources by guessing IDs
- [ ] Rate limiting per-tenant or per-user
- [ ] Warns about horizontal privilege escalation risks
- [ ] Database-level enforcement recommended (RLS or WHERE clause in every query)

## Should NOT

- Should not rely solely on frontend to filter org data
- Should not use sequential/guessable IDs without authorization checks
- Should not give super-admin a bypass that could accidentally leak to regular users
- Should not skip tenant scoping on any data access query

## Pass criteria

Every query is tenant-scoped. Role-based authorization with clear escalation boundaries. IDOR explicitly addressed. Database-level enforcement discussed.
