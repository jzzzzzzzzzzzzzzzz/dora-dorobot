#!/bin/bash

# DoRobot SO101 正确部署脚本
# 按照 README_SO101.md 的完整流程部署

set -e

# 配置信息
BOARD_IP="192.168.1.100"
BOARD_USER="HwHiAiUser"
BOARD_PASSWORD="Mind@123"
PROJECT_NAME="DoRobot-Preview"

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

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

# 检查当前目录
check_project() {
    print_info "检查项目目录..."
    if [ ! -f "README_SO101.md" ]; then
        print_error "请在DoRobot项目根目录下运行此脚本"
        exit 1
    fi
    print_success "项目目录检查通过"
}

# 清理项目文件
clean_project() {
    print_info "清理项目文件..."
    
    # 删除Git历史
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
    TEMP_DIR="/tmp/dorobot_so101_deploy_$$"
    mkdir -p $TEMP_DIR
    
    # 复制项目文件
    rsync -av --exclude='.git' --exclude='__pycache__' --exclude='*.pyc' --exclude='.pytest_cache' --exclude='*.log' --exclude='.DS_Store' --exclude='Thumbs.db' . $TEMP_DIR/
    
    # 进入临时目录
    cd $TEMP_DIR
    
    # 创建部署包
    tar -czf /tmp/dorobot_so101_deploy.tar.gz .
    
    # 返回原目录
    cd - > /dev/null
    
    # 清理临时目录
    rm -rf $TEMP_DIR
    
    print_success "部署包创建完成: /tmp/dorobot_so101_deploy.tar.gz"
}

# 上传到开发板
upload_to_board() {
    print_info "上传部署包到开发板..."
    
    if sshpass -p "$BOARD_PASSWORD" scp /tmp/dorobot_so101_deploy.tar.gz $BOARD_USER@$BOARD_IP:/tmp/; then
        print_success "部署包上传成功"
    else
        print_error "部署包上传失败"
        exit 1
    fi
}

# 在开发板上完整安装
install_on_board() {
    print_info "在开发板上完整安装DoRobot SO101..."
    
    sshpass -p "$BOARD_PASSWORD" ssh $BOARD_USER@$BOARD_IP << 'REMOTE_SCRIPT'
        set -e
        
        echo "=== 开始完整安装DoRobot SO101 ==="
        
        # 停止现有服务
        echo "停止现有服务..."
        pkill -f dorobot || true
        pkill -f operating_platform || true
        
        # 备份现有版本
        if [ -d /home/HwHiAiUser/DoRobot-Preview ]; then
            BACKUP_NAME="DoRobot-Preview_backup_$(date +%Y%m%d_%H%M%S)"
            mv /home/HwHiAiUser/DoRobot-Preview /home/HwHiAiUser/$BACKUP_NAME
            echo "已备份现有版本到: $BACKUP_NAME"
        fi
        
        # 创建项目目录
        mkdir -p /home/HwHiAiUser/DoRobot-Preview
        cd /home/HwHiAiUser/DoRobot-Preview
        
        # 解压新版本
        echo "解压新版本..."
        tar -xzf /tmp/dorobot_so101_deploy.tar.gz
        
        # 检查conda是否安装
        echo "检查conda环境..."
        if ! command -v conda &> /dev/null; then
            echo "错误: 未找到conda，请先安装conda"
            exit 1
        fi
        
        # 1. 创建DoRobot主环境 (op)
        echo "创建DoRobot主环境 (op)..."
        if conda env list | grep -q "op"; then
            echo "环境 'op' 已存在，跳过创建"
        else
            conda create --name op python==3.11 -y
            echo "环境 'op' 创建完成"
        fi
        
        # 2. 创建SO101机器人环境 (dr-robot-so101)
        echo "创建SO101机器人环境 (dr-robot-so101)..."
        if conda env list | grep -q "dr-robot-so101"; then
            echo "环境 'dr-robot-so101' 已存在，跳过创建"
        else
            conda create --name dr-robot-so101 python==3.10 -y
            echo "环境 'dr-robot-so101' 创建完成"
        fi
        
        # 3. 安装DoRobot主项目
        echo "安装DoRobot主项目..."
        source ~/miniconda3/etc/profile.d/conda.sh
        conda activate op
        
        # 安装项目
        pip install -e .
        
        # 安装PyTorch (CPU版本，适合开发板)
        echo "安装PyTorch (CPU版本)..."
        pip install torch==2.6.0 torchvision==0.21.0 torchaudio==2.6.0 --index-url https://download.pytorch.org/whl/cpu
        
        # 安装音频库
        echo "安装音频库..."
        sudo apt update
        sudo apt install -y libportaudio2
        
        # 4. 安装SO101机器人环境
        echo "安装SO101机器人环境..."
        conda activate dr-robot-so101
        
        # 进入SO101目录并安装
        cd operating_platform/robot/robots/so101_v1
        pip install -e .
        
        # 返回项目根目录
        cd /home/HwHiAiUser/DoRobot-Preview
        
        # 设置权限
        echo "设置文件权限..."
        chmod +x scripts/*.sh 2>/dev/null || true
        chmod +x operating_platform/robot/components/*/main.py 2>/dev/null || true
        
        # 验证安装
        echo "验证安装..."
        conda activate op
        if python -c "import operating_platform; print('DoRobot主环境安装成功!')" 2>/dev/null; then
            echo "✓ DoRobot主环境验证通过"
        else
            echo "✗ DoRobot主环境验证失败"
        fi
        
        conda activate dr-robot-so101
        if python -c "import dr_robot_so101; print('SO101机器人环境安装成功!')" 2>/dev/null; then
            echo "✓ SO101机器人环境验证通过"
        else
            echo "✗ SO101机器人环境验证失败"
        fi
        
        # 清理临时文件
        rm -f /tmp/dorobot_so101_deploy.tar.gz
        
        echo "=== DoRobot SO101完整安装完成 ==="
        echo ""
        echo "环境信息:"
        echo "- DoRobot主环境: conda activate op"
        echo "- SO101机器人环境: conda activate dr-robot-so101"
        echo ""
        echo "使用说明:"
        echo "1. 校准leader arm: cd operating_platform/robot/components/arm_normal_so101_v1/ && conda activate dr-robot-so101 && dora run dora_calibrate_leader.yml"
        echo "2. 校准follower arm: cd operating_platform/robot/components/arm_normal_so101_v1/ && conda activate dr-robot-so101 && dora run dora_calibrate_follower.yml"
        echo "3. 遥操作: cd operating_platform/robot/components/arm_normal_so101_v1/ && conda activate dr-robot-so101 && dora run dora_teleoperate_arm.yml"
        echo "4. 录制数据: cd operating_platform/robot/robots/so101_v1 && conda activate dr-robot-so101 && dora run dora_teleoperate_dataflow.yml"
        echo "5. 运行CLI: bash scripts/run_so101_cli.sh"
REMOTE_SCRIPT
    
    if [ $? -eq 0 ]; then
        print_success "DoRobot SO101完整安装完成"
    else
        print_error "安装过程中出现错误"
        exit 1
    fi
}

# 显示使用说明
show_usage() {
    print_info "DoRobot SO101部署完成！"
    echo ""
    echo "=========================================="
    echo "    完整使用流程"
    echo "=========================================="
    echo ""
    echo "1. SSH到开发板:"
    echo "   ssh $BOARD_USER@$BOARD_IP"
    echo ""
    echo "2. 进入项目目录:"
    echo "   cd /home/HwHiAiUser/DoRobot-Preview"
    echo ""
    echo "3. 校准机械臂:"
    echo "   # 校准leader arm"
    echo "   cd operating_platform/robot/components/arm_normal_so101_v1/"
    echo "   conda activate dr-robot-so101"
    echo "   dora run dora_calibrate_leader.yml"
    echo ""
    echo "   # 校准follower arm"
    echo "   dora run dora_calibrate_follower.yml"
    echo ""
    echo "4. 遥操作测试:"
    echo "   dora run dora_teleoperate_arm.yml"
    echo ""
    echo "5. 录制数据:"
    echo "   cd ../../robots/so101_v1"
    echo "   dora run dora_teleoperate_dataflow.yml"
    echo ""
    echo "6. 运行CLI (新终端):"
    echo "   bash scripts/run_so101_cli.sh"
    echo ""
    echo "项目路径: /home/HwHiAiUser/DoRobot-Preview"
    echo "环境: op (主环境), dr-robot-so101 (机器人环境)"
}

# 主函数
main() {
    echo "=========================================="
    echo "    DoRobot SO101 完整部署脚本"
    echo "    目标: Orange Pi AI Pro 20T"
    echo "=========================================="
    echo ""
    
    check_project
    clean_project
    create_package
    upload_to_board
    install_on_board
    show_usage
    
    print_success "部署完成！"
}

# 运行主函数
main "$@"
