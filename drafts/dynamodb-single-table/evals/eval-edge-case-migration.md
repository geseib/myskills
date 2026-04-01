<!-- eval-version: v1 -->
<!-- eval-notes: v1=Original criteria -->
# Eval: Existing relational schema migration

**Skill:** `dynamodb-single-table`
**Type:** edge-case

## Prompt

```
I'm migrating from PostgreSQL to DynamoDB. Currently I have these tables:
- users (id, email, name, org_id)
- organizations (id, name, plan)
- invoices (id, org_id, amount, status, created_at)
- invoice_line_items (id, invoice_id, description, amount)

My queries are:
- Get user by email
- List users in an org
- Get invoice with all line items
- List invoices for an org by date
- List unpaid invoices across all orgs (admin view)
```

## Expected behavior

- [ ] Starts with access pattern table
- [ ] Does NOT map SQL tables 1:1 to DynamoDB entities
- [ ] Denormalizes where appropriate (e.g., org name on user items)
- [ ] Co-locates invoice + line items under same PK
- [ ] Handles "unpaid invoices across all orgs" with sparse GSI or entity-type index
- [ ] Warns about denormalization trade-offs (data duplication, update complexity)
- [ ] Produces entity chart showing the flattened single-table structure

## Should NOT

- Should not create 4 separate DynamoDB tables mirroring the SQL schema
- Should not use Scan for the admin "all unpaid invoices" query
- Should not assume JOINs exist in DynamoDB
- Should not skip discussing what changes about the data model in the migration

## Pass criteria

Design collapses 4 SQL tables into 1 DynamoDB table. Denormalization is applied. Invoice + line items co-located. Admin query uses GSI. Migration considerations discussed.
