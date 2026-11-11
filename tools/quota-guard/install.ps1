<#
.SYNOPSIS  Installs (or removes) the quota-guard mod into the local Claude Code of the current user.
.EXAMPLE   .\install.ps1            # install
.EXAMPLE   .\install.ps1 -Uninstall # remove
#>
param([switch]$Uninstall)
$ErrorActionPreference = 'Stop'
$here = $PSScriptRoot
$market = 'quota-guard-local'
$plugin = "quota-guard@$market"

if (-not (Get-Command claude -ErrorAction SilentlyContinue)) {
    Write-Error "The 'claude' command is not on PATH. Install Claude Code first."
}

if ($Uninstall) {
    & claude plugin uninstall $plugin
    & claude plugin marketplace remove $market
    Write-Host "quota-guard removed. Restart Claude Code or run /reload-plugins."
    exit 0
}

& claude plugin validate $here
if ($LASTEXITCODE -ne 0) { Write-Error "Validation failed; nothing installed." }

# Reads the mod from this folder: do not move or delete it while the mod is installed.
$known = & claude plugin marketplace list 2>&1 | Out-String
if ($known -notmatch [regex]::Escape($market)) {
    & claude plugin marketplace add $here
    if ($LASTEXITCODE -ne 0) { Write-Error "Could not add the marketplace." }
}
& claude plugin install $plugin --scope user --config threshold=85
if ($LASTEXITCODE -ne 0) { Write-Error "Could not install the plugin." }

Write-Host ""
Write-Host "Installed. In a running Claude Code session type /reload-plugins (or restart it)."
Write-Host "The threshold defaults to 85 (percent of the 5-hour window). Change it with:  claude plugin configure quota-guard"
