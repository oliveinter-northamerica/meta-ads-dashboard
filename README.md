# meta-ads-dashboard

AI-assisted comment moderation for Meta Pages and Instagram Business accounts.

Reviewers see one inbox of comments across organic posts and ads (incl. dark
posts), automatically classified (spam / toxic / negative-genuine / neutral /
positive) and translated to English from EN / ES / KO / ZH / JA. Actions are
hide-only (never delete) and fully audited.

See **[PLAN.md](./PLAN.md)** for architecture and the phased build plan.

## Stack

Next.js 15 (App Router, TypeScript) · Postgres + Prisma · NextAuth · Anthropic
Claude · Vercel + Vercel Cron.

## Local setup

```bash
cp .env.example .env.local        # set DATABASE_URL, DASHBOARD_PASSWORD, NEXTAUTH_SECRET
npm install
npx prisma migrate dev            # creates the schema in your Postgres
npm run dev                       # → http://localhost:3000
```

You'll be redirected to `/login` — paste the password from `DASHBOARD_PASSWORD`,
then go to **Accounts** to paste a Meta user token and pick which Pages / IG
accounts to connect.

A free [Neon](https://neon.tech) Postgres works for `DATABASE_URL`.

## Status

- **Phase 1** ✅ Foundation: plan, schema, scaffold.
- **Phase 2** ✅ Auth gate + manual account connect (paste a token → discover
  Pages and IG Business accounts → select which to add).
- **Phase 3** ⏳ Ingest organic comments + read-only inbox table.
- See [PLAN.md](./PLAN.md) for the full roadmap.
