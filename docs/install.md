# Agent-assisted installation

**English** | [简体中文](install.zh-CN.md)

This is a supervised procedure, not an unattended installer. The byte-writing ELF and underlying service/Backup operations have hardware validation records. `wifi.py` contains only Wi-Fi-specific operations; it imports the existing zv-e10-toolkit server, client, transport helpers and generic Backup property actions. Linux read-only `inspect`, `boot-check` and teardown have physical-camera validation; integrated write operations have offline checks only. Read [AGENTS.md](../AGENTS.md) and [recovery](recovery.md) first.

## 1. Prepare without connecting

Use a Python 3 virtual environment and libusb. On macOS, install libusb through your normal package manager; `LIBUSB_PATH` can select the library. The common helper also checks Apple Silicon and Intel Homebrew locations. Linux x86_64 has physical-camera validation for the read-only session path using polkit and libusb; the Linux write path remains untested. Windows launchers are not supplied.

This project uses [zv-e10-toolkit `e8d4cb5`](https://github.com/dino2048/zv-e10-toolkit/commit/e8d4cb566fa04dac249e10431302e4d950550bde), which provides the generic Backup-property actions and the existing persistent-session extension interface. Clone the toolkit and check out the pinned commit:

```sh
mkdir -p vendor
git clone https://github.com/dino2048/zv-e10-toolkit.git vendor/zv-e10-toolkit
export ZVE10_TOOLKIT="$PWD/vendor/zv-e10-toolkit"
git -C "$ZVE10_TOOLKIT" checkout --detach e8d4cb566fa04dac249e10431302e4d950550bde
PYTHON=python3 sh "$ZVE10_TOOLKIT/linux/scripts/setup.sh"
export WIFI_PYTHON="$ZVE10_TOOLKIT/linux/.venv/bin/python"
"$WIFI_PYTHON" -B tools/wifi.py --help
```

If you already have the updated toolkit, set `ZVE10_TOOLKIT` to that checkout and `WIFI_PYTHON` to its interpreter; do not copy its code or create another environment unnecessarily. Use the owner's chosen interpreter when specified. Toolkit setup installs dependencies and its pinned Sony-PMCA-RE checkout. This repository does not carry duplicate common helpers, dependency lists, service servers or clients. It does not patch an external checkout automatically.

The two tiny ARM Linux helpers are supplied with assembly source. `patch.arm` is the exact camera-tested executable (MD5 `8a1bd57091f544a758300b7151d94f05`). `restore.arm` is built from the same source with expected/replacement bytes reversed; it has offline validation only. To rebuild, use clang with an ARM target and GNU `arm-none-eabi-ld`:

```sh
sh tools/build-helpers.sh
```

No ARM libc is required. A different source filename/toolchain may change ELF symbols or metadata; validate load segments and instruction/data content, not just executable size. See [release checks](release.md).

## 2. Confirm the camera and backup

Confirm **ZV-E10 first generation, displayed firmware 2.02**, stable power, normal boot and no unresolved prior modifications. Strongly recommend a verified full eMMC user-area backup via [zv-e10-toolkit](https://github.com/dino2048/zv-e10-toolkit), over ordinary USB-C. Keep the backup privately; it may contain device secrets. Know where a hardware-assisted fastboot recovery would come from before writing. Backup is not a guarantee of recovery.

Set USB Connection to **Mass Storage**, not Auto/MTP, and use a data-capable USB-C cable. Do not ask the owner to navigate menus while stuck in USB storage: start the persistent service session first.

The owner must explicitly confirm the country of use and the proposed changes. Only China B=2/C=22 is validated for ordinary installation. Stop for unknown firmware, region, or library content. Do not automatically upgrade/downgrade firmware.

## 3. Keep one service session open

From the repository root, in a separate terminal:

```sh
sudo ZVE10_TOOLKIT="$ZVE10_TOOLKIT" "$WIFI_PYTHON" -B tools/wifi.py serve --session-dir private/install-01 --owner-authorized-write
```

Use a new directory for every session; resolve any prior session before starting another. `sudo` is needed for raw USB access on the demonstrated macOS path; use the host's normal privileged terminal mechanism, never ask an agent to collect a password. The toolkit session stays open until `close` or ten minutes of inactivity. The existing toolkit server hands its queue/results back to the client UID; `--client-uid` can specify the owner when needed. Wi-Fi snapshots use the toolkit checkout owner. Only run trusted code as root. For inspection only, omit `--owner-authorized-write`.

Read `private/install-01/state.json` and wait for `state: ready`. Keep `ZVE10_TOOLKIT` and `WIFI_PYTHON` set in both terminals (including the privileged process). In the agent's other terminal:

```sh
"$WIFI_PYTHON" -B tools/wifi.py request --session private/install-01 '{"action":"inspect"}'
```

This exports the full current library and both Backup files to unique names inside the private session directory, reports the three one-byte values and mounts. Record the snapshot token. FileControl reads and the terminal share this same authenticated service connection. Authentication itself may update Sony service bookkeeping; read-only inspection is not a promise of zero internal bookkeeping.

Require factory library size 17,694,160 and SHA-256:

```text
5ad8746a229da259fe00b297e8f897d682f7ae9a13393025b3d1c95a808e68d7
```

Preserve the returned original property values in a private installation note, alongside the model, displayed firmware, confirmed region, backup location, and file hashes. If the library is already patched, inspect all state and decide whether installation is already complete; do not rerun `patch`.

## 4. Perform the confirmed minimal changes

The Wi-Fi action guards `/usr` mount identity and full library hash, uploads the hash-pinned helper in one Jiritsu SET_FILE2 write under `/tmp/jiritsu`, reads the whole file through toolkit Jiritsu GET_FILE and compares every byte on the host, remounts `/usr` writable, runs the non-truncating writer, exports the result, validates the complete expected hash and unique difference, then remounts read-only and removes the helper.

```sh
"$WIFI_PYTHON" -B tools/wifi.py request --session private/install-01 '{"action":"patch"}'
```

Require `only_difference: 0xd778e4` and patched SHA-256:

```text
14f42cc09ee1b9ddde5352482c13b68e5a5e97d9d79e8456087b5e0b7af6ff6a
```

Then write the Backup properties individually. **These examples assume the inspected originals were `00/09/09`; replace `expected` with your own saved originals.** All value strings are hexadecimal. Never copy these defaults without inspection.

```sh
"$WIFI_PYTHON" -B tools/wifi.py request --session private/install-01 '{"action":"backup-write","id":"0x01071C54","expected":"00","value":"01"}'
"$WIFI_PYTHON" -B tools/wifi.py request --session private/install-01 '{"action":"backup-write","id":"0x00A5000B","expected":"09","value":"02"}'
"$WIFI_PYTHON" -B tools/wifi.py request --session private/install-01 '{"action":"backup-write","id":"0x00A5000C","expected":"09","value":"16"}'
```

Review `match: true` after each command. The Wi-Fi action validates the three permitted keys and values, then delegates to toolkit's generic Backup action, which saves the original before writing, invokes Sony's save call, and immediately rereads it. Already-correct properties can be skipped. It does not edit the BK4 files directly. Partial completion is possible: retain each result and restore only what changed if needed.

An error in a structured Wi-Fi/Backup action stops the existing server. Do not blindly resend, reboot, or continue. Check preserved snapshots, state, and the recovery guide. A failed response after writing may still mean the camera changed. A remount failure requires resolving the current mount state before cold boot.

## 5. Verify and close

Run `inspect` again. Require the patched full hash, properties `01/02/16`, and `/usr` mounted read-only. Preserve before/after files privately. Then:

```sh
"$WIFI_PYTHON" -B tools/wifi.py request --session private/install-01 '{"action":"close"}'
```

Wait for server exit and require `state: closed`, `terminal_closed: true`, `service_returned: true` in state.json. The close response alone precedes terminal teardown and is not sufficient.

Switch OFF, wait for the access lamp to go out, unplug USB and remove the battery for about 30 seconds. Refit it and start a new **read-only** session in `private/verify-01`, wait for `ready`, then inspect. Ask the owner to check Network → Wi-Fi Settings → Frequency Band and select 2.4/5 GHz while the session remains ready/open.

**Warm boot check:** Battery removal for about 30 seconds may still resume a saved Warm Boot Image with an old four-item Wi-Fi page. In the verification session, inspect the boot log and confirm that the running Page1 has five TypeNB items. If it is still TypeRK/four items or the band menu is missing, stop acceptance and preserve the logs and snapshot. Do not repeat the same byte patch or Backup writes. On the tested camera, a separately backed-up, verified Sony updater operation invalidated only the first 512 bytes of the 60 MiB `nflasha5` warm image; the next boot had no warm-resume log and restored the five-item native page. Use the separate guarded `wbi-prepare` / `wbi-drop` actions in [WBI recovery](wbi.md), with full double backup, explicit eMMC-write consent and readback. Sony's binary must be extracted privately from the owner's official update package; it is not distributed here.

Run the read-only check in the new ready session:

```sh
"$WIFI_PYTHON" -B tools/wifi.py request --session private/verify-01 '{"action":"boot-check"}'
```

Require `page1.type: TypeNB`, `page1.count: 5`, no warm-resume markers, and the owner's confirmation that the native band page opens. `boot-check` reads the global Page1 object; the camera menu remains the final UI check. If the result is TypeRK/four items while the patch and properties match, follow [WBI recovery](wbi.md) under Agent supervision. WBI invalidation is a separate confirmed eMMC operation; it is never automatically chained to the patch.

Use [verification steps](recovery.md) for optional functional checks and read-only active radio sampling. Close the verification session normally. Then create a privacy-safe summary without copying raw mounts, property IDs or values, process IDs, addresses, logs or snapshot tokens:

```sh
"$WIFI_PYTHON" -B tools/session_summary.py private/verify-01
```

The command exits nonzero unless the closed session was read-only, used a known library, retained `/usr` read-only, returned a known Page1 layout, had no refused requests and completed normal teardown. Keep the original session and all private backups outside any public archive even when sharing the summary.
