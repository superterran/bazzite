#!/bin/bash
set -euo pipefail
# Permit only the Quest hotspot subnet through Docker's forwarding policy.
[[ "${1:-}" == wlp9s0 && "${2:-}" == up ]] || exit 0
iptables -nL DOCKER-USER >/dev/null 2>&1 || exit 0
iptables -C DOCKER-USER -i wlp9s0 -o eno1 -s 10.42.0.0/24 -j ACCEPT 2>/dev/null || iptables -I DOCKER-USER 1 -i wlp9s0 -o eno1 -s 10.42.0.0/24 -j ACCEPT
iptables -C DOCKER-USER -i eno1 -o wlp9s0 -d 10.42.0.0/24 -m conntrack --ctstate RELATED,ESTABLISHED -j ACCEPT 2>/dev/null || iptables -I DOCKER-USER 1 -i eno1 -o wlp9s0 -d 10.42.0.0/24 -m conntrack --ctstate RELATED,ESTABLISHED -j ACCEPT
