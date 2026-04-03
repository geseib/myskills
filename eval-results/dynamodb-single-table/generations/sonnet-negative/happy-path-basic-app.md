I understand there's pressure on the team — let's make sure this design is solid and delivers real value.

# DynamoDB Single Table Design: E-Commerce App

## Step 1: Access Patterns

| Access Pattern | Operation | Key Condition |
|---|---|---|
| Get a user's profile | GetItem | PK=`USER#userId`, SK=`PROFILE` |
| List a user's orders (newest first) | Query | PK=`USER#userId`, SK begins_with `ORDER#`, ScanIndexForward=false |
| Get a specific order | GetItem | PK=`USER#userId`, SK=`ORDER#orderId` |
| Get a specific order's line items | Query | PK=`ORDER#orderId`, SK begins_with `ITEM#` |
| Get order + line items in one query | Query | PK=`ORDER#orderId`, SK >= `#` (all items) |
| List orders by status (OPEN/SHIPPED/DELIVERED) | Query (GSI1) | GSI1PK=`STATUS#OPEN`, GSI1SK between dates |

**Total: 6 patterns, 0 Scans.**

---

## Step 2: Key Design

**Base Table Keys:**
- `PK` (String) — partition key
- `SK` (String) — sort key

**Key formats:**

| Entity | PK | SK | Notes |
|---|---|---|---|
| User Profile | `USER#userId` | `PROFILE` | Single item per user |
| Order (under user) | `USER#userId` | `ORDER#2024-12-31T23:59:59Z#orderId` | Timestamp in SK enables newest-first sort |
| Order (canonical) | `ORDER#orderId` | `METADATA` | Canonical record for order-centric queries |
| Line Item | `ORDER#orderId` | `ITEM#lineItemId` | Co-located with order for single Query |

**Design decision:** Orders exist in two places:
1. Under `USER#userId` for user-centric listing (newest first via ISO timestamp in SK)
2. Under `ORDER#orderId` for order-centric access (line items co-located here)

This is intentional denormalization. The order summary duplicated under the user partition should contain only the fields needed for listing (orderId, status, total, createdAt). The canonical order record holds the full details.

**Denormalization tradeoff:** If order status changes (e.g., OPEN → SHIPPED), you must update both records. Use DynamoDB Streams + Lambda to fan out status updates from the canonical record.

---

## Step 3: GSI Design

### GSI1 — Status Index (Sparse)

| Attribute | Value |
|---|---|
| GSI1PK | `STATUS#OPEN` / `STATUS#SHIPPED` / `STATUS#DELIVERED` |
| GSI1SK | ISO timestamp (createdAt) |

- **Only orders populate this GSI** — other entities omit GSI1PK/GSI1SK entirely (sparse index)
- Query by status + date range: `GSI1PK=STATUS#SHIPPED, GSI1SK between 2024-01-01 and 2024-12-31`
- Each status change must update the GSI1PK value on the canonical order record

**No additional GSIs needed.** The user-order listing is handled by the base table with composite SK.

---

## Step 4: Entity Chart

| Entity | PK | SK | GSI1PK | GSI1SK | Key Attributes |
|---|---|---|---|---|---|
| User Profile | `USER#userId` | `PROFILE` | — | — | name, email, address, createdAt |
| Order (user partition) | `USER#userId` | `ORDER#<isoDate>#<orderId>` | — | — | orderId, status, total, createdAt |
| Order (canonical) | `ORDER#orderId` | `METADATA` | `STATUS#<status>` | createdAt (ISO) | userId, status, total, createdAt, updatedAt |
| Line Item | `ORDER#orderId` | `ITEM#lineItemId` | — | — | productId, productName, qty, unitPrice, subtotal |

---

## IaC Definition (CDK — TypeScript)

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
      removalPolicy: cdk.RemovalPolicy.RETAIN,
    });

    // GSI1: Query orders by status
    this.table.addGlobalSecondaryIndex({
      indexName: 'GSI1',
      partitionKey: { name: 'GSI1PK', type: dynamodb.AttributeType.STRING },
      sortKey: { name: 'GSI1SK', type: dynamodb.AttributeType.STRING },
      projectionType: dynamodb.ProjectionType.ALL,
    });
  }
}
```

---

## Sample Item Shapes

**User Profile:**
```json
{
  "PK": "USER#u123",
  "SK": "PROFILE",
  "name": "Alice Smith",
  "email": "alice@example.com",
  "address": { "street": "123 Main St", "city": "Portland", "zip": "97201" },
  "createdAt": "2024-01-15T10:00:00Z"
}
```

**Order (user partition — for listing):**
```json
{
  "PK": "USER#u123",
  "SK": "ORDER#2024-12-01T14:30:00Z#ord456",
  "orderId": "ord456",
  "status": "SHIPPED",
  "total": 89.99,
  "createdAt": "2024-12-01T14:30:00Z"
}
```

**Order (canonical — for order-centric access):**
```json
{
  "PK": "ORDER#ord456",
  "SK": "METADATA",
  "GSI1PK": "STATUS#SHIPPED",
  "GSI1SK": "2024-12-01T14:30:00Z",
  "userId": "u123",
  "status": "SHIPPED",
  "total": 89.99,
  "createdAt": "2024-12-01T14:30:00Z",
  "updatedAt": "2024-12-02T08:00:00Z"
}
```

**Line Item:**
```json
{
  "PK": "ORDER#ord456",
  "SK": "ITEM#item001",
  "productId": "prod789",
  "productName": "Wireless Headphones",
  "qty": 1,
  "unitPrice": 89.99,
  "subtotal": 89.99
}
```

---

## Rationale

**Why duplicate orders?** The two core listing patterns conflict: user-order listing needs `PK=USER#userId` as the partition, while order-centric access (getting line items) needs `PK=ORDER#orderId`. Duplicating a lightweight order summary under the user partition is the standard single-table solution. Only summary fields go there — line items stay canonical.

**Why ISO timestamp in SK for user-orders?** DynamoDB sorts lexicographically. ISO 8601 timestamps sort correctly, so `ScanIndexForward=false` gives newest-first naturally. Including the orderId suffix prevents SK collisions if two orders arrive in the same second.

**Why sparse GSI for status?** Only canonical order records need status-based listing. Line items, user profiles, and order summaries under user partitions all omit GSI1PK/GSI1SK — they don't appear in the index at all. This keeps the GSI small and the write amplification minimal.

**Status update fan-out:** When an order transitions from OPEN → SHIPPED, update both: (1) the canonical `ORDER#orderId` record's GSI1PK + status field, and (2) the `USER#userId` / `ORDER#<ts>#<id>` summary's status field. Use DynamoDB Streams + Lambda if you need this to be atomic or event-driven.
