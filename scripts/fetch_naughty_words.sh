#!/usr/bin/env bash
set -euo pipefail
base_dir="$(cd "$(dirname "$0")/.."; pwd)"
dest_dir="${base_dir}/data/naughty-words"
mkdir -p "$dest_dir"
langs=(ar zh cs da nl en eo fil fi fr fr-CA de hi hu it ja kab tlh ko no fa pl pt ru es sv th tr)
for lang in "${langs[@]}"; do
  url="https://cdn.jsdelivr.net/npm/naughty-words/${lang}.json"
  out="${dest_dir}/${lang}.json"
  curl -fsSL "$url" -o "$out" || echo "skip $lang"
done
