# CPU/GPU temperature overlay

Disabled at the user's request on2026-10-31. The custom MangoApp environment
override was removed, the session hook was made inert, and its source line was
removed from the live Game Mode session configuration. General setup can source
the inert hook without re-enabling the overlay.

The running MangoApp was replaced with the normal Steam-controlled instance using
the original temporary configuration containing no_display. Game Mode, Steam and
games were not restarted. A transient mangoapp-native-overlay user unit manages
this replacement and is bound to the current Game Mode service; future Game Mode
sessions use the normal built-in MangoApp supervisor.

The former temperature layout remains archived in config/temperature-overlay.conf
for reference. Original pre-customization config remains at
~/.local/state/hardware-monitor/overlay-before.conf. Native Steam performance
overlay controls remain available.
