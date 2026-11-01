# Noctua cooling update — 2026-10-25
User installed NF-A12x25 G2 PWM Sx2-PP, two 120mm fans, rear label toward top radiator (exhaust). User confirmed pump=AIO_PUMP, fans=CPU_FAN and CHA_FAN.
Verified NCT6799 mapping: CPU_FAN fan2/pwm2; CHA_FAN fan7/pwm7; AIO_PUMP fan6/pwm6.
Both fan curves: 30C/70, 50C/100, 65C/135, 75C/175, 85C/255, CPU source selector8, PWM mode, Smart Fan IV enable5. Pump full output255. No response-delay changes.
Saved in bin/fan-curve.sh and installed /usr/local/bin/fan-curve.sh; enabled fan-curve.service restarted successfully. Timestamped pre-change backups retained.
Hardware Monitor now labels both radiator fans and pump correctly.
Full-output brief check: fans ~1744/1846 RPM, pump ~4103 RPM; CPU ~77-78C. Automatic check: fans ~1129/1182 RPM, pump4090 RPM, CPU83.6C. Light-load CPU remains warmer than desired; not resolved. No stress test or reboot performed; boot persistence relies on verified enabled service.

Follow-up: balance_power trial reduced package power modestly and temperature slightly; original CPU preferences restored. NCT temperature selector8 is PECI/TSI Agent 0 Calibration (~70C while k10temp ~81C). Full-speed threshold85 refers to that sensor, NOT guaranteed package85. Direct TSI0_TEMP/temp13 selection rejected EINVAL and original sources restored. Do not claim the old10C thermal margin. Further cooler-contact/heat-transfer checks need physical observations. No stress test started.

Sensor correction applied: both fans now use 30/70,50/100,65/135,70/175,75/255 (calibrated Celsius/PWM). Full-speed calibrated threshold reduced85->75; no claim of exact package threshold. Low points unchanged. Pump full output retained. Service restarted successfully.

Linux-only idle comparison: 5min automatic82.75C/48.24W/1.04percentbusy; 2min full-fans82.65C/47.88W/1.03percentbusy; 1min recovery82.58C/48.07W. Negligible0.1C difference. Both full fan speeds1739.5/1828.8RPM, pump4079.6RPM. No stress workload. Found active processor.max_cstate=1 and onlyPOLL/C1 states; historical June7 notes state freezes persisted with this mitigation. BIOS is now1805. User approved removing only max_cstate=1 and normal Linux reboot for comparison. Original boot/deployment details and rollback command saved under docs/hardware-runs/2026-10-25-noctua.

## Completed normal idle-state trial

No BIOS navigation or changes. User approved removing only processor.max_cstate=1 and a normal Linux reboot. Verified no other effective boot argument differences. BIOS1805 and firmware-reported6400MT/s retained. CPU preference balance_performance unchanged.

Five-minute automatic baseline: CPU82.75C, package48.24W, CPU busy1.04%, fan11740RPM/fan21331RPM, pump4075RPM.
Two-minute full-fan comparison: CPU82.65C, package47.88W, busy1.03%, fans1739.5/1828.8RPM, pump4079.6RPM. Extra fan airflow made negligible difference at this light workload; this does not prove coolant flow or mounting health.

Found boot restriction processor.max_cstate=1, module limit1 and onlyPOLL/C1 available. Historical June7 NVIDIA GSP troubleshooting notes explicitly say the system froze with C1-only already active. The older June6 workaround preceded the BIOS1805 update.

After authorized removal and reboot: POLL/C1/C2/C3 available and enabled. Two minutes settling followed by three minutes measured idle. CPU78.86C mean(range77.125..81), package36.95W, busy0.74%, fans1056/1113RPM, pump4072RPM. Last average-core idle residency C3about94%. Idle package power fell about23%, temperature about3.9C, with lower fan speeds. CPU usage is not exactly identical and room temperature was not measured; this is one short before/after trial, not long-term stability proof.

No new hardware-error/MCE/EDAC/thermal-throttle messages matched in the current boot's kernel log. No stress test or game performance claim. Old hard locks and RAM stability are not declared resolved.

Fan curve remains CPU_FAN/pwm2 and CHA_FAN/pwm7, PWM mode, hardware auto mode5, calibrated sensor8. Points30C/70,50/100,65/135,70/175,75/255. These are calibrated-controller temperatures, not exact CPU package thresholds. Pump=AIO_PUMP/fan6, full output. Controller fan outputs tracked each other after reboot. The before-reboot output mismatch was observed; no unproven driver/firmware root cause is asserted.

Setup script desktop.d/idle-freeze-fix.sh now preserves watchdog/hang-capture installation but makes the historical C1 restriction opt-in via BAZZITE_LIMIT_CSTATES=1. Default setup does not re-add it or alter other existing boot arguments. Shell syntax passed; the full setup script was not run. Original script and boot/deployment details preserved here. Watchdog remains1minute.

Rollback if instability recurs: sudo rpm-ostree kargs --append-if-missing=processor.max_cstate=1, then normal reboot. If Linux cannot be reached, select previous Bazzite deployment from boot menu. No firmware settings are required for rollback.

Files: fan-comparison.jsonl, fan-comparison-summary.json, normal-idle-states.jsonl, normal-idle-summary.json, post-boot-verification.json, boot/deployment snapshots, rollback.txt. Power is zenergy socket energy delta; temperatures use k10temp and corroborating TSI; traces sampled every5seconds. CCD fields in fan-comparison.jsonl normalized toCelsius; sysfs *_input fields keep native units.


### Clean launcher-exit cooldown, 2026-10-25 02:57 UTC
Closed residual upc.exe and xalia.exe with SIGTERM; game already closed. No BIOS, voltage, C-state or fan-curve changes. Three-minute trace saved in docs/hardware-runs/2026-10-25-assassins-creed/clean-cooldown.json. Final minute means: {"CPU_C": 73.69, "package_W": 38.29, "fan1_RPM": 873.5, "fan2_RPM": 926.5, "pump_RPM": 4075.0}. CPU fell from preceding ~90 C observation to ~73.5 C; fans settled below 1000 RPM. Residual launcher load contributed to heat. This does not prove cooler contact or circulation is healthy. MSI stock fans rated 2000 RPM, 78.73 CFM, 2.39 mmH2O; Noctua pair nominal 1800 RPM, 63.15 CFM, 3.14 mmH2O. Separate vendor endpoints are not radiator airflow or equal-noise comparisons; fan downgrade not established. Temporary game limiter restored to original 0/60 after game exit.


### Idle efficiency preference comparison
PowerTOP absent; used zenergy package energy, k10temp, fan tachometers, and turbostat instead. Core C3 residency 88–91% across two 3-second samples; package 38.6–39.8 W, core power 6.6–7.6 W. Tuned balanced-bazzite inherits balance_performance EPP. Controlled one-minute-per-setting test (last 40 seconds averaged): balance_performance 74.62 C, 38.04 W, fans 893/950 RPM; balance_power 74.09 C, 35.97 W, fans 891/947 RPM. Small ~2 W benefit, negligible fan-speed change. Original EPP restored on all policies; no persistent power-profile changes or blanket PowerTOP autotuning. Raw evidence: hardware-runs/2026-10-25-assassins-creed/idle-epp-comparison.json. Short sequential trial is directional, not definitive equilibrium comparison.


### Expanded AMD EPP sweep
Four 90-second phases; first 30 seconds of each excluded from means. Results: [{"phase": "baseline_before", "EPP": "balance_performance", "means": {"CPU_C": 75.7, "package_W": 39.16, "busy_pct": 1.16, "fan1_RPM": 907.75, "fan2_RPM": 965.92, "pump_RPM": 4063.92}}, {"phase": "balanced_efficiency", "EPP": "balance_power", "means": {"CPU_C": 74.56, "package_W": 36.23, "busy_pct": 1.3, "fan1_RPM": 892.58, "fan2_RPM": 949.42, "pump_RPM": 4065.0}}, {"phase": "maximum_efficiency", "EPP": "power", "means": {"CPU_C": 74.66, "package_W": 36.23, "busy_pct": 1.28, "fan1_RPM": 894.17, "fan2_RPM": 952.17, "pump_RPM": 4072.17}}, {"phase": "baseline_after", "EPP": "balance_performance", "means": {"CPU_C": 76.41, "package_W": 39.24, "busy_pct": 1.17, "fan1_RPM": 932.08, "fan2_RPM": 990.0, "pump_RPM": 4069.92}}]. Repeated baseline supports ~3W lower near-idle package power with balance_power; power offered no extra benefit. Runtime EPP left at balance_power on all policies; no persistent profile change, boost/core/BIOS/fan settings untouched. Reboot restores tuned balanced-bazzite defaults. Gaming performance under retained preference not tested.


### Side-panel airflow comparison, room 72 F / 22.2 C
User confirmed both panels on, then both side panels physically removed; top left in place. Fans fixed full, pump unchanged, EPP balance_power. Closed final minute: {"CPU_C": 77.35, "package_W": 37.62, "fan1_RPM": 1740.58, "fan2_RPM": 1845.83, "pump_RPM": 4079.08}. Open final minute: {"CPU_C": 78.91, "package_W": 37.75, "fan1_RPM": 1740.0, "fan2_RPM": 1844.67, "pump_RPM": 4081.25}. Original 10-minute logger restored fan curve before user panel-off confirmation, so open sample was restarted for 3 minutes at matching full fan settings. Normal curve verified restored afterward (both enable=5). No CPU cooling improvement from side removal; 1.6 C higher open is not proof open panels worsen cooling because phases were sequential with a gap and background/thermal drift possible. Side-panel restriction not supported as primary cause of high near-idle Tctl; gaming airflow effect and cooler contact/circulation remain unproven.


### Top cover removed, front still fitted
User said all but front removed; interpreted and stated back as sides and top off, front on. Three-minute sample at fixed full fans, final minute: {"CPU_C": 79.96, "package_W": 37.59, "fan1_RPM": 1740.75, "fan2_RPM": 1844.42, "pump_RPM": 4090.33}. Normal fan curve restored and verified by restoration marker. No meaningful cooling improvement over previous samples at similar power. Sequential phases and thermal drift prevent interpreting small increases as causal. Front-off test pending physical confirmation.


### All four panels removed: front, top, both sides
User explicitly confirmed all four off and requested repeat to test front-side radiator airflow restriction. Three minutes at fixed full fans with unchanged pump and balance_power EPP. Final minute: {"CPU_C": 81.03, "package_W": 37.98, "fan1_RPM": 1739.92, "fan2_RPM": 1843.25, "pump_RPM": 4094.42}. Normal fan curve restored afterward, both channels verified auto mode 5. Compared with top/sides-off front-on sample (~79.96 C at37.59 W), no clear improvement. Small sequential differences are not causal proof. Exterior panel restriction does not explain the high near-idle temperature in these short samples; internal obstructions, cooler contact/circulation, sensor interpretation remain possible. No BIOS changes.


### Sensor response and remaining diagnostics
Monitor CPU package row clarified as CPU Tctl; source/thresholds unchanged. TSI0 tracks same CPU signal, not independent thermometer. Lower CCD values do not justify subtracting an offset. Guarded two-worker int64 test terminated at first 2-second sample: Tctl94.625C, CCD1 95.375C, CCD2 70C, package76.76W. After70s recovery: Tctl81C, CCD1 67.125C, CCD2 64.625C, package40.04W. Normal fan curve restored. Real localized response supports taking readings seriously but does not diagnose paste or circulation. Idle core power~5–6W, package~38W, core C3~88–92%. Boot-log checks: no matching GPU Xid, hardware/MCE, OOM, hung-task signatures; both DIMMs configured6400. Fan output mismatch recurred despite matching curve/source: pwm2=255,pwm7=175. target_temp50C vs0 differs, relevance in SmartFanIV unresolved; no permanent fan-control changes. No further heavy-load tests pending mechanical inspection. Evidence hardware-runs/2026-10-25-sensor-response/.


### First post-repaste startup and guarded test
User cleaned CPU/block, applied MX-6 cross (photos reviewed), alternately seated two spring-loaded AMD mounting screws, and powered on desktop. User confirms panels still off. Reboot reset EPP to balance_performance; restored previous runtime balance_power for comparison, no persistent changes. Early automatic-fan reading Tctl67.5C, fans809/867RPM,pump4141. Controlled full-fan baseline40s ended Tctl73C, package36.72W. Two-worker int64 load guard terminated after4s at Tctl94.625C, CCD1 94.875C, package79.92W. After40s recovery Tctl75C, package37.33W. Normal fan curve restored. Earlier pre-repaste controlled test cutoff after2s with CCD1 95.375C; different boot/thermal conditions preclude quantitative improvement claim. AC3751950 launch requested, original limiter0/60 and raytracing/upscaler settings preserved. New guarded logger closes only game after two3s samples CPU(anyTctl/CCD)>=97C or GPU>=90C. Moving benchmark not yet user-confirmed.


Post-repaste AC launch reached Tctl97.375C at103.61W with radiator1741/1844RPM,pump4090RPM; guard fired before moving benchmark confirmed. Game process remained present on follow-up, so explicit termination retried with bounded SIGKILL fallback. Repaste did not resolve load-temperature issue; cannot diagnose AIO failure solely from these readings. Stop further repeat benchmark loops and investigate mount/contact versus circulation or test known-good cooler.
