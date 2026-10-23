#!/usr/bin/env bash
set -euo pipefail
export XDG_RUNTIME_DIR="${XDG_RUNTIME_DIR:-/run/user/$(id -u)}"
export DISPLAY=:20
export XAUTHORITY="${XDG_RUNTIME_DIR:-/run/user/$(id -u)}/chrome-private/Xauthority"
unset WAYLAND_DISPLAY
for ((attempt=0; attempt<40; attempt++)); do
    if xprop -root >/dev/null 2>&1; then break; fi
    sleep .25
done
case "${1:?select wm, browser, vnc or sunshine}" in
    wm)
        export LD_LIBRARY_PATH="$HOME/.local/opt/chrome-private/usr/lib64${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"
        export XDG_DATA_DIRS="$HOME/.local/opt/chrome-private/usr/share:/usr/share"
        exec "$HOME/.local/opt/chrome-private/usr/bin/openbox" --sm-disable --config-file "$HOME/repos/bazzite/config/chrome-private/openbox.xml"
        ;;
    browser)
        profile="$HOME/.var/app/com.google.Chrome/config/chrome-tv-automation"
        mkdir -p "$profile"
        chmod 700 "$profile"
        exec flatpak run --nosocket=pulseaudio --filesystem=xdg-run/chrome-private/pulse \
            --env=PULSE_SERVER="unix:${XDG_RUNTIME_DIR}/chrome-private/pulse/native" \
            com.google.Chrome --user-data-dir="$profile" \
            --remote-debugging-address=127.0.0.1 --remote-debugging-port=9223 \
            --ozone-platform=x11 --window-position=0,0 --window-size=1920,1080 \
            --start-maximized --no-first-run --no-default-browser-check \
            --disable-background-mode --restore-last-session
        ;;
    vnc)
        exec "$HOME/.local/opt/chrome-private/usr/bin/x11vnc" -display :20 -auth "$XAUTHORITY" \
            -localhost -rfbport 5905 -forever -shared -nopw -noxdamage -quiet
        ;;
    sunshine)
        export XDG_SEAT=seat-browser
        export PULSE_SERVER="unix:${XDG_RUNTIME_DIR}/chrome-private/pulse/native"
        exec /usr/bin/sunshine "$HOME/.config/sunshine-browser/sunshine.conf"
        ;;
    audio)
        export DBUS_SYSTEM_BUS_ADDRESS=unix:path=/run/dbus/system_bus_socket
        export PULSE_RUNTIME_PATH="${XDG_RUNTIME_DIR}/chrome-private/pulse"
        mkdir -p "$PULSE_RUNTIME_PATH"
        chmod 700 "$PULSE_RUNTIME_PATH"
        exec /home/linuxbrew/.linuxbrew/bin/pulseaudio --daemonize=no --use-pid-file=no \
            --exit-idle-time=-1 --disable-shm=yes --log-target=stderr -n \
            --load="module-native-protocol-unix socket=$PULSE_RUNTIME_PATH/native auth-anonymous=1" \
            --load="module-null-sink sink_name=browser channels=2 rate=48000"
        ;;
    *) exit 2 ;;
esac
