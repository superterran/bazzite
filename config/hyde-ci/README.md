# Hyde local Linux Actions runner

Repository-scoped runner for `hatcher-ltd/hyde`, label `hyde-linux`, on desktop.
The canonical files live in `superterran/bazzite`. A rootless Podman container mounts only its private working state, not the host Docker socket, personal home, credentials or unrelated folders. There are no inbound listeners. GitHub injects selected environment secrets per job, and a runner-owned completion hook removes rendered deployment scratch and plan files.

Provision/update with `bash desktop.d/50-hyde-ci.sh`. Enroll once with `config.sh` using a short-lived repository registration token passed through stdin/environment; never print or commit it. The state is private in `~/.local/share/hyde-ci/service`, UID10001 inside the container. Restart the service after enrollment. The initial runner archive is pinned and SHA-256 verified; the official matching Playwright image supplies browser dependencies.

Check `systemctl --user status hyde-ci-linux`, `podman logs hyde-ci-linux`, and the repository Actions runner page. Linger is enabled on desktop. Verify the runner is idle before restarting it for maintenance. No other user services need a restart. Its container is limited to four CPUs and six GiB and has no additional privileges.

GitHub-hosted jobs are not a fallback. A missing local runner queues work and uses no hosted compute. One job runs at a time. Backups, recovery and production environment gates remain in Actions. Guide artifacts have short retention; encrypted backups retain their existing thirty-day policy. GitHub artifact storage has its own allowance, independent of free self-hosted compute. Desktop must be online for schedules to execute.
