#requires -Version 5.1
[CmdletBinding()]
param([Management.Automation.Runspaces.PSSession]$Session)
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$vmId = [guid]'2ac1b401-7076-4965-af71-de36ee0f9f9c'
if ($env:COMPUTERNAME -cne '9SX2VF4') { throw 'Local development host required.' }
if (-not ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
    throw 'Use an elevated Windows PowerShell console for local Hyper-V access.'
}
$vm = Get-VM -Id $vmId
if ($vm.Name -cne 'K98-MGE-Qualification-20261029' -or @(Get-VMNetworkAdapter -VM $vm).Count -ne 0) {
    throw 'Expected isolated qualification VM required.'
}
if ([string]$vm.State -eq 'Off') {
    Start-VM -VM $vm | Out-Null
    $vm = Get-VM -Id $vmId
}
if ([string]$vm.State -ne 'Running') { throw 'Qualification VM is not running.' }
if ($null -eq $Session) {
    $available = @(Get-PSSession | Where-Object { $_.VMId -eq $vmId -and $_.State -eq 'Opened' -and $_.Availability -eq 'Available' })
    if ($available.Count -eq 1) { $Session = $available[0] }
    elseif ($available.Count -gt 1) { throw 'Pass the intended existing lab session explicitly.' }
    else {
        $credential = Get-Credential -UserName 'MINI_AMD\K98LabAdmin' -Message 'Local isolated qualification VM only; credentials are not saved.'
        if ($null -eq $credential) { throw 'Lab authentication was cancelled.' }
        $Session = New-PSSession -VMId $vmId -Credential $credential
        $credential = $null
    }
}
if ($Session.VMId -ne $vmId -or $Session.State -ne 'Opened' -or $Session.Availability -ne 'Available') {
    throw 'An available session to the exact local VM is required.'
}
$global:P02ObserverLabSession = $Session
$guest = Invoke-Command -Session $Session -ScriptBlock {
    Set-StrictMode -Version Latest
    $ErrorActionPreference = 'Stop'
    if ($env:COMPUTERNAME -cne 'MINI_AMD') { throw 'Unexpected lab guest identity.' }
    $connection = [Data.SqlClient.SqlConnection]::new('Data Source=lpc:localhost;Initial Catalog=master;Integrated Security=True;Connect Timeout=5;Pooling=False;Application Name=P02ObserverLabInventory')
    $rows = [Collections.Generic.List[object]]::new()
    $reader = $null; $command = $null
    try {
        $connection.Open()
        $command = $connection.CreateCommand(); $command.CommandTimeout = 10
        $command.CommandText = "SELECT d.name,d.state_desc,d.is_read_only,d.create_date,CONVERT(bigint,SUM(f.size))*8192 AS BytesAllocated FROM sys.databases d JOIN sys.master_files f ON f.database_id=d.database_id WHERE d.database_id>4 GROUP BY d.name,d.state_desc,d.is_read_only,d.create_date ORDER BY d.name"
        $reader = $command.ExecuteReader()
        while ($reader.Read()) {
            $row = [ordered]@{}
            for ($i=0; $i -lt $reader.FieldCount; $i++) { $row[$reader.GetName($i)] = if ($reader.IsDBNull($i)) { $null } else { $reader.GetValue($i) } }
            $rows.Add([pscustomobject]$row)
        }
        [pscustomobject]@{
            computer=$env:COMPUTERNAME
            account=[Security.Principal.WindowsIdentity]::GetCurrent().Name
            databases=$rows.ToArray()
            python=@(Get-Command python.exe -ErrorAction SilentlyContinue | Select-Object -ExpandProperty Source)
            drives=@(Get-PSDrive -PSProvider FileSystem | Select-Object Name,Root,Used,Free)
        }
    } finally {
        if ($null -ne $reader) { $reader.Close(); $reader.Dispose() }
        if ($null -ne $command) { $command.Dispose() }
        $connection.Close(); $connection.Dispose()
    }
}
$root = Split-Path -Parent $PSScriptRoot
$output = Join-Path $root '.codex_artifacts\p02-observer-proof-20261119'
$name = 'lab-inventory-' + [DateTime]::UtcNow.ToString('yyyyMMddTHHmmssfff') + '.json'
$path = Join-Path $output $name
$result = [ordered]@{schema='p02-observer-lab-inventory/1';utc=[DateTime]::UtcNow.ToString('o');host=$env:COMPUTERNAME;vmId=[string]$vmId;vmName=$vm.Name;session=[string]$Session.InstanceId;guest=$guest;sqlMutations=0;productionOperations=0}
$bytes = [Text.Encoding]::UTF8.GetBytes(($result | ConvertTo-Json -Depth 10))
$file = [IO.File]::Open($path,[IO.FileMode]::CreateNew,[IO.FileAccess]::Write,[IO.FileShare]::None)
try { $file.Write($bytes,0,$bytes.Length) } finally { $file.Dispose() }
Write-Host ('Inventory saved: ' + $path)
$guest.databases | Format-Table -AutoSize
Write-Host 'SQL connections closed. Lab session retained as $global:P02ObserverLabSession.'
