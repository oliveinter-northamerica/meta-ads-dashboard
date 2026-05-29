// Minimal Graph API client. Just enough for Phase 2 — validate a token and
// discover which Pages / IG Business accounts it can access.
// Fetchers for posts and comments land in Phase 3+.

const GRAPH_VERSION = process.env.META_GRAPH_API_VERSION ?? "v21.0";
const GRAPH_BASE = `https://graph.facebook.com/${GRAPH_VERSION}`;

export class GraphApiError extends Error {
  constructor(
    message: string,
    readonly status: number,
    readonly fbCode?: number,
    readonly fbSubcode?: number,
  ) {
    super(message);
    this.name = "GraphApiError";
  }
}

type GraphFetchOptions = {
  accessToken: string;
  searchParams?: Record<string, string>;
};

async function graphFetch<T>(
  path: string,
  { accessToken, searchParams }: GraphFetchOptions,
): Promise<T> {
  const url = new URL(`${GRAPH_BASE}${path}`);
  url.searchParams.set("access_token", accessToken);
  for (const [k, v] of Object.entries(searchParams ?? {})) {
    url.searchParams.set(k, v);
  }

  const res = await fetch(url, { cache: "no-store" });
  const json = (await res.json()) as
    | T
    | { error: { message: string; code: number; error_subcode?: number } };

  if (!res.ok || (json as { error?: unknown }).error) {
    const err = (json as { error?: { message: string; code: number; error_subcode?: number } }).error;
    throw new GraphApiError(
      err?.message ?? `Graph API ${res.status}`,
      res.status,
      err?.code,
      err?.error_subcode,
    );
  }
  return json as T;
}

// ---------- Token introspection ----------

export type TokenDebugInfo = {
  appId: string;
  type: string; // "USER", "PAGE", "APP", "SYSTEM_USER"
  isValid: boolean;
  expiresAt: Date | null; // null = never expires
  scopes: string[];
  userId?: string;
};

export async function debugToken(token: string): Promise<TokenDebugInfo> {
  // /debug_token requires {access_token}|{app_secret} as the app token, OR a
  // user token. For Phase 2 we accept the token introspecting itself, which
  // works for User and Page tokens that have admin rights to their own app.
  const res = await graphFetch<{
    data: {
      app_id: string;
      type: string;
      is_valid: boolean;
      expires_at: number; // 0 = never expires
      scopes: string[];
      user_id?: string;
    };
  }>("/debug_token", {
    accessToken: token,
    searchParams: { input_token: token },
  });

  return {
    appId: res.data.app_id,
    type: res.data.type,
    isValid: res.data.is_valid,
    expiresAt: res.data.expires_at > 0 ? new Date(res.data.expires_at * 1000) : null,
    scopes: res.data.scopes ?? [],
    userId: res.data.user_id,
  };
}

// ---------- Discovery: list Pages + IG accounts behind a user token ----------

export type DiscoveredAccount = {
  platform: "FB_PAGE" | "IG_BUSINESS";
  externalId: string;
  name: string;
  pictureUrl?: string;
  pageAccessToken?: string; // FB pages return their own long-lived token
  linkedFbPageId?: string; // for IG accounts
};

type FbPageNode = {
  id: string;
  name: string;
  access_token?: string;
  picture?: { data: { url: string } };
  instagram_business_account?: { id: string };
};

export async function discoverAccounts(userToken: string): Promise<DiscoveredAccount[]> {
  const res = await graphFetch<{ data: FbPageNode[] }>("/me/accounts", {
    accessToken: userToken,
    searchParams: {
      fields:
        "id,name,access_token,picture{url},instagram_business_account{id,username,profile_picture_url}",
      limit: "100",
    },
  });

  const out: DiscoveredAccount[] = [];
  for (const page of res.data) {
    out.push({
      platform: "FB_PAGE",
      externalId: page.id,
      name: page.name,
      pictureUrl: page.picture?.data.url,
      pageAccessToken: page.access_token,
    });

    if (page.instagram_business_account) {
      const ig = await graphFetch<{
        id: string;
        username: string;
        profile_picture_url?: string;
      }>(`/${page.instagram_business_account.id}`, {
        accessToken: page.access_token ?? userToken,
        searchParams: { fields: "id,username,profile_picture_url" },
      }).catch(() => null);

      if (ig) {
        out.push({
          platform: "IG_BUSINESS",
          externalId: ig.id,
          name: `@${ig.username}`,
          pictureUrl: ig.profile_picture_url,
          pageAccessToken: page.access_token,
          linkedFbPageId: page.id,
        });
      }
    }
  }
  return out;
}
