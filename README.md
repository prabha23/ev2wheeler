# VoltBoard — Static Edition (GitHub-backed data, zero deploys after setup)

This version splits VoltBoard into two independent pieces:

1. **The site code** (`index.html`, `app.js`, `style.css`) — this is what you
   deploy to Netlify, **once**. It almost never changes.
2. **The data** (`data.json`) — this lives in a separate, free GitHub repo.
   You overwrite it there as often as you like (even daily). The live
   dashboard fetches whatever's currently in that file every time someone
   opens the page — **no Netlify redeploy, no deploy credits used, ever.**

This solves both problems you had: the manual drag-and-drop every time, and
burning Netlify deploy credits on every data refresh.

---

## One-time setup (10–15 minutes total)

### Part A — Put `data.json` on GitHub

1. Go to **https://github.com** and sign up (free).
2. Click **New repository**. Name it something like `voltboard-data`.
   Keep it **Public** (so the dashboard can read it without any login/token).
3. On the repo page, click **Add file → Upload files**, and upload your
   `data.json`. Commit it.
4. Click on `data.json` in the repo, then click the **Raw** button. Copy that
   URL — it looks like:
   `https://raw.githubusercontent.com/yourname/voltboard-data/main/data.json`
   This is your permanent data link. It never changes, no matter how many
   times you replace the file's contents.

### Part B — Point the dashboard at that link

1. Open `index.html` in a text editor.
2. Find this line near the bottom:
   ```js
   window.VOLTBOARD_DATA_URL = '';
   ```
3. Paste your Raw URL from Part A in between the quotes:
   ```js
   window.VOLTBOARD_DATA_URL = 'https://raw.githubusercontent.com/yourname/voltboard-data/main/data.json';
   ```
4. Save the file.

### Part C — Deploy the site to Netlify (this is the *only* deploy you'll need)

1. Go to **https://app.netlify.com/drop**.
2. Drag `index.html`, `app.js`, and `style.css` onto the page (you don't need
   to include `data.json` here anymore — it's no longer read from this folder
   unless `VOLTBOARD_DATA_URL` is left blank).
3. Netlify gives you a permanent link, e.g. `https://voltboard-ev2w.netlify.app`.
   (Optional: rename it under **Site settings → Change site name**.)

You're done. This link never needs to be redeployed again for data updates.

---

## Every day/week (≈1 minute, 0 deploy credits): refreshing the data

1. In your personal VoltBoard dashboard, export the latest `data.json` like
   always.
2. Go to your **`voltboard-data`** repo on GitHub.
3. Click on `data.json` → the **pencil/edit icon** (or **Upload files** again
   to overwrite it) → drop in the new file → **Commit changes**.
4. That's it. Refresh your public Netlify link — the new numbers are live
   within seconds. No Netlify deploy, no credits spent.

GitHub's raw file CDN typically reflects a fresh commit almost immediately,
and the dashboard adds a cache-busting parameter on every load so visitors
always get the latest version rather than a stale cached copy.

---

## What your audience sees vs. what you control

- Anyone with the public link sees the live dashboard — Overview, Maker
  detail, full data table, all charts and drill-downs. There's no upload
  button or data-management screen anywhere on the public site.
- Only you, with push/edit access to the `voltboard-data` GitHub repo, can
  change what the dashboard shows. No password is needed on the public site
  itself — control lives entirely in who can write to that GitHub repo.

## Fallback / old behavior
If you ever leave `window.VOLTBOARD_DATA_URL = '';` blank, the dashboard
falls back to reading a local `data.json` sitting next to `index.html` on
Netlify — i.e. the original drag-and-drop-everything workflow. Useful if you
want to test locally before wiring up GitHub.

## If this ever feels like too many manual steps
The next step up is a version with a real backend (password-protected admin
page, live updates with no GitHub commits needed) — ask and I can point you
to that package; the trade-off is a slightly more involved one-time setup.
