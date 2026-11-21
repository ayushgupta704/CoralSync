<p align="center">
  <a href="https://coralsync.quest">
    <img src="https://coralsync.quest/banner.png" alt="coralSync - the operations layer for revenue disputes" />
  </a>
</p>

<h3 align="center">coralSync</h3>

<p align="center">
  The operations layer for revenue disputes.
  <br />
  Settles chargebacks, refund requests, and failed payments in minutes - not days.
  <br /><br />
  <a href="https://coralsync.quest"><strong>coralsync.quest »</strong></a>
  <br /><br />
  <a href="#about-coralsync"><strong>About</strong></a> ·
  <a href="#how-it-works"><strong>How it works</strong></a> ·
  <a href="#the-coral-data-plane"><strong>Coral</strong></a> ·
  <a href="#sources"><strong>Sources</strong></a> ·
  <a href="#features"><strong>Features</strong></a> ·
  <a href="#quick-start"><strong>Quick start</strong></a> ·
  <a href="#architecture"><strong>Architecture</strong></a> ·
  <a href="#self-hosting"><strong>Self-host</strong></a>
</p>

<p align="center">
  <a href="https://github.com/ayush-gupta/coralsync/blob/main/LICENSE"><img src="https://img.shields.io/badge/License-Apache_2.0-blue.svg" alt="License"></a>
  <a href="https://github.com/ayush-gupta/coralsync/stargazers"><img src="https://img.shields.io/github/stars/ayush-gupta/coralsync?style=flat&logo=github" alt="Stars"></a>
  <a href="https://github.com/ayush-gupta/coralsync/pulse"><img src="https://img.shields.io/github/commit-activity/m/ayush-gupta/coralsync?style=flat&logo=github" alt="Commits per month"></a>
  <a href="https://github.com/ayush-gupta/coralsync/issues?q=is%3Aissue+is%3Aopen+label%3A%22help+wanted%22"><img src="https://img.shields.io/badge/PRs-welcome-brightgreen.svg" alt="PRs welcome"></a>
</p>


## About coralSync

coralSync is the autonomous investigator for B2B SaaS billing operations. The moment a chargeback hits Stripe, a refund request lands in your support inbox, or a teammate `@-mentions` coralSync in Slack, the agent reads across **every connected system in one query**, drafts a **cited decision brief**, and queues the right actions for one-click human approval.

A senior analyst spends 5 hours on a chargeback. coralSync spends 3 minutes.

The work happens on top of [**Coral**](https://github.com/withcoral/coral) - a unified Postgres-compatible SQL surface over 11 SaaS schemas. Instead of integrating 11 vendor SDKs and stitching results in Python, the agent writes one wide `SELECT` that joins Stripe + Salesforce + HubSpot + Intercom + Zendesk + Slack + Notion + PostHog + Sentry + Datadog + PagerDuty, gets one rowset back, and grounds every claim in the brief with a citation that links back to the underlying record. Click any citation chip and the source dashboard opens to the exact row.

## How it works

| Stage | What happens |
|---|---|
| **1 · Trigger** | Stripe webhook fires · customer email lands at support@ · teammate `@-mentions` coralSync in Slack. The agent picks it up the moment the event lands. |
| **2 · Investigate** | The agent issues 3-6 Coral queries to pull every relevant fact in parallel, surfaces findings with citations, and emits a live narrative you can watch in real time. |
| **3 · Brief** | A two-paragraph executive memo with the math shown, every number cited back to a source record. |
| **4 · Decide** | Recommends refund / fight / partial-credit / escalate, then **drafts the actions** (Stripe refund, dispute response, customer email, HubSpot note, Slack post). |
| **5 · Approve** | One click. Each action fires against the real systems in a sequential cinematic - refund posts to Stripe, email lands in the inbox, HubSpot note appears, Slack pings. |

## Sources


| Schema | Tables used | What it grounds in the brief |
|---|---|---|
| `stripe`     | `disputes`, `charges`, `customers`, `subscriptions`, `refunds`, `invoices` | Payment + dispute facts, prior-dispute counts, subscription health |
| `salesforce` | `accounts`, `opportunities`, `contacts` | Customer-tier + revenue context |
| `hubspot`    | `companies`, `contacts`, `deals`, `notes` | ARR, tier, owner, prior notes |
| `intercom`   | `conversations`, `contacts` | Support history, recent subjects |
| `zendesk`    | `tickets`, `users` | Open tickets, priority history |
| `slack`      | `channels`, `messages` | Internal mentions, ops-channel context |
| `notion`     | `pages`, `blocks` | Policy docs, runbooks, post-mortems |
| `posthog`    | `events`, `persons` | Feature-usage signals during the disputed window |
| `sentry`     | `events`, `issues` | App errors correlated with the customer's session |
| `datadog`    | `incidents`, `metrics` | Service outages during the disputed window |
| `pagerduty`  | `incidents`, `users` | On-call history + ack/resolve timestamps |

**Write / action adapters** - hit by the actor worker after operator approval, implemented natively (not via Coral) so we can return real `external_ref` IDs and idempotency keys:

| Adapter | Action |
|---|---|
| `stripe`  | `POST /v1/refunds`, `POST /v1/disputes/{id}/evidence` |
| `resend`  | `POST /emails` (templated, branded HTML; table-based for Outlook/Gmail compat) |
| `hubspot` | `POST /crm/v3/objects/companies/{id}/notes` |
| `slack`   | `chat.postMessage` to `#billing-ops` |
| `notion`  | Append resolution block to the case page |
| `linear`  | Open an issue when the agent escalates (low-confidence or out-of-policy cases) |

When an upstream rejects an action (Stripe `charge_disputed`, Slack `channel_not_found`, etc.) the action is recorded as `failed` in the audit trail with the verbatim error; we never synthesize a success ref. The parallel actions still fire — e.g. the partial credit lands via `stripe_dispute_response` even when `stripe_refund` is rejected on a disputed charge.

## Features

- 🧠 **One-query investigations.** Coral exposes 11 SaaS schemas as Postgres-compatible SQL. The agent writes wide joins across them in a single round-trip, never per-source lookups.
- 📑 **Cited brief.** Every claim in the postmortem carries a citation chip linking back to the underlying record (Stripe dispute, Notion page, Datadog incident). No fabrication - if it's in the brief, it's in a source.
- 🔴 **Live investigation cinematic.** Watch the agent query each source in real time, with brand glyphs inline in the narrative ("coralSync is asking 🟢 Intercom") and a running list of facts. Toggle the Coral panel to see the raw SQL feed.
- ✋ **Human-in-the-loop approval.** Operator reviews the brief, approves with one click, watches each action fire in a full-screen cinematic with per-action status and external-ref deep-links back to the source record (real Stripe refund / Resend email / HubSpot note / Slack ts).
- ✉️ **Branded customer emails.** Templated HTML emails (table-based for Outlook/Gmail compat) with summary cards, branded header, and policy-grounded reasoning - never the raw decision rationale.
- 🔒 **Per-user workspace isolation.** Every Clerk-authenticated user gets their own isolated org. Two operators can run investigations in parallel against the same demo data without seeing each other's cases.
- 📖 **Editorial UI.** The whole product reads like a magazine spread - Spectral serif, hairline rules, brand-colored source pills, Geist Mono for the data - not a SaaS dashboard.

## Quick start

### Prerequisites
- Node 20+ · `pnpm` or `npm`
- Python 3.12+ · [`uv`](https://github.com/astral-sh/uv)
- Docker (for the local Postgres)
- The [Coral binary](https://github.com/withcoral/coral) built and on your `PATH` (or available at `./coral/target/release/coral`)

### Setup
```sh
git clone https://github.com/ayush-gupta/coralsync
cd coralsync

# 1 · Environment - fill in OPENROUTER_API_KEY, CORAL_BINARY,
#                   STRIPE_API_KEY, RESEND_API_KEY, HUBSPOT_ACCESS_TOKEN,
#                   SLACK_TOKEN, NOTION_TOKEN, CLERK_*
cp .env.example .env
cp coral-sync-api/.env.example coral-sync-api/.env
cp agent/.env.example agent/.env

# 2 · Database
docker compose -f coral-sync-api/docker-compose.yml up -d postgres

# 3 · Backend (API + 3 workers)
cd coral-sync-api && uv sync
uv run uvicorn coral_sync_api.main:app --reload --port 8765 &
uv run python -m coral_sync_api.workers.investigate &
uv run python -m coral_sync_api.workers.actor        &
uv run python -m coral_sync_api.workers.prettifier   &

# 4 · Frontend
cd ../coral-sync-ui && npm install && npm run dev
```

Visit **[http://localhost:5173](http://localhost:5173)**, sign in via Clerk, then click **Stripe Chargeback** on the empty-inbox hero to fire the canonical Aperture demo (an $8,400 dispute that resolves to a $560 partial credit).

## Architecture

```
       │  Stripe / Email / Slack
       │  webhook · inbound · @-mention
       ▼
┌────────────────────────────────────────────────────────────────┐
│   coral-sync-api  ·  FastAPI + asyncpg                            │
│   • cases / events / findings / actions  (per-org PG schema)   │
│   • per-Clerk-user workspace isolation                         │
│   • SSE streams: /api/inbox/stream, /api/cases/:id/stream      │
└──────────────┬─────────────────┬────────────────┬──────────────┘
               │                 │                │
               ▼                 ▼                ▼
        ┌────────────┐    ┌────────────┐   ┌────────────┐
        │ investigate│    │   actor    │   │ prettifier │
        │   worker   │    │   worker   │   │   worker   │
        │            │    │            │   │            │
        │ runs agent │    │ executes   │   │ summarizes │
        │ loop, draft│    │ approved   │   │ tool calls │
        │ brief +    │    │ actions    │   │ for the    │
        │ findings   │    │ idempotently│  │ live trace │
        └─────┬──────┘    └─────┬──────┘   └────────────┘
              │                 │
              ▼                 ▼
       ┌────────────┐    ┌──────────────────────┐
       │   Coral    │    │  Action adapters     │
       │ (MCP/stdio)│    │  • Stripe · refunds  │
       │            │    │  • Stripe · disputes │
       │ 11 SaaS as │    │  • Resend · emails   │
       │  pg-SQL    │    │  • HubSpot · notes   │
       │ (read-only)│    │  • Slack  · posts    │
       │            │    │  • Notion · blocks   │
       │            │    │  • Linear · issues   │
       └────────────┘    └──────────────────────┘
```

## Tech stack

**Frontend** · [React 19](https://react.dev) + [Vite](https://vite.dev) + [TypeScript](https://typescriptlang.org) · [Tailwind v4](https://tailwindcss.com) · [motion/react](https://motion.dev) · [Clerk](https://clerk.com) auth · deployable to Vercel or a static host.

**Backend** · [FastAPI](https://fastapi.tiangolo.com) + [asyncpg](https://github.com/MagicStack/asyncpg) · [PostgreSQL](https://www.postgresql.org) (cases, events, findings, actions) · 3 background workers (`investigate`, `actor`, `prettifier`) coordinated via `FOR UPDATE SKIP LOCKED`.

**Agent** · `agent/` is a ~hundreds-of-LOC Python loop (no framework) over the [OpenAI-compat](https://platform.openai.com/docs/api-reference) client pointed at [OpenRouter](https://openrouter.ai). Tools: `coral_sql`, `coral_list_catalog`, `coral_describe_table` (read, via Coral MCP) and `record_finding`, `ask_human`, `conclude`, `amend_brief` (in-loop, no external side effects). See [`agent/README.md`](./agent/README.md) for the full tool surface + loop walkthrough.

**Data plane** · [Coral](https://github.com/withcoral/coral) - Rust binary, MCP/stdio bridge, 11 SaaS schemas as Postgres SQL.

**Models** (all via OpenRouter)
- Investigator + chat: `x-ai/grok-build-0.1`
- Tool-call summarizer (the live "prettifier"): `inception/mercury-2`
- Story-image generation: `google/gemini-3.1-flash-image-preview`

**External services** · [Stripe](https://stripe.com) (payments + disputes) · [Resend](https://resend.com) (transactional + inbound email) · [HubSpot](https://hubspot.com) (CRM notes) · [Slack](https://slack.com) (ops notifications) · [Notion](https://notion.so) (policy + resolution blocks) · [Linear](https://linear.app) (escalation issues).

## Self-hosting

coralSync ships as 1 API + 3 workers + a Postgres + a Vite static frontend + the Coral subprocess. Single-box VPS deploy is the supported path - Caddy + cloud-init + a small setup script bring up the whole stack on one Ubuntu box. This is what runs at [coralsync.quest](https://coralsync.quest). Full walkthrough in [`DEPLOY.md`](./DEPLOY.md).

## Contributing

Issues and PRs welcome. Before pushing:

- `cd coral-sync-ui && npm run typecheck`
- `cd coral-sync-api && uv run pytest`
- `cd agent && uv run pytest`

Keep PRs scoped to a single concern; we squash-merge.

## License

Apache 2.0 - see [`LICENSE`](./LICENSE). The hosted version at [coralsync.quest](https://coralsync.quest) ships the same code with managed Coral connections, OAuth onboarding, and Clerk-issued workspaces.

---

<sub>Built by <a href="https://ayush-gupta.com">ayush-gupta</a> · Made with 🪸 Coral</sub>
