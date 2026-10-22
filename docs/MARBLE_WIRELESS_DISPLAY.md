# MARBLE Wireless display diagnosis (20H392, 2026-10-23)

## Physical observation

SpringBoard throws NSInternalInconsistencyException: `We expect a valid bounds
for configuration:`. The dumped FBSDisplayConfiguration is Main-External,
CADisplay Wireless, device wireless0, currentMode 0x0 @ 0Hz, pixelSize/bounds
zero, preferredScale 1. This is a real FBS configuration failure. It does not
prove that AppleCLCD reports those values.

Containers hierarchy PASS; pre-display container wall PASSED; SpringBoard FBS
path PASS; FBSDisplayConfiguration constructed PASS; Wireless config INVALID;
SpringBoard stable FAIL; visible GUI FAIL. HFS swap compatibility is installed
and validated; this physical report does not independently prove a particular
VNOP_EXCHANGE invocation.

## Proven origin (local Apple 20H392 cache disassembly)

Addresses below are unslid arm64 cache addresses. Analysis used the cache and
SpringBoard extracted from the existing containers root, not a different OS.
Temporary evidence is /tmp/marble-display-re/{IOMFB,QuartzCore,FBS,FigInstall,
FigInstallBlock}.dis. No Apple binary or extracted cache is committed.

* IOMobileFramebuffer `_iomfb_populate_display_infos` (0x1af224108) invokes
  `_open_media_toolbox` (0x1af224be4), which dlopens MediaToolbox and resolves
  FigInstallVirtualDisplay. Its once block (0x1954fed2c) gets virtual framebuffer
  contexts and calls IOMobileFramebufferInstallVirtualDisplays (0x1954fedd0).
  StartWirelessDisplayServer in SubServerConfiguration.plist defaults true.
* The populate loop creates `wireless%d` (0x1af224260..2a4), sets its IOService
  handle to zero (0x1af22428c), and assigns display type 2 (0x1af2242c0).
  This is a userspace virtual entry, not an AppleCLCD service renamed Wireless.
* Native `_iomfb_match_callback` (0x1af22b9b8) reads only local Boolean service
  properties dfr, AppleTV, external. dfr -> type3; AppleTV/external -> type1;
  otherwise type0/primary. None of these branches produces type2.
* QuartzCore display_count_of_type (0x1883aec84) counts the IOMFB list types.
  AppleWirelessDisplay::count uses type2 (0x1883af138). Its open is
  0x1883aeff0; new_server passes literal Wireless to EAGLServer at
  0x1883ac7a4..814. IOMFB OpenByName routes type2 through virtual contexts;
  other types use the native service path (0x1af229fd4..0x1af22a314).
* CAWindowServer _detectDisplays (0x1884e3150) visits CLCD, RGBOut, Wireless
  in order. The first added server gets the main flag (0x1884e31dc..1ec).
  Display construction assigns the incrementing display id (0x18841c728);
  its generator at0x1dcdf81a8 is initially zero in this cache.
  FBS immutable-display initialization tests displayId==1 (0x19b921bf0),
  independently copies isExternal (0x19b921ca0), and its identity description
  adds -External (0x19b924898). CA isExternal treats type1..3 as external
  (0x18836d4cc). FBS reads current/preferred/available modes from CADisplay
  (0x19b921d4c..d6c); it does not originate the Wireless name.

Thus Wireless is a real virtual-display path, installed through MediaToolbox,
not a SpringBoard-created placeholder or misclassified AppleCLCD. With native
primary absent, the virtual display can occupy the first/main position. The
physical Main-External failure is consistent with that exact path. Runtime
ordering and native values must still be confirmed on the next physical boot.

## Missing native provider: source and linked evidence

The old linked MARBLE processTopLevel (0xfffffe0007a71868 in run39790623310)
only publishes CPU children and direct root children. IODTFindMatchingEntries
without kIODTRecursive does not descend into arm-io. There is no AppleARMIO to
publish disp0. AppleCLCD's personality requires an IOPlatformDevice named
sweet,display: a linked class plus an ADT node cannot satisfy that match alone.

Working SWEET's 0046 platform expert explicitly publishes arm-io children,
excluding gic. That publication is missing from MARBLE's platform expert.
This directly explains a missing native display without changing mode bytes,
AirPlay, root jobs or display-scale. No evidence justifies importing unrelated
SWEET root changes or suppressing the virtual display.

The minimal functional fix publishes only arm-io/disp0 using createNub,
attach(this), registerService, release. It follows the SWEET provider model;
IOPlatformDevice::compareName consults its direct platform-expert provider.
No other arm-io child or framebuffer implementation is changed.

AppleCLCD::start explicitly sets external=false. It never sets AppleTV or dfr.
The personality does not override them (IOClass AppleCLCD, IOProviderClass
IOPlatformDevice, IONameMatch sweet,display). Native classification is type0.
Bounded diagnostic output reports the actual registered service properties,
class, provider, canvas and computed 20H392 classification at runtime.

## Mode/selector audit and scope

The existing implementation returns selector8=1125x2436 (unless sweetfb_native),
18=1, 28=458. These are source values, NOT measurements from the latest phone
log. The next kernel logs the actual copied output for backboardd, SpringBoard
and MobileGestaltHelper. The ADT retains chosen/display-scale=3 and disp0 canvas
1125x2436. Physical framebuffer remains 0xb8000000,1080x2400,stride4320.

QuartzCore IOMFBDisplay::set_physical_and_canvas_sizes (0x188534318) calls
GetDisplaySize (0x188534358), GetCanvasSizes (0x188534400), GetDotPitch
(0x188534458) and GetDisplayArea (0x188534468). DisplayArea supplies physical
area, not FBS logical bounds. GetBlock79 reads capability blocks 0x4d/0x4a/0x48
(0x1883ad2f4,0x1883ad4d0,0x1883ad4fc), with count checks before array use.
SupportedFrameInfo74 participates in capabilities (0x1883da374). Other listed
selectors concern color remap57, debug15, display device22, display area29,
power saving33, power12, swap wait6, gamma27/17, contrast84, brightness50.
No evidence connects their zeroed native responses to the failing type2 virtual
mode. A complete native timing ABI has not been established by this audit and
is deliberately unchanged. The physical zero virtual mode is observed; its
inactive callback state is not a measurement of AppleCLCD's mode.

Diagnostics are MARBLE-only and gated by marbleguidiag=1: 32 registered/open
service notes, 96 selector value notes restricted to the three processes and
selectors8/18/28, and one provider-publication note. Existing bounded IOKit and
crash diagnostics remain. All graphics operations, selector return values,
surface/swap/copy/vsync/geometry/scale remain unchanged.

The virtual GetDisplaySize implementation (0x1af22bddc) independently defaults
to1080x1920 (constant pair at0x1af22d830). Its dimension state and digital
mode state are distinct; the physical zero FBS mode is not evidence of a zero
AppleCLCD selector8. The old NOTES statement that the main display must come
from a kernel service was too broad: type2 is installed in userspace.

## Validation

Complete0001..0082 patch replay and strict0082 application PASS. Both changed
C++ units compile with matching CI headers/arm64 flags. Normalized preprocessing
is unchanged for SWEET, BCM2837 and T8103. Source audit confirms the other0082
sections are unchanged. Source commit `0eb04bb90ed1fa36be6270aee38209ae4b362dd0`, exact Actions
`39796176138` SUCCESS. Both changed units compile remotely; full link has zero
undefined symbols. Fresh artifact SHA256SUMS verified. Linked PE has the disp0
lookup/create/attach/register path; linked AppleCLCD still sets external=false,
and personality has no classification overrides. Linked bounded diagnostic
and unchanged timer audits PASS. Independent packaging audit verifies all kernel
segments, ADT scale3/canvas1125x2436/physical1080x2400,stride4320 and existing
boot args. Kernel/payload/boot hashes and manual command are in NOTES.md.
Framebuffer minus diagnostic additions and all unrelated0082 sections are
byte-identical to the preceding source. No root changes or phone commands.

Next physical test must establish actual selector outputs and native display
ordering. Expected service note: name/class AppleCLCD, external=false,
AppleTV/dfr absent, iomfb-type0, provider disp0, canvas1125x2436; selector8
1125,2436, selector18 1, selector28 458. These remain predictions until the
user's manual boot. Visible GUI and stable SpringBoard are not claimed.
