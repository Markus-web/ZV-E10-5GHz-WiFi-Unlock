# AI Agent 辅助安装

**简体中文** | [English](install.md)

本流程需要用户与 Agent 配合完成。相机端的单字节写入和底层服务、Backup 操作已有实机记录；`wifi.py` 只负责 Wi-Fi 专用操作，直接调用 zv-e10-toolkit 的服务端、客户端、传输方法和通用 Backup 接口。Wi-Fi 主机工具集成已完成离线检查，验证范围见[许可与验证范围](release.zh-CN.md)。操作前先读 [AGENTS.md](../AGENTS.md) 和[恢复说明](recovery.zh-CN.md)。

## 1. 准备环境，暂不连接相机

需要 Python 3 虚拟环境和 libusb。macOS 可通过常用包管理器安装 libusb；也可用 `LIBUSB_PATH` 指定库路径。toolkit 会检查 Apple Silicon 和 Intel Homebrew 的常用路径。已有实机流程使用 macOS；本项目尚未在 Linux 上完整验证，未提供 Windows 启动器。

本项目使用 [zv-e10-toolkit `e8d4cb5`](https://github.com/dino2048/zv-e10-toolkit/commit/e8d4cb566fa04dac249e10431302e4d950550bde) 提供的通用 Backup 属性接口和持久会话扩展入口。克隆后切换到以下固定提交：

```sh
mkdir -p vendor
git clone https://github.com/dino2048/zv-e10-toolkit.git vendor/zv-e10-toolkit
export ZVE10_TOOLKIT="$PWD/vendor/zv-e10-toolkit"
git -C "$ZVE10_TOOLKIT" checkout --detach e8d4cb566fa04dac249e10431302e4d950550bde
PYTHON=python3 sh "$ZVE10_TOOLKIT/linux/scripts/setup.sh"
export WIFI_PYTHON="$ZVE10_TOOLKIT/linux/.venv/bin/python"
"$WIFI_PYTHON" -B tools/wifi.py --help
```

已有更新版 toolkit 时，将 `ZVE10_TOOLKIT` 指向该目录，`WIFI_PYTHON` 指向其解释器即可，不必复制代码或重复建立环境。用户指定了解释器时优先使用。toolkit 的安装脚本负责依赖及固定版本 Sony-PMCA-RE；本项目不另存一套公共工具、依赖清单、服务端或客户端，也不会自动修改外部 toolkit。

仓库附带两个小型 ARM Linux 程序及汇编源码。`patch.arm` 就是历史实机成功使用的文件，MD5 为 `8a1bd57091f544a758300b7151d94f05`。`restore.arm` 使用相同源码反转原值和目标值构建，目前仅做离线检查。如需重建，使用支持 ARM 目标的 clang 和 GNU `arm-none-eabi-ld`：

```sh
sh tools/build-helpers.sh
```

无需 ARM libc。源码文件名或工具链变化可能改变 ELF 符号和元数据；应核对加载段及指令、数据，不能只比较文件大小。见[发布核查](release.zh-CN.md)。

## 2. 核对相机并备份

确认是 **ZV-E10 第一代，机内版本页显示 2.02**，供电稳定、正常启动，且没有尚未处理的旧修改。强烈建议用 USB-C 数据线连接相机和电脑，通过 [zv-e10-toolkit](https://github.com/dino2048/zv-e10-toolkit) 完整备份 eMMC 用户区并校验。备份可能包含设备秘密，应私密保管。写入前了解额外硬件 fastboot 恢复的途径；备份并不保证所有故障都能恢复。

将 USB 连接设为 **海量存储器（Mass Storage）**，使用支持数据传输的 USB-C 线。相机处于 USB 存储模式时可能无法操作菜单，应先建立持久服务会话，再请机主操作菜单。

机主需要明确确认实际使用国家或地区及修改范围。目前普通安装流程仅采用已实测的中国大陆 B=2/C=22。型号、固件、地区或目标文件不明时停止，不自动升级或降级固件。

## 3. 保持一个服务会话

在仓库根目录另开终端：

```sh
sudo ZVE10_TOOLKIT="$ZVE10_TOOLKIT" "$WIFI_PYTHON" -B tools/wifi.py serve --session-dir private/install-01 --owner-authorized-write
```

每次使用新的会话目录，开始前确认没有其他服务连接。macOS 的已验证 USB 路径需要管理员权限；使用正常的系统授权或终端输入，不要让 Agent 收集密码。会话在收到 `close` 或空闲十分钟后结束。toolkit 将队列及响应文件交回客户端 UID，必要时用 `--client-uid` 指定；Wi-Fi 快照归 toolkit 目录的所有者。只检查、不修改时，省略 `--owner-authorized-write`。

读取 `private/install-01/state.json`，等到 `state` 为 `ready`。两个终端及管理员进程都需要正确的 `ZVE10_TOOLKIT`、`WIFI_PYTHON`。随后在 Agent 使用的终端执行：

```sh
"$WIFI_PYTHON" -B tools/wifi.py request --session private/install-01 '{"action":"inspect"}'
```

`inspect` 会将完整目标库、两份 Backup 文件保存到私密会话目录，使用独立文件名避免覆盖，并返回三个属性值、挂载信息及快照编号。文件读取和终端操作共用同一个认证连接。认证本身可能更新 Sony 服务记账文件。

原厂目标库长度必须为 **17,694,160 字节**，SHA-256 为：

```text
5ad8746a229da259fe00b297e8f897d682f7ae9a13393025b3d1c95a808e68d7
```

将返回的原始属性值、型号、机内版本、确认的地区、备份位置及文件哈希记入私密安装记录。文件已经是补丁版时，先检查是否已完成安装，不重复运行 `patch`。

## 4. 执行已确认的最小修改

Wi-Fi 操作先检查 `/usr` 的挂载来源及整文件哈希，再把小程序传到 `/tmp` 并逐字节核对；随后临时改为可写挂载，原位修改一个字节，导出完整结果，检查哈希和唯一差异，最后恢复只读挂载并删除临时程序。

```sh
"$WIFI_PYTHON" -B tools/wifi.py request --session private/install-01 '{"action":"patch"}'
```

要求返回 `only_difference: 0xd778e4`，补丁后 SHA-256 为：

```text
14f42cc09ee1b9ddde5352482c13b68e5a5e97d9d79e8456087b5e0b7af6ff6a
```

再逐项写入 Backup 属性。**下例仅适用于检查到原值为 `00/09/09` 的情况；必须把 `expected` 换成本机实际保存的原值。** 所有值字符串均为十六进制。

```sh
"$WIFI_PYTHON" -B tools/wifi.py request --session private/install-01 '{"action":"backup-write","id":"0x01071C54","expected":"00","value":"01"}'
"$WIFI_PYTHON" -B tools/wifi.py request --session private/install-01 '{"action":"backup-write","id":"0x00A5000B","expected":"09","value":"02"}'
"$WIFI_PYTHON" -B tools/wifi.py request --session private/install-01 '{"action":"backup-write","id":"0x00A5000C","expected":"09","value":"16"}'
```

每条命令后检查 `match: true`。Wi-Fi 操作限制可修改的三个属性和值，再调用 toolkit 通用 Backup 接口：先保存原值，写入后调用 Sony 保存方法并立即读回。已经正确的属性可以跳过，不直接编辑 BK4 文件。若仅部分步骤成功，应保留每一步结果，按实际变化恢复。

结构化 Wi-Fi 或 Backup 操作报错会结束服务端。不要直接重发、重启或继续写入；先检查快照、状态和恢复说明。响应丢失不代表相机没有变化。恢复只读挂载失败时，必须先处理挂载状态，再考虑冷启动。

## 5. 验收并结束会话

再次执行 `inspect`，确认完整补丁哈希、属性 `01/02/16` 和 `/usr` 只读。私密保留修改前后文件，然后执行：

```sh
"$WIFI_PYTHON" -B tools/wifi.py request --session private/install-01 '{"action":"close"}'
```

等待服务端退出，确认 state.json 中 `state: closed`、`terminal_closed: true`、`service_returned: true`。收到 close 响应时，终端清理可能尚未结束，不能只看这一条响应。

相机 OFF，等待存取指示灯熄灭，拔掉 USB 并取下电池约 30 秒。重新装入后，在 `private/verify-01` 建立新的**只读**会话，等待 `ready` 再检查。保持会话打开，请机主进入“网络 → Wi-Fi 设置 → 频带”，检查 2.4/5 GHz 选择页。

**暖启动检查：**取电池约 30 秒仍可能从相机保存的 Warm Boot Image 恢复旧菜单状态。2026-11-07 实机曾在补丁和三个属性都正确时，运行中的 Wi-Fi 页仍是 TypeRK 四项；内核日志有 `PM: Low-level resume complete`。在验收会话中查看启动日志，并核对当前 Page1 是否为 TypeNB 五项。若仍为 TypeRK 四项或缺少「频带」，停止验收，保留日志与快照；不要重刷同一字节、重复写 Backup 或把取电池当作已经完成真正冷启动。该机经先备份完整 60 MiB `nflasha5`、再用 Sony 原厂工具仅清除其首 512 B 暖镜像入口、断电重启后，日志无暖恢复标志，Page1 和屏幕均恢复五项。此操作尚未集成到公开安装器，也不随仓库分发 Sony 工具；需要单独按已验证的备份、校验和恢复流程处理。

在新建且处于 `ready` 状态的只读会话中执行：

```sh
"$WIFI_PYTHON" -B tools/wifi.py request --session private/verify-01 '{"action":"boot-check"}'
```

要求返回 `page1.type: TypeNB`、`page1.count: 5`，没有暖恢复标志，并由机主确认原生频带页能打开。`boot-check` 读取全局 Page1 对象；最终仍以相机屏幕验证。若补丁及属性正确但返回 TypeRK/4，请在 Agent 协助下按[暖镜像恢复流程](wbi.zh-CN.md)处理。公开工具不会运行 Sony 专有程序或写入 `nflasha5`。

需要功能检查或活动无线状态采样时，按[验收与恢复](recovery.zh-CN.md)执行。完成后正常关闭验收会话，所有个人备份均不得混入公开发布包。
