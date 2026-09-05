# Profile Artwork

Regenerate the desktop and mobile artwork from the repository root:

```bash
python3 scripts/build_profile_art.py
```

The banner reuses the illustrated avatar from `assets/banner.svg`. The research
map and terminal animation use locally maintained labels. They do not represent
live activity, scores, or research metrics. No API keys or network access are
needed to generate or display these assets.

The profile uses `<picture>` sources for mobile layouts. All SVGs include titles
and descriptions; the README retains text and direct links for the same work.
