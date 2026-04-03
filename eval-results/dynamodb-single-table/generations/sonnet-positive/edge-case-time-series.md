# DynamoDB Single-Table Design: IoT Sensor Platform

Time-series at scale requires careful partitioning. Let me address the hot partition risk upfront.

---

## Step 1: Access Patterns

| # | Access Pattern | Operation | Key Condition |
|---|---|---|---|
| 1 | Get latest reading for a sensor | Query | PK=`SENSOR#sensorId#<currentBucket>`, SK begins_with `READING#`, ScanIndexForward=false, Limit=1 |
| 2 | Query readings for a sensor in last hour | Query | PK=`SENSOR#sensorId#<currentBucket>`, SK between `READING#<1hrAgo>` and `READING#<now>` |
| 3 | Query readings for a sensor in last day | Query (multi-bucket) | Query 24 hourly buckets or 1 daily bucket for sensorId |
| 4 | List all sensors in a facility | Query (GSI1) | GSI1PK=`FACILITY#facilityId`, GSI1SK begins_with `SENSOR#` |
| 5 | Alert on readings above threshold | DynamoDB Streams → Lambda | Stream filters on threshold attribute |
| 6 | Auto-delete readings older than 90 days | TTL | ttl attribute set at write time |

---

## Step 2: Key Design

**Base Table:** `PK` (String) + `SK` (String)

### The Hot Partition Problem

With 1,000s of sensors reporting every 10 seconds, naively using `PK=SENSOR#sensorId` would put all of one sensor's data in a single partition — which is fine for reads per sensor but limits write throughput to DynamoDB's per-partition limit.

More critically, if you had used `PK=READINGS` or any low-cardinality partition for all sensors, you'd hit a severe hot partition. We avoid this by using the sensor ID as the PK — each sensor is its own partition.

### Time Bucketing

**Use hourly buckets** to bound partition size and enable efficient time-range queries:

`PK = SENSOR#<sensorId>#<YYYY-MM-DDTHH>` (e.g., `SENSOR#abc123#2024-12-15T14`)

Benefits:
- Each partition holds at most 360 readings per hour (every 10s × 3600s = 360 items)
- At ~200 bytes/reading: ~72KB per partition — well within DynamoDB limits
- Time-range queries within an hour hit exactly one partition
- "Last day" query hits at most 24 partitions (paginated or parallel)

**SK for readings:**
`READING#<isoTimestamp>` (e.g., `READING#2024-12-15T14:32:10Z`)

ISO timestamps sort lexicographically, so newest-first is `ScanIndexForward=false`, and range queries use `between`.

### Latest Reading

For "get the latest reading," query the current hour bucket with `ScanIndexForward=false, Limit=1`. If the sensor hasn't reported this hour yet, fall back to the previous hour bucket. This 1-2 partition lookup is fast and cheap.

Alternatively, maintain a `SENSOR#sensorId` / `LATEST` item updated with each write (using `UpdateItem`). This is faster for the latest-reading pattern but adds a write per reading.

---

## Step 2b: Patterns That Don't Fit DynamoDB

- **Alert on readings above threshold**: **DynamoDB Streams + Lambda** is the right architecture. The Lambda receives the stream event, checks the value against threshold, and triggers the alert. Do NOT poll DynamoDB for threshold violations — that's a Scan.
- **Aggregate analytics** (average temperature per facility per day, trends): Use **Redshift** or **OpenSearch** with zero-ETL from DynamoDB Streams. DynamoDB cannot do aggregations efficiently.
- **Cross-sensor queries** (e.g., "all sensors in facility X above 80°F right now"): This is a fan-out query — query each sensor's current bucket in parallel, or use **OpenSearch** with Streams to index the latest values.
- **Backfill or bulk import of historical data**: Write directly to DynamoDB with appropriate bucket PKs and TTLs. Use BatchWriteItem for efficiency.

---

## Step 3: GSI Design

**GSI1** — Sensors by facility
- `GSI1PK` = `FACILITY#facilityId`
- `GSI1SK` = `SENSOR#sensorId`
- **Sparse**: only sensor registration records (not reading records) populate this index
- Handles pattern 4: list all sensors in a facility

This is the only GSI needed. Reading records do NOT populate GSI1 (they omit `GSI1PK`/`GSI1SK` attributes), so the index stays lean even with millions of readings.

**Write amplification:** Only the sensor registration record writes to GSI1. The high-volume reading records write only to the base table. This keeps GSI write cost at 1× for readings, 2× only for the rare sensor registration writes.

---

## Step 4: Design Output

### Entity Chart

| Entity | PK | SK | GSI1PK | GSI1SK | Key Attributes |
|---|---|---|---|---|---|
| Sensor registration | `SENSOR#sensorId` | `META` | `FACILITY#facilityId` | `SENSOR#sensorId` | facilityId, type, location, installedAt |
| Sensor reading | `SENSOR#sensorId#<YYYY-MM-DDTHH>` | `READING#<isoTimestamp>` | — | — | value, unit, sensorId, ttl |
| Sensor latest (optional) | `SENSOR#sensorId` | `LATEST` | — | — | value, timestamp, unit (updated each write) |

### Access Pattern Resolution

| # | Access Pattern | How |
|---|---|---|
| 1 | Latest reading for a sensor | `Query(PK=SENSOR#s1#2024-12-15T14, SK begins_with READING#, ScanIndexForward=false, Limit=1)` — or `GetItem(PK=SENSOR#s1, SK=LATEST)` if maintaining latest item |
| 2 | Readings in last hour | `Query(PK=SENSOR#s1#2024-12-15T14, SK between READING#2024-12-15T13:32:00Z and READING#2024-12-15T14:32:00Z)` |
| 3 | Readings in last day | Query 24 hourly buckets: `SENSOR#s1#2024-12-15T00` through `SENSOR#s1#2024-12-15T23` (parallel or sequential) |
| 4 | List sensors in a facility | `Query(GSI1, GSI1PK=FACILITY#f1, GSI1SK begins_with SENSOR#)` |
| 5 | Alert on threshold | Streams + Lambda (no DynamoDB query needed) |
| 6 | Auto-delete after 90 days | TTL: set `ttl = writetime + 90*24*3600` on each reading record |

### IaC Definition (CDK — TypeScript)

```typescript
import * as cdk from 'aws-cdk-lib';
import * as dynamodb from 'aws-cdk-lib/aws-dynamodb';
import { Construct } from 'constructs';

export class IoTSensorTable extends Construct {
  public readonly table: dynamodb.Table;

  constructor(scope: Construct, id: string) {
    super(scope, id);

    this.table = new dynamodb.Table(this, 'IoTSensorTable', {
      tableName: 'iot-sensors',
      partitionKey: { name: 'PK', type: dynamodb.AttributeType.STRING },
      sortKey: { name: 'SK', type: dynamodb.AttributeType.STRING },
      billingMode: dynamodb.BillingMode.PAY_PER_REQUEST,
      timeToLiveAttribute: 'ttl',           // required for 90-day auto-delete
      pointInTimeRecovery: true,
      deletionProtection: true,
      stream: dynamodb.StreamViewType.NEW_IMAGE, // required for threshold alerts
    });

    // GSI1: Sensors by facility (registration records only — sparse)
    this.table.addGlobalSecondaryIndex({
      indexName: 'GSI1',
      partitionKey: { name: 'GSI1PK', type: dynamodb.AttributeType.STRING },
      sortKey: { name: 'GSI1SK', type: dynamodb.AttributeType.STRING },
      projectionType: dynamodb.ProjectionType.ALL,
    });
  }
}
```

**Lambda for threshold alerting:**
```typescript
// Lambda triggered by DynamoDB Streams
export const handler = async (event: DynamoDBStreamEvent) => {
  for (const record of event.Records) {
    if (record.eventName !== 'INSERT') continue;
    
    const newImage = record.dynamodb?.NewImage;
    if (!newImage?.SK?.S?.startsWith('READING#')) continue;
    
    const value = parseFloat(newImage.value?.N ?? '0');
    const THRESHOLD = 80; // configurable per sensor type
    
    if (value > THRESHOLD) {
      // trigger alert: SNS, EventBridge, etc.
      console.log(`ALERT: Sensor ${newImage.sensorId?.S} reading ${value} exceeds threshold`);
    }
  }
};
```

### Rationale

1. **Hourly time buckets** — `SENSOR#sensorId#YYYY-MM-DDTHH` bounds partition size to a predictable maximum (360 readings/hour). Without buckets, a sensor writing for months would accumulate millions of items in one partition, degrading performance. Hourly granularity makes "last hour" queries a single partition hit and "last day" queries 24 sequential or parallel hits.

2. **TTL for 90-day retention** — set `ttl = epoch + 90*86400` at write time. DynamoDB TTL deletes expired items asynchronously at no read/write capacity cost. Items may persist up to 48 hours past TTL — if exact retention is required, add an application-level check.

3. **Streams for threshold alerts** — putting threshold logic in the write path (Streams + Lambda) means you never need to query DynamoDB to detect violations. The stream event delivers the new value immediately after write. Filter in the Lambda by SK prefix to ignore non-reading records.

4. **Sparse GSI1** — reading records (the high-volume items) do NOT write `GSI1PK`/`GSI1SK` attributes. Only the rare sensor registration records do. This keeps GSI1 small and write costs low.

5. **Optional LATEST item** — if "get latest reading" is a hot path (e.g., a dashboard polling every second), maintain a `SENSOR#sensorId` / `LATEST` item updated with each write using `UpdateItem`. This trades 1 extra write per reading for guaranteed O(1) latest-reading lookup without bucket logic in the application.
