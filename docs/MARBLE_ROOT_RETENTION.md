# Automatic MARBLE root retention

Future `tools/mkiosroot.sh --board marble ... OUT.img` builds automatically
invoke `tools/marble-root-finalize.py OUT.img`. Use a unique generation name:
`shim/out/marble-xnu/ios16-root-marble-20H392-GENERATION.img`.
The finalizer can also finalize a future separately edited root clone at that
same location. Kernel CI/packaging does not call it. The historical
`--no-journal` experiment skips automatic finalization/cleanup because it
cannot satisfy journal verification; sparse packaging there remains manual.

Before any deletion the finalizer completes, in order:

1. Read-only fsck (`FSCK_HFSPLUS`, default fsck.hfsplus).
2. Matching primary/alternate HFSX headers with journal bit set.
3. Read-only loop mount, `verify-iosroot.py`, and successful unmount.
4. Sparse creation using iosroot-sparse.sh.
5. Full simg2img expansion and byte-for-byte cmp against raw.
6. Independent SHA256 of raw and sparse, `.sha256` output, and atomic validation
   registry update (`.marble-root-validations.json`).

Any failure before these complete prevents cleanup. Existing sparse/hash output
is not overwritten. An interrupted generation can leave an incomplete output
for manual investigation; it never acquires a successful validation record.

Default retention is newest validated raw `.img` + its `.simg` + one immediately
previous available validated `.simg`. Successful validation order in the registry,
not filename ordering or timestamps, defines generations. Current hashes and
fallback sparse hash are rechecked before planning. Bootstrap exception: until
a recorded previous validated sparse fallback exists, retain all artifacts;
legacy sparse files are not guessed to be validated. With two recorded valid
generations, older matching legacy roots can also be pruned.

Set `MARBLE_KEEP_ROOTS=all` to keep all roots. Validation and hashes still run.

Deletion scope is exclusively canonical regular files matching
`ios16-root-marble-20H392-*.img` / `ios16-root-marble-20H392-*.simg` directly
inside the resolved repository's `shim/out/marble-xnu/`. The implementation
further restricts generation characters to ASCII letters/digits/dot/underscore/
hyphen. Symlink directory components or matching symlink/nonregular entries
abort cleanup. A lock serializes finalizers; device/inode/size/mtime are checked
again before deletion. The complete KEEP/DELETE plan prints first, then
`rm --` receives only exact individually checked paths. No recursion or shell
glob expansion is used for removal. Producers must not concurrently replace
artifacts outside this lock.

Never matched: latest-marble-xnu.img, boot_a.img, payloads, unrelated images,
subdirectories or anything outside that exact output directory. No cleanup
is run against existing artifacts by the diagnostic kernel task. Tests use
only disposable temporary fixtures:

```sh
python3 tools/test-marble-root-retention.py
```
