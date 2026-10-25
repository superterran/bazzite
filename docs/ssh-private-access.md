# Desktop SSH through Tailscale

Verified2026-10-25. SSH remains on2222 with existing key authentication. Public/WAN SSH is retired; HTTP/MCP tunnel routes stay public.

- `desktop.superterran.net` is now an unproxied A record for100.119.114.55, preserving the hostname used by existing SSH shortcuts. It requires Tailscale connectivity. No Cloudflare SSH ingress existed in either the desktop or Closet tunnel.
- Runtime and permanent firewalld: allow2222 in moonlight-tailnet (tailscale0), permit LAN IPv4 10.0.0.0/24, remove the unrestricted physical-zone port, and explicitly drop non-LAN IPv4 / all physical-interface IPv6 on2222. LAN IPv4 and tailnet IPv4/IPv6 remain separate paths.
- cloudflare-ddns.timer disabled/stopped; oneshot service stopped. Legacy ssh-remote-access.sh and firewall-hardening.sh now call ssh-private-access.sh rather than recreating WAN/DDNS access. Credentials retained in their existing protected location; do not print or commit them.
- Closet-scoped authorized keys now accept only10.0.0.75 or the same host’s tailnet IP100.101.167.38.
- Authenticated SSH succeeded from Closet using both100.119.114.55 and desktop.superterran.net after cutover; a fresh LAN SSH login also succeeded. Public-source firewall rules were inspected; an independent off-LAN SSH probe was not performed.
- Xfinity router forwarding settings were not edited. Any old port2222 forward is blocked at the desktop firewall; remove the redundant router forward separately when router administration is available.
- Desktop Tailscale DNS acceptance enabled and closet.tail3758dd.ts.net resolves to100.101.167.38.
- Both Cloudflare tunnel configurations compared exactly equal before/after the DNS change. Unauthenticated public MCP HTTP probes returned403; no authenticated MCP session test was performed. No MCP routes or CNAME records were changed.

Canonical policy: desktop.d/ssh-private-access.sh. DNS record ca38a9d219e852ce87f8b88caac4f357 in the superterran.net zone is private SSH alias state; retire DDNS before changing it. Re-running the private SSH setup preserves the firewall policy and keeps DDNS disabled.
