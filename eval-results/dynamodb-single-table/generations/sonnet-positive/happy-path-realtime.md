# DynamoDB Single-Table Design: Real-Time Quiz Game (WebSocket)

Real-time game data is a classic DynamoDB use case. Let me design this carefully.

---

## Step 1: Access Patterns

| # | Access Pattern | Operation | Key Condition |
|---|---|---|---|
| 1 | Track WebSocket connection (store connection→game mapping) | PutItem | PK=`CONN#connectionId`, SK=`META` |
| 2 | Look up which game a connection belongs to (disconnect cleanup) | GetItem | PK=`CONN#connectionId`, SK=`META` |
| 3 | List all connections in a game (broadcast) | Query | PK=`GAME#gameId`, SK begins_with `CONN#` |
| 4 | Get player profile within a game | GetItem | PK=`GAME#gameId`, SK=`PLAYER#playerId` |
| 5 | List all players in a game | Query | PK=`GAME#gameId`, SK begins_with `PLAYER#` |
| 6 | Store a player's answer for a question | PutItem | PK=`GAME#gameId`, SK=`QUESTION#qId#ANSWER#playerId` |
| 7 | Get all answers for a question | Query | PK=`GAME#gameId`, SK begins_with `QUESTION#qId#ANSWER#` |
| 8 | Store a vote on an answer | PutItem | PK=`GAME#gameId`, SK=`QUESTION#qId#VOTE#voterId` |
| 9 | Get all votes for a question | Query | PK=`GAME#gameId`, SK begins_with `QUESTION#qId#VOTE#` |
| 10 | Get game state | GetItem | PK=`GAME#gameId`, SK=`META` |
| 11 | Look up which game a connection is in (GSI for disconnect) | Query (GSI1) | GSI1PK=`CONN#connectionId` |

---

## Step 2: Key Design

**Base Table:** `PK` (String) + `SK` (String)

Key decisions:
- **Everything under `GAME#gameId`** — all entities (connections, players, answers, votes, game state) share the game partition. This enables single-partition reads for most game operations and is the right choice since games are naturally scoped.
- **Connection → game mapping** has two representations:
  1. `PK=CONN#connectionId`, `SK=META` — for O(1) disconnect lookup without scanning
  2. `PK=GAME#gameId`, `SK=CONN#connectionId` — for listing connections per game (broadcasts)
- **Hierarchical SK for answers/votes** — `QUESTION#qId#ANSWER#playerId` allows querying all answers to a specific question via `begins_with QUESTION#qId#ANSWER#`
- **TTL on all items** — game data should expire. Set `ttl` to game end time + buffer (e.g., 24 hours)

**WebSocket disconnect pattern:** When API Gateway calls your disconnect handler, you only have the `connectionId`. The `CONN#connectionId` partition gives you an immediate GetItem to find the `gameId`, then you can clean up the connection record in the game partition.

---

## Step 2b: Patterns That Don't Fit DynamoDB

- **Leaderboard ranking across all games** (e.g., top 100 players globally): Use **ElastiCache (Sorted Sets)** or **OpenSearch** — DynamoDB cannot efficiently rank across partitions
- **Live vote aggregation with real-time counts**: Pre-compute counters using atomic increments (`ADD` on a Number attribute) on a score record per question, rather than counting all vote records at read time
- **Fan-out to all players** (broadcast game events): DynamoDB Streams → Lambda → API Gateway Management API to push events to each `connectionId`

---

## Step 3: GSI Design

**GSI1** — Connection-to-game reverse lookup
- `GSI1PK` = `CONN#connectionId`
- `GSI1SK` = `GAME#gameId`
- **Sparse**: only the connection-in-game records (`PK=GAME#gameId, SK=CONN#connectionId`) populate this GSI
- Handles disconnect cleanup: given connectionId, find the gameId

This is the classic **inverted index** pattern: the base table has `PK=GAME#gameId, SK=CONN#connectionId`, and the GSI inverts it so you can query from the connection side.

Only 1 GSI needed. Everything else is served by the base table with `begins_with` on the game partition.

---

## Step 4: Design Output

### Entity Chart

| Entity | PK | SK | GSI1PK | GSI1SK | Key Attributes |
|---|---|---|---|---|---|
| Game state | `GAME#gameId` | `META` | — | — | status, currentQuestion, hostId, ttl |
| Player profile | `GAME#gameId` | `PLAYER#playerId` | — | — | name, score, joinedAt, ttl |
| Connection (in game) | `GAME#gameId` | `CONN#connectionId` | `CONN#connectionId` | `GAME#gameId` | playerId, ttl |
| Connection (lookup) | `CONN#connectionId` | `META` | — | — | gameId, playerId, ttl |
| Player answer | `GAME#gameId` | `QUESTION#qId#ANSWER#playerId` | — | — | answer, submittedAt, ttl |
| Vote | `GAME#gameId` | `QUESTION#qId#VOTE#voterId` | — | — | targetPlayerId, ttl |
| Vote counter | `GAME#gameId` | `QUESTION#qId#TALLY` | — | — | counts (Map: {playerId: N}), ttl |

**Note on Vote counter:** Rather than counting vote records at read time, maintain a `TALLY` record with atomic `ADD` operations. This avoids a full Query just to count votes.

### Access Pattern Resolution

| # | Access Pattern | How |
|---|---|---|
| 1 | Store connection | `PutItem(PK=CONN#c1, SK=META, gameId=g1, ttl=...)` + `PutItem(PK=GAME#g1, SK=CONN#c1, GSI1PK=CONN#c1, GSI1SK=GAME#g1, ttl=...)` |
| 2 | Disconnect cleanup: find game from connectionId | `GetItem(PK=CONN#c1, SK=META)` → returns gameId |
| 3 | List connections in a game | `Query(PK=GAME#g1, SK begins_with CONN#)` |
| 4 | Get player profile | `GetItem(PK=GAME#g1, SK=PLAYER#p1)` |
| 5 | List all players in game | `Query(PK=GAME#g1, SK begins_with PLAYER#)` |
| 6 | Store player answer | `PutItem(PK=GAME#g1, SK=QUESTION#q1#ANSWER#p1, answer=..., ttl=...)` |
| 7 | Get all answers for a question | `Query(PK=GAME#g1, SK begins_with QUESTION#q1#ANSWER#)` |
| 8 | Get game state | `GetItem(PK=GAME#g1, SK=META)` |

### IaC Definition (CDK — TypeScript)

```typescript
import * as cdk from 'aws-cdk-lib';
import * as dynamodb from 'aws-cdk-lib/aws-dynamodb';
import { Construct } from 'constructs';

export class QuizGameTable extends Construct {
  public readonly table: dynamodb.Table;

  constructor(scope: Construct, id: string) {
    super(scope, id);

    this.table = new dynamodb.Table(this, 'QuizGameTable', {
      tableName: 'quiz-game',
      partitionKey: { name: 'PK', type: dynamodb.AttributeType.STRING },
      sortKey: { name: 'SK', type: dynamodb.AttributeType.STRING },
      billingMode: dynamodb.BillingMode.PAY_PER_REQUEST,
      timeToLiveAttribute: 'ttl',          // critical for game session cleanup
      pointInTimeRecovery: true,
      deletionProtection: true,
    });

    // GSI1: Connection → game reverse lookup (for disconnect handling)
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

1. **Single game partition for all entities** — co-locating connections, players, answers, and votes under `GAME#gameId` matches the natural query scope of a game. All reads during an active game hit the same partition — low latency, no cross-partition reads needed.

2. **Dual connection records** — the `CONN#connectionId` standalone record exists purely for O(1) disconnect lookup. Without it, disconnect cleanup would require a GSI query. With it, disconnect is: GetItem → find gameId → delete from game partition.

3. **Inverted GSI for connections** — GSI1 indexes connection-in-game records so you can go from connectionId to gameId via Query as an alternative to the standalone connection record. In practice, the standalone record is faster (GetItem vs Query), but GSI1 also lets you see if a connectionId is in multiple games (shouldn't happen, but useful for debugging).

4. **Hierarchical SK for answers** — `QUESTION#q1#ANSWER#p1` means you can retrieve all answers to question 1 with `begins_with QUESTION#q1#ANSWER#`, or all game answers with `begins_with QUESTION#`. The hierarchy is encoded in the SK prefix.

5. **TTL on everything** — game session data is ephemeral. Set TTL to game end time + 24 hours. DynamoDB TTL handles cleanup asynchronously at no extra cost, keeping the table lean.

6. **Counter for votes** — using a `TALLY` item with atomic `UpdateItem ADD` for vote counts avoids a Query just to count votes. The tradeoff: if you need to audit individual votes, keep the raw `VOTE#voterId` records too.
