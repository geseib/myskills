# DynamoDB Single-Table Design: Scheduling App (Doctors ↔ Patients)

Many-to-many relationships with time-sorted queries — this is the adjacency list pattern. Let me work through it.

---

## Step 1: Access Patterns

| # | Access Pattern | Operation | Key Condition |
|---|---|---|---|
| 1 | List all patients for a doctor | Query | PK=`DOCTOR#doctorId`, SK begins_with `PATIENT#` |
| 2 | List all doctors for a patient | Query | PK=`PATIENT#patientId`, SK begins_with `DOCTOR#` |
| 3 | Get appointment details | GetItem | PK=`APPT#apptId`, SK=`META` |
| 4 | List upcoming appointments by date | Query (GSI1) | GSI1PK=`APPTS`, GSI1SK >= `<today's date>` |

---

## Step 2: Key Design

**Base Table:** `PK` (String) + `SK` (String)

The doctor-patient relationship is many-to-many: a doctor sees many patients, a patient sees many doctors. The standard DynamoDB approach is an **adjacency list**:

- A doctor-patient relationship record under the doctor's partition: `PK=DOCTOR#doctorId`, `SK=PATIENT#patientId`
- A doctor-patient relationship record under the patient's partition: `PK=PATIENT#patientId`, `SK=DOCTOR#doctorId`

Both records are written together (use a TransactWriteItems to keep them consistent). Querying from either side is then a simple `begins_with` Query with no GSI needed.

**Appointment records** live in their own partition (`PK=APPT#apptId`) for direct O(1) lookup. The appointment is also referenced in the doctor and patient partitions for listing.

**Upcoming appointments by date** requires a GSI because the base table partitions by entity ID, not by date. We'll use a sparse GSI with a date-based SK.

---

## Step 2b: Patterns That Don't Fit DynamoDB

- **Available time slots for a doctor** (find open slots): This is a range query over what's *not* booked — DynamoDB doesn't support "gaps" queries. Compute available slots in application code by querying booked appointments and subtracting.
- **Cross-doctor scheduling search** (e.g., "find any available cardiologist tomorrow"): Use **OpenSearch** or application-side logic with pre-computed availability records. DynamoDB cannot efficiently search across all doctors' schedules simultaneously.

---

## Step 3: GSI Design

**GSI1** — Upcoming appointments by date
- `GSI1PK` = `APPTS` (a fixed value — this is intentionally a low-cardinality PK for a bounded result set)
- `GSI1SK` = ISO 8601 datetime of the appointment (e.g., `2024-12-15T09:00:00Z`)
- **Sparse**: only appointment META records populate this GSI
- Query: `GSI1PK=APPTS, GSI1SK >= <today>` with a filter or limit for pagination

**Hot partition warning:** `GSI1PK=APPTS` puts all appointments in one GSI partition. If appointment volume is very high (thousands per hour), this becomes a hot partition. Mitigations:
- Add a shard suffix: `APPTS#0` through `APPTS#9` and query all shards in parallel
- Use a date-bucketed PK: `APPTS#2024-12` and query the current + next month buckets

For most scheduling apps the shard approach is overkill — start with `APPTS` and monitor.

**Inverted index via dual writes (no GSI needed):**
- Doctor → patients: base table `PK=DOCTOR#doctorId, SK=PATIENT#patientId`
- Patient → doctors: base table `PK=PATIENT#patientId, SK=DOCTOR#doctorId`

Both directions are served by base table Queries. The inverted relationship is maintained via application-level dual writes (or TransactWriteItems).

---

## Step 4: Design Output

### Entity Chart

| Entity | PK | SK | GSI1PK | GSI1SK | Key Attributes |
|---|---|---|---|---|---|
| Doctor profile | `DOCTOR#doctorId` | `PROFILE` | — | — | name, specialty, phone |
| Patient profile | `PATIENT#patientId` | `PROFILE` | — | — | name, dob, phone |
| Doctor→Patient link | `DOCTOR#doctorId` | `PATIENT#patientId` | — | — | firstApptDate, apptCount |
| Patient→Doctor link | `PATIENT#patientId` | `DOCTOR#doctorId` | — | — | firstApptDate |
| Appointment | `APPT#apptId` | `META` | `APPTS` | `<isoDatetime>` | doctorId, patientId, datetime, duration, status, notes |
| Doctor's appointment ref | `DOCTOR#doctorId` | `APPT#<isoDatetime>#<apptId>` | — | — | patientId, status |
| Patient's appointment ref | `PATIENT#patientId` | `APPT#<isoDatetime>#<apptId>` | — | — | doctorId, status |

**Why appointment refs in doctor/patient partitions?**
To list a doctor's or patient's upcoming appointments without a GSI, store appointment references under their partition with the datetime in the SK. This gives sorted-by-date appointment listing per person for free.

### Access Pattern Resolution

| # | Access Pattern | How |
|---|---|---|
| 1 | List all patients for a doctor | `Query(PK=DOCTOR#d1, SK begins_with PATIENT#)` |
| 2 | List all doctors for a patient | `Query(PK=PATIENT#p1, SK begins_with DOCTOR#)` |
| 3 | Get appointment details | `GetItem(PK=APPT#a1, SK=META)` |
| 4 | List upcoming appointments (all) by date | `Query(GSI1, GSI1PK=APPTS, GSI1SK >= <today>, ScanIndexForward=true)` |
| Bonus | List a doctor's upcoming appointments | `Query(PK=DOCTOR#d1, SK >= APPT#<today>, begins_with=APPT#)` |
| Bonus | List a patient's upcoming appointments | `Query(PK=PATIENT#p1, SK >= APPT#<today>, begins_with=APPT#)` |

### IaC Definition (CDK — TypeScript)

```typescript
import * as cdk from 'aws-cdk-lib';
import * as dynamodb from 'aws-cdk-lib/aws-dynamodb';
import { Construct } from 'constructs';

export class SchedulingTable extends Construct {
  public readonly table: dynamodb.Table;

  constructor(scope: Construct, id: string) {
    super(scope, id);

    this.table = new dynamodb.Table(this, 'SchedulingTable', {
      tableName: 'scheduling',
      partitionKey: { name: 'PK', type: dynamodb.AttributeType.STRING },
      sortKey: { name: 'SK', type: dynamodb.AttributeType.STRING },
      billingMode: dynamodb.BillingMode.PAY_PER_REQUEST,
      timeToLiveAttribute: 'ttl',
      pointInTimeRecovery: true,
      deletionProtection: true,
    });

    // GSI1: All upcoming appointments sorted by date
    this.table.addGlobalSecondaryIndex({
      indexName: 'GSI1',
      partitionKey: { name: 'GSI1PK', type: dynamodb.AttributeType.STRING },
      sortKey: { name: 'GSI1SK', type: dynamodb.AttributeType.STRING },
      projectionType: dynamodb.ProjectionType.ALL,
    });
  }
}
```

### Rationale

1. **Adjacency list for many-to-many** — the doctor-patient relationship is stored twice: once under the doctor's partition and once under the patient's partition. This is intentional duplication. Both Queries are O(patients) and O(doctors) respectively, with no GSI. Use TransactWriteItems to write both records atomically.

2. **Appointment canonical record** — the appointment detail lives at `PK=APPT#apptId` for direct lookup. References (with datetime in SK) live under doctor and patient partitions for per-person sorted listing.

3. **GSI1 for cross-entity date sorting** — listing upcoming appointments globally requires a GSI because the base table partitions by entity. The `APPTS` fixed PK puts all appointments in one GSI partition. Monitor throughput and add sharding if needed.

4. **ISO 8601 in SK for natural sort** — datetime strings in ISO format sort lexicographically in chronological order. Using `between` or `>=` conditions on ISO datetime SKs gives you date-range queries without any numeric conversion.

5. **Write amplification** — creating one appointment writes 4 records: the canonical `APPT#` record, the doctor's appointment ref, the patient's appointment ref, and potentially the doctor-patient link if first appointment. This is expected in DynamoDB single-table design. Use TransactWriteItems (max 25 items per transaction) to keep writes atomic.
