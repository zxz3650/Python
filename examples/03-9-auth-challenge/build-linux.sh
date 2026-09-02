#!/usr/bin/env sh
set -eu

script_dir=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
dist_dir="$script_dir/dist"

mkdir -p "$dist_dir"

CGO_ENABLED=0 GOOS=linux GOARCH=amd64 go build \
  -trimpath -ldflags="-s -w" \
  -o "$dist_dir/auth-lab-linux-amd64" "$script_dir"

CGO_ENABLED=0 GOOS=linux GOARCH=arm64 go build \
  -trimpath -ldflags="-s -w" \
  -o "$dist_dir/auth-lab-linux-arm64" "$script_dir"

if command -v sha256sum >/dev/null 2>&1; then
  (
    cd "$dist_dir"
    sha256sum auth-lab-linux-amd64 auth-lab-linux-arm64 > SHA256SUMS
  )
else
  (
    cd "$dist_dir"
    shasum -a 256 auth-lab-linux-amd64 auth-lab-linux-arm64 > SHA256SUMS
  )
fi

echo "Linux 실행 파일 생성 완료: $dist_dir"
