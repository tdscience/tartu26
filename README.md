# Tartu 2026: Transport Data Science

Course materials for the Transport Data Science workshop at the University of Tartu, 2026.

## Overview

This workshop covers modern data science skills for transport planning, including data acquisition, cleaning, analysis, visualisation, and reproducible reporting.

## Getting Started

Open the repo in GitHub Codespaces or clone locally and open in VS Code with the devcontainer.

[![Open in GitHub Codespaces](https://github.com/codespaces/badge.svg)](https://codespaces.new/tdscience/tartu26?quickstart=1)

## Website

Visit [https://tdscience.github.io/tartu26/](https://tdscience.github.io/tartu26/) for the rendered course materials.

## Publishing

Use the helper script to publish to GitHub Pages non-interactively and run a quick post-deploy check:

```bash
./scripts/publish-gh-pages.sh
```

Manual equivalent:

```bash
printf 'Y\n' | quarto publish gh-pages
curl -s https://tdscience.github.io/tartu26/prerequisites.html | rg -n "flowmap-embed|seville_flowmap_embed\.html|paste-3\.png"
```

## Sessions

1. Finding and importing data
2. Origin-destination analysis
3. Visualisation
4. Spatio-temporal data
5. Routing and route networks
6. Best practices
7. Advanced topics
