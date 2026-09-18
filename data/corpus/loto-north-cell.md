# Lockout / tagout — North cell (LOTO-N2)

Standard: OSHA-equivalent plant policy APX-EHS-07 plus customer Honda SQM overlay.

For HAAS-VF2-04:
- Energy sources: 415V 3-phase at N2-DISC-04, compressed air drop AIR-N2-4 (lock ball valve), hydraulic unit HU-04.
- Isolation sequence: feed hold → spindle stop → E-stop → open N2-DISC-04 → apply personal lock (red) + supervisor lock (blue) → try-start prove-out → bleed air.
- Restart sequence is reverse, with two-person verify if the job is automotive PPAP.

For CONV-12:
- Disconnect CONV-12-DISC on the east column. Pinch points at infeed rollers. Never reach under belt while live.

For PKG-A PLC cabinet:
- Only controls techs with S7-1500 card. Do not cycle 24V rail to "reset" a watchdog — that corrupts recipe memory.

PPE: safety glasses, cut gloves for chip work, hearing protection in North-2.
If a Japanese visiting engineer is present, brief in English then Japanese; do not skip LOTO for "just a look."
