#!/bin/bash
# Firewall hardening for bazzite-desktop
#
# Problem this fixes: the FedoraWorkstation zone ships with a blanket
# "ports: 1025-65535/tcp 1025-65535/udp" allow on the LAN interface. Because the
# Xfinity router forwards port 2222 to this host, anything else that happens to
# be forwarded (now or later) on a high port is wide open to the internet, and
# every service is reachable by every device on the LAN.
#
# Approach: keep the high-port range, but scope it to the LAN subnet via rich
# rules. Ports that genuinely need to face the internet are allowed explicitly.
# This preserves Steam Remote Play, Sunshine, NFS ancillary (statd/lockd) ports
# and mDNS on the LAN while removing the internet-facing blanket.
#
# Rollback:
#   sudo firewall-cmd --permanent --zone=FedoraWorkstation --add-port=1025-65535/tcp
#   sudo firewall-cmd --permanent --zone=FedoraWorkstation --add-port=1025-65535/udp
#   sudo firewall-cmd --reload

set -euo pipefail

ZONE="FedoraWorkstation"
LAN="10.0.0.0/24"

echo "Hardening firewalld zone: $ZONE"

fw() { sudo firewall-cmd --permanent --zone="$ZONE" "$@" >/dev/null; }

# --- 1. LAN keeps the full high-port range (Steam, Sunshine, NFS statd, mDNS, netdata) ---
for proto in tcp udp; do
    rule="rule family=\"ipv4\" source address=\"$LAN\" port port=\"1025-65535\" protocol=\"$proto\" accept"
    if sudo firewall-cmd --permanent --zone="$ZONE" --query-rich-rule="$rule" >/dev/null 2>&1; then
        echo "  = LAN high-port $proto rule already present"
    else
        fw --add-rich-rule="$rule"
        echo "  + LAN high-port $proto rule added"
    fi
done

# --- 2. Ports that must stay reachable from the internet ---
# 2222/tcp  : SSH (pubkey-only, PerSourcePenalties enabled — see sshd_config.d/03-bruteforce.conf)
# 22000     : Syncthing sync protocol (authenticated + encrypted; direct beats relay)
# 21027/udp : Syncthing local discovery
# NOTE: do not guard these with --query-port. While the blanket 1025-65535 range
# is still present, query-port reports these as already open (range containment),
# so the explicit entries never get added — and step 4 then removes the range,
# closing SSH from the internet. --add-port is idempotent, so just always run it.
for p in 2222/tcp 22000/tcp 22000/udp 21027/udp; do
    fw --add-port="$p"
    echo "  + port $p open (internet-facing, intentional)"
done

# --- 3. File sharing restricted to the LAN (was open to any source) ---
# SMB/NFS exposed to the internet is the classic home-lab disaster. Every client
# for these is on the LAN, so scope them there.
for svc in samba nfs nfs3 mountd rpc-bind; do
    rule="rule family=\"ipv4\" source address=\"$LAN\" service name=\"$svc\" accept"
    if sudo firewall-cmd --permanent --zone="$ZONE" --query-rich-rule="$rule" >/dev/null 2>&1; then
        echo "  = $svc LAN rule already present"
    else
        fw --add-rich-rule="$rule"
        echo "  + $svc restricted to $LAN"
    fi
    if sudo firewall-cmd --permanent --zone="$ZONE" --query-service="$svc" >/dev/null 2>&1; then
        fw --remove-service="$svc"
        echo "  - $svc removed from any-source services"
    fi
done

# --- 4. Drop the blanket high-port allow (must come last) ---
for p in 1025-65535/tcp 1025-65535/udp; do
    if sudo firewall-cmd --permanent --zone="$ZONE" --query-port="$p" >/dev/null 2>&1; then
        fw --remove-port="$p"
        echo "  - blanket $p removed"
    else
        echo "  = blanket $p already removed"
    fi
done

echo "Reloading firewalld..."
sudo firewall-cmd --reload >/dev/null
echo "Done."
echo
sudo firewall-cmd --zone="$ZONE" --list-all
