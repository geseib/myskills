# Eval: Multi-tenant SaaS application

**Skill:** `dynamodb-single-table`
**Type:** happy-path

## Prompt

```
Design a DynamoDB table for a multi-tenant project management SaaS. Each tenant (organization) has users, projects, and tasks. I need to:
- Get a user's profile by ID
- List all users in an organization
- List all projects in an organization
- List tasks in a project, filterable by status (TODO, IN_PROGRESS, DONE)
- List tasks assigned to a specific user across all projects
- Get a single task by ID
```

## Expected behavior

- [ ] Starts with access pattern table
- [ ] Uses ORG#<id> or TENANT#<id> as primary PK for tenant isolation
- [ ] Co-locates users, projects, tasks under the org PK where appropriate
- [ ] Uses GSI overloading for cross-cutting queries (tasks by assignee, tasks by status)
- [ ] Keeps tenant data isolated — no cross-tenant leakage in any access pattern
- [ ] Outputs entity chart and IaC
- [ ] Recommends PAY_PER_REQUEST

## Should NOT

- Should not create separate tables per tenant
- Should not use Scan for any access pattern
- Should not create more than 3 GSIs
- Should not allow a query on one tenant to return another tenant's data

## Pass criteria

All 6 access patterns satisfied with GetItem/Query. Tenant isolation is maintained. GSI count <= 3. Design handles the cross-cutting "tasks by assignee" pattern elegantly.
