# Migrating VEGA Tree State 1.1

VGTREE can convert the internal VEGA Tree state schema 1.1 to public schema 2.0:

```bash
vgtree migrate-state --input old-state.json --output new-state.json
```

The command never overwrites its source or an existing output. It adds `engine_version`, converts phases and branches, creates typed migration evidence, preserves the workflow reference, and validates the generated state.

Legacy caller-provided gate booleans are not promoted as proof. Legacy free-text evidence is retained as a typed observation or migration reference. After migration, rerun relevant domain and integration checks before completion.

Unsupported versions, malformed input, missing dependencies, or invalid output return controlled JSON failure. Keep the original state until the new state and its real-world outcome have been verified.
