# Artifact Format

Every WebRead artifact includes:

- source URL
- run_id
- fetched_at
- success flag
- HTTP status if available
- source grade
- note
- output paths

The `run_id` makes repeated reads immutable: the same URL read twice on the same day generates separate files.
