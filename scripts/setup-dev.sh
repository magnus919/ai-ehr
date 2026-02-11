#!/usr/bin/env bash
###############################################################################
# OpenMedRecord -- Development Environment Setup
#
# Checks prerequisites, installs dependencies, starts Docker services,
# runs database migrations, and seeds test data.
#
# Usage:
#   ./scripts/setup-dev.sh          # Full setup
#   ./scripts/setup-dev.sh --skip-seed   # Skip seed data
###############################################################################

set -euo pipefail

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
BACKEND_DIR="${PROJECT_ROOT}/src/backend"
FRONTEND_DIR="${PROJECT_ROOT}/src/frontend"
DOCKER_DIR="${PROJECT_ROOT}/infrastructure/docker"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

SKIP_SEED=false

for arg in "$@"; do
    case $arg in
        --skip-seed)
            SKIP_SEED=true
            ;;
    esac
done

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

log_info()    { echo -e "${BLUE}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[OK]${NC}   $1"; }
log_warn()    { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error()   { echo -e "${RED}[ERR]${NC}  $1"; }

check_command() {
    local cmd=$1
    local min_version=${2:-""}
    local install_hint=${3:-""}

    if ! command -v "$cmd" &> /dev/null; then
        log_error "$cmd is not installed."
        if [ -n "$install_hint" ]; then
            echo "       Install: $install_hint"
        fi
        return 1
    fi

    if [ -n "$min_version" ]; then
        local version
        version=$("$cmd" --version 2>&1 | grep -oE '[0-9]+\.[0-9]+' | head -1)
        log_success "$cmd ${version} found"
    else
        log_success "$cmd found"
    fi
    return 0
}

# ---------------------------------------------------------------------------
# Step 1: Check prerequisites
# ---------------------------------------------------------------------------

echo ""
echo "============================================"
echo "  OpenMedRecord Development Setup"
echo "============================================"
echo ""

log_info "Checking prerequisites..."

MISSING=0

check_command "docker" "24.0" "https://docs.docker.com/get-docker/" || MISSING=1
check_command "docker" "" "" && {
    if docker compose version &> /dev/null; then
        log_success "docker compose found"
    else
        log_error "docker compose plugin not found"
        MISSING=1
    fi
}
check_command "python3" "3.12" "https://www.python.org/downloads/" || MISSING=1
check_command "node" "20.0" "https://nodejs.org/" || MISSING=1
check_command "npm" "" "" || MISSING=1
check_command "git" "" "" || MISSING=1

if [ $MISSING -ne 0 ]; then
    log_error "Missing prerequisites. Please install the above tools and retry."
    exit 1
fi

echo ""
log_success "All prerequisites satisfied."
echo ""

# ---------------------------------------------------------------------------
# Step 2: Install backend dependencies
# ---------------------------------------------------------------------------

log_info "Setting up Python virtual environment..."

cd "$BACKEND_DIR"

if [ ! -d ".venv" ]; then
    python3 -m venv .venv
    log_success "Virtual environment created at ${BACKEND_DIR}/.venv"
else
    log_success "Virtual environment already exists"
fi

source .venv/bin/activate

log_info "Installing Python dependencies..."
pip install --quiet --upgrade pip
pip install --quiet -r requirements.txt
log_success "Python dependencies installed"

# ---------------------------------------------------------------------------
# Step 3: Install frontend dependencies
# ---------------------------------------------------------------------------

log_info "Installing frontend dependencies..."

cd "$FRONTEND_DIR"
npm ci --silent 2>/dev/null || npm install --silent
log_success "Frontend dependencies installed"

# ---------------------------------------------------------------------------
# Step 4: Create environment file
# ---------------------------------------------------------------------------

cd "$PROJECT_ROOT"

if [ ! -f ".env" ]; then
    log_info "Creating .env file from .env.example..."
    if [ -f ".env.example" ]; then
        cp .env.example .env
        log_success ".env file created"
    else
        log_warn ".env.example not found; skipping .env creation"
    fi
else
    log_success ".env file already exists"
fi

# ---------------------------------------------------------------------------
# Step 5: Start Docker services
# ---------------------------------------------------------------------------

log_info "Starting Docker services (PostgreSQL, Redis)..."

cd "$DOCKER_DIR"

# Start only infrastructure services (not the app containers)
docker compose up -d postgres redis mailpit

log_info "Waiting for PostgreSQL to be ready..."
RETRIES=30
until docker compose exec -T postgres pg_isready -U openmed -d openmedrecord > /dev/null 2>&1; do
    RETRIES=$((RETRIES - 1))
    if [ $RETRIES -le 0 ]; then
        log_error "PostgreSQL failed to start within 30 seconds."
        exit 1
    fi
    sleep 1
done
log_success "PostgreSQL is ready"

log_info "Waiting for Redis to be ready..."
RETRIES=15
until docker compose exec -T redis redis-cli ping > /dev/null 2>&1; do
    RETRIES=$((RETRIES - 1))
    if [ $RETRIES -le 0 ]; then
        log_error "Redis failed to start within 15 seconds."
        exit 1
    fi
    sleep 1
done
log_success "Redis is ready"

# ---------------------------------------------------------------------------
# Step 6: Run database migrations
# ---------------------------------------------------------------------------

log_info "Running database migrations..."

cd "$BACKEND_DIR"
source .venv/bin/activate

# Set DATABASE_URL for local development
export DATABASE_URL="postgresql+asyncpg://openmed:openmed_dev@localhost:5432/openmedrecord"

if [ -f "alembic.ini" ]; then
    python -m alembic upgrade head
    log_success "Migrations complete"
else
    log_warn "alembic.ini not found; creating tables directly..."
    python -c "
import asyncio
from app.core.database import init_db
asyncio.run(init_db())
print('Tables created.')
"
    log_success "Database tables created"
fi

# ---------------------------------------------------------------------------
# Step 7: Seed test data
# ---------------------------------------------------------------------------

if [ "$SKIP_SEED" = false ]; then
    log_info "Seeding test data..."
    cd "$PROJECT_ROOT"

    if [ -f "scripts/seed-data.py" ]; then
        python scripts/seed-data.py
        log_success "Test data seeded"
    else
        log_warn "seed-data.py not found; skipping seed"
    fi
else
    log_info "Skipping seed data (--skip-seed flag)"
fi

# ---------------------------------------------------------------------------
# Done
# ---------------------------------------------------------------------------

echo ""
echo "============================================"
echo "  Setup Complete"
echo "============================================"
echo ""
echo "  Services running:"
echo "    PostgreSQL : localhost:5432"
echo "    Redis      : localhost:6379"
echo "    Mailpit UI : http://localhost:8025"
echo ""
echo "  Start the backend:"
echo "    cd src/backend && source .venv/bin/activate"
echo "    uvicorn app.main:app --reload --host 0.0.0.0 --port 8000"
echo ""
echo "  Start the frontend:"
echo "    cd src/frontend && npm run dev"
echo ""
echo "  Run tests:"
echo "    make test"
echo ""
