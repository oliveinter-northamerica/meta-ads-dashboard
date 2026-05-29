"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";

type Discovered = {
  platform: "FB_PAGE" | "IG_BUSINESS";
  externalId: string;
  name: string;
  pictureUrl?: string;
  pageAccessToken?: string;
};

type TokenInfo = { type: string; expiresAt: string | null; scopes: string[] };

export function ConnectAccountForm() {
  const router = useRouter();
  const [token, setToken] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [discovered, setDiscovered] = useState<Discovered[] | null>(null);
  const [tokenInfo, setTokenInfo] = useState<TokenInfo | null>(null);
  const [selected, setSelected] = useState<Set<string>>(new Set());
  const [saving, setSaving] = useState(false);

  async function onDiscover(e: React.FormEvent) {
    e.preventDefault();
    setLoading(true);
    setError(null);
    setDiscovered(null);
    setSelected(new Set());
    const res = await fetch("/api/accounts/discover", {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({ token }),
    });
    setLoading(false);
    const data = await res.json();
    if (!res.ok) {
      setError(data.error ?? "Discovery failed");
      return;
    }
    setTokenInfo(data.tokenInfo);
    setDiscovered(data.accounts);
    setSelected(new Set(data.accounts.map((a: Discovered) => key(a))));
  }

  function toggle(k: string) {
    setSelected((prev) => {
      const next = new Set(prev);
      if (next.has(k)) next.delete(k);
      else next.add(k);
      return next;
    });
  }

  async function onConnect() {
    if (!discovered) return;
    setSaving(true);
    setError(null);
    try {
      for (const a of discovered) {
        if (!selected.has(key(a))) continue;
        const res = await fetch("/api/accounts", {
          method: "POST",
          headers: { "content-type": "application/json" },
          body: JSON.stringify({
            platform: a.platform,
            externalId: a.externalId,
            name: a.name,
            pictureUrl: a.pictureUrl,
            accessToken: a.pageAccessToken ?? token,
            tokenExpiresAt: tokenInfo?.expiresAt ?? null,
          }),
        });
        if (!res.ok) {
          const data = await res.json().catch(() => ({}));
          throw new Error(data.error ?? `Failed to connect ${a.name}`);
        }
      }
      setToken("");
      setDiscovered(null);
      setTokenInfo(null);
      setSelected(new Set());
      router.refresh();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to connect");
    } finally {
      setSaving(false);
    }
  }

  return (
    <div style={{ display: "grid", gap: 12 }}>
      <form onSubmit={onDiscover} style={{ display: "grid", gap: 8 }}>
        <label style={{ display: "grid", gap: 4 }}>
          <span style={{ fontSize: 12, color: "#555" }}>User access token</span>
          <textarea
            value={token}
            onChange={(e) => setToken(e.target.value)}
            placeholder="EAAxxxxxxxxxxxxxx…"
            rows={3}
            required
            style={{
              padding: 8,
              border: "1px solid #ccc",
              borderRadius: 4,
              fontFamily: "monospace",
              fontSize: 12,
            }}
          />
          <span style={{ fontSize: 12, color: "#888" }}>
            Paste a user access token with{" "}
            <code>pages_show_list</code>, <code>pages_read_engagement</code>,{" "}
            <code>pages_manage_engagement</code>, <code>instagram_basic</code>, and{" "}
            <code>instagram_manage_comments</code>. We&apos;ll fetch the list of Pages and IG
            accounts it can access.
          </span>
        </label>
        <button
          type="submit"
          disabled={loading || !token}
          style={{
            padding: "8px 12px",
            background: "#111",
            color: "#fff",
            border: 0,
            borderRadius: 4,
            cursor: "pointer",
            justifySelf: "start",
          }}
        >
          {loading ? "Looking up…" : "Look up accounts"}
        </button>
      </form>

      {error && <p style={{ color: "#c00", fontSize: 13 }}>{error}</p>}

      {discovered && tokenInfo && (
        <div
          style={{
            border: "1px solid #ddd",
            borderRadius: 8,
            padding: 12,
            display: "grid",
            gap: 12,
          }}
        >
          <div style={{ fontSize: 12, color: "#555" }}>
            Token type: <strong>{tokenInfo.type}</strong> · expires:{" "}
            <strong>
              {tokenInfo.expiresAt
                ? new Date(tokenInfo.expiresAt).toLocaleString()
                : "Never"}
            </strong>{" "}
            · scopes: {tokenInfo.scopes.join(", ") || "(none)"}
          </div>

          {discovered.length === 0 ? (
            <p style={{ color: "#666", fontSize: 13 }}>
              This token isn&apos;t an admin of any Page or IG Business account.
            </p>
          ) : (
            <>
              <table style={{ width: "100%", fontSize: 14, borderCollapse: "collapse" }}>
                <tbody>
                  {discovered.map((a) => {
                    const k = key(a);
                    return (
                      <tr key={k} style={{ borderBottom: "1px solid #f0f0f0" }}>
                        <td style={{ padding: "6px 4px", width: 28 }}>
                          <input
                            type="checkbox"
                            checked={selected.has(k)}
                            onChange={() => toggle(k)}
                          />
                        </td>
                        <td style={{ padding: "6px 4px" }}>
                          {a.pictureUrl && (
                            // eslint-disable-next-line @next/next/no-img-element
                            <img
                              src={a.pictureUrl}
                              alt=""
                              width={20}
                              height={20}
                              style={{
                                borderRadius: "50%",
                                verticalAlign: "middle",
                                marginRight: 6,
                              }}
                            />
                          )}
                          <strong>{a.name}</strong>{" "}
                          <span style={{ color: "#888", fontSize: 12 }}>{a.externalId}</span>
                        </td>
                        <td style={{ padding: "6px 4px", color: "#555" }}>
                          {a.platform === "FB_PAGE" ? "Facebook Page" : "Instagram"}
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
              <button
                onClick={onConnect}
                disabled={saving || selected.size === 0}
                style={{
                  padding: "8px 12px",
                  background: "#0a7d2c",
                  color: "#fff",
                  border: 0,
                  borderRadius: 4,
                  cursor: "pointer",
                  justifySelf: "start",
                }}
              >
                {saving ? "Connecting…" : `Connect ${selected.size} account(s)`}
              </button>
            </>
          )}
        </div>
      )}
    </div>
  );
}

function key(a: Discovered): string {
  return `${a.platform}:${a.externalId}`;
}
