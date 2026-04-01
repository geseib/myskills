# Eval: Real-time app with WebSocket connections

**Skill:** `dynamodb-single-table`
**Type:** happy-path

## Prompt

```
I'm building a real-time quiz game with WebSocket connections. Players join a game room, answer questions, and vote on answers. I need to:
- Track WebSocket connections per game
- Look up which game a connection belongs to (for disconnect cleanup)
- Store player profiles within a game
- Store answers and votes per question per player
- Get all answers for a question
- Get game state
```

## Expected behavior

- [ ] Lists all access patterns before designing keys
- [ ] Uses GAME#<id> as primary PK to co-locate all game data
- [ ] Uses composite SK patterns (e.g., ANSWER#<q>#PLAYER#<name>)
- [ ] Includes a GSI on ConnectionId for disconnect lookup
- [ ] Recommends TTL for game session data
- [ ] Outputs entity chart and IaC

## Should NOT

- Should not create separate tables for connections, answers, votes
- Should not use Scan to find connections for a game
- Should not skip ConnectionId GSI for disconnect handling

## Pass criteria

Design co-locates all game entities under a single PK. ConnectionId GSI is present. TTL is recommended for session data. Matches the patterns from the engagement repo reference.
