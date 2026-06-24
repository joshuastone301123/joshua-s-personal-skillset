---
name: notion-recap-system
description: "How the user's automated weekly/monthly Notion recaps work, plus the key Notion database and page IDs in their JPOS workspace"
metadata: 
  node_type: memory
  type: project
  originSessionId: 884007b7-c901-4c27-886e-4b03bc3d6c4b
---

User tracks everything they do in a Notion **Tasks [JPOS]** database and in-person events in an **Interactions [JPOS]** database. They want a weekly summary of what they got done + alignment with goals, and a monthly month-end recap with focus areas.

**System built (2026-06-24):** the `notion-recap` skill (`/workspace/.claude/skills/notion-recap/`) gathers data and publishes a recap page. Scheduled tasks drive it:
- "Weekly Recap — Ask (iMessage)" — cron `0 8 * * 1` (Mon 8am ET): gathers prior-week data, texts user 3–4 tailored questions, writes `state/weekly_pending.json` (status awaiting_reply). Does NOT publish.
- Inbound iMessage reply → handled by any triggered session per CLAUDE.md "Interactive Weekly Recap protocol": folds answers in, publishes, texts link.
- "Weekly Recap — Fallback Publish" — cron `0 20 * * 1` (Mon 8pm ET): publishes without answers if still awaiting_reply.
- "Monthly Recap (Notion)" — cron `0 8 1 * *` (1st 8am ET): fully automatic, covers prior month (not interactive).

**Interactive flow chosen by user (2026-06-24):** texting channel = **iMessage**; timing = Mon 8am ask → wait → evening fallback publish. Monthly stays automatic. State + reply contract documented in CLAUDE.md and SKILL.md.

**iMessage integration (connected 2026-06-24):** id `b278b13a-7942-43d3-af9e-673588b1657c`, chat `eea10bb1-0ffa-4292-b257-1fb1c2759287` (+19255886587). Still prefer `list_chat_integrations` at runtime in case IDs change, but this is the active one.

Recaps publish into the **Recaps** database (`389384b2-b53f-8114-bb43-e72b1fc1cd1f`) created under their **Scratchpad** page. User said they'll "likely put a page library" for summaries under Scratchpad — confirm/move if they reorganize.

**Key Notion IDs (account `ea6c6c56-bf38-4c59-a67e-e1748b4031d9`, access via PROXY):**
- Tasks DB: `284384b2-b53f-8108-b609-f26cca6a95f9` (Status incl. "Complete", Date, Category, Urgency, Importance, Contact relation)
- Interactions DB: `284384b2-b53f-815a-8d07-c312141c9e0b` (Type, Date, Contact relation → Contacts, Interaction Notes)
- Contacts DB: `284384b2-b53f-8120-967d-ef2a691dd7e6` (title prop = "Name")
- Goals "I WILL 2026": `2d7384b2-b53f-801b-8710-da9d3b588eab` (areas: Professional, Travel, Health, Social, Personal, Fun)
- Intentions "INTENTION SETTING 2026": `2d7384b2-b53f-80df-91b3-ed07baec08c6`
- "Your People" (priority people to see more): `359384b2-b53f-8096-8a4d-e8abba34a259`
- Scratchpad page: `284384b2-b53f-811a-8680-e366a0ac2df9`

**Why:** recaps are explicitly meant to surface goal alignment and *where to be more focused* — the analysis (not just the data dump) is the point. Health goals were the standout gap in the first week tested (Jun 15–21).

**How to apply:** reference pages are read live each run, so goal edits in Notion flow through automatically. If the user asks for an ad-hoc recap, invoke the `notion-recap` skill directly with `--period` and optional `--ref`.
