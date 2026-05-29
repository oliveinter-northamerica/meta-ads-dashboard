import { NextResponse } from "next/server";
import { prisma } from "@/lib/db";

export async function DELETE(_req: Request, ctx: { params: Promise<{ id: string }> }) {
  const { id } = await ctx.params;
  await prisma.metaAccount.delete({ where: { id } }).catch(() => null);
  return NextResponse.json({ ok: true });
}
