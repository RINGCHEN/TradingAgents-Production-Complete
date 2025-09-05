#!/bin/bash
# 預部署檢查腳本 - 防止錯誤部署
# 使用方法: ./scripts/pre_deploy_check.sh [target]
# target: main-site | admin-site | all

set -e  # 任何錯誤都退出

# 顏色定義
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 全局變量
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
ERRORS=0
WARNINGS=0

# 日誌函數
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
    ((WARNINGS++))
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
    ((ERRORS++))
}

# 檢查必要工具
check_dependencies() {
    log_info "檢查必要工具..."
    
    local required_tools=("python3" "curl" "firebase" "npm")
    
    for tool in "${required_tools[@]}"; do
        if ! command -v "$tool" &> /dev/null; then
            log_error "缺少必要工具: $tool"
        else
            log_success "找到工具: $tool"
        fi
    done
}

# 檢查 steering 文件
check_steering_files() {
    log_info "檢查 steering 文件..."
    
    local required_files=(
        ".kiro/steering/README.md"
        ".kiro/steering/active/tradingagents-system-overview.md"
        ".kiro/steering/active/_ADMIN_FRONTEND_HUB.md"
    )
    
    cd "$PROJECT_ROOT"
    
    for file in "${required_files[@]}"; do
        if [[ -f "$file" ]]; then
            log_success "找到 steering 文件: $file"
        else
            log_error "缺少 steering 文件: $file"
        fi
    done
}

# 執行架構驗證
run_architecture_validation() {
    log_info "執行網站架構驗證..."
    
    cd "$PROJECT_ROOT"
    
    if python3 scripts/validate_website_architecture.py; then
        log_success "網站架構驗證通過"
        return 0
    else
        log_error "網站架構驗證失敗"
        return 1
    fi
}

# 檢查 Google 認證配置
check_google_auth() {
    log_info "檢查 Google 認證配置..."
    
    local client_id="351731559902-11g45sv5947cr3q89lhkar272kfeiput.apps.googleusercontent.com"
    local config_files=(
        "TradingAgents/frontend/src/services/GoogleAuthService.ts"
        "TradingAgents/frontend/firebase.json"
    )
    
    cd "$PROJECT_ROOT"
    
    for file in "${config_files[@]}"; do
        if [[ -f "$file" ]]; then
            if grep -q "$client_id" "$file"; then
                log_success "Google Client ID 在 $file 中正確"
            else
                log_error "Google Client ID 在 $file 中不正確或缺失"
            fi
        else
            log_error "配置文件不存在: $file"
        fi
    done
    
    # 檢查 CSP 配置
    if [[ -f "TradingAgents/frontend/firebase.json" ]]; then
        if grep -q "script-src-elem" "TradingAgents/frontend/firebase.json" && \
           grep -q "accounts.google.com" "TradingAgents/frontend/firebase.json" && \
           grep -q "gsi.google.com" "TradingAgents/frontend/firebase.json"; then
            log_success "CSP 配置包含必要的 Google 域名"
        else
            log_error "CSP 配置缺少必要的 Google 域名"
        fi
    fi
}

# 檢查入口點配置
check_entry_points() {
    log_info "檢查入口點配置..."
    
    local index_html="TradingAgents/frontend/index.html"
    
    cd "$PROJECT_ROOT"
    
    if [[ -f "$index_html" ]]; then
        if grep -q "main.tsx" "$index_html"; then
            if grep -q "AI 智能投資分析平台" "$index_html"; then
                log_success "index.html 配置為主站 (正確)"
            else
                log_warning "index.html 使用 main.tsx 但標題可能不正確"
            fi
        elif grep -q "index-admin.tsx" "$index_html"; then
            if grep -q "企業管理後台" "$index_html"; then
                log_warning "index.html 配置為管理後台 (請確認部署目標)"
            else
                log_error "index.html 使用 index-admin.tsx 但標題不正確"
            fi
        else
            log_error "index.html 入口點配置不明確"
        fi
    else
        log_error "找不到 index.html 文件"
    fi
}

# 檢查 Firebase 配置
check_firebase_config() {
    log_info "檢查 Firebase 配置..."
    
    local firebaserc="TradingAgents/frontend/.firebaserc"
    local firebase_json="TradingAgents/frontend/firebase.json"
    
    cd "$PROJECT_ROOT"
    
    if [[ -f "$firebaserc" ]]; then
        if grep -q "tradingagents-main" "$firebaserc" && \
           grep -q "twstock-admin-466914" "$firebaserc" && \
           grep -q "03king" "$firebaserc"; then
            log_success "Firebase 專案和目標配置正確"
        else
            log_error "Firebase 配置缺少必要的專案或目標"
        fi
    else
        log_error "找不到 .firebaserc 文件"
    fi
    
    if [[ -f "$firebase_json" ]]; then
        log_success "找到 firebase.json"
    else
        log_error "找不到 firebase.json 文件"
    fi
}

# 測試網站可訪問性
test_website_accessibility() {
    log_info "測試網站可訪問性..."
    
    local sites=(
        "https://03king.com"
        "https://admin.03king.com"
    )
    
    for site in "${sites[@]}"; do
        if curl -s --max-time 10 "$site" > /dev/null; then
            log_success "可以訪問: $site"
            
            # 檢查內容
            local title=$(curl -s --max-time 10 "$site" | grep -i "<title>" | head -1)
            log_info "  標題: $title"
            
        else
            log_warning "無法訪問: $site (可能是網絡問題)"
        fi
    done
}

# 檢查建構狀態
check_build_status() {
    log_info "檢查建構狀態..."
    
    cd "$PROJECT_ROOT/TradingAgents/frontend"
    
    if [[ -d "build" ]]; then
        local build_time=$(stat -c %Y build 2>/dev/null || stat -f %m build 2>/dev/null || echo "unknown")
        log_success "找到 build 目錄 (修改時間: $(date -d @$build_time 2>/dev/null || date -r $build_time 2>/dev/null || echo "unknown"))"
        
        if [[ -f "build/index.html" ]]; then
            local build_title=$(grep -i "<title>" build/index.html | head -1)
            log_info "  建構版本標題: $build_title"
        fi
    else
        log_warning "找不到 build 目錄，可能需要執行 npm run build"
    fi
}

# 主檢查函數
run_pre_deploy_checks() {
    local target="$1"
    
    echo "========================================================================"
    echo "🛡️  預部署檢查開始 (目標: ${target:-all})"
    echo "========================================================================"
    echo "⏰ 檢查時間: $(date)"
    echo ""
    
    # 執行所有檢查
    check_dependencies
    echo ""
    
    check_steering_files  
    echo ""
    
    run_architecture_validation
    echo ""
    
    check_google_auth
    echo ""
    
    check_entry_points
    echo ""
    
    check_firebase_config
    echo ""
    
    check_build_status
    echo ""
    
    test_website_accessibility
    echo ""
    
    # 輸出結果摘要
    echo "========================================================================"
    echo "📊 檢查結果摘要"
    echo "========================================================================"
    
    if [[ $ERRORS -eq 0 && $WARNINGS -eq 0 ]]; then
        echo -e "${GREEN}✅ 所有檢查通過，可以安全部署！${NC}"
        return 0
    elif [[ $ERRORS -eq 0 ]]; then
        echo -e "${YELLOW}⚠️  發現 $WARNINGS 個警告，建議檢查後再部署${NC}"
        return 1
    else
        echo -e "${RED}❌ 發現 $ERRORS 個錯誤和 $WARNINGS 個警告，必須修復後才能部署！${NC}"
        echo ""
        echo "請執行以下命令修復問題："
        echo "1. python3 scripts/validate_website_architecture.py"
        echo "2. python3 scripts/cleanup_google_auth.py --dry-run"
        echo "3. 檢查 DEVELOPMENT_PROTECTION_GUIDE.md 中的解決方案"
        return 2
    fi
}

# 顯示使用說明
show_usage() {
    echo "使用方法:"
    echo "  $0 [target]"
    echo ""
    echo "參數:"
    echo "  target    部署目標 (main-site|admin-site|all)"
    echo ""
    echo "例子:"
    echo "  $0                # 檢查所有配置"
    echo "  $0 main-site     # 檢查主站配置" 
    echo "  $0 admin-site    # 檢查管理後台配置"
}

# 主程序
main() {
    local target="${1:-all}"
    
    case "$target" in
        "main-site"|"admin-site"|"all")
            run_pre_deploy_checks "$target"
            ;;
        "-h"|"--help")
            show_usage
            exit 0
            ;;
        *)
            echo "錯誤: 不支援的目標 '$target'"
            show_usage
            exit 1
            ;;
    esac
}

# 執行主程序
main "$@"