param(
    [string]$InstallRoot = "$env:LOCALAPPDATA\Proxy2VPN",
    [string]$StateRoot = "$env:USERPROFILE\.proxy2vpn",
    [int]$Port = 18990,
    [switch]$NoAutostart,
    [switch]$NoBrowser
)
$ErrorActionPreference = 'Stop'
$ProgressPreference = 'SilentlyContinue'
[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
if (-not [Environment]::Is64BitOperatingSystem -or $env:PROCESSOR_ARCHITECTURE -eq 'ARM64') {
    throw 'Proxy2VPN currently supports Windows x64. See the GitHub release for supported platforms.'
}
$version = '0.2.2'
$base = "https://github.com/Yeqi99/proxy2vpn/releases/download/v$version"
$name = "proxy2vpn-$version-windows-x64.zip"
$stage = Join-Path ([IO.Path]::GetTempPath()) ("Proxy2VPN-" + [guid]::NewGuid().ToString('N'))
New-Item -ItemType Directory -Path $stage | Out-Null
Write-Host "Downloading Proxy2VPN $version..."
$archive = Join-Path $stage $name
Invoke-WebRequest -UseBasicParsing -Uri "$base/$name" -OutFile $archive
$checksums = (Invoke-WebRequest -UseBasicParsing -Uri "$base/SHA256SUMS").Content
$pattern = '(?m)^([a-fA-F0-9]{64})\s+' + [regex]::Escape($name) + '\r?$'
$match = [regex]::Match([string]$checksums, $pattern)
if (-not $match.Success -or (Get-FileHash -LiteralPath $archive -Algorithm SHA256).Hash -ine $match.Groups[1].Value) {
    throw 'Package checksum verification failed. Installation has not started.'
}
Expand-Archive -LiteralPath $archive -DestinationPath $stage
$arguments = @('-NoProfile','-ExecutionPolicy','Bypass','-File',(Join-Path $stage 'Proxy2VPN\Install-Windows.ps1'),'-InstallRoot',$InstallRoot,'-StateRoot',$StateRoot,'-Port',"$Port")
if ($NoAutostart) { $arguments += '-NoAutostart' }
if ($NoBrowser) { $arguments += '-NoBrowser' }
& powershell.exe @arguments
if ($LASTEXITCODE) { throw "Installation failed. Downloaded files remain at $stage for diagnosis." }
Write-Host 'Done. The local console and desktop shortcut are ready.'
