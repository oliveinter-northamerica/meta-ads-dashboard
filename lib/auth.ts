// Lightweight password gate for the single-user Phase 2 dashboard.
// Uses Web Crypto so this module works in both Edge (middleware) and Node
// (API routes) runtimes.

import { cookies } from "next/headers";

const COOKIE_NAME = "mad_session";
const SESSION_TTL_MS = 1000 * 60 * 60 * 24 * 7; // 7 days
const enc = new TextEncoder();

function getSecret(): string {
  const secret = process.env.NEXTAUTH_SECRET;
  if (!secret) {
    throw new Error("NEXTAUTH_SECRET is not set — required to sign session cookies");
  }
  return secret;
}

async function importKey(): Promise<CryptoKey> {
  return crypto.subtle.importKey(
    "raw",
    enc.encode(getSecret()),
    { name: "HMAC", hash: "SHA-256" },
    false,
    ["sign", "verify"],
  );
}

function toHex(buf: ArrayBuffer): string {
  const bytes = new Uint8Array(buf);
  let s = "";
  for (let i = 0; i < bytes.length; i++) {
    s += bytes[i].toString(16).padStart(2, "0");
  }
  return s;
}

async function sign(payload: string): Promise<string> {
  const key = await importKey();
  const sig = await crypto.subtle.sign("HMAC", key, enc.encode(payload));
  return toHex(sig);
}

function constantTimeEqual(a: string, b: string): boolean {
  if (a.length !== b.length) return false;
  let diff = 0;
  for (let i = 0; i < a.length; i++) {
    diff |= a.charCodeAt(i) ^ b.charCodeAt(i);
  }
  return diff === 0;
}

export function getExpectedPassword(): string | null {
  return process.env.DASHBOARD_PASSWORD ?? null;
}

export function verifyPassword(provided: string): boolean {
  const expected = getExpectedPassword();
  if (!expected) return false;
  return constantTimeEqual(provided, expected);
}

export async function createSessionCookieValue(): Promise<{ value: string; expires: Date }> {
  const expires = new Date(Date.now() + SESSION_TTL_MS);
  const nonceBytes = new Uint8Array(16);
  crypto.getRandomValues(nonceBytes);
  const nonce = toHex(nonceBytes.buffer);
  const payload = `${nonce}.${expires.getTime()}`;
  const signature = await sign(payload);
  return { value: `${payload}.${signature}`, expires };
}

export async function isValidSessionCookieValue(raw: string | undefined): Promise<boolean> {
  if (!raw) return false;
  const parts = raw.split(".");
  if (parts.length !== 3) return false;
  const [nonce, expiresStr, signature] = parts;
  const expectedSig = await sign(`${nonce}.${expiresStr}`);
  if (!constantTimeEqual(signature, expectedSig)) return false;
  const expires = Number(expiresStr);
  if (!Number.isFinite(expires) || expires < Date.now()) return false;
  return true;
}

export async function isAuthenticated(): Promise<boolean> {
  const store = await cookies();
  return isValidSessionCookieValue(store.get(COOKIE_NAME)?.value);
}

export const sessionCookieName = COOKIE_NAME;
