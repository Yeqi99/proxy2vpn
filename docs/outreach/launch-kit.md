# 首轮宣传包

状态：文案草稿，尚未向社区发布。项目现为 v0.2.3 预览版。

## 建议先做什么

首轮目标：获得 5 份可复现的安装或兼容性反馈（这是目标，不是已有用户数）。优先找已经有本地代理、常开电脑和原厂路由器的人。先发一篇，回答问题，再根据实际反馈决定下一站。

1. V2EX「分享创造」：优先中文首发。该节点明确欢迎自己的作品。https://www.v2ex.com/go/create
2. 掘金：把下面的起因、架构与踩坑扩成技术文章；不要只重复安装链接。
3. Show HN：使用英文稿，链接可下载项目并准备回答实现与限制问题。官方要求作品可试用、作者愿意讨论，不要组织投票。https://news.ycombinator.com/showhn.html
4. Reddit：先确认具体社区的当日规则和账号条件；不直接批量投放。r/selfhosted 对自荐与内容相关性有要求，不能默认适合网络网关项目。

核对日期：2026-09-23。平台规则与登录资格可能变化，发布前以站内规则为准。

## 中文首发稿

标题：开源一个小工具：把电脑上的 HTTP/SOCKS5 代理转成路由器能用的 VPN

起因是家里的小米原厂路由器有 L2TP 客户端，但没法把已有代理的 IP 和端口直接填进去使用。我又想让 Quest 这类设备通过路由器接入，于是做了 Proxy2VPN。

它在常开的电脑上运行，把已有 HTTP/SOCKS5 代理接到一个本地网关，再给路由器提供 L2TP 或 WireGuard 入口，也支持认证 HTTP、SOCKS5 接入。路由器按设备分流时，排除运行代理的电脑，避免流量绕回自身。

现在有：

- Windows / Mac 一条指令安装，自动部署环境、创建快捷方式、打开管理网页。
- 中文 / English 控制台，配置代理、选择协议、测试连接。
- 默认登录自启，可以在网页关闭，升级保留选择。
- Windows 上已做实际协议转发和在线安装/升级测试。

也把边界说清楚：这是预览版。Mac 安装包和脚本已经提供，但还缺真实 Mac 验收；Quest 商店、具体游戏和长期速度没有完整验收。L2TP 不带 IPsec，只用于可信内网。工具不提供代理节点或订阅，电脑与原代理都要保持运行。

仓库：https://github.com/Yeqi99/proxy2vpn
安装包和一键命令：https://github.com/Yeqi99/proxy2vpn/releases/tag/v0.2.3

想找几位有 Apple Silicon Mac 或不同原厂路由器的朋友试试。如果遇到问题，欢迎在仓库提交系统、路由器型号/固件、接入协议和具体出错步骤。请别贴订阅、密码或私钥。

## 英文首发稿

Title: Show HN: Proxy2VPN – expose an existing proxy as a router-compatible VPN

I built Proxy2VPN after running into a mismatch at home: my stock Xiaomi router has an L2TP client, while the proxy on my computer exposes HTTP/SOCKS5. An IP address and proxy port cannot simply be entered as an L2TP server.

Proxy2VPN runs a small Linux guest through QEMU on an always-on computer. It connects an existing HTTP/SOCKS5 upstream to L2TP or WireGuard inbounds; authenticated HTTP and TCP-only SOCKS5 inbounds are also available. A compatible router can then route selected devices through that computer.

The project includes version-pinned one-command installers, a Chinese/English localhost UI, desktop launchers, and user-controlled login startup. End users do not need Docker. Windows has local installation and traffic validation. macOS installers are available, but actual Mac/HVF/login/sleep testing is still pending.

This is a preview, not a VPN provider or a universal router solution. Plain L2TP is for trusted LANs only. It has no IPv6 forwarding or kill switch; VPN UDP requires an upstream that supports SOCKS5 UDP ASSOCIATE. The computer and upstream proxy must remain running.

Source and installation: https://github.com/Yeqi99/proxy2vpn

I would appreciate compatibility reports from Apple Silicon Mac and stock-router users, and feedback on installation failure recovery. Please include OS/CPU, router firmware and which traffic was actually tested, without posting credentials.

## 群聊 / 社交短文

开源了 Proxy2VPN：把常开电脑上的 HTTP/SOCKS5 代理，转成原厂路由器能连接的 L2TP / WireGuard 入口。支持一条指令安装、中英文网页管理、自启开关。目前 Windows 已实测，Mac 正在征集真机反馈。适合已有代理、想让家中指定设备通过路由器接入的人。
https://github.com/Yeqi99/proxy2vpn

## 配图与反馈

- 项目原理图：`../media/overview.svg`。这是产品示意图，不是假装的用户截图。
- 首页配有一键安装与限制说明。
- 反馈入口：https://github.com/Yeqi99/proxy2vpn/issues/new?template=compatibility.yml
- 记录每个实际发布链接、安装尝试数、成功反馈与阻塞问题；未拿到的数据留空，不把 Star 当成使用人数。
- 第一批若集中遇到同一安装问题，先修复，再继续扩散。
