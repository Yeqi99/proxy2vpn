# 验证记录

验证日期：2026-09-17。以下结果对应本仓库 0.1.0 通用版的本地测试，未声称所有设备兼容。

| 测试 | 结果 | 证据范围 |
| --- | --- | --- |
| Python 单元/网络测试 | 17 项通过 | 配置输入、注入防护、initramfs 编码、UDP 来源过滤、关闭后重连、平台命令 |
| x86_64 干净镜像构建 | 通过 | Docker 官方 Alpine 软件源，Mihomo 固定版本与哈希 |
| ARM64 干净镜像构建 | 通过 | 对应 ARM64 包与 Mihomo 官方 ARM64 二进制 |
| Windows x64 + WHPX + SOCKS5 | 通过 | 独立 QEMU 客户端经宿主机 LAN 入口，PPP 认证、HTTPS 204、Meta DNS、公共 DNS UDP |
| Windows x64 + WHPX + HTTP CONNECT | 通过 | 独立 QEMU 客户端 PPP、HTTPS 204、Meta DNS；不支持一般 UDP |
| ARM64 Linux 核心 | 通过 | Windows QEMU TCG 模拟 ARM64，独立 ARM64 客户端 PPP、HTTPS、DNS、UDP |
| macOS HVF 真机 | **未验证** | 已实现原生架构选择、HVF 命令及启动脚本，不能把 ARM64 模拟测试视为 Mac 真机测试 |
| 小米 BE7200 Pro 原厂 1.0.36 | 原型已连接 | 本项目来源原型使用相同 xl2tpd/pppd/Mihomo 转发链；通用版没有替换正在运行的家庭服务 |
| Quest 商店/具体游戏/长时间吞吐 | **未验证** | 流量与协议测试不代表头显用户体验验收 |
| Windows / Mac 整机重启、睡眠恢复 | **未验证** | 不承诺首次发布已经具备长期无人值守稳定性 |

集成客户端从原始镜像启动，实际经 Windows LAN UDP 端口发起 L2TP/PPP，不通过宿主机
直接 HTTP 代理冒充 VPN 测试。UDP 测试向外部 DNS 地址发包，区别于虚拟机 DNS 服务内部
使用 TCP 上游的检查。测试入口使用独立端口，不改用户路由器。

复现方法见 [CONTRIBUTING.md](../CONTRIBUTING.md)。私人测试状态与日志不纳入仓库。
CI 配置覆盖 Windows/macOS/Linux 的 Python 测试；首版云端任务未能启动，尚无云端通过证据。
本页已通过结果均为本地执行，后续 CI 运行结果以实际 Actions 为准。
