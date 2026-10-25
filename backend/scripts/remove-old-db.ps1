$ErrorActionPreference = "Continue"
$log = "C:\Users\KL000060\Desktop\dukaan_assistant\backend\scripts\remove-old-db.log"
function Log($msg) {
  $line = "$(Get-Date -Format o) $msg"
  Add-Content -Path $log -Value $line
  Write-Host $line
}

Log "Stopping PostgreSQL 17 and MySQL"
Stop-Service -Name "postgresql-x64-17" -Force -ErrorAction Continue
Set-Service -Name "postgresql-x64-17" -StartupType Disabled -ErrorAction Continue
Stop-Service -Name "MySQL80" -Force -ErrorAction Continue
Set-Service -Name "MySQL80" -StartupType Disabled -ErrorAction Continue

$pg17 = "C:\Program Files\PostgreSQL\17\uninstall-postgresql.exe"
if (Test-Path $pg17) {
  Log "Uninstalling PostgreSQL 17"
  Start-Process -FilePath $pg17 -ArgumentList "--mode","unattended" -Wait -NoNewWindow
} else {
  Log "PostgreSQL 17 uninstaller not found"
}

$mysql = @(
  "{A30BD638-8BF3-4782-A2B5-1956738D9E4E}",
  "{D9468427-386F-4CF9-BA6E-4EC414DB6663}",
  "{17796717-E924-4198-BC42-BE20338FADA2}",
  "{AE2B2ACC-46FB-457B-8687-06E789168089}"
)
foreach ($guid in $mysql) {
  Log "Uninstalling MSI $guid"
  Start-Process -FilePath "msiexec.exe" -ArgumentList "/x",$guid,"/qn","/norestart" -Wait -NoNewWindow
}

Log "Done"
Get-Service -Name "*postgres*","*mysql*" -ErrorAction SilentlyContinue | Format-Table Name, Status, StartType -AutoSize | Out-String | ForEach-Object { Log $_ }
