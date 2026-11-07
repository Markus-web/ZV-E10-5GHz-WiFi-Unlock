# 实测记录与来源

**简体中文** | [English](evidence.md)

本文汇总 ZV-E10 第一代、固件 2.02 的实机测试结果，以及相关技术资料来源。

## 实测环境与配置

- 相机：Sony ZV-E10 第一代，机内版本页显示 2.02。
- 主机：macOS；通过 USB-C 持久服务会话操作。
- 地区：中国大陆；B=2、C=22，对应 XR/76、XR/143。
- 修改：`CautionConfig.so` 的 `0xD778E4:20→1B`，及三个 Backup 属性。
- 记录日期：2026-11-05 至 2026-11-07。

## 实机结果

| 检查或实验 | 结果 | 验证范围 |
| --- | --- | --- |
| 2.02／2.03 文件对照 | 按 inode 提取的目标库与 2.03 样本相同；`libObj.so` 不同 | 不能由目标库相同推导整套版本兼容 |
| 原生频带菜单 | TypeNB 配合 Backup 菜单属性 `01`，可进入 2.4/5 GHz 选择页 | 原生菜单已实测；A7C 模板为静态对照 |
| Backup 属性写入 | 通过 Sony 服务接口保存原值，B/C 由 `09/09` 改为 `02/16` 后立即读回一致 | 菜单属性为 `01` |
| 2.4／5 GHz 相机热点 | 活动驱动读到 XR/76；2.4 GHz 信道 1，5 GHz 信道 157、80 MHz；手机传一张照片成功 | 未做传输速度基准测试 |
| 路由器连接及远程拍摄 | 活动驱动读到 XR/143；曾连接信道 6 和 40；经 5 GHz 路由器在信道 40、80 MHz 下远程拍摄并接收照片 | 专门的“发送到电脑”功能未测试 |
| 最小修改状态核查 | 目标库仅一字节不同，三个无线属性符合配置；已查其他库、驱动、固件及 81 份 NVRAM 匹配原厂对照 | 未对整个 eMMC 做逐分区来源审计；未重置无关用户设置 |
| USB-C 原位安装 | 从完整原厂库出发，辅助程序以不截断文件的方式写入 `20→1B`；完整导出后仅目标字节不同 | 普通安装无须 fastboot |
| 2026-11-07 暖镜像恢复 | 补丁和属性正确但暖恢复后仍为 TypeRK 四项；经备份并使旧 WBI 失效、真正冷启动后，全局和当前 Page1 均为 TypeNB 五项。机主确认菜单、5 GHz 手机传图及 5 GHz 路由器远程操作 | 完整 60 MiB 分区双备份，只有首 512 字节变化；本轮未新增信道及受控速度测试 |
| 安装后取电池重启 | 拔 USB、取电池后，文件长度及补丁仍保持，属性为 `01/02/16`，`/usr` 只读；机主确认菜单正常 | 仅取电池不能证明真正冷启动；此次未重复前述功能实验 |

热点、路由器功能与最终 USB-C 安装分别有实机记录；不能将它们合并描述为新版主机工具已完整实机验收。

## 原位写入与恢复经验

早期整文件 `cp` 尝试因空间不足，将目标库截短为 11,173,888 字节。相机当时仍在运行，但下次启动已存在风险。通过额外硬件进入 fastboot，从同一相机的原始备份恢复受损分区后，才继续验证 USB-C 单字节安装。

成功的 USB-C 安装保留了文件 inode 和完整长度。冷启动后目标库 MD5 为 `4823e8af6a38cece419636332e00b5a2`，服务会话正常关闭，`terminal_closed=true`、`service_returned=true`。因此安装流程采用原位单字节写入，禁止整文件复制和会截断文件的 BusyBox `dd` 写法。

## 可复核信息

完整原厂及补丁文件的长度、SHA-256、唯一差异见[技术说明](technical.zh-CN.md)。安装时会在机主电脑保存本机文件和属性快照，便于自行核对及恢复；快照包含相机数据，应私密保管。

地区表来自第一代 A7C 2.03 原厂 Backup 模板的静态分析。CLM 文件头及顶层范围已解析，逐 XR 修订的完整功率、DFS 等规则尚未可靠解码；中国大陆功能结论来自实机读数和操作结果。

## 资料来源

- [Sony A7C 频带设置](https://helpguide.sony.net/ilc/2020/v1/en/contents/TP1000156044.html)：原生菜单及直连功能适用范围。
- [Sony A7C 访问点设置](https://helpguide.sony.net/ilc/2020/v1/en/contents/TP1000115299.html)：连接路由器的操作。
- [Sony ZV-E10 PC Remote](https://helpguide.sony.net/ilc/2070/v1/en/contents/TP0002392805.html)：直连、访问点连接、配对、拍摄及保存方式。
- [Sony A7C 规格](https://helpguide.sony.net/ilc/2020/v1/en/contents/TP1000156734.html)：不同地区无线版本。
- [IFT Sony 设备清单](https://www.ift.org.mx/node/19562)：ZV-E10 Type1DR 条目。
- [NTC 2021 设备清单](https://region7.ntc.gov.ph/wp-content/uploads/2024/01/RCE_08312021.pdf)：A7C Type1DR 条目，印刷第 187 页。
- [Sony-PMCA-RE](https://github.com/ma1co/Sony-PMCA-RE)、[MIT 许可](https://github.com/ma1co/Sony-PMCA-RE/blob/master/LICENSE.txt)：服务协议实现；toolkit 固定版本为 `a82f5baaa8e9c3d9f28f94699e860fb2e48cc8e0`。
- [zv-e10-toolkit](https://github.com/dino2048/zv-e10-toolkit)：备份、持久服务及恢复工具。本项目使用提交 `e8d4cb566fa04dac249e10431302e4d950550bde`。
