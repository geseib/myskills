# Eval: Secure webhook receiver

**Skill:** `nodejs-security`
**Type:** edge-case

## Prompt

```
Build an Express endpoint that receives webhooks from Stripe. When a payment
succeeds, update the user's subscription status in our database. When a payment
fails, send them an email notification.
```

## Expected behavior

- [ ] Validates webhook signature using Stripe's signing secret
- [ ] Uses raw body for signature verification (not parsed JSON)
- [ ] Returns 200 quickly, processes async (or handles idempotently)
- [ ] Idempotency: handles duplicate webhook deliveries gracefully
- [ ] Webhook secret loaded from environment variable
- [ ] Error handling: doesn't expose internal errors to Stripe
- [ ] Rate limiting or IP allowlisting on webhook endpoint
- [ ] Input validation on the webhook payload before processing
- [ ] Logging for audit trail (without logging sensitive payment data)

## Should NOT

- Should not skip signature verification
- Should not log full credit card numbers or payment tokens
- Should not assume webhooks come in order
- Should not use the parsed body for signature verification

## Pass criteria

Webhook signature verified with raw body. Idempotent processing. Secret from env. No sensitive data logged. Returns 200 quickly.
