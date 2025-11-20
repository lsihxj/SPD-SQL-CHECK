# SQL检查工具 - Windows安装脚本
# PowerShell脚本

Write-Host "==================================" -ForegroundColor Cyan
Write-Host "SQL检查工具 - 安装向导" -ForegroundColor Cyan
Write-Host "==================================" -ForegroundColor Cyan
Write-Host ""

# 检查Python
Write-Host "检查Python环境..." -ForegroundColor Yellow
$pythonVersion = python --version 2>&1
if ($LASTEXITCODE -eq 0) {
    Write-Host "✓ 找到Python: $pythonVersion" -ForegroundColor Green
} else {
    Write-Host "✗ 未找到Python，请先安装Python 3.11+" -ForegroundColor Red
    exit 1
}

# 检查PostgreSQL
Write-Host "检查PostgreSQL..." -ForegroundColor Yellow
$psqlVersion = psql --version 2>&1
if ($LASTEXITCODE -eq 0) {
    Write-Host "✓ 找到PostgreSQL: $psqlVersion" -ForegroundColor Green
} else {
    Write-Host "⚠ 未找到PostgreSQL，请确保已安装PostgreSQL 12+" -ForegroundColor Yellow
}

# 创建虚拟环境
Write-Host ""
Write-Host "创建Python虚拟环境..." -ForegroundColor Yellow
Set-Location backend
python -m venv venv
if ($LASTEXITCODE -eq 0) {
    Write-Host "✓ 虚拟环境创建成功" -ForegroundColor Green
} else {
    Write-Host "✗ 虚拟环境创建失败" -ForegroundColor Red
    exit 1
}

# 激活虚拟环境
Write-Host "激活虚拟环境..." -ForegroundColor Yellow
.\venv\Scripts\Activate.ps1

# 安装后端依赖
Write-Host ""
Write-Host "安装后端依赖..." -ForegroundColor Yellow
pip install -r requirements.txt
if ($LASTEXITCODE -eq 0) {
    Write-Host "✓ 后端依赖安装成功" -ForegroundColor Green
} else {
    Write-Host "✗ 后端依赖安装失败" -ForegroundColor Red
    exit 1
}

# 复制环境变量文件
if (!(Test-Path ".env")) {
    Write-Host ""
    Write-Host "创建环境变量文件..." -ForegroundColor Yellow
    Copy-Item ".env.example" ".env"
    Write-Host "✓ 已创建.env文件，请根据实际情况修改配置" -ForegroundColor Green
}

# 返回项目根目录
Set-Location ..

# 初始化数据库
Write-Host ""
Write-Host "==================================" -ForegroundColor Cyan
Write-Host "数据库初始化" -ForegroundColor Cyan
Write-Host "==================================" -ForegroundColor Cyan
Write-Host ""
$initDb = Read-Host "是否现在初始化数据库？(Y/N)"

if ($initDb -eq "Y" -or $initDb -eq "y") {
    $dbUser = Read-Host "请输入PostgreSQL用户名 (默认: postgres)"
    if ([string]::IsNullOrWhiteSpace($dbUser)) {
        $dbUser = "postgres"
    }
    
    Write-Host "创建数据库SPDSQLCheck..." -ForegroundColor Yellow
    psql -U $dbUser -c "CREATE DATABASE SPDSQLCheck;" 2>$null
    
    Write-Host "执行初始化脚本..." -ForegroundColor Yellow
    psql -U $dbUser -d SPDSQLCheck -f database/init_schema.sql
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✓ 数据库初始化成功" -ForegroundColor Green
    } else {
        Write-Host "⚠ 数据库初始化可能存在问题，请检查" -ForegroundColor Yellow
    }
}

# 完成
Write-Host ""
Write-Host "==================================" -ForegroundColor Cyan
Write-Host "安装完成！" -ForegroundColor Green
Write-Host "==================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "后续步骤：" -ForegroundColor Yellow
Write-Host "1. 编辑 backend/.env 文件，配置数据库连接和加密密钥"
Write-Host "2. 在数据库中配置AI厂家和模型（通过Web界面）"
Write-Host "3. 运行后端服务："
Write-Host "   cd backend"
Write-Host "   .\venv\Scripts\Activate.ps1"
Write-Host "   python main.py"
Write-Host ""
Write-Host "4. 访问 http://localhost:8000/docs 查看API文档"
Write-Host ""
