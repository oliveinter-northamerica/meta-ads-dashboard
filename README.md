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

- `pages_show_list` — list your Pages
- `pages_read_engagement` — read Page posts and their comments
- `pages_manage_engagement` — reply, hide, delete comments on FB Pages
- `instagram_basic` — read IG Business profile + media
- `instagram_manage_comments` — reply, hide, delete comments on IG

Each Page you connect gets its own Page Access Token returned from
`/me/accounts`; the dashboard uses that token for read/write on that Page and
its linked IG Business account, so even if your user token expires, the
connected Pages keep working until their Page tokens roll over.

## What it does

- Lists recent comments across every connected account, newest first.
- Filters: by account, by status (visible / hidden / needs reply).
- Per-comment actions: **Reply**, **Hide** (FB only writes `is_hidden=true`;
  IG writes `hide=true`), **Delete**.
- Shows the post each comment belongs to with a link to the original.

## Limitations

- Pulls only the 10 most recent posts per account and up to 25 comments per
  post on each refresh. Older threads need to be loaded from the post directly.
- No webhooks — comments only appear after you click Refresh.
- Tokens live in `localStorage`. Don't open the file on a shared machine, and
  use the **Wipe everything** button before walking away.
