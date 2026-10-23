# MARBLE diagnostic-first Setup boot (2026-10-23)

The user physically booted setup-fast and left it overnight. FairPlay flood
suppression passed. The old migration progress UI no longer remains on screen;
setup-fast changed/bypassed that visible wall, **not proof of completed migration**.
Later userspace runs, with nanotimekitcompaniond/maintenanced relaunches and
ReportCrash AKS selector 17 traffic. No panic/reboot was observed. No Hello
appeared. The blocker remains unknown. AKS traffic from ReportCrash does not
identify which process crashed, or prove ReportCrash is crashing.

## Comparison with SWEET 0057u / v12

Audited the final source replay, historical patches 0050–0057, root recipe,
and NOTES.md's 2026-10-17 Hello handoff, rather than reverting to old graphics.

| Prerequisite | Current MARBLE evidence |
| --- | --- |
| 0057 no external identity resolver | `config/MASTER.arm64.marble` FILESYS_BASE omits `config_ext_resolver`, just like final SWEET. Actual DEVELOPMENT/MARBLE CI compile flags lack CONFIG_EXT_RESOLVER. Local UID/GID to GUID compatibility mapping remains available for ACLs without memberd. |
| 0055 AKS 35 / 101 | Shared final SweetKeyStore.cpp: 35 (`kAKSGetExtDeviceState`) shares device-state DER response with 17; 101 (`kAKSAssertConsume`) succeeds in the no-output group. Both implementation and AppleKeyStore personality enabled on MARBLE. |
| 0056 throttle | Shared final SweetFramebuffer.cpp retains pending-swap recording and dirty/modulo vsync presentation, default 10 Hz. No framebuffer changes in this task. |
| Containers / ACLs | Prior focused mounted setup-fast audit recorded Bundle 33:33 0755 and Data/System, Shared/SystemGroup, Temp 0:0 0755; copied image and hierarchy unchanged. CONFIG_PERSONAS retained; no ext resolver. No new root mount or phone inspection in this task. |
| 0052 RENAME_SWAP | MARBLE shares exact ENOTSUP + exact VFS_RENAME_SWAP + two regular files + same mount VNOP_EXCHANGE fallback in kpi_vfs.c. Unchanged. |
| 0050 Sandbox | Existing sweet_amfi policy registration includes Sandbox compatibility policy; MARBLE register call and shared policy remain. No policy change. |
| Migration preferences / UUID | Existing setup-fast plain migration LastSystemVersion=20H392 and stable UUID/ByHost state retained. No preference changes. |
| GUI launch stderr | GUI launchd jobs retain original output configuration; no /dev/console job redirection. Existing /dev/null tee reused. |
| Graphics | Final shared IOSurface/AppleCLCD code, disp0 publishing, scale 3, 1125x2436, physical 1080x2400, and console retained. No GPU/SMP or graphics change. |

SWEET v12 also moved VirtualAudio.plugin from HAL to HAL.disabled. The recorded
analysis identified mediaserverd's NULL virtual-default-device fault in
ApplyBeamFormerPreference/VirtualAudio_PlugIn::SetPropertyData, not a proven
SpringBoard/Setup dependency. Its effect was still marked **unverified** at
Hello. A later v14 mediaserverd fix addressed a different NULL GL portrait-filter
prewarm path. Neither finding establishes VirtualAudio as this MARBLE GUI gate.
Leave it alone until crash evidence connects it to the GUI path.

At successful 0057u/v12 Hello, SpringBoard, backboardd and Setup ran without GUI
crashes. The handoff still listed installcoordinationd (0057 fix unverified),
mediaserverd (VirtualAudio effect unverified), mobileactivationd (~100/boot,
not analysed), bluetoothd and FairPlay loops. Thus daemon crashes alone are
not sufficient evidence of a Hello blocker. No specific v12 observation for
nanotimekitcompaniond, maintenanced or ReportCrash is recorded in the available
handoff; historical raw logs and external codex reports are not present in this
workspace. Their absence from the summary is not proof that they were healthy.
The source/root history in NOTES.md is the available evidence for those logs.

## Diagnostic scope and strict budgets

Everything below requires `marbleguidiag=1`; all matches are exact full `p_name`
via `proc_selfname`, never `p_comm`/`proc_name` truncations. Shared allowlist:
SpringBoard, backboardd, Setup, nanotimekitcompaniond, maintenanced, ReportCrash,
mobileactivationd, installcoordinationd, mediaserverd. Unknown names/prefixes
are rejected. Saturating atomic reservations prevent preemption overruns.

* Abnormal exits: 32 events/boot, at most 4/name across respawns. One signal /
  exception-code / subcode / exit-status line, plus one namespace/code/reason
  line if a reason exists; **64 CRASH lines maximum**, reason text capped at
  512 characters. Hook precedes the crash-report eligibility filter so
  NO_CRASH_REPORT does not hide abnormal exits. Original critical-exit,
  signal, crash-report and corpse behavior is unchanged.
* /dev/null stdout/stderr tee: 64 chunks/name across respawns and 512 chunks
  total/boot; at most 256 input bytes/chunk = **16 KiB/name, 128 KiB/boot**.
  This includes stdout written to the same device; not every os_log message
  necessarily reaches stderr. No launchd plist redirection/environment edits.
* Heap: SIGABRT/SIGTRAP only, same allowlist **except ReportCrash**; 4 scans/boot,
  at most 1/name; 4096 region queries/scan; **16 MiB attempted copy/scan,
  64 MiB/boot**, counting failed copies with a strict final-chunk clamp.
  Read/write heap tags 1–11 only, 64 KiB buffer, 64 strings/scan (256/boot),
  each at most 159 characters, plus scan begin/end lines. Zero-size/overflow
  terminates traversal. Strings must contain exception/reason/abort/denial/
  sandbox/container/entitlement/activation/service/EACCES/failure keywords.
  Original SWEET scan defaults, budgets and string selection are unchanged.
* Existing short exec logger already uses full `p_name` after set_proc_name;
  prints `exec backboardd`, `exec SpringBoard`, `exec Setup` when each passes
  the existing iOS exec authorization path. It is not capped by the new
  diagnostic budgets. Exec authorization itself is unchanged. An exec line
  does not prove an application reached its main run loop.

## Sampler decision

Not ported. Final SWEET sweet_sample_task holds task_lock over all task threads
and calls vm_map_read_user for frame pointers. vm_map.c explicitly permits
that reader to block on page faults; it switches maps and calls copyin. There
is no thread-count or elapsed-time bound. Merely reducing SWEET's 40 iterations
and 120-second spacing would not establish safe CPU0 latency or lock behavior.
A resident-only reader and safely retained thread snapshots need separate
review; importing that architecture is beyond this diagnostic extension.
SWEET's sampler remains byte-identical in behavior and excluded from MARBLE.

## Next physical interpretation

Keep the installed setup-fast userdata. Boot only the new kernel image;
**no userdata flash**. Record output from the beginning (budgets are per boot).

* `exec Setup` followed by `CRASH Setup`: read stderr/namespace/reason/STR text.
* No `exec Setup`: capture SpringBoard/backboardd exec, crash and IOKit output.
  Whether launchd/SpringBoard/activation withheld launch remains a question
  for that evidence; current observations do not establish a specific gate.
* Setup executes without an abnormal exit but has no UI: investigate
  SpringBoard/backboardd launch/scene/check-in state, not unrelated daemons.
  Without a safe sampler this build alone cannot prove a live process's
  synchronous wait; it is not an automatic diagnosis of every possible stall.

No functional fix or physical success is claimed. No phone commands were run.
