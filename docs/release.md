# Licensing and validation scope

**English** | [简体中文](release.zh-CN.md)

## License boundaries

- Original project code, helper assembly and documentation are MIT licensed; see [LICENSE](../LICENSE).
- Service server/client, queue, authentication and generic Backup actions come from external [zv-e10-toolkit](https://github.com/dino2048/zv-e10-toolkit). This repository keeps only Wi-Fi-specific rules and patch operations, without copying toolkit implementations. Its [MIT notice](../licenses/zv-e10-toolkit-MIT.txt) is retained for attribution.
- Sony-PMCA-RE is an external runtime dependency, not bundled; its [MIT notice](../licenses/Sony-PMCA-RE-MIT.txt) is retained. Downloaded dependencies retain their own licenses and notices when redistributing an environment. No Python environment, libusb, clang or GNU binutils is distributed here.
- OpenWrt `bcmclm.c` is GPL-2.0-or-later and is only a technical research reference; no implementation is copied here.
- `patch.arm` and `restore.arm` are our small ARM Linux programs, not Sony firmware. Both have assembly source.
- Sony firmware, proprietary libraries, driver, NVRAM/calibration, personal backups, device keys and credentials are not included or licensed by this project. Published hashes and offsets do not grant permission to redistribute Sony code. Sony and product names belong to their owners.

## Validation scope

- **Hardware-validated underlying procedure:** one byte plus three properties, native menu, 5 GHz hotspot photo transfer, remote shooting through a 5 GHz router, and post-install cold-boot persistence. See [test records](evidence.md).
- **Hardware-validated read-only integration:** on Linux x86_64, exact 2.02 version gating, full `inspect` exports, property reads, mount reporting, warm-resume `boot-check`, normal teardown and return to Mass Storage.
- **Offline-validated write integration:** target hashes, patch preconditions, simulated writes and restore flow; toolkit original-value guards, private snapshots, readback and normal/error teardown.
- **Not fully hardware-validated:** integrated patch, rollback and WBI write actions, the reverse-byte helper, Linux write behavior and real USB or filesystem failures.

The dependency is pinned to toolkit commit `e8d4cb566fa04dac249e10431302e4d950550bde`; installation includes the exact checkout command. Results are in [offline-checks.json](offline-checks.json), a machine-readable result file whose field names are language-independent.

## Checks without a camera

After preparing the environment and variables in [installation](install.md), run from this repository:

```sh
"$WIFI_PYTHON" -B tools/check_offline.py
"$WIFI_PYTHON" -B -m unittest discover -s tools -p test_safety.py -v
"$WIFI_PYTHON" -B -m unittest discover -s tools -p test_session_summary.py -v
"$WIFI_PYTHON" -B -m unittest discover -s "$ZVE10_TOOLKIT/linux/tests" -v
"$WIFI_PYTHON" -B "$ZVE10_TOOLKIT/linux/host/zve10_terminal_server.py" --self-test
```

These checks neither connect to a camera nor require private firmware files. Maintainers may use `check_offline.py` options `--factory`, `--patched` and `--tested-helper` for extra comparison against private evidence; do not add those fixtures to the repository.

## Sharing files

Exclude `private/`, `vendor/`, virtual environments and external camera backups from public archives. `.gitignore` controls Git tracking and does not protect arbitrary zip operations. Private snapshots may contain device identifiers, credentials or keys.

New SET_FILE2 uploads, version enforcement, WBI transaction guards and full readback have offline simulation tests. A 2026-11-07 Linux session physically validated the read-only integration and privacy-safe summary against system **2.02**. System 2.03 is unsupported. The exact Sony ELF source package was 2.03, not the installed camera system. Integrated writes, new sysfs identity checks, rollback and real power/USB failure behavior remain untested on hardware.
