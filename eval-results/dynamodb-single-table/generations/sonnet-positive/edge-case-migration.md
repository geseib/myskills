# DynamoDB Single-Table Design: PostgreSQL Migration

Migrating from relational to DynamoDB requires a mindset shift. Let me design this properly rather than mapping tables 1:1.

---

## Step 1: Access Patterns

Start with the queries, not the tables.

| # | Access Pattern | Operation | Key Condition |
|---|---|---|---|
| 1 | Get user by email | Query (GSI1) | GSI1PK=`EMAIL#user@example.com` |
| 2 | List users in an org | Query | PK=`ORG#orgId`, SK begins_with `USER#` |
| 3 | Get invoice with all line items | Query | PK=`INVOICE#invoiceId`, SK begins_with `#` (META + all ITEMs) |
| 4 | List invoices for an org by date | Query | PK=`ORG#orgId`, SK begins_with `INVOICE#` (with ISO date in SK) |
| 5 | List unpaid invoices across all orgs (admin) | Query (GSI2) | GSI2PK=`STATUS#UNPAID`, GSI2SK=`<date>` |

**Pattern 5 analysis:** "Across all orgs" is the dangerous phrase. This is essentially a global query. In SQL it's `WHERE status = 'unpaid'`. In DynamoDB, a Scan is not acceptable. The answer is a sparse GSI on status — only unpaid invoices appear in it.

---

## Step 2: Key Design

**Base Table:** `PK` (String) + `SK` (String)

### The SQL → DynamoDB Translation

| SQL Table | DynamoDB Equivalent |
|---|---|
| `users` + `organizations` JOIN | Co-located under `ORG#orgId` PK |
| `invoices` | Own partition `INVOICE#invoiceId` for detail; summary ref under `ORG#orgId` |
| `invoice_line_items` | Items under `INVOICE#invoiceId` partition |
| `users.email` unique index | Sparse GSI1 on email |
| `WHERE status = 'unpaid'` | Sparse GSI2 on status |

**Key decisions:**
- **Org partition** (`PK=ORG#orgId`) holds user membership records and invoice summary references — patterns 2 and 4 with no GSI
- **Invoice partition** (`PK=INVOICE#invoiceId`) holds the canonical invoice + all line items — pattern 3 is a single Query
- **Email GSI** is sparse — only the canonical user record (`PK=USER#userId`, `SK=PROFILE`) populates it
- **Status GSI** is sparse — only UNPAID invoices populate it; when paid, the attribute is removed (or the GSI key is unset)

**No JOINs in DynamoDB** — if you previously JOINed `invoices` to `organizations`, now:
- Invoice records store `orgId` as an attribute (denormalization)
- The org-invoice relationship is maintained by writing an invoice summary under `ORG#orgId` at invoice creation time

---

## Step 2b: Patterns That Don't Fit DynamoDB

- **Ad-hoc admin queries** (e.g., "show me all invoices between $1000-$5000 across all orgs"): These require Scan or multi-condition filters. Route to **OpenSearch** or **Redshift** via zero-ETL. DynamoDB is not a reporting database.
- **Cross-org analytics** (revenue by plan tier, churn analysis): Use **Redshift** — these are OLAP queries.
- **Search by partial email** (autocomplete): Use **OpenSearch** — DynamoDB requires exact match on GSI keys.

---

## Step 3: GSI Design

**GSI1** — User lookup by email
- `GSI1PK` = `EMAIL#<email>` (e.g., `EMAIL#alice@example.com`)
- `GSI1SK` = `USER#userId`
- **Sparse**: only user profile records populate this; no other entities have email
- Handles pattern 1: get user by email (login, password reset, invite lookup)

**GSI2** — Unpaid invoices across all orgs (admin view)
- `GSI2PK` = `STATUS#UNPAID`
- `GSI2SK` = `<isoDate>` (invoice creation date, for sorted listing)
- **Sparse**: only invoices with `status=UNPAID` write these attributes
- When an invoice is paid: `UpdateItem` to remove `GSI2PK` and `GSI2SK` attributes — the item falls out of the index automatically

Two GSIs. All five access patterns covered.

---

## Step 4: Design Output

### Entity Chart

| Entity | PK | SK | GSI1PK | GSI1SK | GSI2PK | GSI2SK | Key Attributes |
|---|---|---|---|---|---|---|---|
| User profile | `USER#userId` | `PROFILE` | `EMAIL#<email>` | `USER#userId` | — | — | name, email, orgId, role |
| Org-User membership | `ORG#orgId` | `USER#userId` | — | — | — | — | name, email, role, joinedAt |
| Org metadata | `ORG#orgId` | `META` | — | — | — | — | name, plan, createdAt |
| Org-Invoice ref | `ORG#orgId` | `INVOICE#<isoDate>#<invoiceId>` | — | — | — | — | amount, status, createdAt |
| Invoice detail | `INVOICE#invoiceId` | `META` | — | — | `STATUS#UNPAID` (if unpaid) | `<isoDate>` (if unpaid) | orgId, amount, status, createdAt |
| Line item | `INVOICE#invoiceId` | `ITEM#<lineItemId>` | — | — | — | — | description, amount |

### Access Pattern Resolution

| # | Access Pattern | How |
|---|---|---|
| 1 | Get user by email | `Query(GSI1, GSI1PK=EMAIL#alice@example.com)` → returns userId, then `GetItem(PK=USER#u1, SK=PROFILE)` if full profile needed |
| 2 | List users in an org | `Query(PK=ORG#o1, SK begins_with USER#)` |
| 3 | Get invoice with all line items | `Query(PK=INVOICE#i1, SK >= #)` — returns META + all ITEM# records |
| 4 | List invoices for an org by date | `Query(PK=ORG#o1, SK begins_with INVOICE#, ScanIndexForward=false)` |
| 5 | List unpaid invoices (admin) | `Query(GSI2, GSI2PK=STATUS#UNPAID, ScanIndexForward=false)` |

### IaC Definition (CDK — TypeScript)

```typescript
import * as cdk from 'aws-cdk-lib';
import * as dynamodb from 'aws-cdk-lib/aws-dynamodb';
import { Construct } from 'constructs';

export class BillingTable extends Construct {
  public readonly table: dynamodb.Table;

  constructor(scope: Construct, id: string) {
    super(scope, id);

    this.table = new dynamodb.Table(this, 'BillingTable', {
      tableName: 'billing',
      partitionKey: { name: 'PK', type: dynamodb.AttributeType.STRING },
      sortKey: { name: 'SK', type: dynamodb.AttributeType.STRING },
      billingMode: dynamodb.BillingMode.PAY_PER_REQUEST,
      timeToLiveAttribute: 'ttl',
      pointInTimeRecovery: true,
      deletionProtection: true,
    });

    // GSI1: User lookup by email
    this.table.addGlobalSecondaryIndex({
      indexName: 'GSI1',
      partitionKey: { name: 'GSI1PK', type: dynamodb.AttributeType.STRING },
      sortKey: { name: 'GSI1SK', type: dynamodb.AttributeType.STRING },
      projectionType: dynamodb.ProjectionType.ALL,
    });

    // GSI2: Unpaid invoices (admin view)
    this.table.addGlobalSecondaryIndex({
      indexName: 'GSI2',
      partitionKey: { name: 'GSI2PK', type: dynamodb.AttributeType.STRING },
      sortKey: { name: 'GSI2SK', type: dynamodb.AttributeType.STRING },
      projectionType: dynamodb.ProjectionType.ALL,
    });
  }
}
```

### Migration Strategy

**Run in parallel, don't cut over blindly:**

1. **Dual-write phase**: Write all new records to both PostgreSQL and DynamoDB. Reads still come from PostgreSQL.
2. **Backfill**: Use a migration script to write historical data to DynamoDB (batch by org to avoid hot writes).
3. **Read validation**: For a sample of requests, read from both systems and compare results.
4. **Cutover**: Switch reads to DynamoDB one access pattern at a time (start with the simplest: get user by ID).
5. **PostgreSQL deprecation**: Keep PostgreSQL as backup for 30 days, then decommission.

**Completeness checklist before cutover:**
- [ ] Every access pattern in Step 1 is covered
- [ ] No Scans in production code paths
- [ ] Dual-write tested under production load
- [ ] Read validation shows 100% result parity
- [ ] TTL configured if any data has retention requirements

### Rationale

1. **Collapsed 4 SQL tables into 1 DynamoDB table** — `users`, `organizations`, `invoices`, and `invoice_line_items` become a single table. Entities that were JOINed in SQL are now co-located under the same PK.

2. **Invoice line items moved under invoice PK** — `invoice_line_items` was a separate SQL table joined by `invoice_id`. In DynamoDB, line items live at `PK=INVOICE#invoiceId, SK=ITEM#<id>` — a single Query returns both the invoice header and all line items.

3. **Sparse GSI for status** — the admin "unpaid invoices" query is a classic SQL `WHERE status = 'unpaid'` pattern. In DynamoDB, we use a sparse GSI where only unpaid invoices write the GSI key attributes. When paid, remove the attributes via UpdateItem — the item exits the index automatically. No Scan, no filter-heavy Query.

4. **Denormalized org references** — invoice records store `orgId` directly. This replaces the SQL foreign key + JOIN. The consistency tradeoff: if an org's name changes, you don't need to update invoices (they reference by ID, not name). If you need org name on invoice views, either do a second GetItem or denormalize the name and update via Streams.

5. **No ad-hoc queries** — the biggest mindset shift from PostgreSQL. Every query must be planned. The 5 access patterns here cover the stated requirements. Any new query not covered by base table or these GSIs will require adding a new GSI or routing to a secondary store (OpenSearch/Redshift).
