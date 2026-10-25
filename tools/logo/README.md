# Logo and illustration generator

The Haqdar logo, app icon and illustrations are drawn by these scripts. The Urdu lettering is converted
to plain vector paths, so it looks the same on every device and the website needs no font.

## Regenerate

1. Download **Noto Nastaliq Urdu** (variable font, SIL Open Font License) and save it in this folder as
   `NotoNastaliqUrdu.ttf`:
   https://github.com/google/fonts/tree/main/ofl/notonastaliqurdu
2. Install the tools: `pip install fonttools uharfbuzz pillow`
3. From the project root run:

python tools/logo/build_logo.py # logo.svg, logo-light.svg, logo-stacked.svg, logo-mark.svg, icon.svg
python tools/logo/build_art.py # hero.svg, spot-ask.svg, spot-notice.svg
python tools/make_icons.py # PNG app icons
python tools/build_pages.py # index.html, ask.html, notice.html, about.html


## Licence note

The font is not committed to the repository. Its licence is in `docs/third-party/NotoNastaliqUrdu-OFL.txt`.
Credit the Noto Project Authors in the README acknowledgements.