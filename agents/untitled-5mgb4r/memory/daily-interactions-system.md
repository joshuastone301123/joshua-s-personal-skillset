---
name: daily-interactions-system
description: "How the end-of-day Notion Interactions enrichment works — finds note-less interactions, asks via iMessage text (voice-to-text OK), confirms entity tags, creates+links, writes notes"
metadata: 
  node_type: memory
  type: project
  originSessionId: 884007b7-c901-4c27-886e-4b03bc3d6c4b
---

**Built 2026-06-24, revised 2026-06-24 after test run.** End-of-day flow to fill in note-less Notion Interactions, driven by an **iMessage TEXT** reply (typed or dictated via iOS voice-to-text). Skill: `/workspace/.claude/skills/daily-interactions/`. Protocol + reply handling in CLAUDE.md ("Daily Interactions enrichment protocol").

**Audio path is DEAD.** iMessage voice-memo bubbles deliver a non-decodable blob through the relay (ftyp header + ~12KB zeros + ~49KB high-entropy data, no recognizable container — likely encrypted at the relay layer). Confirmed by deep-scanning for every audio container marker. No fix from agent side; the iMessage chat provider is a single managed relay with no config. WhatsApp isn't a supported provider; Telegram works but user doesn't want the app switch. **Resolution: skill is text-only.** Voice memo path / `transcribe.py` removed from the skill.

**Flow (current):**
1. 10pm daily job (`Daily Interactions — Ask (iMessage)`, cron `0 22 * * *` ET) runs `find_noteless.py` (today + 7-day stragglers, empty Interaction Notes), texts a numbered list, writes `state/interactions_pending.json` (status `awaiting_details`). Prompt says *"reply by text — voice-to-text is fine, I'll clean it up."*
2. User text reply → session cleans up voice-to-text artifacts (run-ons, dropped punctuation, homophone errors), parses per-interaction plan, runs `enrich_interaction.py --resolve`. **ALWAYS** sets `awaiting_entity_ok` and texts a confirmation listing per-interaction the cleaned note text + the entities to tag, each marked `(existing match)` or `(NEW — will create)`. Confirmation required even when no new records would be created — see [[recap-facts]] / feedback memory: voice-to-text mangles names and the fuzzy resolver will silently bind to the wrong existing contact.
3. On OK → `enrich_interaction.py --apply --create-missing` creates+links entities, writes notes, texts back page URLs. On correction → adjust plan, re-confirm.

**Why these choices (user, 2026-06-24):**
- Texts at 10pm
- Wants to approve entity tags every time (not just new records)
- Include past-7-day stragglers, not just today
- Text-only (forced by audio path being broken; user prefers no app-switching to Voice Memos / WhatsApp / Telegram)

**Entity → DB → Interaction relation:** contacts→Contacts(`...8120`,Name)→Contact; artists→Artists(`...810d`,Artist)→Artist; companies→Companies(`...814b`,Company)→Company; venues→Venues(`284384b2-b53f-81c7-a254-f9c9780673cd`,Venue)→"Venue 1"; areas→Areas(`...814e`,Area)→Area. Interactions DB `284384b2-b53f-815a-8d07-c312141c9e0b`.
