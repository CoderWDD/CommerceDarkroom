#!/usr/bin/env bash
# ==============================================================================
# 🛒 电商视觉工坊 (Ecommerce Studio) - 现代化全栈一键启动脚本
# 支持: 环境自检、依赖检查与静默安装、端口冲突排查、健康轮询、信号优雅捕获与安全退出
# ==============================================================================

set -o pipefail

# 脚本所在工程根目录
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "${PROJECT_ROOT}"

# 运行日志与 PID 存放目录
LOGS_DIR="${PROJECT_ROOT}/logs"
BACKEND_LOG="${LOGS_DIR}/backend.log"
FRONTEND_LOG="${LOGS_DIR}/frontend.log"
BACKEND_PID_FILE="${LOGS_DIR}/backend.pid"
FRONTEND_PID_FILE="${LOGS_DIR}/frontend.pid"

# 进程变量与状态标志
BACKEND_PID=""
FRONTEND_PID=""
CLEANED_UP=false
DAEMON_MODE=false
FORCE_KILL=false
PYTHON_CMD=""

# ------------------------------------------------------------------------------
# 终端彩色与高亮格式化
# ------------------------------------------------------------------------------
if [ -t 1 ]; then
    BOLD='\033[1m'
    DIM='\033[2m'
    RED='\033[0;31m'
    GREEN='\033[0;32m'
    YELLOW='\033[0;33m'
    BLUE='\033[0;34m'
    MAGENTA='\033[0;35m'
    CYAN='\033[0;36m'
    WHITE='\033[1;37m'
    NC='\033[0m' # No Color
else
    BOLD=''
    DIM=''
    RED=''
    GREEN=''
    YELLOW=''
    BLUE=''
    MAGENTA=''
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

log_step() {
    echo -e "\n${BOLD}${MAGENTA}==>${NC} ${BOLD}$*${NC}"
}

# ------------------------------------------------------------------------------
# 命令行参数解析
# ------------------------------------------------------------------------------
show_help() {
    cat <<EOF
电商视觉工坊 (Ecommerce Studio) 一键启动脚本

用法:
  ./start.sh [选项]

选项:
  -d, --daemon       后台守护模式运行（健康就绪后脚本退出，服务保持后台常驻）
  -f, --force        端口冲突时自动强制清理，无需手动确认
  -h, --help         显示帮助信息并退出

示例:
  ./start.sh              # 默认前台交互模式运行，按 Ctrl+C 优雅停止
  ./start.sh --daemon     # 后台运行服务，后续可用 ./stop.sh 停止
  ./start.sh --force      # 自动清理 8000/3000 冲突端口并启动
EOF
}

while [[ $# -gt 0 ]]; do
    case "$1" in
        -d|--daemon|--background)
            DAEMON_MODE=true
            shift
            ;;
        -f|--force)
            FORCE_KILL=true
            shift
            ;;
        -h|--help)
            show_help
            exit 0
            ;;
        *)
            log_error "未知参数: $1"
            show_help
            exit 1
            ;;
    esac
done

# ------------------------------------------------------------------------------
# 彩色欢迎界面
# ------------------------------------------------------------------------------
print_banner() {
    echo -e "${CYAN}"
    cat <<'EOF'
  ███████╗ ██████╗ ██████╗ ███╗   ███╗███╗   ███╗███████╗██████╗  ██████╗███████╗
  ██╔════╝██╔════╝██╔═══██╗████╗ ████║████╗ ████║██╔════╝██╔══██╗██╔════╝██╔════╝
  █████╗  ██║     ██║   ██║██╔████╔██║██╔████╔██║█████╗  ██████╔╝██║     █████╗  
  ██╔══╝  ██║     ██║   ██║██║╚██╔╝██║██║╚██╔╝██║██╔══╝  ██╔══██╗██║     ██╔══╝  
  ███████╗╚██████╗╚██████╔╝██║ ╚═╝ ██║██║ ╚═╝ ██║███████╗██║  ██║╚██████╗███████╗
  ╚══════╝ ╚═════╝ ╚═════╝ ╚═╝     ╚═╝╚═╝     ╚═╝╚══════╝╚═╝  ╚═╝ ╚═════╝╚══════╝
EOF
    echo -e "${BOLD}${WHITE}       🛒 电商视觉工坊 (Ecommerce Studio) · 全栈一键运行控制台${NC}"
    echo -e "${DIM}========================================================================${NC}"
    echo -e "  ${WHITE}项目根目录:${NC} ${PROJECT_ROOT}"
    echo -e "  ${WHITE}系统信息:  ${NC} $(uname -s) $(uname -r) ($(uname -m))"
    echo -e "  ${WHITE}运行模式:  ${NC} $([ "$DAEMON_MODE" = "true" ] && echo -e "${YELLOW}后台守护模式 (daemon)${NC}" || echo -e "${GREEN}前台交互模式 (Ctrl+C 优雅退出)${NC}")"
    echo -e "${DIM}========================================================================${NC}"
}

# ------------------------------------------------------------------------------
# 端口检测与进程树清理工具函数
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

kill_pids() {
    local pids="$1"
    local sig="${2:-TERM}"
    for pid in $pids; do
        if [ -n "$pid" ] && kill -0 "$pid" 2>/dev/null; then
            kill "-$sig" "$pid" 2>/dev/null || true
        fi
    done
}

kill_tree() {
    local parent="$1"
    local sig="${2:-TERM}"
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

ensure_port_free() {
    local port="$1"
    local service_name="$2"
    local pids
    pids=$(get_port_pids "$port")
    
    if [ -z "$pids" ]; then
        log_success "端口 ${port} (${service_name}) 可用"
        return 0
    fi
    
    log_warn "${service_name} 端口 ${port} 当前已被占用，占用进程 PID: [${pids}]"
    
    local should_clean=false
    if [ "$FORCE_KILL" = "true" ]; then
        should_clean=true
    elif [ -t 0 ]; then
        echo -en "${YELLOW}[提示] 是否自动清理端口 ${port} 的占用进程以保证服务启动? [Y/n]: ${NC}"
        read -r choice
        case "$choice" in
            [yY][eE][sS]|[yY]|"")
                should_clean=true
                ;;
            *)
                should_clean=false
                ;;
        esac
    else
        log_info "非交互式运行环境，自动尝试释放端口 ${port}..."
        should_clean=true
    fi
    
    if [ "$should_clean" = "true" ]; then
        log_info "正在尝试优雅终止端口 ${port} 上的冲突进程..."
        for p in $pids; do
            kill_tree "$p" "TERM"
        done
        
        local waited=0
        while [ $waited -lt 5 ]; do
            sleep 1
            waited=$((waited + 1))
            pids=$(get_port_pids "$port")
            [ -z "$pids" ] && break
        done
        
        if [ -n "$pids" ]; then
            log_warn "进程未在预期时间内退出，正在发送 SIGKILL 强制释放..."
            for p in $pids; do
                kill_tree "$p" "KILL"
            done
            sleep 1
        fi
        
        pids=$(get_port_pids "$port")
        if [ -n "$pids" ]; then
            log_error "端口 ${port} 释放失败，残留 PID: ${pids}。请手动终止后重试。"
            exit 1
        fi
        log_success "端口 ${port} 已成功清理并就绪！"
    else
        log_error "端口 ${port} 被占用，启动取消。请释放端口后重试或使用 -f / --force 参数。"
        exit 1
    fi
}

# ------------------------------------------------------------------------------
# 环境检测 (Python 3.10+ / Node.js 18+)
# ------------------------------------------------------------------------------
check_environment() {
    log_step "环境自检: 正在检测运行时引擎与核心工具链..."
    
    # 1. 检测 Python 3.10+
    if command -v python3 >/dev/null 2>&1; then
        PYTHON_CMD="python3"
    elif command -v python >/dev/null 2>&1; then
        PYTHON_CMD="python"
    else
        log_error "未检测到 Python 解释器，请先安装 Python 3.10+。"
        exit 1
    fi
    
    local py_ver
    py_ver=$($PYTHON_CMD -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}")' 2>/dev/null || true)
    local py_check
    py_check=$($PYTHON_CMD -c 'import sys; print(1 if sys.version_info >= (3, 10) else 0)' 2>/dev/null || echo 0)
    
    if [ "$py_check" != "1" ]; then
        log_error "检测到 Python 版本为 ${py_ver}，电商视觉工坊需要 Python 3.10 或更高版本。"
        exit 1
    fi
    log_success "Python 环境就绪: ${PYTHON_CMD} (v${py_ver})"
    
    # 2. 检测 Node.js 18+ 与 npm
    if ! command -v node >/dev/null 2>&1; then
        log_error "未检测到 Node.js，请先安装 Node.js 18+。"
        exit 1
    fi
    if ! command -v npm >/dev/null 2>&1; then
        log_error "未检测到 npm 包管理器，请先安装 npm。"
        exit 1
    fi
    
    local node_ver
    node_ver=$(node -v 2>/dev/null | tr -d 'v' || true)
    local node_major
    node_major=$(echo "$node_ver" | cut -d. -f1)
    
    if [ -z "$node_major" ] || [ "$node_major" -lt 18 ]; then
        log_error "检测到 Node.js 版本为 v${node_ver}，电商视觉工坊前端需要 Node.js 18 或更高版本。"
        exit 1
    fi
    local npm_ver
    npm_ver=$(npm -v 2>/dev/null || true)
    log_success "Node.js 环境就绪: node v${node_ver}, npm v${npm_ver}"
    
    # 3. 检测 curl (健康检查必需)
    if ! command -v curl >/dev/null 2>&1; then
        log_error "系统缺少 curl 工具，无法进行服务健康轮询，请先安装 curl。"
        exit 1
    fi
}

# ------------------------------------------------------------------------------
# 依赖检查与自动安装
# ------------------------------------------------------------------------------
check_dependencies() {
    log_step "依赖自检: 检查前后端项目依赖完整性..."
    
    # Python 核心依赖检测
    local py_deps_ok
    py_deps_ok=$($PYTHON_CMD -c "import fastapi, uvicorn, sse_starlette, httpx, pydantic, dotenv; print(1)" 2>/dev/null || echo 0)
    
    if [ "$py_deps_ok" != "1" ]; then
        log_warn "检测到缺少 Python 必要核心依赖，正在自动通过 pip 安装..."
        local req_file="${PROJECT_ROOT}/ecommerce_studio/requirements.txt"
        if [ -f "$req_file" ]; then
            $PYTHON_CMD -m pip install -r "$req_file" || {
                log_error "Python 依赖自动安装失败，请手动执行: pip install -r ${req_file}"
                exit 1
            }
            log_success "Python 依赖安装完成。"
        else
            log_error "未找到 requirements.txt 文件: ${req_file}"
            exit 1
        fi
    else
        log_success "Python 核心依赖已满足。"
    fi
    
    # 前端 node_modules 检测
    local web_modules_dir="${PROJECT_ROOT}/ecommerce_studio_web/node_modules"
    if [ ! -d "$web_modules_dir" ]; then
        log_warn "检测到前端依赖未安装 (${web_modules_dir} 不存在)，正在执行 npm install..."
        (
            cd "${PROJECT_ROOT}/ecommerce_studio_web" && npm install
        ) || {
            log_error "前端依赖安装失败，请手动进入 ecommerce_studio_web 目录执行 npm install 排查。"
            exit 1
        }
        log_success "前端 npm 依赖安装完成。"
    else
        log_success "前端 node_modules 依赖已就绪。"
    fi
}

# ------------------------------------------------------------------------------
# 优雅关闭信号捕获与资源回收
# ------------------------------------------------------------------------------
cleanup() {
    local exit_code=$?
    # 阻止信号重入
    trap - SIGINT SIGTERM EXIT
    
    if [ "$CLEANED_UP" = "true" ]; then
        exit "$exit_code"
    fi
    CLEANED_UP=true
    
    echo ""
    log_step "收到终止信号，正在优雅关闭电商视觉工坊所有服务..."
    
    # 优雅关闭后端
    if [ -n "$BACKEND_PID" ] && kill -0 "$BACKEND_PID" 2>/dev/null; then
        log_info "正在停止后端 FastAPI 服务 (PID: ${BACKEND_PID})..."
        kill_tree "$BACKEND_PID" "TERM"
    fi
    
    # 优雅关闭前端
    if [ -n "$FRONTEND_PID" ] && kill -0 "$FRONTEND_PID" 2>/dev/null; then
        log_info "正在停止前端 Next.js 服务 (PID: ${FRONTEND_PID})..."
        kill_tree "$FRONTEND_PID" "TERM"
    fi
    
    # 等待进程释放资源 (至多 4 秒)
    local waited=0
    while [ $waited -lt 4 ]; do
        local still_running=false
        [ -n "$BACKEND_PID" ] && kill -0 "$BACKEND_PID" 2>/dev/null && still_running=true
        [ -n "$FRONTEND_PID" ] && kill -0 "$FRONTEND_PID" 2>/dev/null && still_running=true
        local p8000
        local p3000
        p8000=$(get_port_pids 8000)
        p3000=$(get_port_pids 3000)
        if [ -n "$p8000" ] || [ -n "$p3000" ]; then
            still_running=true
        fi
        [ "$still_running" = "false" ] && break
        sleep 1
        waited=$((waited + 1))
    done
    
    # 对超时未退出的进程进行强制清理
    if [ -n "$BACKEND_PID" ] && kill -0 "$BACKEND_PID" 2>/dev/null; then
        kill_tree "$BACKEND_PID" "KILL"
    fi
    if [ -n "$FRONTEND_PID" ] && kill -0 "$FRONTEND_PID" 2>/dev/null; then
        kill_tree "$FRONTEND_PID" "KILL"
    fi
    
    # 扫描并清理残留端口
    local residual_8000
    residual_8000=$(get_port_pids 8000)
    [ -n "$residual_8000" ] && kill_pids "$residual_8000" "KILL"
    
    local residual_3000
    residual_3000=$(get_port_pids 3000)
    [ -n "$residual_3000" ] && kill_pids "$residual_3000" "KILL"
    
    # 移除 PID 标识文件
    rm -f "${BACKEND_PID_FILE}" "${FRONTEND_PID_FILE}" 2>/dev/null || true
    
    log_success "所有服务子进程已优雅关闭，端口 8000 / 3000 已完全释放。再会！"
    exit "$exit_code"
}

# 注册信号捕获
trap 'cleanup' SIGINT SIGTERM EXIT

# ------------------------------------------------------------------------------
# 启动前后端服务
# ------------------------------------------------------------------------------
start_services() {
    log_step "启动服务: 并发拉起后端 FastAPI 与前端 Next.js 服务..."
    
    mkdir -p "${LOGS_DIR}"
    
    # 清空或初始化日志
    > "${BACKEND_LOG}"
    > "${FRONTEND_LOG}"
    
    # 1. 启动后端
    log_info "正在启动后端服务 (FastAPI / 端口 8000)..."
    (
        cd "${PROJECT_ROOT}"
        exec nohup "$PYTHON_CMD" ecommerce_studio/server.py --host 0.0.0.0 --port 8000 </dev/null
    ) >> "${BACKEND_LOG}" 2>&1 &
    BACKEND_PID=$!
    echo "$BACKEND_PID" > "${BACKEND_PID_FILE}"
    log_info "后端服务已启动 (PID: ${BACKEND_PID})，实时日志: ${BACKEND_LOG}"
    
    # 2. 启动前端
    log_info "正在启动前端服务 (Next.js / 端口 3000)..."
    (
        cd "${PROJECT_ROOT}/ecommerce_studio_web"
        exec nohup npm run dev </dev/null
    ) >> "${FRONTEND_LOG}" 2>&1 &
    FRONTEND_PID=$!
    echo "$FRONTEND_PID" > "${FRONTEND_PID_FILE}"
    log_info "前端服务已启动 (PID: ${FRONTEND_PID})，实时日志: ${FRONTEND_LOG}"
}

# ------------------------------------------------------------------------------
# 服务健康轮询
# ------------------------------------------------------------------------------
wait_for_health() {
    log_step "健康检测: 轮询等待前后端网关就绪..."
    
    local timeout=60
    local elapsed=0
    local backend_ready=false
    local frontend_ready=false
    
    while [ $elapsed -lt $timeout ]; do
        # 进程存活性探测 (Fail-fast)
        if [ "$backend_ready" = "false" ] && ! kill -0 "$BACKEND_PID" 2>/dev/null; then
            echo ""
            log_error "后端服务异常退出！最后 25 行日志如下:"
            echo -e "${DIM}------------------------------------------------------------${NC}"
            tail -n 25 "${BACKEND_LOG}" 2>/dev/null || true
            echo -e "${DIM}------------------------------------------------------------${NC}"
            exit 1
        fi
        
        if [ "$frontend_ready" = "false" ] && ! kill -0 "$FRONTEND_PID" 2>/dev/null; then
            echo ""
            log_error "前端服务异常退出！最后 25 行日志如下:"
            echo -e "${DIM}------------------------------------------------------------${NC}"
            tail -n 25 "${FRONTEND_LOG}" 2>/dev/null || true
            echo -e "${DIM}------------------------------------------------------------${NC}"
            exit 1
        fi
        
        # 轮询后端健康端点
        if [ "$backend_ready" = "false" ]; then
            if curl -s -f -m 2 http://127.0.0.1:8000/api/v1/studio/health >/dev/null 2>&1; then
                backend_ready=true
                echo ""
                log_success "后端 FastAPI 服务就绪: http://127.0.0.1:8000 (耗时: ${elapsed}s)"
            fi
        fi
        
        # 轮询前端就绪状态
        if [ "$frontend_ready" = "false" ]; then
            local status_code
            status_code=$(curl -s -m 2 -o /dev/null -w "%{http_code}" http://127.0.0.1:3000 2>/dev/null || true)
            if [ "$status_code" = "200" ] || [ "$status_code" = "304" ]; then
                frontend_ready=true
                echo ""
                log_success "前端 Next.js 服务就绪: http://localhost:3000 (耗时: ${elapsed}s)"
            fi
        fi
        
        if [ "$backend_ready" = "true" ] && [ "$frontend_ready" = "true" ]; then
            break
        fi
        
        sleep 1
        elapsed=$((elapsed + 1))
        echo -en "${DIM}==> 等待服务就绪... [${elapsed}/${timeout}s] 后端 API: $([ "$backend_ready" = "true" ] && echo -e "${GREEN}就绪${DIM}" || echo "等待中") | 前端 Web: $([ "$frontend_ready" = "true" ] && echo -e "${GREEN}就绪${DIM}" || echo "编译中")\r${NC}"
    done
    echo ""
    
    if [ "$backend_ready" != "true" ] || [ "$frontend_ready" != "true" ]; then
        log_error "服务健康检查超时 (${timeout}s)！"
        if [ "$backend_ready" != "true" ]; then
            log_error "后端未能按时响应，日志输出:"
            tail -n 20 "${BACKEND_LOG}"
        fi
        if [ "$frontend_ready" != "true" ]; then
            log_error "前端未能按时响应，日志输出:"
            tail -n 20 "${FRONTEND_LOG}"
        fi
        exit 1
    fi
}

# ------------------------------------------------------------------------------
# 就绪成功面板展示
# ------------------------------------------------------------------------------
show_ready_dashboard() {
    echo ""
    echo -e "${GREEN}${BOLD}========================================================================${NC}"
    echo -e "${GREEN}${BOLD}  🎉 电商视觉工坊全栈服务已成功就绪！${NC}"
    echo -e "${GREEN}${BOLD}========================================================================${NC}"
    echo -e "  ${WHITE}🌐 前端视觉工作台:${NC}     ${BOLD}${GREEN}http://localhost:3000${NC}"
    echo -e "  ${WHITE}📚 后端 API 接口文档:${NC}   ${BOLD}${CYAN}http://localhost:8000/docs${NC}"
    echo -e "  ${WHITE}🩺 后端健康监控端点:${NC}   ${DIM}http://localhost:8000/api/v1/studio/health${NC}"
    echo -e "${DIM}------------------------------------------------------------------------${NC}"
    echo -e "  ${WHITE}📁 后端运行日志:${NC}       ${DIM}${BACKEND_LOG}${NC}"
    echo -e "  ${WHITE}📁 前端运行日志:${NC}       ${DIM}${FRONTEND_LOG}${NC}"
    echo -e "${DIM}------------------------------------------------------------------------${NC}"
    if [ "$DAEMON_MODE" = "true" ]; then
        echo -e "  ${YELLOW}💡 服务已在后台守护运行。${NC}"
        echo -e "  ${YELLOW}👉 停止服务请执行: ./stop.sh${NC}"
    else
        echo -e "  ${YELLOW}💡 按 [Ctrl + C] 随时停止所有前后端服务${NC}"
        echo -e "  ${DIM}👉 或在其他终端窗口执行 ./stop.sh 统一停止${NC}"
    fi
    echo -e "${GREEN}${BOLD}========================================================================${NC}"
    echo ""
}

# ------------------------------------------------------------------------------
# 主流程控制
# ------------------------------------------------------------------------------
main() {
    print_banner
    check_environment
    check_dependencies
    
    log_step "检查端口可用性..."
    ensure_port_free 8000 "后端服务 (FastAPI)"
    ensure_port_free 3000 "前端服务 (Next.js)"
    
    start_services
    wait_for_health
    show_ready_dashboard
    
    if [ "$DAEMON_MODE" = "true" ]; then
        # 后台模式：解除信号捕获与作业依附，使进程在当前会话退出后继续常驻
        CLEANED_UP=true
        disown -a 2>/dev/null || true
        trap - SIGINT SIGTERM EXIT
        exit 0
    fi
    
    # 前台交互模式：持续监测子进程并响应中断
    while true; do
        wait -n "$BACKEND_PID" "$FRONTEND_PID" 2>/dev/null || true
        if ! kill -0 "$BACKEND_PID" 2>/dev/null; then
            log_error "后端服务进程已意外终止！"
            exit 1
        fi
        if ! kill -0 "$FRONTEND_PID" 2>/dev/null; then
            log_error "前端服务进程已意外终止！"
            exit 1
        fi
        sleep 1
    done
}

main
