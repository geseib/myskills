# Eval: Adversarial — too many access patterns

**Skill:** `dynamodb-single-table`
**Type:** adversarial

## Prompt

```
Design a DynamoDB table for a social media platform. I need to:
- Get user profiles
- List a user's posts (newest first)
- Get a specific post
- List comments on a post
- List a user's comments across all posts
- List followers of a user
- List who a user follows
- Get a user's feed (posts from people they follow, sorted by time)
- Search posts by hashtag
- Get trending hashtags
- List users who liked a post
- Get like count for a post
- List a user's liked posts
- Direct message threads between two users
- Notification inbox for a user
```

## Expected behavior

- [ ] Starts with access pattern table (all 15 patterns listed)
- [ ] Groups related patterns and identifies which can share key structures
- [ ] Acknowledges that some patterns may be better served by secondary stores (e.g., feed generation, trending = better with caching or search)
- [ ] Recommends zero-ETL to OpenSearch for search/trending patterns
- [ ] Keeps core CRUD patterns in DynamoDB with <=3 GSIs
- [ ] Does NOT try to force all 15 patterns into a single table with 10+ GSIs
- [ ] Explicitly warns about trade-offs and what doesn't fit cleanly

## Should NOT

- Should not create 5+ GSIs trying to satisfy every pattern
- Should not claim single table design handles everything perfectly
- Should not ignore the feed generation problem (it's inherently fan-out)
- Should not skip the access pattern listing step

## Pass criteria

Skill shows good judgment by NOT forcing everything into one table. Recommends complementary services (OpenSearch, ElastiCache, or Streams) for patterns that don't fit. Core patterns use <=3 GSIs. Tradeoffs are explicitly discussed.
