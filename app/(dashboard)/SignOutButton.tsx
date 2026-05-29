"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";

export function SignOutButton() {
  const router = useRouter();
  const [pending, setPending] = useState(false);
  async function onClick() {
    setPending(true);
    await fetch("/api/auth/logout", { method: "POST" });
    router.push("/login");
    router.refresh();
  }
  return (
    <button
      onClick={onClick}
      disabled={pending}
      style={{
        background: "transparent",
        border: 0,
        color: "#666",
        cursor: "pointer",
        fontSize: 14,
      }}
    >
      {pending ? "…" : "Sign out"}
    </button>
  );
}
