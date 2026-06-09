#!/usr/bin/env bash
set -e

REPO_ROOT="$(cd "$(dirname "$0")" && pwd)"
BACKEND_DIR="$REPO_ROOT/backend"
FRONTEND_DIR="$REPO_ROOT/frontend"
PID_FILE="$REPO_ROOT/.run.pid"
LOG_DIR="$REPO_ROOT/.logs"

BACKEND_PORT="${BACKEND_PORT:-10051}"
FRONTEND_PORT=5173

# ── helpers ──────────────────────────────────────────────────────────────────

log()  { echo "[run.sh] $*"; }
info() { echo "[run.sh] ✓ $*"; }
warn() { echo "[run.sh] ⚠ $*"; }
die()  { echo "[run.sh] ✗ $*"; exit 1; }

# Resolve the Python 3 binary (prefer 3.12, fall back to 3.11, then 3.10+)
find_python() {
  for py in python3.12 python3.11 python3.10 python3; do
    if command -v "$py" &>/dev/null; then
      ver=$("$py" -c "import sys; print(sys.version_info[:2])" 2>/dev/null)
      # require >= (3, 10)
      if "$py" -c "import sys; sys.exit(0 if sys.version_info >= (3,10) else 1)" 2>/dev/null; then
        echo "$py"
        return
      fi
    fi
  done
  die "Python 3.10+ not found. Install it and re-run."
}

# ── setup steps ───────────────────────────────────────────────────────────────

setup_env() {
  if [ -f "$BACKEND_DIR/.env" ]; then
    info "backend/.env already exists — skipping"
    return
  fi
  log "Creating backend/.env from .env.example ..."
  cp "$BACKEND_DIR/.env.example" "$BACKEND_DIR/.env"
  warn "backend/.env created with defaults. Edit it if you need custom settings:"
  warn "  \$EDITOR $BACKEND_DIR/.env"
}

setup_venv() {
  if [ -f "$BACKEND_DIR/.venv/bin/activate" ]; then
    info "Python venv already exists — skipping"
    return
  fi
  PY=$(find_python)
  log "Creating Python venv with $PY ..."
  "$PY" -m venv "$BACKEND_DIR/.venv"
  info "Venv created at backend/.venv"
  log "Installing backend dependencies ..."
  source "$BACKEND_DIR/.venv/bin/activate"
  pip install --quiet --upgrade pip
  pip install --quiet -r "$BACKEND_DIR/requirements.txt"
  info "Backend dependencies installed"
}

setup_node() {
  if [ -d "$FRONTEND_DIR/node_modules" ]; then
    info "node_modules already exists — skipping"
    return
  fi
  if ! command -v node &>/dev/null; then
    die "Node.js not found. Install Node 18+ and re-run."
  fi
  if ! command -v npm &>/dev/null; then
    die "npm not found. Install npm and re-run."
  fi
  log "Installing frontend dependencies ..."
  cd "$FRONTEND_DIR" && npm install --silent
  cd "$REPO_ROOT"
  info "Frontend dependencies installed"
}

# Run all setup steps (idempotent — skips anything already done)
setup_all() {
  log "Running setup ..."
  setup_env
  setup_venv
  setup_node
  info "Setup complete."
}

# ── runtime helpers ───────────────────────────────────────────────────────────

start_backend() {
  mkdir -p "$LOG_DIR"
  log "Starting backend on http://localhost:$BACKEND_PORT ..."
  source "$BACKEND_DIR/.venv/bin/activate"
  cd "$BACKEND_DIR"
  uvicorn src.main:app --reload --port "$BACKEND_PORT" \
    > "$LOG_DIR/backend.log" 2>&1 &
  echo $! >> "$PID_FILE"
  log "  PID $! → .logs/backend.log"
  cd "$REPO_ROOT"
}

start_frontend() {
  mkdir -p "$LOG_DIR"
  log "Starting frontend on http://localhost:$FRONTEND_PORT ..."
  cd "$FRONTEND_DIR"
  BACKEND_PORT="$BACKEND_PORT" npm run dev -- --port "$FRONTEND_PORT" \
    > "$LOG_DIR/frontend.log" 2>&1 &
  echo $! >> "$PID_FILE"
  log "  PID $! → .logs/frontend.log"
  cd "$REPO_ROOT"
}

stop_all() {
  if [ ! -f "$PID_FILE" ]; then
    log "Nothing running (no .run.pid)."
    return
  fi
  log "Stopping processes ..."
  while read -r pid; do
    if kill -0 "$pid" 2>/dev/null; then
      kill "$pid" && log "  killed PID $pid"
    fi
  done < "$PID_FILE"
  rm -f "$PID_FILE"
  info "Stopped."
}

status() {
  if [ ! -f "$PID_FILE" ]; then
    log "Not running."
    return
  fi
  log "Running PIDs:"
  while read -r pid; do
    if kill -0 "$pid" 2>/dev/null; then
      echo "  PID $pid — $(ps -p "$pid" -o comm= 2>/dev/null || echo '(unknown)')"
    else
      echo "  PID $pid — (dead)"
    fi
  done < "$PID_FILE"
}

print_urls() {
  log ""
  log "  Frontend → http://localhost:$FRONTEND_PORT"
  log "  Backend  → http://localhost:$BACKEND_PORT"
  log ""
  log "Commands: ./run.sh stop | restart | status | logs"
}

# ── commands ──────────────────────────────────────────────────────────────────

CMD="${1:-start}"

case "$CMD" in
  setup)
    setup_all
    ;;

  start)
    setup_all
    if [ -f "$PID_FILE" ]; then
      log "Already running. Use './run.sh restart' to restart."
      status
      exit 0
    fi
    start_backend
    start_frontend
    print_urls
    ;;

  stop)
    stop_all
    ;;

  restart)
    stop_all
    sleep 1
    setup_all
    start_backend
    start_frontend
    log "Restarted."
    print_urls
    ;;

  status)
    status
    ;;

  logs)
    log "Tailing .logs/backend.log and .logs/frontend.log (Ctrl+C to stop) ..."
    tail -f "$LOG_DIR/backend.log" "$LOG_DIR/frontend.log" 2>/dev/null \
      || log "No log files yet — run './run.sh start' first."
    ;;

  *)
    echo "Usage: ./run.sh [command]"
    echo ""
    echo "  setup    Install all dependencies and create .env (safe to re-run)"
    echo "  start    Setup (if needed) then start backend + frontend"
    echo "  stop     Stop both services"
    echo "  restart  Stop, setup (if needed), start"
    echo "  status   Show running PIDs"
    echo "  logs     Tail both log files live"
    exit 1
    ;;
esac
