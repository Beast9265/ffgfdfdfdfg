# MARBLE GUI startup experiment

The graphics-enabled kernel executes SpringBoard repeatedly on the POCO F5,
but stable SpringBoard and a visible GUI have not been observed. The old
GUI-debug root redirects backboardd and SpringBoard stdout/stderr to
`/dev/console`. SWEET testing proved those properties could make backboardd's
`posix_spawn` fail with EACCES. This experiment restores normal descriptors
before diagnosing any display failure.

`ios16-root-marble-20H392-gui-clean.{img,simg}` derives from the verified
journaled GUI-debug root. Only its mounted launchd cache was changed:
bluetoothd stays removed, the existing panic suppression stays, and the two
GUI jobs' output/environment fields match the original Apple cache.
SpringBoard retains its original `CA_ASSERT_MAIN_THREAD_TRANSACTIONS=1`.
The cleanup helper rejects unrelated semantic changes. See NOTES.md for
validation, provenance and exact artifact hashes.

The kernel adds only `marbleguidiag=1` to the existing boot arguments. Without
it, the new MARBLE diagnostics are off. They select only backboardd and
SpringBoard; SWEET's existing behavior and boot arguments are preserved.

| Output | Limit per boot | Meaning |
| --- | --- | --- |
| `CRASH name[pid] sig ...` | 32 crash reports total | Signal, exception/code and subcode at the existing crash-exit hook |
| `CRASH name reason ns N code X: text` | Same reports, 512 text characters | Exit reason if available; `(none)` can be legitimate |
| `\|name\| text` | 256 chunks of at most 256 bytes | Selected `/dev/null` writes, including possible libc++ exception text |
| `IOK name: ...` | 400 lines total | Registry paths/children, matching, notifications and service open results |

These limits are cumulative, so record early boot output. The kernel tee
requires no launchd file-descriptor changes. The full SWEET stack sampler,
heap scanner and persistent UFS logger are not imported by this experiment.

The retained graphics drivers already log after calling `registerService()`:

```text
MARBLE SURF: IOCoreSurfaceRoot registered
MARBLE FB: AppleCLCD ...
```

Physical observations should distinguish:

- Neither registration line: examine early registration/setup output. Linked
  classes and matching personalities alone do not prove successful startup.
- Registration lines appear, but no GUI client reaches display services:
  use crash reasons and preceding IOKit lookups to find the earlier failure.
- GUI clients match/open IOMobileFramebuffer, AppleCLCD or IOCoreSurfaceRoot:
  correlate open results and existing FB/SURF selector logs with the crash.
  An ABI mismatch requires evidence from those calls; it is not assumed.

A signal crash without reason text may still need a later focused diagnostic.
No GPU, touch, battery, audio, modem, Bluetooth or sensor support changes are
part of this experiment. The user performs all phone operations manually.
