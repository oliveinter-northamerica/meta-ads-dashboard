import { NextResponse } from "next/server";
import { z } from "zod";
import { prisma } from "@/lib/db";

export async function GET() {
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
  return NextResponse.json({ accounts });
}

const PostBody = z.object({
  platform: z.enum(["FB_PAGE", "IG_BUSINESS"]),
  externalId: z.string().min(1),
  name: z.string().min(1),
  pictureUrl: z.string().url().optional(),
  accessToken: z.string().min(20),
  tokenExpiresAt: z.string().datetime().nullable().optional(),
});

export async function POST(req: Request) {
  const parsed = PostBody.safeParse(await req.json().catch(() => ({})));
  if (!parsed.success) {
    return NextResponse.json(
      { error: "Invalid input", details: parsed.error.flatten() },
      { status: 400 },
    );
  }
  const data = parsed.data;

  // Phase 2: stored plain. Encryption at rest lands in Phase 3.
  const account = await prisma.metaAccount.upsert({
    where: { platform_externalId: { platform: data.platform, externalId: data.externalId } },
    create: {
      // ownerId is a placeholder until multi-user auth lands. Single-user
      // mode uses a synthetic user row created on first connect.
      owner: {
        connectOrCreate: {
          where: { email: "single-user@local" },
          create: { email: "single-user@local", name: "Local user" },
        },
      },
      platform: data.platform,
      externalId: data.externalId,
      name: data.name,
      pictureUrl: data.pictureUrl,
      accessToken: data.accessToken,
      tokenExpiresAt: data.tokenExpiresAt ? new Date(data.tokenExpiresAt) : null,
      settings: { create: {} },
    },
    update: {
      name: data.name,
      pictureUrl: data.pictureUrl,
      accessToken: data.accessToken,
      tokenExpiresAt: data.tokenExpiresAt ? new Date(data.tokenExpiresAt) : null,
      tokenStatus: "ACTIVE",
    },
    select: { id: true, name: true, platform: true },
  });

  return NextResponse.json({ account });
}

