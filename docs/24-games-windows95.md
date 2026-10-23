# 24 Games for Windows 95

Steam shortcut: **24 Games for Windows 95**, app ID **3616716904**.
Launcher: `bin/launch-24-games.sh`.
Data: `/var/mnt/fast/shared-games/24-games-windows95/`.

Original Expert Software collection, sourced from https://archive.org/details/24GamesForWindows95 . The ISO's SHA-1 was checked against that item's published metadata. Extracted CD files are under `cd/`; the installed collection's launcher is `cd/WIN/PROGRAM/GAMES.EXE`. The original front-cover image supplies Steam portrait artwork.

These are 16-bit Windows 3.1 applications. Proton 11.0's winevdm launches them successfully in an isolated prefix under `compatdata/`. No Windows OS installation or virtual desktop is used. Steam runs the shell launcher as a native shortcut, which invokes Proton; do not additionally force a compatibility tool on this shortcut. Game Mode/Gamescope handles fullscreen presentation.

Verified in an isolated Xvfb session: the 24-game picker displays correctly; its Run Black Box Chess button launches Black Box Chess with a score window. The test session was closed through that prefix's wineserver, without touching other games. Visible Game Mode presentation still needs user verification. To control this game with a controller, configure its per-game Steam Input mouse layout; the separate menu-only mouse bridge intentionally pauses during games.
