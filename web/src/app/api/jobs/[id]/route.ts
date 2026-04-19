import { NextResponse } from "next/server";

import { readJob } from "@/server/jobRunner";

export const dynamic = "force-dynamic";

export async function GET(_request: Request, context: { params: Promise<{ id: string }> }) {
  const { id } = await context.params;
  const job = await readJob(id);
  if (!job) {
    return NextResponse.json({ error: "Job no encontrado" }, { status: 404 });
  }
  return NextResponse.json({ job });
}
