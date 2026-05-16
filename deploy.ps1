# --- evidensgjennomgang-me-cfs : opprett offentlig repo + push ---
# Forutsetning: gh er innlogget (gh auth status) som FunksterOne med 'repo'-scope.
$ErrorActionPreference = "Stop"
$root = $PSScriptRoot
Set-Location $root
Write-Host "Arbeidsmappe: $root"

# rydd bort tidligere feiltransfer hvis den finnes
$junk = Join-Path $env:USERPROFILE "_payload.b64"
if (Test-Path $junk) { Remove-Item $junk -Force; Write-Host "Slettet gammel _payload.b64" }

git init | Out-Null
git add -A
git -c user.email="local@local" -c user.name="FunksterOne" commit -m "Evidensgjennomgang ME/CFS - etterarbeid etter hoering (16.05.2026)" | Out-Null
git branch -M main

# Opprett repo OG push i ett (gh har repo-scope). Hvis repoet finnes fra for, faller vi tilbake.
$created = $true
try {
  gh repo create FunksterOne/evidensgjennomgang-me-cfs --public --source . --remote origin --push
} catch {
  $created = $false
}
if (-not $created) {
  Write-Host "Repo fantes trolig fra for - kobler til og pusher i stedet."
  git remote remove origin 2>$null
  git remote add origin https://github.com/FunksterOne/evidensgjennomgang-me-cfs.git
  git push -u origin main --force
}

Write-Host ""
Write-Host "FERDIG. Repo: https://github.com/FunksterOne/evidensgjennomgang-me-cfs"
Write-Host "Naa: Vercel -> Add New -> Project -> Import dette repoet -> Deploy."
