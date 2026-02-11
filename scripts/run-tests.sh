#!/usr/bin/env bash
###############################################################################
# OpenMedRecord -- Test Runner
#
# Runs all tests with coverage reporting. Supports running specific test
# suites via command-line arguments.
#
# Usage:
#   ./scripts/run-tests.sh              # All tests
#   ./scripts/run-tests.sh --unit       # Unit tests only
#   ./scripts/run-tests.sh --integration # Integration tests only
#   ./scripts/run-tests.sh --e2e        # E2E tests only
#   ./scripts/run-tests.sh --frontend   # Frontend tests only
#   ./scripts/run-tests.sh --backend    # All backend tests
###############################################################################

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
BACKEND_DIR="${PROJECT_ROOT}/src/backend"
FRONTEND_DIR="${PROJECT_ROOT}/src/frontend"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Default: run all tests
RUN_UNIT=false
RUN_INTEGRATION=false
RUN_E2E=false
RUN_FRONTEND=false
RUN_BACKEND=false
RUN_ALL=true

for arg in "$@"; do
    case $arg in
        --unit)        RUN_UNIT=true; RUN_ALL=false ;;
        --integration) RUN_INTEGRATION=true; RUN_ALL=false ;;
        --e2e)         RUN_E2E=true; RUN_ALL=false ;;
        --frontend)    RUN_FRONTEND=true; RUN_ALL=false ;;
        --backend)     RUN_BACKEND=true; RUN_ALL=false ;;
        --help|-h)
            echo "Usage: $0 [--unit] [--integration] [--e2e] [--frontend] [--backend]"
            exit 0
            ;;
    esac
done

EXIT_CODE=0

log_header() { echo -e "\n${BLUE}=== $1 ===${NC}\n"; }
log_success() { echo -e "${GREEN}PASS${NC} $1"; }
log_fail()    { echo -e "${RED}FAIL${NC} $1"; }

# ---------------------------------------------------------------------------
# Backend Tests
# ---------------------------------------------------------------------------

run_backend_tests() {
    local test_path=$1
    local label=$2

    log_header "$label"

    cd "$BACKEND_DIR"

    if [ ! -d ".venv" ]; then
        echo "Virtual environment not found. Run setup-dev.sh first."
        return 1
    fi

    source .venv/bin/activate

    export ENVIRONMENT=testing
    export DATABASE_URL="${DATABASE_URL:-postgresql+asyncpg://openmed_test:openmed_test@localhost:5433/openmedrecord_test}"
    export JWT_SECRET_KEY="test-jwt-secret-for-tests-only"
    export FIELD_ENCRYPTION_KEY="dGVzdC1mZXJuZXQta2V5LW5vdC1mb3ItcHJvZA=="
    export REDIS_URL="${REDIS_URL:-redis://localhost:6380/0}"

    if python -m pytest "$test_path" \
        -v \
        --tb=short \
        --cov=app \
        --cov-report=term-missing \
        --cov-report=xml:"${PROJECT_ROOT}/coverage-${label// /-}.xml" \
        --junitxml="${PROJECT_ROOT}/test-results-${label// /-}.xml" \
        -x; then
        log_success "$label"
    else
        log_fail "$label"
        EXIT_CODE=1
    fi
}

# ---------------------------------------------------------------------------
# Frontend Tests
# ---------------------------------------------------------------------------

run_frontend_tests() {
    log_header "Frontend Tests"

    cd "$FRONTEND_DIR"

    if [ ! -d "node_modules" ]; then
        echo "node_modules not found. Running npm install..."
        npm ci --silent 2>/dev/null || npm install --silent
    fi

    if npx vitest run \
        --coverage \
        --reporter=verbose \
        --reporter=junit \
        --outputFile="${PROJECT_ROOT}/test-results-frontend.xml"; then
        log_success "Frontend Tests"
    else
        log_fail "Frontend Tests"
        EXIT_CODE=1
    fi
}

# ---------------------------------------------------------------------------
# Run requested test suites
# ---------------------------------------------------------------------------

if [ "$RUN_ALL" = true ]; then
    RUN_UNIT=true
    RUN_INTEGRATION=true
    RUN_E2E=true
    RUN_FRONTEND=true
fi

if [ "$RUN_BACKEND" = true ]; then
    RUN_UNIT=true
    RUN_INTEGRATION=true
    RUN_E2E=true
fi

if [ "$RUN_UNIT" = true ]; then
    run_backend_tests "tests/unit/" "Backend Unit Tests"
fi

if [ "$RUN_INTEGRATION" = true ]; then
    run_backend_tests "tests/integration/" "Backend Integration Tests"
fi

if [ "$RUN_E2E" = true ]; then
    run_backend_tests "tests/e2e/" "Backend E2E Tests"
fi

if [ "$RUN_FRONTEND" = true ]; then
    run_frontend_tests
fi

# ---------------------------------------------------------------------------
# Summary
# ---------------------------------------------------------------------------

echo ""
echo "============================================"
if [ $EXIT_CODE -eq 0 ]; then
    echo -e "  ${GREEN}All tests passed.${NC}"
else
    echo -e "  ${RED}Some tests failed.${NC}"
fi
echo "============================================"
echo ""
echo "  Coverage reports:"
ls -1 "${PROJECT_ROOT}"/coverage-*.xml 2>/dev/null || echo "    (none)"
echo ""
echo "  Test result reports:"
ls -1 "${PROJECT_ROOT}"/test-results-*.xml 2>/dev/null || echo "    (none)"
echo ""

exit $EXIT_CODE
