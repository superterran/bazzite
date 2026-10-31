#!/bin/sh
# Dropbear lacks OpenSSH's from= option. Gate Closet's recovery key explicitly.
set -eu
case "${SSH_CONNECTION%% *}" in
    10.0.0.75|100.101.167.38) ;;
    *) echo 'This recovery key is restricted to Closet.' >&2; exit 1 ;;
esac
if [ -n "${SSH_ORIGINAL_COMMAND:-}" ]; then
    exec /bin/sh -c "$SSH_ORIGINAL_COMMAND"
fi
exec /bin/sh -l
