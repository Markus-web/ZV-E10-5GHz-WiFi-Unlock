# 许可与验证范围

**简体中文** | [English](release.md)

## 许可边界

- 本项目原创代码、辅助程序汇编及文档采用 MIT，见 [LICENSE](../LICENSE)。
- 服务端、客户端、请求队列、认证及通用 Backup 操作由外部 [zv-e10-toolkit](https://github.com/dino2048/zv-e10-toolkit) 提供。本仓库只保留 Wi-Fi 专用规则及补丁操作，没有复制 toolkit 的通用实现；保留 [toolkit MIT 声明](../licenses/zv-e10-toolkit-MIT.txt)用于署名。
- Sony-PMCA-RE 为外部运行依赖，未随仓库打包；保留其 [MIT 声明](../licenses/Sony-PMCA-RE-MIT.txt)。下载依赖各自保留原许可证，重新分发环境时应保留相关声明。本项目不分发 Python 环境、libusb、clang 或 GNU binutils。
- OpenWrt `bcmclm.c` 为 GPL-2.0-or-later，仅作技术文档中的研究参考，本仓库未复制其实现。
- `patch.arm`、`restore.arm` 是自有的小型 ARM Linux 程序，不是 Sony 固件，均附汇编源码。
- Sony 完整固件、专有库、驱动、NVRAM／校准数据、个人备份、设备密钥和凭据未包含在仓库中，也不属于本项目许可范围。公开哈希及偏移不授予再分发 Sony 代码的权利。Sony 及产品名称归相应权利人。

## 验证范围

- **已有实机验证**：一字节加三个属性的底层修改、原生菜单、5 GHz 热点传图、5 GHz 路由器远程拍摄及安装后冷启动保留，见[实测记录](evidence.zh-CN.md)。
- **已做离线验证**：Wi-Fi 集成工具的文件哈希、补丁前置检查、模拟读写及恢复流程；toolkit 的属性原值校验、私密快照、写后读回和正常／异常关闭。
- **尚未完整实机验证**：整理后的 Wi-Fi 主机集成及反向单字节恢复程序。离线通过不能替代实际 USB 及文件系统故障下的验证。

依赖固定为 toolkit 提交 `e8d4cb566fa04dac249e10431302e4d950550bde`；安装文档包含确切 checkout 命令。验证结果记录在 [offline-checks.json](offline-checks.json)，它是机器可读结果文件，不需要翻译字段名称。

## 不连接相机的自检

按[安装说明](install.zh-CN.md)准备环境并设置变量后，在本仓库执行：

```sh
"$WIFI_PYTHON" -B tools/check_offline.py
"$WIFI_PYTHON" -B -m unittest discover -s tools -p test_safety.py -v
"$WIFI_PYTHON" -B -m unittest discover -s "$ZVE10_TOOLKIT/linux/tests" -v
"$WIFI_PYTHON" -B "$ZVE10_TOOLKIT/linux/host/zve10_terminal_server.py" --self-test
```

这些检查不连接相机，也不要求个人固件文件。维护者可用 `check_offline.py` 的 `--factory`、`--patched`、`--tested-helper` 参数，对私密样本做额外比对；样本不应加入仓库。

## 分享文件时

不要把 `private/`、`vendor/`、虚拟环境或外部相机备份加入公开压缩包。`.gitignore` 只影响 Git 文件跟踪，不会自动排除任意方式打包的内容。私密快照可能含设备标识、凭据或密钥。

新增 SET_FILE2 上传、版本保护、WBI 执行保护和完整回读均经过离线模拟测试。2026-11-07 的底层成功操作运行在系统 **2.02**；不支持系统 2.03。Sony 原厂 ELF 的来源更新包为 2.03，不等于相机安装系统。新增 sysfs 身份检查、完整 USB 执行集成、回滚及真实断电/USB 故障行为仍待实机验证。
