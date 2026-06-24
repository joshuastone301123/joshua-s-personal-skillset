# Weekly Monthly Recap Agent — Setup

When installed on a fresh machine, the following are NOT carried over by the skillset (they're per-agent platform state, not files). On first run the agent should bootstrap each item, or the user can say "run setup" and the agent walks through them.

## 1. Connected Account: Notion

The agent reads from and writes to multiple Notion databases in Joshua Pollak's workspace (JPOS): Tasks, Interactions, Contacts, Artists, Companies, Venues, Areas, Recaps.

Bootstrap step:
- Call `mcp__user-input__request_connected_account` with `toolkit: "notion"` and reason `"Allow access to Notion to read tasks/interactions and publish weekly + monthly recaps?"`.

## 2. Connected Account: Google Calendar (optional)

Used as a data source for recaps (events attended, meetings).

Bootstrap step:
- Call `mcp__user-input__request_connected_account` with `toolkit: "googlecalendar"` and reason `"Allow access to Google Calendar so recaps can reference events attended?"`.

## 3. Chat Integration: iMessage

Both the weekly recap and the daily interactions protocols send and receive iMessage. Without this, the agent has no way to ask questions or receive replies.

Bootstrap step:
- Call `mcp__chat__list_chat_integrations` to check if iMessage is already wired up.
- If not, call `mcp__chat__list_available_chat_providers` to see what iMessage needs, then `mcp__chat__add_chat_integration` once the user supplies the relay details.

## 4. Scheduled Task: Daily Interactions ask (10 PM daily)

Each evening, looks for note-less Interactions from today + last 7 days, texts the user a numbered list asking who was there.

Bootstrap step — call `mcp__user-input__schedule_task` with:
- `scheduleType: "cron"`
- `scheduleExpression: "0 22 * * *"` (10 PM daily, local time)
- `prompt: "Run the daily-interactions skill: find note-less Interactions for today + the last 7 days, and if any exist, text the user a numbered list per the daily-interactions protocol in CLAUDE.md."`
- `name: "Daily Interactions Ask"`

## 5. Scheduled Task: Weekly Recap ask (Monday 8 AM)

Gathers the prior week's tasks/interactions, texts the user 3–4 tailored questions, and stores `weekly_pending.json`.

Bootstrap step — call `mcp__user-input__schedule_task` with:
- `scheduleType: "cron"`
- `scheduleExpression: "0 8 * * 1"` (Mondays at 8 AM)
- `prompt: "Run the notion-recap skill in interactive mode: build the weekly digest, ask the user 3-4 tailored questions via iMessage, and store weekly_pending.json per CLAUDE.md."`
- `name: "Weekly Recap Ask"`

## 6. Scheduled Task: Weekly Recap fallback (Monday 8 PM)

If the user never replied to the morning's questions, publish the recap anyway and text the link.

Bootstrap step — call `mcp__user-input__schedule_task` with:
- `scheduleType: "cron"`
- `scheduleExpression: "0 20 * * 1"` (Mondays at 8 PM)
- `prompt: "Run the notion-recap skill fallback: if weekly_pending.json is still awaiting_reply, publish the recap without answers, mark published_no_reply, and text the user the page URL."`
- `name: "Weekly Recap Fallback"`

## 7. (Optional) Scheduled Task: Monthly Recap

Bootstrap step — call `mcp__user-input__schedule_task` with:
- `scheduleType: "cron"`
- `scheduleExpression: "0 9 1 * *"` (1st of the month, 9 AM)
- `prompt: "Run the notion-recap skill in monthly mode: build a recap of the prior month, publish to the Recaps DB, and text the user the link."`
- `name: "Monthly Recap"`

## 8. Memory files

`memory/*.md` in this agent dir contains seed memory (Notion DB IDs, recap facts, daily-interactions notes, feedback rules). On first run, copy them into the agent's live memory:

```
mkdir -p /workspace/.claude/projects/-workspace/memory
cp agents/untitled-5mgb4r/memory/*.md /workspace/.claude/projects/-workspace/memory/
```

(Or: the agent can read them in place and write a fresh MEMORY.md index as it learns.)

## How to run setup

After installing on a fresh machine, message the agent:

> Run setup from SETUP.md — request Notion + Google Calendar, set up iMessage chat, schedule the daily-interactions and weekly + monthly recap jobs, and seed memory from `memory/`.

The agent should iterate through sections 1–8 above using the listed tools, asking the user to approve each grant/connection.

## Inbound iMessage routing

CLAUDE.md already documents the routing rule: before treating an inbound iMessage as ordinary chat, the agent checks the two pending-state files (`.claude/skills/notion-recap/state/weekly_pending.json` and `.claude/skills/daily-interactions/state/interactions_pending.json`) and disambiguates by content + recency. No platform-side trigger setup is required — Gamut already creates a session for each inbound message via the chat integration.
