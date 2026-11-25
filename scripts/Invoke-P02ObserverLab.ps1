#requires -Version 5.1
[CmdletBinding()]
param(
    [Parameter(Mandatory=$true)][string]$SealPath,
    [switch]$CollectOnly,
    [Management.Automation.Runspaces.PSSession]$Session
)
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
$vmId=[guid]'2ac1b401-7076-4965-af71-de36ee0f9f9c'
if ($env:COMPUTERNAME -cne '9SX2VF4') { throw 'Local development host required.' }
if (-not ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
    throw 'Use the existing elevated Windows PowerShell console for local Hyper-V access.'
}
$vm=Get-VM -Id $vmId
if ($vm.Name -cne 'K98-MGE-Qualification-20261029' -or [string]$vm.State -ne 'Running' -or @(Get-VMNetworkAdapter -VM $vm).Count -ne 0) {
    throw 'Exact running, network-isolated qualification VM required.'
}
if ($null -eq $Session) {
    $available=@(Get-PSSession | Where-Object { $_.VMId -eq $vmId -and $_.State -eq 'Opened' -and $_.Availability -eq 'Available' })
    if ($available.Count -ne 1) { throw 'Pass the authenticated lab session from the inventory command.' }
    $Session=$available[0]
}
if ($Session.VMId -ne $vmId -or $Session.State -ne 'Opened' -or $Session.Availability -ne 'Available') { throw 'Unexpected lab session.' }
$seal=Get-Content -LiteralPath $SealPath -Raw | ConvertFrom-Json
$representative=$seal.database -ceq 'K98_P025_D5e_Cost_20261115'
$restored=$seal.database -ceq 'ROK_TRACKER'
$releaseRetained=$restored -and $seal.stage -cin @('observer-release-preflight-read','observer-release-fixture-read','observer-release-prerequisite-read','observer-release-owner-correction')
if ($restored -and $seal.stage -cnotin @('restored-application-observer','observer-release-preflight-read','observer-release-fixture-read','observer-release-prerequisite-read','observer-release-owner-correction')) { throw 'Exact restored application proof required.' }
if ($seal.stage -ceq 'observer-release-owner-correction' -and $seal.purpose -cne 'retained-lab-dbo-mapping-repair') { throw 'Exact retained lab owner correction purpose required.' }
if ((-not $representative -and -not $restored -and $seal.database -cnotmatch '^K98_P02Observer_[0-9]{17}$') -or $seal.guest_directory -cnotmatch '^Q:\\P02Observer\\[0-9]{17}$') { throw 'Unexpected fixture identity.' }
if ((Get-FileHash -LiteralPath $seal.archive -Algorithm SHA256).Hash.ToLowerInvariant() -cne $seal.sha256) { throw 'Sealed packet differs.' }
if (-not $CollectOnly) {
$destination=Invoke-Command -Session $Session -ArgumentList $seal.guest_directory,($representative -or ($restored -and -not $releaseRetained)) -ScriptBlock {
    param($path,$preserveSnapshot)
    if ($env:COMPUTERNAME -cne 'MINI_AMD' -or (Test-Path -LiteralPath $path)) { throw 'Unexpected guest or existing fixture directory.' }
    if ((Get-PSDrive C).Free -lt 1GB -or (Get-PSDrive Q).Free -lt 1GB) { throw 'Insufficient fixture headroom.' }
    if ($preserveSnapshot -and (Get-PSDrive Q).Free -lt 20GB) { throw 'Insufficient headroom for the preserved lab snapshot.' }
    New-Item -ItemType Directory -Path $path -ErrorAction Stop | Out-Null
    Join-Path $path 'packet.zip'
}
Copy-Item -LiteralPath $seal.archive -Destination $destination -ToSession $Session
$run=Invoke-Command -Session $Session -ArgumentList $seal.guest_directory,$seal.sha256,$representative,$restored -ScriptBlock {
    param($path,$digest,$representative,$restored)
    Set-StrictMode -Version Latest
    $ErrorActionPreference='Stop'
    $archive=Join-Path $path 'packet.zip'
    if ((Get-FileHash -LiteralPath $archive -Algorithm SHA256).Hash.ToLowerInvariant() -cne $digest) { throw 'Guest packet differs.' }
    Expand-Archive -LiteralPath $archive -DestinationPath $path
    $python='C:\Program Files\Python311\python.exe'
    if (-not (Test-Path -LiteralPath $python)) { throw 'Existing lab Python installation missing.' }
    $entry=Join-Path $path 'qualification\p02_observer\prove.py'
    if ($representative) { $entry=Join-Path $path 'qualification\p02_observer\representative.py' }
    if ($restored) { $entry=Join-Path $path 'qualification\p02_observer\application.py' }
    $arguments='-I -S -B "'+$entry+'"'
    $process=Start-Process -FilePath $python -ArgumentList $arguments -WorkingDirectory $path -WindowStyle Hidden -PassThru -RedirectStandardOutput (Join-Path $path 'stdout.txt') -RedirectStandardError (Join-Path $path 'stderr.txt')
    # Retain the native process handle before waiting; PS5.1 can otherwise lose
    # the exit-code observation for a quickly exiting redirected child.
    $processHandle=$process.Handle
    $started=[DateTime]::UtcNow
    while (-not $process.WaitForExit(10000)) {
        Write-Host ('Local SQL proof still running; elapsed '+[int]([DateTime]::UtcNow-$started).TotalSeconds+' seconds.')
        if (([DateTime]::UtcNow-$started).TotalSeconds -ge 180) {
            # Do not pretend a timeout cancelled SQL or release physical ownership.
            # Preserve this process/fixture; collect and diagnose before any rerun.
            $global:P02ObserverHeldProcess=$process
            return [pscustomobject]@{state='retained-running';pid=$process.Id;path=$path}
        }
    }
    $process.WaitForExit()
    [pscustomobject]@{state='exited';pid=$process.Id;exitCode=$process.ExitCode;path=$path}
}
$output=Split-Path -Parent $SealPath
$run | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath (Join-Path $output 'launch-result.json') -Encoding UTF8
} else {
    $output=Split-Path -Parent $SealPath
    $run=Get-Content -LiteralPath (Join-Path $output 'launch-result.json') -Raw | ConvertFrom-Json
}
$collection=@('receipt.json','progress.json','stdout.txt','stderr.txt','protocol-definitions.txt','representative-before.json','representative-observation.json','changed-catalogue-observation.json','catalogue-timings.json','catalogue-cost-result.json','catalogue-query-plans.json','publisher-before.json','publisher-actor-first-commit.json','publisher-actor-first-output.json','publisher-actor-first-observation.json','publisher-observer-first-commit.json','publisher-observer-first-output.json','publisher-observer-first-observation.json','publisher-failure-state.json','publisher-object-read.json','publisher-final-observation.json','combined-budget.json','combined-observation.json')
if ($restored) { $collection += @('lab-installation.json','application-observation.json','cold-application-observation.json'); $collection += @(1..10 | ForEach-Object { 'stage-'+$_+'.json' }) }
foreach ($name in $collection) {
    $exists=Invoke-Command -Session $Session -ArgumentList $seal.guest_directory,$name -ScriptBlock {param($path,$name) Test-Path -LiteralPath (Join-Path $path $name)}
    if ($exists) {
        $localPath=Join-Path $output $name
        if (Test-Path -LiteralPath $localPath) { throw ('Existing evidence is preserved: '+$localPath) }
        Copy-Item -FromSession $Session -LiteralPath ([IO.Path]::Combine($seal.guest_directory,$name)) -Destination $localPath
    }
}
$run | Format-List
Write-Host ('Evidence saved: '+$output)
if ($representative -or $restored) {
    Write-Host 'Evidence and any created snapshot retained. The receipt records local fixture operations and completed stages. Production was not targeted.'
} else {
    Write-Host 'Fixture retained. Earlier programme databases and production were not targeted.'
}
