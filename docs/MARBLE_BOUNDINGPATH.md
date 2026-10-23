# MARBLE SpringBoard bounding-path investigation — 2026-10-23

Physical observation: SpringBoard repeatedly aborts with
`NSInternalInconsistencyException`, reason:
`Failed to load bounding path bitmap data from the asset manager for asset name: BoundingPathBitmap-1125x2436-375x812-3.00x`.
The assertion is `_UIScreenComplexBoundingPathUtilities.m:326`.
Setup has not been reached. Physical validation now PASS: user reports animated iOS 16.7.16 Setup Hello
(ciao / Scorri verso l'alto), status bar, home indicator and info button.
Bounding-path lookup and GUI path are proven; physical input is the next blocker.

## Exact 20H392 code path

Addresses below are unslid arm64 dyld-cache addresses, inspected with `ipsw`
v3.1.739 against the cache in the physically tested setup-fast image.

1. `-[_UIScreenComplexBoundingPathUtilities _loadBitmapForScreen:type:]`
   (`0x1890897c4`) gets native bounds, reference bounds and scale for the
   supplied screen type through `__UIScreenNativeDisplayBoundsSizeForType`,
   `__UIScreenReferenceBoundsSizeForType`, `__UIScreenScaleForType`.
   It formats `BoundingPathBitmap-%ldx%ld-%ldx%ld-%.2fx`. Types 17–22 and 36
   append `-A`; the observed name has no suffix. These geometry inputs already
   produce the intended 1125x2436, 375x812, 3x name. Display class/idiom is not
   another field in this name.
2. `___UIKitSharedBoundingPathDataManager` (`0x1891f4644`), once-body
   `0x18908d570`, constructs `_UIAssetManager` with name
   `UIKit_BoundingPathData`, bundle from
   `__UIKitResourceBundlePath("BoundingPathData.bundle")`, and UIDevice idiom.
   The resource helper (`0x1891eccfc`) appends to UIKit's bundle path.
3. `_UIAssetManager` initialization (`0x188f42254`) constructs a `CUICatalog`
   using `initWithName:@"Assets" fromBundle:error:` at `0x188f423a4`.
   Thus the actual catalog is **not UIKitCore.framework/Assets.car**:
   `/System/Library/PrivateFrameworks/UIKitCore.framework/BoundingPathData.bundle/Assets.car`.
   `allowMissingCatalog` is false. A failed catalog initialization gives a nil
   manager, checked at a different assertion (line 324).
4. `_UIAssetManager dataNamed:` (`0x189089bf0`) calls its catalog's
   `dataWithName:`. It does **not** forward its manager idiom to that call.
   CoreUI `dataWithName:appearanceName:` (`0x19ee98458`) instead uses its own
   MobileGestalt device traits. `_dataWithName:…` (`0x19ee985f4`) tries scale
   1 then scale 0; the device idiom stays the same in both attempts.
5. The UIKit caller sends `data` to the returned CUI data asset. Nil NSData
   branches at `0x189089908` to assertion line 326 (`0x189089ae0`).
   Only afterward does `NSKeyedUnarchiver` decode `_UIBoundingPathBitmap`
   (`0x189089934`); archive failure is line 330 and size mismatch line 354.
   The observed failure therefore precedes bitmap unarchiving.

## Catalog/source proof

| Copy | Size | SHA256 |
|---|---:|---|
| setup-fast root | 101768 | `0a53453f1e096f70ccb38618b0b8c32fa950f71dc3b559c4ce556825517aa04d` |
| OS 087-86698-044.dmg, same absolute path | 101768 | `0a53453f1e096f70ccb38618b0b8c32fa950f71dc3b559c4ce556825517aa04d` |
| SystemOS 087-86593-047.dmg | absent | — |
| AppOS 087-86715-047.dmg | absent | — |
| surviving working SWEET image | unavailable | no direct comparison possible |

The root copy and OS source were compared byte-for-byte. Root catalog inode
289212, link count 1, root:wheel (0:0), mode 0644; every ancestor inspected is
root:wheel 0755. File xattr: `osx.com.apple.FinderInf`. HFS directory xattr
listing returns ENOTSUP on this host, so this is not a complete ACL audit.
The companion [catalog inventory](MARBLE_BOUNDINGPATH_CATALOGS.json) records
all relevant discovered catalogs, source copies, hashes and inode/link metadata.

All 44 root-visible dyld cache files were byte-compared with the SystemOS
source; all match. Their root-visible paths are hard links to the in-root
cryptex copies. Source SystemVersion reports 16.7.16 / 20H392. Resource bundle
DTSDKBuild 20H343 / DTPlatformVersion 16.7.3 is also present in the original
20H392 OS resource, rather than evidence of an accidentally mixed root.
`mkiosroot.sh` links cryptex counterparts only when root paths do not exist,
but there is no overlapping BoundingPathData bundle in either cryptex. No
code/catalog overlay skew was found; root-builder overlay behavior is unchanged.

### Structured rendition inspection

The official ipsw release tarball SHA256 is
`8124bdba7902e7627bae1bb2e1117c9cfcdc31de0f65ec55e341565ac6029a01`
(verified against the release checksums). Its strict BOM validator initially
rejects 49 unused `(0xffffffff,0xffffffff)` pointer-table entries. In a
**temporary parser copy only**, those entries were normalized to zero; live
catalog/source bytes were never changed. Used rendition blocks remain intact.
The inspection commands were:

```sh
ipsw car /tmp/boundingpath-catalog-parser-copy.car --metadata-only --json \
  --name 'BoundingPathBitmap-1125x2436-375x812-3.00x'
ipsw car /tmp/boundingpath-catalog-parser-copy.car \
  --name 'BoundingPathBitmap-1125x2436-375x812-3.00x' \
  --output /tmp/boundingpath-car-decoded \
  --manifest /tmp/boundingpath-car-decoded-manifest.json
```

Result: 23 total renditions; one selected/exported; zero decode, resolve or
export failures. The exact logical name resolves to DATA key
`[scale=1, idiom=1, identifier=19814, element=85, part=181]`; there is no
universal-idiom variant of this name. DATA scale 1 is independent of the 3x
geometry embedded in its name. Exported DATA is a 3090-byte binary plist,
SHA256 `799026f7d7fe3cd6728dfb9987ddbe3c53aa7eb8516cee8002c77e8a34e56bda`.
Python plistlib parses its NSKeyedArchiver `_UIBoundingPathBitmap`: width1125,
height2436, nodeCount1340, rows2680 bytes, skip-region y134/height2168,
maxNodesPerRow5. Apple NSKeyedUnarchiver was not run on this Linux host;
structured extraction/archive parsing passes, and the physical failure is
before the unarchiver. The asset is present, rather than missing or corrupt.

## Source-backed mismatch and one primary fix

CoreUI's `_____getDeviceTraits_block_invoke` (`0x19eea1064`) initializes idiom
to 0, asks MobileGestalt key `oPeik/9e8lQWMszEjbPzng` (ArtworkTraits), then
maps `ArtworkDeviceIdiom` through its theme-idiom table. Missing input leaves
idiom 0. MobileGestalt's native iOS ArtworkTraits provider (`0x19c57013c`,
`IODeviceTree:/product` reads beginning `0x19c5703b8`) gets
`artwork-device-idiom`, subtype, scale, memory class, graphics feature set and
fallbacks from that device-tree node. The idiom dictionary entry is only
inserted when its property exists (`0x19c5704bc`).

The physically tested MARBLE ADT contains **no `/product` node**. This supplies
no phone artwork idiom to CoreUI, whereas the requested DATA rendition requires
phone (1). This is the source-backed trait mismatch selected for correction;
the next physical test must confirm the resulting runtime behavior.

Restore only the original D22AP `/product` metadata using
`tools/marble-product-adt.py`; require those inputs for future MARBLE generation
in `mkadt.py`. The helper appends 61 original non-placeholder properties with a
unique phandle. It preserves every existing node/property, seed, CPU topology,
identity, geometry and boot metadata. Removing the added node serializes to
**exactly** the tested old ADT. No Apple executable or catalog is patched.

The recovered original DeviceTree is from the pinned Apple 20H392 IPSW's
`Firmware/all_flash/DeviceTree.d22ap.im4p`, checked against both D22AP
BuildManifest identities (SHA1 digests). Original IM4P SHA256:
`480e8b0888949b4128b7aa2cd254497581c69e1bafa596a760b2fa955a8a6368`;
decoded ADT SHA256:
`9e670987c80493bd69aba7be62e3179c04663324d9249b0973675baac175dbf1`.
Apple bytes remain ignored under `research/ipsw-x/d22ap.adt`. Properties include
idiom `phone`, subtype2436, artwork scale3, gamutP3, memory class4 and original
feature/fallback strings. Metadata restoration does not enable a GPU.

SWEET comparison is reconstructed: its generator imports this same original
D22AP `/product`; historical NOTES records Hello (0057/v12) and later home
(0069/v14). The 0061 iPhone X geometry patch is after initial Hello and before
home. No surviving v12/v14 root or original catalog hash is available locally,
so neither a direct SWEET catalog comparison nor exact historical runtime
traits can be claimed. Current SWEET generator output with the same source
and seed is byte-identical before/after this change; no SWEET kernel changed.

## Identity, cache and access limits

Preserved ADT identity is D22AP / iPhone10,3, display-scale3, home-button-type2,
internal/main display, logical1125x2436 over physical1080x2400/stride4320 at
PA0xb8000000. The physical requested name proves reference375x812/scale3.
No live rotation/idiom dump was available. Source audit also finds unrelated
MARBLE sysctl identity defects: getTargetName=marble,
getProductName=POCO F5 / Redmi Note 12 Turbo; the iOS-on-macOS
HW_MACHINE path still returns iPad8,6. These are not corrected speculatively
alongside this fix. MobileGestalt ProductType/HWModelStr runtime answers were
not captured; ADT compatible/model retain iPhone10,3/D22AP.

The local setup-fast image has no MobileGestalt cache plist at the requested
systemgroup path. The phone's possibly persisted cache was not read. No cache
was deleted or regenerated. No exact file-open/sandbox denial was observed;
line326 rather than manager-init line324 and the source trait mismatch point
to rendition matching. No sandbox policy was weakened.

## Packaging, validation and retention

Reused exact diagnostic kernel from CI39888158542 (kernel source b16c741),
SHA256 `462dc21b476550949aaebdd335c5e6584f120c3481bfbda2cae92958398160d9`.
No new XNU build or workflow. Same shim SHA256
`586713d3b4c5862f73443cb1e5f555e465a9ffa5f3e2662672d41fff1715ee05`.
New ADT SHA256 `35f0bff762c339e86a0e67392267ed148ae06b24703b682ce2327c9296ed84e3`.
Payload SHA256 `823706ba303643c4880d235abac8aaa2145983c23258c2af119f0019f3f0906c`.
Boot SHA256 `789377d9cc9de5027038b074e3c0c61121f2229594e7895282933a44b1eb6242`.

Validation: ten unit tests; seven retention fixtures; repository validation;
exact kernel segment comparison, arm64/full link/no undefined symbols,
boot-v4 header/stock metadata/footer/bounds/padding, bootstrap mapping and
capacity checks. Original nodes and same-source SWEET output byte-identical.
`cpus=1 marbleguidiag=1` and the complete prior command line are unchanged.
No IOSurface, panel, framebuffer, UFS, sandbox or daemon changes.

No new root generation. Rehashed setup-fast raw SHA256
`7ca8c990f98875d892ffa38f769f4a8bb5af23bdbabb4ee50d69d2df13822798`
and sparse SHA256
`cec3daf08e3236065d14c3939c48051430c7737f798c2b7d8affb475c3f4aa01`
match the prior recorded values. No root
cleanup was run. Existing automatic finalization/cleanup is retained, its
plan labels clarified, and tested only in temporary fixtures. See
[retention policy](MARBLE_ROOT_RETENTION.md): fsck/journal/root/sparse/full
expansion comparison/hashes must pass; keep newest validated raw+sparse and
previous validated sparse; canonical exact directory/name scope, no symlinks,
complete plan before exact `rm --`, and `MARBLE_KEEP_ROOTS=all` escape hatch.
Until a previous validated fallback is recorded, retain existing artifacts.

Only manual phone command for this test (no userdata reflash):

```sh
fastboot boot ~/ios-marble/shim/out/marble-xnu/latest-marble-xnu.img
```

Physical user test subsequently demonstrated Setup Hello. Preserve the named
`hello-known-good-marble-xnu.img` checkpoint; input work is tracked separately.
