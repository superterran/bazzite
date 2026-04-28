# bazzite repo — System Automation for bazzite-desktop

This repository is the **infrastructure-as-code source of truth** for the bazzite-desktop machine.
Systemd services, helper scripts, config templates, and setup automation all live here.

GitHub: `superterran/bazzite`
Local clone: `~/repos/bazzite/`

---

## What Lives Here

| Path | Purpose |
|------|---------|
| `bin/` | Scripts executed by systemd services (e.g. `vault-watch-push.sh`) |
| `common.d/` | Idempotent setup scripts that run on all machines (Flatpaks, Claude CLI, etc.) |
| `desktop.d/` | Idempotent setup scripts for the desktop only |
| `handheld.d/` | Idempotent setup scripts for handheld devices (ROG Ally) |
| `config/systemd/user/` | **Source of truth** for all `~/.config/systemd/user/` service and timer files |
| `config/` | Config file templates for all services |
| `justfile` | Task runner — see below |

---

## Key Workflows

### Capture live service changes into the repo
When you edit a service file directly in `~/.config/systemd/user/`, pull it back into the repo:

```bash
just capture-services
```

This copies all `*.service` and `*.timer` files from `~/.config/systemd/user/` into `config/systemd/user/`.

### Deploy repo service files to the live system
After editing service files in the repo:

```bash
just deploy-services
```

This copies all units from `config/systemd/user/` to `~/.config/systemd/user/` and reloads systemd.

### Full machine setup (fresh install or re-apply)
```bash
just setup           # auto-detects desktop vs handheld
just desktop-setup   # force desktop
```

Runs all `common.d/` then `desktop.d/` scripts in lexical order. Scripts are idempotent — safe to re-run.

---

## Adding a New Service

1. Write the unit file in `config/systemd/user/my-service.service`
2. If the service needs a helper script, add it to `bin/` and make it executable
3. Create `desktop.d/my-service.sh` using the existing scripts as a template — it should:
   - Install any required deps
   - Copy service files from `$REPO_ROOT/config/systemd/user/`
   - Run `systemctl --user daemon-reload && systemctl --user enable --now my-service.service`
4. Run `just deploy-services` to apply immediately

---

## Script Rules

- **Idempotent**: check before acting — skip if already done
- **No hardcoded secrets**: reference `~/.env` or environment variables only
- **Heredocs for inline configs are discouraged**: put configs in `config/` instead
- **`set -euo pipefail`** at the top of every script
- **ExecStart scripts belong in `bin/`**, not embedded in the vault or home directory

---

## Relationship to Other Systems

| System | Relationship |
|--------|-------------|
| `~/Documents/Cloud Vault/` | Obsidian vault — personal notes and agent context. **Not** where service scripts live. |
| `~/.config/systemd/user/` | Live systemd units. Sourced from this repo via `just deploy-services`. |
| `~/.claude/CLAUDE.md` | Symlinked from vault machine profile. Documents overall machine context. |
| `~/repos/wellbeing-mcp/` | Separate repo for wellbeing MCP server — has its own service file tracked here. |
| `~/repos/mcpvault-remote/` | Separate repo for mcpvault SSE bridge — service tracked here. |

---

## Service File Registry

All live services on this machine should have a corresponding file in `config/systemd/user/`.
Run `just capture-services` any time a new service is created outside this repo.

To see what's live but not yet captured:
```bash
diff <(ls ~/.config/systemd/user/) <(ls config/systemd/user/)
```

---

## justfile Reference

```bash
just setup                # Run common.d + desktop.d setup scripts
just capture-services     # Pull live ~/.config/systemd/user/ → config/systemd/user/
just deploy-services      # Push config/systemd/user/ → live + systemctl daemon-reload
just backup-config        # Snapshot full system config (Flatpaks, RPMs, dconf, etc.)
just setup-ally           # Run setup on ROG Ally via SSH
```
