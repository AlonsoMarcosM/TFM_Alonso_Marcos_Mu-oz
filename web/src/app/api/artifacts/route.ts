import { NextResponse } from "next/server";

import { listArtifacts, readArtifact } from "@/server/artifacts";

export const dynamic = "force-dynamic";

export async function GET(request: Request) {
  const url = new URL(request.url);
  const path = url.searchParams.get("path");
  try {
    if (path) {
      return NextResponse.json({ artifact: await readArtifact(path) });
    }
    return NextResponse.json({ artifacts: await listArtifacts() });
  } catch (error) {
    return NextResponse.json({ error: error instanceof Error ? error.message : "Error desconocido" }, { status: 400 });
  }
}
