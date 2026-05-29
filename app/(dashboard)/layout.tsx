import Link from "next/link";
import type { ReactNode } from "react";
import { SignOutButton } from "./SignOutButton";

export default function DashboardLayout({ children }: { children: ReactNode }) {
  return (
    <div style={{ fontFamily: "system-ui, sans-serif" }}>
      <nav
        style={{
          display: "flex",
          gap: 16,
          padding: "12px 24px",
          borderBottom: "1px solid #eee",
          alignItems: "center",
        }}
      >
        <strong style={{ marginRight: "auto" }}>Community Moderation</strong>
        <Link href="/inbox">Inbox</Link>
        <Link href="/accounts">Accounts</Link>
        <Link href="/audit">Audit</Link>
        <SignOutButton />
      </nav>
      {children}
    </div>
  );
}
