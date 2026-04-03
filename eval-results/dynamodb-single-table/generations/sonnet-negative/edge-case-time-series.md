IoT time-series data has specific pitfalls in DynamoDB — unbounded partition growth being the biggest one. Let's address this carefully.

# DynamoDB Single Table Design: IoT Sensor Platform

## Step 1: Access Patterns

| Access Pattern | Operation | Key Condition |
|---|---|---|
| Get the latest reading for a sensor | GetItem or Query (limit 1, desc) | PK=`SENSOR#sensorId#<currentBucket>`, SK=`READING#<isoTimestamp>`, ScanIndexForward=false |
| Query readings for a sensor in last hour | Query | PK=`SENSOR#sensorId#<currentBucket>`, SK between `READING#<1hr ago>` and `READING#<now>` |
| Query readings for a sensor in last day | Query (multiple buckets) | Query PK=`SENSOR#sensorId#<bucket>` for each relevant bucket |
| List all sensors in a facility | Query (GSI1) | GSI1PK=`FACILITY#facilityId`, GSI1SK begins_with `SENSOR#` |
| Alert on readings above threshold | DynamoDB Streams + Lambda | — (triggered on write, not a read pattern) |
| Auto-delete readings older than 90 days | TTL | DynamoDB native TTL attribute |

**Total: 5 read patterns + 1 stream-triggered pattern + TTL. 0 Scans.**

---

## Step 2: Key Design

**The critical problem with naive time-series design:**

If you use `PK=SENSOR#sensorId` with `SK=READING#<timestamp>`, a sensor reporting every 10 seconds accumulates:
- 6 readings/minute × 60 minutes × 24 hours = **8,640 readings/day**
- Over 90 days before TTL cleanup: **~777,600 items per partition**

DynamoDB doesn't limit partition size in terms of item count, but an unbounded, single-key hot partition concentrates all reads and writes to one physical partition. At 6 writes/minute per sensor × thousands of sensors, you'll exhaust the per-partition write throughput (1,000 WCUs/sec) on popular sensors.

**Solution: Time-bucketed PKs**

Bucket readings by time period. Monthly buckets are a good default for 10-second cadence data:

| Entity | PK | SK | Notes |
|---|---|---|---|
| Sensor Reading | `SENSOR#sensorId#2024-12` | `READING#2024-12-01T14:30:00Z` | Bucket = YYYY-MM |
| Sensor Metadata | `SENSOR#sensorId` | `METADATA` | Profile, facility, thresholds |
| Facility Sensor Ref | `FACILITY#facilityId` | `SENSOR#sensorId` | For listing sensors in a facility |

**Bucket selection:** Monthly buckets for 10-second cadence means ~259,200 items/bucket (30 days × 8,640/day). This is manageable. If you have extremely write-heavy sensors, consider weekly or daily buckets.

**"Last hour" query:** Always within one bucket (monthly). Single Query.

**"Last day" query:** Usually within one bucket. At month boundaries, spans two buckets — query both and merge results in application code. This is a known tradeoff of the bucket pattern, and it's acceptable.

**"Latest reading" query:** Query the current bucket with `ScanIndexForward=false, Limit=1`. Simple and fast.

---

## Step 2b: Patterns That Don't Fit DynamoDB

**Alert on readings above threshold:** This is NOT a DynamoDB read pattern. You should not poll DynamoDB to check thresholds — that would require either a Scan or a read on every write path. The correct approach:

- **DynamoDB Streams + Lambda:** Configure a Stream on the table. Every new reading item triggers a Lambda. The Lambda checks if the value exceeds the threshold for that sensor and fires the alert if so.
- The Lambda can read the threshold from the `SENSOR#sensorId / METADATA` item or from a configuration cache (ElastiCache/Parameter Store) to avoid extra DynamoDB reads per event.

This is the right architecture. Don't force this into a DynamoDB query pattern.

**Cross-facility analytics** (e.g., average temperature across all facilities): This is an aggregation — not a DynamoDB pattern. Push to:
- **OpenSearch Serverless** via zero-ETL integration from DynamoDB Streams
- **Timestream** — specifically designed for IoT time-series with built-in aggregation functions
- **Kinesis Data Streams** → **S3** → **Athena** for ad-hoc analysis

---

## Step 3: GSI Design

### GSI1 — Facility Sensor Listing (Sparse)

| Entity | GSI1PK | GSI1SK | Purpose |
|---|---|---|---|
| Facility Sensor Ref | `FACILITY#facilityId` | `SENSOR#sensorId` | List all sensors in a facility |

- Only facility-sensor relationship items populate GSI1
- Sensor metadata and readings omit GSI1PK/GSI1SK entirely
- This is a sparse index — very small, very cheap

**One GSI total.** The bucket design handles time-series queries on the base table.

---

## Step 4: Entity Chart

| Entity | PK | SK | GSI1PK | GSI1SK | TTL | Key Attributes |
|---|---|---|---|---|---|---|
| Sensor Metadata | `SENSOR#sensorId` | `METADATA` | — | — | No | facilityId, name, type, alertThreshold, installDate |
| Facility-Sensor Ref | `FACILITY#facilityId` | `SENSOR#sensorId` | `FACILITY#facilityId` | `SENSOR#sensorId` | No | sensorId, name, type |
| Sensor Reading | `SENSOR#sensorId#<YYYY-MM>` | `READING#<ISO8601 timestamp>` | — | — | Yes (90 days) | value, unit, sensorId, timestamp |

**TTL calculation for readings:**
```python
import time
ttl = int(time.time()) + (90 * 24 * 60 * 60)  # 90 days from now
```

---

## IaC Definition (CDK — TypeScript)

```typescript
import * as cdk from 'aws-cdk-lib';
import * as dynamodb from 'aws-cdk-lib/aws-dynamodb';
import * as lambda from 'aws-cdk-lib/aws-lambda';
import * as eventsources from 'aws-cdk-lib/aws-lambda-event-sources';
import { Construct } from 'constructs';

export class IotSensorTable extends Construct {
  public readonly table: dynamodb.Table;

  constructor(scope: Construct, id: string, alertLambda: lambda.Function) {
    super(scope, id);

    this.table = new dynamodb.Table(this, 'IotSensorTable', {
      tableName: 'iot-sensors',
      partitionKey: { name: 'PK', type: dynamodb.AttributeType.STRING },
      sortKey: { name: 'SK', type: dynamodb.AttributeType.STRING },
      billingMode: dynamodb.BillingMode.PAY_PER_REQUEST,
      timeToLiveAttribute: 'ttl',
      pointInTimeRecovery: true,
      deletionProtection: true,
      // Enable Streams for alert processing
      stream: dynamodb.StreamViewType.NEW_IMAGE,
      removalPolicy: cdk.RemovalPolicy.RETAIN,
    });

    // GSI1: List sensors in a facility
    this.table.addGlobalSecondaryIndex({
      indexName: 'GSI1',
      partitionKey: { name: 'GSI1PK', type: dynamodb.AttributeType.STRING },
      sortKey: { name: 'GSI1SK', type: dynamodb.AttributeType.STRING },
      projectionType: dynamodb.ProjectionType.ALL,
    });

    // Wire DynamoDB Streams to alert Lambda
    alertLambda.addEventSource(new eventsources.DynamoEventSource(this.table, {
      startingPosition: lambda.StartingPosition.LATEST,
      batchSize: 100,
      // Filter: only process new READING items
      filters: [
        lambda.FilterCriteria.filter({
          eventName: lambda.FilterRule.isEqual('INSERT'),
          dynamodb: {
            NewImage: {
              SK: { S: lambda.FilterRule.beginsWith('READING#') }
            }
          }
        })
      ]
    }));
  }
}
```

---

## Sample Item Shapes

**Sensor Metadata:**
```json
{
  "PK": "SENSOR#sensor42",
  "SK": "METADATA",
  "facilityId": "facility-north",
  "name": "HVAC Zone A - Temp",
  "type": "TEMPERATURE",
  "alertThreshold": 85.0,
  "unit": "fahrenheit",
  "installDate": "2024-01-15"
}
```

**Facility-Sensor Ref:**
```json
{
  "PK": "FACILITY#facility-north",
  "SK": "SENSOR#sensor42",
  "GSI1PK": "FACILITY#facility-north",
  "GSI1SK": "SENSOR#sensor42",
  "sensorId": "sensor42",
  "name": "HVAC Zone A - Temp",
  "type": "TEMPERATURE"
}
```

**Sensor Reading (with TTL):**
```json
{
  "PK": "SENSOR#sensor42#2024-12",
  "SK": "READING#2024-12-01T14:30:00Z",
  "sensorId": "sensor42",
  "value": 72.5,
  "unit": "fahrenheit",
  "timestamp": "2024-12-01T14:30:00Z",
  "ttl": 1717027200
}
```

---

## Query Examples

**Latest reading for sensor42:**
```python
result = table.query(
    KeyConditionExpression=Key('PK').eq('SENSOR#sensor42#2024-12'),
    ScanIndexForward=False,
    Limit=1
)
latest = result['Items'][0] if result['Items'] else None
```

**Last hour of readings for sensor42:**
```python
from datetime import datetime, timedelta, timezone

now = datetime.now(timezone.utc)
one_hour_ago = now - timedelta(hours=1)
bucket = now.strftime('%Y-%m')

result = table.query(
    KeyConditionExpression=Key('PK').eq(f'SENSOR#sensor42#{bucket}') &
                           Key('SK').between(
                               f'READING#{one_hour_ago.isoformat()}',
                               f'READING#{now.isoformat()}'
                           )
)
```

**Last day of readings (handling month boundary):**
```python
from datetime import datetime, timedelta, timezone

now = datetime.now(timezone.utc)
one_day_ago = now - timedelta(days=1)

buckets_needed = set()
buckets_needed.add(now.strftime('%Y-%m'))
buckets_needed.add(one_day_ago.strftime('%Y-%m'))

all_readings = []
for bucket in buckets_needed:
    result = table.query(
        KeyConditionExpression=Key('PK').eq(f'SENSOR#sensor42#{bucket}') &
                               Key('SK').between(
                                   f'READING#{one_day_ago.isoformat()}',
                                   f'READING#{now.isoformat()}'
                               )
    )
    all_readings.extend(result['Items'])

all_readings.sort(key=lambda x: x['SK'])
```

**List all sensors in facility-north:**
```python
table.query(
    IndexName='GSI1',
    KeyConditionExpression=Key('GSI1PK').eq('FACILITY#facility-north') &
                           Key('GSI1SK').begins_with('SENSOR#')
)
```

---

## Alert Lambda (Streams Handler)

```python
def handler(event, context):
    for record in event['Records']:
        if record['eventName'] != 'INSERT':
            continue
        
        new_image = record['dynamodb']['NewImage']
        
        # Only process readings
        if not new_image.get('SK', {}).get('S', '').startswith('READING#'):
            continue
        
        sensor_id = new_image['sensorId']['S']
        value = float(new_image['value']['N'])
        
        # Get sensor threshold (cache this — don't read DynamoDB per event)
        threshold = get_threshold_from_cache(sensor_id)
        
        if value > threshold:
            send_alert(sensor_id, value, threshold)
```

---

## Rationale

**Why monthly buckets?** A 10-second cadence generates ~259,200 items per sensor per month. Monthly buckets prevent unbounded partition growth while keeping "last hour" queries to a single partition. Weekly or daily buckets would be safer at higher cardinality but add more complexity to the cross-bucket query logic.

**Why not use a SENSOR#sensorId#LATEST item for the latest reading?** You could maintain a denormalized "latest reading" item updated on every write. This is a valid optimization for extremely frequent "latest reading" queries, but it adds write amplification (every reading triggers a second write). For most IoT use cases, querying the current bucket with `Limit=1, ScanIndexForward=false` is fast enough and simpler.

**Why DynamoDB Streams for alerts?** Threshold alerting is a write-path concern, not a read-path concern. Triggering from a Stream is idiomatic AWS — it decouples the write path from alert processing, scales independently, and avoids the need to poll or scan. The Lambda filter ensures only `READING#` inserts trigger the alert handler, not metadata updates or facility-sensor refs.

**Why TTL instead of explicit cleanup?** 90 days × 8,640 readings/day = ~777,600 items per sensor to eventually delete. Explicit cleanup would require querying and batch-deleting items, adding operational complexity. TTL handles this automatically and asynchronously — DynamoDB deletes expired items for free, typically within 48 hours of expiration. For strict 90-day compliance (e.g., regulatory), supplement TTL with a scheduled Lambda that explicitly deletes items past the threshold (since TTL can lag by up to 48 hours).
