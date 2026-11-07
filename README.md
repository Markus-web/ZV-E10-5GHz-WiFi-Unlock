# ZV-E10 5 GHz Wi-Fi Unlock

**English** | [简体中文](README.zh-CN.md)

## Fun fact

The ZV-E10 and original A7C share the Murata Type 1DR wireless module and Broadcom BCM4339 chip. The firmware already contains Sony's native 2.4/5 GHz band menu, hidden by Sony. See [technical notes](docs/technical.md).

This project unlocks native 5 GHz Wi-Fi on the first-generation Sony ZV-E10 for better wireless photo transfers and remote connections.

**Tested camera: first-generation ZV-E10, firmware 2.02.**

## What changes

Only **one byte in `CautionConfig.so` and three Backup properties** need changing:

| Target | Change / purpose |
| --- | --- |
| `/usr/lib/CautionConfig.so`, file offset `0xD778E4` | `20` → `1B`: select the native TypeNB Wi-Fi menu |
| Backup `0x01071C54` | `01`: enable the frequency-band menu |
| Backup `0x00A5000B` | `02`: hotspot profile XR/76 |
| Backup `0x00A5000C` | `16` hex = **22 decimal**: router-connection profile XR/143 |

The table shows the mainland China configuration. Connect the camera to a computer with a USB-C data cable to make these changes; fastboot is not needed for installation. See [installation instructions](docs/install.md).

**After installation, verify a real cold boot.** A saved Sony Warm Boot Image can keep the old four-item Wi-Fi page even when the byte and properties are correct; removing the battery for 30 seconds may still resume it. This was diagnosed and resolved on firmware 2.02. Require runtime TypeNB/five items and the actual native band menu. The installer includes read-only `boot-check` plus separately confirmed [WBI recovery](docs/wbi.md), with two full backups and complete readback. Helper uploads use Jiritsu SET_FILE2 with host byte comparison. Only system **2.02 (`30110_05.2025031501`)** is supported; 2.03 is refused. The new integration has offline tests only.

## Features

- **Camera hotspot:** select 2.4 GHz or 5 GHz in the native menu for direct connections such as phone photo transfers. See Sony's A7C [frequency-band guide](https://helpguide.sony.net/ilc/2020/v1/en/contents/TP1000156044.html).
- **Router connection:** connect to a 2.4 GHz or 5 GHz router for features such as remote shooting. See the A7C [access-point setup guide](https://helpguide.sony.net/ilc/2020/v1/en/contents/TP1000115299.html). When both bands use the same SSID and encryption, the stronger access point is displayed, as described in Sony's [band guide](https://helpguide.sony.net/ilc/2020/v1/en/contents/TP1000156044.html).

5 GHz hotspot photo transfer, router connection and remote shooting through a router have been tested with the mainland China configuration. See [test records](docs/evidence.md).

## Back up before installation

**Strongly recommended: connect the camera to a computer using a USB-C data cable and back up its entire eMMC user area with [zv-e10-toolkit](https://github.com/dino2048/zv-e10-toolkit).** If firmware flashing fails, additional external hardware can be used for fastboot recovery.

## Install with an AI agent

Clone the repository and open its directory in Codex or Claude Code:

```sh
git clone https://github.com/dino2048/ZV-E10-5GHz-WiFi-Unlock.git
cd ZV-E10-5GHz-WiFi-Unlock
```

Suggested prompt:

> Read AGENTS.md and docs/install.md. Help me check compatibility and back up my camera before installing. Ask me to confirm my actual country of use and the exact changes before writing. Preserve my original values and verify recovery steps.

Installation reuses [zv-e10-toolkit](https://github.com/dino2048/zv-e10-toolkit). Have the agent follow the [installation guide](docs/install.md) to prepare the environment and perform the procedure.

[Installation](docs/install.md) · [Agent instructions](AGENTS.md) · [Verification and recovery](docs/recovery.md)

## Regions and compatibility

Countries and regions have different requirements for radio bands, transmit power and other wireless parameters. Choose the region profile for where the camera will be used.

The table lists A7C factory profiles and corresponding XR revisions. **Only mainland China B=2/C=22 has been functionally tested on ZV-E10.**

| A7C factory region label | B / C (decimal) | XR revisions (hotspot / router) | ZV-E10 status |
| --- | --- | --- | --- |
| Mainland China CN1/CN2 | 2 / 22 | 76 / 143 | Functionally tested |
| Japan J1 | 3 / 23 | 77 / 144 | Untested |
| Europe CEC | 14 / 23 | 88 / 144 | Untested |
| North America UC2 | 18 / 25 | 139 / 146 | Untested |
| KR2 | 14 / 23 | 88 / 144 | Untested |
| AP2 | 14 / 23 | 88 / 144 | Untested |
| IN5 | 14 / 23 | 88 / 144 | Untested |
| JE3 | 20 / 22 | 141 / 143 | Untested |
| E38 | 17 / 24 | 138 / 145 | Untested |
| ALLLANG | 14 / 23 | 88 / 144 | Untested |
| AF1 | 9 / 9 | 83 / 83 | Untested; factory band menu disabled |

See the complete [region reference](docs/regions.md).

## Technical material and credits

[Technical notes and reverse-engineering lessons](docs/technical.md) · [Test records and sources](docs/evidence.md) · [Validation scope](docs/release.md)

Thanks to [Sony-PMCA-RE](https://github.com/ma1co/Sony-PMCA-RE) for the service protocol and [zv-e10-toolkit](https://github.com/dino2048/zv-e10-toolkit) for backup, service and recovery tools. Original project code and documentation are MIT licensed; third-party notices are in [licenses/](licenses/). No Sony firmware, personal backups, device keys, MAC addresses or Wi-Fi credentials are included.

## Disclaimer

This is unofficial and not endorsed by Sony. Firmware modification and radio unlocking can cause device failure, data loss, warranty issues and regulatory violations. A7C factory settings do not establish local radio approval for a modified ZV-E10. You are responsible for the rules where you use the camera.
