---
name: Notion Recap
description: Generate weekly or monthly recaps from the JPOS Notion Tasks and Interactions databases, analyze how completed work and logged interactions align with the 2026 goals / intentions / "Your People" list, and publish the recap as a page in the Notion "Recaps" database. Use for "weekly recap", "monthly recap", "month-end review", "what did I get done", "how am I tracking against my goals".
metadata:
  version: "1.0.0"
---

# Notion Recap

Produces a goal-aligned recap of a period (prior week or prior month) from the
user's Notion workspace and publishes it as a page.

## Architecture

Two scripts + an analysis step done by the agent:

1. **`recap_data.py`** — deterministic data collection. Pulls completed Tasks
   and all Interactions from Notion, **plus all Google Calendar events** from
   both the personal (`josh.pollak365@gmail.com`) and work
   (`josh@joshuapollak.com`) calendars for the period. Resolves contact
   relations to names, detects which of the "Your People" the user actually
   spent time with, and loads the *live* Goals / Intentions / Your People
   reference pages. Emits one JSON object on stdout. Calendar events land
   under `calendar_events.{personal,work}` and are the source of truth for
   routines, gym/movement, and recurring habit blocks (Music Discovery Monday,
   Why Not Wednesday, Sunday planning, etc.) — these are NOT in Notion.
2. **Agent analysis** — read the JSON, write a narrative recap in Markdown:
   what got done, who they saw, alignment with each goal area, and an honest
   "where to be more focused" section (call out goal areas with zero activity).
3. **`publish_recap.py`** — converts the Markdown to Notion blocks and creates a
   page in the **Recaps** database (under the Scratchpad page).

## Usage

Always run with uv and the env file (proxy token + base come from `.env`):

```bash
# 1. Gather data (weekly = prior Mon–Sun; monthly = prior calendar month)
uv run --env-file /workspace/.env --with requests \
  /workspace/.claude/skills/notion-recap/recap_data.py --period weekly > /tmp/digest.json
# optional: --ref YYYY-MM-DD to compute relative to a specific date

# 2. Read /tmp/digest.json, then write the narrative recap to /tmp/recap.md.
#    Markdown supported: # ## ### headings, "- " bullets, "1." numbers,
#    "> " quotes, "---" divider, "[ ]/[x]" todos, **bold**, *italic*.
#    NOTE: Markdown tables are NOT supported — use bullets instead.

# 3. Publish
uv run --env-file /workspace/.env --with requests \
  /workspace/.claude/skills/notion-recap/publish_recap.py \
  --title "Weekly Recap — Jun 15–21, 2026" \
  --type Weekly --start 2026-06-15 --end 2026-06-21 \
  --tasks 12 --interactions 17 --body /tmp/recap.md
```

## Recap content guidance

- Lead with totals (tasks completed, interactions, plus a one-line read of routine adherence from calendar) and a one-line theme.
- "What you got done" — group completed tasks by theme (business, travel, personal). Add a "Recurring structure" sub-section from `calendar_events` for routines and weekly habit blocks (Music Discovery Monday, Why Not Wednesday, Sunday planning, morning/evening routines).
- "Who you spent time with" — highlight `your_people_seen` (priority people) first; family is a separate notable group even though family members aren't on the Your People list.
- "How it aligns with your 2026 goals" — map activity to the goal areas (Professional, Travel, Health, Social, Personal, Fun). Use `calendar_events` to detect gym/movement before declaring Health a blank — gym is on calendar, not Notion.
- "Where to focus" — explicitly name goal areas with **no** activity this period; reference Intentions where relevant. Be honest, not flattering.
- Monthly recaps: same structure but synthesize trends across the weeks, note progress on annual goals, and give 2–3 focus priorities for the next month.

### Hard facts to respect (also stored in auto-memory `recap-facts.md`)

- **KPMG is already left.** Never frame "Leave KPMG" as in-progress, even though it still appears in the Goals page.
- **"Show up for the people you care about"** = Your People list **plus family**, and specifically means showing up *when tired or didn't want to go*. Frame the intention that way, not as any social time.
- **Raw Cuts team roster:** Rachel Silva, Joseph Sicoli, Gavin Parisi, Cal Green, Molly Jackson, Erez Davids, James Casino, Ariel Fine, Doran Dyer, Jess, Will, and Josh. Interactions tag everyone present at a shoot, but only call these names "Raw Cuts" — others are collaborators on a shoot, not team members.
- **Do NOT suggest tracking eating / sleep / gym in Notion** — he won't follow through. For habits, read the **calendar** instead. The calendar IS the habit-tracking system.

## Key IDs (JPOS Notion)

- Account: `ea6c6c56-bf38-4c59-a67e-e1748b4031d9`
- Tasks DB: `284384b2-b53f-8108-b609-f26cca6a95f9`
- Interactions DB: `284384b2-b53f-815a-8d07-c312141c9e0b`
- Goals (I WILL 2026): `2d7384b2-b53f-801b-8710-da9d3b588eab`
- Intentions: `2d7384b2-b53f-80df-91b3-ed07baec08c6`
- Your People: `359384b2-b53f-8096-8a4d-e8abba34a259`
- Recaps DB (output): `389384b2-b53f-8114-bb43-e72b1fc1cd1f`

Override any ID via env vars `NOTION_ACCOUNT_ID` / `RECAPS_DB_ID` if the workspace changes.

## Interactive weekly flow (iMessage)

The weekly recap is two-phase so it can incorporate the user's own input:

- **Mon 8am "ask" job** runs `recap_data.py`, saves the digest to
  `state/weekly_digest.json`, composes 3–4 questions tailored to the week's
  data (especially goal areas with zero activity), writes
  `state/weekly_pending.json` (`status: "awaiting_reply"` + the questions), and
  texts the questions via iMessage.
- **User's iMessage reply** lands in a fresh session. Per `CLAUDE.md`, that
  session checks `weekly_pending.json`; if `awaiting_reply`, it treats the
  message as answers, folds them into the narrative (user input > inferred
  reads), publishes, sets `status: "published"`, and texts back the page URL.
- **Mon 8pm fallback job** publishes without answers if still `awaiting_reply`
  (`status: "published_no_reply"`).

State file `state/weekly_pending.json` shape:
```json
{"status":"awaiting_reply|published|published_no_reply",
 "label":"Jun 15–Jun 21, 2026","start":"2026-06-15","end":"2026-06-21",
 "tasks_completed":12,"interactions":17,
 "questions":["..."],"digest_path":".../state/weekly_digest.json",
 "asked_at":"2026-..."}
```

When publishing from answers, weave responses into the relevant sections (a
strong highlight leads the recap; an off-DB health activity corrects the
"where to focus" section).

## Notes

- "Done" tasks = Status **Complete** with a **Date** inside the period.
- Interactions are matched by **Date**; future-dated planned events are excluded.
- Reference pages are read live each run, so editing goals in Notion updates future recaps automatically.
