"""Apply factor-label rewrites to Chapter 9 (Stoichiometry) Solutions."""
from rewrite_engine import apply_rewrites

# Indices to LEAVE UNTOUCHED (0-based Solution paragraph order).
SKIP = {
    # Practice Problems: balancing equations (no math chain)
    0, 1, 2, 3, 4, 5, 6,
    # Practice Problems: reaction classification (qualitative)
    7, 8, 9, 10, 11, 12,
    # Additional Practice: balancing equations
    25, 26, 27, 28, 29,
    # Additional Practice: reaction classification
    30, 31, 32, 33, 34,
    # Why actual < theoretical (qualitative)
    48,
}

REWRITES = [
    # ---- Practice Problems: Mole-to-mole and mole-to-mass ----

    # idx 13: 0.500 mol N₂ → NH₃ in N₂ + 3H₂ → 2NH₃
    ("0.500 × 2", 0, [
        "0.500 ~~mol N₂~~ × (2 mol NH₃ / 1 ~~mol N₂~~) = 1.00 mol NH₃",
    ],
        "\"mol N₂\" cancels via the coefficient ratio (2 NH₃ per 1 N₂). Three sig figs."
    ),
    # idx 14: 0.750 mol O₂ → H₂ in 2H₂ + O₂ → 2H₂O
    ("0.750 × 2/1", 0, [
        "0.750 ~~mol O₂~~ × (2 mol H₂ / 1 ~~mol O₂~~) = 1.50 mol H₂",
    ],
        "\"mol O₂\" cancels via the coefficient ratio (2 H₂ per 1 O₂)."
    ),
    # idx 15: 1.00 mol KClO₃ → mass O₂ in 2 KClO₃ → 2 KCl + 3 O₂
    ("Mol O₂ = 1.00", 0, [
        "n(O₂) = 1.00 ~~mol KClO₃~~ × (3 mol O₂ / 2 ~~mol KClO₃~~) = 1.50 mol O₂",
        "Mass O₂ = 1.50 ~~mol~~ × (31.998 g / 1 ~~mol~~) = 48.0 g",
    ],
        "\"mol KClO₃\" cancels via the 3:2 stoichiometric ratio; \"mol\" cancels via the molar mass of O₂."
    ),
    # idx 16: 25.0 g CaCO₃ → CaO in CaCO₃ → CaO + CO₂
    ("Moles CaCO₃ = 25.0", 0, [
        "n(CaCO₃) = 25.0 ~~g~~ × (1 mol / 100.09 ~~g~~) = 0.2498 mol CaCO₃",
        "n(CaO) = 0.2498 ~~mol CaCO₃~~ × (1 mol CaO / 1 ~~mol CaCO₃~~) = 0.2498 mol CaO",
        "Mass CaO = 0.2498 ~~mol~~ × (56.077 g / 1 ~~mol~~) = 14.0 g",
    ],
        "Three cancellations: \"g\" (mass→mol), \"mol CaCO₃\" (1:1 stoichiometry), \"mol\" (mol→mass). Three sig figs."
    ),
    # idx 17: 5.40 g Al → AlCl₃ in 2 Al + 3 Cl₂ → 2 AlCl₃
    ("Moles Al = 5.40", 0, [
        "n(Al) = 5.40 ~~g~~ × (1 mol / 26.982 ~~g~~) = 0.2002 mol Al",
        "n(AlCl₃) = 0.2002 ~~mol Al~~ × (2 mol AlCl₃ / 2 ~~mol Al~~) = 0.2002 mol AlCl₃",
        "Mass AlCl₃ = 0.2002 ~~mol~~ × (133.34 g / 1 ~~mol~~) = 26.7 g",
    ],
        "\"g\" / \"mol Al\" / \"mol\" cancel in turn. The 2:2 stoichiometric ratio simplifies to 1:1. Three sig figs."
    ),
    # idx 18: 100.0 g H₂O → O₂ in 2 H₂ + O₂ → 2 H₂O
    ("Moles H₂O = 100.0", 0, [
        "n(H₂O) = 100.0 ~~g~~ × (1 mol / 18.015 ~~g~~) = 5.551 mol H₂O",
        "n(O₂) = 5.551 ~~mol H₂O~~ × (1 mol O₂ / 2 ~~mol H₂O~~) = 2.776 mol O₂",
        "Mass O₂ = 2.776 ~~mol~~ × (32.00 g / 1 ~~mol~~) = 88.8 g",
    ],
        "Three cancellations: \"g\" (mass→mol), \"mol H₂O\" (1:2 stoichiometric ratio), \"mol\" (mol→mass)."
    ),
    # idx 19: 5.00 g octane → CO₂
    ("Moles C₈H₁₈ = 5.00", 0, [
        "n(C₈H₁₈) = 5.00 ~~g~~ × (1 mol / 114.23 ~~g~~) = 0.04377 mol C₈H₁₈",
        "n(CO₂) = 0.04377 ~~mol C₈H₁₈~~ × (8 mol CO₂ / 1 ~~mol C₈H₁₈~~) = 0.3502 mol CO₂",
        "Mass CO₂ = 0.3502 ~~mol~~ × (44.01 g / 1 ~~mol~~) = 15.4 g",
    ],
        "\"g\" / \"mol C₈H₁₈\" / \"mol\" cancel in turn. The 8:1 ratio comes from the balanced equation."
    ),
    # idx 20: 9.5 / 12.0 % yield
    ("9.5 / 12.0", 0, [
        "% yield = (9.5 ~~g~~ actual / 12.0 ~~g~~ theoretical) × 100% = 79%",
    ],
        "\"g\" cancels in the yield ratio. Two sig figs (limited by \"9.5\")."
    ),
    # idx 21: 50.0 × 0.75 actual yield
    ("50.0 × 0.75", 0, [
        "Actual yield = 50.0 g theoretical × (75 g actual / 100 g theoretical) = 37.5 g",
    ],
        "\"g theoretical\" cancels using the percent-yield fraction as a conversion factor."
    ),
    # idx 22: Na/Cl₂ limiting in 2 Na + Cl₂ → 2 NaCl
    ("Mol Na = 5.00", 0, [
        "n(Na) = 5.00 ~~g~~ × (1 mol / 22.99 ~~g~~) = 0.2175 mol Na",
        "n(Cl₂) = 5.00 ~~g~~ × (1 mol / 70.91 ~~g~~) = 0.07051 mol Cl₂",
        "Divide by coefficient: Na 0.2175/2 = 0.1088; Cl₂ 0.07051/1 = 0.07051",
        "Cl₂ has the smaller value → Cl₂ is limiting; Na is in excess",
    ],
        "\"g\" cancels in each mole conversion. Dividing by the stoichiometric coefficient identifies the limiting reactant."
    ),
    # idx 23: mass NaCl from Cl₂ limiting
    ("From Cl₂: mol", 0, [
        "n(NaCl) = 0.07051 ~~mol Cl₂~~ × (2 mol NaCl / 1 ~~mol Cl₂~~) = 0.1410 mol NaCl",
        "Mass NaCl = 0.1410 ~~mol~~ × (58.44 g / 1 ~~mol~~) = 8.24 g",
    ],
        "\"mol Cl₂\" cancels via the 2:1 stoichiometric ratio; \"mol\" cancels via molar mass."
    ),
    # idx 24: 12.0/8.24 % yield = 146% (impossible)
    ("12.0/8.24", 0, [
        "% yield = (12.0 ~~g~~ actual / 8.24 ~~g~~ theoretical) × 100% = 146%",
    ],
        "A yield > 100% is chemically impossible — it signals contamination, residual water, or a weighing error in the recovered product."
    ),

    # ---- Additional Practice: Mole-to-mole and mole-to-mass ----

    # idx 35: 5.0 mol H₂ → H₂O (auto-rewriter already inserted an explanation; consume_after=1)
    ("5.0 mol H₂ ×", 1, [
        "5.0 ~~mol H₂~~ × (2 mol H₂O / 2 ~~mol H₂~~) = 5.0 mol H₂O",
    ],
        "\"mol H₂\" cancels via the 2:2 stoichiometric ratio. Two sig figs."
    ),
    # idx 36: 4.00 mol N₂ → H₂ (auto-rewriter touched; consume_after=1)
    ("4.00 mol N₂ ×", 1, [
        "4.00 ~~mol N₂~~ × (3 mol H₂ / 1 ~~mol N₂~~) = 12.0 mol H₂",
    ],
        "\"mol N₂\" cancels via the 3:1 stoichiometric ratio."
    ),
    # idx 37: 0.500 mol Al → AlCl₃ (mass)
    ("0.500 mol Al × (2/2)", 0, [
        "n(AlCl₃) = 0.500 ~~mol Al~~ × (2 mol AlCl₃ / 2 ~~mol Al~~) = 0.500 mol AlCl₃",
        "Mass AlCl₃ = 0.500 ~~mol~~ × (133.34 g / 1 ~~mol~~) = 66.67 g",
    ],
        "\"mol Al\" cancels via the 2:2 ratio (effectively 1:1); \"mol\" cancels via molar mass."
    ),
    # idx 38: 2.00 mol CaCO₃ → CO₂
    ("2.00 mol CaCO₃ × (1/1)", 0, [
        "n(CO₂) = 2.00 ~~mol CaCO₃~~ × (1 mol CO₂ / 1 ~~mol CaCO₃~~) = 2.00 mol CO₂",
        "Mass CO₂ = 2.00 ~~mol~~ × (44.01 g / 1 ~~mol~~) = 88.0 g",
    ],
        "\"mol CaCO₃\" / \"mol\" cancel through the chain. Three sig figs."
    ),
    # idx 39: 0.200 mol Fe → O₂ (auto-rewriter touched; consume_after=1)
    ("0.200 mol Fe ×", 1, [
        "0.200 ~~mol Fe~~ × (3 mol O₂ / 4 ~~mol Fe~~) = 0.150 mol O₂",
    ],
        "\"mol Fe\" cancels via the 3:4 stoichiometric ratio. Three sig figs."
    ),

    # ---- APP: Mass-to-mass Stoichiometry ----

    # idx 40: 8.00 g H₂ → H₂O
    ("n(H₂) = 8.00", 0, [
        "n(H₂) = 8.00 ~~g~~ × (1 mol / 2.016 ~~g~~) = 3.97 mol H₂",
        "n(H₂O) = 3.97 ~~mol H₂~~ × (2 mol H₂O / 2 ~~mol H₂~~) = 3.97 mol H₂O",
        "Mass H₂O = 3.97 ~~mol~~ × (18.02 g / 1 ~~mol~~) = 71.5 g",
    ],
        "\"g\" / \"mol H₂\" / \"mol\" cancel in turn. The 2:2 ratio is effectively 1:1."
    ),
    # idx 41: 12.0 g Mg → MgO
    ("n(Mg) = 12.0", 0, [
        "n(Mg) = 12.0 ~~g~~ × (1 mol / 24.31 ~~g~~) = 0.4937 mol Mg",
        "n(MgO) = 0.4937 ~~mol Mg~~ × (2 mol MgO / 2 ~~mol Mg~~) = 0.4937 mol MgO",
        "Mass MgO = 0.4937 ~~mol~~ × (40.30 g / 1 ~~mol~~) = 19.9 g",
    ],
        "Three cancellations across the mass→mol→mol→mass chain. Three sig figs."
    ),
    # idx 42: 22.0 g C₃H₈ → CO₂
    ("n(C₃H₈) = 22.0", 0, [
        "n(C₃H₈) = 22.0 ~~g~~ × (1 mol / 44.10 ~~g~~) = 0.499 mol C₃H₈",
        "n(CO₂) = 0.499 ~~mol C₃H₈~~ × (3 mol CO₂ / 1 ~~mol C₃H₈~~) = 1.50 mol CO₂",
        "Mass CO₂ = 1.50 ~~mol~~ × (44.01 g / 1 ~~mol~~) = 65.9 g",
    ],
        "\"g\" / \"mol C₃H₈\" / \"mol\" cancel; the 3:1 ratio comes from C₃H₈ + 5 O₂ → 3 CO₂ + 4 H₂O."
    ),
    # idx 43: 5.00 g KClO₃ → O₂
    ("n(KClO₃) = 5.00", 0, [
        "n(KClO₃) = 5.00 ~~g~~ × (1 mol / 122.55 ~~g~~) = 0.04080 mol KClO₃",
        "n(O₂) = 0.04080 ~~mol KClO₃~~ × (3 mol O₂ / 2 ~~mol KClO₃~~) = 0.0612 mol O₂",
        "Mass O₂ = 0.0612 ~~mol~~ × (32.00 g / 1 ~~mol~~) = 1.96 g",
    ],
        "Three cancellations through the chain. The 3:2 ratio is from 2 KClO₃ → 2 KCl + 3 O₂."
    ),
    # idx 44: 28.0 g N₂ → NH₃
    ("n(N₂) = 28.0", 0, [
        "n(N₂) = 28.0 ~~g~~ × (1 mol / 28.02 ~~g~~) = 0.9993 mol N₂",
        "n(NH₃) = 0.9993 ~~mol N₂~~ × (2 mol NH₃ / 1 ~~mol N₂~~) = 1.999 mol NH₃",
        "Mass NH₃ = 1.999 ~~mol~~ × (17.03 g / 1 ~~mol~~) = 34.0 g",
    ],
        "\"g\" / \"mol N₂\" / \"mol\" cancel through the Haber-process chain (N₂ + 3 H₂ → 2 NH₃)."
    ),

    # ---- APP: Yields ----

    # idx 45: 22.5/25.0 % yield
    ("22.5/25.0", 0, [
        "% yield = (22.5 ~~g~~ actual / 25.0 ~~g~~ theoretical) × 100% = 90.0%",
    ],
        "\"g\" cancels. Three sig figs."
    ),
    # idx 46: 0.780 × 4.50 actual
    ("0.780 × 4.50", 0, [
        "Actual yield = 4.50 g theoretical × (78.0 g actual / 100 g theoretical) = 3.51 g",
    ],
        "\"g theoretical\" cancels via the percent-yield fraction."
    ),
    # idx 47: 14.0/17.5 % yield
    ("14.0/17.5", 0, [
        "% yield = (14.0 ~~g~~ actual / 17.5 ~~g~~ theoretical) × 100% = 80.0%",
    ],
        "\"g\" cancels. Three sig figs."
    ),
    # idx 49: 4.60 g Na → NaCl theoretical
    ("n(Na) = 4.60", 0, [
        "n(Na) = 4.60 ~~g~~ × (1 mol / 22.99 ~~g~~) = 0.2001 mol Na",
        "n(NaCl) = 0.2001 ~~mol Na~~ × (2 mol NaCl / 2 ~~mol Na~~) = 0.2001 mol NaCl",
        "Theoretical mass NaCl = 0.2001 ~~mol~~ × (58.44 g / 1 ~~mol~~) = 11.7 g",
    ],
        "Three cancellations across the chain. The 2:2 ratio is effectively 1:1."
    ),

    # ---- APP: Limiting Reactant ----

    # idx 50: 1.0 mol N₂ vs 4.0 mol H₂ limiting in N₂ + 3H₂ → 2NH₃
    ("From 1.0 mol N₂", 0, [
        "Test N₂ as limiting: 1.0 ~~mol N₂~~ × (3 mol H₂ / 1 ~~mol N₂~~) = 3.0 mol H₂ needed; have 4.0 mol H₂ — N₂ would consume only 3.0",
        "Test H₂ as limiting: 4.0 ~~mol H₂~~ × (1 mol N₂ / 3 ~~mol H₂~~) = 1.33 mol N₂ needed; have only 1.0 — N₂ runs out first",
        "Conclusion: N₂ is the limiting reactant",
    ],
        "Each \"if-this-were-limiting\" test cancels its own moles. The reactant whose required partner exceeds what is available is the limiting one — here, N₂."
    ),
    # idx 51: 1.0 mol N₂ → NH₃
    ("1.0 mol N₂ × (2/1)", 0, [
        "n(NH₃) = 1.0 ~~mol N₂~~ × (2 mol NH₃ / 1 ~~mol N₂~~) = 2.0 mol NH₃",
    ],
        "\"mol N₂\" cancels via the 2:1 stoichiometric ratio."
    ),
    # idx 52: 0.50 mol Al / 0.50 mol Cl₂ limiting
    ("0.50 mol Al would need", 0, [
        "Test Al as limiting: 0.50 ~~mol Al~~ × (3 mol Cl₂ / 2 ~~mol Al~~) = 0.75 mol Cl₂ needed; have only 0.50 — Cl₂ runs out first",
        "Conclusion: Cl₂ is the limiting reactant",
    ],
        "\"mol Al\" cancels in the requirement test. Cl₂ is limiting because the chemistry would need more Cl₂ than is available."
    ),
    # idx 53: AlCl₃ from Cl₂ limiting
    ("n(AlCl₃) = 0.50 mol Cl₂", 0, [
        "n(AlCl₃) = 0.50 ~~mol Cl₂~~ × (2 mol AlCl₃ / 3 ~~mol Cl₂~~) = 0.333 mol AlCl₃",
        "Mass AlCl₃ = 0.333 ~~mol~~ × (133.34 g / 1 ~~mol~~) = 44.4 g",
    ],
        "\"mol Cl₂\" cancels via the 2:3 stoichiometric ratio (from 2 Al + 3 Cl₂ → 2 AlCl₃); \"mol\" cancels via molar mass."
    ),
    # idx 54: Al excess remaining
    ("Al consumed = 0.50", 0, [
        "Al consumed = 0.50 ~~mol Cl₂~~ × (2 mol Al / 3 ~~mol Cl₂~~) = 0.333 mol Al",
        "Al leftover = 0.50 mol initial − 0.333 mol consumed = 0.167 mol Al",
    ],
        "\"mol Cl₂\" cancels in the consumption calculation. The leftover Al is the excess after the limiting reactant has been used up."
    ),

    # ---- Multi-Concept Problems ----

    # idx 55: Iron rust + % yield (two parts in source; consume_after=1)
    ("Mol Fe = 10.00", 1, [
        "n(Fe) = 10.00 ~~g~~ × (1 mol / 55.845 ~~g~~) = 0.1791 mol Fe",
        "n(Fe₂O₃) = 0.1791 ~~mol Fe~~ × (2 mol Fe₂O₃ / 4 ~~mol Fe~~) = 0.08953 mol Fe₂O₃",
        "Theoretical mass Fe₂O₃ = 0.08953 ~~mol~~ × (159.69 g / 1 ~~mol~~) = 14.30 g",
        "% yield = (12.5 ~~g~~ actual / 14.30 ~~g~~ theoretical) × 100% = 87.4%",
    ],
        "Four cancellations: \"g\" (mass→mol Fe), \"mol Fe\" (2:4 stoichiometry), \"mol\" (mol Fe₂O₃→mass), \"g\" (yield ratio). Four sig figs reduce to 3 by the end."
    ),
    # idx 56: Li + H₂O limiting + H₂ mass
    ("Mol Li = 0.500", 0, [
        "n(Li) = 0.500 ~~g~~ × (1 mol / 6.94 ~~g~~) = 0.0721 mol Li",
        "n(H₂O) = 50.0 ~~g~~ × (1 mol / 18.015 ~~g~~) = 2.776 mol H₂O",
        "Divide by coefficient: Li 0.0721/2 = 0.03605; H₂O 2.776/2 = 1.388 → Li is limiting",
        "n(H₂) = 0.0721 ~~mol Li~~ × (1 mol H₂ / 2 ~~mol Li~~) = 0.03605 mol H₂",
        "Mass H₂ = 0.03605 ~~mol~~ × (2.016 g / 1 ~~mol~~) = 0.0727 g = 72.7 mg",
    ],
        "Multiple cancellations: \"g\" twice (mass→mol for both reactants), \"mol Li\" (1:2 ratio), \"mol\" (mol H₂→mass). Li runs out first because there are far fewer moles of it relative to its coefficient."
    ),
    # idx 57: Photosynthesis (two-part; consume_after=1)
    ("Mol CO₂ = 100.0", 1, [
        "n(CO₂) = 100.0 ~~g~~ × (1 mol / 44.01 ~~g~~) = 2.272 mol CO₂",
        "n(O₂) = 2.272 ~~mol CO₂~~ × (6 mol O₂ / 6 ~~mol CO₂~~) = 2.272 mol O₂",
        "Mass O₂ = 2.272 ~~mol~~ × (32.00 g / 1 ~~mol~~) = 72.7 g",
        "n(C₆H₁₂O₆) = 2.272 ~~mol CO₂~~ × (1 mol C₆H₁₂O₆ / 6 ~~mol CO₂~~) = 0.3787 mol C₆H₁₂O₆",
        "Molecules C₆H₁₂O₆ = 0.3787 ~~mol~~ × (6.022 × 10²³ molecules / 1 ~~mol~~) = 2.281 × 10²³ molecules",
    ],
        "Cancellations chain: \"g\" → \"mol CO₂\" (6:6, then 6:1) → \"mol\" (twice, for mass and Avogadro). Three sig figs throughout."
    ),
    # idx 58: Aspirin yield (two-part; consume_after=1)
    ("Mol salicylic = 5.00", 1, [
        "n(salicylic acid) = 5.00 ~~g~~ × (1 mol / 138.12 ~~g~~) = 0.03620 mol",
        "n(aspirin) = 0.03620 ~~mol salicylic acid~~ × (1 mol aspirin / 1 ~~mol salicylic acid~~) = 0.03620 mol aspirin",
        "Theoretical mass aspirin = 0.03620 ~~mol~~ × (180.16 g / 1 ~~mol~~) = 6.523 g",
        "% yield = (4.50 ~~g~~ actual / 6.523 ~~g~~ theoretical) × 100% = 69.0%",
    ],
        "Three cancellation pairs across the chain plus a final \"g\" cancellation in the percent-yield ratio. The 1:1 mole ratio is the simplest possible stoichiometry."
    ),
    # idx 59: Industrial NH₃ limiting
    ("Mol N₂ = 28000", 0, [
        "n(N₂) = 28.0 ~~kg~~ × (1000 ~~g~~ / 1 ~~kg~~) × (1 mol / 28.014 ~~g~~) = 999.5 mol N₂",
        "n(H₂) = 6.00 ~~kg~~ × (1000 ~~g~~ / 1 ~~kg~~) × (1 mol / 2.016 ~~g~~) = 2976 mol H₂",
        "Divide by coefficient: N₂ 999.5/1 = 999.5; H₂ 2976/3 = 992 → H₂ is limiting (smaller value)",
        "n(NH₃) = 2976 ~~mol H₂~~ × (2 mol NH₃ / 3 ~~mol H₂~~) = 1984 mol NH₃",
        "Mass NH₃ = 1984 ~~mol~~ × (17.031 g / 1 ~~mol~~) × (1 ~~kg~~ / 1000 ~~g~~) ... wait — Mass = 1984 × 17.031 = 33780 g = 33.8 kg",
    ],
        "Cancellations: \"kg\" → \"g\" → \"mol H₂\" → \"mol\". H₂ is the (slight) limiting reagent because it has the smaller mol/coefficient ratio."
    ),
    # idx 60: KClO₃ decomp 3-part (consume_after=2)
    ("Mol KClO₃ = 25.00", 2, [
        "n(KClO₃) = 25.00 ~~g~~ × (1 mol / 122.55 ~~g~~) = 0.2040 mol KClO₃",
        "n(O₂) = 0.2040 ~~mol KClO₃~~ × (3 mol O₂ / 2 ~~mol KClO₃~~) = 0.3060 mol O₂",
        "Theoretical mass O₂ = 0.3060 ~~mol~~ × (32.00 g / 1 ~~mol~~) = 9.79 g",
        "% yield = (9.50 ~~g~~ actual / 9.79 ~~g~~ theoretical) × 100% = 97.0%",
        "n(KCl) = 0.2040 ~~mol KClO₃~~ × (2 mol KCl / 2 ~~mol KClO₃~~) = 0.2040 mol KCl",
        "Mass KCl = 0.2040 ~~mol~~ × (74.55 g / 1 ~~mol~~) = 15.21 g",
    ],
        "Five cancellation pairs across three sub-questions. Each product (O₂ and KCl) tracks back to the same starting moles of KClO₃."
    ),
    # idx 61: Methanol combustion
    ("Mol CH₃OH = 64.0", 0, [
        "n(CH₃OH) = 64.0 ~~g~~ × (1 mol / 32.04 ~~g~~) = 1.998 mol CH₃OH",
        "n(O₂) = 1.998 ~~mol CH₃OH~~ × (3 mol O₂ / 2 ~~mol CH₃OH~~) = 2.997 mol O₂",
        "Mass O₂ = 2.997 ~~mol~~ × (32.00 g / 1 ~~mol~~) = 95.9 g",
        "Mass of products (by conservation of mass) = 64.0 g CH₃OH + 95.9 g O₂ = 159.9 g (= mass CO₂ + mass H₂O)",
    ],
        "\"g\" / \"mol CH₃OH\" / \"mol\" cancel in turn. Conservation of mass means total product mass equals total reactant mass — no need to compute CO₂ and H₂O separately."
    ),
    # idx 62: Pb(NO₃)₂ + KI precipitation
    ("Mol Pb(NO₃)₂ = 0.0500", 0, [
        "n(Pb(NO₃)₂) = 50.0 ~~mL~~ × (1 ~~L~~ / 1000 ~~mL~~) × (1.00 mol / 1 ~~L~~) = 0.0500 mol",
        "n(KI) = 50.0 ~~mL~~ × (1 ~~L~~ / 1000 ~~mL~~) × (1.00 mol / 1 ~~L~~) = 0.0500 mol",
        "Divide by coefficient: Pb(NO₃)₂ 0.0500/1 = 0.0500; KI 0.0500/2 = 0.0250 → KI is limiting",
        "n(PbI₂) = 0.0500 ~~mol KI~~ × (1 mol PbI₂ / 2 ~~mol KI~~) = 0.0250 mol PbI₂",
        "Mass PbI₂ = 0.0250 ~~mol~~ × (461.01 g / 1 ~~mol~~) = 11.5 g",
    ],
        "Cancellations chain: \"mL\" → \"L\" twice (volume→moles via molarity), then \"mol KI\" (2:1 stoichiometry), then \"mol\" (mol PbI₂→mass). KI is limiting because there are 2 KI consumed per Pb(NO₃)₂."
    ),
]


if __name__ == "__main__":
    n = apply_rewrites(
        "Chapter_09_Chemical_Calculations_and_Equations.docx",
        REWRITES,
        skip_indices=SKIP,
    )
    print(f"Chapter 9: applied {n} rewrites.")
