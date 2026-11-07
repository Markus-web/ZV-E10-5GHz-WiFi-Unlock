# Warm Boot Image recovery (Agent assisted)

**English** | [简体中文](wbi.zh-CN.md)

Use this only when firmware 2.02 has the verified one-byte patch and Backup values `01/02/16`, but `boot-check` reports a TypeRK four-item Page1 or warm-resume markers and the native band menu is absent. Do not repeat the firmware or Backup writes. This is a supervised recovery procedure, not an automatic installer action.

Sony's Warm Boot Image (WBI) is stored in `nflasha5`. On the tested camera, a saved old WBI restored a four-item TypeRK page while the patched code was present. Removing the battery for about 30 seconds did not prevent that resume. Invalidating the saved image allowed the next boot to construct the five-item TypeNB page. This does **not** permanently disable normal warm boot.

## Required safeguards

1. Confirm first-generation ZV-E10, displayed firmware **2.02**, target library hash and the three Backup values. Confirm `/proc/partitions` reports `nflasha5` as **61,440 KiB (62,914,560 bytes)**. Sony's matching `partinf.conf` identifies it as **Warm Boot Image**, start `0x05800000`, size `0x03C00000`, type `2`.
2. In one authenticated persistent service session, read the **entire** `nflasha5` twice to separate private host files using a verified raw-read facility. Require exact size, matching SHA-256 and byte-for-byte equality. Require a `WBI1` header. Preserve both files and a tested route to restore this camera's own partition through the existing fastboot recovery tools. Do not substitute another camera's image.
3. Obtain Sony's original `ud_wbi_drop.elf` from a firmware package the owner may use; do not download an unverified binary or commit it here. The tested file is 6,200 bytes, SHA-256 `f2a5b27a0c11d55a612d61e61e82c55278efb744052ecb8ec2cbbd8851d0ea6e`. Use the matching five-entry `partinf.conf` from that package. Upload both to temporary camera paths, then compare camera-side hashes with host files before execution. Do not run a guessed block-device command.
4. Run the Sony utility once, with that `partinf.conf`, only after all checks pass. The tested output was `[UD_WBI_DROP] /dev/nflasha5 wbi_drop`, exit 0. Read the entire partition again before power-off. Require the first **512 bytes all zero** and the remaining **62,914,048 bytes identical** to the backup. Any other difference stops the procedure; preserve all logs and use the verified recovery route.
5. Close the service session normally. Unplug USB, switch OFF, wait for the access lamp, remove the battery for about 30 seconds, then boot. In a **new read-only ready session**, run `inspect` and `boot-check`. Require no warm-resume marker, TypeNB/five items, unchanged patch and Backup values. Ask the owner to open the native band menu; test hotspot transfer and router connection separately if needed.

The Sony executable is proprietary and is **not bundled**. The public `wifi.py` intentionally offers only a read-only `boot-check`, because its current toolkit integration does not provide a separately hardware-validated, transaction-guarded WBI write and full-partition readback action. If a required backup, identity check, upload hash, readback, or restoration route is unavailable, stop and keep the camera as-is.

The 2026-11-07 camera test achieved exactly this 512-byte difference, then booted without warm-resume markers; Page1 became TypeNB/five items and the owner confirmed native menu, 5 GHz phone transfer, and 5 GHz router remote operation. This result applies to the tested 2.02 state. Firmware 2.03 has not received equivalent post-recovery acceptance.
