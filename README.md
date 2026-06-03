# meta-ads-dashboard

Single-file moderation inbox for **Facebook Page + Instagram Business comments**.
No build step, no server, no database — just open `index.html`.

## Usage

1. Open `index.html` in a browser (Chrome/Edge/Safari).
2. Expand **Credentials**, paste a Meta user access token, click **Save**.
3. Expand **Connected accounts**, click **Look up accounts**, check the Pages
   and IG Business accounts you want to manage, click **Save selected**.
4. In **Inbox**, click **Refresh** to pull recent comments. Reply, hide, or
   delete each one inline.

The token, connected accounts, and any cached state live in your browser's
`localStorage`. **Wipe everything** in the warning banner clears it all.

## Required token scopes

Generate a user token (Graph API Explorer or your own OAuth flow) with:

**Facebook Pages**
- `pages_show_list` — required for `/me/accounts` to list the Pages you admin.
- `pages_read_engagement` — read your Page's posts, comments, reactions, basic metadata.
- `pages_read_user_content` — read user-generated content on your Page (visitor
  posts, and the comment threads Meta classifies as UGC). Without this some
  comment lists come back empty.
- `pages_manage_engagement` — reply, hide/unhide, delete comments.

**Instagram Business / Creator (linked to a Page)**
- `instagram_basic` — discover the IG Business account via its linked Page, read
  profile, media, captions, comments.
- `instagram_manage_comments` — reply, hide, delete IG comments.

**If the Page or IG account is owned by a Business Manager (common for brands)**
- `business_management` — without this, `/me/accounts` silently omits Business
  Manager-owned Pages and you'll see "0 accounts found".

**To also pull comments from ad creatives (dark posts and any other post
referenced by an ad)**
- `ads_read` — lets the dashboard walk `/me/adaccounts → /act_*/ads` and grab
  every post referenced by an ad, then pull comments on those posts via the
  Page Access Token. Without this scope, the **Include ads** checkbox in
  section 3 logs a warning and refresh falls back to organic + dark posts
  only. The page's own endpoints (`/posts`, `/promotable_posts`) cover most
  brands; the ad-account path catches anything else (ads that re-use posts
  from a different page, oddly-classified dark posts, etc.).

Each Page you connect gets its own Page Access Token returned from
`/me/accounts`; the dashboard uses that token for read/write on that Page and
its linked IG Business account, so even if your user token expires, the
connected Pages keep working until their Page tokens roll over.

> The user token from Graph API Explorer lasts ~1–2 hours. For something more
> durable, exchange it for a long-lived token via
> `GET /oauth/access_token?grant_type=fb_exchange_token&client_id=...&client_secret=...&fb_exchange_token=...`
> then paste the long-lived one into the dashboard. The Page tokens we store
> after **Look up accounts** outlive the user token regardless.
>
> These scopes work without App Review for users who are admins / developers /
> testers of the app. For a non-admin teammate to use their own token you'll
> need App Review on `pages_manage_engagement`, `instagram_manage_comments`,
> `pages_read_user_content`, and `business_management`.

## What it does

- Lists recent comments across every connected account, newest first.
- Filters: by account, by status (visible / hidden / needs reply).
- Per-comment actions: **Reply**, **Hide** (FB only writes `is_hidden=true`;
  IG writes `hide=true`), **Delete**.
- Shows the post each comment belongs to with a link to the original.

## Optional: Google Sheets sync

The dashboard can mirror your data to a Google Sheet you own — useful for
backing up sentiment labels, sharing the connected-accounts list with a
teammate, or building pivot tables on the full comment log.

How it works: you deploy a tiny Apps Script as a web app, paste the URL into
section 1.5, and the dashboard POSTs to it on relevant events. No Google
Cloud project, no OAuth — the deployment URL itself is the shared secret.

**One-time setup**

1. Create / open a Google Sheet.
2. **Extensions → Apps Script**. Delete the default `Code.gs`, paste the
   script shown in section 1.5 of the dashboard (there's a Copy button), save.
3. **Deploy → New deployment → Type: Web app**. Execute as: *Me*. Who has
   access: *Anyone*. Accept the permissions prompt.
4. Copy the resulting **Web app URL**, paste it into the dashboard, click
   **Save**, then **Test connection**.

**What gets synced**

- **Sentiment overrides** (toggle in section 1.5): pushed on every click of
  **Save** in the inbox. The sheet's `Overrides` tab gets a full replace —
  one row per overridden comment with id, account, author, message,
  sentiment, timestamp.
- **Connected accounts** (toggle): mirrored to the `Accounts` tab on connect
  / disconnect. Tokens are **not** sent — only id, name, platform, linked
  Page id.
- **Comment log** (toggle, off by default): upserts every fetched comment
  into the `CommentLog` tab on each Refresh, keyed by `comment_id`. Each
  comment is one row that gets updated in place when its `like_count`,
  `is_hidden`, `sentiment`, etc. change, so the sheet stays unique. The
  `fetched_at` column becomes "last seen at." Pre-existing duplicate
  rows in the tab are collapsed automatically on the next sync.

**Reverse direction**: the **Pull overrides from sheet** button reads the
`Overrides` tab and merges it back into the dashboard, so you can label in
the sheet and have the dashboard pick it up.

## Limitations

- Pulls only the 10 most recent posts per account and up to 25 comments per
  post on each refresh. Older threads need to be loaded from the post directly.
- No webhooks — comments only appear after you click Refresh.
- Tokens live in `localStorage`. Don't open the file on a shared machine, and
  use the **Wipe everything** button before walking away.
