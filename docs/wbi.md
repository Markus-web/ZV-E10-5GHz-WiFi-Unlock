# Warm Boot Image recovery

**English** | [简体中文](wbi.zh-CN.md)

Use only on first-generation **ZV-E10 system 2.02**, after the one-byte patch and Backup `01/02/16` are verified, when Page1 is still TypeRK/four items and the native band menu is absent. Do not repeat the patch/property writes. An old WBI can restore the old page; battery removal for 30 seconds does not guarantee a true cold boot.

The 2026-11-07 **2.02** records show two matching full backups, Sony's utility returning `[UD_WBI_DROP] /dev/nflasha5 wbi_drop`, then a complete readback with only the first 512 bytes zeroed. After power removal, global and current Page1 became TypeNB/five items, and the owner confirmed the band menu and 5 GHz phone/router use. The new host integration has **offline tests only**. System 2.03 is refused.

## 1. Obtain the original Sony tool offline

The tested 6,200-byte `ud_wbi_drop.elf` came from the **Sony ZV-E10 2.03 official update package**, but was executed on **camera system 2.02**. Package version and installed system version are different facts. Do not upgrade the camera. Sony's ELF and complete firmware are proprietary and are not bundled here.

Obtain the official ZV-E10 2.03 updater yourself from Sony support, retain its source URL/package hash privately, and unpack it **offline without running the updater**. Use [fwtool.py](https://github.com/ma1co/fwtool.py), the same extractor recorded in the local research (commit `cdba742b73eed5981480c326aeb30033aabf0223`); follow its requirements in a virtual environment. For a Windows updater EXE or its extracted FirmwareData DAT:

```sh
git clone https://github.com/ma1co/fwtool.py.git vendor/fwtool
git -C vendor/fwtool checkout --detach cdba742b73eed5981480c326aeb30033aabf0223
"$WIFI_PYTHON" -B vendor/fwtool/fwtool.py unpack -f /path/to/official-ZV-E10-2.03-updater.exe -o private/sony-unpacked
"$WIFI_PYTHON" -B tools/prepare_sony_wbi.py --from-tree private/sony-unpacked --out private/sony-wbi/ud_wbi_drop.elf
```

The offline selector requires SHA-256 `f2a5b27a0c11d55a612d61e61e82c55278efb744052ecb8ec2cbbd8851d0ea6e` and length 6200. It never executes extracted code. If extraction fails or no exact file matches, stop; do not substitute a similar ELF. The source containers were removed from the local research before this release, so extraction has not been rerun for this integration. The utility is checked again before every proposed use.

The host generates the exact five-entry partition configuration used in the successful run, SHA-256 `9bb1cba13c10ce88bd88d054dc49a823b3b1409ce6dfbeaeaa180f31d22744a8`. Its only WBI entry is start `0x05800000`, length `0x03C00000`, type 2. No arbitrary partition/path override is accepted.

## 2. Prepare and review two full backups

Follow [installation](install.md) to establish one persistent session in `private/wbi-01`, with `--owner-authorized-write` if later proceeding. Wait for `ready`. Confirm the physical model, displayed system **2.02**, stable power and the actual missing menu. Run `inspect` and `boot-check` first. Ensure at least 400 MiB free host space; preserve this camera's full eMMC backup and verify the toolkit fastboot recovery route and required hardware are available before authorizing WBI writing.

```sh
"$WIFI_PYTHON" -B tools/wifi.py request --session private/wbi-01 '{"action":"wbi-prepare","model":"ZV-E10","displayed_firmware":"2.02","sony_tool":"private/sony-wbi/ud_wbi_drop.elf"}'
```

`wbi-prepare` performs no camera write. It automatically checks two exact `/version.txt` reads (`30110_05.2025031501`), the ZV-E10 2.02 `libObj.so` fingerprint, the patched complete `CautionConfig.so` hash, and all three properties. Model identification uses these known system fingerprints plus the owner's model confirmation; it does not query a separate USB product-name API. The 2.03 version `30110_06.2026060501` and its different `libObj.so` are rejected.

It checks `/proc/partitions`, sysfs major/minor/start/size, the block node identity and absence of a symlink, requiring `nflasha5`, **61,440 KiB / 62,914,560 bytes**, start sector **180224**, length **122880 sectors**. If this kernel does not expose the required sysfs metadata, it stops; do not bypass the checks. These additional identity checks still need hardware validation.

FileControl READ streams the whole partition twice into exclusive private files, fsyncs them and compares full sizes, host hashes and every byte. `WBI1` is required. A zero first sector returns `already-invalid` and cannot authorize another write; unknown headers stop. Results, originals and partial reads are retained in the session, never overwritten. Preparation returns a `token`, both hashes, an eMMC warning and a `confirmation` string. Review them before proceeding.

## 3. Obtain explicit eMMC-write confirmation, then invalidate once

Explain to the owner: **this writes internal eMMC; it invalidates the first 512 bytes of this camera's WBI, may fail under power/USB faults, and recovery is not automatic.** Get explicit permission for this operation after reviewing the two backups. Confirm a workable recovery route, not just possession of a backup. Do not prefill confirmation without the owner's consent.

Replace `PREPARED_TOKEN` and `BACKUP_SHA256` with the exact returned values. Use the same session and tool path:

```sh
"$WIFI_PYTHON" -B tools/wifi.py request --session private/wbi-01 '{"action":"wbi-drop","prepared":"PREPARED_TOKEN","sony_tool":"private/sony-wbi/ud_wbi_drop.elf","confirm_emmc_write":"INVALIDATE WBI BACKUP_SHA256","recovery_ready":true}'
```

The action rechecks firmware, fingerprints, properties, device identity, saved backups and a fresh whole-partition read against preparation. The token is consumed before any possible execution, preventing blind retries. Sony's exact utility and the generated configuration are uploaded through Jiritsu SET_FILE2 and **fully read back with GET_FILE for host byte comparison** before execution. Camera BusyBox hashes/hex dumps are not trusted.

Sony's utility runs once. Even when its response reports failure, the tool attempts full partition readback. Success requires the known output, exit 0, zero first 512 bytes and **all remaining 62,914,048 bytes unchanged**. Any mismatch stops the server and saves diagnostics. Fixed temporary files are cleaned up; a USB failure may prevent cleanup. No general block writer and no automatic restoration of old WBI are provided.

## 4. Cold boot, acceptance and recovery

Close normally and check `terminal_closed=true` and `service_returned=true`. Unplug USB, switch OFF, wait for the access lamp, remove the battery for about 30 seconds, then boot. In a **new read-only ready session**, run `inspect` and `boot-check`. Require unchanged patch/properties, no warm-resume marker, TypeNB/five items, and owner confirmation that the native band menu opens. Keep the session open for menu interaction. Phone hotspot transfer and router remote operation are separate functional checks.

If any write/readback error occurs, stop and preserve the entire private session, including `wbi-*-read1.bin`, `read2.bin`, `prewrite.bin`, `after.bin`, result JSON, consumed marker and toolkit responses/state. A timeout can mean writing occurred. Do not blindly retry or automatically power-cycle after an unexplained difference. Follow [recovery](recovery.md): qualified review may use toolkit fastboot with **this camera's exact original 60 MiB image and verified partition map**, followed by whole-partition readback. Never restore another camera's WBI, and never restore old WBI merely to undo successful invalidation: it can restore obsolete runtime state. This release has no hardware-tested WBI rollback. Normal warm boot is not permanently disabled.
