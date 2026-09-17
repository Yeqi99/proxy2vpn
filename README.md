# Proxy2VPN

[English](README.en.md)

把 Windows / macOS 电脑上的现有代理，变成家用路由器可以连接的 **L2TP 服务**。

```
Quest / 电视 / 游戏机 → 家用 Wi-Fi 路由器 → Proxy2VPN → 已有 HTTP / SOCKS5 代理 → Internet
```

电脑可以通过 Wi-Fi 联网，无需桥接网卡、额外网线或刷路由器。路由器必须支持 **不带 IPsec 的 L2TP 客户端**，最好支持按设备分流。工具不提供节点、订阅或免费网络服务，也不会读取你的 Clash / BitzNet 配置。

**0.1.0 是早期版本。** Windows 原型已完成小米 BE7200 Pro 实际连接。通用版和 macOS 的验证情况见 [验证记录](docs/validation.md)，不能把原型结果视为所有平台、路由器或游戏都已验证。

## 能力与边界

| 项目 | 当前支持 |
| --- | --- |
| 路由器入口 | L2TP / PPP / CHAP，IPv4，UDP 1701 |
| SOCKS5 上游 | TCP；上游支持 UDP ASSOCIATE 时可转发 UDP |
| HTTP CONNECT 上游 | TCP；DNS 通过上游 TCP 查询；一般 UDP 不支持 |
| Windows x64 | QEMU WHPX，失败回退 TCG |
| Apple Silicon Mac | ARM64 镜像，QEMU HVF，失败回退 TCG；真机待验证 |
| Intel Mac | x86_64 镜像，QEMU HVF；真机待验证 |
| PPTP / IPsec / WireGuard 入口 | 不支持 |
| IPv6 | 不通过本工具转发；需要在目标设备/路由器另行处理 |

L2TP 本身不加密，**只用于可信家庭内网，不要把 UDP 1701 暴露到公网**。来源 IP 白名单不是加密认证的替代品。项目不自动开放防火墙、不改宿主机默认路由、不代替路由器设置分流。

## 安装

需要 Python 3.11+、[QEMU](https://www.qemu.org/download/) 和已有代理。Docker **只在构建镜像时需要**，运行服务不依赖 Docker。

macOS：先安装 Python 和 QEMU（例如 `brew install python qemu`）。Windows：安装 Python 与 QEMU，将 QEMU 加入 PATH，或初始化时使用 `--qemu` 指定程序路径。

在源码目录执行：

```sh
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS: source .venv/bin/activate
python -m pip install -e .
```

构建无私人数据的运行镜像（需要已运行的 Docker Desktop）：

```sh
# Windows x64 / Intel Mac
python scripts/build_guest.py --arch x86_64
# Apple Silicon Mac
python scripts/build_guest.py --arch aarch64
```

首次构建会从 Alpine 和 Mihomo 官方源下载依赖。Mihomo 版本及 SHA-256 固定在 `guest/versions.json`。Alpine 软件包会随官方安全更新变化；`packages.txt` 记录本次实际版本，并非字节级可重复构建。

## 配置与运行

下面的地址是示例，请替换为自己家的电脑、路由器和代理端口。

```sh
proxy2vpn init --listen-ip 192.168.50.10 --router-ip 192.168.50.1 --proxy-host 192.168.50.10 --proxy-port 7890
proxy2vpn up --assets artifacts/x86_64
proxy2vpn status
proxy2vpn doctor --assets artifacts/x86_64 --network
proxy2vpn router
```

Apple Silicon 把资产路径换为 `artifacts/aarch64`。`up` 在后台启动；启动成功不代表镜像已经完成引导，稍后 `status` 应显示 `l2tp_ready: true`。`doctor --network` 会通过代理访问 gstatic 做 HTTPS 连通性检测。

初始化也可以直接运行 `proxy2vpn init`，按提示填写 IP。HTTP 代理加 `--proxy-type http`；代理需要账号密码时加 `--proxy-auth`，密码通过隐藏输入获取。L2TP 密码自动随机生成，`router` 命令只在本地显示。

默认配置、密码及日志位于用户目录 `~/.proxy2vpn`。可以编辑 `config.json`，修改后先 `down` 再 `up`。自定义状态目录时，每个命令都在子命令前加 `--home 路径`。

已有代理最好通过**电脑的内网 IP**访问，尤其是 SOCKS5 UDP。部分代理通过 `127.0.0.1` 访问时会返回不可供虚拟机使用的 UDP 地址。使用内网 IP 时，需在原代理应用开启相应 LAN 监听，并将其访问范围限制在可信内网。工具不会自动修改代理应用。

## 路由器设置

1. 为运行工具的电脑设置固定 DHCP 地址。
2. 在 VPN 客户端中添加 L2TP，填入 `proxy2vpn router` 显示的服务器、用户名和密码。
3. 选择按设备分流，只加入需要使用代理的设备。**不要把运行代理的电脑也分流进该 VPN**，否则可能形成循环。
4. 连接 VPN，验证目标设备的网页、商店、游戏。需要无人值守时，再配置路由器自动连接。

若防火墙拦截，只放行路由器 IP 到本机 UDP 1701；不要关闭整个防火墙。Wi-Fi 客户端隔离、访客网络隔离会阻止电脑与路由器之间的连接。路由器对 LAN 侧 L2TP 服务器的支持也存在差异。

## 日常操作

```sh
proxy2vpn status
proxy2vpn down
proxy2vpn up --assets artifacts/x86_64
```

运行时请求系统保持唤醒，屏幕仍可关闭；关机、手动睡眠、合盖或退出代理会影响网络。停止工具前可以先断开路由器 VPN。按设备分流在 VPN 断开后的行为取决于路由器，**工具不承诺断网保护**。

双击入口见 `scripts/windows/` 和 `scripts/macos/`；登录自启配置示例及删除方法见 [平台说明](docs/platforms.md)。本版本不自动安装系统服务。

## 开发

```sh
python -m unittest discover -s tests -v
```

见 [架构](docs/architecture.md)、[贡献说明](CONTRIBUTING.md)、[安全说明](SECURITY.md) 和 [第三方组件](THIRD_PARTY_NOTICES.md)。源代码采用 MIT；依赖组件保持各自许可证。本仓库不收录用户凭据、订阅、私人磁盘或个人运行日志。
