# Eval: Basic app — e-commerce orders

**Skill:** `dynamodb-single-table`
**Type:** happy-path

## Prompt

```
Design a DynamoDB table for an e-commerce app. Users place orders containing line items. I need to:
- Get a user's profile
- List a user's orders (newest first)
- Get a specific order with its line items
- List orders by status (OPEN, SHIPPED, DELIVERED)
```

## Expected behavior

- [ ] Starts by listing access patterns in a table before designing keys
- [ ] Uses generic PK/SK naming
- [ ] Uses entity-type prefixes (e.g., USER#, ORDER#)
- [ ] Co-locates order + line items under same PK for single-query fetch
- [ ] Uses a GSI with sparse index or overloading for status-based queries
- [ ] Targets 1-2 GSIs, not more
- [ ] Outputs an entity chart showing all entity types
- [ ] Includes IaC definition (CDK, SAM, or CloudFormation)
- [ ] Recommends PAY_PER_REQUEST and TTL

## Should NOT

- Should not use Scan for any access pattern
- Should not create a separate GSI for each access pattern
- Should not use specific attribute names like `userId` for partition key
- Should not skip the access pattern listing step

## Pass criteria

All access patterns are satisfied with GetItem or Query operations. The design uses no more than 2 GSIs. Entity chart is present and complete.
