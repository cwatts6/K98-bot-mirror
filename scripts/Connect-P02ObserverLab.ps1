#requires -Version 5.1
[CmdletBinding()]
param([Parameter(Mandatory=$true)][string]$SealPath)
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
$vmId=[guid]'2ac1b401-7076-4965-af71-de36ee0f9f9c'
$checkpointId=[guid]'125272d0-20b7-4705-908f-d3debc71bce2'
if($env:COMPUTERNAME -cne '9SX2VF4'){throw 'Exact development host required.'}
if(-not ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)){
    throw 'Use the existing elevated Windows PowerShell 5.1 console.'
}
$seal=Get-Content -LiteralPath $SealPath -Raw | ConvertFrom-Json
$runner=Join-Path $PSScriptRoot 'Invoke-P02ObserverLab.ps1'
if($seal.purpose -cne 'retained-lab-post-restart-read' -or $seal.vm_id -cne [string]$vmId -or
   (Get-FileHash -LiteralPath $PSCommandPath -Algorithm SHA256).Hash.ToLowerInvariant() -cne $seal.reconnect_sha256 -or
   (Get-FileHash -LiteralPath $runner -Algorithm SHA256).Hash.ToLowerInvariant() -cne $seal.runner_sha256 -or
   (Get-FileHash -LiteralPath $seal.archive -Algorithm SHA256).Hash.ToLowerInvariant() -cne $seal.sha256){
    throw 'Exact sealed restart reader and host scripts required.'
}
$output=Split-Path -Parent $SealPath
$hostReceipt=Join-Path $output 'reconnect.json'
if((Test-Path -LiteralPath $hostReceipt) -or (Test-Path -LiteralPath (Join-Path $output 'launch-result.json'))){
    throw 'Existing restart evidence is preserved; do not rerun.'
}
$vm=Get-VM -Id $vmId
if($vm.Name -cne 'K98-MGE-Qualification-20261029' -or [string]$vm.State -cne 'Running' -or @(Get-VMNetworkAdapter -VM $vm).Count -ne 0){
    throw 'Exact running, network-isolated qualification VM required.'
}
$checkpoints=@(Get-VMSnapshot -VM $vm | Where-Object {$_.Id -eq $checkpointId})
if($checkpoints.Count -ne 1){throw 'Original SQL-update recovery checkpoint is missing.'}
$sessions=@(Get-PSSession | Where-Object {$_.VMId -eq $vmId -and $_.State -eq 'Opened' -and $_.Availability -eq 'Available'})
if($sessions.Count -gt 1){throw 'Multiple lab sessions exist; retain them for review.'}
if($sessions.Count -eq 1){
    $global:P02LabSession=$sessions[0]
}else{
    $labCredential=Get-Credential -UserName 'MINI_AMD\K98LabAdmin' -Message 'Enter the existing qualification VM Windows password here only.'
    if($null -eq $labCredential){throw 'Lab sign-in cancelled; no packet dispatched.'}
    $global:P02LabSession=New-PSSession -VMId $vmId -Credential $labCredential -ErrorAction Stop
    $labCredential=$null
}
if($global:P02LabSession.VMId -ne $vmId -or $global:P02LabSession.State -ne 'Opened' -or $global:P02LabSession.Availability -ne 'Available'){
    throw 'Lab connection identity or state differs.'
}
$guest=Invoke-Command -Session $global:P02LabSession -ScriptBlock {
    Set-StrictMode -Version Latest
    $ErrorActionPreference='Stop'
    if($env:COMPUTERNAME -cne 'MINI_AMD' -or [Security.Principal.WindowsIdentity]::GetCurrent().Name -ine 'MINI_AMD\K98LabAdmin'){
        throw 'Exact isolated guest and Windows identity required.'
    }
    $services=@(Get-CimInstance -ClassName Win32_Service -Filter "Name='MSSQLSERVER' OR Name='SQLSERVERAGENT'" |
        Select-Object Name,State,StartMode)
    $disk=Get-Partition -DriveLetter Q | Get-Disk
    if($disk.UniqueId -cne '60022480F18852E666A58D834543C4BC'){throw 'Retained lab data disk differs.'}
    [pscustomobject]@{
        computer=$env:COMPUTERNAME
        windows_user=[Security.Principal.WindowsIdentity]::GetCurrent().Name
        last_boot_utc=(Get-CimInstance -ClassName Win32_OperatingSystem).LastBootUpTime.ToUniversalTime().ToString('o')
        services=$services
        disk_id=$disk.UniqueId
        disk_bytes=$disk.Size
        q_free_bytes=(Get-PSDrive Q).Free
        c_free_bytes=(Get-PSDrive C).Free
    }
}
$record=[ordered]@{
    schema='p02-reconnect/1';observed_utc=[DateTime]::UtcNow.ToString('o')
    vm_id=[string]$vmId;vm_name=$vm.Name;network_adapters=0
    checkpoint_id=[string]$checkpoints[0].Id;guest=$guest
    phase='connected_before_packet_dispatch';credential_saved=$false
}
# Save a new read-only host receipt before any SQL packet can be dispatched.
$stream=New-Object IO.FileStream($hostReceipt,[IO.FileMode]::CreateNew,[IO.FileAccess]::Write,[IO.FileShare]::Read)
$writer=New-Object IO.StreamWriter($stream,(New-Object Text.UTF8Encoding($false)))
try{$writer.Write(($record | ConvertTo-Json -Depth 8))}finally{$writer.Dispose()}
$engine=@($guest.services | Where-Object {$_.Name -ceq 'MSSQLSERVER'})
$agent=@($guest.services | Where-Object {$_.Name -ceq 'SQLSERVERAGENT'})
if($engine.Count -ne 1 -or $engine[0].State -cne 'Running' -or $agent.Count -ne 1 -or
   $agent[0].State -cne 'Stopped' -or $agent[0].StartMode -cne 'Disabled'){
    throw 'SQL service state differs; reconnect evidence saved and no SQL packet dispatched.'
}
& $runner -SealPath $SealPath -Session $global:P02LabSession
Write-Host 'Authenticated lab session retained in this console as $global:P02LabSession.'
$receipt=Join-Path $output 'receipt.json'
if(Test-Path -LiteralPath $receipt){
    Get-Content -LiteralPath $receipt -Raw | ConvertFrom-Json |
        Select-Object outcome,stage,connections_closed,physical_custody_retained,first_failure | Format-List
}else{
    Write-Host 'No final SQL receipt collected; retain the original process and evidence without rerunning.'
}
