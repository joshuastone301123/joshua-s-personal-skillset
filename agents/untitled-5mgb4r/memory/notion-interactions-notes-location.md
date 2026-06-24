---
name: notion-interactions-notes-location
description: "For Interactions [JPOS] in Notion, 'notes' live in the page BODY (child blocks), not in the 'Interaction Notes' rich_text property — read and write to the body, not the property"
metadata: 
  node_type: memory
  type: project
  originSessionId: 04d57ce5-8cf8-4618-b7d4-6307a7a8fd7c
---

When dealing with the Notion **Interactions [JPOS]** database (`284384b2-b53f-815a-8d07-c312141c9e0b`), **notes live in the page BODY (child blocks), not in the "Interaction Notes" rich_text property.** The property exists in the schema but the user doesn't populate it.

**Why this matters:**
- "Has notes?" cannot be answered by querying `Interaction Notes is_empty: true` — that returns false positives. You must fetch each candidate page's children.
- "Has child blocks" is ALSO not the only signal: Notion AI meeting notes are stored as `transcription` block type with empty `rich_text` (real content nested under children). So checking only "any block with non-empty rich_text" gives false negatives on AI-noted meetings. `transcription` and `ai_block` types should be treated as "has notes" without inspecting their text.
- When writing notes back to an interaction, append a paragraph block to the page body (via `POST /v1/blocks/{page_id}/children`) — do NOT set the property.

**How to apply:**
- `daily-interactions` skill (`/workspace/.claude/skills/daily-interactions/`) was originally built against the property and corrected on 2026-06-24. `find_noteless.py` now reads page children; `enrich_interaction.py --notes` now appends a paragraph block.
- For any future flow touching Interactions [JPOS] notes: same pattern. Page body = source of truth.
- Other Notion DBs in this workspace may use rich_text properties for notes — this rule is specific to Interactions [JPOS]. Verify the user's pattern before assuming the same for another DB.

Related: [[daily-interactions-system]], [[notion-recap-system]].
