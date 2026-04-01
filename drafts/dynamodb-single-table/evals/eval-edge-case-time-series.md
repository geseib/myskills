<!-- eval-version: v1 -->
<!-- eval-notes: v1=Original criteria -->
# Eval: IoT time-series with high write volume

**Skill:** `dynamodb-single-table`
**Type:** edge-case

## Prompt

```
Design a DynamoDB table for an IoT platform. Thousands of sensors report temperature readings every 10 seconds. I need to:
- Get the latest reading for a sensor
- Query readings for a sensor in a time range (last hour, last day)
- List all sensors in a facility
- Alert on readings above a threshold (this triggers a Lambda)
- Readings older than 90 days should be automatically deleted
```

## Expected behavior

- [ ] Starts with access pattern table
- [ ] Uses time-bucketed partition keys to prevent unbounded partition growth (e.g., SENSOR#<id>#2024-03)
- [ ] Uses ISO timestamp or epoch as sort key for range queries
- [ ] Recommends TTL (90 days) for automatic cleanup
- [ ] Addresses the "latest reading" pattern (either overwrite a LATEST item or query with ScanIndexForward=false, Limit=1)
- [ ] Mentions DynamoDB Streams + Lambda for threshold alerting
- [ ] Warns about hot partition risk with high-frequency writes

## Should NOT

- Should not use a single PK per sensor without bucketing (unbounded growth)
- Should not suggest Scan for time-range queries
- Should not ignore the 10GB partition size limit
- Should not forget TTL for the 90-day expiration

## Pass criteria

Time-bucketed partitions are used. TTL is set for 90-day cleanup. Streams mentioned for alerting. Hot partition risk addressed. All access patterns satisfied without Scan.
