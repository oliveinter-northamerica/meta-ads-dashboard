import { NextResponse } from "next/server";
import { cookies } from "next/headers";
import { createSessionCookieValue, sessionCookieName, verifyPassword } from "@/lib/auth";

export async function POST(req: Request) {
  const body = (await req.json().catch(() => ({}))) as { password?: string };
  if (!body.password || !verifyPassword(body.password)) {
    return NextResponse.json({ error: "Invalid password" }, { status: 401 });
  }
  const { value, expires } = await createSessionCookieValue();
  const store = await cookies();
  store.set(sessionCookieName, value, {
    httpOnly: true,
    secure: process.env.NODE_ENV === "production",
    sameSite: "lax",
    path: "/",
    expires,
  });
  return NextResponse.json({ ok: true });
}
