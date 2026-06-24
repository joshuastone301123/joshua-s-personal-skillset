# NYC Dance Weekly Briefing — Setup

When this agent is first installed on a new machine, the following are NOT carried over by the skillset (they're per-agent platform state, not files). The agent should bootstrap them on first run, or the user can request "run setup" and the agent walks through each item.

## 1. Connected Account: Notion

The briefing publishes to the Notion **Dance Knowledge Hub** parent page (ID: `340384b2-b53f-8008-91ed-fc77aac34858`) in Joshua Pollak's workspace.

Bootstrap step:
- Call `mcp__user-input__request_connected_account` with `toolkit: "notion"` and reason `"Allow access to Notion to publish the weekly NYC dance music briefing as a child page of the Dance Knowledge Hub?"`.
- After the user grants it, the account appears in `CONNECTED_ACCOUNTS` env var.

## 2. Secret: NOTION_API_TOKEN

The CLAUDE.md instructions specifically call out using the **native Notion API** (not the Composio OAuth proxy, which returned 502s) with the internal integration token "Suepragent".

Bootstrap step:
- Call `mcp__user-input__request_secret` with `secretName: "NOTION_API_TOKEN"` and reason `"Add NOTION_API_TOKEN so the agent can publish the weekly briefing directly via the native Notion API?"`.
- Token is saved to `/workspace/.env`.

## 3. Scheduled Task: Weekly Briefing

The briefing runs weekly, covering Mon–Sun of the upcoming week. Typical schedule: Sunday evening.

Bootstrap step:
- Call `mcp__user-input__schedule_task` with:
  - `scheduleType: "cron"`
  - `scheduleExpression: "0 18 * * 0"` (every Sunday at 6 PM local time — adjust to taste)
  - `prompt: "Produce this week's NYC dance music briefing per CLAUDE.md and publish it as a child page of the Dance Knowledge Hub."`
  - `name: "Weekly NYC Dance Briefing"`

## 4. (Optional) Trigger: RA News

If you want to be notified of breaking dance-music news between scheduled runs, set up a webhook trigger on the connected account. Most likely not needed — the weekly cron is sufficient.

## How to run setup

After installing the agent on a fresh machine, message it:

> Run setup from SETUP.md — request the Notion connection, request the NOTION_API_TOKEN secret, and schedule the weekly briefing.

The agent should iterate through sections 1–3 above using the listed tools.
