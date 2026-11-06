# AI agent entry point

Read README.md, docs/install.md, docs/regions.md, docs/recovery.md, and docs/release.md before device access. Do not rely on earlier chat history. Explain results in the owner's language. Distinguish camera-tested operations, static evidence, and the offline-only validation of the Wi-Fi integration.

## Scope and permission

- Support only first-generation ZV-E10 firmware **2.02** for ordinary installation. Ask the owner to confirm model and the camera's displayed firmware version. `30110_05.2025031501` alone does not distinguish 2.02 from 2.03. An identical library in 2.03 is static evidence, not full compatibility.
- First inventory USB connection, boot status, power, backup availability, existing modifications, and host dependencies. Strongly recommend and help verify an eMMC user-area backup with zv-e10-toolkit. Obtain explicit acknowledgement if the owner chooses to proceed without it; never imply that file snapshots replace it.
- Ask the owner for the actual country/region of operation and explicit confirmation of the B/C choice and scope: one file byte, three Backup properties, temporary helper upload and `/usr` remount. Never infer region. Only China B=2/C=22 has functional evidence; stop the ordinary path for any untested region. Do not experiment without a separate request.
- Do not connect or modify a camera when the current task is only document review or packaging. Do not publish, upload, or push without a publication request.

## Exact implementation

Use tools/wifi.py, not newly guessed offsets, raw partition writes, whole-file copies, or ad-hoc Backup database editing. It imports zv-e10-toolkit's existing server/client/common helpers and generic Backup property actions. Connection, queue, authentication, timeouts and teardown belong to the toolkit, not this repository. Use the toolkit environment and explicit ZVE10_TOOLKIT/WIFI_PYTHON settings from docs/install.md. Use toolkit commit 67b1b142bff0421d5d666da96ce45f274fd61ee2; docs/install.md includes the exact checkout command. It uses the demonstrated root-shell byte writer. Do not launch a one-shot callback probe: keep one persistent service connection throughout sampling. Confirm state.json is `ready` **before asking the owner to use camera menus**. Only one service connection at a time.

For installation, require length **17,694,160**, SHA-256 `5ad8746a229da259fe00b297e8f897d682f7ae9a13393025b3d1c95a808e68d7`, and byte `20` at file offset `0xD778E4` in `/usr/lib/CautionConfig.so`. Expected result: SHA-256 `14f42cc09ee1b9ddde5352482c13b68e5a5e97d9d79e8456087b5e0b7af6ff6a`, exactly one difference `20→1B`. Unknown content must stop. Already patched content should be inspected, not patched again.

Save original full library, `/setting/Backup.bin`, `/setting/Backup.bak`, and the three property values privately on the host before writes. Inspect additionally snapshots before each write; never overwrite earlier evidence. `backup-write` restricts keys/values here and calls the toolkit generic Backup action; the toolkit invokes PMCA-RE readBackup/writeBackup/saveBackup(id >> 16)/readBackup. Do not duplicate that implementation or edit database files directly. For China use `0x01071C54=01`, `0x00A5000B=02`, `0x00A5000C=16` (hex 16 = decimal 22). Do not assume the owner's originals are `00/09/09`.

Never alter BCM4339 firmware, driver, NVRAM, radio calibration, unrelated Backup fields, or other menu libraries. B/C are mode-specific profile selectors, not one selector per band. Do not change sales region or model identity.

## Checks, failure, and completion

Follow the concrete commands in docs/install.md. Review each response before the next dependent write. No blind retries on timeout. Stop on mismatched values, short reads, helper failure, unexpected mounts, failed remount, or unknown version. A tool failure after a write does not imply nothing changed; reconnect only after reviewing state and preserved evidence.

Do not power off a camera with a truncated/corrupt library. Never use `cp` over the loaded library or BusyBox `dd` as a writer: the demonstrated versions truncate or run out of space. File offsets are not block-device offsets. Recovery is described separately; do not flash an entire partition just to reverse one byte.

Verify the complete exported library and all three properties after writing, confirm `/usr` read-only, remove the temporary helper, then close the session normally and check `terminal_closed=true` and `service_returned=true`. Ask the owner to switch OFF, wait for the access lamp, unplug USB and remove the battery for about 30 seconds, then reconnect. Create a new persistent ready session, inspect again and check the native menu. Keep that session open during owner interaction and read-only active Wi-Fi sampling.

Report file/property state, cold-boot persistence, user-reported menu/function results, and measured active radio state separately. Driver channel lists are not regulatory certification. No performance figures without a benchmark. Restore the exact saved originals on request using docs/recovery.md; don't reset all Backup settings.

## Privacy and handoff

Put all Wi-Fi session output in ignored `private/`. The reused toolkit also maintains its normal session pointer inside its own checkout. They may contain device identity, credentials, and keys; never commit or upload them. Publish only carefully redacted summaries. End with evidence paths, actions completed, current state, recovery readiness, and limitations. The Wi-Fi integration has offline checks only; report that accurately and use the existing hardware records for the underlying procedure.
