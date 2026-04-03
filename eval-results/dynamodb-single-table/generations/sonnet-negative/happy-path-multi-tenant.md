Let's get this right. A clean, production-grade design will make a real difference here.

# DynamoDB Single Table Design: Multi-Tenant Project Management SaaS

## Step 1: Access Patterns

| Access Pattern | Operation | Key Condition |
|---|---|---|
| Get user by ID | GetItem | PK=`USER#userId`, SK=`PROFILE` |
| List all users in an org | Query (GSI1) | GSI1PK=`ORG#orgId#USERS`, GSI1SK begins_with `USER#` |
| List all projects in an org | Query | PK=`ORG#orgId`, SK begins_with `PROJECT#` |
| List tasks in a project | Query | PK=`PROJECT#projectId`, SK begins_with `TASK#` |
| List tasks in a project by status | Query (GSI1) | GSI1PK=`PROJECT#projectId#STATUS#TODO`, GSI1SK begins_with `TASK#` |
| List tasks assigned to a user across all projects | Query (GSI2) | GSI2PK=`USER#userId#TASKS`, GSI2SK begins_with `TASK#` |
| Get a single task by ID | GetItem | PK=`PROJECT#projectId`, SK=`TASK#taskId` |

**Total: 7 patterns, 0 Scans.**

---

## Step 2: Key Design

**Base Table Keys:**
- `PK` (String) — partition key
- `SK` (String) — sort key

**Tenant isolation:** Every entity is scoped to an org. User IDs and project IDs should be globally unique (UUIDs) to prevent cross-tenant collisions, even when used as PK without the org prefix.

**Key formats:**

| Entity | PK | SK | Notes |
|---|---|---|---|
| Organization | `ORG#orgId` | `METADATA` | Org profile (name, plan, etc.) |
| Project | `ORG#orgId` | `PROJECT#projectId` | Projects co-located under org |
| User Profile | `USER#userId` | `PROFILE` | Global user record |
| Task | `PROJECT#projectId` | `TASK#taskId` | Tasks co-located under project |

**Design rationale:**
- Projects live under `ORG#orgId` so "list all projects for an org" is a single Query on the base table
- Tasks live under `PROJECT#projectId` so "list all tasks in a project" is a single Query on the base table
- Users have a top-level partition for profile lookups by ID
- GSIs handle cross-partition queries (users in an org, tasks assigned to a user)

---

## Step 2b: Patterns That Don't Fit DynamoDB

**All listed patterns fit cleanly in DynamoDB.** No full-text search or aggregations required here.

If you later add:
- **Search by task title/description** → OpenSearch (zero-ETL integration from DynamoDB Streams)
- **Dashboard analytics** (tasks completed per sprint, velocity charts) → Redshift or OpenSearch Serverless

---

## Step 3: GSI Design

### GSI1 — Org-User Membership + Project-Task-Status (Overloaded)

| Entity | GSI1PK | GSI1SK | Purpose |
|---|---|---|---|
| User (org membership) | `ORG#orgId#USERS` | `USER#userId` | List all users in an org |
| Task (by status) | `PROJECT#projectId#STATUS#<status>` | `TASK#taskId` | List tasks in a project by status |

- Overloading: two entity types share GSI1 with different prefix patterns — no collision possible
- User membership records (`PK=USER#userId, SK=ORG#orgId`) populate GSI1 for the org-user listing
- Task records populate GSI1 only when a status filter is needed (all tasks populate it regardless)
- **Sparse usage:** Org records, project records, and other entities omit GSI1PK/GSI1SK

### GSI2 — User Task Assignment (Cross-Project)

| Entity | GSI2PK | GSI2SK | Purpose |
|---|---|---|---|
| Task (assigned to user) | `USER#assigneeId#TASKS` | `TASK#taskId` | List tasks assigned to a user |

- Only tasks with an assignee populate GSI2
- Unassigned tasks omit GSI2PK/GSI2SK (sparse index — smaller, cheaper)

**Two GSIs total.** Write amplification: tasks write to both GSI1 and GSI2 (if assigned). All other entities write to at most one GSI.

---

## Step 4: Entity Chart

| Entity | PK | SK | GSI1PK | GSI1SK | GSI2PK | GSI2SK | Key Attributes |
|---|---|---|---|---|---|---|---|
| Organization | `ORG#orgId` | `METADATA` | — | — | — | — | name, plan, createdAt |
| Project | `ORG#orgId` | `PROJECT#projectId` | — | — | — | — | projectId, name, ownerId, createdAt |
| User Profile | `USER#userId` | `PROFILE` | — | — | — | — | name, email, orgId, createdAt |
| User Org Membership | `USER#userId` | `ORG#orgId` | `ORG#orgId#USERS` | `USER#userId` | — | — | role, joinedAt |
| Task | `PROJECT#projectId` | `TASK#taskId` | `PROJECT#projectId#STATUS#<status>` | `TASK#taskId` | `USER#assigneeId#TASKS` (if assigned) | `TASK#taskId` | title, status, assigneeId, dueDate, createdAt |

---

## IaC Definition (CDK — TypeScript)

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
      removalPolicy: cdk.RemovalPolicy.RETAIN,
    });

    // GSI1: Org-user membership + project-task-status (overloaded)
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

---

## Sample Item Shapes

**Organization:**
```json
{
  "PK": "ORG#org001",
  "SK": "METADATA",
  "name": "Acme Corp",
  "plan": "ENTERPRISE",
  "createdAt": "2024-01-01T00:00:00Z"
}
```

**User Profile:**
```json
{
  "PK": "USER#user42",
  "SK": "PROFILE",
  "name": "Jane Doe",
  "email": "jane@acme.com",
  "createdAt": "2024-02-01T00:00:00Z"
}
```

**User Org Membership (enables "list users in org" via GSI1):**
```json
{
  "PK": "USER#user42",
  "SK": "ORG#org001",
  "GSI1PK": "ORG#org001#USERS",
  "GSI1SK": "USER#user42",
  "role": "MEMBER",
  "joinedAt": "2024-02-01T00:00:00Z"
}
```

**Project:**
```json
{
  "PK": "ORG#org001",
  "SK": "PROJECT#proj99",
  "projectId": "proj99",
  "name": "Website Redesign",
  "ownerId": "user42",
  "createdAt": "2024-03-01T00:00:00Z"
}
```

**Task:**
```json
{
  "PK": "PROJECT#proj99",
  "SK": "TASK#task101",
  "GSI1PK": "PROJECT#proj99#STATUS#IN_PROGRESS",
  "GSI1SK": "TASK#task101",
  "GSI2PK": "USER#user42#TASKS",
  "GSI2SK": "TASK#task101",
  "title": "Design mockups",
  "status": "IN_PROGRESS",
  "assigneeId": "user42",
  "dueDate": "2024-04-30",
  "createdAt": "2024-03-15T00:00:00Z"
}
```

---

## Rationale

**Why a separate User Org Membership item?** The user profile (`USER#userId / PROFILE`) enables fast lookup by ID, but "list all users in an org" needs to query from the org's perspective. A separate membership item (`USER#userId / ORG#orgId`) populates GSI1 with the org as the partition key. This is the adjacency list pattern — the membership item also naturally supports "list all orgs a user belongs to" by querying `PK=USER#userId, SK begins_with ORG#` on the base table.

**Why overload GSI1?** Two different query shapes use GSI1: org-user listing and project-task-by-status. Their GSI1PK values have different prefixes (`ORG#...#USERS` vs `PROJECT#...#STATUS#...`), so they never collide. This avoids the anti-pattern of creating one GSI per access pattern.

**Status update on tasks:** When a task's status changes from `IN_PROGRESS` to `DONE`, the GSI1PK value must be updated from `PROJECT#proj99#STATUS#IN_PROGRESS` to `PROJECT#proj99#STATUS#DONE`. DynamoDB doesn't update GSI keys automatically — your application must write the new value. This is a delete-then-put at the item level (UpdateItem with the new GSI1PK attribute value).

**Tenant isolation guarantee:** All data is scoped. Projects are only retrievable via `ORG#orgId` partition. Tasks are only retrievable via `PROJECT#projectId`. User org membership items gate org-level user listing. Your application layer should verify that the requesting user's orgId matches the queried orgId before executing any query.
