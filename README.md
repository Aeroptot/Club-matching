# Club Matching

Web app that recommends clubs based on your interests, busy times, and a tag quiz.

**Live site:** https://aeroptot.github.io/Club-matching/

## Enable GitHub Pages (one-time)

If the live link shows 404, turn Pages on:

1. Open **Settings → Pages** on this repo.
2. Under **Build and deployment → Source**, choose **Deploy from a branch**.
3. Set **Branch** to `gh-pages`, folder **`/ (root)`**, then click **Save**.
4. Wait 1–3 minutes and refresh the live link above.

After the first push to `main`, the **Deploy GitHub Pages** workflow creates/updates the `gh-pages` branch automatically.

**Alternative:** Source = branch `main`, folder `/docs` (no `gh-pages` needed).

## Run locally

```bash
python3 app.py
```

Open http://127.0.0.1:8765

## Rebuild the static site

```bash
python3 build_pages.py
```
