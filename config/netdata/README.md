# Netdata — real-time temps/fans + thermal alerting

Added 2026-06-03 after repeated thermal lockups (the quiet AIO fan curve was
starving the radiator; see `bin/fan-curve.sh`). Netdata gives a live dashboard
and DMs Slack when the cooling is actually in trouble.

- **Dashboard (LAN):** http://10.0.0.226:19999  (no auth, no cloud needed —
  dismiss the "Sign in to Netdata Cloud" nag; the local charts are behind it)
- **Service:** `config/systemd/user/netdata.service` (Docker, systemd --user)
- **Container config persists** in the named Docker volumes `netdataconfig`,
  `netdatalib`, `netdatacache`. The files below are the repo copies of what
  lives in `netdataconfig`.

## Alarms (`health.d/aio-thermal.conf`)

Tuned to the *runaway signature*, not normal heat — a 9950X hits 95 °C by
design under load, so we only alarm on **sustained** pinning:

| Alarm | Fires when | Why |
|-------|-----------|-----|
| `cpu_tctl_pinned` | Tctl 2-min avg > 96 °C (warn > 90) | coolant runaway / AIO not coping |
| `aio_pump_stopped` | pump (`fan7`) < 500 RPM | catastrophic — coolant not circulating |

## Slack delivery (`health_alarm_notify.append.conf`)

The notify config's `custom_sender()` posts alarms as a DM via Slack
`chat.postMessage`, reusing the OpenClaw bot token from closet's
`gmail-watcher`. The block is **appended** to the stock
`/etc/netdata/health_alarm_notify.conf` (last-definition-wins) and the role
override must come *after* the stock `role_recipients_*` arrays.

**The token is NOT in this repo.** It lives only in the container at
`/etc/netdata/slack-thermal.env` (mode 0600, in the `netdataconfig` volume),
which is `.gitignore`'d. To (re)provision it:

```bash
# one-time, copies the existing bot token from closet into the volume — never printed
ssh closet 'docker exec gmail-watcher sh -lc "printf \"SLACK_BOT_TOKEN=%s\nSLACK_TARGET=%s\n\" \"\$SLACK_BOT_TOKEN\" \"\$SLACK_TARGET\""' \
  | docker exec -i netdata sh -c 'umask 077; cat > /etc/netdata/slack-thermal.env'
```

`SLACK_TARGET=U0AELPY5KHV` is Doug's Slack user id → alarms arrive as a DM.

## Reproduce from scratch

```bash
just deploy-services                          # installs netdata.service
systemctl --user enable --now netdata.service
# copy health rule + notify snippet into the netdataconfig volume:
docker exec -i netdata sh -c 'cat > /etc/netdata/health.d/aio-thermal.conf' < health.d/aio-thermal.conf
docker exec -i netdata sh -c 'cat >> /etc/netdata/health_alarm_notify.conf' < health_alarm_notify.append.conf
# provision the token (see above), then:
docker exec netdata netdatacli reload-health
# test: docker exec netdata /usr/libexec/netdata/plugins.d/alarm-notify.sh test sysadmin
```
