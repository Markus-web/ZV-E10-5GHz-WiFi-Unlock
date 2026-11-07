# 暖启动镜像恢复

**简体中文** | [English](wbi.md)

仅用于 **ZV-E10 第一代、系统 2.02**：单字节补丁与 Backup `01/02/16` 已正确，但运行时 Page1 仍为 TypeRK 四项，且原生频带菜单缺失。不要重复写补丁或属性。旧暖启动镜像（WBI）会保留旧页面，取电池 30 秒不能保证真正冷启动。

2026-11-07 的 **2.02** 记录包含完整双备份、Sony 工具输出 `[UD_WBI_DROP] /dev/nflasha5 wbi_drop`，以及完整回读确认只有首 512 字节清零。断电重启后，全局及屏幕当前 Page1 均变为 TypeNB 五项，机主确认原生菜单、5 GHz 手机传图及路由器远程操作成功。**本次新增主机集成仅经过离线测试**，拒绝系统 2.03。

## 1. 离线准备 Sony 原厂工具

实测 6,200 字节的 `ud_wbi_drop.elf` 来自 **Sony ZV-E10 2.03 官方更新包**，实际执行时相机系统是 **2.02**。工具来源版本与相机系统版本是两回事，不要升级相机。Sony ELF 和完整固件是专有文件，本仓库不分发。

用户自行从 Sony 支持网站取得 ZV-E10 2.03 官方更新包，私密记录下载地址及包哈希，**不要运行升级器**。使用研究记录中的 [fwtool.py](https://github.com/ma1co/fwtool.py)，固定提交 `cdba742b73eed5981480c326aeb30033aabf0223`，按其要求在虚拟环境准备依赖。输入 Windows EXE 更新包或其中提取的 FirmwareData DAT：

```sh
git clone https://github.com/ma1co/fwtool.py.git vendor/fwtool
git -C vendor/fwtool checkout --detach cdba742b73eed5981480c326aeb30033aabf0223
"$WIFI_PYTHON" -B vendor/fwtool/fwtool.py unpack -f /path/to/official-ZV-E10-2.03-updater.exe -o private/sony-unpacked
"$WIFI_PYTHON" -B tools/prepare_sony_wbi.py --from-tree private/sony-unpacked --out private/sony-wbi/ud_wbi_drop.elf
```

离线筛选脚本只接受长度 6200、SHA-256 为 `f2a5b27a0c11d55a612d61e61e82c55278efb744052ecb8ec2cbbd8851d0ea6e` 的文件，不执行提取内容。解包失败或没有精确匹配时停止，不能替换为“类似”工具。本地研究的源更新包已在本轮之前清理，因此本次没有重新执行解包。实际使用前还会再次核对工具。

主机生成成功操作中使用的固定五行分区配置，SHA-256 为 `9bb1cba13c10ce88bd88d054dc49a823b3b1409ce6dfbeaeaa180f31d22744a8`。唯一 WBI 条目的起点为 `0x05800000`，长度 `0x03C00000`，类型 2。没有任意分区或路径覆盖选项。

## 2. 准备并审阅完整双备份

按[安装说明](install.zh-CN.md)建立唯一持久会话 `private/wbi-01`；若稍后要执行，启动时带 `--owner-authorized-write`。等待 `ready`，确认物理机型、屏幕系统版本 **2.02**、稳定供电和实际缺失的菜单，先执行 `inspect`、`boot-check`。主机至少留 400 MiB 空间；写入前保留本机完整 eMMC 备份，并核实 toolkit fastboot 恢复途径及所需硬件可用。

```sh
"$WIFI_PYTHON" -B tools/wifi.py request --session private/wbi-01 '{"action":"wbi-prepare","model":"ZV-E10","displayed_firmware":"2.02","sony_tool":"private/sony-wbi/ud_wbi_drop.elf"}'
```

`wbi-prepare` 不写相机。它自动两读 `/version.txt`，严格要求 `30110_05.2025031501`，并检查 ZV-E10 2.02 的 `libObj.so` 指纹、完整补丁版 `CautionConfig.so` 哈希及三个属性。机型识别采用已知系统文件指纹与机主屏幕确认，不另行查询 USB 产品名称。2.03 的 `30110_06.2026060501` 及其不同的 `libObj.so` 均被拒绝。

工具核对 `/proc/partitions`、sysfs 主次设备号/起点/长度、块设备节点身份及非符号链接，严格要求 `nflasha5`、**61,440 KiB / 62,914,560 字节**、起始扇区 **180224**、长度 **122880 扇区**。若内核没有所需 sysfs 信息，停止，不要绕过保护；这些新增识别检查仍待实机验证。

通过 FileControl READ 将完整分区流式读取两次，主机独占创建私密文件并 fsync，核对完整长度、主机哈希和逐字节相等。首部必须是 `WBI1`。若首 512 字节已经全零，返回 `already-invalid`，禁止重复写入；未知首部立即停止。结果、原始文件及失败时的部分读数保留在会话目录，不覆盖旧证据。返回的 `token`、双哈希、eMMC 风险提示和 `confirmation` 字符串必须先审阅。

## 3. 取得明确 eMMC 写入确认，再执行一次

向机主说明：**本操作写入内部 eMMC，只使本机 WBI 首 512 字节失效；断电或 USB 故障可能导致失败，不自动恢复。** 审阅双备份后取得本次操作的明确授权，核实恢复途径确实可用，不能把“有备份”当成已具备恢复能力。机主未同意时不得代填确认。

将 `PREPARED_TOKEN`、`BACKUP_SHA256` 换成返回的精确值，使用同一会话和工具路径：

```sh
"$WIFI_PYTHON" -B tools/wifi.py request --session private/wbi-01 '{"action":"wbi-drop","prepared":"PREPARED_TOKEN","sony_tool":"private/sony-wbi/ud_wbi_drop.elf","confirm_emmc_write":"INVALIDATE WBI BACKUP_SHA256","recovery_ready":true}'
```

工具重新核对系统、文件指纹、属性、设备身份、保存的双备份，并新读完整分区与准备阶段比较。执行前先消耗令牌，防止盲目重试。Sony 原厂程序与生成的配置通过 Jiritsu SET_FILE2 上传，并用 **GET_FILE 完整读回，在主机逐字节比较**。不依赖相机 BusyBox 哈希或十六进制转储。

只执行一次 Sony 工具。即使命令报错，也尝试完整读回分区。成功必须满足原厂预期输出、退出码 0、首 512 字节全零、**其余 62,914,048 字节完全不变**。任何异常立即停止服务端并保存诊断。清理固定临时文件；USB 故障可能使清理失败。工具不提供通用块设备写入，也不自动回刷旧 WBI。

## 4. 真正冷启动、验收与恢复

正常关闭，确认 `terminal_closed=true`、`service_returned=true`。拔 USB、OFF 等访问灯熄灭、取电池约 30 秒再开机。在**新建且 ready 的只读会话**运行 `inspect`、`boot-check`，要求补丁/属性不变、无暖恢复标志、TypeNB 五项，并由机主确认原生频带菜单能进入。菜单操作期间保持会话打开，热点传图和路由器远程操作分别验证。

任何写入或回读异常都应停止，保留完整私密会话：`wbi-*-read1.bin`、`read2.bin`、`prewrite.bin`、`after.bin`、结果 JSON、已消耗令牌标记及 toolkit 响应和状态。超时不代表未写入。不要盲目重试，也不要在差异未查明时自动断电。按[恢复说明](recovery.zh-CN.md)交由具备能力的人复核；必要时可通过 toolkit fastboot，使用**本机原始 60 MiB 镜像及已确认的分区表**恢复，再完整回读比较。不能使用其他相机的 WBI，也不要仅为撤销成功失效而回刷旧镜像，它可能再次引入旧运行状态。本版本未实测 WBI 回刷恢复；失效旧镜像不会永久禁用正常暖启动。
