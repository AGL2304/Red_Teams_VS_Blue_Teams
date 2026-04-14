#!/bin/bash

################################################################################
# Docker Vulnerable Apps Launcher
# Starts: Juice Shop, crAPI, and VAmPI for security testing
################################################################################

set -e  # Exit on error

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Functions
print_header() {
    echo -e "${BLUE}=== $1 ===${NC}"
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

print_info() {
    echo -e "${YELLOW}ℹ $1${NC}"
}

print_urls() {
    echo ""
    echo -e "${BLUE}╔════════════════════════════════════════════════════════╗${NC}"
    echo -e "${BLUE}║${NC}         ${GREEN}✓ ALL VULNERABLE APPS STARTED SUCCESSFULLY!${NC}${BLUE}║${NC}"
    echo -e "${BLUE}╠════════════════════════════════════════════════════════╣${NC}"
    echo -e "${BLUE}║${NC} ${YELLOW}Juice Shop (OWASP)${NC}${BLUE}                              ║${NC}"
    echo -e "${BLUE}║${NC}   URL: ${GREEN}http://localhost:3000${NC}${BLUE}               ║${NC}"
    echo -e "${BLUE}║${NC}${BLUE}                                                    ║${NC}"
    echo -e "${BLUE}║${NC} ${YELLOW}crAPI (OWASP)${NC}${BLUE}                                 ║${NC}"
    echo -e "${BLUE}║${NC}   URL: ${GREEN}http://localhost:8080${NC}${BLUE}               ║${NC}"
    echo -e "${BLUE}║${NC}${BLUE}                                                    ║${NC}"
    echo -e "${BLUE}║${NC} ${YELLOW}MailHog (Email Testing)${NC}${BLUE}                      ║${NC}"
    echo -e "${BLUE}║${NC}   URL: ${GREEN}http://127.0.0.1:8025${NC}${BLUE}                ║${NC}"
    echo -e "${BLUE}║${NC}${BLUE}                                                    ║${NC}"
    echo -e "${BLUE}║${NC} ${YELLOW}VAmPI (Vulnerable API)${NC}${BLUE}                       ║${NC}"
    echo -e "${BLUE}║${NC}   URL: ${GREEN}http://127.0.0.1:5000/ui${NC}${BLUE}              ║${NC}"
    echo -e "${BLUE}╚════════════════════════════════════════════════════════╝${NC}"
    echo ""
}

# Check if Docker is installed
check_docker() {
    if ! command -v docker &> /dev/null; then
        print_error "Docker is not installed. Please install Docker first."
        exit 1
    fi
    print_success "Docker is installed"
}

################################################################################
# JUICE SHOP
################################################################################
run_juice_shop() {
    print_header "Starting Juice Shop (OWASP)"
    
    # Remove existing container if running
    docker rm -f juice-shop 2>/dev/null || true
    
    print_info "Pulling Juice Shop image..."
    docker pull bkimminich/juice-shop
    
    print_info "Running Juice Shop container..."
    docker run --rm -d -p 127.0.0.1:3000:3000 --name juice-shop bkimminich/juice-shop
    
    print_success "Juice Shop started"
    echo -e "${GREEN}Access at: http://localhost:3000${NC}"
}

stop_juice_shop() {
    print_header "Stopping Juice Shop"
    docker stop juice-shop 2>/dev/null || print_info "Juice Shop container not running"
    print_success "Juice Shop stopped"
}

################################################################################
# crAPI
################################################################################
run_crapi() {
    print_header "Starting crAPI"
    
    # Set crAPI directory
    CRAPI_DIR="${HOME}/crAPI-main/deploy/docker"
    
    # Download if not exists
    if [ ! -d "$CRAPI_DIR" ]; then
        print_info "Downloading crAPI..."
        curl -L -o /tmp/crapi.zip https://github.com/OWASP/crAPI/archive/refs/heads/main.zip
        unzip -q /tmp/crapi.zip -d "$HOME/"
        rm /tmp/crapi.zip
        print_success "crAPI downloaded"
    fi
    
    print_info "Pulling crAPI images..."
    cd "$CRAPI_DIR"
    docker compose pull
    
    print_info "Starting crAPI services..."
    docker compose -f docker-compose.yml --compatibility up -d
    
    print_success "crAPI started"
    echo -e "${GREEN}Access at: http://localhost:8080${NC}"
}

stop_crapi() {
    print_header "Stopping crAPI"
    
    CRAPI_DIR="${HOME}/crAPI-main/deploy/docker"
    if [ -d "$CRAPI_DIR" ]; then
        cd "$CRAPI_DIR"
        docker compose down
        print_success "crAPI stopped"
    else
        print_info "crAPI not found"
    fi
}

################################################################################
# VAmPI
################################################################################
run_vampi() {
    print_header "Starting VAmPI"
    
    # Remove existing container if running
    docker rm -f vampi 2>/dev/null || true
    
    print_info "Pulling VAmPI image..."
    docker pull erev0s/vampi:latest
    
    print_info "Running VAmPI container..."
    docker run --rm -d -p 5000:5000 --name vampi erev0s/vampi:latest
    
    print_success "VAmPI started"
    echo -e "${GREEN}Access at: http://127.0.0.1:5000/ui/${NC}"
}

stop_vampi() {
    print_header "Stopping VAmPI"
    docker stop vampi 2>/dev/null || print_info "VAmPI container not running"
    print_success "VAmPI stopped"
}

################################################################################
# MENU
################################################################################
show_menu() {
    echo ""
    echo "Select what to do:"
    echo "1) Start all vulnerable apps"
    echo "2) Start Juice Shop only"
    echo "3) Start crAPI only"
    echo "4) Start VAmPI only"
    echo "5) Stop all vulnerable apps"
    echo "6) Stop Juice Shop only"
    echo "7) Stop crAPI only"
    echo "8) Stop VAmPI only"
    echo "9) Exit"
    echo ""
}

################################################################################
# MAIN
################################################################################
main() {
    check_docker
    
    if [ $# -eq 0 ]; then
        # Interactive mode
        while true; do
            show_menu
            read -p "Enter your choice [1-9]: " choice
            
            case $choice in
                1)
                    run_juice_shop
                    run_crapi
                    run_vampi
                    print_urls
                    ;;
                2) run_juice_shop ;;
                3) run_crapi ;;
                4) run_vampi ;;
                5)
                    stop_juice_shop
                    stop_crapi
                    stop_vampi
                    print_header "All apps stopped successfully!"
                    ;;
                6) stop_juice_shop ;;
                7) stop_crapi ;;
                8) stop_vampi ;;
                9)
                    print_info "Exiting..."
                    exit 0
                    ;;
                *)
                    print_error "Invalid choice. Please try again."
                    ;;
            esac
        done
    else
        # Command line mode
        case "$1" in
            all-start)
                run_juice_shop
                run_crapi
                run_vampi
                print_urls
                ;;
            all-stop)
                stop_juice_shop
                stop_crapi
                stop_vampi
                print_header "All apps stopped successfully!"
                ;;
            juice-start) run_juice_shop ;;
            juice-stop) stop_juice_shop ;;
            crapi-start) run_crapi ;;
            crapi-stop) stop_crapi ;;
            vampi-start) run_vampi ;;
            vampi-stop) stop_vampi ;;
            *)
                echo "Usage: $0 [command]"
                echo "Commands:"
                echo "  all-start    - Start all apps"
                echo "  all-stop     - Stop all apps"
                echo "  juice-start  - Start Juice Shop"
                echo "  juice-stop   - Stop Juice Shop"
                echo "  crapi-start  - Start crAPI"
                echo "  crapi-stop   - Stop crAPI"
                echo "  vampi-start  - Start VAmPI"
                echo "  vampi-stop   - Stop VAmPI"
                echo ""
                echo "Run without arguments for interactive mode."
                exit 1
                ;;
        esac
    fi
}

main "$@"
