#!/usr/bin/env bash
set -euo pipefail

echo "[devcontainer] Installing R package dependencies via pak..."

Rscript -e "if (!requireNamespace('pak', quietly = TRUE)) install.packages('pak', repos = 'https://cloud.r-project.org')"
Rscript -e "pak::pak('tdscience/tartu26')"

echo "[devcontainer] Dependency setup complete."
