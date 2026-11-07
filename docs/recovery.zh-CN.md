# 验收与恢复

**简体中文** | [English](recovery.md)

## 安装验收

安装记录分别保存以下结果：

1. 完整目标库哈希、长度及唯一字节差异；三个 Backup 属性写后立即读回。
2. `/usr` 恢复只读，临时程序已删除，服务会话正常关闭。
3. 拔 USB、取电池后，在**新会话**中再次读到完整补丁哈希及 `01/02/16`；执行 `boot-check`，要求 TypeNB 五项且没有暖恢复标志。单靠取电池不能证明真正冷启动。
4. 机主可以进入原生频带菜单。菜单出现与 5 GHz 无线实际工作分别记录。
5. 如需功能测试，先验证 5 GHz 相机热点传图，再分别检查路由器连接和远程拍摄，记录结果及活动信道。未做受控测速时不填写速度提升数据。

若补丁和属性正确但 Page1 仍为 TypeRK 四项，停止重复写入，按[Agent 辅助暖镜像流程](wbi.zh-CN.md)处理。完整 `nflasha5` 备份须私密保存；如恢复计划需要回刷，只能使用同一机身的镜像。使旧 WBI 失效不会永久关闭正常暖启动机制。

请机主操作菜单前保持会话为 `ready`。Wi-Fi 正在工作时，可提交如下只读查询：

```sh
"$WIFI_PYTHON" -B tools/wifi.py request --session private/verify-01 '{"action":"shell","command":"/usr/bin/wl -i wlan0 country"}'
"$WIFI_PYTHON" -B tools/wifi.py request --session private/verify-01 '{"action":"shell","command":"/usr/bin/wl -i wlan0 status"}'
```

还可查询 `channels`、`chanspecs`。退出 Wi-Fi 后接口常会消失，此时查询失败不能用来判断地区配置。输出可能包含设备标识，应私密保存。历史中国大陆实验中，热点 GO 读到 XR/76，路由器 STA 读到 XR/143；实际选择信道随环境变化。驱动列出的信道不是合规测试结果。

## 通过 USB-C 正常恢复

核对型号、机内版本、当前目标库及私密安装记录，确认恢复操作范围。新建带 `--owner-authorized-write` 的持久会话，先 `inspect`。恢复程序只接受完整、已知哈希的补丁文件，拒绝未知或截短文件。

```sh
"$WIFI_PYTHON" -B tools/wifi.py request --session private/restore-01 '{"action":"restore"}'
```

恢复后要求原厂 SHA-256 为 `5ad8746a229da259fe00b297e8f897d682f7ae9a13393025b3d1c95a808e68d7`、长度 17,694,160 字节、唯一差异位于 `0xD778E4`，且 `/usr` 只读。

逐项恢复 Backup 属性：`expected` 使用**刚检查到的当前值**，`value` 使用**本机安装前保存的原值**。历史实验相机的恢复示例如下，不代表其他相机的默认值：

```sh
"$WIFI_PYTHON" -B tools/wifi.py request --session private/restore-01 '{"action":"backup-write","id":"0x01071C54","expected":"01","value":"00"}'
"$WIFI_PYTHON" -B tools/wifi.py request --session private/restore-01 '{"action":"backup-write","id":"0x00A5000B","expected":"02","value":"09"}'
"$WIFI_PYTHON" -B tools/wifi.py request --session private/restore-01 '{"action":"backup-write","id":"0x00A5000C","expected":"16","value":"09"}'
```

不要整库恢复旧 Backup，以免覆盖正常用户设置；不要改变无关的无线电源模式或机型字段。原值超出本工具支持范围时停止检查，不绕过限制。已经恢复的属性或文件，检查后可跳过。

再次检查，正常关闭会话并确认清理完成，按安装说明冷启动。建立新的只读会话，核对原厂哈希、原始属性和相机行为。反向单字节程序已通过离线检查，完整恢复集成尚未经过实机验证。

## 安装失败或中断

超时或读回不符时停止，重新连接前先检查状态及修改前后证据。命令即使没有返回，也可能已经生效。重新建立唯一服务会话后，先检查再决定继续或恢复。服务退出后相机从 USB 消失，可先重新插线；只有确认系统文件完整后才考虑断电重启。

**已知库文件被截短时，不要重启相机。** 不要用 `cp` 覆盖正在加载的目标库：历史实验曾因空间不足而截短文件。机内 BusyBox 的 `dd` 缺少可用的 `conv=notrunc`，不能用来写此补丁。整文件替换与保留长度的单字节写入不是同一操作。

若写入成功但无法恢复只读挂载，保存前后哈希，停止其他操作并先处理恢复问题，不报告安装完成。USB 或文件系统故障下，工具不会保证自动回滚。

## 相机无法启动

USB-C 服务终端需要相机正常启动到相应服务。严重文件系统损坏可能需要额外硬件，通过 BootROM 注入和 fastboot 恢复，参考 [zv-e10-toolkit](https://github.com/dino2048/zv-e10-toolkit) 当前文档及硬件要求。本项目不附带硬件恢复 payload 或个人分区镜像。

必须使用同一相机的已校验原始备份，核对分区表及长度，恢复后整分区回读比较。不要写入其他相机的 Backup、校准或密钥，不要将 `0xD778E4` 当成分区偏移。恢复旧分区可能重新带回旧实验文件或覆盖之后的变更。备份和 fastboot 不保证所有故障都能恢复。

## WBI 失败证据

实际命令见[暖镜像恢复](wbi.zh-CN.md)。保留完整双备份、写前/写后读数及 JSON 诊断；不自动回刷旧 WBI。令牌已消耗或命令超时必须先复核，不能直接重试。如确需恢复，只能通过已确认的 fastboot 恢复途径使用本机原始镜像，并完整回读比较。本版本未实测 WBI 回刷恢复。
