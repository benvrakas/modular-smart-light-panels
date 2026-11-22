#!/bin/sh
# Regenerate every WP 1.6 output: STLs, PNGs and the film cut template.
# Run from Git Bash in mechanical/panel:   sh make_all.sh        (about 10-15 min)
# Square/triangle outputs (not rev A, unchecked) are written to stl/square, stl/triangle.
set -e
cd "$(dirname "$0")"
S="/c/Program Files (x86)/OpenSCAD/openscad.com"
mkdir -p stl stl/square stl/triangle png
run() { "$S" "$@" 2>&1 | grep -E "WARNING|ERROR|assert" || true; }

# ---------------- STL (print orientation) ----------------
run -o stl/frame.stl          -D 'part="print"' frame.scad
run -o stl/back_plate.stl     -D 'part="print"' back_plate.scad
run -o stl/plug.stl           -D 'part="plug"'  back_plate.scad
run -o stl/wall_puck.stl      wall_puck.scad
run -o stl/bridge_carrier.stl bridge_carrier.scad
for h in 3 6 10; do run -o stl/riser_$h.stl -D 'part="riser"' -D riser_h=$h diffuser.scad; done
run -o stl/bezel.stl          -D 'part="bezel"' diffuser.scad
run -o film_template.dxf      -D 'part="film"'  diffuser.scad
run -o film_template.svg      -D 'part="film"'  diffuser.scad

for n in 4 3; do
  d=$([ $n = 4 ] && echo square || echo triangle)
  run -o stl/$d/frame.stl      -D n_sides=$n -D 'part="print"' frame.scad
  run -o stl/$d/back_plate.stl -D n_sides=$n -D 'part="print"' back_plate.scad
  run -o stl/$d/riser_3.stl    -D n_sides=$n -D 'part="riser"' -D riser_h=3 diffuser.scad
  run -o stl/$d/bezel.stl      -D n_sides=$n -D 'part="bezel"' diffuser.scad
  run -o stl/$d/film_template.dxf -D n_sides=$n -D 'part="film"' diffuser.scad
done
run -o stl/triangle/wall_puck.stl -D n_sides=3 wall_puck.scad

# ---------------- PNG: parts (CGAL render) ----------------
P="--render --imgsize=1400,1000 --colorscheme=Tomorrow --viewall --autocenter"
run -o png/frame.png            $P --camera=0,0,0,55,0,25,500   -D 'part="assembly"' frame.scad
run -o png/frame_corner.png     --render --imgsize=1400,1000 --colorscheme=Tomorrow --camera=52,-85,8,235,0,40,90 -D 'part="assembly"' frame.scad
run -o png/back_plate_top.png   $P --camera=0,0,0,40,0,0,500    -D 'part="assembly"' back_plate.scad
run -o png/back_plate_bottom.png $P --camera=0,0,0,180,0,0,500  -D 'part="assembly"' back_plate.scad
run -o png/back_plate_pocket.png --render --imgsize=1400,1000 --colorscheme=Tomorrow --camera=0,-68,4,50,0,0,110 -D 'part="assembly"' back_plate.scad
run -o png/wall_puck.png        $P --camera=0,0,0,55,0,25,500   wall_puck.scad
run -o png/bridge_carrier.png   $P --camera=0,0,0,55,0,25,500   bridge_carrier.scad
run -o png/riser_3.png          $P --camera=0,0,0,55,0,25,500   -D 'part="riser"' diffuser.scad
run -o png/square_back_plate.png   $P --camera=0,0,0,40,0,0,500 -D n_sides=4 -D 'part="assembly"' back_plate.scad
run -o png/triangle_back_plate.png $P --camera=0,0,0,40,0,0,500 -D n_sides=3 -D 'part="assembly"' back_plate.scad

# ---------------- PNG: assembly ----------------
A="--imgsize=1800,1200 --colorscheme=Tomorrow --viewall --autocenter"
run -o png/assembly_panel_color.png    $A --camera=0,0,0,50,0,20,500 -D 'view="panel"'    assembly.scad
run -o png/assembly_exploded_color.png $A --camera=0,0,0,72,0,20,500 -D 'view="exploded"' assembly.scad
run -o png/assembly_cluster_color.png  $A --camera=0,0,0,45,0,15,500 -D 'view="cluster"'  assembly.scad
run -o png/section_seam.png       --imgsize=1800,1100 --projection=o --camera=100,10,0,0,0,0,95  -D 'view="section2d"' assembly.scad
run -o png/section_controller.png --imgsize=1800,1100 --projection=o --camera=78,8,0,0,0,0,115   -D 'view="ctrl2d"'    assembly.scad
run -o png/assembly_panel.png    --render $A --camera=0,0,0,50,0,20,500 -D 'view="panel"'    assembly.scad
run -o png/assembly_exploded.png --render $A --camera=0,0,0,72,0,20,500 -D 'view="exploded"' assembly.scad
run -o png/assembly_cluster.png  --render $A --camera=0,0,0,45,0,15,500 -D 'view="cluster"'  assembly.scad
echo "make_all: done"
