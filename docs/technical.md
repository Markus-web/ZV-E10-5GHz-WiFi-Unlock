# Technical notes and research lessons

**English** | [简体中文](technical.zh-CN.md)

This document explains the minimal modification and the research behind it. See [test records and sources](evidence.md) for hardware results and source material.

## Warm Boot Image and menu construction

Sony stores a Warm Boot Image in the 60 MiB `nflasha5` partition. On the tested 2.02 camera, the patched `CautionConfig.so` jump table and correct Backup values coexisted with an old TypeRK/four-item Page1 after warm resume; the frequency node `0x285` had not been created. Battery removal for about 30 seconds did not guarantee a fresh Page1. After the backed-up Sony updater invalidated the WBI header, the next boot lacked warm-resume markers and both global and current Page1 held TypeNB/five items, including an enabled `0x285`. The owner confirmed the native menu and 5 GHz operations. See [WBI recovery](wbi.md) for guarded acceptance. This is a 2.02 hardware result; 2.03 remains unaccepted under equivalent conditions.

## Native menu: TypeNB, not a replacement UI

Static comparison found the original A7C Wi-Fi page selects **TypeNB**, which contains Frequency Band; the ZV-E10 selects **TypeRK**, which omits it. The single-byte change in `CautionConfig.so` changes the native page selection at file offset `0xD778E4` from `20` to `1B`. It does not transplant A7C code or invent an English-only menu.

A second gate is Backup property `0x01071C54`. All 28 analyzed ZV-E10 factory templates had `00`; 24 of 26 A7C templates had `01` (AF1 was the exception). On the tested ZV-E10, native TypeNB selection plus property `01` exposed a working Sony 2.4/5 GHz page. The correct native frequency-object mapping was retained; old experiments redirecting the row to unrelated object types are not the solution.

The frequency choice applies to direct connections; it is not a global force-5-GHz command for router association. Sony's [A7C guide](https://helpguide.sony.net/ilc/2020/v1/en/contents/TP1000156044.html) describes the native direct-connection scope. Actual router association is independently governed by its selected profile, available networks and driver rules.

## Backup and B/C startup

Sony's BK4 configuration database stores property IDs and values. Here **B/C are research shorthand** for the last hexadecimal digit in `0x00A5000B` and `0x00A5000C`, not claimed official Sony names. They select NVRAM file numbers 1–26 for different network paths. B serves the normal camera GO hotspot; C serves ordinary access-point/STA connection. They do **not** separately represent 2.4 and 5 GHz.

Code evidence: the network service passes the mode-dependent selector to `libWlanResource`; its `get_bcmdhd_insmod_args` path constructs a numbered `bcm4339_*_%02d.txt` path for driver initialization. Three factory directories contain different RF calibration combinations. Preserve those directories; do not mix calibration data or borrow complete A7C NVRAM files.

The service API used in the demonstrated workflow is:

```python
original = bytes(camera.readBackup(property_id))
camera.writeBackup(property_id, value)
camera.saveBackup(property_id >> 16)
assert bytes(camera.readBackup(property_id)) == value
```

Use Sony's property interface so its persistence mechanism is invoked; don't hex-edit the two BK4 files. Save each exact original and full private database snapshots first. Whole databases also change during normal use: the final audit found many non-Wi-Fi property differences and did not reset them.

China's `B=2/C=22` selects **XR/76** and **XR/143**. In the real ZV-E10 2.02 hotspot/router paths, those revisions were actually read from the active driver and functional tests succeeded. Original `09/09` selected XR/83, which only exposed 2.4 GHz in the recorded baseline. See [region table](regions.md).

## Hardware and original-file comparisons

Public regulatory inventories identify the Murata **Type1DR** family for [ZV-E10 (IFT)](https://www.ift.org.mx/node/19562) and [A7C (NTC list, printed page 187)](https://region7.ntc.gov.ph/wp-content/uploads/2024/01/RCE_08312021.pdf). Firmware artifacts and the running ZV-E10 driver identify the Broadcom BCM4339 platform. This supports the shared-module/platform statement, not identical boards, antennas or certification across all variants.

A7C and ZV-E10 2.03 normal `bcm4339.bin`, `bcmdhd.ko`, supplicant and the examined network config files matched byte for byte. All 78 numbered NVRAM files had matching same-number XR/regrev selections; an `ed_thresh5g` text difference (`-80` versus `-90`) was observed but not established as the unlock or a transmit-power limit. No replacement wireless firmware or NVRAM is needed in the verified minimum.

A7C has region-dependent single/dual-band product variants in Sony's [official specifications](https://helpguide.sony.net/ilc/2020/v1/en/contents/TP1000156734.html). A module name and factory template label do not prove that a modified ZV-E10 has a corresponding approval.

## ext filesystem extraction and version discipline

A file's bytes are not necessarily contiguous in its partition. Follow the file's **inode** (filesystem metadata locating its actual data blocks), including indirect blocks/extents as appropriate to the filesystem, or use a correct ext filesystem reader. A continuous slice starting at a guessed first block can contain unrelated blocks and yield plausible but wrong ELF content. Verify file size, ELF segment layout, and full hash against an independently exported copy.

Distinguish the ext4-style inode extraction used for offline eMMC evidence from the camera's observed `/usr` mount, reported as **ext2 on `/dev/nflasha15`**. The patch offset is a logical file offset, never a physical partition offset. Historical partition-patch candidates explicitly mapped logical bytes through inode data blocks; they are not needed for normal USB installation.

| Artifact | Verified SHA-256 / meaning |
| --- | --- |
| Factory `CautionConfig.so`, 17,694,160 B | `5ad8746a229da259fe00b297e8f897d682f7ae9a13393025b3d1c95a808e68d7` |
| Minimal patched library, same size | `14f42cc09ee1b9ddde5352482c13b68e5a5e97d9d79e8456087b5e0b7af6ff6a` |
| Factory 2.02 `viewUnified2.so` | `bdf0690fbeef898bba1114c5804e88fdb437b5e31598eac32df05925504f6e1a`; matches analyzed 2.03 |
| Factory 2.02 `libObj.so` | `bc0deb2f0e94218752e42ce6f5a3576d7456971eb63fbde705ffbd9b3a7fdeea` |
| Analyzed 2.03 `libObj.so` | `cfdc59b94fa56116e9d99154ca03a2c1aaf6039dd272679b78b0b76e21c722ac`; differs from 2.02 |
| Normal BCM4339 firmware | `cbb464370e3a954736b05ed16377fc53450eda50252f2b8ffe0fd8464ff200b5` |

The camera's displayed version was **2.02**. The internal string `30110_05.2025031501` also appears in the analyzed 2.03 material and is not a sufficient version discriminator. Identical target-library bytes establish a local patch relationship; they do not prove every 2.03 path works. The installer deliberately requires model/version confirmation and the full target hash.

## CLM and unresolved regulatory questions

CLM is Broadcom's compiled radio regulatory data. The analyzed firmware contains 26 XR revision records matching numbered NVRAM selections. The CLM header is at file `0x79058`, virtual header `0x1F9058`, API `9.10.139`, compiler `1.26.11`. For this image, virtual-to-file translation subtracts `0x180000`. Header/table structure and top-level channel ranges were parsed.

The full **XR revision → locale → permitted channels/power/DFS** chain has not been decoded reliably. Top-level 5 GHz ranges cannot be assigned to every XR record: XR/83 is the counterexample, with no 5 GHz entries in the original ZV-E10 runtime. [OpenWrt's bcmclm source](https://lxr.openwrt.org/source/firmware-utils/src/bcmclm.c) was a format reference, not a complete Sony region decoder; no OpenWrt code is copied here.

Later China runtime tests established functional XR/76 and XR/143 behavior, superseding older “untested China” notes. They did not resolve transmit power, DFS/TPC, indoor restrictions, or local type approval. XR is an internal two-character code, not an ISO-country translation. No reliable automatic profile change on international travel has been established.

## Discarded approaches

- Temporary US/0 NVRAM replacement could expose 5 GHz, but was unnecessary for the final China solution and changed the channel set. The final audited state restored original NVRAM and removed the US runtime copies.
- Extra `viewUnified2` virtual-slot / permission / row-factory patches were exploratory. Some had no visible menu effect; a single-slot ELF candidate was never deployed. None is part of the verified minimum. Do not reuse runtime addresses from old sessions.
- Patching supplicant/P2P setup, full BCM4339 firmware or driver is unnecessary for the proven minimum. Absence of a need is not proof that every possible patch has no effect.
- The attempted **whole-library `cp`** failed with “No space left on device” and left an 11,173,888-byte truncated file. A running process still mapped the old deleted inode; current operation did not prove next boot would work. Hardware fastboot restored damaged partitions from the owner's backup before further USB testing.
- Camera BusyBox `dd` lacked usable `conv=notrunc`; using it to seek/write truncates. Never use that path for this patch.

## Persistent USB-C byte writer

After restoring an intact factory library, the proven ARM Linux helper opened the existing fixed path using `O_RDWR`, **without `O_CREAT` or `O_TRUNC`**. It sought to the known offset, checked `20`, wrote `1B`, called `fsync`, and reread it. Exit codes 10–16 distinguish open, seek, read, comparison, write, sync and verification failures. It cannot validate a complete hash itself: the host must do that before and after. The Wi-Fi actions add those full-file guards and delegate the session lifecycle to zv-e10-toolkit. Generic property snapshots, writes and persistence are implemented once in the toolkit, calling the existing PMCA-RE methods.

The actual library retained its inode and full length. Exported bytes differed from factory at only the expected offset; a battery/USB-disconnected cold boot preserved it. The original menu worked afterwards. Fastboot was needed to recover the earlier failed experiment, **not for normal single-byte USB-C installation**.
