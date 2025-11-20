# SQL检查工具 - 一键启动脚本
# PowerShell脚本

Write-Host "==================================" -ForegroundColor Cyan
Write-Host "SQL检查工具 - 启动服务" -ForegroundColor Cyan
Write-Host "==================================" -ForegroundColor Cyan
Write-Host ""

# 检查虚拟环境是否存在
if (!(Test-Path "backend\venv")) {
    Write-Host "⚠ 虚拟环境不存在，正在创建..." -ForegroundColor Yellow
    Set-Location backend
    python -m venv venv
    .\venv\Scripts\Activate.ps1
    pip install -r requirements.txt
    Set-Location ..
    Write-Host "✓ 虚拟环境创建完成" -ForegroundColor Green
}

# 启动后端服务
Write-Host ""
Write-Host "启动后端服务..." -ForegroundColor Yellow
Set-Location backend

# 激活虚拟环境
.\venv\Scripts\Activate.ps1

# 启动FastAPI服务
Write-Host "✓ 后端服务启动中..." -ForegroundColor Green
Write-Host "访问 http://localhost:8000 查看应用" -ForegroundColor Cyan
Write-Host "访问 http://localhost:8000/docs 查看API文档" -ForegroundColor Cyan
Write-Host ""
Write-Host "按 Ctrl+C 停止服务" -ForegroundColor Yellow
Write-Host ""

python main.py
