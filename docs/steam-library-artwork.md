# Steam library artwork refresh — 2026-11-01

User-directed changes on desktop:

- Secure Desktop3716438448: shipped GNOME50 Adwaita light background and official
  GNOME foot paths, white. Portrait600x900, wide920x430, hero1920x620, icon512.
  Regenerate/apply with bin/setup-secure-desktop-artwork.py. Inputs are installed
  gnome-backgrounds50.0 and /usr/share/icons/gnome-logo-text.svg.
- Mahjongg3219622495 and Solitaire(Aisleriot)3865387876: native application icons,
  green tabletop palette, title-safe portrait/wide/hero and512px icons. Apply
  with bin/setup-card-game-artwork.py. Scalable Mahjongg icon rasterized at300DPI.
- Adventure Log3911467097, Aisle Be Back2725390766, Hardware Monitor4235516157:
  new generated colorful cartoon key art, with separate portrait and wide
  compositions. Full titles visually inspected before applying. Generated
  masters and exports live in config/illustrated-steam-artwork. Hero/icon
  exports match. Transparent custom logo suppresses older flat logo overlays.
  Apply all with bin/apply-library-artwork.py. Hardware setup prefers these
  reviewed assets instead of regenerating its previous technical flat covers.
- Moon Mission3937440644: portrait now fits the full existing pixel title-screen
  image within600x900 with matching black padding, so MOON MISSION is not clipped.
- 24 Games for Windows95 3616716904: original full box scan fitted within600x900
  on white; EXPERT, Native Windows95 and the G in GAMES remain fully visible.
  Conflicting old portrait JPG archived so Steam has one active portrait file.
  Both fitted originals/exports are in config/fitted-library-artwork. No AI
  recreation of publisher logos or replacement of the original packaging.

Source art was visually inspected, then Steam's SetCustomArtworkForApp API used
for live refresh and standard per-user grid files written for persistence.
Previous art backed up under ~/.local/state/steam-artwork-refresh. Existing
artwork synchronization exports changes by title, preserving each machine's
shortcut IDs. User confirmation of the final live library appearance is pending.

Removed through Steam's live RemoveShortcut API, with identity checks:
1Password4154030664, Chrome - TV & Automation3789767895, and both Dusklight IDs
2323161660/3802447962. Their application/game files and background automation
services were not removed. Shortcut/art backups are under
~/.local/state/steam-shortcut-retirement/20261101-114508. Saved per-host policy
~/.config/retired-steam-shortcuts.json prevents the respective setup scripts
from recreating those titles; BAZZITE_RESTORE_RETIRED_SHORTCUTS=1 is an explicit
restore override. Other machines without that policy are unchanged.

Artwork work did not request any encrypted-home unlock. Steam/Game Mode
and Sunshine were not restarted. Current artwork does not alter any game save,
controller layout, application installation or encrypted desktop customization.

24 Games refinement: user requested the original box elements arranged to fill
its tall card, rather than square scan floating in white padding. Created a
reference-based image edit: Expert at upper left, complete Windows95 triangle
at upper right, larger24GAMES/FORWINDOWS95 center, blue Ultimate Game Pack/CDROM
banner near bottom. Reviewed wording and full edges before applying600x900.
This later revision is AI-recomposed from the original scan; the original scan
and previous fitted version remain in source/history. Apply helper now uses the
reviewed recomposed master so later setup does not restore the padded layout.
