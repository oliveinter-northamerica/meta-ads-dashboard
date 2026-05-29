import { NextResponse } from "next/server";
import { z } from "zod";
import { debugToken, discoverAccounts, GraphApiError } from "@/lib/meta/client";

const Body = z.object({ token: z.string().min(20) });

export async function POST(req: Request) {
  const parsed = Body.safeParse(await req.json().catch(() => ({})));
  if (!parsed.success) {
    return NextResponse.json({ error: "token is required" }, { status: 400 });
  }
  const { token } = parsed.data;

  try {
    const debug = await debugToken(token);
    if (!debug.isValid) {
      return NextResponse.json({ error: "Token is not valid" }, { status: 400 });
    }
    const accounts = await discoverAccounts(token);
    return NextResponse.json({
      tokenInfo: {
        type: debug.type,
        expiresAt: debug.expiresAt?.toISOString() ?? null,
        scopes: debug.scopes,
      },
      accounts,
    });
  } catch (e) {
    if (e instanceof GraphApiError) {
      return NextResponse.json(
        { error: `Meta: ${e.message}`, code: e.fbCode },
        { status: e.status === 401 || e.status === 400 ? 400 : 502 },
      );
    }
    return NextResponse.json({ error: "Failed to validate token" }, { status: 500 });
  }
}
