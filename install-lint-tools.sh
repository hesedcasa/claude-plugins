#!/usr/bin/env bash
set -euo pipefail

# Install linting tools: shellcheck, flake8, black

install_shellcheck() {
  if command -v shellcheck &>/dev/null; then
    echo "[skip] shellcheck already installed ($(shellcheck --version | head -2 | tail -1))"
    return
  fi

  echo "[install] shellcheck..."
  if [[ "$OSTYPE" == "darwin"* ]]; then
    brew install shellcheck
  elif command -v apt-get &>/dev/null; then
    apt-get update -qq && apt-get install -y shellcheck
  elif command -v yum &>/dev/null; then
    yum install -y ShellCheck
  else
    echo "[error] Cannot install shellcheck: unsupported package manager" >&2
    exit 1
  fi
  echo "[ok] shellcheck installed"
}

install_python_tools() {
  local pip_cmd

  if command -v pip3 &>/dev/null; then
    pip_cmd="pip3"
  elif command -v pip &>/dev/null; then
    pip_cmd="pip"
  else
    echo "[error] pip not found — install Python 3 first" >&2
    exit 1
  fi

  local missing=()
  command -v flake8 &>/dev/null || missing+=("flake8")
  command -v black &>/dev/null || missing+=("black")

  if [[ ${#missing[@]} -eq 0 ]]; then
    echo "[skip] flake8 and black already installed"
    return
  fi

  echo "[install] ${missing[*]}..."
  "$pip_cmd" install --quiet --break-system-packages "${missing[@]}"
  echo "[ok] ${missing[*]} installed"
}

install_shellcheck
install_python_tools

echo ""
echo "All lint tools ready:"
echo "  shellcheck $(shellcheck --version | grep version: | awk '{print $2}')"
echo "  flake8     $(flake8 --version 2>&1 | head -1)"
echo "  black      $(black --version 2>&1 | head -1)"
