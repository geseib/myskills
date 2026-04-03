Real-time quiz games are a great DynamoDB use case. Let's design this properly — WebSocket connections, game state, and time-series answers all have well-established patterns.

# DynamoDB Single Table Design: Real-Time Quiz Game

## Step 1: Access Patterns

| Access Pattern | Operation | Key Condition |
|---|---|---|
| Track WebSocket connection for a game | PutItem | PK=`GAME#gameId`, SK=`CONN#connectionId` |
| Look up which game a connection belongs to (disconnect cleanup) | GetItem (GSI1) | GSI1PK=`CONN#connectionId` |
| Get player profile within a game | GetItem | PK=`GAME#gameId`, SK=`PLAYER#playerId` |
| List all players in a game | Query | PK=`GAME#gameId`, SK begins_with `PLAYER#` |
| Store an answer for a question by a player | PutItem | PK=`GAME#gameId`, SK=`QUESTION#questionId#ANSWER#playerId` |
| Store a vote on an answer | PutItem | PK=`GAME#gameId`, SK=`QUESTION#questionId#VOTE#playerId` |
| Get all answers for a question | Query | PK=`GAME#gameId`, SK begins_with `QUESTION#questionId#ANSWER#` |
| Get all votes for a question | Query | PK=`GAME#gameId`, SK begins_with `QUESTION#questionId#VOTE#` |
| Get game state | GetItem | PK=`GAME#gameId`, SK=`METADATA` |

**Total: 9 patterns, 0 Scans.**

---

## Step 2: Key Design

**Base Table Keys:**
- `PK` (String) — partition key
- `SK` (String) — sort key

**Core design principle:** Everything in a game lives under `PK=GAME#gameId`. This co-locates all related entities for efficient single-partition queries. The one exception is the connection-to-game lookup (for disconnect cleanup), which requires a GSI since the query starts from a connectionId, not a gameId.

**Key formats:**

| Entity | PK | SK | Notes |
|---|---|---|---|
| Game State | `GAME#gameId` | `METADATA` | Current question, phase, scores |
| WebSocket Connection | `GAME#gameId` | `CONN#connectionId` | Maps connection to game |
| Player Profile | `GAME#gameId` | `PLAYER#playerId` | Score, display name, status |
| Answer | `GAME#gameId` | `QUESTION#questionId#ANSWER#playerId` | Composite SK enables prefix query |
| Vote | `GAME#gameId` | `QUESTION#questionId#VOTE#playerId` | Same prefix pattern |

**Composite SK design for answers/votes:** The SK `QUESTION#questionId#ANSWER#playerId` allows:
- `begins_with(QUESTION#q1#ANSWER#)` → all answers for question 1
- `begins_with(QUESTION#q1#VOTE#)` → all votes for question 1
- `begins_with(QUESTION#q1#)` → all activity for question 1 (answers + votes)

---

## Step 2b: Patterns That Don't Fit DynamoDB

**Leaderboards with real-time ranking:** If you need a global leaderboard sorted by score across all active games, that's an aggregation that doesn't fit DynamoDB key design. Options:
- **ElastiCache (Redis Sorted Sets)** — sub-millisecond sorted score updates, ideal for real-time leaderboards
- **DynamoDB Streams + Lambda** — fan out score updates to a leaderboard table or Redis

For a single-game leaderboard (all players in one game), a Query on `PK=GAME#gameId, SK begins_with PLAYER#` and sorting client-side is perfectly fine.

---

## Step 3: GSI Design

### GSI1 — Connection Index (for disconnect cleanup)

| Entity | GSI1PK | GSI1SK | Purpose |
|---|---|---|---|
| WebSocket Connection | `CONN#connectionId` | `GAME#gameId` | Look up game from connectionId |

**This is the critical pattern:** When a WebSocket disconnects, your Lambda receives only the `connectionId`. You need to find which game that connection belongs to, then clean up the player's state. Without this GSI, you'd need a Scan — which is never acceptable.

- Only connection items populate GSI1 — all other entities omit GSI1PK/GSI1SK (sparse index)
- GSI1PK = `CONN#connectionId` gives you a GetItem-equivalent lookup via Query

**TTL on connections and session data:** Set a `ttl` attribute on all connection, player, answer, and vote items. For a quiz game, sessions are short-lived — TTL of 24 hours is usually sufficient. DynamoDB will automatically delete expired items at no extra cost.

---

## Step 4: Entity Chart

| Entity | PK | SK | GSI1PK | GSI1SK | TTL | Key Attributes |
|---|---|---|---|---|---|---|
| Game State | `GAME#gameId` | `METADATA` | — | — | Yes | currentQuestion, phase, startedAt, hostId |
| WebSocket Connection | `GAME#gameId` | `CONN#connectionId` | `CONN#connectionId` | `GAME#gameId` | Yes | playerId, connectedAt |
| Player Profile | `GAME#gameId` | `PLAYER#playerId` | — | — | Yes | displayName, score, connectionId, status |
| Answer | `GAME#gameId` | `QUESTION#questionId#ANSWER#playerId` | — | — | Yes | answerText, answeredAt, isCorrect |
| Vote | `GAME#gameId` | `QUESTION#questionId#VOTE#playerId` | — | — | Yes | votedFor (playerId), votedAt |

---

## IaC Definition (CDK — TypeScript)

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
      timeToLiveAttribute: 'ttl',
      pointInTimeRecovery: true,
      deletionProtection: true,
      removalPolicy: cdk.RemovalPolicy.RETAIN,
    });

    // GSI1: Connection index — look up game from connectionId on disconnect
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

**Game State:**
```json
{
  "PK": "GAME#game001",
  "SK": "METADATA",
  "hostId": "player99",
  "currentQuestion": 3,
  "phase": "VOTING",
  "startedAt": "2024-12-01T14:00:00Z",
  "ttl": 1733097600
}
```

**WebSocket Connection:**
```json
{
  "PK": "GAME#game001",
  "SK": "CONN#abc-123-xyz",
  "GSI1PK": "CONN#abc-123-xyz",
  "GSI1SK": "GAME#game001",
  "playerId": "player42",
  "connectedAt": "2024-12-01T14:01:00Z",
  "ttl": 1733097600
}
```

**Player Profile:**
```json
{
  "PK": "GAME#game001",
  "SK": "PLAYER#player42",
  "displayName": "QuizMaster2000",
  "score": 150,
  "connectionId": "abc-123-xyz",
  "status": "ACTIVE",
  "ttl": 1733097600
}
```

**Answer:**
```json
{
  "PK": "GAME#game001",
  "SK": "QUESTION#q3#ANSWER#player42",
  "answerText": "Paris",
  "answeredAt": "2024-12-01T14:05:30Z",
  "isCorrect": true,
  "ttl": 1733097600
}
```

**Vote:**
```json
{
  "PK": "GAME#game001",
  "SK": "QUESTION#q3#VOTE#player42",
  "votedFor": "player17",
  "votedAt": "2024-12-01T14:06:00Z",
  "ttl": 1733097600
}
```

---

## Disconnect Cleanup Workflow

When API Gateway WebSocket sends a `$disconnect` event with `connectionId`:

```python
# Lambda disconnect handler
def handler(event, context):
    connection_id = event['requestContext']['connectionId']
    
    # 1. Look up which game this connection belongs to
    result = table.query(
        IndexName='GSI1',
        KeyConditionExpression=Key('GSI1PK').eq(f'CONN#{connection_id}')
    )
    
    if not result['Items']:
        return  # Already cleaned up or never registered
    
    conn_item = result['Items'][0]
    game_id = conn_item['GSI1SK']  # e.g., "GAME#game001"
    player_id = conn_item['playerId']
    
    # 2. Delete the connection record
    table.delete_item(Key={'PK': game_id, 'SK': f'CONN#{connection_id}'})
    
    # 3. Update player status to DISCONNECTED
    table.update_item(
        Key={'PK': game_id, 'SK': f'PLAYER#{player_id}'},
        UpdateExpression='SET #s = :disconnected',
        ExpressionAttributeNames={'#s': 'status'},
        ExpressionAttributeValues={':disconnected': 'DISCONNECTED'}
    )
```

---

## Rationale

**Why co-locate everything under GAME#gameId?** All game operations — getting state, listing players, fetching answers, counting votes — start with knowing the gameId. Co-location means a single Query retrieves any combination of these entities. This is the defining advantage of single-table design for session-scoped data.

**Why a GSI for connections?** The disconnect use case is the only pattern that starts from a connectionId rather than a gameId. A GSI with `GSI1PK=CONN#connectionId` is the textbook solution — it's sparse (only connection items appear), cheap to maintain, and gives O(1) lookup.

**Why TTL on everything?** Quiz game sessions are ephemeral. Rather than explicitly deleting thousands of answer/vote items when a game ends, set a TTL slightly beyond the maximum expected game duration. DynamoDB handles cleanup asynchronously at no charge. This simplifies your game-end logic significantly.

**Hot partition consideration:** If a single game becomes extremely popular (thousands of concurrent players all writing answers simultaneously), the `GAME#gameId` partition could become hot. For typical quiz game traffic this is not a concern — DynamoDB partitions handle ~1,000 WCUs per second. If you're building a massive-scale product (tens of thousands concurrent), consider write sharding the answer/vote items by adding a shard suffix to PK.
