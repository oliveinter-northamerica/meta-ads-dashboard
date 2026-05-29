"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";

export function DisconnectButton({ id, name }: { id: string; name: string }) {
  const router = useRouter();
  const [pending, setPending] = useState(false);

  async function onClick() {
    if (!confirm(`Disconnect ${name}? Comments already ingested are kept.`)) return;
    setPending(true);
    await fetch(`/api/accounts/${id}`, { method: "DELETE" });
    setPending(false);
    router.refresh();
  }

  return (
    <button
      onClick={onClick}
      disabled={pending}
      style={{
        padding: "4px 10px",
        background: "transparent",
        color: "#b00020",
        border: "1px solid #b00020",
        borderRadius: 4,
        cursor: "pointer",
        fontSize: 12,
      }}
    >
      {pending ? "…" : "Disconnect"}
    </button>
  );
}
