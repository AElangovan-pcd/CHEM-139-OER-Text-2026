#!/usr/bin/env bash
# Downloads OpenStax Chemistry 2e figure renders as PNG.
# All sources are CC BY 4.0 (OpenStax content license).
set -e
ARCHIVE=20260407.195030
BASE="https://openstax.org/apps/image-cdn/v1/f=png/apps/archive/${ARCHIVE}/resources"

dl() {
  local hash="$1" outdir="$2" name="$3"
  mkdir -p "$outdir"
  curl -sSfL -A "Mozilla/5.0 (CHEM139-OER/1.0)" "$BASE/$hash" -o "$outdir/$name"
  echo "  $outdir/$name"
}

dl 7a81a4456ab3500d3e2cf2bb8efdde3cbce4d33f Images/Chapter_02/embedded fig2-2_temperature_scales.png
dl eb4d29159164d8e6933252a94b835b8a2264e952 Images/Chapter_03/embedded fig3-1_solid_liquid_gas.png
dl 1e26282d74f3082952e06bdd924b9771934ae9ae Images/Chapter_03/embedded fig3-2_matter_classification.png
dl 593f207630a46c81d03967246cae21946c2c2277 Images/Chapter_04/embedded fig4-1_modern_atom.png
dl 2b721b0944b10dcfed1a88cb056a233b350838a9 Images/Chapter_04/embedded fig4-2_rutherford_apparatus.png
dl a90abd7d07f0304260a7d292a97f60ef7eee1b1f Images/Chapter_05/embedded fig5-2_orbital_shapes.png
dl 7909e7ef9926a80d76573e73d00eec2c1be57c1e Images/Chapter_05/embedded fig5-3_aufbau.png
dl 1244eb3d86cd0d55eae35c418fe44447025a01e4 Images/Chapter_05/embedded fig5-4_atomic_radius.png
dl 07e6e57cd454a443c561effb54fa3eafb3f00547 Images/Chapter_06/embedded fig6-1_vsepr.png
dl 9d1e6170fc7727642a0fa60bf8f43ed5019bf40c Images/Chapter_10/embedded fig10-2_hbond_water.png
dl 7b1a1b1600c9514b29554da94cfdc3ad1ded603f Images/Chapter_10/embedded fig10-3_phase_diagram_water.png
echo "Done."
