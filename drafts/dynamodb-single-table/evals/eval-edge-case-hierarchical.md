# Eval: Deep hierarchy with variable-depth queries

**Skill:** `dynamodb-single-table`
**Type:** edge-case

## Prompt

```
Design a DynamoDB table for a company directory. The hierarchy is: Company > Division > Department > Team > Employee. I need to:
- List all employees in a specific team
- List all teams in a department
- List everyone in an entire division (all departments, teams, employees)
- Get an individual employee's record
- Search employees by email
```

## Expected behavior

- [ ] Starts with access pattern table
- [ ] Uses composite sort keys to encode the hierarchy (e.g., SK = DIV#eng#DEPT#platform#TEAM#infra#EMP#alice)
- [ ] Leverages `begins_with` on SK for variable-depth queries
- [ ] Uses a GSI for email lookup (sparse or overloaded)
- [ ] Single PK per company (or warns about partition size if company is very large)

## Should NOT

- Should not create separate tables or separate PKs for each hierarchy level
- Should not require multiple queries to traverse the hierarchy
- Should not use Scan for any level of hierarchy traversal
- Should not use nested/map attributes to encode hierarchy (that can't be queried)

## Pass criteria

Composite sort key encodes full hierarchy path. `begins_with` queries work at every level. Email lookup uses GSI. Design is a single table.
