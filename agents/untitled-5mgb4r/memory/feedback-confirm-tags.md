---
name: feedback-confirm-tags
description: "For daily-interactions and similar entity-tagging flows: ALWAYS confirm proposed entity tags with the user before writing; for NEW records, also list the available fields so the user can fill what they know"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 04d57ce5-8cf8-4618-b7d4-6307a7a8fd7c
---

For daily-interactions (and any Notion-write flow that tags entities from a parsed user message), **always confirm the entity tags back to the user before writing** — not just when new records would be created.

**Why:** User often replies via iOS voice-to-text. Voice-to-text reliably mangles names ("Sicoli" → "second oli", "Gurwitz" → "Gerwood"). The fuzzy entity resolver will happily pair a mangled name with the wrong existing contact, and the bad tag lands in Notion silently. The user explicitly asked for a confirmation step on every run, calling out names as the failure mode.

**When proposing NEW records, also surface the available fields** so the user can provide what they know. They told me explicitly: *"If you are creating a new page for Artist, Company, Contact, Venue, etc, make sure to tell me all the details I should provide. I won't always provide every single one, I'll tell you what I can."* Don't force them to know what fields exist.

**Field menus by entity type (JPOS Notion):**
- **Contact**: Name *(req)*, Email, Phone, Profile (URL), Title (job title), Status, Industry, Job, Interest, Birthday
- **Artist**: Artist *(req)*, Genre, Website, Streaming Link
- **Company**: Company *(req)*, Industry, Service, Status, Website, Description
- **Venue**: Venue *(req)*, Address, Capacity, Website
- **Area**: Area *(req)* only

**How to apply:**
- In daily-interactions: after `enrich_interaction.py --resolve`, always set `awaiting_entity_ok` and text back the per-interaction plan (cleaned note text + each tagged entity marked existing/NEW + the field menu for each NEW). Wait for OK before applying. See [[daily-interactions-system]].
- For any future skill that tags entities in Notion from natural-language input: same pattern. Resolve → confirm (with field menu for NEWs) → write.
- Clean up voice-to-text input (punctuation, run-ons, dropped articles, homophones) before parsing — that's the agent's job, not the user's.
