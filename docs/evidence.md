# Test records and sources

**English** | [简体中文](evidence.zh-CN.md)

This document summarizes hardware tests on the first-generation ZV-E10, firmware 2.02, and the supporting technical sources.

## Camera and configuration

- Camera: first-generation Sony ZV-E10, displayed firmware 2.02.
- Host: macOS, using a persistent USB-C service session.
- Region: mainland China; B=2/C=22, selecting XR/76 and XR/143.
- Modification: `CautionConfig.so` at `0xD778E4:20→1B` and three Backup properties.
- Record dates: 2026-11-05 through 2026-11-06.

## Hardware results

| Check or experiment | Result | Scope |
| --- | --- | --- |
| 2.02/2.03 file comparison | Inode-extracted target library matched the 2.03 sample; `libObj.so` differed | An identical target library does not establish whole-version compatibility |
| Native band menu | TypeNB plus Backup menu property `01` exposed the 2.4/5 GHz page | Menu operation tested; A7C templates compared statically |
| Backup writes | Originals saved; B/C changed from `09/09` to `02/16` through Sony's service interface and immediately reread | Menu property was `01` |
| 2.4/5 GHz camera hotspot | Active driver reported XR/76; 2.4 GHz channel 1 and 5 GHz channel 157/80 MHz; phone photo transfer succeeded | No transfer-speed benchmark |
| Router connection and remote shooting | Active driver reported XR/143; connections on channels 6 and 40; remote capture and photo reception through a 5 GHz router at 40/80 MHz | Dedicated Send to Computer not tested |
| Minimal-state audit | One target-library byte and three properties; examined other libraries, driver, firmware and 81 NVRAM files matched factory references | Not a whole-eMMC provenance audit; unrelated user settings were not reset |
| USB-C in-place installation | Starting from an intact factory library, the non-truncating helper wrote `20→1B`; full export differed at only that byte | Normal installation does not require fastboot |
| Post-install cold boot | USB/battery disconnected; full library length and patch persisted, properties `01/02/16`, `/usr` read-only; owner confirmed the menu | Earlier functional tests were not repeated after this cold boot |

Hotspot/router functionality and the final USB-C installation have separate hardware records. They do not constitute a complete hardware acceptance test of the newly integrated host tool.

## In-place writing and recovery lessons

An earlier whole-file `cp` attempt ran out of space and truncated the library to 11,173,888 bytes. The camera still ran, but its next boot was at risk. Additional hardware and fastboot were used to restore damaged partitions from the same camera's original backup before testing USB-C byte installation.

The successful USB-C installation retained the inode and full file length. After cold boot the library MD5 was `4823e8af6a38cece419636332e00b5a2`; the service session closed normally with `terminal_closed=true` and `service_returned=true`. The installation therefore uses in-place byte writing and prohibits whole-file replacement or truncating BusyBox `dd` writes.

## Reproducible checks

Factory/patched file lengths, SHA-256 hashes and the unique byte difference are in [technical notes](technical.md). Installation saves the owner's own files and property snapshots on the host for comparison and recovery. Keep these camera-data snapshots private.

The region table derives from static analysis of original A7C 2.03 Backup templates. CLM headers and top-level ranges were parsed, but complete per-XR power/DFS rules remain undecoded; the mainland China functional findings come from active readings and actual camera use.

## Sources

- [Sony A7C Frequency Band](https://helpguide.sony.net/ilc/2020/v1/en/contents/TP1000156044.html): native menu and direct-connection scope.
- [Sony A7C Access Point Set.](https://helpguide.sony.net/ilc/2020/v1/en/contents/TP1000115299.html): router setup.
- [Sony ZV-E10 PC Remote](https://helpguide.sony.net/ilc/2070/v1/en/contents/TP0002392805.html): direct/AP methods, pairing, capture and storage.
- [Sony A7C specifications](https://helpguide.sony.net/ilc/2020/v1/en/contents/TP1000156734.html): regional wireless variants.
- [IFT Sony equipment inventory](https://www.ift.org.mx/node/19562): ZV-E10 Type1DR entry.
- [NTC 2021 inventory](https://region7.ntc.gov.ph/wp-content/uploads/2024/01/RCE_08312021.pdf): A7C Type1DR entry, printed page 187.
- [Sony-PMCA-RE](https://github.com/ma1co/Sony-PMCA-RE), [MIT license](https://github.com/ma1co/Sony-PMCA-RE/blob/master/LICENSE.txt): service protocol; the toolkit pins `a82f5baaa8e9c3d9f28f94699e860fb2e48cc8e0`.
- [zv-e10-toolkit](https://github.com/dino2048/zv-e10-toolkit): backup, persistent service and recovery. This project uses commit `e8d4cb566fa04dac249e10431302e4d950550bde`.
