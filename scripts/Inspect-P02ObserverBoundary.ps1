#requires -Version 5.1
[CmdletBinding()]
param([switch]$Permissions,[switch]$Representative,[switch]$QueryPlans,[switch]$ReleasePrerequisites)
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
if (([int][bool]$Permissions+[int][bool]$Representative+[int][bool]$QueryPlans+[int][bool]$ReleasePrerequisites) -gt 1) { throw 'Select one read-only diagnostic.' }
$vmId=[guid]'2ac1b401-7076-4965-af71-de36ee0f9f9c'
if ($env:COMPUTERNAME -cne '9SX2VF4') { throw 'Local development host required.' }
$vm=Get-VM -Id $vmId
if ($vm.Name -cne 'K98-MGE-Qualification-20261029' -or [string]$vm.State -ne 'Running' -or @(Get-VMNetworkAdapter -VM $vm).Count -ne 0) { throw 'Exact isolated VM required.' }
$sessions=@(Get-PSSession | Where-Object { $_.VMId -eq $vmId -and $_.State -eq 'Opened' -and $_.Availability -eq 'Available' })
if ($sessions.Count -ne 1) { throw 'The existing authenticated lab session is required.' }
$session=$sessions[0]
$stamp=[DateTime]::UtcNow.ToString('yyyyMMddHHmmssfff')
$guestRoot='Q:\P02Observer\20261119175737420'
$source=Join-Path $PSScriptRoot $(if ($ReleasePrerequisites) { 'inspect_p02_observer_release.py' } elseif ($QueryPlans) { 'inspect_p02_observer_query_plans.py' } elseif ($Representative) { 'inspect_p02_observer_representative.py' } else { 'diagnose_p02_observer_lab.py' })
$guestScript=[IO.Path]::Combine($guestRoot,('diagnose-'+$stamp+'.py'))
$guestResult=[IO.Path]::Combine($guestRoot,('boundary-'+$stamp+'.json'))
$digest=(Get-FileHash -LiteralPath $source -Algorithm SHA256).Hash
Copy-Item -LiteralPath $source -ToSession $session -Destination $guestScript
$diagnosticExit=Invoke-Command -Session $session -ArgumentList $guestScript,$guestResult,$digest,[bool]$Permissions -ScriptBlock {
    param($script,$result,$digest,$permissions)
    if ((Get-FileHash -LiteralPath $script -Algorithm SHA256).Hash -cne $digest) { throw 'Diagnostic source differs.' }
    if ($permissions) {
        & 'C:\Program Files\Python311\python.exe' -I -S -B $script $result permissions | Out-Host
    } else {
        & 'C:\Program Files\Python311\python.exe' -I -S -B $script $result | Out-Host
    }
    [int]$LASTEXITCODE
}
$localRoot=Join-Path (Split-Path -Parent $PSScriptRoot) '.codex_artifacts\p02-observer-proof-20261119\packet-20261119175737420'
$localResult=Join-Path $localRoot ('boundary-'+$stamp+'.json')
Copy-Item -FromSession $session -LiteralPath $guestResult -Destination $localResult
Write-Host ('Read-only boundary evidence saved: '+$localResult)
if ($diagnosticExit -ne 0) { throw 'Read-only diagnostic failed; its evidence was collected without replay.' }
