# Sage — Setup

When this agent is first installed on a new machine, the following platform state is not carried over by the skillset. Bootstrap on first run, or the user can say "run setup" to walk through each item.

## 1. Connected Account: Notion

Sage publishes weekly discovery briefings to Notion (typically as child pages of the Dance Knowledge Hub).

Bootstrap:
- Call `mcp__user-input__request_connected_account` with `toolkit: "notion"` and reason `"Allow access to Notion to publish the weekly dance music discovery briefing?"`.

## 2. Secret: NOTION_API_TOKEN

Briefings post directly via the native Notion API (the Composio OAuth proxy returned 502s on this workspace).

Bootstrap:
- Call `mcp__user-input__request_secret` with `secretName: "NOTION_API_TOKEN"` and reason `"Add NOTION_API_TOKEN so Sage can publish briefings via the native Notion API?"`.

## 3. Chat Integration: Telegram (Dance Music Discovery)

After each Notion publish, Sage pushes a teaser to Josh's Telegram via the **Dance Music Discovery** integration. See `memory/reference_weekly_discovery_telegram_delivery.md` for the locked format.

Bootstrap:
- Ask Josh for the Telegram bot token (from @BotFather) if not already configured.
- Call `mcp__chat__add_chat_integration` with `provider: "telegram"` and the bot token. Name it "Dance Music Discovery".

## 4. Scheduled Task: Weekly Discovery

Typical schedule: Monday morning.

Bootstrap:
- Call `mcp__user-input__schedule_task` with:
  - `scheduleType: "cron"`
  - `scheduleExpression: "0 9 * * 1"` (Mondays 9 AM local — adjust to taste)
  - `prompt: "Compile this week's dance music discovery briefing per CLAUDE.md and memory, publish to Notion, then push the Telegram teaser."`
  - `name: "Weekly Discovery"`

## How to run setup

After installing the agent on a fresh machine, message Sage:

> Run setup from SETUP.md — request the Notion connection, add the NOTION_API_TOKEN secret, configure the Telegram chat integration, and schedule the weekly discovery.

Sage should iterate through sections 1–4 above using the listed tools.
