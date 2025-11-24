# Docker Quick Start Script

Write-Host "==================================" -ForegroundColor Cyan
Write-Host "  Docker Distributed System" -ForegroundColor Cyan
Write-Host "==================================" -ForegroundColor Cyan
Write-Host ""

Write-Host "Building and starting Docker containers..." -ForegroundColor Yellow
docker-compose up --build -d

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "==================================" -ForegroundColor Green
    Write-Host "  Docker containers started!" -ForegroundColor Green
    Write-Host "==================================" -ForegroundColor Green
    Write-Host ""
    Write-Host "Waiting for services to be ready..." -ForegroundColor Yellow
    Start-Sleep -Seconds 10
    
    Write-Host ""
    Write-Host "Access the applications at:" -ForegroundColor Yellow
    Write-Host "  • Node A:          http://localhost:5001" -ForegroundColor White
    Write-Host "  • Node B:          http://localhost:5002" -ForegroundColor White
    Write-Host "  • Control Panel:   http://localhost:5003" -ForegroundColor White
    Write-Host "  • RabbitMQ Mgmt:   http://localhost:15672" -ForegroundColor White
    Write-Host "                     (user: admin, pass: admin)" -ForegroundColor Gray
    Write-Host ""
    Write-Host "View logs:" -ForegroundColor Yellow
    Write-Host "  docker-compose logs -f" -ForegroundColor White
    Write-Host ""
    Write-Host "Stop containers:" -ForegroundColor Yellow
    Write-Host "  docker-compose down" -ForegroundColor White
    Write-Host ""
    
    $open = Read-Host "Open browsers? (y/n)"
    if ($open -eq "y") {
        Start-Process "http://localhost:5001"
        Start-Process "http://localhost:5002"
        Start-Process "http://localhost:5003"
        Write-Host "✅ Browsers opened!" -ForegroundColor Green
    }
} else {
    Write-Host ""
    Write-Host "❌ Error starting Docker containers!" -ForegroundColor Red
    Write-Host "Please check the error messages above." -ForegroundColor Yellow
}

Write-Host ""
