#!/bin/bash

# Marvel vs DC Search Engine - Docker Management Script

set -e

# Colors untuk output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function untuk print colored output
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

# Function untuk menampilkan help
show_help() {
    echo "Marvel vs DC Search Engine - Docker Management"
    echo ""
    echo "Usage: ./docker-manage.sh [COMMAND]"
    echo ""
    echo "Commands:"
    echo "  start           - Start semua services (production mode)"
    echo "  start-dev       - Start dalam development mode"
    echo "  start-graphdb   - Start hanya GraphDB"
    echo "  stop            - Stop semua services"
    echo "  restart         - Restart semua services"
    echo "  build           - Build ulang Docker images"
    echo "  logs            - Tampilkan logs semua services"
    echo "  logs-web        - Tampilkan logs web application"
    echo "  logs-graphdb    - Tampilkan logs GraphDB"
    echo "  shell-web       - Akses shell web container"
    echo "  shell-graphdb   - Akses shell GraphDB container"
    echo "  status          - Tampilkan status containers"
    echo "  clean           - Stop dan hapus containers, networks, images"
    echo "  backup          - Backup data GraphDB"
    echo "  restore [FILE]  - Restore data GraphDB dari backup"
    echo "  setup-repository - Setup repository 'kb' di GraphDB"
    echo "  help            - Tampilkan help ini"
}

# Function untuk start services
start_services() {
    print_info "Starting Marvel vs DC Search Engine..."
    docker-compose up -d
    print_success "Services started successfully!"
    print_info "Web App: http://localhost:8000"
    print_info "GraphDB: http://localhost:7200"
}

# Function untuk start development mode
start_dev() {
    print_info "Starting in development mode..."
    docker-compose -f docker-compose.yml -f docker-compose.dev.yml up -d
    print_success "Development services started!"
    print_warning "Remember to setup GraphDB repository if this is first run"
}

# Function untuk start hanya GraphDB
start_graphdb() {
    print_info "Starting GraphDB only..."
    docker-compose up graphdb -d
    print_success "GraphDB started!"
    print_info "GraphDB Workbench: http://localhost:7200"
}

# Function untuk stop services
stop_services() {
    print_info "Stopping services..."
    docker-compose down
    print_success "Services stopped!"
}

# Function untuk restart services
restart_services() {
    print_info "Restarting services..."
    docker-compose restart
    print_success "Services restarted!"
}

# Function untuk build images
build_images() {
    print_info "Building Docker images..."
    docker-compose build --no-cache
    print_success "Images built successfully!"
}

# Function untuk show logs
show_logs() {
    docker-compose logs -f
}

show_web_logs() {
    docker-compose logs -f web
}

show_graphdb_logs() {
    docker-compose logs -f graphdb
}

# Function untuk akses shell
web_shell() {
    print_info "Accessing web container shell..."
    docker-compose exec web bash
}

graphdb_shell() {
    print_info "Accessing GraphDB container shell..."
    docker-compose exec graphdb bash
}

# Function untuk status
show_status() {
    print_info "Container status:"
    docker-compose ps
    echo ""
    print_info "Resource usage:"
    docker stats --no-stream
}

# Function untuk clean up
clean_up() {
    print_warning "This will remove all containers, networks, and images"
    read -p "Are you sure? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        print_info "Cleaning up..."
        docker-compose down -v --rmi all --remove-orphans
        print_success "Clean up completed!"
    else
        print_info "Clean up cancelled"
    fi
}

# Function untuk backup
backup_data() {
    print_info "Creating backup..."
    TIMESTAMP=$(date +%Y%m%d_%H%M%S)
    BACKUP_FILE="graphdb-backup-${TIMESTAMP}.tar.gz"
    
    docker-compose exec graphdb tar -czf /tmp/backup.tar.gz /opt/graphdb/home
    docker cp $(docker-compose ps -q graphdb):/tmp/backup.tar.gz ./${BACKUP_FILE}
    
    print_success "Backup created: ${BACKUP_FILE}"
}

# Function untuk restore
restore_data() {
    if [ -z "$1" ]; then
        print_error "Please specify backup file: ./docker-manage.sh restore <backup-file>"
        exit 1
    fi
    
    if [ ! -f "$1" ]; then
        print_error "Backup file not found: $1"
        exit 1
    fi
    
    print_warning "This will replace current Blazegraph data"
    read -p "Are you sure? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        print_info "Restoring from backup: $1"
        docker cp $1 $(docker-compose ps -q graphdb):/tmp/backup.tar.gz
        docker-compose exec graphdb tar -xzf /tmp/backup.tar.gz -C /
        docker-compose restart graphdb
        print_success "Restore completed!"
    else
        print_info "Restore cancelled"
    fi
}

# Function untuk setup repository
setup_repository() {
    print_info "Setting up GraphDB repository 'kb'..."
    print_warning "Please ensure GraphDB is running and accessible"
    print_info "1. Open http://localhost:7200"
    print_info "2. Go to 'Setup' > 'Repositories'"
    print_info "3. Click 'Create new repository'"
    print_info "4. Select 'GraphDB Repository'"
    print_info "5. Enter Repository ID: kb"
    print_info "6. Enter Repository title: Marvel DC Knowledge Base"
    print_info "7. Click 'Create'"
    echo ""
    read -p "Press Enter after completing the setup..."
    print_success "Repository setup completed!"
}

# Main script logic
case "$1" in
    "start")
        start_services
        ;;
    "start-dev")
        start_dev
        ;;
    "start-graphdb")
        start_graphdb
        ;;
    "stop")
        stop_services
        ;;
    "restart")
        restart_services
        ;;
    "build")
        build_images
        ;;
    "logs")
        show_logs
        ;;
    "logs-web")
        show_web_logs
        ;;
    "logs-graphdb")
        show_graphdb_logs
        ;;
    "shell-web")
        web_shell
        ;;
    "shell-graphdb")
        graphdb_shell
        ;;
    "status")
        show_status
        ;;
    "clean")
        clean_up
        ;;
    "backup")
        backup_data
        ;;
    "restore")
        restore_data "$2"
        ;;
    "setup-repository")
        setup_repository
        ;;
    "help"|"--help"|"-h")
        show_help
        ;;
    "")
        print_error "No command specified"
        show_help
        exit 1
        ;;
    *)
        print_error "Unknown command: $1"
        show_help
        exit 1
        ;;
esac 