Set-Location $PSScriptRoot

if (Test-Path ".\venv\Scripts\Activate.ps1") {
    . .\venv\Scripts\Activate.ps1
} else {
    Write-Host "Virtual environment not found: venv\Scripts\Activate.ps1"
    exit 1
}

python manage.py runserver 127.0.0.1:8000 --noreload
