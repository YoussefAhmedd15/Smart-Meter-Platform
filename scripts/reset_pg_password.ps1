# reset_pg_password.ps1
# Run this in an ADMIN PowerShell window:
#   powershell -ExecutionPolicy Bypass -File "d:\University\Iskra Int\Smart-Meter-Platform\scripts\reset_pg_password.ps1"

$PG_BIN   = "D:\Program Files\PostgreSQL\bin"
$PG_DATA  = "D:\Program Files\PostgreSQL\data"
$PG_HBA   = "$PG_DATA\pg_hba.conf"
$SERVICE  = "postgresql-x64-16"
$NEW_PASS = "postgres123"

Write-Host "=== Step 1: Backing up pg_hba.conf ===" -ForegroundColor Cyan
Copy-Item $PG_HBA "$PG_HBA.backup" -Force
Write-Host "Backup saved."

Write-Host "`n=== Step 2: Setting auth to TRUST ===" -ForegroundColor Cyan
$content = Get-Content $PG_HBA
$content = $content -replace 'scram-sha-256', 'trust'
$content = $content -replace 'md5', 'trust'
Set-Content $PG_HBA $content -Encoding UTF8
Write-Host "pg_hba.conf updated to trust mode."

Write-Host "`n=== Step 3: Restarting PostgreSQL ===" -ForegroundColor Cyan
Restart-Service -Name $SERVICE -Force
Start-Sleep -Seconds 3
Write-Host "PostgreSQL restarted."

Write-Host "`n=== Step 4: Setting new password ===" -ForegroundColor Cyan
$env:PGPASSWORD = ""
& "$PG_BIN\psql.exe" -U postgres -c "ALTER USER postgres PASSWORD '$NEW_PASS';"
if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: Could not set password. Restoring backup..." -ForegroundColor Red
    Copy-Item "$PG_HBA.backup" $PG_HBA -Force
    Restart-Service -Name $SERVICE -Force
    exit 1
}
Write-Host "Password set to: $NEW_PASS"

Write-Host "`n=== Step 5: Restoring pg_hba.conf to scram-sha-256 ===" -ForegroundColor Cyan
Copy-Item "$PG_HBA.backup" $PG_HBA -Force
Write-Host "pg_hba.conf restored."

Write-Host "`n=== Step 6: Final PostgreSQL restart ===" -ForegroundColor Cyan
Restart-Service -Name $SERVICE -Force
Start-Sleep -Seconds 3
Write-Host "PostgreSQL restarted."

Write-Host "`n=== Step 7: Verifying connection ===" -ForegroundColor Cyan
$env:PGPASSWORD = $NEW_PASS
$result = & "$PG_BIN\psql.exe" -U postgres -c "SELECT version();" 2>&1
if ($LASTEXITCODE -eq 0) {
    Write-Host "SUCCESS! Password reset complete." -ForegroundColor Green
} else {
    Write-Host "FAILED. Output:" -ForegroundColor Red
    Write-Host $result
}
