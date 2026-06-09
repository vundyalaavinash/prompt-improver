#!/usr/bin/env bash
set -e

REPO_ROOT="$(cd "$(dirname "$0")" && pwd)"
BACKEND_DIR="$REPO_ROOT/backend"
FRONTEND_DIR="$REPO_ROOT/frontend"
PID_FILE="$REPO_ROOT/.run.pid"
LOG_DIR="$REPO_ROOT/.logs"

BACKEND_PORT=8000
FRONTEND_PORT=5173

# ── helpers ─────────────────────────────────────────────────────────────────

log() { echo "[run.sh] $*"; }

check_env() {
  if [ ! -f "$BACKEND_DIR/.env" ]; then
    log "ERROR: backend/.env not found. Copy backend/.env.example and fill in your keys:"
    log "  cp backend/.env.example backend/.env"
    exit 1
  fi
}

check_venv() {
  if [ ! -f "$BACKEND_DIR/.venv/bin/activate" ]; then
    log "ERROR: Python venv not found. Run:"
    log "  cd backend && python3.12 -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt"
    exit 1
  fi
}

check_node() {
  if [ ! -d "$FRONTEND_DIR/node_modules" ]; then
    log "ERROR: node_modules not found. Run:"
    log "  cd frontend && npm install"
    exit 1
  fi
}

start_backend() {
  mkdir -p "$LOG_DIR"
  log "Starting backend on http://localhost:$BACKEND_PORT ..."
  source "$BACKEND_DIR/.venv/bin/activate"
  cd "$BACKEND_DIR"
  uvicorn src.main:app --reload --port "$BACKEND_PORT" \
    > "$LOG_DIR/backend.log" 2>&1 &
  echo $! >> "$PID_FILE"
  log "  backend PID $! → logs: .logs/backend.log"
}

start_frontend() {
  mkdir -p "$LOG_DIR"
  log "Starting frontend on http://localhost:$FRONTEND_PORT ..."
  cd "$FRONTEND_DIR"
  npm run dev -- --port "$FRONTEND_PORT" \
    > "$LOG_DIR/frontend.log" 2>&1 &
  echo $! >> "$PID_FILE"
  log "  frontend PID $! → logs: .logs/frontend.log"
}

stop_all() {
  if [ ! -f "$PID_FILE" ]; then
    log "Nothing running (no .run.pid file)."
    return
  fi
  log "Stopping processes..."
  while read -r pid; do
    if kill -0 "$pid" 2>/dev/null; then
      kill "$pid" && log "  killed PID $pid"
    fi
  done < "$PID_FILE"
  rm -f "$PID_FILE"
  log "Stopped."
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

# ── commands ─────────────────────────────────────────────────────────────────

CMD="${1:-start}"

case "$CMD" in
  start)
    check_env
    check_venv
    check_node
    if [ -f "$PID_FILE" ]; then
      log "Already running. Use './run.sh restart' to restart."
      status
      exit 0
    fi
    start_backend
    start_frontend
    log ""
    log "App running:"
    log "  Frontend → http://localhost:$FRONTEND_PORT"
    log "  Backend  → http://localhost:$BACKEND_PORT"
    log ""
    log "Use './run.sh logs' to tail logs, './run.sh stop' to stop."
    ;;

  stop)
    stop_all
    ;;

  restart)
    stop_all
    sleep 1
    check_env
    check_venv
    check_node
    start_backend
    start_frontend
    log ""
    log "Restarted."
    log "  Frontend → http://localhost:$FRONTEND_PORT"
    log "  Backend  → http://localhost:$BACKEND_PORT"
    ;;

  status)
    status
    ;;

  logs)
    log "Tailing .logs/backend.log and .logs/frontend.log (Ctrl+C to stop)..."
    tail -f "$LOG_DIR/backend.log" "$LOG_DIR/frontend.log" 2>/dev/null \
      || log "No log files yet. Run './run.sh start' first."
    ;;

  *)
    echo "Usage: ./run.sh [start|stop|restart|status|logs]"
    echo ""
    echo "  start    Start backend + frontend"
    echo "  stop     Stop both"
    echo "  restart  Stop then start"
    echo "  status   Show running PIDs"
    echo "  logs     Tail both log files"
    exit 1
    ;;
esac
