# Hyde local Linux Actions runner

Private repository-scoped runner for hatcher-ltd/hyde, label hyde-linux.
No host Docker socket, credentials, LAN listeners or unrelated host folders are mounted.
Only the runner working directory is persisted; GitHub supplies environment secrets to the selected job.
The pinned GitHub runner archive is SHA-256 verified. The Playwright image supplies matching browser dependencies, avoiding apt installs in jobs.

Deploy: docker compose build && docker compose up -d. Enroll once through config.sh using a short-lived GitHub repository registration token on stdin/environment; never commit or print the token. Restart the service after enrollment. The runner credentials remain private in the UID10001 state folder.

GitHub-hosted jobs are not a fallback. A missing local runner queues work and uses no hosted compute. One service job runs at a time; backups, recovery and production environment gates remain in Actions.
