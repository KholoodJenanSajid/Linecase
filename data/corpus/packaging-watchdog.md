# Packaging line PKG-A — seal quality and recipe watchdog

Asset: PKG-A, Siemens S7-1500, heat sealer HS-A, vision station VIS-A (Cognex).
Customer: Japanese automotive electronics. Seal spec 3.2 ± 0.3 mm, no wrinkles.

Fault: "WATCHDOG / recipe CRC" on HMI after a brownout, or random recipe 7 loaded instead of recipe 3.

Actions:
- Do not power-cycle the 24V rail.
- Load last known good from MMC slot 2 (labeled LKG-2026-08). Controls tech only.
- If seal wrinkles: check heater HS-A zone 2 thermocouple. Zone 2 open thermocouple looks like "cold seal" and operators over-temp zone 1 — scrap spike.

Vision false rejects:
- Usually lighting shift after bulb change. Recalibrate VIS-A with gold sample GS-PKG-3 stored in the locked drawer.

Parts:
- Thermocouple type K, 2 m, TC-K-2M, bin MRO-PKG-11
- Sealer belt 40 mm, BELT-HS-40

If customer engineer is on site, freeze the lot and print the last 50 VIS-A images into the case file before touching the recipe.
