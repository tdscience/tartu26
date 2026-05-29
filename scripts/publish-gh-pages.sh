#!/usr/bin/env bash
set -euo pipefail

# Publish the Quarto site to GitHub Pages without interactive prompts,
# then verify key markers from the deployed page.

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$repo_root"

site_url="https://tdscience.github.io/tartu26/prerequisites.html"

echo "Publishing site to gh-pages..."
set +e
timeout 240 quarto publish gh-pages --no-prompt --no-browser
publish_exit=$?
set -e

if [[ $publish_exit -ne 0 && $publish_exit -ne 124 ]]; then
  echo "quarto publish failed with exit code $publish_exit"
  exit $publish_exit
fi

if [[ $publish_exit -eq 124 ]]; then
  echo "quarto publish timed out while waiting for final deployment spinner; continuing with verification checks."
fi

echo "Checking gh-pages head on origin..."
git ls-remote --heads origin gh-pages

echo "Checking deployed page markers on $site_url ..."
curl -s "$site_url" | rg -n "flowmap-embed|seville_flowmap_embed\.html|paste-3\.png" || {
  echo "Expected markers were not found on the live page."
  echo "This can happen due to GitHub Pages caching; try a hard refresh and rerun this check."
  exit 1
}

echo "Publish and verification completed."
