#!/usr/bin/env bash
set -euo pipefail

# The hosted image may already provide both CLIs. Avoid package-network work then.
if ! command -v ffmpeg >/dev/null 2>&1 || ! command -v ffprobe >/dev/null 2>&1; then
  # #70: the hosted EC2 mirror repeatedly exhausted these deadlines. Use Ubuntu's
  # official signed archives, isolated from the runner's mirror/third-party lists.
  # Do not rewrite /etc/apt, trust arbitrary mirrors, or retry the entire install.
  [[ "$(lsb_release -is)" == Ubuntu ]] || { echo 'Media provisioning requires Ubuntu' >&2; exit 1; }
  [[ "$(dpkg --print-architecture)" == amd64 ]] || { echo 'Media provisioning requires amd64' >&2; exit 1; }
  codename=$(lsb_release -sc)
  [[ "$codename" =~ ^[a-z]+$ ]] || { echo 'Invalid Ubuntu codename' >&2; exit 1; }
  apt_dir=$(mktemp -d)
  # apt owns its partial downloads; remove only this mktemp-created directory.
  trap 'sudo rm -rf -- "$apt_dir"' EXIT
  chmod 755 "$apt_dir"
  mkdir -p "$apt_dir/lists/partial"
  for suite in "$codename" "$codename-updates"; do
    printf 'deb [signed-by=/usr/share/keyrings/ubuntu-archive-keyring.gpg] https://archive.ubuntu.com/ubuntu %s main universe\n' "$suite"
  done > "$apt_dir/sources.list"
  printf 'deb [signed-by=/usr/share/keyrings/ubuntu-archive-keyring.gpg] https://security.ubuntu.com/ubuntu %s-security main universe\n' "$codename" >> "$apt_dir/sources.list"
  apt_options=(
    -o "Dir::Etc::sourcelist=$apt_dir/sources.list" -o Dir::Etc::sourceparts=-
    -o "Dir::State::lists=$apt_dir/lists" -o APT::Update::Error-Mode=any
    -o Acquire::Retries=1 -o Acquire::http::Timeout=20 -o Acquire::https::Timeout=20
  )
  timeout --kill-after=10s 90s sudo apt-get \
    "${apt_options[@]}" update
  timeout --kill-after=10s 180s sudo apt-get \
    "${apt_options[@]}" install --no-install-recommends -y ffmpeg
fi

command -v ffmpeg
command -v ffprobe
ffmpeg -version
ffprobe -version
