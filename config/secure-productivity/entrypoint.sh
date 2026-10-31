#!/bin/sh
set -eu
umask 077
ulimit -c 0
mkdir -p /run/xrdp
/usr/sbin/xrdp-sesman --nodaemon &
exec /usr/sbin/xrdp --nodaemon --config /etc/xrdp/secure-productivity.ini
