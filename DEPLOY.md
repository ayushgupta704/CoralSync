# Deploy opsGaurdian to your own VPS

End-to-end deploy guide. Estimated time: ~45 min on a fresh box. Live
reference: [opsgaurdian.quest](https://opsgaurdian.quest).

## What you'll end up with

A single Ubuntu VPS (DigitalOcean / Vultr / Linode / Hetzner / Lightsail,
4 vCPU / 8 GB / 80 GB is plenty) running:

| Process | Where | Listens on |
|---|---|---|
| Caddy | systemd, auto Let's Encrypt | :80, :443 |
| `opsgaurdian-api` (FastAPI) | systemd, `uv run uvicorn` | 127.0.0.1:8765 |
| `opsgaurdian-investigate` (agent loop) | systemd | PG LISTEN |
| `opsgaurdian-actor` (action executor) | systemd | PG LISTEN |
| `opsgaurdian-prettifier` (event summaries) | systemd | PG LISTEN |
| `opsgaurdian-postgres` | Docker container | 127.0.0.1:5432 |
| Coral binary | spawned by `opsgaurdian-investigate` over MCP stdio | n/a |
| UI (Vite build) | static, served by Caddy | from `/opt/opsgaurdian/opsgaurdian-ui/dist/` |

One domain (`opsgaurdian.quest`) covers everything. UI at `/`, API at
`/api/*`, webhooks at `/webhooks/*`, SSE at `/api/inbox/stream` and
`/api/cases/{id}/events`.

```
┌─────────────────┐
│  opsgaurdian.quest  │  Caddy (TLS, gzip, SSE flush)
└────────┬────────┘
         │ reverse_proxy → 127.0.0.1:8765
         ▼
   ┌─────────────┐         LISTEN/NOTIFY
   │ opsgaurdian-api │ ──────────┬──────────┬──────────┐
   └──────┬──────┘           │          │          │
          │                  ▼          ▼          ▼
          │           investigate    actor    prettifier
          │                  │
          ▼                  ▼ MCP stdio
       Postgres            Coral binary ──► Stripe, HubSpot,
       (Docker)                              Notion, Slack, …
```

---

## 0. Provision the VPS

Pick any Ubuntu 22.04 / 24.04 box with root SSH. Two bootstrap paths:

### A) One-click cloud-init (DigitalOcean, Vultr, Linode)

Paste [`deploy/vps/cloud-init.yaml`](deploy/vps/cloud-init.yaml) into the
provider's "User data" / "Startup script" field. The box installs
Docker, clones the repo into `/opt/opsgaurdian`, writes a placeholder
`.env`, and brings the docker-compose stack up. Three to five minutes.

After it finishes:
```bash
ssh root@<vps-ip>
nano /opt/opsgaurdian/.env       # paste OPENROUTER_API_KEY etc.
docker compose -f /opt/opsgaurdian/docker-compose.yml restart
```

### B) Manual bootstrap

If your provider doesn't have a cloud-init field, SSH in and run:
```bash
curl -fsSL https://raw.githubusercontent.com/ayush-gupta/opsgaurdian/main/deploy/vps/setup.sh | bash
```

This is the same script the cloud-init runs. Idempotent, safe to
re-run if it half-fails.

---

## 1. Postgres (~2 min)

The docker-compose stack starts `opsgaurdian-postgres` (postgres:16-alpine)
on `127.0.0.1:5432`. Schema migrations:

```bash
cd /opt/opsgaurdian
docker exec opsgaurdian-postgres psql -U opsgaurdian -d opsgaurdian \
    -f /docker-entrypoint-initdb.d/001_initial.sql \
    -f /docker-entrypoint-initdb.d/002_event_summary.sql \
    -f /docker-entrypoint-initdb.d/003_policy_engine.sql \
    -f /docker-entrypoint-initdb.d/004_citation_reasonings.sql \
    -f /docker-entrypoint-initdb.d/005_auth_signups.sql
```

(The compose mount makes `opsgaurdian-api/schema/*.sql` available inside
the container at `/docker-entrypoint-initdb.d/`. On first boot they
run automatically; this command is the re-apply path.)

Seed the demo org + members:
```bash
cd /opt/opsgaurdian/opsgaurdian-api
uv run python -m opsgaurdian_api.scripts.bootstrap_dev_org
```

---

## 2. Env vars (~5 min)

The four systemd services all read from `/opt/opsgaurdian/opsgaurdian-api/.env`.
Minimal viable set:

```bash
# ── Database ──────────────────────────────────────────────────────
DATABASE_URL=postgresql://opsgaurdian:<pg-password>@127.0.0.1:5432/opsgaurdian

# ── Agent + Coral ─────────────────────────────────────────────────
OPENROUTER_API_KEY=sk-or-v1-...
OPSGAURDIAN_MODEL=deepseek/deepseek-v4-pro:exacto
CORAL_BINARY=/usr/local/bin/coral

# ── Auth (Clerk) ──────────────────────────────────────────────────
CLERK_SECRET_KEY=sk_test_...
CLERK_PUBLISHABLE_KEY=pk_test_...

# ── Outbound integrations the actor calls directly ────────────────
STRIPE_API_KEY=sk_test_...
HUBSPOT_ACCESS_TOKEN=...
SLACK_TOKEN=xoxb-...
RESEND_API_KEY=re_...
RESEND_FROM_ADDRESS=support@opsgaurdian.quest

# ── Inbound webhook signing ───────────────────────────────────────
STRIPE_WEBHOOK_SECRET=whsec_...
SLACK_SIGNING_SECRET=...
RESEND_INBOUND_WEBHOOK_SECRET=whsec_...

# ── App ───────────────────────────────────────────────────────────
WEB_APP_ORIGIN=https://opsgaurdian.quest
OPSGAURDIAN_ENV=production
```

Note on source credentials: the agent itself does NOT speak to Stripe,
HubSpot, Notion, etc. Coral handles those connections; you configure
them on the Coral side with `coral source add <kind> --token=...`.
The keys above are only the ones the actor (write side) and webhook
verifiers need directly.

After editing the `.env`, restart all four services:
```bash
systemctl restart opsgaurdian-api opsgaurdian-investigate opsgaurdian-actor opsgaurdian-prettifier
```

---

## 3. Caddy + TLS (~3 min)

Caddy ships with the cloud-init / setup.sh path. Drop in the real
domain:

```bash
cp /opt/opsgaurdian/deploy/vps/Caddyfile.example /etc/caddy/Caddyfile
sed -i 's/your-domain.com/opsgaurdian.quest/g' /etc/caddy/Caddyfile
systemctl restart caddy
```

First request to `https://opsgaurdian.quest` triggers Let's Encrypt cert
issuance automatically. The Caddyfile has SSE-friendly settings
already (no proxy buffering, 30-min response timeout) so the inbox
stream + per-case event stream flow through cleanly.

DNS at your registrar:
```
TYPE   NAME              VALUE
A      opsgaurdian.quest     <vps-ip>
A      *.opsgaurdian.quest   <vps-ip>     (optional, only if you use subdomains)
```

---

## 4. UI build + serve (~3 min)

The UI is a Vite static build served by Caddy from
`/opt/opsgaurdian/opsgaurdian-ui/dist/`. Build it locally and rsync up, OR
build on the VPS:

```bash
cd /opt/opsgaurdian/opsgaurdian-ui
npm ci
echo 'VITE_OPSGAURDIAN_API_URL=https://opsgaurdian.quest' > .env.production.local
echo 'VITE_CLERK_PUBLISHABLE_KEY=pk_test_...' >> .env.production.local
npm run build
```

Caddy picks the new `dist/` up on the next request. Hard-refresh your
browser to bust the previous JS bundle's hash.

For iterative deploys from your laptop, the loop we've been using:
```bash
# from your laptop
cd opsgaurdian-ui && npm run build
rsync -avz --delete dist/ root@<vps-ip>:/opt/opsgaurdian/opsgaurdian-ui/dist/
```

---

## 5. Inbound email (~10 min)

In **Resend dashboard**:
1. Add domain `opsgaurdian.quest` and verify SPF + DKIM + DMARC.
2. Enable **Inbound**. Resend gives you the MX record.
3. Create an Inbound Webhook → URL:
   `https://opsgaurdian.quest/api/webhooks/email/acme`
4. Copy the signing secret into `.env` as
   `RESEND_INBOUND_WEBHOOK_SECRET`.

DNS at your registrar:
```
TYPE    NAME                          VALUE
MX      opsgaurdian.quest          10     inbound-smtp.resend.com
TXT     opsgaurdian.quest                 v=spf1 include:resend.com ~all
TXT     resend._domainkey.opsgaurdian.quest    (DKIM value from Resend)
TXT     _dmarc.opsgaurdian.quest          v=DMARC1; p=quarantine; rua=mailto:postmaster@opsgaurdian.quest
```

Verify by sending an email to `support@opsgaurdian.quest` and watching:
```bash
journalctl -u opsgaurdian-api -f | grep email
```

---

## 6. Stripe webhook (~3 min)

In **Stripe Dashboard** (test mode for the demo, live mode in
production):
1. Developers → Webhooks → Add endpoint.
2. Endpoint URL: `https://opsgaurdian.quest/api/webhooks/stripe/acme`
3. Events to send:
   - `charge.dispute.created`
   - `charge.dispute.funds_withdrawn`
   - `charge.dispute.closed`
4. Copy signing secret to `.env` as `STRIPE_WEBHOOK_SECRET`.

Note: the demo flow doesn't actually wait for real Stripe webhooks.
Clicking the Stripe Chargeback card on the inbox seeds a synthetic
`charge.dispute.created` against the seeded Aperture customer. The
webhook is only needed if you wire opsGaurdian against a real Stripe
account.

---

## 7. Slack app (~10 min)

In **api.slack.com → Create New App → From scratch**:
1. App name: `opsGaurdian` (workspace: your demo workspace).
2. **OAuth & Permissions → Bot Token Scopes**:
   - `app_mentions:read`
   - `channels:history` *(needed for the cleanup script that wipes bot messages)*
   - `channels:manage`
   - `channels:read`
   - `chat:write`
   - `groups:read`
   - `im:history`
   - `users:read`
   - `users:read.email` *(critical — used to route inbound mentions to the right opsGaurdian member)*
   - `users:write`
3. **Event Subscriptions → Enable**:
   - Request URL: `https://opsgaurdian.quest/webhooks/slack/<org-slug>/events`
   - Subscribe to bot events: `app_mention`, `message.im`
4. **Interactivity & Shortcuts → Enable**:
   - Request URL: `https://opsgaurdian.quest/webhooks/slack/<org-slug>/interactive`
5. Install to workspace, copy Bot Token + Signing Secret to `.env`.
6. Invite the bot to your demo channel: `/invite @opsgaurdian`

`<org-slug>` is the org slug your demo workspace lives under. For the
public demo it's `acme`; for a single-tenant install it's whatever
slug you bootstrapped.

---

## 8. Coral (~5 min)

The investigate worker spawns a Coral binary over MCP stdio. Install
the binary on the VPS:

```bash
# from the Coral repo's release page or your build:
curl -fsSL https://github.com/withcoral/coral/releases/latest/download/coral-linux-amd64 \
     -o /usr/local/bin/coral
chmod +x /usr/local/bin/coral
```

Then configure Coral's source connections (this is on the Coral side,
not opsGaurdian):
```bash
coral source add stripe --token=sk_test_...
coral source add hubspot --token=...
coral source add notion --token=secret_...
# ...etc per the source you want the agent to investigate against
```

The agent itself reads zero of those tokens. It only knows the path
to the binary (`CORAL_BINARY` env var) and talks to it over MCP.

---

## 9. Verify

```bash
# UI loads
curl -I https://opsgaurdian.quest

# API health
curl https://opsgaurdian.quest/api/me   # should 401 (auth required) - reachable

# Webhook endpoints reachable
curl -X POST https://opsgaurdian.quest/api/webhooks/stripe/acme \
     -H 'Content-Type: application/json' -d '{}'   # 400 (bad sig) is fine, means reachable

# Trigger a demo case from the UI:
#   - sign in via Clerk
#   - click the Stripe Chargeback card on the empty inbox
#   - walk the story slides, click Begin Investigation
#   - watch the case appear in the inbox + agent steps populate live
```

---

## 10. Updating (the actual deploy loop)

For day-to-day changes (the flow we've been using):

```bash
# from the VPS
cd /opt/opsgaurdian
git fetch origin main && git reset --hard origin/main
systemctl restart opsgaurdian-api opsgaurdian-investigate opsgaurdian-actor opsgaurdian-prettifier
```

UI changes also need a rebuild + rsync:
```bash
# from your laptop
cd opsgaurdian-ui && npm run build
rsync -avz --delete dist/ root@<vps-ip>:/opt/opsgaurdian/opsgaurdian-ui/dist/
```

Postgres schema changes: apply manually
```bash
docker exec -i opsgaurdian-postgres psql -U opsgaurdian -d opsgaurdian < migration.sql
```

---

## Troubleshooting

| Symptom | Likely cause |
|---|---|
| CORS errors in browser | `WEB_APP_ORIGIN` mismatch. Must match the host the browser sees (`https://opsgaurdian.quest`, not `https://www.opsgaurdian.quest`). |
| Slack signature 401 | `SLACK_SIGNING_SECRET` wrong, or VPS clock drifted > 5 min. Check `timedatectl`. |
| Slack mention opens case but UI hangs at "Listening" | Demo-v3 wizard polling needs the bot to have `users:read.email`. Without it `mentioned_by_email` is null and the poll never matches. |
| Resend inbound 404 | Webhook URL slug must match an `orgs.slug` row in Postgres. Default is `acme`. |
| Stripe webhook 400 | Signing secret is for the wrong mode (test vs. live). |
| Worker silently does nothing | `journalctl -u opsgaurdian-investigate -n 100`. Most "0 STEPS forever" cases trace to a Pydantic literal_error on `source_surface` or a missing env var. |
| `trigger_payload->>'key'` returns NULL but key is "there" | asyncpg JSONB codec auto-serializes dicts. Don't wrap in `json.dumps()`. The codec will double-encode and the value becomes a JSONB string scalar; first `||` concat flips it to an array. |
| Brief lands in Slack thread saying "No actions drafted" but UI shows 3 | `maybe_notify(brief_drafted)` ordering. Make sure the projection block in investigate.py materializes actions BEFORE the Slack notify fires. |
| `Approved by (autonomous)` on every Slack close card | UI's `/api/cases/{id}/approve` not stamping `slack_signer_display` on `case.trigger_payload`. |

For anything not on this list: `journalctl -u opsgaurdian-<service> -n 200`
on the offending worker is almost always the fastest path.
