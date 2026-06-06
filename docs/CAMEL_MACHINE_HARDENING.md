# THE CAMEL — Machine Hardening Checklist (S6, founder actions)

> **Canonical home for the founder-only machine setup.** These steps are NOT code and cannot
> be unit-tested — they are things you do once on the Windows PC that runs The Camel. The
> S6 *code* (dashboard, Telegram, secrets manager, heartbeat, log rotation, weekly checks,
> off-box archive) is in the repo and tested; this is the rest of the S6 gate.
>
> A money-controlling, remotely-reachable machine is a target. Do these **before Phase 1**.

---

## 1. Identity & access

- [ ] **Dedicated non-admin OS user** for The Camel (not your daily login). The loop runs as this user.
- [ ] **MFA on every account**: broker (Alpaca), GitHub, OpenAI/Anthropic, Supabase, email, Telegram.
- [ ] **No inbound ports** open to the public internet.
- [ ] **OS-level config immutability (S6.6).** The code already proves the agent has no *write path*
      to `config/limits.yaml` (`config_guard`), but defence-in-depth means the **OS** should enforce it
      too: set NTFS permissions so the Camel's OS user has **read-only** on the `config/` directory
      (deny Write/Modify). Then a motivated adversarial prompt can't write an adjacent file to redirect
      config loading. Verify: as the Camel user, attempt to edit `config/limits.yaml` → permission denied.
- [ ] **Dead-man's-switch (S6.6).** Create a free external check (e.g. healthchecks.io) and set
      `CAMEL_DEADMAN_URL`; the EOD loop pings it via `ops/deadman.py`. A missed ping (power cycle, forced
      Windows Update restart, sleep, logout) alerts you — the internal health monitor can't, since it
      isn't running when the box is down.

## 2. Tailscale (private remote access + the kill switch path)

- [ ] Install Tailscale; join the PC and your phone/laptop to the tailnet.
- [ ] **Lock the ACL** to your devices only (no sharing, no exit-node exposure).
- [ ] Verify you can SSH/remote in from your phone and run the kill switch:
      `python ops/kill_switch.py halt`  → loop halts on the next tick (Constitution also
      blocks every action while the `config/HALT` flag exists).
      `python ops/kill_switch.py resume` → restored.
- [ ] Confirm the halt works **end-to-end over Tailscale** (this is the S6 gate item).

## 3. Disk & machine

- [ ] **BitLocker** full-disk encryption ON.
- [ ] Windows automatic security updates ON; firewall ON; screen-lock ON.
- [ ] **UPS / power backup** on the PC (a clean shutdown beats a corrupt DB).
- [ ] **5G / hotspot fallback** internet (so the EOD loop and alerts survive an outage).

## 4. Secrets (migrate off plaintext .env)

- [ ] Install `keyring` (`pip install keyring`) so `ops/secrets_manager.get_secret` uses the
      **Windows Credential Manager** under the service name `the-camel`.
- [ ] Move ALPACA / OpenAI / Anthropic / Supabase keys out of `.env` into Credential Manager.
- [ ] Turn on the **hard refusal**: call `ops.secrets_manager.enforce_startup(strict=True)` at
      startup — it raises `PlaintextSecretError` if any sensitive key is still a plaintext env var.
- [ ] Broker key scoped **trade-only, withdrawals disabled** (re-confirm at the broker).

## 5. Backups

- [ ] Local verified backup runs in the weekly check (`ops/scheduled_checks.run_weekly_checks`).
- [ ] **Off-box encrypted** copy: `ops/archive.archive_backup` makes a single `.zip`; push it
      off-machine with an **encrypted** transfer (rclone crypt / restic / an encrypted volume).
      Never ship the raw zip off-box unencrypted.
- [ ] Test a **restore** at least once (`ops/backup.restore`) and confirm the suite still runs.

## 6. Windows Task Scheduler entries

- [ ] **EOD loop** — `python loop/scheduler.py` ~30 min after US close (set `CAMEL_DB_DIR`, `CAMEL_PHASE=0`).
- [ ] **Weekly checks** — a task that runs `ops/scheduled_checks.run_weekly_checks` (kill-switch
      self-test + verified backup + reconciliation), result logged to `op_log`.
- [ ] **Daily report** — `alerts/daily.send_daily_report` after close (Telegram once the bot
      token + chat id are in Credential Manager; until then it logs the report text).
- [ ] **Heartbeat** — the loop calls `ops/heartbeat.beat` each tick; alert if it goes stale.

## 7. Recovery runbook (write it down, keep it offline)

- [ ] "Key leaked / machine compromised" → revoke broker + API keys, `tailscale down`, halt the loop.
- [ ] Where the encrypted backups live and how to restore them.
- [ ] How to reach the kill switch from your phone if the PC is unreachable.

---

**S6 gate (combined code + machine):** kill switch stops the next tick (verified over
Tailscale); daily-loss-stop simulation halts (tested); dashboard reflects a paper trade
(tested); weekly kill-switch test passes (tested); backup restore verified (tested); secrets
not in plaintext (enforced once §4 is done on the machine).
