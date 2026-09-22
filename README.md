# Proxy2VPN

[English](README.en.md) · [下载安装包](https://github.com/Yeqi99/proxy2vpn/releases/tag/v0.2.2)

**把家里电脑上的代理，变成路由器和浏览器都能使用的接入口。**

下载对应系统的安装包，解压后双击安装。安装器会准备运行环境、启动本地网页控制台，并设置当前用户登录后自启。无需自行安装 Python、Docker 或手动构建镜像。首次安装需要联网下载依赖。

## 一条指令安装

Windows x64：打开 **PowerShell**，复制执行：

```powershell
& ([scriptblock]::Create((irm 'https://raw.githubusercontent.com/Yeqi99/proxy2vpn/v0.2.2/install.ps1')))
```

Mac：打开 **终端**，复制执行（自动识别 Apple Silicon / Intel）：

```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Yeqi99/proxy2vpn/v0.2.2/install.sh)"
```

自动下载并校验安装包、部署依赖、创建快捷方式，完成后直接打开本地 UI。首次安装默认登录自启，已有安装保留用户选择。第一次仍需在网页填写自己的代理地址。

安装过程需要访问 GitHub、Python 软件源和平台依赖源。Mac 首次安装 Homebrew / Command Line Tools 可能要求密码或系统确认；Mac 真机仍待验证。无需手动安装 Docker。

## 下载后安装

1. Windows x64：解压 `proxy2vpn-0.2.2-windows-x64.zip`，双击 `Install-Windows.cmd`。Apple Silicon Mac 使用 `macos-arm64.zip`，Intel Mac 使用 `macos-intel.zip`，打开其中 `Install-Mac.command`。
2. 自动打开的控制台位于 `http://127.0.0.1:18990/`。填写电脑内网 IP、路由器 IP、已有 HTTP/SOCKS5 代理地址和端口，选择接入口，点击「保存并启动」。
3. 按网页教程配置路由器或浏览器。路由器按设备分流时，排除运行代理的电脑，避免循环。

关闭网页后继续后台运行。转发进程异常退出会尝试重新启动。「停止」会记住停止状态，登录自启不会擅自恢复被你停止的转发。电脑和原代理应用仍需保持运行。

## 接入协议

| 接入口 | 场景 | 限制 |
| --- | --- | --- |
| L2TP | 小米等支持 plain L2TP 的原厂路由器，默认 UDP 1701 | 不带 IPsec，只用于可信内网 |
| WireGuard | 支持 WireGuard 的路由器，默认 UDP 51820 | 加密接入；网页下载一份客户端配置，不应多设备同时复用 |
| HTTP | 浏览器/系统代理，默认 TCP 18080 | 需要生成的账号密码，支持 CONNECT |
| SOCKS5 | 支持 SOCKS 的应用，默认 TCP 11080 | 需要账号密码；此接入口仅 TCP |

可以同时开启多个入口。上游 SOCKS5 必须支持 UDP ASSOCIATE 才能转发 VPN 的 UDP；普通 HTTP 上游只支持 TCP，DNS 通过 TCP 上游查询。工具不提供节点、订阅或断网保护，也不代理 IPv6。

VPN 接入限制来自配置的路由器 IP 和本机诊断地址；HTTP/SOCKS 接受局域网连接并要求认证。**不要将端口映射到公网。** IP 白名单不等于加密。

## 安装与平台边界

Windows 下载官方 Python 嵌入式运行时、QEMU，安装到用户目录；7-Zip 仅用于解压。不修改系统默认路由、原代理或已有 Python。控制台只监听本机；Windows 自动创建桌面和开始菜单快捷方式；Mac 自动创建桌面 Proxy2VPN.command 入口。后台未运行时，快捷方式会先启动控制台再打开网页。

Mac 通过 Homebrew 准备 Python/QEMU，创建独立环境。**首次安装 Homebrew 或 Command Line Tools 时，macOS 可能要求密码或系统确认**；脚本不会绕过 Gatekeeper。自动启动指当前用户登录自启，不是无人登录的系统服务。

**Windows x64 和四种协议已本机验证；ARM64 核心可模拟运行。Mac 安装/HVF/睡眠恢复尚未真机验收，不承诺所有 Mac 上零交互。** 详见 [验证记录](docs/validation.md)。

## 控制台与日常使用

- 首次安装默认开启登录自启。管理页顶部可随时切换，立即保存并显示结果；升级和重装会保留关闭选择。关闭自启不停止当前会话，也不影响通过快捷方式手动启动。
- 网页可设置上游地址、端口、账号、接入协议与端口；启停、测试已保存代理、修改登录自启、显示账号、下载 WireGuard 配置。
- `~/.proxy2vpn` 保存私人设置，默认限制当前用户访问。状态接口不返回密码或私钥。页面使用本机密钥和 Host/Origin 检查。
- 首次安装自动登录。直接访问 URL 时按提示输入 `console.token`；Windows 使用桌面或开始菜单的 `Proxy2VPN` 快捷方式，Mac 使用桌面的 `Proxy2VPN.command`。
- 测试按钮仅验证上游 HTTPS；L2TP 就绪只说明控制握手。目标设备的游戏、商店与速度应实际验证。
- 需要防火墙放行时只允许目标来源和端口；不要关闭整个防火墙。SOCKS5 UDP 建议填写内网 IP，且原代理允许所需 LAN 访问。

停用时先点击「停止」并取消自启，再从路由器断开 VPN。关闭本项目控制台进程后可删除程序目录。需要保留凭据就保留 `~/.proxy2vpn`；Mac 的 Homebrew 依赖不自动卸载，避免影响其他软件。

## 开发

```sh
python -m venv .venv
# 激活虚拟环境
python -m pip install -e .
python -m unittest discover -s tests -v
python scripts/build_guest.py --arch x86_64
python scripts/build_guest.py --arch aarch64
```

只有开发构建需要 Docker。原 CLI 保留；`proxy2vpn console --assets artifacts/x86_64` 启动控制台。见 [架构](docs/architecture.md)、[贡献](CONTRIBUTING.md)、[安全](SECURITY.md) 与 [第三方许可证](THIRD_PARTY_NOTICES.md)。原创代码 MIT，第三方组件保持各自许可；发行页提供预构建镜像的对应源码和构建配方。
