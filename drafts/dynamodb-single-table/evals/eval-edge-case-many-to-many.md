<!-- eval-version: v1 -->
<!-- eval-notes: v1=Original criteria -->
# Eval: Many-to-many relationship

**Skill:** `dynamodb-single-table`
**Type:** edge-case

## Prompt

```
Design a DynamoDB table for a scheduling app. Doctors see patients. I need to:
- List all patients for a doctor
- List all doctors for a patient
- Get appointment details
- List upcoming appointments by date
```

## Expected behavior

- [ ] Uses adjacency list pattern (PK=DOCTOR#id, SK=PATIENT#id)
- [ ] Uses inverted GSI (GSI1PK=SK, GSI1SK=PK) to query from either direction
- [ ] Handles the date-based query with a time-sortable SK or separate GSI
- [ ] Does not create two separate tables for the two directions

## Should NOT

- Should not duplicate items manually for both directions (the GSI handles inversion)
- Should not require Scan for either direction of the relationship
- Should not create more than 2 GSIs

## Pass criteria

Both directions of the doctor-patient relationship are queryable. Date-based filtering works. Design uses adjacency list with inverted GSI.
