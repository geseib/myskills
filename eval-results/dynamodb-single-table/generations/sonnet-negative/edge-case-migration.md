PostgreSQL-to-DynamoDB migrations require a mindset shift — stop thinking in tables and joins, start thinking in access patterns. Let's work through this systematically.

# DynamoDB Migration Design: PostgreSQL → Single Table

## Step 1: Access Patterns

Map every SQL query to a DynamoDB operation. **No SQL tables → DynamoDB tables. Think access patterns.**

| Access Pattern | SQL Equivalent | DynamoDB Operation | Key Condition |
|---|---|---|---|
| Get user by email | `SELECT * FROM users WHERE email = ?` | Query (GSI1) | GSI1PK=`EMAIL#email` |
| Get user by ID | `SELECT * FROM users WHERE id = ?` | GetItem | PK=`USER#userId`, SK=`PROFILE` |
| List users in an org | `SELECT * FROM users WHERE org_id = ?` | Query (GSI1) | GSI1PK=`ORG#orgId#USERS`, GSI1SK begins_with `USER#` |
| Get invoice with all line items | `SELECT ... JOIN invoice_line_items` | Query | PK=`INVOICE#invoiceId`, SK >= `#` (all items) |
| List invoices for an org by date | `SELECT * FROM invoices WHERE org_id = ? ORDER BY created_at DESC` | Query (GSI2) | GSI2PK=`ORG#orgId#INVOICES`, GSI2SK between dates |
| List unpaid invoices across all orgs (admin) | `SELECT * FROM invoices WHERE status = 'unpaid'` | Query (GSI2) | GSI2PK=`STATUS#UNPAID`, GSI2SK between dates |

**Total: 6 patterns, 0 Scans.**

---

## Step 2: Key Design

**Migration principle:** Don't create one DynamoDB "table" per SQL table. Collapse related entities into co-located items in a single DynamoDB table. Every JOIN in SQL becomes either:
1. **Co-location** — same PK (query retrieves both in one request)
2. **GSI** — different starting point for the query

**Key formats:**

| Entity | PK | SK | Notes |
|---|---|---|---|
| Organization | `ORG#orgId` | `METADATA` | Collapses `organizations` SQL table |
| User Profile | `USER#userId` | `PROFILE` | Collapses `users` SQL table |
| User Org Membership | `USER#userId` | `ORG#orgId` | Enables org-scoped user listing |
| Invoice | `INVOICE#invoiceId` | `METADATA` | Collapses `invoices` SQL table |
| Invoice Line Item | `INVOICE#invoiceId` | `ITEM#lineItemId` | Collapses `invoice_line_items` — co-located! |

**The JOIN elimination:** In SQL, getting an invoice with its line items requires `JOIN invoice_line_items ON invoices.id = invoice_line_items.invoice_id`. In DynamoDB, both the invoice metadata and its line items share `PK=INVOICE#invoiceId`. A single Query with `SK >= "#"` retrieves the invoice and all line items in one request. The JOIN is gone.

---

## Step 2b: Patterns That Don't Fit DynamoDB

**"List unpaid invoices across all orgs (admin view)"** — this is the hardest pattern. It requires querying across all org partitions. The options:

**Option A: GSI with status as partition key (recommended for small to medium scale)**
- `GSI2PK=STATUS#UNPAID, GSI2SK=createdAt`
- Sparse index — only invoices with status=UNPAID populate this
- When an invoice is paid, remove GSI2PK/GSI2SK attributes (status changes make it disappear from the index)
- **Risk:** If you have millions of unpaid invoices, this becomes a hot partition. For admin views that are infrequent and can tolerate pagination, it's acceptable.

**Option B: OpenSearch (recommended for large scale)**
- Use DynamoDB Streams + Lambda → OpenSearch for admin reporting and cross-org queries
- Keeps DynamoDB optimized for per-org transactional access; OpenSearch handles admin aggregations
- This is the clean separation of concerns: DynamoDB for OLTP, OpenSearch for OLAP

**My recommendation:** Start with Option A (sparse GSI). If unpaid invoice volume grows large or admin query patterns become more complex (filtering, sorting, aggregations), add OpenSearch as a read model.

---

## Step 3: GSI Design

### GSI1 — User Lookup Index (Overloaded)

| Entity | GSI1PK | GSI1SK | Purpose |
|---|---|---|---|
| User (email lookup) | `EMAIL#email` | `USER#userId` | Get user by email |
| User Org Membership | `ORG#orgId#USERS` | `USER#userId` | List all users in an org |

- Overloaded: two different entity types share GSI1 with different prefix patterns
- User profile items populate GSI1 with `GSI1PK=EMAIL#email` for email lookup
- User org membership items populate GSI1 with `GSI1PK=ORG#orgId#USERS` for org-user listing
- No collision possible — different PK prefix formats

### GSI2 — Invoice Listing Index (Overloaded)

| Entity | GSI2PK | GSI2SK | Purpose |
|---|---|---|---|
| Invoice (by org) | `ORG#orgId#INVOICES` | `<ISO date>#<invoiceId>` | List invoices for an org by date |
| Invoice (by status — admin) | `STATUS#UNPAID` | `<ISO date>#<invoiceId>` | List unpaid invoices across all orgs |

- Overloaded: same GSI serves both per-org and admin-wide invoice listing
- Invoice records populate both GSI2 attributes simultaneously
- When invoice status changes: update `GSI2PK` from `STATUS#UNPAID` to remove it from the admin index (or change to `STATUS#PAID`); this can be done by removing the attribute entirely if paid status items shouldn't appear in any status index

**Two GSIs total.** Covers all 6 access patterns.

---

## Step 4: Entity Chart

| Entity | PK | SK | GSI1PK | GSI1SK | GSI2PK | GSI2SK | Key Attributes |
|---|---|---|---|---|---|---|---|
| Organization | `ORG#orgId` | `METADATA` | — | — | — | — | name, plan |
| User Profile | `USER#userId` | `PROFILE` | `EMAIL#email` | `USER#userId` | — | — | name, email, orgId |
| User Org Membership | `USER#userId` | `ORG#orgId` | `ORG#orgId#USERS` | `USER#userId` | — | — | role |
| Invoice | `INVOICE#invoiceId` | `METADATA` | — | — | `ORG#orgId#INVOICES` | `<ISO date>#<invoiceId>` | orgId, amount, status, createdAt |
| Invoice (if unpaid) | (same item) | (same item) | — | — | also sets: `STATUS#UNPAID` | (same as above) | (status attribute drives this) |
| Invoice Line Item | `INVOICE#invoiceId` | `ITEM#lineItemId` | — | — | — | — | description, amount |

**Note on invoice GSI2PK:** An invoice item can only have one GSI2PK value. The design above uses a single GSI2PK per invoice. To support both "list by org" AND "list unpaid globally," we need to choose:

**Recommended approach:** Use GSI2 for org-invoice listing (`GSI2PK=ORG#orgId#INVOICES`). Use a **separate sparse index (GSI3)** for admin unpaid listing (`GSI3PK=STATUS#UNPAID`). But wait — we want to stay at max 2-3 GSIs.

**Better approach:** Overload GSI2 differently. Each invoice writes TWO items:
1. Invoice metadata: `PK=INVOICE#invoiceId, SK=METADATA` (canonical record, no GSI2)
2. Invoice org ref: `PK=ORG#orgId, SK=INVOICE#<isoDate>#<invoiceId>` (enables org listing on base table!)

This eliminates the need for GSI2 for org-invoice listing entirely. Then GSI2 can be dedicated to the admin unpaid pattern.

**Revised approach:**

| Entity | PK | SK | GSI1PK | GSI1SK | GSI2PK | GSI2SK | Key Attributes |
|---|---|---|---|---|---|---|---|
| Organization | `ORG#orgId` | `METADATA` | — | — | — | — | name, plan |
| User Profile | `USER#userId` | `PROFILE` | `EMAIL#email` | `USER#userId` | — | — | name, email, orgId |
| User Org Membership | `USER#userId` | `ORG#orgId` | `ORG#orgId#USERS` | `USER#userId` | — | — | role |
| Invoice (org ref) | `ORG#orgId` | `INVOICE#<isoDate>#<invoiceId>` | — | — | — | — | invoiceId, amount, status, createdAt |
| Invoice (canonical) | `INVOICE#invoiceId` | `METADATA` | — | — | `STATUS#UNPAID` (if unpaid) | `<isoDate>#<invoiceId>` | orgId, amount, status, createdAt |
| Invoice Line Item | `INVOICE#invoiceId` | `ITEM#lineItemId` | — | — | — | — | description, amount |

This gives:
- **Org invoice listing by date:** Query base table `PK=ORG#orgId, SK begins_with INVOICE#`
- **Invoice + line items:** Query `PK=INVOICE#invoiceId, SK >= #`
- **Admin unpaid invoices:** Query GSI2 `GSI2PK=STATUS#UNPAID, GSI2SK between dates`
- **Get user by email:** Query GSI1 `GSI1PK=EMAIL#email`
- **List users in org:** Query GSI1 `GSI1PK=ORG#orgId#USERS`

---

## IaC Definition (CDK — TypeScript)

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
      removalPolicy: cdk.RemovalPolicy.RETAIN,
    });

    // GSI1: User by email + users in org (overloaded)
    this.table.addGlobalSecondaryIndex({
      indexName: 'GSI1',
      partitionKey: { name: 'GSI1PK', type: dynamodb.AttributeType.STRING },
      sortKey: { name: 'GSI1SK', type: dynamodb.AttributeType.STRING },
      projectionType: dynamodb.ProjectionType.ALL,
    });

    // GSI2: Unpaid invoices (admin view — sparse)
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

## Migration Strategy

**Do NOT do a big-bang cutover.** Run DynamoDB in parallel:

1. **Dual-write phase:** Write to both PostgreSQL and DynamoDB. Read from PostgreSQL. Verify DynamoDB data integrity.
2. **Shadow-read phase:** Read from both. Compare results. Fix discrepancies.
3. **Read cutover:** Flip reads to DynamoDB by access pattern (start with the simplest — GetItem by ID).
4. **Write cutover:** Remove PostgreSQL writes for each access pattern as confidence builds.
5. **PostgreSQL decommission:** Once all patterns are covered and validated.

**What changes in your application code:**
- No more `JOIN` queries — fetching invoice + line items is now a single `Query` call
- No more `WHERE status = ?` with a Scan — admin views must use the GSI
- Email login must go through GSI1 (not a direct column lookup)
- Every ad-hoc query you run against PostgreSQL today must have a planned access pattern in DynamoDB

**What you gain:**
- Predictable O(1) or O(log n) performance at any scale — no query planner surprises
- Pay-per-request billing — no capacity planning
- Sub-10ms P99 latency for all designed access patterns

**What you lose:**
- Ad-hoc queries (you must plan all access patterns upfront)
- Complex aggregations (push to OpenSearch or Redshift)
- Flexible filtering (filter expressions help but consume read capacity — push filtering into key design)

---

## Rationale

**Why not map SQL tables 1:1?** If you create a DynamoDB table per SQL table and use GSIs to replicate foreign key joins, you end up with the worst of both worlds — DynamoDB's write costs with SQL's query patterns. The power of single-table design comes from co-locating related entities so joins become single Queries.

**Why collapse invoice_line_items into the invoice partition?** Line items are never queried independently of their invoice. "Get invoice with line items" is a single Query. "Get all line items ever" is not a real access pattern. Co-locating them eliminates a join, reduces read cost, and simplifies application code.

**Why a sparse GSI for unpaid invoices?** When an invoice is paid, remove the `GSI2PK` and `GSI2SK` attributes (or set them to a different value). The invoice disappears from the unpaid index. This keeps the GSI small — only the genuinely unpaid invoices appear. No cleanup needed for historical paid invoices.
