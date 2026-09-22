# 平台与启动

## 0.2 安装包（普通用户）

优先使用发行页 Windows / Mac 安装包，按 README 双击安装。下面的 Python/CLI 流程供开发者手动管理。
安装版会注册 `Proxy2VPN`（Windows 当前用户 Run）或 `local.proxy2vpn.console`（Mac LaunchAgent）。
可在网页关闭登录自启；Windows 注册项仅在登录时启动，Mac 由 launchd 管理。
Mac 没有 Homebrew/CLT 时仍需响应系统提示；本版本没有签名公证的 Mac App。

配置保存在 `~/.proxy2vpn`；Windows 程序默认位于 `%LOCALAPPDATA%/Proxy2VPN`，Mac 位于
`~/Library/Application Support/Proxy2VPN`。网站只监听 `127.0.0.1:18990`。

## Windows

安装 Python 3.11+、QEMU，按 README 安装项目依赖并构建 x86_64 镜像。
`scripts/windows/Start.bat` 首次运行会启动配置向导，之后后台启动服务。
Stop / Status 分别停止与检查。脚本优先使用项目 `.venv`，否则使用 PATH 中的 Python。

QEMU 未在 PATH 时，编辑用户目录 `.proxy2vpn/config.json` 的 `qemu` 字段为程序绝对路径。
Windows Hypervisor Platform 可提供 WHPX 加速；工具不会自动修改 Windows 功能，无法使用
时回退 TCG。不要为了本工具关闭系统安全功能。

需要登录自启时，可以将 Start.bat 的快捷方式放入 Windows 当前用户的“启动”文件夹
（运行 `shell:startup`）。撤销时只移除该快捷方式。它是登录后自启，不是开机前系统服务。

## macOS

安装 Python 和 QEMU，例如 `brew install python qemu`，然后按照 README 创建 `.venv`。
Apple Silicon 使用 aarch64 资产；Intel 使用 x86_64。脚本通过本机 CPU 选择架构。

```sh
chmod +x scripts/macos/*.command
```

双击 Start.command、Stop.command、Status.command。初次运行会询问电脑与路由器地址。
QEMU 优先使用 HVF。真正的 Mac 网络、HVF、合盖/休眠恢复仍需真机验收。

若需要后台登录自启，可使用 `scripts/install_launch_agent.py --assets <镜像目录>`。
它只写入当前用户的 `~/Library/LaunchAgents/local.proxy2vpn.plist`，使用当前 Python 路径和
当前配置目录，随后打印需要执行的 `launchctl bootstrap` 命令，不替用户加载。
如果已经用 `up` 启动，应先 `down`，再加载 LaunchAgent，避免重复实例。

停止登录服务时先 `launchctl bootout gui/$(id -u) ~/Library/LaunchAgents/local.proxy2vpn.plist`，
然后删除这个特定 plist。不要在 KeepAlive 的 LaunchAgent 仍加载时仅使用 `down`，否则
launchd 会重新启动服务。

## 故障定位

| 现象 | 检查 |
| --- | --- |
| L2TP 无法连接 | 本机 IP、端口占用、来源白名单、防火墙 UDP 规则、Wi-Fi 客户端隔离、路由器是否支持 plain L2TP |
| 可以连接但打不开网页 | `doctor --network`、PPP 认证、代理是否开启、路由器有没有把代理电脑也分流进 VPN |
| HTTPS 可用但游戏不行 | 是否 HTTP 模式、SOCKS5 UDP ASSOCIATE、上游 UDP 回报的地址是否能被虚拟机访问 |
| TCP 正常但 DNS 异常 | VPN 客户端是否使用分配的 DNS、路由器强制 DNS、上游是否允许 TCP 53 |
| Wi-Fi 显示网络受限 | 单独验证网页、商店和连通性探测；标签本身不能证明整条网络不可用 |
| 休眠/代理重启后断线 | 恢复代理与服务，确认 `l2tp_ready`，必要时让路由器重新拨号 |

默认日志在 `~/.proxy2vpn/service.log`、`guest.log`、`launcher.log`。日志可能含访问目标，
报告问题前自行脱敏。长时间使用请注意 `guest.log` 的大小；当前版本未做完整轮转。
