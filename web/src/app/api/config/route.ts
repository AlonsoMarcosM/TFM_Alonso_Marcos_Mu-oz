import { NextResponse } from "next/server";

import { editableConfigFiles } from "@/server/configFiles";

export const dynamic = "force-dynamic";

export async function GET() {
  return NextResponse.json({ files: editableConfigFiles });
}
