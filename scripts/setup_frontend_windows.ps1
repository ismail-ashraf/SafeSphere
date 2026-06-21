Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

Set-Location "$PSScriptRoot\..\frontend"
npm install

if (!(Test-Path ".env")) {
    Copy-Item ".env.example" ".env"
}

Write-Host "Frontend setup completed. Edit frontend/.env if your backend URL is different."
