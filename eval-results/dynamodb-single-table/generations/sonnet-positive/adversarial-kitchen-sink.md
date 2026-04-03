# DynamoDB Single-Table Design: Social Media Platform

I'll work through this systematically — but I need to flag upfront that several of these patterns don't fit DynamoDB well, and forcing them into a single table would be a mistake. Let me be explicit about what goes where.

---

## Step 1: Access Patterns

| # | Access Pattern | Operation | Key Condition |
|---|---|---|---|
| 1 | Get user profile | GetItem | PK=`USER#userId`, SK=`PROFILE` |
| 2 | List user's posts (newest first) | Query | PK=`USER#userId`, SK begins_with `POST#`, ScanIndexForward=false |
| 3 | Get a specific post | GetItem | PK=`POST#postId`, SK=`META` |
| 4 | List comments on a post | Query | PK=`POST#postId`, SK begins_with `COMMENT#` |
| 5 | List a user's comments across all posts | Query (GSI1) | GSI1PK=`USER#userId`, GSI1SK begins_with `COMMENT#` |
| 6 | List followers of a user | Query | PK=`USER#userId`, SK begins_with `FOLLOWER#` |
| 7 | List who a user follows | Query (GSI1) | GSI1PK=`USER#followerId`, GSI1SK begins_with `FOLLOWS#` |
| 8 | Get user's feed (posts from followed users) | **See below — complex** | — |
| 9 | Search posts by hashtag | **OpenSearch — not DynamoDB** | — |
| 10 | Get trending hashtags | **OpenSearch or Redshift** | — |
| 11 | List users who liked a post | Query (GSI2) | GSI2PK=`POST#postId`, GSI2SK begins_with `LIKE#` |
| 12 | Get like count for a post | GetItem (counter) | PK=`POST#postId`, SK=`STATS` |
| 13 | List a user's liked posts | Query (GSI2) | GSI2PK=`USER#userId`, GSI2SK begins_with `LIKED#` |
| 14 | DM threads between two users | Query | PK=`THREAD#<userA-userB>`, SK begins_with `MSG#` |
| 15 | Notification inbox for a user | Query | PK=`USER#userId`, SK begins_with `NOTIF#` |

---

## Step 2b: What DOESN'T Fit DynamoDB (Say This Upfront)

Before key design, I need to be direct:

**Pattern 9 — Hashtag search**: DynamoDB requires exact key matches. Searching posts by hashtag requires knowing the exact hashtag, then using a GSI — that's manageable (a sparse tag index). Fuzzy search, partial match, or relevance ranking? That's **OpenSearch**, full stop.

**Pattern 10 — Trending hashtags**: "Trending" means aggregating counts over a time window across all posts. DynamoDB cannot aggregate. Use **OpenSearch** (computed from Streams) or a pre-computed counter updated via Streams + Lambda. You can store a `TRENDING#<date>` item updated periodically, but the trending computation itself happens outside DynamoDB.

**Pattern 8 — User feed**: This is the hardest problem in social media architecture. There are two approaches:

- **Fan-out-on-write**: When a user posts, Lambda writes the post reference to every follower's feed partition. Feed reads are O(1) — just query the user's feed partition. Write cost scales with follower count. **Not viable for users with millions of followers** (celebrities, viral accounts).
- **Fan-out-on-read**: When a user loads their feed, query each followed user's posts partition and merge/sort in application code. Read cost scales with follow count. Expensive for users following thousands of accounts.
- **Hybrid**: Fan-out-on-write for regular users, fan-out-on-read for celebrity accounts (identified by follower threshold). This is what Twitter/X used.

**My recommendation for the feed**: Fan-out-on-write for accounts with <10K followers (DynamoDB Streams + Lambda writes to feed partitions). For celebrity accounts, compute the feed on-read with a short TTL cache (**ElastiCache**). This is a product decision — I'll design the DynamoDB side for fan-out-on-write and note the celebrity exception.

**Pattern 9 revised for hashtag**: Store a `HASHTAG#<tag>` partition with post references. This handles "list posts by exact hashtag" but not search/trending. Add **OpenSearch** for those.

---

## Step 2: Key Design

**Base Table:** `PK` (String) + `SK` (String)

Key principles for this design:
- User profile, posts (refs), followers, and notifications co-locate under `USER#userId`
- Post canonical record + comments live under `POST#postId`
- Likes live as adjacency list records (user→post and post→user)
- DM threads live under a deterministic `THREAD#<sortedUserIds>` key
- Feed uses a dedicated `FEED#userId` partition populated by fan-out

---

## Step 3: GSI Design

**GSI1** — User's comments across posts + follow graph (inverted)
- For comments: `GSI1PK=USER#userId`, `GSI1SK=COMMENT#<isoDate>#<commentId>`
- For follow graph (who a user follows): `GSI1PK=USER#followerId`, `GSI1SK=FOLLOWS#followeeId`
- **Overloaded**: two different record types use the same GSI attributes

**GSI2** — Likes (bidirectional)
- For "users who liked a post": `GSI2PK=POST#postId`, `GSI2SK=LIKE#userId`
- For "posts a user liked": `GSI2PK=USER#userId`, `GSI2SK=LIKED#<isoDate>#<postId>`
- **Overloaded**: like records serve both directions

**GSI3** — Hashtag post index
- `GSI3PK=HASHTAG#<tag>`, `GSI3SK=<isoDate>#<postId>`
- **Sparse**: only posts with hashtags populate this; hashtag items written separately for each tag on a post
- Handles "list posts by exact hashtag" sorted by date

Three GSIs — at the upper end of what I'd recommend. The like adjacency list (GSI2) alone doubles write cost for every like action. Evaluate whether "users who liked a post" (pattern 11) is worth the GSI cost, or if you can serve it from application-side pagination with a base table Query.

---

## Step 4: Design Output

### Entity Chart

| Entity | PK | SK | GSI1PK | GSI1SK | GSI2PK | GSI2SK | GSI3PK | GSI3SK |
|---|---|---|---|---|---|---|---|---|
| User profile | `USER#userId` | `PROFILE` | — | — | — | — | — | — |
| Post ref (in user) | `USER#userId` | `POST#<isoDate>#<postId>` | — | — | — | — | — | — |
| Post canonical | `POST#postId` | `META` | — | — | — | — | — | — |
| Comment | `POST#postId` | `COMMENT#<isoDate>#<commentId>` | `USER#authorId` | `COMMENT#<isoDate>#<commentId>` | — | — | — | — |
| Follower record | `USER#userId` | `FOLLOWER#<followerId>` | `USER#followerId` | `FOLLOWS#<userId>` | — | — | — | — |
| Like record | `POST#postId` | `LIKE#<userId>` | — | — | `POST#postId` | `LIKE#<userId>` | — | — |
| Like ref (on user) | `USER#userId` | `LIKED#<isoDate>#<postId>` | — | — | `USER#userId` | `LIKED#<isoDate>#<postId>` | — | — |
| Post stats | `POST#postId` | `STATS` | — | — | — | — | — | — |
| Hashtag post ref | `POST#postId` | `TAG#<tag>` | — | — | — | — | `HASHTAG#<tag>` | `<isoDate>#<postId>` |
| Feed item | `FEED#userId` | `POST#<isoDate>#<postId>` | — | — | — | — | — | — |
| DM message | `THREAD#<userA-userB>` | `MSG#<isoDate>#<msgId>` | — | — | — | — | — | — |
| Notification | `USER#userId` | `NOTIF#<isoDate>#<notifId>` | — | — | — | — | — | — |

**DM thread key format:** Sort the two user IDs lexicographically and join with `-` to get a deterministic thread ID regardless of who initiates: `THREAD#alice-bob` (not `THREAD#bob-alice`).

### Access Pattern Resolution

| # | Access Pattern | How |
|---|---|---|
| 1 | Get user profile | `GetItem(PK=USER#u1, SK=PROFILE)` |
| 2 | List user's posts newest first | `Query(PK=USER#u1, SK begins_with POST#, ScanIndexForward=false)` |
| 3 | Get specific post | `GetItem(PK=POST#p1, SK=META)` |
| 4 | List comments on a post | `Query(PK=POST#p1, SK begins_with COMMENT#)` |
| 5 | User's comments across all posts | `Query(GSI1, GSI1PK=USER#u1, GSI1SK begins_with COMMENT#)` |
| 6 | List followers of a user | `Query(PK=USER#u1, SK begins_with FOLLOWER#)` |
| 7 | List who a user follows | `Query(GSI1, GSI1PK=USER#u1, GSI1SK begins_with FOLLOWS#)` |
| 8 | User feed | `Query(PK=FEED#u1, SK begins_with POST#, ScanIndexForward=false)` |
| 9 | Posts by hashtag | `Query(GSI3, GSI3PK=HASHTAG#<tag>, ScanIndexForward=false)` |
| 10 | Trending hashtags | Precomputed `TRENDING#<date>` item updated by Lambda; or OpenSearch |
| 11 | Users who liked a post | `Query(GSI2, GSI2PK=POST#p1, GSI2SK begins_with LIKE#)` |
| 12 | Like count for a post | `GetItem(PK=POST#p1, SK=STATS)` — counter maintained via atomic UpdateItem |
| 13 | User's liked posts | `Query(GSI2, GSI2PK=USER#u1, GSI2SK begins_with LIKED#)` |
| 14 | DM thread | `Query(PK=THREAD#alice-bob, SK begins_with MSG#, ScanIndexForward=false)` |
| 15 | Notification inbox | `Query(PK=USER#u1, SK begins_with NOTIF#, ScanIndexForward=false)` |

### IaC Definition (CDK — TypeScript)

```typescript
import * as cdk from 'aws-cdk-lib';
import * as dynamodb from 'aws-cdk-lib/aws-dynamodb';
import { Construct } from 'constructs';

export class SocialMediaTable extends Construct {
  public readonly table: dynamodb.Table;

  constructor(scope: Construct, id: string) {
    super(scope, id);

    this.table = new dynamodb.Table(this, 'SocialMediaTable', {
      tableName: 'social-media',
      partitionKey: { name: 'PK', type: dynamodb.AttributeType.STRING },
      sortKey: { name: 'SK', type: dynamodb.AttributeType.STRING },
      billingMode: dynamodb.BillingMode.PAY_PER_REQUEST,
      timeToLiveAttribute: 'ttl',
      pointInTimeRecovery: true,
      deletionProtection: true,
      stream: dynamodb.StreamViewType.NEW_AND_OLD_IMAGES, // for feed fan-out Lambda
    });

    // GSI1: User's comments + follow graph (overloaded)
    this.table.addGlobalSecondaryIndex({
      indexName: 'GSI1',
      partitionKey: { name: 'GSI1PK', type: dynamodb.AttributeType.STRING },
      sortKey: { name: 'GSI1SK', type: dynamodb.AttributeType.STRING },
      projectionType: dynamodb.ProjectionType.ALL,
    });

    // GSI2: Like adjacency list (post→users, user→posts)
    this.table.addGlobalSecondaryIndex({
      indexName: 'GSI2',
      partitionKey: { name: 'GSI2PK', type: dynamodb.AttributeType.STRING },
      sortKey: { name: 'GSI2SK', type: dynamodb.AttributeType.STRING },
      projectionType: dynamodb.ProjectionType.ALL,
    });

    // GSI3: Hashtag post index
    this.table.addGlobalSecondaryIndex({
      indexName: 'GSI3',
      partitionKey: { name: 'GSI3PK', type: dynamodb.AttributeType.STRING },
      sortKey: { name: 'GSI3SK', type: dynamodb.AttributeType.STRING },
      projectionType: dynamodb.ProjectionType.ALL,
    });
  }
}
```

### Rationale and Honest Tradeoffs

**What DynamoDB handles well here:**
- User profiles, posts, comments, DMs, notifications — straightforward co-location patterns
- Follower graph — adjacency list with inverted GSI1
- Like counts — atomic counter on STATS item
- Feed reads — single partition Query on `FEED#userId`

**What requires careful engineering:**

1. **Feed fan-out** — creating a post triggers a Lambda (via Streams) that writes a feed item to every follower's `FEED#userId` partition. For a user with 1M followers, this is 1M writes. Implement a celebrity threshold: users with >10K followers are "celebrities" and their posts are fetched on-read instead of written to follower feeds. Use **ElastiCache** to cache celebrity post lists.

2. **Write amplification on likes** — liking a post writes 3 records: `POST#postId/LIKE#userId`, `USER#userId/LIKED#date#postId`, and an atomic add to `POST#postId/STATS`. Three writes per like. Monitor and consider dropping pattern 11 (users who liked a post) from DynamoDB if it's only for vanity UI — store counts only.

3. **Trending hashtags** — DynamoDB cannot compute trending. Options:
   - Lambda aggregates hashtag counts from Streams into a `TRENDING#<date>` item (simple, approximate)
   - Zero-ETL to OpenSearch for real trending computation (accurate, more complex)

4. **Hashtag search** — GSI3 handles exact hashtag lookup only. Any fuzzy search, autocomplete, or relevance ranking requires **OpenSearch**.

5. **3 GSIs** — this is at the limit I'd recommend. Each GSI roughly doubles write costs for items that populate it. Evaluate whether each GSI earns its keep in your read pattern frequency. If "users who liked a post" (GSI2 post-side) is rarely shown, cut it and fetch from the post's base table records instead.

**Architecture summary:**
- DynamoDB: profiles, posts, comments, likes (counts + lists), followers, DMs, notifications, feeds, exact hashtag lookup
- Lambda + Streams: feed fan-out, trending computation, like count fan-out
- ElastiCache: celebrity post caches, hot-read optimization
- OpenSearch: hashtag search, trending hashtags, full-text search
