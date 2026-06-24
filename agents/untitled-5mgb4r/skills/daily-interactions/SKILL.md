---
name: Daily Interactions
description: End-of-day enrichment of Notion Interactions [JPOS] that have no notes yet. Finds note-less interactions (today + recent stragglers), texts the user via iMessage to ask who was there and what to note, cleans up text replies (including voice-to-text), resolves people/venues/companies/artists against their databases, ALWAYS confirms the entity tags back to the user before writing, then creates any new records + links and writes the notes. Use for "log my interactions", "fill in interaction notes", end-of-day interaction prompts.
metadata:
  version: "1.1.0"
---

# Daily Interactions

Turns the day's note-less Interactions into fully-noted, fully-linked records,
driven by **text replies over iMessage** (typed or voice-to-text dictated).

> **Note on audio:** iMessage voice-memo bubbles deliver a non-decodable blob
> through the relay. We don't try to transcribe those server-side. Users dictate
> with iOS voice-to-text instead; the agent's job is to clean up the resulting
> text (punctuation, fragmented thoughts) and — critically — confirm any names
> that got mangled by voice-to-text before writing to Notion.

## Scripts

1. **`find_noteless.py`** — Interactions with empty notes whose Date is today or
   within the trailing `--days` window (default 7). Returns JSON split into
   `today` and `stragglers`, each item with id/title/date/type/existing_contacts.
2. **`enrich_interaction.py`** — resolve + apply, one interaction at a time:
   - `--resolve` → report matched vs **missing** entities per type (no writes).
   - `--apply --create-missing` → create the missing records, link ALL named
     entities (merging with existing relations), set notes. Prints page URL.
   - Entity flags: `--contacts --artists --companies --venues --areas`
     (comma-separated names) and `--notes`.

Entity → database → interaction-relation map:

| Flag | Database | Title | Relation prop |
|---|---|---|---|
| `--contacts` | Contacts [JPOS] | Name | Contact |
| `--artists` | Artists [JPOS] | Artist | Artist |
| `--companies` | Companies [JPOS] | Company | Company |
| `--venues` | Venues | Venue | Venue 1 |
| `--areas` | Areas | Area | Area |

### Fields available per entity (for NEW records)

When a NEW record is being created, the confirmation step must surface the
available fields so the user can fill in what they know (they won't always
provide everything — that's fine; just title is required). Only Name/Artist/
etc. is required by Notion; the rest are optional.

- **Contact** (NEW): Name *(required)*, Email, Phone, Profile (URL — IG/LinkedIn),
  Title (job title text), Status [Cold/Prospect/Contacted/Engaged/Client/Partner/
  Vendor/Defunct DNC/Friend/Family/Colleague/Date/Romantic], Industry [19 opts],
  Job [94 opts], Interest [72 opts], Birthday
- **Artist** (NEW): Artist *(required)*, Genre [18 opts], Website, Streaming Link
- **Company** (NEW): Company *(required)*, Industry [Marketing/Music/Tax/Accounting/
  Artist Management/Event Production/Food and Beverage/Fashion/Tech/Creative],
  Service [17 opts], Status [Cold/Prospect/Contacted/Engaged/Client/Partner/Vendor/
  Defunct DNC/Sponsor], Website, Description
- **Venue** (NEW): Venue *(required)*, Address, Capacity (number), Website
- **Area** (NEW): Area *(required)* — name only

Currently `enrich_interaction.py --apply --create-missing` only sets the title
field. To capture other fields the agent can either (a) write them itself via
the Notion API in the same session before linking, or (b) prompt the user to
fill them in Notion after — explicitly tell them which fields were collected
and which were left blank.

## Daily flow (state machine)

State lives in `state/interactions_pending.json`. Statuses:
`awaiting_details` → `awaiting_entity_ok` → `done`.

1. **10pm "ask" job**: run `find_noteless.py`. If `total == 0`, send nothing and
   exit. Otherwise write state (`status: awaiting_details`, the items list,
   `asked_at`) and text the user a numbered list of the note-less interactions,
   asking for each: who was there + anything to note. Phrasing should say
   *"reply by text — voice-to-text is fine, I'll clean it up."* Do **not**
   prompt for voice memos (the iMessage audio path is broken upstream).
2. **Reply (awaiting_details)** — a fresh session per CLAUDE.md:
   - **Clean up the reply first.** Voice-to-text input often comes in as a
     wall of run-on text with no punctuation, dropped articles, and homophone
     errors. Normalize it before parsing.
   - Parse the reply into a per-interaction plan: for each listed interaction,
     the people/artists/companies/venues/areas mentioned + the note text.
   - Run `enrich_interaction.py --resolve` per interaction. Capture BOTH
     matched-existing entities and missing entities.
   - **ALWAYS confirm with the user before writing.** This is the critical
     step — voice-to-text mangles names ("Sophie Gerwitz" → "Sophie Garwood",
     "Sicoli" → "second oli") and the fuzzy resolver will happily pair the
     mangled name with the wrong existing contact. Set
     `awaiting_entity_ok` and text the user a confirmation message that lists,
     per interaction:
       - The proposed **note text** (post-cleanup)
       - The **entities to tag**, grouped by type, marking each as
         `(existing match)` or `(NEW — will create)`
     For each `(NEW — will create)` record, also list the **available fields**
     for that entity type (see "Fields available per entity" below) and ask
     the user to provide what they can. They won't always have every field —
     just title is required. Capture whatever they give back and write it on
     create.
     Ask them to reply OK, or correct anything that's wrong. This applies even
     when no new records would be created.
3. **Reply (awaiting_entity_ok)**:
   - On approval: for each interaction run `enrich_interaction.py --apply
     --create-missing` with the stored plan. Collect the returned page URLs.
     Set `done`. Text the user the list of updated pages to review + a summary
     of what was created.
   - On correction: adjust the plan (e.g. drop a record, rename, re-map a
     person), re-resolve, and re-confirm. Repeat until they approve.
   - If the inbound message is clearly unrelated to the prompt, handle it
     normally and leave the pending state untouched.

## Notes

- **"Notes" = page body content (child blocks), NOT the "Interaction Notes"
  property.** The user keeps interaction notes in the page body. `find_noteless.py`
  fetches each candidate page's children and checks for any non-empty text
  block. `enrich_interaction.py --notes "..."` appends a paragraph block to the
  page body — it does NOT write to the Interaction Notes property.
- Only interactions dated on/before today are surfaced (no future planned events).
- New records are created with just their title/name unless the user provides
  additional field values in the confirmation step; capture whatever they give.
  Always list what was created in the review message.
- Reuse `list_chat_integrations` at runtime for the iMessage integration/chat ID.
