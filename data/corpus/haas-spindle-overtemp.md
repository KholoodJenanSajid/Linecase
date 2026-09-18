# Haas VF-2 (HAAS-VF2-04) — spindle thermal alarm SOP

Asset: HAAS-VF2-04
Alarm: SPINDLE OVERTEMP / alarm 151 / "Spindle temperature exceeded"
Typical HMI: red banner, spindle load > 90%, coolant flow warning optional.

Immediate actions (do not skip LOTO):
1. Press FEED HOLD. Do not rapid-retract if the tool is in a cut — feed hold first.
2. If smoke or burning smell: E-STOP, then LOTO at the main disconnect (panel N2-DISC-04).
3. Allow spindle to idle-cool 8 minutes if temperature is 70–85 C. Above 90 C, power down and wait 20 minutes.

Root causes ranked by this plant's last 18 months:
- 61% coolant concentration drifted below 6% (refractometer). Target 8–10% for aluminum 6061.
- 22% chip packing in the spindle nose / flood nozzle misaligned.
- 11% worn spindle bearings (vibration at 8–12 kHz on the handheld meter).
- 6% cabinet chiller failed (look for chiller E-04 amber LED).

Corrective:
- Check coolant tank T-04. If Brix < 6%, add concentrate per SDS-COOL-2, recirc 10 min, retest.
- Inspect nozzle: should hit the tool-work interface, not the way cover.
- If alarm returns within 30 minutes after coolant correction, escalate to spindle specialist and quarantine the job (do not run production).

Parts:
- Coolant concentrate Apex-Kool AL, bin RAW-C-12, min 1 jerrycan
- Flood nozzle 1/4 NPT, part NZ-FL-14
- Spindle bearing kit SBK-VF2, vendor Haas, lead 9 days (do not install on shift without specialist)

Citation rule: never restart after overtemp without recording spindle temp at alarm and at restart in the case file.
