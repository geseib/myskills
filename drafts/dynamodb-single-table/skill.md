<!-- skill-version: v2 -->
# DynamoDB Single Table Design

Design DynamoDB tables using single table design patterns that are efficient, simple, and eliminate the need for multiple tables or database types.

## When to use

TRIGGER when:
- Designing a new DynamoDB table or data model
- Adding entities or access patterns to an existing DynamoDB table
- Reviewing or refactoring a DynamoDB schema
- Building a serverless application that needs a database
- The user asks about DynamoDB modeling, key design, or GSI strategy

DO NOT TRIGGER when:
- Working with relational databases (RDS, Aurora, etc.)
- The user explicitly wants a multi-table DynamoDB design
- Working with non-AWS databases

## Design methodology

Always follow this order. Never skip step 1.

### Step 1: Define access patterns FIRST

Before touching key design, list every read and write operation the application needs. Format each as:

```
Access Pattern                          | Operation | Key Condition
----------------------------------------|-----------|-----------------------------
Get user profile                        | GetItem   | PK=USER#<id>, SK=PROFILE
List orders for user                    | Query     | PK=USER#<id>, SK begins_with ORDER#
Get order by ID                         | Query     | GSI1: GSI1PK=ORDER#<id>, GSI1SK=ORDER#<id>
List open orders by date                | Query     | GSI1: GSI1PK=STATUS#OPEN, GSI1SK=<date>
```

Every access pattern must map to a GetItem, Query (not Scan). If a pattern requires Scan, redesign the keys.

### Step 2: Design the key schema

**Base table keys:** Always use generic names `PK` (String) and `SK` (String).

**Key value format:** Prefix every key value with an entity type and `#` delimiter:
```
PK = USER#alice          SK = PROFILE
PK = USER#alice          SK = ORDER#2024-03-15#ord-001
PK = ORG#acme            SK = MEMBER#alice
PK = GAME#1234           SK = PLAYER#marco
PK = GAME#1234           SK = STATE
```

**Rules:**
- `#` is the standard delimiter — it sorts predictably and is URI-safe
- PK must be high-cardinality to distribute load across partitions
- SK enables range queries — structure it for `begins_with`, `between`, and comparison operators
- Co-locate related items under the same PK so a single Query can fetch them together
- Composite sort keys encode hierarchy: `SK = DEPT#engineering#TEAM#backend#EMP#alice`

### Step 2b: Identify patterns that DON'T belong in DynamoDB

Before designing GSIs, group related access patterns and flag any that are a poor fit for DynamoDB:

**Patterns that need complementary services:**
- **Full-text search** (substring, fuzzy, faceted) → OpenSearch (use zero-ETL integration)
- **Aggregations** (trending, top-N, analytics) → OpenSearch or Redshift (use zero-ETL)
- **Fan-out feeds** (social feeds, activity streams) → consider fan-out-on-write with Streams, or cache with ElastiCache
- **Caching hot reads** (leaderboards, session data) → ElastiCache/DAX

**Always state explicitly** which patterns you're handling in DynamoDB vs which need other services. Don't force everything into one table.

### Step 3: Design GSIs (only as needed)

**Naming:** Use generic names: `GSI1PK`/`GSI1SK`, `GSI2PK`/`GSI2SK`

**GSI overloading:** Different entity types populate the same GSI attributes with different values:
```
Entity: User     → GSI1PK = EMAIL#alice@co.com    GSI1SK = USER#alice
Entity: Order    → GSI1PK = STATUS#OPEN           GSI1SK = 2024-03-15
```
Items that don't need a GSI simply omit those attributes (sparse index — they won't appear in the GSI).

**Target 2-3 GSIs maximum.** Each GSI doubles write cost for items that populate it. If you need more than 3, reconsider your key design.

**Common GSI patterns:**
- **Inverted index:** GSI1PK=SK, GSI1SK=PK — query relationships from either direction
- **Sparse index:** Only items with a specific attribute appear — e.g., only OPEN orders get a GSI1PK, so the GSI is a filtered view
- **Entity-type index:** GSI1PK=entity type, GSI1SK=date — list all entities of a type sorted by time
- **Connection index:** GSI on a connection/session ID for WebSocket or real-time apps

### Step 4: Output the design

Present the final design as:

1. **Access pattern table** (from step 1, now filled in with key conditions)
2. **Entity chart** showing every entity type with its PK, SK, GSI keys, and key attributes
3. **Table definition** in CDK, SAM, or CloudFormation (match the project's IaC tool)

## Key design patterns

### One-to-many (parent-child)
```
PK              SK                    Data
USER#alice      PROFILE               {name, email}
USER#alice      ORDER#2024-001        {total, status}
USER#alice      ORDER#2024-002        {total, status}
```
Query: `PK = USER#alice AND SK begins_with ORDER#` → all orders for user.

### Many-to-many (adjacency list)
```
PK              SK                    Data
DOCTOR#dr1      PATIENT#p1            {appointment}
DOCTOR#dr1      PATIENT#p2            {appointment}
```
GSI inverts: `GSI1PK = SK, GSI1SK = PK` → query patients for a doctor OR doctors for a patient.

### Hierarchical data (composite sort key)
```
PK              SK
COMPANY#acme    DEPT#eng#TEAM#backend#EMP#alice
COMPANY#acme    DEPT#eng#TEAM#frontend#EMP#carol
```
- `begins_with("DEPT#eng")` → all engineering
- `begins_with("DEPT#eng#TEAM#backend")` → just backend

### Time-series (bucketed partitions)
```
PK                          SK
SENSOR#temp-1#2024-03       2024-03-15T10:30:00Z
SENSOR#temp-1#2024-03       2024-03-15T10:31:00Z
```
Bucket by month/day to prevent unbounded partition growth (10GB limit per partition).

### Real-time / WebSocket connections
```
PK              SK                    ConnectionId
GAME#1234       PLAYER#marco          conn-abc-123
GAME#1234       STATE                 —
```
GSI on `ConnectionId` for disconnect cleanup — look up which game/entity a connection belongs to.

### Game/session entity model (reference pattern)
```
PK              SK                          Purpose
GAME#1234       STATE                       Game state and metadata
GAME#1234       PLAYER#marco                Player in game
GAME#1234       QUESTION#c001#001           Question used in game
GAME#1234       ANSWER#001#PLAYER#marco     Player's answer to question
GAME#1234       VOTE#001#PLAYER#marco       Player's vote on question
SET#trivia-1    CAT#science                 Question set category
```
All game data under one PK — single Query fetches everything for a game.

### Social feed / fan-out pattern
When a user's feed must show content from people they follow:
- **Fan-out-on-write:** When User A posts, write a copy to every follower's feed partition. Fast reads, expensive writes. Works when follower counts are bounded.
- **Fan-out-on-read:** At read time, query each followed user's posts and merge. Cheap writes, expensive reads. Works for celebrity accounts (millions of followers).
- **Hybrid:** Fan-out-on-write for normal users, fan-out-on-read for celebrities. Use DynamoDB Streams to trigger the fan-out asynchronously.

This is an inherently hard problem. **Always discuss the tradeoff explicitly** — don't pretend a single DynamoDB query solves it.

### Denormalization trade-offs

When you denormalize (duplicate data to avoid extra reads), always warn about:
- **Update complexity:** If the duplicated field changes, you must update every copy. Use DynamoDB Streams + Lambda for async propagation.
- **Storage cost:** Minimal concern — DynamoDB storage is cheap (~$0.25/GB/month).
- **Consistency window:** During propagation, copies may be temporarily stale. Acceptable for most use cases (eventual consistency).
- **When NOT to denormalize:** If the data changes frequently (e.g., price that updates hourly), keep it normalized and do an extra read.

### Migrating from relational databases

When converting from SQL tables to DynamoDB single table:

1. **Don't map tables 1:1** — collapse related SQL tables into one DynamoDB table
2. **Identify JOIN patterns** — every SQL JOIN becomes either co-location (same PK) or a GSI
3. **Denormalize aggressively** — copy parent data onto child items (e.g., org name on every user item)
4. **Address what changes:**
   - No more ad-hoc queries — every query must be planned in advance
   - No more JOINs — replaced by denormalization and co-location
   - No more foreign key constraints — application must enforce referential integrity
   - Schema flexibility — each item can have different attributes
5. **Migration approach:** Run DynamoDB in parallel with SQL during transition. Use DMS or custom ETL. Validate data completeness before cutting over.

## Table configuration defaults

Always include unless there's a reason not to:

```yaml
BillingMode: PAY_PER_REQUEST        # Start on-demand, switch to provisioned at scale
TimeToLiveSpecification:
  AttributeName: ttl
  Enabled: true                     # Free cleanup of expired items
PointInTimeRecoverySpecification:
  PointInTimeRecoveryEnabled: true  # Free insurance for data recovery
DeletionProtectionEnabled: true     # Prevent accidental table deletion
```

- **PAY_PER_REQUEST** for most workloads — simpler, no capacity planning needed
- **TTL** on a `ttl` attribute (epoch seconds) — auto-deletes expired items at no cost. Use for sessions, temp data, caches.
- Set `TableClass: STANDARD_INFREQUENT_ACCESS` if data is rarely read (60% storage savings)

## Anti-patterns to avoid

1. **Scanning** — if any access pattern requires Scan, the key design is wrong
2. **Hot partitions** — avoid low-cardinality PKs like `STATUS#active`. Use write sharding if needed
3. **Unbounded collections** — don't let one PK accumulate unlimited items. Bucket or paginate
4. **Entity fragmentation** — don't split one entity across multiple items. Each item should be a complete entity
5. **Over-normalization** — denormalize aggressively. Duplicate data to avoid extra reads. Storage is cheap, reads are not
6. **Filter expressions as primary filtering** — filters reduce returned data but still consume read capacity. Push filtering into key conditions
7. **One GSI per access pattern** — overload GSIs instead. Each additional GSI doubles write cost for affected items
8. **Large items returned when few fields needed** — use ProjectionExpressions to return only needed attributes

## Modern DynamoDB features to leverage

- **Zero-ETL to OpenSearch/Redshift/SageMaker Lakehouse** — don't fight single table for analytics. Use DynamoDB for OLTP, zero-ETL for reporting. This removes the biggest argument against single table design.
- **Warm throughput** — pre-warm tables for traffic spikes (product launches, migrations). Set warm throughput values so tables are ready to serve immediately.
- **Resource-based policies** — enable cross-account access when needed (data mesh architectures). Prefer IAM roles for same-account access.
- **Multi-region strong consistency** (global tables) — for applications requiring strong consistency across regions.
- **On-demand pricing reduced 50%** (Nov 2024) — on-demand is now even more cost-effective for variable workloads.

## Output format

When presenting a design, always include:

1. **Access patterns table** — every read/write the app needs and how it maps to DynamoDB operations
2. **Entity chart** — visual table of entity types, their PK/SK values, GSI values, and key attributes
3. **IaC definition** — CDK, SAM, or CloudFormation table resource matching the project's toolchain
4. **Rationale** — brief explanation of key design decisions and tradeoffs
