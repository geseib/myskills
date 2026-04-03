This is an ambitious scope for a single DynamoDB table. Let me work through this methodically — some of these patterns fit DynamoDB cleanly, and some don't. Being honest about that is more useful than forcing everything into DynamoDB.

# DynamoDB Single Table Design: Social Media Platform

## Step 1: Access Patterns

| Access Pattern | Operation | Key Condition |
|---|---|---|
| Get user profile | GetItem | PK=`USER#userId`, SK=`PROFILE` |
| List a user's posts (newest first) | Query | PK=`USER#userId`, SK begins_with `POST#`, ScanIndexForward=false |
| Get a specific post | GetItem | PK=`POST#postId`, SK=`METADATA` |
| List comments on a post | Query | PK=`POST#postId`, SK begins_with `COMMENT#` |
| List a user's comments across all posts | Query (GSI1) | GSI1PK=`USER#userId#COMMENTS`, GSI1SK begins_with `COMMENT#` |
| List followers of a user | Query | PK=`USER#userId`, SK begins_with `FOLLOWER#` |
| List who a user follows | Query (GSI1) | GSI1PK=`USER#userId#FOLLOWING`, GSI1SK begins_with `USER#` |
| Get a user's feed | DynamoDB Streams + fan-out (see Step 2b) | — |
| Search posts by hashtag | **OpenSearch — not DynamoDB** | — |
| Get trending hashtags | **OpenSearch — not DynamoDB** | — |
| List users who liked a post | Query (GSI2) | GSI2PK=`POST#postId#LIKES`, GSI2SK begins_with `USER#` |
| Get like count for a post | Denormalized counter on post item | GetItem on `POST#postId / METADATA` |
| List a user's liked posts | Query (GSI2) | GSI2PK=`USER#userId#LIKES`, GSI2SK begins_with `POST#` |
| DM threads between two users | Query | PK=`DM#<sortedUserId1>_<sortedUserId2>`, SK begins_with `MSG#` |
| Notification inbox for a user | Query | PK=`USER#userId`, SK begins_with `NOTIF#`, ScanIndexForward=false |

**Total: 13 DynamoDB patterns + 2 that require OpenSearch. 0 Scans.**

---

## Step 2b: Patterns That Don't Fit DynamoDB

### 1. Search posts by hashtag — Use OpenSearch

DynamoDB has no full-text or tag search capability. You'd need a Scan with a FilterExpression — unacceptable at scale.

**Solution:** Index posts into OpenSearch Serverless via DynamoDB Streams + Lambda zero-ETL. Hashtag searches run against OpenSearch. This gives you full-text search, hashtag queries, and boolean filters with millisecond response times.

### 2. Trending hashtags — Use OpenSearch

"Trending" requires aggregation — counting hashtag occurrences in a time window, sorting by frequency. DynamoDB cannot aggregate.

**Solution:** Same OpenSearch index. Run a date-range aggregation on the hashtags field. OpenSearch handles this natively. Alternatively, use Kinesis Data Streams → Lambda to maintain a trending leaderboard in ElastiCache (Redis Sorted Sets — purpose-built for real-time rankings).

### 3. User feed — Fan-out on write (DynamoDB Streams)

"Posts from people I follow, sorted by time" cannot be served by a single DynamoDB Query without pre-materializing the feed. Your two options:

**Fan-out-on-write (recommended for most cases):**
- When user A posts, a Lambda reads A's follower list and writes a feed item to each follower's feed partition
- Feed reads are fast (O(1) Query on `USER#userId / FEED#` items)
- Write cost scales with follower count — problematic for celebrities with millions of followers
- **Hybrid approach:** Fan out to all followers with <10,000 followers. For high-follower accounts, use fan-out-on-read (query followed accounts at feed load time and merge results)

**Fan-out-on-read:**
- At feed load time, query the follower list, then fetch recent posts from each followed user
- No write amplification, but N+1 queries at read time (one per followed user)
- Only viable if following count is small (<50) and feed refresh is infrequent

I'll design the fan-out-on-write approach as the default, with a flag for hybrid mode.

---

## Step 2 (continued): Key Design

**Base Table Keys:** `PK` (String), `SK` (String)

**Key design decisions:**

**Posts exist in two places:**
1. Under `USER#userId` for "list user's posts" (post summary)
2. Under `POST#postId` for canonical access, comments, and interactions

**Follow relationships use the adjacency list pattern:**
- `PK=USER#userId, SK=FOLLOWER#followerId` → stores who follows a user (list followers)
- GSI inverts this → `GSI1PK=USER#userId#FOLLOWING, GSI1SK=USER#followedId` → who a user follows

**DM threads:** Sort both user IDs lexicographically to create a deterministic thread ID (`DM#userA_userB` where userA < userB alphabetically). This ensures both users always hit the same partition.

**Notifications:** Time-sorted under user partition with `NOTIF#<isoTimestamp>#<notifId>` SK. Newest-first via `ScanIndexForward=false`.

| Entity | PK | SK | Notes |
|---|---|---|---|
| User Profile | `USER#userId` | `PROFILE` | — |
| Post (user ref) | `USER#userId` | `POST#<isoTimestamp>#<postId>` | For "list user's posts" |
| Post (canonical) | `POST#postId` | `METADATA` | Full post data |
| Comment | `POST#postId` | `COMMENT#<isoTimestamp>#<commentId>` | Co-located with post |
| Follow Relationship | `USER#userId` | `FOLLOWER#followerId` | "userId is followed by followerId" |
| Like | `USER#userId` | `LIKED#<postId>` | "userId liked postId" (for user's likes) |
| Feed Item | `USER#userId` | `FEED#<isoTimestamp>#<postId>` | Fan-out-on-write target |
| DM Message | `DM#<userId1>_<userId2>` | `MSG#<isoTimestamp>#<msgId>` | Deterministic thread ID |
| Notification | `USER#userId` | `NOTIF#<isoTimestamp>#<notifId>` | Newest-first |

---

## Step 3: GSI Design

**Maximum 3 GSIs.** Overload each one.

### GSI1 — User-Centric Cross-Partition Queries (Overloaded)

| Entity | GSI1PK | GSI1SK | Purpose |
|---|---|---|---|
| Comment (by user) | `USER#userId#COMMENTS` | `COMMENT#<isoTimestamp>#<commentId>` | List user's comments across all posts |
| Follow Relationship (inverted) | `USER#userId#FOLLOWING` | `USER#followedId` | List who a user follows |

- Follow relationship item at `PK=USER#userId / FOLLOWER#followerId` populates GSI1 with the inverse: `GSI1PK=USER#followerId#FOLLOWING, GSI1SK=USER#userId`
- Comment items at `PK=POST#postId / COMMENT#ts#commentId` populate GSI1 with `GSI1PK=USER#authorId#COMMENTS`

### GSI2 — Like Index (Overloaded, Bidirectional)

| Entity | GSI2PK | GSI2SK | Purpose |
|---|---|---|---|
| Like (post-centric) | `POST#postId#LIKES` | `USER#userId` | List users who liked a post |
| Like (user-centric) | `USER#userId#LIKES` | `POST#postId` | List posts a user liked |

A Like item has both GSI2PK options... but an item can only have one GSI2PK. **Solution:** Create two items per like:
1. `PK=USER#userId, SK=LIKED#postId` with `GSI2PK=POST#postId#LIKES, GSI2SK=USER#userId`
2. `PK=POST#postId, SK=LIKE#userId` with `GSI2PK=USER#userId#LIKES, GSI2SK=POST#postId`

Both items in a transaction (TransactWrite) ensures consistency.

### GSI3 — Feed Fan-Out Reference (Optional)

If you implement fan-out-on-write, you may need to identify followers of a user efficiently during the post Lambda. The base table pattern `PK=USER#userId, SK=FOLLOWER#followerId` handles this with a Query — no extra GSI needed if follower counts are manageable. Skip GSI3.

**Final count: 2 GSIs.** This is deliberately conservative.

---

## Step 4: Entity Chart

| Entity | PK | SK | GSI1PK | GSI1SK | GSI2PK | GSI2SK | Key Attributes |
|---|---|---|---|---|---|---|---|
| User Profile | `USER#userId` | `PROFILE` | — | — | — | — | name, handle, bio, followerCount, followingCount, likeCount |
| Post (user ref) | `USER#userId` | `POST#<isoTs>#<postId>` | — | — | — | — | postId, excerpt, likeCount, commentCount, createdAt |
| Post (canonical) | `POST#postId` | `METADATA` | — | — | — | — | authorId, content, hashtags[], likeCount, commentCount, createdAt |
| Comment | `POST#postId` | `COMMENT#<isoTs>#<commentId>` | `USER#authorId#COMMENTS` | `COMMENT#<isoTs>#<commentId>` | — | — | authorId, content, createdAt |
| Follow (follower list) | `USER#userId` | `FOLLOWER#followerId` | `USER#followerId#FOLLOWING` | `USER#userId` | — | — | followedAt |
| Like (post-centric) | `USER#userId` | `LIKED#postId` | — | — | `POST#postId#LIKES` | `USER#userId` | likedAt |
| Like (user-centric) | `POST#postId` | `LIKE#userId` | — | — | `USER#userId#LIKES` | `POST#postId` | likedAt |
| Feed Item | `USER#userId` | `FEED#<isoTs>#<postId>` | — | — | — | — | postId, authorId, excerpt, createdAt, ttl |
| DM Message | `DM#<u1>_<u2>` | `MSG#<isoTs>#<msgId>` | — | — | — | — | senderId, content, readAt |
| Notification | `USER#userId` | `NOTIF#<isoTs>#<notifId>` | — | — | — | — | type, actorId, targetId, read, createdAt, ttl |

---

## IaC Definition (CDK — TypeScript)

```typescript
import * as cdk from 'aws-cdk-lib';
import * as dynamodb from 'aws-cdk-lib/aws-dynamodb';
import { Construct } from 'constructs';

export class SocialTable extends Construct {
  public readonly table: dynamodb.Table;

  constructor(scope: Construct, id: string) {
    super(scope, id);

    this.table = new dynamodb.Table(this, 'SocialTable', {
      tableName: 'social',
      partitionKey: { name: 'PK', type: dynamodb.AttributeType.STRING },
      sortKey: { name: 'SK', type: dynamodb.AttributeType.STRING },
      billingMode: dynamodb.BillingMode.PAY_PER_REQUEST,
      timeToLiveAttribute: 'ttl',
      pointInTimeRecovery: true,
      deletionProtection: true,
      stream: dynamodb.StreamViewType.NEW_AND_OLD_IMAGES, // For feed fan-out
      removalPolicy: cdk.RemovalPolicy.RETAIN,
    });

    // GSI1: User comments + following list (overloaded)
    this.table.addGlobalSecondaryIndex({
      indexName: 'GSI1',
      partitionKey: { name: 'GSI1PK', type: dynamodb.AttributeType.STRING },
      sortKey: { name: 'GSI1SK', type: dynamodb.AttributeType.STRING },
      projectionType: dynamodb.ProjectionType.ALL,
    });

    // GSI2: Like index — bidirectional (post→users, user→posts)
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

## Denormalized Counters

Like counts and follower counts change frequently. Two options:

**Option A: DynamoDB Atomic Counters (recommended)**
```python
# On like:
table.update_item(
    Key={'PK': f'POST#{post_id}', 'SK': 'METADATA'},
    UpdateExpression='ADD likeCount :one',
    ExpressionAttributeValues={':one': 1}
)
```
- Atomic, no race conditions
- Slightly stale on eventual consistency reads (GSI)
- Correct for strongly consistent base table reads

**Option B: ElastiCache (Redis) for real-time counts**
- Sub-millisecond counter updates with INCR
- Periodic flush to DynamoDB for durability
- Better for extremely high-throughput like operations

For most social platforms, Option A (atomic counters in DynamoDB) is sufficient.

---

## Rationale

**Why are search and trending excluded from DynamoDB?** These patterns fundamentally require capabilities DynamoDB doesn't have: full-text indexing and aggregation. Forcing them into DynamoDB means Scan operations or denormalized hashtag tables that become inconsistent. OpenSearch is the right tool and integrates seamlessly via zero-ETL Streams processing.

**Why fan-out-on-write for feeds?** The alternative — querying every followed user's posts at feed load time — requires N+1 Queries where N is the number of accounts the user follows. For a user following 500 accounts, that's 500 parallel Queries every time they open the app. Fan-out-on-write pre-materializes the feed, making reads a single Query. The tradeoff is write amplification when a celebrity posts — mitigated by the hybrid approach (fan out only to non-celebrity followers).

**Why two items per Like?** The like relationship is many-to-many: a post has many likers, a user has many liked posts. Without two items, you can't serve both directions without a Scan. Two items in a TransactWrite ensures they stay consistent. Each item populates a different GSI partition, solving both query directions with O(1) lookups.

**Why TTL on feed items and notifications?** Feeds and notification inboxes are naturally time-bounded. Items older than 30 days (or whatever your retention policy is) lose value and accumulate indefinitely without cleanup. TTL handles this automatically and for free. Users who haven't opened the app in 30 days get a fresh feed on return (fetched via fan-out-on-read fallback).

**Known scale limits with this design:**
- **DM threads:** Storing all messages in one partition is fine for most user-to-user threads. If you're building a group chat product (thousands of messages, many participants), bucket by time period (e.g., `DM#<threadId>#<YYYY-MM>`).
- **Celebrity followers:** A user with 10M followers will trigger 10M write items when they post. Use the hybrid fan-out strategy — identify high-follower accounts and exclude them from write fan-out, serving their followers via on-read merge instead.
- **Notification inbox:** Unbounded growth if users never read notifications. TTL of 30-90 days prevents this. Consider also a `read` boolean + a periodic cleanup Lambda for very active users.
