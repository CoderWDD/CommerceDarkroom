#!/usr/bin/env bash
# ==============================================================================
# 🛒 电商视觉工坊 (Ecommerce Studio) - 快速优雅停止脚本
# 支持: PID 精准终止、端口残余检测、树状子进程清理、强退备用与环境复位
# ==============================================================================

set -o pipefail

# 脚本所在工程根目录
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "${PROJECT_ROOT}"

# 运行日志与 PID 目录
LOGS_DIR="${PROJECT_ROOT}/logs"
BACKEND_PID_FILE="${LOGS_DIR}/backend.pid"
FRONTEND_PID_FILE="${LOGS_DIR}/frontend.pid"

FORCE=false

# ------------------------------------------------------------------------------
# 终端彩色输出
# ------------------------------------------------------------------------------
if [ -t 1 ]; then
    BOLD='\033[1m'
    DIM='\033[2m'
    RED='\033[0;31m'
    GREEN='\033[0;32m'
    YELLOW='\033[0;33m'
    CYAN='\033[0;36m'
    WHITE='\033[1;37m'
    NC='\033[0m'
else
    BOLD=''
    DIM=''
    RED=''
    GREEN=''
    YELLOW=''
    CYAN=''
    WHITE=''
    NC=''
fi

log_info() {
    echo -e "${CYAN}[INFO]${NC} $*"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $*"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $*"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $*"
}

# ------------------------------------------------------------------------------
# 帮助信息与参数处理
# ------------------------------------------------------------------------------
show_help() {
    cat <<EOF
电商视觉工坊 (Ecommerce Studio) 服务停止脚本

用法:
  ./stop.sh [选项]

选项:
  -f, --force    立即发送 SIGKILL 强制终止所有相关服务与端口进程
  -h, --help     显示帮助信息并退出
EOF
}

while [[ $# -gt 0 ]]; do
    case "$1" in
        -f|--force)
            FORCE=true
            shift
            ;;
        -h|--help)
            show_help
            exit 0
            ;;
        *)
            log_error "未知选项: $1"
            show_help
            exit 1
            ;;
    esac
done

# ------------------------------------------------------------------------------
# 获取端口占用 PID 集合
# ------------------------------------------------------------------------------
get_port_pids() {
    local port="$1"
    local pids=""
    if command -v fuser >/dev/null 2>&1; then
        pids=$(fuser "${port}/tcp" 2>/dev/null | tr -s ' ' '\n' | grep -E '^[0-9]+$' || true)
    elif command -v ss >/dev/null 2>&1; then
        pids=$(ss -lptn "sport = :${port}" 2>/dev/null | grep -oP 'pid=\K[0-9]+' || true)
    elif command -v lsof >/dev/null 2>&1; then
        pids=$(lsof -ti ":${port}" -sTCP:LISTEN 2>/dev/null || true)
    fi
    echo "$pids"
}

# 递归终止进程及其子树
kill_tree() {
    local parent="$1"
    local sig="$2"
    if [ -z "$parent" ] || ! kill -0 "$parent" 2>/dev/null; then
        return 0
    fi
    local children
    children=$(pgrep -P "$parent" 2>/dev/null || true)
    for child in $children; do
        kill_tree "$child" "$sig"
    done
    kill "-$sig" "$parent" 2>/dev/null || true
}

# ------------------------------------------------------------------------------
# 主停止逻辑
# ------------------------------------------------------------------------------
main() {
    echo -e "${BOLD}${WHITE}正在停止电商视觉工坊所有服务...${NC}"
    
    local any_action=false
    local sig="TERM"
    [ "$FORCE" = "true" ] && sig="KILL"
    
    # 1. 根据 PID 文件终止后端
    if [ -f "${BACKEND_PID_FILE}" ]; then
        local bpid
        bpid=$(cat "${BACKEND_PID_FILE}" 2>/dev/null || true)
        if [ -n "$bpid" ] && kill -0 "$bpid" 2>/dev/null; then
            log_info "发现后端服务 PID: ${bpid}，正在停止..."
            kill_tree "$bpid" "$sig"
            any_action=true
        fi
        rm -f "${BACKEND_PID_FILE}" 2>/dev/null || true
    fi
    
    # 2. 根据 PID 文件终止前端
    if [ -f "${FRONTEND_PID_FILE}" ]; then
        local fpid
        fpid=$(cat "${FRONTEND_PID_FILE}" 2>/dev/null || true)
        if [ -n "$fpid" ] && kill -0 "$fpid" 2>/dev/null; then
            log_info "发现前端服务 PID: ${fpid}，正在停止..."
            kill_tree "$fpid" "$sig"
            any_action=true
        fi
        rm -f "${FRONTEND_PID_FILE}" 2>/dev/null || true
    fi
    
    # 3. 检查并清理端口 8000 与 3000 残留进程
    for port in 8000 3000; do
        local pids
        pids=$(get_port_pids "$port")
        if [ -n "$pids" ]; then
            for p in $pids; do
                if kill -0 "$p" 2>/dev/null; then
                    log_warn "发现端口 ${port} 仍有占用进程 (PID: ${p})，正在清理..."
                    kill_tree "$p" "$sig"
                    any_action=true
                fi
            done
        fi
    done
    
    # 4. 如果非强制模式，等待最多 4 秒确认退出
    if [ "$FORCE" = "false" ] && [ "$any_action" = "true" ]; then
        local waited=0
        while [ $waited -lt 4 ]; do
            local p8000
            local p3000
            p8000=$(get_port_pids 8000)
            p3000=$(get_port_pids 3000)
            if [ -z "$p8000" ] && [ -z "$p3000" ]; then
                break
            fi
            sleep 1
            waited=$((waited + 1))
        done
        
        # 若仍有残余，升级为 SIGKILL
        local rest8000
        local rest3000
        rest8000=$(get_port_pids 8000)
        rest3000=$(get_port_pids 3000)
        if [ -n "$rest8000" ] || [ -n "$rest3000" ]; then
            log_warn "部分服务未及时退出，升级为 SIGKILL 强行终止..."
            for rp in $rest8000 $rest3000; do
                kill_tree "$rp" "KILL"
            done
            sleep 1
        fi
    fi
    
    # 5. 最终验证
    local final8000
    local final3000
    final8000=$(get_port_pids 8000)
    final3000=$(get_port_pids 3000)
    
    if [ -n "$final8000" ] || [ -n "$final3000" ]; then
        log_error "部分端口未能完全释放 (8000: [${final8000}], 3000: [${final3000}])，建议执行 ./stop.sh -f 强制清理。"
        exit 1
    fi
    
    if [ "$any_action" = "true" ]; then
        log_success "电商视觉工坊前后端服务已全部安全停止，端口 8000 / 3000 已完全释放。"
    else
        log_info "未检测到正在运行的电商视觉工坊服务或端口占用，无需重复停止。"
    fi
}

main
