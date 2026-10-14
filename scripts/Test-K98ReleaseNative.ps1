# Isolated administrative Windows rehearsal. Never addresses the Bot task or SQL.
[CmdletBinding()]
param()
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
if($PSVersionTable.PSEdition -cne 'Desktop'){throw 'Windows PowerShell 5.1 required'}
$identity=[Security.Principal.WindowsIdentity]::GetCurrent()
if(-not ([Security.Principal.WindowsPrincipal]::new($identity)).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)){throw 'An administrative PowerShell is required for this isolated ACL/task rehearsal'}
$source=Join-Path $PSScriptRoot 'Deploy-K98Release.ps1'
$tokens=$null;$parseErrors=$null
$ast=[Management.Automation.Language.Parser]::ParseFile($source,[ref]$tokens,[ref]$parseErrors)
if($parseErrors.Count){throw 'Release script does not parse'}
foreach($name in @('Get-BytesHash','Read-Pinned','Assert-AdminPath','New-ControlAcl','Write-NewBytes')) {
    $function=$ast.Find({param($node) $node -is [Management.Automation.Language.FunctionDefinitionAst] -and $node.Name -eq $name},$true)
    if($null -eq $function){throw ('Missing production helper '+$name)}
    . ([scriptblock]::Create($function.Extent.Text))
}
$manifest=[pscustomobject]@{application_sid=$identity.User.Value}
$nonce=[guid]::NewGuid().ToString('N')
$directory=Join-Path $env:ProgramData ('K98ReleaseRehearsal-'+$nonce)
$taskName='K98ReleaseRehearsal-'+$nonce
$registered=$false
$process=$null
try {
    $null=[IO.Directory]::CreateDirectory($directory,(New-ControlAcl $true))
    Assert-AdminPath $directory
    $bytes=[Text.Encoding]::UTF8.GetBytes('isolated rehearsal')
    $file=Join-Path $directory 'control.bin'
    Write-NewBytes $file $bytes
    $null=Read-Pinned $file (Get-BytesHash $bytes) 4096
    $rejected=$false
    try {Write-NewBytes $file $bytes} catch [IO.IOException] {$rejected=$true}
    if(-not $rejected){throw 'Immutable control was overwritten'}
    $acl=Get-Acl -LiteralPath $file
    foreach($ace in $acl.GetAccessRules($true,$true,[Security.Principal.SecurityIdentifier])) {
        if($ace.IdentityReference.Value -ceq $identity.User.Value -and ([long]$ace.FileSystemRights -band 0x500d0156) -ne 0){throw 'Ordinary application SID has control write access'}
    }
    $powershell='C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe'
    # Retain a real native handle before exit, then check its identity after exit.
    $process=Start-Process -FilePath $powershell -ArgumentList @('-NoProfile','-NonInteractive','-Command','Start-Sleep -Seconds 2; exit 0') -WindowStyle Hidden -PassThru
    $nativeHandle=$process.Handle
    $created=$process.StartTime.ToFileTimeUtc()
    if(-not $process.WaitForExit(15000) -or $process.ExitCode -ne 0 -or $process.StartTime.ToFileTimeUtc() -ne $created -or $nativeHandle -eq [IntPtr]::Zero){throw 'Retained process handle rehearsal failed'}
    $action=New-ScheduledTaskAction -Execute $powershell -Argument '-NoProfile -NonInteractive -Command "exit 0"'
    $settings=New-ScheduledTaskSettingsSet -Disable
    $principal=New-ScheduledTaskPrincipal -UserId $identity.User.Value -LogonType Interactive -RunLevel Highest
    $task=New-ScheduledTask -Action $action -Settings $settings -Principal $principal
    $null=Register-ScheduledTask -TaskName $taskName -TaskPath '\' -InputObject $task
    $registered=$true
    if((Get-ScheduledTask -TaskName $taskName -TaskPath '\').Settings.Enabled){throw 'Isolated task unexpectedly enabled'}
    $result=[ordered]@{Status='PASS';Host=$env:COMPUTERNAME;RunnerSHA256=(Get-FileHash -LiteralPath $source -Algorithm SHA256).Hash.ToLowerInvariant();AtomicACL=$true;ImmutableControl=$true;RetainedNativeHandle=$true;DisabledScratchTask=$true;Evidence=$directory;ProductionTouched=$false;SqlConnected=$false;BotStarted=$false}
    Write-NewBytes (Join-Path $directory 'result.json') ([Text.Encoding]::UTF8.GetBytes(($result|ConvertTo-Json -Compress)))
    $result|ConvertTo-Json -Compress
} finally {
    if($registered){Unregister-ScheduledTask -TaskName $taskName -TaskPath '\' -Confirm:$false}
    if($null -ne $process){$process.Dispose()}
}
