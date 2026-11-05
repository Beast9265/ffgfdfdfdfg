# 0108: GMU clock dependency lease

## Evidence and boundary

On 2026-11-06 the user reported physical `a725-voted-roots-v1` PASS on
POCO F5: MX/CX votes, AOP ACD, CX enable, voted GPLL0 parent,
GMU/HUB/XO CFG `00100602/00100603/00100001`, root error 0, root cleanup,
CX rollback and CX/MX release all PASS. This supersedes every earlier
0107-pending statement. Photos were described by the user; no image files
were supplied here. It proves clock-root transactions, not GMU execution.

New opt-in `marblegpu=8 marblegpuvisual=1` combines those root leases with
0104's six normal GMU branch dependencies, then unwinds branches before roots,
CX and rail votes. Modes 0–7 retain their functions and semantics. No CPU,
touch, framebuffer, rootfs, partition, shim-loader or userspace change.

Primary audit/adaptation source: [yukoimi/hackios-marble at
8e50e532f09b3042165048c3c72e04b5a8e68898](https://github.com/yukoimi/hackios-marble/tree/8e50e532f09b3042165048c3c72e04b5a8e68898),
`docs/MARBLE-GPU.md`, `docs/MARBLE-HANDOFF.md`, and
`xnu/files/bsd/dev/marble_gpu/marble_{gmu_clocks,gpu_power,gmu_dependencies,gmu_resources,gmu_memory,gmu_sequencers,gmu_boot,gmu_hfi,gmu_tcm,gmu_votes,gmu_rpmh,gpu_zap,smmu,gpu_cp,gpu_secure,gpu_context,gpu_blit,gpu_service}.h`.
Its transaction nesting/retained-resource boundary is adapted individually;
no bulk driver import or A640/A650/A642L register import. Its clock measurement
engine writes and SMMU branch writes are deliberately outside this milestone.
Its historical UI claims and retired build dependencies do not validate our image.

Register authority remains the pinned Cape sources in
[MARBLE_A725_BRINGUP.md](MARBLE_A725_BRINGUP.md) and
[MARBLE_A725_VOTED_PARENT.md](MARBLE_A725_VOTED_PARENT.md): core-kernel
`992742f9cdcc5ba27e07464a5b2c6a8474ffd1f0`, Cape DT
`2e649a7f3e762903eedad43d8256b91e28b512d8`, KGSL
`51cf4da5f05c82122a22413f0fe310023abb80ee`. The reference independently
pins Xiaomi `48952ed36228217531482b39d5bef13e7fd808ec`.

## Comparison and gates

| Component | Ours / missing functionality | A725 reference / value evidence | Preconditions and ownership/rollback |
|---|---|---|---|
| GPLL0 | 0107 voted qualification; no measured frequency | `marble_gmu_clocks.h`, Cape fixed Lucid-OLE | Inherited vote-run/lock/rate checked repeatedly; never write PLL/APSS vote; lease only GCC+62000 bit16 |
| GMU/HUB/XO roots | 0107 physically PASS; mode8 keeps lease active for branches | Cape GPUCC +9318/+93ec/+9010, CFG100602/100603/100001 | Reject pending/force/unknown source; bounded500us; restore reverse, retain on uncertainty |
| GPUCC/GCC branches | 0104 primitives; mode8 nests them inside roots | Cape branch ops; +913c/+9144, GCC+81154/+81010, +911c/+9148 | GMU/AXI/HUB AON must be inherited ON; never turn them off. CXO/MEMNOC/AHB restore only acquired bit0; max200us or10us vendor delay. QDSS APB skipped per KGSL |
| RPMh MX/CX | command DB ARC leases implemented, physically PASS | `marble_gmu_rpmh.h`, `marble_gmu_dependencies.h` | MX then CX, release CX then MX; mode8 retains on uncertain vote/release |
| AOP ACD | existing exact QMP request, physically PASS | Cape mailbox and `marble_gmu_votes.h` | Before CX; bounded mailbox ACK; ACD has no per-cycle disable contract |
| CX/GX GDSCs | CX tested, GX untouched | `marble_gpu_power.h`, `marble_gmu_gx.h` | No HW-control takeover; CX rollback before releases; failed rollback retains rails. GX requires later GMU-controlled lease |
| PDC/RSCC | not implemented here | `marble_gmu_sequencers.h` | Needs demonstrated branch dependency PASS, idle ownership and bounded restore; separate future stage |
| GPU SMMU | resource inventory only, no context access | `marble_smmu.h`, 4KiB tables, DT SID5 GMU | Physical CB accesses previously reset phone in other Marble work; no inference from readable globals. Need clock/power/SCM and stream ownership; retain DMA RAM if detach uncertain |
| GMU firmware RAM/TCM | validated embedded factory firmware; no loading | `marble_gmu_memory.h`, `marble_gmu_resources.h`, `marble_gmu_tcm.h` | GMU reset ownership, metadata range plan, private RAM, cache visibility and 4KiB permissions before any copy/start |
| HFI | absent | `marble_gmu_hfi.h`, empty stopped queues and protocol ACKs | Owned mapped buffers and proven CM3 readiness; bounded ACK; no freeing queues under running firmware |
| SCM/ZAP | structural/hash checks only | `marble_gpu_zap.h`, `marble_gpu_secure.h` | Signed factory segments, secure carveout/SCM ownership; authentication success distinct from structure validity |
| CP | absent | `marble_gpu_cp.h`, `marble_gpu_context.h`, `marble_gpu_blit.h` | Proven GMU/HFI/GX/SMMU/ZAP, private ring and fence. Need completion plus guarded RAM mutation/readback |
| IOSurface/display sync | existing CPU framebuffer baseline | RedwoodGPU.cpp, eagl.c, gl_osmesa.c and service header | Later per-client VA/BO lifecycle, fences/cache sync, IOSurface pitch/guard rows, presentation ownership; no acceleration claim from CPU updates |

Mode8 is milestone A (stable clock dependencies), not a firmware-start stage.
Failure blocks every later stage. AON refusal and branch timeout/failed cleanup
retain roots, CX and rails. Failed CX rollback retains rails. Failed CX release
retains MX. No automatic retry. GPLL0 global configuration and inherited vote
are read-only. Root and branch sibling bits are preserved.

## Physical test

The ten-second screen identifies `a725-gmu-dependencies-v1 (mode8)` and shows
power stages, GPLL0, three root CFGs, each branch CBCR/inherited flag, branch
cleanup, root cleanup, CX rollback, rail releases and RESOURCE RETAINED.
`ACKNOWLEDGED` is the implementation's PASS label.

PASS: all power stages and parent/roots ACKNOWLEDGED; all six normal branches
ACKNOWLEDGED; optional `apb_pclk` NOT ATTEMPTED; branch error0; branch/root
cleanup, CX rollback and both releases ACKNOWLEDGED; RESOURCE RETAINED0;
terminal `stage=8 stop=DEPENDENCY_TEST_COMPLETE result=PASS`; then the existing
SpringBoard/touch/eight-core baseline. This still does not prove GMU execution.

FAIL: FAILED, TIMEOUT, missing required branch, nonzero error, retained resources,
hang, reboot or baseline regression. Photograph the screen. Cold reboot and
analyze before another GPU experiment, including after RESOURCE RETAINED.
No automated phone interaction is permitted.

Unverified assumptions: register qualification does not measure clock frequency;
AON branches may not be inherited enabled on this boot (safe refusal expected
in that case); branch MMIO success is not firmware readiness. Physical mode8
result remains pending until the user tests this exact image.

## Successive hardware milestones

After physical mode8 PASS: separately audit/test PDC/RSCC and CX secure-init;
then inactive 4KiB GMU mapping and firmware memory plan; verify TCM copies while
reset; secure ZAP with unload; bounded CM3 startup/readiness; HFI queue init and
ACKs; GX lease; minimal CP command/fence/guarded readback; rendered pattern and
scanout. Each requires its own opt-in test and failure/retention boundary.
Only then expose the existing IOKit/Mesa25 FD725/EAGL architecture to
CoreAnimation and SpringBoard. Metal is not a prerequisite. Later measure
presentation intervals, actual refresh mode, buffer retirement and copies.

## Other reference audit (2026-11-06)

Remote snapshots and selected source files are cached under ignored
`research/a725-0108/remotes/`. Latest commits checked:

| Repository | Commit | Relevance / limit |
|---|---|---|
| HeliumStudio-Dev/hackios-xnu-kernel raphael-bringup | 57722468a3774e2ec60017705ec356ae9b31f40e | RAPHAEL.md distinguishes host/QEMU from physical logs; adopt triangle/readback/continued submissions methodology only |
| oosexgang/hakios-xnu-kernel | 87bf4851bcc9cbb24fd79997820aa3661abe4ea5 | IOKit/EAGL/IOSurface architecture; 642L performance is not A725 evidence |
| oosexgang/hakios-metal | d7495f43485176785a03a77c4fb82cfff0204043 | Rendering resolution/UI measurements; defer until execution verified |
| aTechGeekDev/ios-apollo | 1f75f381e31da96de537653fbac2252d2eb80418 | Turnip ownership/fence retirement and CA bridge; no A650 power/register import |
| MakrSas/ios-topaz | e4772911e116ab4ab6c4ac1f38e6106fefe8b483 | EAGL/IOSurface timing/allocation; no display change in this stage |
| NWylynko/ios-flame | 745c4341af86089efb0df851fa8a27fb8face624 | iOS16 userspace interface reference |
| UniXNU/UniXNU | 13e5973748a8447cbb90520c9a2dd5e65e272435 | Architecture comparison |
| UniXNU/AdrenoMetal | e82788dd367753802ec2e00476ab27addfb46834 | Device/service architecture; Metal deferred |
| limonetexd/ios-sweet-gpu | 07b4dfb290f05eea0393244af10fad8b4c56c5c5 | Pending patches remain unimported; later stride/cache/guard-row audit |
| jebbranch/ios-port-marble | 7fca21b1eaf41004dabf91a9499ff740dbb601bb | Latest commits focus log-tail/OOB diagnostics, not proof of GPU execution |
| G3134377393/ios-port-marble | 00248e849e0290a880a4d925e46cd9b9bea7d8c7 | Latest AKS client logging, not a clock ownership authority |
| MiLacy/UniXNU-marble | 78f4e7bf00e88129f8b6ef5680d81770d386832d | Packaging work; no imported hardware operations |
| dipa-studio/ios-sweet | 45263bee51df4a0f55cdf9c649af886399488ddb | Latest website work; SWEET hardware not applicable |

These are source audits, not independent physical verification of those projects.
