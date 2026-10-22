# Working on ios-sweet

- Read `NOTES.md` before starting; it contains the project goal, hardware facts,
  current blocker, local artifact locations and the next concrete action.
- The user switches agents frequently. Update the active handoff in `NOTES.md`
  after each milestone and before stopping. Record commits, CI run IDs, exact
  build/boot results and unfinished work. Distinguish observations from guesses.
- Commit completed changes. Use `gh` for GitHub Actions kernel builds and logs.
  Local single-file cross-compiles are useful before spending a CI run.
- Device bring-up uses temporary `fastboot boot` images. Preserve the Android
  installation and partition backups. The user approved (2026-10-15) using
  internal UFS for iOS and said Android may be deleted: the iOS root goes
  into the existing `userdata` partition (no GPT changes). Keep bootloaders,
  recovery, modem, persist and the backups intact, and confirm each
  destructive step with the user before running it.
- Keep device dumps, serial numbers and downloaded Apple artifacts out of git.

## MARBLE XNU automated CI/build workflow

For changes targeting `MACHINE_CONFIG=MARBLE`:

- After completing the requested MARBLE XNU change and all task-specific local
  validation, automatically continue through commit, push, GitHub Actions and
  local boot-image packaging unless the user explicitly says not to.
- Before committing:
  - read/update the active handoff in `NOTES.md`;
  - run all requested task-specific validation;
  - run `git diff --check`;
  - stage only files intentionally changed for the task;
  - run `git diff --cached --check`;
  - review `git diff --cached --stat`.
- Never stage generated kernels, payloads, boot images, stock boot images,
  IPSWs, ramdisks, device dumps, backups, serial numbers, downloaded Apple
  artifacts, secrets, or unrelated files.
- Use an appropriate descriptive commit message.
- Push completed MARBLE work to `origin marble`.
- Trigger `.github/workflows/xnu.yml` with:
    macos_version=13.5
    kernel_config=DEVELOPMENT
    machine_config=MARBLE
    keep_going=true
- Wait for the exact workflow run belonging to the pushed commit.
- If that run fails, inspect the logs and fix the failure. Never substitute an
  older successful artifact.
- After a successful run:
  1. Download that exact run's `xnu-kernel` artifact into a fresh directory.
  2. Locate `kernel.development.marble`.
  3. Regenerate the MARBLE ADT with `tools/mkadt.py --marble`.
  4. Generate `marble-xnu.payload` with:
       debug=0xc serial=3 cpus=1 keepsyms=1 -enable_kprintf_spam
  5. Build the shim with:
       BOARD=marble-xnu shim/build.sh
  6. Repack using:
       marble-boot-backup-clean/boot_a.img
  7. Run `tools/mkbootv4_marble.py inspect`.
  8. Verify and report SHA256 hashes.
  9. Produce the final verified image at:
       shim/out/marble-xnu/latest-marble-xnu.img
- Prefer using `tools/marble-ci-build.sh` for the commit/push/CI/download/package
  sequence once that helper exists.

### Device safety boundary

Automation MUST stop before interacting with the physical phone.

Never automatically execute:
- `fastboot boot`
- `fastboot flash`
- `fastboot erase`
- `fastboot format`
- `adb reboot`
- `adb shell reboot`
- `dd` to a physical block device
- any command that writes to, reboots, boots, flashes or erases the phone

Even though temporary `fastboot boot` is the normal MARBLE testing method, the
user must execute that command manually.

After a successful automated build, finish with:
- commit SHA
- GitHub Actions run ID
- kernel/payload/boot-image SHA256
- final image path
- exact manual command:

    fastboot boot ~/ios-marble/shim/out/marble-xnu/latest-marble-xnu.img

Do not run that command yourself.
