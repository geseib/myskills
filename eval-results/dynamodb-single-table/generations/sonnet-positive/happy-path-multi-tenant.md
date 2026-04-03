# DynamoDB Single-Table Design: Multi-Tenant Project Management SaaS

Let me work through this carefully — multi-tenant SaaS with cross-entity queries is a great fit for single-table design.

---

## Step 1: Access Patterns

| # | Access Pattern | Operation | Key Condition |
|---|---|---|---|
| 1 | Get user profile by ID | GetItem | PK=`USER#userId`, SK=`PROFILE` |
| 2 | List all users in an org | Query | PK=`ORG#orgId`, SK begins_with `USER#` |
| 3 | List all projects in an org | Query | PK=`ORG#orgId`, SK begins_with `PROJECT#` |
| 4 | List tasks in a project (all statuses) | Query | PK=`PROJECT#projectId`, SK begins_with `TASK#` |
| 5 | List tasks in a project by status | Query (GSI1) | GSI1PK=`PROJECT#projectId#STATUS#<status>`, GSI1SK=`TASK#taskId` |
| 6 | List tasks assigned to a user (all projects) | Query (GSI2) | GSI2PK=`USER#userId`, GSI2SK begins_with `TASK#` |
| 7 | Get a single task by ID | GetItem | PK=`TASK#taskId`, SK=`META` |

---

## Step 2: Key Design

**Base Table:** `PK` (String) + `SK` (String)

Key decisions:
- **Org partition** (`PK=ORG#orgId`) holds membership references for both users and projects, enabling patterns 2 and 3 with `begins_with` on different SK prefixes
- **User partition** (`PK=USER#userId`) holds the canonical profile — pattern 1 is a direct GetItem
- **Project partition** (`PK=PROJECT#projectId`) holds tasks — pattern 4 is a Query with `begins_with TASK#`
- **Task partition** (`PK=TASK#taskId`, `SK=META`) allows direct GetItem lookup for pattern 7 without knowing the project

**Critical tradeoff — two task records:**
- A task summary lives in the project partition (`PK=PROJECT#projectId`) for listing
- A task canonical record lives in `PK=TASK#taskId` for direct lookup
- `title`, `status`, `assigneeId` are duplicated — update both when they change (or use DynamoDB Streams + Lambda to fan out)

---

## Step 2b: Patterns That Don't Fit DynamoDB

- **Search tasks by title/description**: Use **OpenSearch** with zero-ETL from Streams — DynamoDB cannot do full-text search
- **Cross-org analytics** (e.g., "all overdue tasks across all orgs for admin"): Use **Redshift** or **OpenSearch** — Scan is not acceptable
- **Task count aggregations per project**: Pre-compute via Streams + Lambda counter, or use **OpenSearch**

---

## Step 3: GSI Design

**GSI1** — Task filtering by project + status
- `GSI1PK` = `PROJECT#projectId#STATUS#<status>` (e.g., `PROJECT#p1#STATUS#IN_PROGRESS`)
- `GSI1SK` = `TASK#taskId`
- **Sparse**: only task-in-project items populate this; user/org items don't
- Handles pattern 5 — filter tasks in a project by status without scanning all tasks

**GSI2** — Tasks assigned to a user (cross-project)
- `GSI2PK` = `USER#userId`
- `GSI2SK` = `TASK#taskId`
- **Sparse**: only task assignments populate this index
- Handles pattern 6 — list all tasks assigned to a user across all projects

Two GSIs is lean. The status filtering (GSI1) uses a compound PK so the same index works for any project + any status combination without additional indexes.

---

## Step 4: Design Output

### Entity Chart

| Entity | PK | SK | GSI1PK | GSI1SK | GSI2PK | GSI2SK | Key Attributes |
|---|---|---|---|---|---|---|---|
| User Profile | `USER#userId` | `PROFILE` | — | — | — | — | name, email, orgId, role |
| Org-User Membership | `ORG#orgId` | `USER#userId` | — | — | — | — | name, email, role |
| Org-Project Link | `ORG#orgId` | `PROJECT#projectId` | — | — | — | — | name, status, createdAt |
| Task (in project) | `PROJECT#projectId` | `TASK#taskId` | `PROJECT#projectId#STATUS#<status>` | `TASK#taskId` | `USER#assigneeId` | `TASK#taskId` | title, status, assigneeId, dueDate |
| Task (canonical) | `TASK#taskId` | `META` | — | — | — | — | projectId, orgId, title, status, assigneeId, dueDate |

### Access Pattern Resolution

| # | Access Pattern | How |
|---|---|---|
| 1 | Get user profile by ID | `GetItem(PK=USER#u1, SK=PROFILE)` |
| 2 | List all users in an org | `Query(PK=ORG#o1, SK begins_with USER#)` |
| 3 | List all projects in an org | `Query(PK=ORG#o1, SK begins_with PROJECT#)` |
| 4 | List tasks in a project (all) | `Query(PK=PROJECT#p1, SK begins_with TASK#)` |
| 5 | List tasks in a project by status | `Query(GSI1, GSI1PK=PROJECT#p1#STATUS#IN_PROGRESS)` |
| 6 | List tasks assigned to a user | `Query(GSI2, GSI2PK=USER#u1, GSI2SK begins_with TASK#)` |
| 7 | Get single task by ID | `GetItem(PK=TASK#t1, SK=META)` |

### IaC Definition (CDK — TypeScript)

```typescript
import * as cdk from 'aws-cdk-lib';
import * as dynamodb from 'aws-cdk-lib/aws-dynamodb';
import { Construct } from 'constructs';

export class ProjectManagementTable extends Construct {
  public readonly table: dynamodb.Table;

  constructor(scope: Construct, id: string) {
    super(scope, id);

    this.table = new dynamodb.Table(this, 'ProjectManagementTable', {
      tableName: 'project-management',
      partitionKey: { name: 'PK', type: dynamodb.AttributeType.STRING },
      sortKey: { name: 'SK', type: dynamodb.AttributeType.STRING },
      billingMode: dynamodb.BillingMode.PAY_PER_REQUEST,
      timeToLiveAttribute: 'ttl',
      pointInTimeRecovery: true,
      deletionProtection: true,
    });

    // GSI1: Tasks by project + status
    this.table.addGlobalSecondaryIndex({
      indexName: 'GSI1',
      partitionKey: { name: 'GSI1PK', type: dynamodb.AttributeType.STRING },
      sortKey: { name: 'GSI1SK', type: dynamodb.AttributeType.STRING },
      projectionType: dynamodb.ProjectionType.ALL,
    });

    // GSI2: Tasks assigned to a user (cross-project)
    this.table.addGlobalSecondaryIndex({
      indexName: 'GSI2',
      partitionKey: { name: 'GSI2PK', type: dynamodb.AttributeType.STRING },
      sortKey: { name: 'GSI2SK', type: dynamodb.AttributeType.STRING },
      projectionType: dynamodb.ProjectionType.ALL,
    });
  }
}
```

### Rationale

1. **Org partition as membership index** — both users and projects are "listed under" the org via `PK=ORG#orgId` with different SK prefixes. This avoids a GSI for these common list queries.

2. **Task appears in multiple places** — the task-in-project record (`PK=PROJECT#projectId`) supports listing; the canonical record (`PK=TASK#taskId`) supports direct lookup. Duplication is intentional. If `status` or `assigneeId` changes frequently, wire DynamoDB Streams → Lambda to keep both in sync.

3. **GSI1 compound PK for status filtering** — `PROJECT#p1#STATUS#IN_PROGRESS` as the GSI PK means the index is automatically partitioned by project+status. Querying a specific project's TODO tasks hits exactly the right partition. Changing a task's status requires removing the old GSI key and writing the new one (standard for status indexes).

4. **GSI2 for cross-project user assignment** — assigning a task to a user writes `GSI2PK=USER#userId`. A single Query on GSI2 returns all tasks for that user across any project, with no knowledge of which projects they're in.

5. **Tenant isolation** — every entity includes `orgId` as an attribute. Your application layer enforces that users only Query their own org's PK. Consider adding a condition expression on writes to ensure data integrity.
