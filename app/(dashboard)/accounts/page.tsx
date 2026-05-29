import { prisma } from "@/lib/db";
import { ConnectAccountForm } from "./ConnectAccountForm";
import { DisconnectButton } from "./DisconnectButton";

export const dynamic = "force-dynamic";

export default async function AccountsPage() {
  const accounts = await prisma.metaAccount.findMany({
    orderBy: { connectedAt: "desc" },
    select: {
      id: true,
      platform: true,
      externalId: true,
      name: true,
      pictureUrl: true,
      tokenStatus: true,
      tokenExpiresAt: true,
      connectedAt: true,
      lastSyncedAt: true,
    },
  });

  return (
    <main style={{ padding: 24, fontFamily: "system-ui, sans-serif", maxWidth: 900 }}>
      <h1 style={{ marginTop: 0 }}>Connected accounts</h1>

      <section style={{ marginBottom: 32 }}>
        <h2 style={{ fontSize: 16 }}>Connect a new account</h2>
        <ConnectAccountForm />
      </section>

      <section>
        <h2 style={{ fontSize: 16 }}>Currently connected ({accounts.length})</h2>
        {accounts.length === 0 ? (
          <p style={{ color: "#666" }}>No accounts yet. Paste a token above to get started.</p>
        ) : (
          <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 14 }}>
            <thead>
              <tr style={{ textAlign: "left", borderBottom: "1px solid #ddd" }}>
                <th style={th}>Account</th>
                <th style={th}>Platform</th>
                <th style={th}>Token status</th>
                <th style={th}>Token expires</th>
                <th style={th}>Connected</th>
                <th style={th}></th>
              </tr>
            </thead>
            <tbody>
              {accounts.map((a) => (
                <tr key={a.id} style={{ borderBottom: "1px solid #eee" }}>
                  <td style={td}>
                    <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
                      {a.pictureUrl && (
                        // eslint-disable-next-line @next/next/no-img-element
                        <img
                          src={a.pictureUrl}
                          alt=""
                          width={24}
                          height={24}
                          style={{ borderRadius: "50%" }}
                        />
                      )}
                      <span>
                        <strong>{a.name}</strong>
                        <br />
                        <span style={{ color: "#888", fontSize: 12 }}>{a.externalId}</span>
                      </span>
                    </div>
                  </td>
                  <td style={td}>{a.platform === "FB_PAGE" ? "Facebook Page" : "Instagram"}</td>
                  <td style={td}>
                    <TokenBadge status={a.tokenStatus} />
                  </td>
                  <td style={td}>
                    {a.tokenExpiresAt
                      ? new Date(a.tokenExpiresAt).toLocaleDateString()
                      : "Never"}
                  </td>
                  <td style={td}>{new Date(a.connectedAt).toLocaleDateString()}</td>
                  <td style={td}>
                    <DisconnectButton id={a.id} name={a.name} />
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </section>
    </main>
  );
}

const th: React.CSSProperties = { padding: "8px 6px", fontWeight: 600 };
const td: React.CSSProperties = { padding: "10px 6px", verticalAlign: "top" };

function TokenBadge({ status }: { status: string }) {
  const color =
    status === "ACTIVE"
      ? "#0a7d2c"
      : status === "EXPIRING_SOON"
        ? "#a86b00"
        : "#b00020";
  return (
    <span
      style={{
        display: "inline-block",
        padding: "2px 8px",
        background: `${color}1a`,
        color,
        borderRadius: 999,
        fontSize: 12,
      }}
    >
      {status}
    </span>
  );
}
