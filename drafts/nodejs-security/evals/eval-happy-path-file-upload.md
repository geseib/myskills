# Eval: Secure file upload endpoint

**Skill:** `nodejs-security`
**Type:** happy-path

## Prompt

```
Add a file upload endpoint to my Express app. Users should be able to upload
profile images (JPEG, PNG only, max 5MB). The images need to be stored on disk
and served back via a URL. Users should only be able to see their own images.
```

## Expected behavior

- [ ] File type validation using magic bytes or mimetype check (not just extension)
- [ ] File size limit enforced (5MB max via multer or similar)
- [ ] Filename sanitized — no path traversal (no `../`)
- [ ] Generated unique filenames (UUID or hash) — don't use user-provided names
- [ ] Files stored outside web root OR served through a controller (not static directory with user paths)
- [ ] Authentication required on upload endpoint
- [ ] Authorization: users can only view their own images
- [ ] Rate limiting on upload endpoint
- [ ] Input validation on any metadata fields

## Should NOT

- Should not use user-provided filename directly in file path
- Should not allow arbitrary file types
- Should not serve uploads from a publicly accessible static directory without access control
- Should not skip authentication on the upload or view endpoints

## Pass criteria

Upload validates file type (not just extension), enforces size limits, generates safe filenames, prevents path traversal, requires auth, and scopes access to the owning user.
