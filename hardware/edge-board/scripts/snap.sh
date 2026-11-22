#!/bin/sh
# snap.sh BOARD.kicad_pcb OUT.png [layers] [extra kicad-cli args]  -> 2D plot via PDF + pdftoppm, cropped to the drawing
B="$1"; O="$2"; L="${3:-F.Cu,B.Cu,Edge.Cuts,F.Fab}"; X="$4"
T="${O%.png}"
"/c/Program Files/KiCad/9.0/bin/kicad-cli.exe" pcb export pdf --layers "$L" --mode-single $X -o "$T.pdf" "$B" >/dev/null || exit 1
pdftoppm -r 600 -png -singlefile "$T.pdf" "$T" && rm -f "$T.pdf" && python - "$O" <<'PY'
import sys
from PIL import Image, ImageChops
im = Image.open(sys.argv[1]).convert('RGB')
bb = ImageChops.difference(im, Image.new('RGB', im.size, (255, 255, 255))).getbbox()
if bb:
    im = im.crop((max(bb[0] - 20, 0), max(bb[1] - 20, 0), bb[2] + 20, bb[3] + 20))
im.save(sys.argv[1]); print(sys.argv[1], im.size)
PY
