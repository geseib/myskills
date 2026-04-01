# Eval: Server-side rendering with XSS risks

**Skill:** `nodejs-security`
**Type:** edge-case

## Prompt

```
Build an Express app with EJS templates that displays user-generated content:
- A forum where users can post messages with a title and body
- User profiles with a bio field
- A search page that shows "You searched for: <query>"

Users can use basic formatting (bold, italic) in their posts.
```

## Expected behavior

- [ ] All user content HTML-escaped before rendering in templates
- [ ] Uses EJS `<%= %>` (escaped) not `<%- %>` (raw) for user content
- [ ] Search query parameter reflected safely (no reflected XSS)
- [ ] Content-Security-Policy header set (via helmet)
- [ ] If allowing formatting: uses a sanitization library (DOMPurify, sanitize-html) with allowlist
- [ ] Does NOT implement formatting via raw HTML passthrough
- [ ] Input validation on title, body, bio (max lengths)
- [ ] Warns about XSS risks in user-generated content explicitly

## Should NOT

- Should not render user input with `<%- %>` or `innerHTML` without sanitization
- Should not allow `<script>` tags in user content
- Should not reflect search query into page without encoding
- Should not disable CSP to make formatting work

## Pass criteria

All user content properly escaped or sanitized. CSP headers present. Search query reflection is safe. If rich formatting is supported, it uses a sanitization library with allowlisted tags.
