# joshua-s-personal

Personal skillset for Joshua Pollak's Gamut agents.

## Layout

```
index.json                              # skillset manifest (required at root)
agents/
  untitled-ahlf8t/
    CLAUDE.md                           # NYC Dance Weekly Briefing agent
```

## Adding this skillset to Gamut

1. Push this repo to GitHub (public or private — if private, Gamut needs access).
2. In Gamut → Settings → Skillsets, paste the repo URL into the "Add skillset repository" input and click **Add**.
3. The agents listed in `index.json` will appear in the Agent Marketplace and can be installed.

## Adding a new agent

1. Create `agents/<slug>/CLAUDE.md` with the agent's standing instructions.
2. Append an entry to `index.json` under `agents`.
3. Commit + push. Refresh the skillset in Gamut.
