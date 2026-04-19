import { NextResponse } from "next/server";

import { listArtifacts } from "@/server/artifacts";
import { envStatus } from "@/server/env";
import { operations } from "@/server/operations";
import { repoRoot } from "@/server/repoPaths";

export const dynamic = "force-dynamic";

export async function GET() {
  return NextResponse.json({
    repoRoot: repoRoot(),
    env: envStatus(),
    operations,
    artifacts: await listArtifacts(),
  });
}
