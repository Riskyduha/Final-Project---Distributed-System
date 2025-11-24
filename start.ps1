# Quick Start Script for Windows
# Menjalankan semua nodes secara bersamaan

Write-Host "==================================" -ForegroundColor Cyan
Write-Host "  Distributed System Launcher" -ForegroundColor Cyan
Write-Host "==================================" -ForegroundColor Cyan
Write-Host ""

# Check if RabbitMQ is running
Write-Host "Checking RabbitMQ status..." -ForegroundColor Yellow
$rabbitmq = Get-Process -Name "erl" -ErrorAction SilentlyContinue

if (-not $rabbitmq) {
    Write-Host "⚠️  RabbitMQ is not running!" -ForegroundColor Red
    Write-Host "Please start RabbitMQ first:" -ForegroundColor Yellow
    Write-Host "  - Using Docker: docker-compose up rabbitmq" -ForegroundColor White
    Write-Host "  - Or install RabbitMQ: https://www.rabbitmq.com/download.html" -ForegroundColor White
    Write-Host ""
    $continue = Read-Host "Continue anyway? (y/n)"
    if ($continue -ne "y") {
        exit
    }
}

Write-Host ""
Write-Host "Starting applications..." -ForegroundColor Green
Write-Host ""

# Start Node A
Write-Host "🚀 Starting Node A on port 5001..." -ForegroundColor Cyan
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$PSScriptRoot\node_a'; python app.py"
Start-Sleep -Seconds 2

# Start Node B
Write-Host "🚀 Starting Node B on port 5002..." -ForegroundColor Cyan
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$PSScriptRoot\node_b'; python app.py"
Start-Sleep -Seconds 2

# Start Control Panel
Write-Host "🚀 Starting Control Panel on port 5003..." -ForegroundColor Cyan
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$PSScriptRoot\control_panel'; python app.py"
Start-Sleep -Seconds 3

Write-Host ""
Write-Host "==================================" -ForegroundColor Green
Write-Host "  All applications started!" -ForegroundColor Green
Write-Host "==================================" -ForegroundColor Green
Write-Host ""
Write-Host "Access the applications at:" -ForegroundColor Yellow
Write-Host "  • Node A:         http://localhost:5001" -ForegroundColor White
Write-Host "  • Node B:         http://localhost:5002" -ForegroundColor White
Write-Host "  • Control Panel:  http://localhost:5003" -ForegroundColor White
Write-Host ""
Write-Host "Press any key to open browsers..." -ForegroundColor Yellow
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")

# Open browsers
Start-Process "http://localhost:5001"
Start-Process "http://localhost:5002"
Start-Process "http://localhost:5003"

Write-Host ""
Write-Host "✅ Done! Check the new browser windows." -ForegroundColor Green
Write-Host "Press any key to exit..." -ForegroundColor Yellow
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
