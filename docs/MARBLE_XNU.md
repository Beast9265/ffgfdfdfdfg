# First one-core XNU execution on MARBLE

Source preparation only. XNU has **not** been physically booted on MARBLE.
The full DEVELOPMENT kernel compile/link is pending human review and CI.
No CI run/ID, commit, push, fastboot, partition write or device access occurred.

## Source and machine configuration

`xnu/patches/0082-marble-onecpu-bringup.patch` applies after 0081 to
xnu-8796.141.3. Separate `MARBLE.h` and `MASTER.arm64.marble` select plain
arm64, `-march=armv8.2-a+crypto`, NO_MONITOR, NO_ECORE, ARM_ARCH_TIMER,
16K pages, GICv3, 64-byte cache lines, MAX_CPUS=1 and MAX_CPU_CLUSTERS=1.
The master config derives from the final patched SWEET config, retaining
open-source assembly/pmap, software KPC and common kernel facilities;
`sweet_hfs` is removed. SWEET-only storage, USB, touch, display and SMP
translation units remain disabled by their existing guards.

MarblePlatformExpert matches `xiaomi,marble`. MarbleCPU matches
`qcom,marble-cpu`; it derives from the original 0018 one-CPU driver, not the
later SWEET SMP driver. It checks one-CPU topology, registers the boot CPU,
uses SGI1 self-signalling and returns KERN_NOT_SUPPORTED from startCPU.
There is no PSCI CPU_ON, secondary entry or secondary registration path.

### Complete conditional-sharing inventory

All broadenings are explicit `SWEET || MARBLE` (or a make filter), leaving
SWEET constants and selected behavior unchanged:

| Files/conditions | Reason |
| --- | --- |
| `makedefs/MakeInc.def`: supported list, flags, plain-arm64 exception | Recognize MARBLE; avoid arm64e/PAC |
| `osfmk/arm64/proc_reg.h`: SWEET cache-line branch | Both use 64-byte I/D lines |
| `pexpert/arm/pe_fiq.c`: timer variable, ADT timer lookup, Group-1 setup, BPR1, distributor/IGRPEN1; `pexpert/pexpert/arm/protos.h`: timer extern; `osfmk/arm64/sleh.c`: IRQ timer/SGI dispatch | Verified Qualcomm Group-1 routing; MARBLE constants 27/1/0x40000 |
| `osfmk/arm64/start.s`: entry marker, invalidation barriers, SCTLR readback exception | Diagnosable generic ARM entry; no SWEET secondary/SMP branches shared |
| `osfmk/arm64/sweet_early.c`, `.h`: early console declarations/implementation; `arm_vm_init.c`: final mapping and relocation; `osfmk/kern/debug.c`: early panic hook | Output before thread state and after TTBR0 teardown |
| `osfmk/arm64/machine_routines.c`: **only** ml_enable_monitor stub | Required call from arm_vm_init with NO_MONITOR; SMP guards unchanged |
| `osfmk/vm/vm_kern.c`: RNG declarations/helper/init/use; `osfmk/prng/prng_random.c`: software PRNG/init; `osfmk/prng/entropy.c`: portable SHA/HMAC seed/add/generate paths and exclusion of closed corecrypto path | Supply early randomness without Apple's closed corecrypto registration |
| `bsd/kern/kern_trustcache.c`: unavailable static/load/query/runtime/init/UUID operations | No Apple trust-cache runtime provider |
| `bsd/conf/Makefile.template`: pthread include paths; `bsd/sys/pthread_internal.h`: wait-element ABI; `bsd/pthread/sweet_pthread_{init,support,synch}.c`: provider guards | Existing built-in libpthread must compile with matching ABI and initialize |
| `libkern/conf/Makefile.template`: portable crypto includes/compiler options; `libkern/crypto/corecrypto_{aes,md5,sha1,sha2}.c`: software API providers (SHA256 and SHA384/512 branches) | Required exported legacy crypto interfaces without closed provider |
| `libkern/crypto/sweet_aes.c`, `sweet_aes_ct{,_enc,_dec,_cbcenc,_cbcdec}.c`, `sweet_{md5,sha1,sha2big,dec32le,enc32le,dec32be,enc32be,dec64be,enc64be}.c`: provider guards | Compile the portable implementations/codecs those interfaces reference |
| `bsd/kern/sweet_amfi.c`, `iokit/Kernel/arm/SweetEntitlements.cpp`: provider guards | Required built-in AMFI interface and its final-series entitlement dependencies; no userspace boot needed for this milestone |
| `0019-stage-libpthread.sh`, `0020-stage-bearssl.sh`: board gates | Stage the sources used by those required link providers |
| `0026-stage-hfs.sh`: board gate | Historical 0031/0052 patches require HFS source **to apply**, even though MARBLE does not select/build HFS |

Additional new MARBLE-only matching and board-selection guards introduce
its own drivers/config. SWEET.h gains aliases for shared timer/SGI symbols;
values remain 19 and 1. No historical `.patch` file was rewritten.

## GIC and framebuffer safety

MARBLE uses virtual timer INTID 27, SGI1, GICR stride 0x40000 and Group-1 IRQ
handling, not Apple's Group-0/FIQ path. The priority loop is guarded by
`!defined(MARBLE)`. MARBLE.h deliberately has no GICR_IPRIORITYR definition.
The preprocessed MARBLE GIC contains no priority access; SWEET's preprocessed
GIC is byte-identical to its baseline. ICC_BPR1/ICC_CTLR setup is inherited
from SWEET and still needs physical validation on MARBLE.

The normal framebuffer console maps the ADT's **0x009e3400** visible length.
Both bootstrap and permanent early aliases use L3 pages on MARBLE, not
SWEET's 32 MiB block. 633 pages map 0x009e4000 bytes: 0xc00 bytes of final
page rounding is unavoidable with 16K granules. No larger splash region
is mapped as framebuffer memory. The bootstrap preserves RAM's existing
L2: both framebuffer and 0x840000000 RAM occupy L1[0] with 16K pages.
Historical early-console function names and on-screen SWEET EARLY labels
remain cosmetic shared names.

## ADT and payload

`python3 tools/mkadt.py OUT.adt --marble --dump` produces a one-CPU tree.
Parsed assertions verify:

- /chosen DRAM: 0x840000000 + 0x100000000; synthetic ECID 0x4d4152424c450001.
- CPU0 reg=0, compatible `qcom,marble-cpu`, `ARM,v8`; 19.2 MHz timebase.
- SOC_BASE=0x01000000; relative GIC regs resolve to GICD 0x17100000/0x10000,
  GICR 0x17180000/0x200000; virtual timer INTID 27.
- sweet-fbcon: 0xb8000000/0x009e3400, 1080x2400, stride 4320.
- Root: D22AP, iPhone10,3, xiaomi,marble, qcom,sm7475, AppleARM; chip-id 0x8015.
- No UFS, touch, GPU or display-driver nodes. arm-io contains only GIC.

Local D22AP artifact is absent: generator warns and omits optional /product.
Root iPhone X identity remains present. CPU clock-frequency is an inherited
placeholder, not a physical MARBLE measurement; timer timebase is verified.
SWEET and QEMU defaults are preserved; MARBLE rejects qemu/highmem combinations.

## Build and packaging after review

```
BOARD=marble-xnu shim/build.sh
python3 tools/mkadt.py /tmp/marble.adt --marble --dump
python3 tools/mkpayload.py KERNEL.DEVELOPMENT.MARBLE /tmp/marble.adt /tmp/marble.payload \
  --cmdline 'debug=0xc serial=3 cpus=1 keepsyms=1 -enable_kprintf_spam'
python3 tools/mkbootv4_marble.py repack STOCK_BOOT.img shim/out/marble-xnu/Image \
  /tmp/marble-xnu.img --xnu-payload /tmp/marble.payload
python3 tools/mkbootv4_marble.py inspect /tmp/marble-xnu.img
```

marble-xnu compiles SHIM_MARBLE + SHIM_MARBLE_XNU with fdt.c/loader.c,
preserves the 64 GiB identity-map design, and omits UFS code. It immediately
uses the existing loader, staying MMU-off for copying/jumping as on SWEET.
An optional payload argument is checked and copied to out/marble-xnu/ramdisk.bin;
packaging is explicitly separate: pass it to the v4 packer's --xnu-payload option.
A loader error remains on screen indefinitely. Diagnostic BOARD=marble and
BOARD=sweet remain separate.

The packer preserves stock metadata, changes kernel and (with explicit
--ramdisk or --xnu-payload) generic ramdisk sizes/content, rejects signed sources, normalizes
padding, copies no AVB footer/partition padding, and exclusively creates its
output. Both independent post-write SHA256 checks and inspect/reparse run.
vendor_boot is never an input or output of repack.

After human source review, commit/push as separately authorized, then run:

```
gh workflow run xnu.yml \
  -R Beast9265/ios-marble \
  --ref marble \
  -f macos_version=13.5 \
  -f kernel_config=DEVELOPMENT \
  -f machine_config=MARBLE \
  -f keep_going=true
```

The existing macos-14 workflow is unchanged. No local Linux full-XNU build.

## Boot-v4 wrapper correction (2026-10-21)

The generic ramdisk is now raw SWEETXNU bytes followed by an exact 16-byte
footer: `MRBLXNU1` then LE64 raw payload size. Use `--xnu-payload`, mutually
exclusive with arbitrary `--ramdisk`. mkpayload.py's format is unchanged.
MARBLE's loader strips an optional Android bootconfig trailer by checking
final `#BOOTCONFIG\n` (12 bytes), requiring span >=20, reading LE32 size at
end-20, checking size <=span-20, and setting ramdisk_end=end-20-size. Size
includes padding. It reads the footer only at ramdisk_end-16 and subtracts
the checked payload size; vendor ramdisks are never searched. Header/table
reads support unaligned generic-ramdisk starts.

Both loaders validate all source/destination ranges and placement arithmetic
before writes. MARBLE requires the exact reviewed 4 GiB memory window.
The shared C locator and actual loader checks have ASan/UBSan host coverage.
Current builds: stage0 Image188416 (recorded hash unchanged), SWEET184320,
marble-xnu81920. Six tools tests and all shim Python/C tests pass.
0082 still applies cleanly to final 0081; MARBLE priority access is excluded,
and SWEET GIC preprocessing matches the prior baseline. See NOTES.md's active
handoff for exact hashes, commands and format-only artifact paths.

## Earlier host validation (before wrapper correction, 2026-10-21)

- BOARD=marble passes without warnings, Image 188416 bytes, SHA256
  `0e105d57f0781223b7c326b6aab702d9029d00788d27bb7784a543d2604aa1a6`:
  **identical to the physically successful recorded stage-0 Image**.
- SHIM_RAW_ONLY=1 BOARD=sweet passes without warnings, Image 180224 bytes.
- BOARD=marble-xnu passes without warnings, Image 77824 bytes, SHA256
  `201a41661691fc55af7d923f03d28a22ef76e33ffc72533f863dfd2b03802113`.
- Five unittest cases pass: ADT roundtrip/exact values/default preservation,
  replacement ramdisk, existing malformed-input and control/repack checks.
- All 81 historical patches applied to public xnu-8796.141.3 with pinned HFS
  source present. 0082 dry-run applies against that final baseline without
  rejected hunks. `git apply --check --whitespace=error` and repository
  `git diff --check` pass. Sources/check logs are under /tmp, not repository artifacts.
- Exact added bootstrap assembly fragment assembles to arm64 Mach-O with
  clang armv8.2-a+crypto and production numeric 16K descriptor constants.
- Actual final pe_fiq.c compiles for both boards to arm64 Mach-O with API
  declaration stubs (not a full XNU build); preprocessed checks prove no
  MARBLE priority access and unchanged SWEET GIC code.
- Existing SWEET Mach-O passes mkpayload with MARBLE ADT for **format only**:
  /tmp/marble-format-only.payload, 16604624 bytes. This is not a MARBLE kernel.
- Synthetic replacement test passes; additionally stock metadata + new shim
  + that SWEET payload pack/reparse independently passes at
  /tmp/marble-xnu-FORMAT-ONLY.img, 16687104 bytes, zero signature/trailer.
  Ramdisk SHA256 `5620aab559016fb6b3b1411c589c3f54aa93440ad57bedd474ae747c049116ff`
  for the first generated test ADT. Do not boot this format-only image.

Remaining: full macOS DEVELOPMENT compile/link (including staged provider
ABI checks), verify plain arm64/no PAC in artifact, create real MARBLE
payload and v4 image, review early high-PA mappings on hardware, and observe
XNU output/panic. Interrupt and persistent early-console mappings are
source/host validated only. Do not infer XNU execution from stage-0 success.
