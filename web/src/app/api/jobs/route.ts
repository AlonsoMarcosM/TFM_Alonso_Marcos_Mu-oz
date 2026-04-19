import { NextResponse } from "next/server";

import { listJobs, startJob } from "@/server/jobRunner";

export const dynamic = "force-dynamic";

export async function GET() {
  return NextResponse.json({ jobs: await listJobs() });
}

export async function POST(request: Request) {
  try {
    const body = (await request.json()) as { operationId?: string };
    if (!body.operationId) {
      return NextResponse.json({ error: "operationId es obligatorio" }, { status: 400 });
    }
    const job = await startJob(body.operationId);
    return NextResponse.json({ job }, { status: 201 });
  } catch (error) {
    return NextResponse.json({ error: error instanceof Error ? error.message : "Error desconocido" }, { status: 400 });
  }
}
