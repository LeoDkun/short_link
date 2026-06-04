Write-Host '========================================'
Write-Host '  ShortLink - Build Frontend & Start'
Write-Host '========================================'
Write-Host ''

Write-Host '[1/3] Installing frontend dependencies...' -ForegroundColor Yellow
Set-Location frontend
npm install
if ($LASTEXITCODE -ne 0) {
    Write-Host 'Failed to install dependencies!' -ForegroundColor Red
    Read-Host 'Press Enter to exit'
    exit 1
}

Write-Host ''
Write-Host '[2/3] Building frontend...' -ForegroundColor Yellow
npm run build
if ($LASTEXITCODE -ne 0) {
    Write-Host 'Failed to build frontend!' -ForegroundColor Red
    Read-Host 'Press Enter to exit'
    exit 1
}

Set-Location ..

Write-Host ''
Write-Host '[3/3] Starting backend server...' -ForegroundColor Yellow
Write-Host ''
Write-Host '========================================'
Write-Host '  Server is running!'
Write-Host '  URL: http://127.0.0.1:8000'
Write-Host '  API Docs: http://127.0.0.1:8000/docs'
Write-Host '========================================'
Write-Host ''

python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
