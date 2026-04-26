"""Generate an original CC BY 4.0 periodic-table SVG from public element data.

Data sources (all public-domain factual data):
  * Element symbols, atomic numbers, group/period assignments — IUPAC.
  * Standard atomic weights — IUPAC 2021.
  * Block (s/p/d/f) and category (metal / metalloid / nonmetal / noble gas /
    halogen / alkali / alkaline-earth / transition / lanthanide / actinide)
    — standard scientific classifications.

Layout: 18-column wide form with the f-block placed below in the conventional
two-row inset, plus markers in periods 6 and 7 row showing where the
lanthanides and actinides belong.
"""
from pathlib import Path

OUT = Path(r"C:/Users/easam/Documents/Claude/Projects/OER/CHEM_139_OER_Text_2026/Images/Chapter_05/embedded/fig5-1_periodic_table.svg")

# (Z, symbol, name, atomic_mass, period, group, block, category)
# atomic mass: IUPAC 2021 standard atomic weights, abridged to 4 sig figs;
# elements with no stable isotopes are reported as the most-stable mass-number
# in square brackets, formatted plain in this rendering.
# category codes:
#   am = alkali metal     ae = alkaline earth     tm = transition metal
#   ptm = post-transition metal    mld = metalloid    nm = nonmetal
#   hg = halogen     ng = noble gas     ln = lanthanide     an = actinide
#   un = unknown / superheavy
ELEMENTS = [
    (1,  "H",  "Hydrogen",     "1.008",   1, 1,  "s", "nm"),
    (2,  "He", "Helium",       "4.003",   1, 18, "s", "ng"),
    (3,  "Li", "Lithium",      "6.94",    2, 1,  "s", "am"),
    (4,  "Be", "Beryllium",    "9.012",   2, 2,  "s", "ae"),
    (5,  "B",  "Boron",        "10.81",   2, 13, "p", "mld"),
    (6,  "C",  "Carbon",       "12.01",   2, 14, "p", "nm"),
    (7,  "N",  "Nitrogen",     "14.01",   2, 15, "p", "nm"),
    (8,  "O",  "Oxygen",       "16.00",   2, 16, "p", "nm"),
    (9,  "F",  "Fluorine",     "19.00",   2, 17, "p", "hg"),
    (10, "Ne", "Neon",         "20.18",   2, 18, "p", "ng"),
    (11, "Na", "Sodium",       "22.99",   3, 1,  "s", "am"),
    (12, "Mg", "Magnesium",    "24.31",   3, 2,  "s", "ae"),
    (13, "Al", "Aluminum",     "26.98",   3, 13, "p", "ptm"),
    (14, "Si", "Silicon",      "28.09",   3, 14, "p", "mld"),
    (15, "P",  "Phosphorus",   "30.97",   3, 15, "p", "nm"),
    (16, "S",  "Sulfur",       "32.06",   3, 16, "p", "nm"),
    (17, "Cl", "Chlorine",     "35.45",   3, 17, "p", "hg"),
    (18, "Ar", "Argon",        "39.95",   3, 18, "p", "ng"),
    (19, "K",  "Potassium",    "39.10",   4, 1,  "s", "am"),
    (20, "Ca", "Calcium",      "40.08",   4, 2,  "s", "ae"),
    (21, "Sc", "Scandium",     "44.96",   4, 3,  "d", "tm"),
    (22, "Ti", "Titanium",     "47.87",   4, 4,  "d", "tm"),
    (23, "V",  "Vanadium",     "50.94",   4, 5,  "d", "tm"),
    (24, "Cr", "Chromium",     "52.00",   4, 6,  "d", "tm"),
    (25, "Mn", "Manganese",    "54.94",   4, 7,  "d", "tm"),
    (26, "Fe", "Iron",         "55.85",   4, 8,  "d", "tm"),
    (27, "Co", "Cobalt",       "58.93",   4, 9,  "d", "tm"),
    (28, "Ni", "Nickel",       "58.69",   4, 10, "d", "tm"),
    (29, "Cu", "Copper",       "63.55",   4, 11, "d", "tm"),
    (30, "Zn", "Zinc",         "65.38",   4, 12, "d", "tm"),
    (31, "Ga", "Gallium",      "69.72",   4, 13, "p", "ptm"),
    (32, "Ge", "Germanium",    "72.63",   4, 14, "p", "mld"),
    (33, "As", "Arsenic",      "74.92",   4, 15, "p", "mld"),
    (34, "Se", "Selenium",     "78.97",   4, 16, "p", "nm"),
    (35, "Br", "Bromine",      "79.90",   4, 17, "p", "hg"),
    (36, "Kr", "Krypton",      "83.80",   4, 18, "p", "ng"),
    (37, "Rb", "Rubidium",     "85.47",   5, 1,  "s", "am"),
    (38, "Sr", "Strontium",    "87.62",   5, 2,  "s", "ae"),
    (39, "Y",  "Yttrium",      "88.91",   5, 3,  "d", "tm"),
    (40, "Zr", "Zirconium",    "91.22",   5, 4,  "d", "tm"),
    (41, "Nb", "Niobium",      "92.91",   5, 5,  "d", "tm"),
    (42, "Mo", "Molybdenum",   "95.95",   5, 6,  "d", "tm"),
    (43, "Tc", "Technetium",   "[98]",    5, 7,  "d", "tm"),
    (44, "Ru", "Ruthenium",    "101.1",   5, 8,  "d", "tm"),
    (45, "Rh", "Rhodium",      "102.9",   5, 9,  "d", "tm"),
    (46, "Pd", "Palladium",    "106.4",   5, 10, "d", "tm"),
    (47, "Ag", "Silver",       "107.9",   5, 11, "d", "tm"),
    (48, "Cd", "Cadmium",      "112.4",   5, 12, "d", "tm"),
    (49, "In", "Indium",       "114.8",   5, 13, "p", "ptm"),
    (50, "Sn", "Tin",          "118.7",   5, 14, "p", "ptm"),
    (51, "Sb", "Antimony",     "121.8",   5, 15, "p", "mld"),
    (52, "Te", "Tellurium",    "127.6",   5, 16, "p", "mld"),
    (53, "I",  "Iodine",       "126.9",   5, 17, "p", "hg"),
    (54, "Xe", "Xenon",        "131.3",   5, 18, "p", "ng"),
    (55, "Cs", "Cesium",       "132.9",   6, 1,  "s", "am"),
    (56, "Ba", "Barium",       "137.3",   6, 2,  "s", "ae"),
    # Lanthanides 57-71 placed in f-block inset (period 8 in render)
    (57, "La", "Lanthanum",    "138.9",   8, 3,  "f", "ln"),
    (58, "Ce", "Cerium",       "140.1",   8, 4,  "f", "ln"),
    (59, "Pr", "Praseodymium", "140.9",   8, 5,  "f", "ln"),
    (60, "Nd", "Neodymium",    "144.2",   8, 6,  "f", "ln"),
    (61, "Pm", "Promethium",   "[145]",   8, 7,  "f", "ln"),
    (62, "Sm", "Samarium",     "150.4",   8, 8,  "f", "ln"),
    (63, "Eu", "Europium",     "152.0",   8, 9,  "f", "ln"),
    (64, "Gd", "Gadolinium",   "157.3",   8, 10, "f", "ln"),
    (65, "Tb", "Terbium",      "158.9",   8, 11, "f", "ln"),
    (66, "Dy", "Dysprosium",   "162.5",   8, 12, "f", "ln"),
    (67, "Ho", "Holmium",      "164.9",   8, 13, "f", "ln"),
    (68, "Er", "Erbium",       "167.3",   8, 14, "f", "ln"),
    (69, "Tm", "Thulium",      "168.9",   8, 15, "f", "ln"),
    (70, "Yb", "Ytterbium",    "173.0",   8, 16, "f", "ln"),
    (71, "Lu", "Lutetium",     "175.0",   8, 17, "f", "ln"),
    (72, "Hf", "Hafnium",      "178.5",   6, 4,  "d", "tm"),
    (73, "Ta", "Tantalum",     "180.9",   6, 5,  "d", "tm"),
    (74, "W",  "Tungsten",     "183.8",   6, 6,  "d", "tm"),
    (75, "Re", "Rhenium",      "186.2",   6, 7,  "d", "tm"),
    (76, "Os", "Osmium",       "190.2",   6, 8,  "d", "tm"),
    (77, "Ir", "Iridium",      "192.2",   6, 9,  "d", "tm"),
    (78, "Pt", "Platinum",     "195.1",   6, 10, "d", "tm"),
    (79, "Au", "Gold",         "197.0",   6, 11, "d", "tm"),
    (80, "Hg", "Mercury",      "200.6",   6, 12, "d", "tm"),
    (81, "Tl", "Thallium",     "204.4",   6, 13, "p", "ptm"),
    (82, "Pb", "Lead",         "207.2",   6, 14, "p", "ptm"),
    (83, "Bi", "Bismuth",      "209.0",   6, 15, "p", "ptm"),
    (84, "Po", "Polonium",     "[209]",   6, 16, "p", "mld"),
    (85, "At", "Astatine",     "[210]",   6, 17, "p", "hg"),
    (86, "Rn", "Radon",        "[222]",   6, 18, "p", "ng"),
    (87, "Fr", "Francium",     "[223]",   7, 1,  "s", "am"),
    (88, "Ra", "Radium",       "[226]",   7, 2,  "s", "ae"),
    # Actinides 89-103 placed in f-block inset (period 9 in render)
    (89, "Ac", "Actinium",     "[227]",   9, 3,  "f", "an"),
    (90, "Th", "Thorium",      "232.0",   9, 4,  "f", "an"),
    (91, "Pa", "Protactinium", "231.0",   9, 5,  "f", "an"),
    (92, "U",  "Uranium",      "238.0",   9, 6,  "f", "an"),
    (93, "Np", "Neptunium",    "[237]",   9, 7,  "f", "an"),
    (94, "Pu", "Plutonium",    "[244]",   9, 8,  "f", "an"),
    (95, "Am", "Americium",    "[243]",   9, 9,  "f", "an"),
    (96, "Cm", "Curium",       "[247]",   9, 10, "f", "an"),
    (97, "Bk", "Berkelium",    "[247]",   9, 11, "f", "an"),
    (98, "Cf", "Californium",  "[251]",   9, 12, "f", "an"),
    (99, "Es", "Einsteinium",  "[252]",   9, 13, "f", "an"),
    (100,"Fm", "Fermium",      "[257]",   9, 14, "f", "an"),
    (101,"Md", "Mendelevium",  "[258]",   9, 15, "f", "an"),
    (102,"No", "Nobelium",     "[259]",   9, 16, "f", "an"),
    (103,"Lr", "Lawrencium",   "[266]",   9, 17, "f", "an"),
    (104,"Rf", "Rutherfordium","[267]",   7, 4,  "d", "tm"),
    (105,"Db", "Dubnium",      "[268]",   7, 5,  "d", "tm"),
    (106,"Sg", "Seaborgium",   "[269]",   7, 6,  "d", "tm"),
    (107,"Bh", "Bohrium",      "[270]",   7, 7,  "d", "tm"),
    (108,"Hs", "Hassium",      "[277]",   7, 8,  "d", "tm"),
    (109,"Mt", "Meitnerium",   "[278]",   7, 9,  "d", "un"),
    (110,"Ds", "Darmstadtium", "[281]",   7, 10, "d", "un"),
    (111,"Rg", "Roentgenium",  "[282]",   7, 11, "d", "un"),
    (112,"Cn", "Copernicium",  "[285]",   7, 12, "d", "un"),
    (113,"Nh", "Nihonium",     "[286]",   7, 13, "p", "un"),
    (114,"Fl", "Flerovium",    "[289]",   7, 14, "p", "un"),
    (115,"Mc", "Moscovium",    "[290]",   7, 15, "p", "un"),
    (116,"Lv", "Livermorium",  "[293]",   7, 16, "p", "un"),
    (117,"Ts", "Tennessine",   "[294]",   7, 17, "p", "un"),
    (118,"Og", "Oganesson",    "[294]",   7, 18, "p", "un"),
]

# Category fill colors. Sufficient contrast against black text;
# also distinguished by pattern via the "block" border to satisfy
# the "no color-only meaning" accessibility rule.
CATEGORY = {
    "am":  ("#F4C7C0", "Alkali metal"),
    "ae":  ("#F8DDB0", "Alkaline earth metal"),
    "tm":  ("#FFE9A0", "Transition metal"),
    "ptm": ("#D9E5C7", "Post-transition metal"),
    "mld": ("#C9DDC1", "Metalloid"),
    "nm":  ("#C5D8EC", "Nonmetal"),
    "hg":  ("#A9C8E9", "Halogen"),
    "ng":  ("#D6C7E8", "Noble gas"),
    "ln":  ("#F0CFE8", "Lanthanide"),
    "an":  ("#E9C0D9", "Actinide"),
    "un":  ("#E5E5E5", "Unknown / superheavy"),
}

# Block stroke colors and stroke widths (the "no color-only meaning" trick:
# block info is encoded as the cell's outline color/style as well as the
# textual "s/p/d/f" classification in the legend).
BLOCK_STROKE = {
    "s": ("#1F4F8B", 1.6, None),     # solid blue
    "p": ("#0E6B36", 1.6, None),     # solid green
    "d": ("#7A2A0A", 1.6, None),     # solid dark-red
    "f": ("#5B2A8B", 1.6, "3 2"),    # dashed purple
}

# Cell geometry
CELL_W = 60
CELL_H = 64
GAP = 4

# Page margins
M_LEFT = 60
M_TOP = 110

# Compute column x and row y. Group 1..18 -> columns 1..18, period 1..7 main,
# 8..9 for f-block inset (placed below the main table with one-row gap).
F_INSET_TOP_OFFSET = (CELL_H + GAP) * 1.5  # extra gap above the inset rows

def cell_x(group):
    return M_LEFT + (group - 1) * (CELL_W + GAP)

def cell_y(period):
    if period <= 7:
        return M_TOP + (period - 1) * (CELL_H + GAP)
    # 8 = lanthanide row, 9 = actinide row
    return M_TOP + 7 * (CELL_H + GAP) + F_INSET_TOP_OFFSET + (period - 8) * (CELL_H + GAP)


def cell(z, sym, name, mass, period, group, block, category):
    fill, _ = CATEGORY[category]
    stroke, sw, dash = BLOCK_STROKE[block]
    x = cell_x(group)
    y = cell_y(period)
    dash_attr = f' stroke-dasharray="{dash}"' if dash else ''
    return f'''  <g class="el">
    <rect x="{x}" y="{y}" width="{CELL_W}" height="{CELL_H}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}"{dash_attr}/>
    <text class="z"    x="{x+5}"            y="{y+13}">{z}</text>
    <text class="mass" x="{x+CELL_W-5}"     y="{y+13}" text-anchor="end">{mass}</text>
    <text class="sym"  x="{x+CELL_W/2}"     y="{y+38}" text-anchor="middle">{sym}</text>
    <text class="name" x="{x+CELL_W/2}"     y="{y+55}" text-anchor="middle">{name}</text>
  </g>'''


def build():
    cells_xml = "\n".join(cell(*e) for e in ELEMENTS)

    # Group numbers (top header) and period numbers (left side)
    group_labels = []
    for g in range(1, 19):
        x = cell_x(g) + CELL_W / 2
        y = M_TOP - 12
        group_labels.append(f'<text class="hdr" x="{x}" y="{y}" text-anchor="middle">{g}</text>')
    period_labels = []
    for p in range(1, 8):
        x = M_LEFT - 14
        y = cell_y(p) + CELL_H / 2 + 4
        period_labels.append(f'<text class="hdr" x="{x}" y="{y}" text-anchor="end">{p}</text>')

    # f-block markers in periods 6 and 7 row, group 3 column
    markers = []
    for p, sym in ((6, "57–71"), (7, "89–103")):
        x = cell_x(3)
        y = cell_y(p)
        markers.append(
            f'<g><rect x="{x}" y="{y}" width="{CELL_W}" height="{CELL_H}" fill="#FAFAFA" stroke="#999" stroke-width="1.2" stroke-dasharray="3 3"/>'
            f'<text class="marker" x="{x+CELL_W/2}" y="{y+34}" text-anchor="middle">{sym}</text>'
            f'<text class="markersub" x="{x+CELL_W/2}" y="{y+50}" text-anchor="middle">see below</text></g>'
        )

    # Inset row labels: " * " for lanthanides, "**" for actinides
    inset_labels = [
        f'<text class="markersub" x="{cell_x(2)+CELL_W-6}" y="{cell_y(8)+CELL_H/2+5}" text-anchor="end">57&#8211;71 (lanthanides)</text>',
        f'<text class="markersub" x="{cell_x(2)+CELL_W-6}" y="{cell_y(9)+CELL_H/2+5}" text-anchor="end">89&#8211;103 (actinides)</text>',
    ]

    # Block-region annotations (s, p, d, f) — drawn as horizontal bars above
    # the block columns so a reader can see the block layout at a glance.
    block_anno = []
    # s-block: groups 1-2
    block_anno.append(_block_bar("s-block", cell_x(1), cell_x(2)+CELL_W, "#1F4F8B"))
    # p-block: groups 13-18
    block_anno.append(_block_bar("p-block", cell_x(13), cell_x(18)+CELL_W, "#0E6B36"))
    # d-block: groups 3-12
    block_anno.append(_block_bar("d-block", cell_x(3), cell_x(12)+CELL_W, "#7A2A0A"))
    # f-block: above inset
    fx0 = cell_x(3)
    fx1 = cell_x(17) + CELL_W
    fy = cell_y(8) - 22
    block_anno.append(
        f'<line x1="{fx0}" y1="{fy}" x2="{fx1}" y2="{fy}" stroke="#5B2A8B" stroke-width="2" stroke-dasharray="3 2"/>'
        f'<text class="bblock" x="{(fx0+fx1)/2}" y="{fy-4}" text-anchor="middle" fill="#5B2A8B">f-block</text>'
    )

    # Legend
    legend_items = [
        ("am", "Alkali metal"),
        ("ae", "Alkaline earth metal"),
        ("tm", "Transition metal"),
        ("ptm", "Post-transition metal"),
        ("mld", "Metalloid"),
        ("nm", "Nonmetal"),
        ("hg", "Halogen"),
        ("ng", "Noble gas"),
        ("ln", "Lanthanide"),
        ("an", "Actinide"),
    ]
    leg_x0 = M_LEFT
    leg_y0 = cell_y(9) + CELL_H + 26
    legend_xml = []
    legend_xml.append(f'<text class="leghdr" x="{leg_x0}" y="{leg_y0}">Element category (color)</text>')
    for i, (k, label) in enumerate(legend_items):
        col = i % 5
        row = i // 5
        ix = leg_x0 + col * 220
        iy = leg_y0 + 12 + row * 22
        fill, _ = CATEGORY[k]
        legend_xml.append(
            f'<rect x="{ix}" y="{iy}" width="22" height="14" fill="{fill}" stroke="#444" stroke-width="0.8"/>'
            f'<text class="legtxt" x="{ix+30}" y="{iy+11}">{label}</text>'
        )

    # Block legend (cell-border style)
    blk_y = leg_y0 + 70
    legend_xml.append(f'<text class="leghdr" x="{leg_x0}" y="{blk_y}">Outermost subshell being filled (cell-border color/style)</text>')
    for i, (k, color, label) in enumerate([
        ("s", "#1F4F8B", "s-block"),
        ("p", "#0E6B36", "p-block"),
        ("d", "#7A2A0A", "d-block"),
        ("f", "#5B2A8B", "f-block (dashed)"),
    ]):
        col = i % 4
        ix = leg_x0 + col * 270
        iy = blk_y + 12
        dash = ' stroke-dasharray="3 2"' if k == "f" else ''
        legend_xml.append(
            f'<rect x="{ix}" y="{iy}" width="22" height="14" fill="white" stroke="{color}" stroke-width="2"{dash}/>'
            f'<text class="legtxt" x="{ix+30}" y="{iy+11}">{label}</text>'
        )

    # Footer attribution + provenance
    foot_y = blk_y + 56
    footer = (
        f'<text class="foot" x="{leg_x0}" y="{foot_y}">'
        'Atomic-mass values: IUPAC 2021 standard atomic weights (rounded). '
        'Brackets indicate the most stable isotope for elements with no stable form.'
        '</text>'
    )
    title_block = (
        '<text class="figtitle" x="60" y="42">Periodic Table of the Elements</text>'
        '<text class="figsub"   x="60" y="68">Annotated with block (s, p, d, f) and category. CHEM 139 OER, 2026 ed. CC BY 4.0.</text>'
    )

    # Compute viewBox
    vb_w = M_LEFT + 18 * (CELL_W + GAP) + 30
    vb_h = foot_y + 30

    svg = f'''<?xml version="1.0" encoding="UTF-8" standalone="no"?>
<!-- (c) 2026 CHEM 139 OER. CC BY 4.0. Original figure built from public IUPAC/NIST data. -->
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {vb_w} {vb_h}" width="{vb_w}" height="{vb_h}" font-family="Arial, Helvetica, sans-serif" role="img" aria-labelledby="t d">
  <title id="t">Figure 5.1 — Periodic table annotated with blocks and categories</title>
  <desc id="d">An eighteen-column periodic table with the f-block placed in a two-row inset below. Each cell shows atomic number, atomic symbol, element name, and IUPAC 2021 atomic mass. Cells are filled by element category (alkali metal, alkaline earth, transition metal, post-transition metal, metalloid, nonmetal, halogen, noble gas, lanthanide, actinide). Cell outline color and style encodes the s, p, d, or f block.</desc>
  <style>
    .figtitle {{ font-size:22px; font-weight:700; fill:#0E2D52; }}
    .figsub   {{ font-size:13px; fill:#444; }}
    .hdr   {{ font-size:13px; font-weight:700; fill:#1B1B1B; }}
    .z     {{ font-size:10.5px; fill:#1B1B1B; }}
    .mass  {{ font-size:9.5px; fill:#1B1B1B; }}
    .sym   {{ font-size:18px; font-weight:700; fill:#1B1B1B; }}
    .name  {{ font-size:7.5px; fill:#1B1B1B; }}
    .marker {{ font-size:13px; font-weight:700; fill:#777; }}
    .markersub {{ font-size:9px; fill:#777; font-style:italic; }}
    .bblock {{ font-size:11px; font-weight:700; }}
    .leghdr {{ font-size:12px; font-weight:700; fill:#0E2D52; }}
    .legtxt {{ font-size:11px; fill:#1B1B1B; }}
    .foot   {{ font-size:10px; fill:#444; font-style:italic; }}
  </style>
  {title_block}
  {''.join(group_labels)}
  {''.join(period_labels)}
  {''.join(block_anno)}
  {''.join(markers)}
  {''.join(inset_labels)}
{cells_xml}
  {''.join(legend_xml)}
  {footer}
</svg>
'''
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(svg, encoding="utf-8")
    print(f"wrote {OUT} ({OUT.stat().st_size} bytes)")


def _block_bar(label, x0, x1, color):
    y = M_TOP - 30
    cx = (x0 + x1) / 2
    return (
        f'<line x1="{x0}" y1="{y}" x2="{x1}" y2="{y}" stroke="{color}" stroke-width="2"/>'
        f'<text class="bblock" x="{cx}" y="{y-4}" text-anchor="middle" fill="{color}">{label}</text>'
    )


if __name__ == "__main__":
    build()
