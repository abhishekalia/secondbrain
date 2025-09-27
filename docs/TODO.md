# TODO (Claude starter)

## Voice/Prompt
- Tighten `core/prompt.py` to enforce one-liner default, bullets only if asked.
- Add a “Next step:” line only when helpful.

## Memory
- Create SQLite index for `memories.jsonl` (schema: id, ts, type, text, tags).
- Add embedding pipeline; store vectors in Qdrant; query top-k; inject.

## Retrieval
- Hybrid score = BM25(text, query) + α * cosine(vector, query).
- Cap total injected context at 800–1200 chars.

## Reliability
- Expand `doctor.sh` with model tag check, Docker health.
- Add unit tests for empty reply, error surfacing.

## UI
- Toggle: “strict one-liner” on/off.
- Button: “append to journal” → writes to `memories.jsonl`.

## Docs
- Update README with memory commands and examples.
