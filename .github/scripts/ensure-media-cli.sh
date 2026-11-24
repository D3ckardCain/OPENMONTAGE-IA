#!/usr/bin/env bash
set -euo pipefail

# The hosted image may already provide both CLIs. Avoid package-network work then.
if ! command -v ffmpeg >/dev/null 2>&1 || ! command -v ffprobe >/dev/null 2>&1; then
  timeout --kill-after=10s 90s sudo apt-get \
    -o Acquire::Retries=1 -o Acquire::http::Timeout=20 -o Acquire::https::Timeout=20 update
  timeout --kill-after=10s 180s sudo apt-get \
    -o Acquire::Retries=1 -o Acquire::http::Timeout=20 -o Acquire::https::Timeout=20 install -y ffmpeg
fi

command -v ffmpeg
command -v ffprobe
ffmpeg -version
ffprobe -version
