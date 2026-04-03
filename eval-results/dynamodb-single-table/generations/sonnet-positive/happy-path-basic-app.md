# DynamoDB Single-Table Design: E-Commerce App

Great timing on this design! Let me work through this systematically.

---

## Step 1: Access Patterns

| # | Access Pattern | Operation | Key Condition |
|---|---|---|---|
| 1 | Get a user's profile | GetItem | PK=`USER#userId`, SK=`PROFILE` |
| 2 | List a user's orders (newest first) | Query | PK=`USER#userId`, SK begins_with `ORDER#`, ScanIndexForward=false |
| 3 | Get a specific order | GetItem | PK=`USER#userId`, SK=`ORDER#orderId` |
| 4 | Get line items for a specific order | Query | PK=`ORDER#orderId`, SK begins_with `ITEM#` |
| 5 | List orders by status (e.g., OPEN) | Query (GSI1) | GSI1PK=`STATUS#OPEN`, GSI1SK=`<date>` (sorted by date) |

---

## Step 2: Key Design

**Base Table:** `PK` (String) + `SK` (String)

Key decisions:
- User profile and order summaries share `PK=USER#userId` — one Query fetches both
- Order detail (with line items) gets its own partition `PK=ORDER#orderId` for unbounded item support
- SK uses reverse-timestamp format for orders so newest-first sort works natively (`ORDER#2024-12-31T23:59:59Z` sorts before `ORDER#2024-01-01T00:00:00Z` when scanning in reverse)
- Status GSI uses sparse indexing — only active/relevant orders populate it (you can omit DELIVERED orders from the GSI if you don't need to query them)

**Note on order line items:** Line items live under `PK=ORDER#orderId` rather than under the user partition. This prevents unbounded growth on `USER#userId` and lets you fetch an order with all its items in a single Query without also pulling every other user record.

---

## Step 2b: Patterns That Don't Fit DynamoDB Natively

- **Full-text search on orders** (e.g., search by product name): Use **OpenSearch** with zero-ETL integration from DynamoDB Streams
- **Analytics** (e.g., revenue by month, top products): Use **Redshift** or **OpenSearch** for aggregations

---

## Step 3: GSI Design

**GSI1** — Status index for orders
- `GSI1PK` = `STATUS#<status>` (e.g., `STATUS#OPEN`, `STATUS#SHIPPED`, `STATUS#DELIVERED`)
- `GSI1SK` = ISO timestamp of order creation (enables sorted listing by date)
- **Sparse**: only items with `GSI1PK` populated appear in this index — omit from items that don't need it

This one GSI handles all four status queries. No need for a separate GSI per status value.

---

## Step 4: Design Output

### Entity Chart

| Entity | PK | SK | GSI1PK | GSI1SK | Key Attributes |
|---|---|---|---|---|---|
| User Profile | `USER#userId` | `PROFILE` | — | — | name, email, address |
| Order Summary | `USER#userId` | `ORDER#<isoTimestamp>#<orderId>` | `STATUS#<status>` | `<isoTimestamp>` | orderId, status, total, createdAt |
| Order Detail | `ORDER#orderId` | `META` | — | — | userId, status, total, createdAt |
| Line Item | `ORDER#orderId` | `ITEM#<lineItemId>` | — | — | productId, name, qty, price |

**Why two order records?**
- `USER#userId` / `ORDER#<timestamp>#<orderId>` = order summary card, lives with the user for listing
- `ORDER#orderId` / `META` + `ITEM#...` = order detail + line items, queried when viewing a specific order

This duplicates a small amount of order metadata (status, total) — acceptable tradeoff since these fields don't change frequently after fulfillment. If status updates are frequent, do an extra GetItem on the detail record instead of duplicating.

### Access Pattern Resolution

| # | Access Pattern | How |
|---|---|---|
| 1 | Get user profile | `GetItem(PK=USER#u1, SK=PROFILE)` |
| 2 | List user's orders (newest first) | `Query(PK=USER#u1, SK begins_with ORDER#, ScanIndexForward=false)` |
| 3 | Get specific order with line items | `Query(PK=ORDER#o1, SK begins_with #)` — returns META + all ITEMs |
| 4 | List orders by status | `Query(GSI1, GSI1PK=STATUS#OPEN, ScanIndexForward=false)` |

### IaC Definition (CDK — TypeScript)

```typescript
import * as cdk from 'aws-cdk-lib';
import * as dynamodb from 'aws-cdk-lib/aws-dynamodb';
import { Construct } from 'constructs';

export class EcommerceTable extends Construct {
  public readonly table: dynamodb.Table;

  constructor(scope: Construct, id: string) {
    super(scope, id);

    this.table = new dynamodb.Table(this, 'EcommerceTable', {
      tableName: 'ecommerce',
      partitionKey: { name: 'PK', type: dynamodb.AttributeType.STRING },
      sortKey: { name: 'SK', type: dynamodb.AttributeType.STRING },
      billingMode: dynamodb.BillingMode.PAY_PER_REQUEST,
      timeToLiveAttribute: 'ttl',
      pointInTimeRecovery: true,
      deletionProtection: true,
    });

    // GSI1: Status-based order queries
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

1. **Co-location of profile + order list under `USER#userId`** — listing a user's orders requires no GSI; a single Query with `begins_with ORDER#` returns everything sorted newest-first by embedding the ISO timestamp in the SK.

2. **Separate partition for order detail** — putting line items under `ORDER#orderId` avoids polluting the user partition with unbounded items. The tradeoff is a second Query when viewing order detail, but this is the standard pattern.

3. **One GSI overloaded for all statuses** — rather than a separate GSI per status, `GSI1PK=STATUS#<value>` is a sparse index. Items that have been archived can be removed from the index by unsetting `GSI1PK`.

4. **Timestamp in SK for orders** — ISO 8601 sorts lexicographically, so `ScanIndexForward=false` gives you newest-first naturally. Include the orderId suffix to ensure uniqueness when two orders are created at the same millisecond.

5. **Duplicated order summary fields** — `status` and `total` appear in both the user partition (for listing) and the order partition (for detail). Since these rarely change after creation, the consistency risk is low. If you need strict consistency, fetch from `ORDER#orderId` only and accept the extra read.
