#!/bin/bash

# DoRobot 一键部署脚本
# 目标: Orange Pi AI Pro 20T (192.168.1.100)

set -e  # 遇到错误立即退出

# 配置信息
BOARD_IP="192.168.1.100"
BOARD_USER="HwHiAiUser"
BOARD_PASSWORD="Mind@123"
BOARD_PATH="/home/HwHiAiUser/dorobot"
PROJECT_NAME="DoRobot-Preview"

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 打印函数
print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 检查网络连接
check_connection() {
    print_info "检查网络连接..."
    # 使用SSH连接测试代替ping（某些设备可能禁用ping）
    if ssh -o ConnectTimeout=5 -o BatchMode=yes $BOARD_USER@$BOARD_IP "echo 'test'" > /dev/null 2>&1; then
        print_success "网络连接正常"
    else
        print_warning "无法通过SSH连接，但继续尝试部署..."
    fi
}

# 检查SSH连接
check_ssh() {
    print_info "检查SSH连接..."
    print_warning "SSH连接需要手动输入密码，请准备好密码"
    print_success "SSH连接检查跳过，将在部署时验证"
}

# 清理项目文件
clean_project() {
    print_info "清理项目文件..."
    
    # 删除Git历史（减小包大小）
    if [ -d .git ]; then
        rm -rf .git
        print_info "已删除Git历史"
    fi
    
    # 删除Python缓存
    find . -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true
    find . -name "*.pyc" -delete 2>/dev/null || true
    find . -name ".pytest_cache" -type d -exec rm -rf {} + 2>/dev/null || true
    
    # 删除日志文件
    find . -name "*.log" -delete 2>/dev/null || true
    
    # 删除临时文件
    find . -name ".DS_Store" -delete 2>/dev/null || true
    find . -name "Thumbs.db" -delete 2>/dev/null || true
    
    print_success "项目文件清理完成"
}

# 创建部署包
create_package() {
    print_info "创建部署包..."
    
    # 创建临时目录
    TEMP_DIR="/tmp/dorobot_deploy_$$"
    mkdir -p $TEMP_DIR
    
    # 复制项目文件（排除当前目录的修改）
    rsync -av --exclude='.git' --exclude='__pycache__' --exclude='*.pyc' --exclude='.pytest_cache' --exclude='*.log' --exclude='.DS_Store' --exclude='Thumbs.db' . $TEMP_DIR/
    
    # 进入临时目录
    cd $TEMP_DIR
    
    # 创建部署包
    tar -czf /tmp/dorobot_deploy.tar.gz .
    
    # 返回原目录
    cd - > /dev/null
    
    # 清理临时目录
    rm -rf $TEMP_DIR
    
    print_success "部署包创建完成: /tmp/dorobot_deploy.tar.gz"
}

# 上传到开发板
upload_to_board() {
    print_info "上传部署包到开发板..."
    
    if sshpass -p "$BOARD_PASSWORD" scp /tmp/dorobot_deploy.tar.gz $BOARD_USER@$BOARD_IP:/tmp/; then
        print_success "部署包上传成功"
    else
        print_error "部署包上传失败"
        exit 1
    fi
}

# 在开发板上安装
install_on_board() {
    print_info "在开发板上安装DoRobot..."
    
    sshpass -p "$BOARD_PASSWORD" ssh $BOARD_USER@$BOARD_IP << 'REMOTE_SCRIPT'
        set -e
        
        echo "=== 开始安装DoRobot ==="
        
        # 停止现有服务
        echo "停止现有服务..."
        pkill -f dorobot || true
        pkill -f operating_platform || true
        
        # 备份现有版本
        if [ -d /home/HwHiAiUser/dorobot ]; then
            BACKUP_NAME="dorobot_backup_$(date +%Y%m%d_%H%M%S)"
            mv /home/HwHiAiUser/dorobot /home/HwHiAiUser/$BACKUP_NAME
            echo "已备份现有版本到: $BACKUP_NAME"
        fi
        
        # 创建新目录
        mkdir -p /home/HwHiAiUser/dorobot
        cd /home/HwHiAiUser/dorobot
        
        # 解压新版本
        echo "解压新版本..."
        tar -xzf /tmp/dorobot_deploy.tar.gz
        
        # 检查Python环境
        echo "检查Python环境..."
        if command -v python3 &> /dev/null; then
            PYTHON_CMD="python3"
        elif command -v python &> /dev/null; then
            PYTHON_CMD="python"
        else
            echo "错误: 未找到Python环境"
            exit 1
        fi
        
        # 检查pip
        if ! command -v pip3 &> /dev/null && ! command -v pip &> /dev/null; then
            echo "错误: 未找到pip"
            exit 1
        fi
        
        # 安装依赖
        echo "安装Python依赖..."
        if [ -f pyproject.toml ]; then
            pip3 install -e . || pip install -e .
        else
            echo "警告: 未找到pyproject.toml文件"
        fi
        
        # 设置权限
        echo "设置文件权限..."
        chmod +x scripts/*.sh 2>/dev/null || true
        chmod +x operating_platform/robot/components/*/main.py 2>/dev/null || true
        
        # 验证安装
        echo "验证安装..."
        if $PYTHON_CMD -c "import operating_platform; print('DoRobot安装成功!')" 2>/dev/null; then
            echo "=== DoRobot安装完成 ==="
        else
            echo "警告: 安装验证失败，但文件已部署"
        fi
        
        # 清理临时文件
        rm -f /tmp/dorobot_deploy.tar.gz
        
        echo "安装完成！"
        echo "项目路径: /home/HwHiAiUser/dorobot"
        echo "运行命令: cd /home/HwHiAiUser/dorobot && python3 -m operating_platform.core.main --help"
REMOTE_SCRIPT
    
    if [ $? -eq 0 ]; then
        print_success "DoRobot安装完成"
    else
        print_error "安装过程中出现错误"
        exit 1
    fi
}

# 验证部署
verify_deployment() {
    print_info "验证部署..."
    
    sshpass -p "$BOARD_PASSWORD" ssh $BOARD_USER@$BOARD_IP << 'REMOTE_SCRIPT'
        cd /home/HwHiAiUser/dorobot
        
        echo "=== 部署验证 ==="
        echo "项目路径: $(pwd)"
        echo "文件数量: $(find . -type f | wc -l)"
        
        # 检查关键文件
        if [ -f "operating_platform/core/main.py" ]; then
            echo "✓ 主程序文件存在"
        else
            echo "✗ 主程序文件缺失"
        fi
        
        if [ -f "pyproject.toml" ]; then
            echo "✓ 项目配置文件存在"
        else
            echo "✗ 项目配置文件缺失"
        fi
        
        # 测试Python导入
        if python3 -c "import operating_platform" 2>/dev/null; then
            echo "✓ Python模块导入成功"
        else
            echo "✗ Python模块导入失败"
        fi
        
        echo "=== 验证完成 ==="
REMOTE_SCRIPT
}

# 显示使用说明
show_usage() {
    print_info "DoRobot部署完成！"
    echo ""
    echo "使用说明:"
    echo "1. SSH到开发板: ssh $BOARD_USER@$BOARD_IP"
    echo "2. 进入项目目录: cd /home/HwHiAiUser/dorobot"
    echo "3. 查看帮助: python3 -m operating_platform.core.main --help"
    echo "4. 开始录制: python3 -m operating_platform.core.main --record.repo_id=test_data"
    echo ""
    echo "项目路径: /home/HwHiAiUser/dorobot"
    echo "日志文件: /home/HwHiAiUser/dorobot/logs/"
}

# 主函数
main() {
    echo "=========================================="
    echo "    DoRobot 一键部署脚本"
    echo "    目标: Orange Pi AI Pro 20T"
    echo "=========================================="
    echo ""
    
    # 检查当前目录
    if [ ! -f "pyproject.toml" ]; then
        print_error "请在DoRobot项目根目录下运行此脚本"
        exit 1
    fi
    
    # 执行部署步骤
    check_connection
    check_ssh
    clean_project
    create_package
    upload_to_board
    install_on_board
    verify_deployment
    show_usage
    
    print_success "部署完成！"
}

# 运行主函数
main "$@"
