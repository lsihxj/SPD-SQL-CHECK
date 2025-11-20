# SQL检查工具 - 完整启动脚本
# 同时启动前端和后端服务

Write-Host "==================================" -ForegroundColor Cyan
Write-Host "SQL检查工具 - 完整启动" -ForegroundColor Cyan
Write-Host "==================================" -ForegroundColor Cyan
Write-Host ""

# 检查后端虚拟环境
if (!(Test-Path "backend\venv")) {
    Write-Host "⚠ 后端虚拟环境不存在,正在创建..." -ForegroundColor Yellow
    Set-Location backend
    python -m venv venv
    .\venv\Scripts\Activate.ps1
    Write-Host "安装后端依赖..." -ForegroundColor Yellow
    pip install -r requirements.txt
    Set-Location ..
    Write-Host "✓ 后端环境准备完成" -ForegroundColor Green
}

# 检查前端依赖
if (!(Test-Path "frontend\node_modules")) {
    Write-Host "⚠ 前端依赖未安装,正在安装..." -ForegroundColor Yellow
    Set-Location frontend
    npm install
    Set-Location ..
    Write-Host "✓ 前端依赖安装完成" -ForegroundColor Green
}

Write-Host ""
Write-Host "正在启动服务..." -ForegroundColor Cyan
Write-Host ""

# 启动后端服务（后台运行）
Write-Host "1️⃣  启动后端服务 (http://localhost:8000)..." -ForegroundColor Yellow
$backendJob = Start-Job -ScriptBlock {
    Set-Location $using:PWD
    Set-Location backend
    .\venv\Scripts\Activate.ps1
    python main.py
}

# 等待后端启动
Start-Sleep -Seconds 3

# 启动前端服务（后台运行）
Write-Host "2️⃣  启动前端服务 (http://localhost:5173)..." -ForegroundColor Yellow
$frontendJob = Start-Job -ScriptBlock {
    Set-Location $using:PWD
    Set-Location frontend
    npm run dev
}

# 等待前端启动
Start-Sleep -Seconds 3

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "✅ 服务启动成功！" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "📝 前端地址: http://localhost:5173" -ForegroundColor Cyan
Write-Host "📝 后端地址: http://localhost:8000" -ForegroundColor Cyan  
Write-Host "📝 API文档: http://localhost:8000/docs" -ForegroundColor Cyan
Write-Host ""
Write-Host "按 Ctrl+C 停止所有服务" -ForegroundColor Yellow
Write-Host ""

# 监控服务状态
try {
    while ($true) {
        Start-Sleep -Seconds 5
        
        # 检查后端状态
        $backendState = (Get-Job -Id $backendJob.Id).State
        if ($backendState -eq "Failed" -or $backendState -eq "Stopped") {
            Write-Host "❌ 后端服务已停止" -ForegroundColor Red
            break
        }
        
        # 检查前端状态
        $frontendState = (Get-Job -Id $frontendJob.Id).State
        if ($frontendState -eq "Failed" -or $frontendState -eq "Stopped") {
            Write-Host "❌ 前端服务已停止" -ForegroundColor Red
            break
        }
    }
}
finally {
    # 清理
    Write-Host ""
    Write-Host "正在停止服务..." -ForegroundColor Yellow
    Stop-Job -Id $backendJob.Id -ErrorAction SilentlyContinue
    Stop-Job -Id $frontendJob.Id -ErrorAction SilentlyContinue
    Remove-Job -Id $backendJob.Id -ErrorAction SilentlyContinue
    Remove-Job -Id $frontendJob.Id -ErrorAction SilentlyContinue
    Write-Host "✓ 服务已停止" -ForegroundColor Green
}
