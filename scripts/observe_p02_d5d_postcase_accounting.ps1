#requires -Version 5.1
[CmdletBinding()]
param(
    [Parameter(Mandatory=$true)][System.Management.Automation.Runspaces.PSSession]$Session,
    [Parameter(Mandatory=$true)][ValidatePattern('^[a-f0-9]{64}$')][string]$RunnerSHA256,
    [Parameter(Mandatory=$true)][ValidatePattern('^[a-f0-9]{64}$')][string]$OfflineReceiptSHA256
)
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
$watch=[Diagnostics.Stopwatch]::StartNew()
$root='C:\discord_file_downloader'
$out=Join-Path $root '.codex_artifacts\p025'
function Plain([string]$Path){
    $item=Get-Item -LiteralPath $Path -Force
    while($null -ne $item){if($item.Attributes -band [IO.FileAttributes]::ReparsePoint){throw 'Redirected diagnostic path'};$item=if($item -is [IO.FileInfo]){$item.Directory}else{$item.Parent}}
}
function New-Receipt([string]$Path,$Value){
    $bytes=[Text.Encoding]::UTF8.GetBytes(($Value|ConvertTo-Json -Depth 40 -Compress))
    if($bytes.Length -gt 1MB){throw 'Diagnostic receipt bound'}
    $stream=[IO.File]::Open($Path,[IO.FileMode]::CreateNew,[IO.FileAccess]::Write,[IO.FileShare]::None)
    try{$stream.Write($bytes,0,$bytes.Length);$stream.Flush($true)}finally{$stream.Dispose()}
}
function Pinned([string]$Path,[string]$Hash){Plain $Path;if((Get-FileHash -LiteralPath $Path).Hash -ine $Hash){throw 'Diagnostic input changed'};[IO.File]::ReadAllText($Path)}
if($env:COMPUTERNAME -cne '9SX2VF4' -or $PSVersionTable.PSEdition -cne 'Desktop' -or [IntPtr]::Size -ne 8){throw 'Wrong diagnostic host'}
if(-not ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)){throw 'Elevation required'}
$null=Pinned $PSCommandPath $RunnerSHA256
if($Session.InstanceId -ne [guid]'b09386eb-cc29-40b3-8f31-75636e9fe3da' -or $Session.VMId -ne [guid]'2ac1b401-7076-4965-af71-de36ee0f9f9c' -or $Session.State -ne 'Opened' -or $Session.Availability -ne 'Available'){throw 'Recorded session unavailable'}
$vm=Get-VM -Id $Session.VMId
if($vm.Name -cne 'K98-MGE-Qualification-20261029' -or $vm.State -ne 'Running' -or $vm.ProcessorCount -ne 4 -or $vm.DynamicMemoryEnabled -or $vm.MemoryAssigned -ne 8GB -or @(Get-VMNetworkAdapter -VM $vm).Count){throw 'VM isolation differs'}
$raw=Pinned (Join-Path $out 'd5d-catalog-continuation-packet.json') '661e4f3e6a94ae983b88ebf49f92d4c1e3b1a862a5f68fdfa82ae3f3528c0056'
$prior=Pinned (Join-Path $out 'd5d-catalog-continuation-result-2a459e53deef4ce18aa11f31f923780f.json') 'fb10c0843685e491533725354a3aedc53c5e9841b4fda6fe68bd40afabaa69f1'
$source=Pinned (Join-Path $root 'scripts\run_p02_d5d_catalog_continuation_packet.ps1') '246fdf6fbc536d458741586527f894d6b8071372dc17047093780d0f7c9b62ef'
$packet=$raw|ConvertFrom-Json
foreach($pin in $packet.pins.PSObject.Properties){$null=Pinned (Join-Path $root $pin.Name) $pin.Value}
foreach($pin in $packet.sqlPins.PSObject.Properties){$null=Pinned $pin.Name $pin.Value}
$previous=$prior|ConvertFrom-Json
if($previous.guest.completed -ne 24 -or $previous.guest.cases.Count -ne 24 -or -not $previous.guest.physicalClosureVerified -or -not $previous.guest.preserved){throw 'Previous native evidence requires adjudication'}
$offlineRaw=Pinned (Join-Path $out 'd5d-restart-qualification\result.json') $OfflineReceiptSHA256
$offline=$offlineRaw|ConvertFrom-Json
if(-not $offline.passed -or $offline.mode -cne 'execute' -or $offline.completed -ne 21 -or $offline.expected -ne 21 -or $offline.nativeOperations -ne 0 -or -not $offline.preservedHashesUnchanged -or $offline.pending.Count){throw 'Original offline restart evidence not accepted'}
$acceptedTotal=71+$offline.completed
$tokens=$null;$parseErrors=$null;$ast=[Management.Automation.Language.Parser]::ParseInput($source,[ref]$tokens,[ref]$parseErrors)
if($parseErrors.Count){throw 'Pinned helper parse failed'}
$helper=''
foreach($name in @('Canon','Same')){$defs=@($ast.FindAll({param($n) $n -is [Management.Automation.Language.FunctionDefinitionAst] -and $n.Name -ceq $name},$true));if($defs.Count -ne 1){throw 'Exact helper absent'};$helper+=$defs[0].Extent.Text+"`n"}
Plain $out
$watch.Restart()
New-Receipt (Join-Path $out 'd5d-postcase-accounting-intent.json') @{atUtc=[DateTime]::UtcNow.ToString('o');runnerSHA256=$RunnerSHA256;nativeReserved=15;windowsReserved=0;newRows=0;newInputs=0;readOnly=$true}
$receipt=@{phase='diagnosis incomplete';errors=@();guest=$null;nativeBalanceBefore=1237;nativeReserved=15;windowsRemaining=49;newRows=0;newInputs=0;expected=92;accepted=$acceptedTotal;runnerSHA256=$RunnerSHA256}
$job=$null
try{
    $remaining=10-$watch.Elapsed.TotalSeconds
    if($remaining -lt 4){throw 'Insufficient read-only observation allowance'}
    $job=Invoke-Command -Session $Session -AsJob -ArgumentList $raw,$prior,$helper,$remaining -ScriptBlock {
        param($Raw,$Prior,$Helper,$Seconds)
        Set-StrictMode -Version Latest;$ErrorActionPreference='Stop'
        $clock=[Diagnostics.Stopwatch]::StartNew();$p=$Raw|ConvertFrom-Json;$old=$Prior|ConvertFrom-Json
        $r=@{errors=@();files=@();births=@();operations=0;rows=0;preserved=$false;observerClosureVerified=$false;finalCollectorCloseAcknowledged=$false;nativeCases=0}
        $connections=[Collections.Generic.List[object]]::new()
        function Budget{if($clock.Elapsed.TotalSeconds -ge $Seconds -or $r.operations -ge 180 -or $r.rows -gt 512){throw 'Read-only observation limit'}}
        function Closure-Mode([int]$Connections,[int]$Births){if($Connections -eq 0 -and $Births -eq 0){return 'none'};if($Connections -gt 0 -and $Births -eq $Connections){return 'bound'};return 'unknown'}
        function Plain([string]$Path){$item=Get-Item -LiteralPath $Path -Force;while($null -ne $item){if($item.Attributes -band [IO.FileAttributes]::ReparsePoint){throw 'Redirected guest path'};$item=if($item -is [IO.FileInfo]){$item.Directory}else{$item.Parent}}}
        function Read-Owned([string]$Path,[int]$Limit,[bool]$Text=$false){
            Budget
            if(-not (Test-Path -LiteralPath $Path)){return @{path=$Path;exists=$false}}
            Plain $Path;$f=Get-Item -LiteralPath $Path
            if($f -isnot [IO.FileInfo] -or $f.Length -gt $Limit){throw 'Owned evidence size/type bound'}
            $value=@{path=$Path;exists=$true;bytes=$f.Length;sha256=(Get-FileHash -LiteralPath $Path).Hash}
            if($Text){$value.text=[IO.File]::ReadAllText($Path)}
            return $value
        }
        function Query($cn,[string]$Sql,[int]$Max=128,$Parameters=@{}){
            Budget;$r.operations++;$cmd=$cn.CreateCommand();$cmd.CommandTimeout=2;$cmd.CommandText=$Sql;$reader=$null;$rows=[Collections.Generic.List[object]]::new()
            foreach($key in $Parameters.Keys){$null=$cmd.Parameters.AddWithValue($key,$Parameters[$key])}
            try{$reader=$cmd.ExecuteReader();do{while($reader.Read()){if($rows.Count -ge $Max -or $r.rows -ge 512){throw 'Diagnostic SQL row limit'};$o=[ordered]@{};for($i=0;$i -lt $reader.FieldCount;$i++){$o[$reader.GetName($i)]=if($reader.IsDBNull($i)){$null}else{$reader.GetValue($i)}};$rows.Add([pscustomobject]$o);$r.rows++}}while($reader.NextResult());return ,$rows.ToArray()}finally{if($null -ne $reader){$reader.Dispose()};$cmd.Dispose()}
        }
        function Open([string]$Db){
            Budget
            if($Db -notin @('master','K98_P025_D5b_20261111','K98_P025_D5c_Hold_20261115','K98_P025_D5d_Fault_20261115')){throw 'Diagnostic database not allowed'}
            $cn=[Data.SqlClient.SqlConnection]::new('Data Source=lpc:localhost;Initial Catalog='+$Db+';Integrated Security=True;Connect Timeout=2;Pooling=False;Application Name=P02D5dReadOnlyDiagnostic');$connections.Add($cn);$r.operations++;$cn.Open()
            $null=Query $cn 'SET NOCOUNT ON; SET LOCK_TIMEOUT 0;' 0
            $birth=Query $cn 'SELECT @@SPID AS sid,CONVERT(varchar(23),s.login_time,121) AS birth,CONVERT(varchar(36),c.connection_id) AS connection_id FROM sys.dm_exec_sessions s JOIN sys.dm_exec_connections c ON s.session_id=c.session_id WHERE s.session_id=@@SPID' 1
            if($birth.Count -ne 1){throw 'Diagnostic observer identity missing'};$r.births+=@($birth[0]);return $cn
        }
        . ([scriptblock]::Create($Helper))
        try{
            if($env:COMPUTERNAME -cne 'MINI_AMD'){throw 'Wrong guest'}
            $volume=Get-CimInstance Win32_Volume -Filter "DriveLetter='Q:'" -OperationTimeoutSec 2
            if($volume.DeviceID -ine '\\?\Volume{47cc6080-9e5f-447c-a9e2-dcc007b1e297}\' -or $volume.Label -cne 'K98_D5B_QUALIFICATION' -or $volume.FileSystem -cne 'NTFS'){throw 'Qualification volume differs'}
            $folder='Q:\D5dContinuation-20261115'
            foreach($name in @('packet.json','actor.py','guest-result.json')){
                $limit=if($name -eq 'packet.json'){786432}elseif($name -eq 'guest-result.json'){1MB}else{65536}
                $r.files+=@(Read-Owned (Join-Path $folder $name) $limit)
            }
            if(-not $r.files[0].exists -or $r.files[0].sha256 -ine $old.packetSHA256 -or -not $r.files[1].exists -or $r.files[1].sha256 -ine $p.pins.'scripts/p02_d5d_continuation_native.py' -or -not $r.files[2].exists){throw 'Retained packet/actor/guest result differs'}
            foreach($case in $old.guest.cases){
                if($case.case -cnotin $p.cases){throw 'Unregistered case path'}
                $path=Join-Path $folder ($case.case.Replace('.','_')+'\stdout.json')
                $file=Read-Owned $path 65536
                if(-not $file.exists -or $file.sha256 -ine $case.stdoutSHA256){throw 'Accepted actor evidence differs'}
                $r.files+=@($file)
            }
            $r.pythonProcesses=@(Get-Process | Where-Object {$_.ProcessName -match '^pythonw?$'} | ForEach-Object {@{pid=$_.Id;birth=$_.StartTime.ToUniversalTime().ToString('o');path=$_.Path}})
            $master=Open 'master'
            $identity=Query $master "SELECT @@SERVERNAME AS host,ORIGINAL_LOGIN() AS login,CONVERT(varchar(128),SERVERPROPERTY('ProductVersion')) AS version" 1
            if($identity.Count -ne 1 -or $identity[0].host -cne 'MINI_AMD' -or $identity[0].login -cne 'MINI_AMD\K98LabAdmin' -or $identity[0].version -cne '16.0.1210.3'){throw 'SQL host identity differs'}
            $r.databases=Query $master "SELECT name,database_id,CONVERT(varchar(23),create_date,121) AS birth,is_read_only,user_access_desc,is_read_committed_snapshot_on,is_trustworthy_on,is_db_chaining_on,snapshot_isolation_state FROM sys.databases WHERE database_id IN (7,8,9,10) ORDER BY database_id" 4
            if($r.databases.Count -ne 4 -or $r.databases[3].name -cne 'K98_P025_D5d_Fault_20261115' -or $r.databases[3].birth -cne '2026-11-15 10:31:04.697'){throw 'Fault database identity differs'}
            if($r.databases[0].name -cne 'K98_P021_PreImport_20261107' -or -not $r.databases[0].is_read_only -or $r.databases[0].user_access_desc -cne 'RESTRICTED_USER' -or $r.databases[1].name -cne 'K98_P025_D5b_20261111' -or $r.databases[1].birth -cne '2026-11-11 17:00:42.830' -or $r.databases[2].name -cne 'K98_P025_D5c_Hold_20261115' -or $r.databases[2].birth -cne '2026-11-15 07:59:24.150'){throw 'Retained database identities differ'}
            $r.oldObserversRemaining=@()
            foreach($set in $old.guest.observerBirths){foreach($b in $set){$present=Query $master 'SELECT s.session_id FROM sys.dm_exec_sessions s JOIN sys.dm_exec_connections c ON s.session_id=c.session_id WHERE s.session_id=@sid AND CONVERT(varchar(23),s.login_time,121)=@birth AND CONVERT(varchar(36),c.connection_id)=@connection' 1 @{'@sid'=$b.sid;'@birth'=$b.birth;'@connection'=$b.connection_id};foreach($row in $present){$r.oldObserversRemaining+=@($row)}}}
            $r.actorSessions=Query $master "SELECT session_id,program_name,CONVERT(varchar(23),login_time,121) AS birth FROM sys.dm_exec_sessions WHERE program_name LIKE 'P02D5d[_]%' OR program_name IN ('P02D5dObserver','P02D5dFinalClosure')" 32
            $copy=Open 'K98_P025_D5b_20261111';$hold=Open 'K98_P025_D5c_Hold_20261115';$work=Open 'K98_P025_D5d_Fault_20261115'
            $r.fixtureRows=@{}
            foreach($table in @('MaintenanceWork','MaintenanceConfigurationWork','MaintenanceBackupWork','MaintenanceKvkWork','D5dEffect','D5dTransactionMarker')){$r.fixtureRows[$table]=Query $work ('SELECT * FROM dbo.['+$table+']') 16}
            $r.finalFixtureCounts=Query $work 'SELECT (SELECT COUNT(*) FROM dbo.MaintenanceWork) AS [maintenance],(SELECT COUNT(*) FROM dbo.MaintenanceConfigurationWork) AS [configuration],(SELECT COUNT(*) FROM dbo.MaintenanceBackupWork) AS [backup],(SELECT COUNT(*) FROM dbo.D5dEffect) AS [effects],(SELECT COUNT(*) FROM dbo.D5dTransactionMarker) AS [committedMarkers]' 1
            $counts=$r.finalFixtureCounts[0]
            if($counts.maintenance -ne 6 -or $counts.configuration -ne 1 -or $counts.backup -ne 1 -or $counts.effects -ne 6 -or $counts.committedMarkers -ne 1){throw 'Final fixture count differs'}
            if($r.fixtureRows.MaintenanceKvkWork.Count -ne 0 -or $r.fixtureRows.D5dTransactionMarker[0].CaseID -cne 'commit_lost'){throw 'Final transaction marker differs'}
            if($r.pythonProcesses.Count -or $r.actorSessions.Count -or $r.oldObserversRemaining.Count){throw 'Previous owners remain; read-only stop'}
            foreach($s in $p.preserve){$cn=if($s.database -ceq 'K98_P025_D5b_20261111'){$copy}elseif($s.database -ceq 'K98_P025_D5c_Hold_20261115'){$hold}else{throw 'Preservation database differs'};Same (Query $cn $s.sql $s.maxRows) $s.expected}
            $r.preserved=$true
        }catch{$r.errors+=@($_.Exception.Message)}finally{
            foreach($cn in $connections){try{$cn.Dispose()}catch{$r.errors+=@('Diagnostic observer disposal unconfirmed');$global:D5dPostcaseAccountingConnectionCustody=$connections}}
            $closure=$null
            $mode=Closure-Mode $connections.Count $r.births.Count
            if($mode -eq 'none'){$r.observerClosureVerified=$true;$r.finalCollectorCloseAcknowledged=$true}
            elseif($mode -eq 'unknown'){$r.errors+=@('Diagnostic observer identity incomplete; closure unknown');$r.finalCollectorCloseAcknowledged=$true}
            else{try{
                $closure=[Data.SqlClient.SqlConnection]::new('Data Source=lpc:localhost;Initial Catalog=master;Integrated Security=True;Connect Timeout=2;Pooling=False;Application Name=P02D5dPostcaseAccountingClosure');$closure.Open();$r.operations++
                foreach($b in $r.births){if((Query $closure 'SELECT s.session_id FROM sys.dm_exec_sessions s JOIN sys.dm_exec_connections c ON s.session_id=c.session_id WHERE s.session_id=@sid AND CONVERT(varchar(23),s.login_time,121)=@birth AND CONVERT(varchar(36),c.connection_id)=@connection' 1 @{'@sid'=$b.sid;'@birth'=$b.birth;'@connection'=$b.connection_id}).Count){throw 'Diagnostic observer remains'}}
                $r.observerClosureVerified=$true
            }catch{$r.errors+=@('Diagnostic closure independently unconfirmed')}finally{if($null -ne $closure){try{$closure.Dispose();$r.finalCollectorCloseAcknowledged=$true}catch{$r.errors+=@('Final collector disposal unconfirmed');$global:D5dPostcaseAccountingFinalCustody=$closure}}}}
            $r.elapsedSeconds=$clock.Elapsed.TotalSeconds
        }
        $r
    }
    $wait=[Math]::Max(1,[Math]::Floor(12-$watch.Elapsed.TotalSeconds))
    if(-not (Wait-Job $job -Timeout $wait) -or $job.State -ne 'Completed'){throw 'Diagnostic not joined; retain job and do not retry'}
    $receipt.guest=Receive-Job $job -ErrorAction Stop
    if($receipt.guest.errors.Count -or -not $receipt.guest.preserved -or -not $receipt.guest.observerClosureVerified -or -not $receipt.guest.finalCollectorCloseAcknowledged){throw 'Diagnostic evidence incomplete'}
    $receipt.phase='read-only evidence collected; adjudication required'
}catch{$receipt.errors+=@($_.Exception.Message)}finally{
    $receipt.elapsedSeconds=$watch.Elapsed.TotalSeconds
    $receipt.timeSettled=($null -ne $receipt.guest -and $receipt.guest.observerClosureVerified -and $receipt.guest.finalCollectorCloseAcknowledged)
    $charged=if($receipt.timeSettled){[Math]::Ceiling($watch.Elapsed.TotalSeconds)}else{[Math]::Max(15,[Math]::Ceiling($watch.Elapsed.TotalSeconds))}
    $receipt.nativeRemaining=1237-$charged
    if(-not $receipt.timeSettled){$global:D5dPostcaseAccountingJobCustody=$job}
    $path=Join-Path $out ('d5d-postcase-accounting-result-'+[guid]::NewGuid().ToString('N')+'.json')
    New-Receipt $path $receipt
    [pscustomobject]@{Phase=$receipt.phase;Receipt=$path;SHA256=(Get-FileHash $path).Hash;Completed=$acceptedTotal;Expected=92;NativeRemaining=$receipt.nativeRemaining;WindowsRemaining=49;Errors=$receipt.errors}|Format-List
}
