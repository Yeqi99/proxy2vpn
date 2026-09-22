param([string]$InstallRoot = "$env:LOCALAPPDATA\Proxy2VPN", [string]$StateRoot = "$env:USERPROFILE\.proxy2vpn", [int]$Port = 18990, [switch]$NoAutostart, [switch]$NoBrowser)
$ErrorActionPreference = 'Stop'
$ProgressPreference = 'SilentlyContinue'
[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
if ([Environment]::Is64BitOperatingSystem -eq $false -or $env:PROCESSOR_ARCHITECTURE -eq 'ARM64') { throw 'This package requires Windows x64.' }
$root = [IO.Path]::GetFullPath($InstallRoot)
New-Item -ItemType Directory -Force -Path $root | Out-Null
$cache = Join-Path $root 'downloads'
New-Item -ItemType Directory -Force -Path $cache | Out-Null
function Download-Verified([string]$Url, [string]$File, [string]$Hash, [string]$Algorithm='SHA256') {
    if ((Test-Path -LiteralPath $File) -and ((Get-FileHash -LiteralPath $File -Algorithm $Algorithm).Hash -ieq $Hash)) { return }
    $pending = "$File.partial"
    Invoke-WebRequest -UseBasicParsing -Uri $Url -OutFile $pending
    if ((Get-FileHash -LiteralPath $pending -Algorithm $Algorithm).Hash -ine $Hash) { throw "Download integrity check failed: $Url" }
    Move-Item -LiteralPath $pending -Destination $File -Force
}
Write-Host '[1/4] Preparing private Python runtime...'
$pyZip = Join-Path $cache 'python.zip'
Download-Verified 'https://www.python.org/ftp/python/3.13.7/python-3.13.7-embed-amd64.zip' $pyZip 'f6cca216a359be84797cabb54149ce5e062afb16cc7567eb7fc51cacb2d86b65'
$pyDir = Join-Path $root 'python'
if (-not (Test-Path -LiteralPath "$pyDir\python.exe")) { Expand-Archive -LiteralPath $pyZip -DestinationPath $pyDir -Force }
$pth = Join-Path $pyDir 'python313._pth'
@('python313.zip','.','Lib\site-packages','import site') | Set-Content -LiteralPath $pth -Encoding ASCII
$python = Join-Path $pyDir 'python.exe'
$getPip = Join-Path $cache 'get-pip.py'
Download-Verified 'https://raw.githubusercontent.com/pypa/get-pip/f6f644156f23dfe9acc06e7b9ca75eee311f2e37/public/get-pip.py' $getPip 'fb24e693bab954209a063d90953621412ccad4a500905a726286e038f508ddf6'
& $python $getPip --disable-pip-version-check
if ($LASTEXITCODE) { throw 'Python dependency installer failed.' }
Write-Host '[2/4] Preparing QEMU (first installation downloads a large official archive)...'
$qemuDir = Join-Path $root 'qemu'
$qemu = Join-Path $qemuDir 'qemu-system-x86_64.exe'
if (-not (Test-Path -LiteralPath $qemu)) {
    $qemuArchive = Join-Path $cache 'qemu-20260811.exe'
    Download-Verified 'https://qemu.weilnetz.de/w64/2026/qemu-w64-setup-20260811.exe' $qemuArchive '5bcf9eed634e8575a37b74f445af41a2fe4106da512d0c30c368301d4c105037fdfab40a5287367a28a957624cddebbc8c07e16c88ab6634f554cdf3d16bf543' 'SHA512'
    & "$PSScriptRoot\tools\7z.exe" x $qemuArchive "-o$qemuDir" -y | Out-Null
    if ($LASTEXITCODE -or -not (Test-Path -LiteralPath $qemu)) { throw 'QEMU extraction failed.' }
}
Write-Host '[3/4] Installing the application and guest...'
$wheel = Get-ChildItem -LiteralPath "$PSScriptRoot\app" -Filter '*.whl' | Select-Object -First 1
if (-not $wheel) { throw 'Application wheel is missing. Download the complete installer package.' }
& $python -m pip install --disable-pip-version-check --upgrade --force-reinstall $wheel.FullName
if ($LASTEXITCODE) { throw 'Application install failed.' }
$assets = Join-Path $root 'assets'
New-Item -ItemType Directory -Force -Path $assets | Out-Null
Copy-Item -Path "$PSScriptRoot\assets\*" -Destination $assets -Force
Write-Host '[4/4] Starting the local console...'
$arguments = @('-m','proxy2vpn.setup','--restart','--home',$StateRoot,'--assets',$assets,'--qemu',$qemu,'--port',"$Port")
if ($NoAutostart) { $arguments += '--no-autostart' }
if ($NoBrowser) { $arguments += '--no-browser' }
& $python @arguments
if ($LASTEXITCODE) { throw 'Console setup failed. Existing private configuration has been preserved.' }
Write-Host "Ready: http://127.0.0.1:$Port/"
