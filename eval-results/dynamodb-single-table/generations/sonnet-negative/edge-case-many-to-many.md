Many-to-many relationships are one of the most important patterns to get right in DynamoDB. This uses the adjacency list pattern with an inverted GSI — the standard approach.

# DynamoDB Single Table Design: Doctor-Patient Scheduling

## Step 1: Access Patterns

| Access Pattern | Operation | Key Condition |
|---|---|---|
| List all patients for a doctor | Query (GSI1) | GSI1PK=`DOCTOR#doctorId`, GSI1SK begins_with `PATIENT#` |
| List all doctors for a patient | Query | PK=`PATIENT#patientId`, SK begins_with `DOCTOR#` |
| Get appointment details | GetItem | PK=`APPOINTMENT#appointmentId`, SK=`METADATA` |
| List upcoming appointments by date | Query (GSI1) | GSI1PK=`APPOINTMENTS`, GSI1SK between `<today>` and `<future>` |
| Get appointments for a doctor by date | Query (GSI2) | GSI2PK=`DOCTOR#doctorId`, GSI2SK between `<date>#` and `<date>#~` |
| Get appointments for a patient by date | Query (GSI2) | GSI2PK=`PATIENT#patientId`, GSI2SK between `<date>#` and `<date>#~` |

**Total: 6 patterns, 0 Scans.**

---

## Step 2: Key Design

**Base Table Keys:**
- `PK` (String) — partition key
- `SK` (String) — sort key

**The many-to-many challenge:** A doctor sees many patients; a patient sees many doctors. Neither direction can be the "primary" relationship without making the other direction impossible without a Scan. The solution is the **adjacency list pattern**:

- Store the relationship from both directions
- Use an inverted GSI to query from either direction

**Key formats:**

| Entity | PK | SK | Notes |
|---|---|---|---|
| Doctor Profile | `DOCTOR#doctorId` | `PROFILE` | Doctor metadata |
| Patient Profile | `PATIENT#patientId` | `PROFILE` | Patient metadata |
| Relationship (patient→doctor) | `PATIENT#patientId` | `DOCTOR#doctorId` | "This patient sees this doctor" |
| Relationship (doctor→patient via GSI) | `PATIENT#patientId` | `DOCTOR#doctorId` | Same item; GSI inverts direction |
| Appointment | `APPOINTMENT#appointmentId` | `METADATA` | Full appointment details |
| Appointment ref (under doctor) | `DOCTOR#doctorId` | `APPT#<isoDate>#appointmentId` | For doctor schedule queries |
| Appointment ref (under patient) | `PATIENT#patientId` | `APPT#<isoDate>#appointmentId` | For patient schedule queries |

**Note on appointment references:** Similar to the e-commerce pattern, appointments exist canonically at `APPOINTMENT#appointmentId` and as lightweight references under doctor and patient partitions. This enables both per-doctor and per-patient schedule queries without duplicating full appointment details.

---

## Step 2b: Patterns That Don't Fit DynamoDB

**"List upcoming appointments by date" across all doctors:** This pattern (a global calendar view) is problematic if it means "all appointments in the system in the next 7 days." Using a single `APPOINTMENTS` partition key for this would create a hot partition at scale. For a small system (hundreds of appointments/day) it's workable. For larger systems:

- **Recommendation:** Use a date-bucketed PK: `APPT_DATE#2024-12-01` → query for a specific day without hot partition risk.
- Alternatively, push to an **OpenSearch** or **Redshift** index for admin scheduling views.

I'll design the base case with the date-bucket approach since it's safer.

---

## Step 3: GSI Design

### GSI1 — Inverted Relationship Index (Doctor→Patient)

The relationship item `PK=PATIENT#patientId, SK=DOCTOR#doctorId` naturally answers "list all doctors for a patient." To query in the other direction (list all patients for a doctor), invert the keys:

| Entity | GSI1PK | GSI1SK | Purpose |
|---|---|---|---|
| Relationship | `DOCTOR#doctorId` | `PATIENT#patientId` | List all patients for a doctor |

- GSI1PK = SK of the base item (`DOCTOR#doctorId`)
- GSI1SK = PK of the base item (`PATIENT#patientId`)
- This is the classic **inverted index** pattern

Only relationship items populate GSI1. Doctor profiles, patient profiles, and appointments omit GSI1PK/GSI1SK.

### GSI2 — Appointment by Date (for schedule queries)

| Entity | GSI2PK | GSI2SK | Purpose |
|---|---|---|---|
| Appointment ref (doctor) | `DOCTOR#doctorId` | `<isoDate>#<appointmentId>` | Doctor's schedule by date |
| Appointment ref (patient) | `PATIENT#patientId` | `<isoDate>#<appointmentId>` | Patient's upcoming appointments |
| Appointment (date-bucket) | `APPT_DATE#<YYYY-MM-DD>` | `<isoTime>#<appointmentId>` | Global calendar view for a day |

- Overloaded: doctor, patient, and date-bucket appointment refs all share GSI2
- Prefixes prevent collisions: `DOCTOR#...`, `PATIENT#...`, `APPT_DATE#...`

**Two GSIs total.** This covers all access patterns cleanly.

---

## Step 4: Entity Chart

| Entity | PK | SK | GSI1PK | GSI1SK | GSI2PK | GSI2SK | Key Attributes |
|---|---|---|---|---|---|---|---|
| Doctor Profile | `DOCTOR#doctorId` | `PROFILE` | — | — | — | — | name, specialty, phone |
| Patient Profile | `PATIENT#patientId` | `PROFILE` | — | — | — | — | name, dob, phone |
| Relationship | `PATIENT#patientId` | `DOCTOR#doctorId` | `DOCTOR#doctorId` | `PATIENT#patientId` | — | — | since, primaryCare |
| Appointment (canonical) | `APPOINTMENT#appointmentId` | `METADATA` | — | — | `APPT_DATE#<YYYY-MM-DD>` | `<HH:MM>#<appointmentId>` | doctorId, patientId, datetime, duration, type, notes, status |
| Appt Ref (under doctor) | `DOCTOR#doctorId` | `APPT#<isoDatetime>#<appointmentId>` | — | — | `DOCTOR#doctorId` | `<isoDate>#<appointmentId>` | appointmentId, patientId, datetime, type, status |
| Appt Ref (under patient) | `PATIENT#patientId` | `APPT#<isoDatetime>#<appointmentId>` | — | — | `PATIENT#patientId` | `<isoDate>#<appointmentId>` | appointmentId, doctorId, datetime, type, status |

---

## IaC Definition (CDK — TypeScript)

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
      removalPolicy: cdk.RemovalPolicy.RETAIN,
    });

    // GSI1: Inverted relationship index — list patients for a doctor
    this.table.addGlobalSecondaryIndex({
      indexName: 'GSI1',
      partitionKey: { name: 'GSI1PK', type: dynamodb.AttributeType.STRING },
      sortKey: { name: 'GSI1SK', type: dynamodb.AttributeType.STRING },
      projectionType: dynamodb.ProjectionType.ALL,
    });

    // GSI2: Appointment schedule by date (overloaded for doctor, patient, global)
    this.table.addGlobalSecondaryIndex({
      indexName: 'GSI2',
      partitionKey: { name: 'GSI2PK', type: dynamodb.AttributeType.STRING },
      sortKey: { name: 'GSI2SK', type: dynamodb.AttributeType.STRING },
      projectionType: dynamodb.ProjectionType.ALL,
    });
  }
}
```

---

## Sample Item Shapes

**Relationship (patient→doctor, bidirectional via GSI1):**
```json
{
  "PK": "PATIENT#pat001",
  "SK": "DOCTOR#doc007",
  "GSI1PK": "DOCTOR#doc007",
  "GSI1SK": "PATIENT#pat001",
  "since": "2023-06-01",
  "primaryCare": true
}
```

**Appointment (canonical):**
```json
{
  "PK": "APPOINTMENT#appt555",
  "SK": "METADATA",
  "GSI2PK": "APPT_DATE#2024-12-15",
  "GSI2SK": "09:30#appt555",
  "doctorId": "doc007",
  "patientId": "pat001",
  "datetime": "2024-12-15T09:30:00Z",
  "durationMinutes": 30,
  "type": "FOLLOW_UP",
  "status": "CONFIRMED",
  "notes": "Review lab results"
}
```

**Appointment ref under doctor:**
```json
{
  "PK": "DOCTOR#doc007",
  "SK": "APPT#2024-12-15T09:30:00Z#appt555",
  "GSI2PK": "DOCTOR#doc007",
  "GSI2SK": "2024-12-15#appt555",
  "appointmentId": "appt555",
  "patientId": "pat001",
  "datetime": "2024-12-15T09:30:00Z",
  "type": "FOLLOW_UP",
  "status": "CONFIRMED"
}
```

---

## Query Examples

**List all patients for Dr. doc007:**
```python
table.query(
    IndexName='GSI1',
    KeyConditionExpression=Key('GSI1PK').eq('DOCTOR#doc007') & 
                           Key('GSI1SK').begins_with('PATIENT#')
)
```

**List all doctors for patient pat001:**
```python
table.query(
    KeyConditionExpression=Key('PK').eq('PATIENT#pat001') & 
                           Key('SK').begins_with('DOCTOR#')
)
```

**Dr. doc007's schedule for December 2024:**
```python
table.query(
    IndexName='GSI2',
    KeyConditionExpression=Key('GSI2PK').eq('DOCTOR#doc007') & 
                           Key('GSI2SK').between('2024-12', '2024-12~')
)
```

**All appointments on 2024-12-15 (global calendar view):**
```python
table.query(
    IndexName='GSI2',
    KeyConditionExpression=Key('GSI2PK').eq('APPT_DATE#2024-12-15') & 
                           Key('GSI2SK').begins_with('')
)
```

---

## Rationale

**Why adjacency list instead of two separate relationship tables?** A single relationship item (`PATIENT#patientId / DOCTOR#doctorId`) represents the relationship from the patient's perspective. The GSI inverts the keys to serve the doctor's perspective. You get both directions from one item — half the write cost of maintaining two separate relationship items.

**Why duplicate appointment refs under doctor and patient partitions?** The canonical appointment record serves appointment detail lookups. But "list upcoming appointments for Dr. X" needs a Query that starts from the doctor's perspective — it can't start from `APPOINTMENT#appointmentId` without a Scan. The appointment ref under `DOCTOR#doctorId` solves this at the cost of one extra write and some duplication. Only denormalize fields needed for the list view (status, datetime, type) — fetch the full appointment separately when needed.

**Denormalization warning:** If an appointment is rescheduled or canceled, you must update three records: the canonical appointment, the ref under the doctor, and the ref under the patient. Use DynamoDB Streams + Lambda to fan out status/datetime changes from the canonical record to keep refs in sync.
