# Internship Pipeline

A single-page internship and interview tracker: summary stats, a stage funnel, upcoming deadlines, and a drag-and-drop board / table of every application.

**Live:** https://palashpawar.github.io/internship-tracker/

- Stages: Wishlist → Applied → Online assessment → Phone screen → Interviews → Final round → Offer (plus Rejected / Withdrawn)
- **Sync:** click *Sync* and paste a classic GitHub token with only the `gist` scope. Data lives in a secret gist on your own account (`internship-pipeline.json`), so every device shows the same tracker. The token stays in that browser's `localStorage`.
- Without sync, data stays in the browser's `localStorage`. **Export** / **Import** move it as JSON.
- No build step: it's one `index.html`.
