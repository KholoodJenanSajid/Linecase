# Conveyor CONV-12 jam and motor overload

Asset: CONV-12, Interroll 24V driven rollers, 8 m, photoeye PE-12A infeed / PE-12B outfeed.
PLC tags: CONV12_JAM, CONV12_OL, CONV12_ESTOP.

Symptoms:
- Boxes stall at the CNC outbound chute. Operator often reports "motor humming" or a red OL trip on the small drive (SEW MOVIMOT).
- Photoeye PE-12A blocked > 8 seconds sets jam. Clearing the box without resetting the latch leaves the line dead.

Causes at this plant:
- 48% cardboard flap or stray chip palletizing dunnage under the belt (clean weekly, often skipped on C shift).
- 27% PE-12A dusty / misaligned after forklift bump (alignment mark is a yellow scribe on the bracket).
- 15% downstream packaging starved so boxes back up — not a conveyor fault; check PKG-A infeed.
- 10% roller cartridge failure (listen for grinding at roller 6–7).

Fix path:
1. LOTO CONV-12-DISC.
2. Clear debris. Vacuum chips; do not blow with air toward electronics.
3. Wipe PE-12A lens. Confirm yellow scribe alignment.
4. Reset OL on MOVIMOT (blue button). If OL trips twice in one shift, replace cartridge ROL-IR-90, bin MRO-CONV-06.
5. Jog empty 30 seconds before releasing to production.

Do not bypass PE-12A with tape. Last bypass caused a crushed-hand near-miss (NCR-2025-441).
