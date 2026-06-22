import { NextResponse } from "next/server";

import { isDemoMode } from "@/server/demo";
import { readGovernanceSheet, validateGovernanceRows, writeGovernanceSheet, type GovernanceRow } from "@/server/governanceCsv";

export const dynamic = "force-dynamic";

export async function GET() {
  try {
    const rows = await readGovernanceSheet();
    return NextResponse.json({ rows });
  } catch (error) {
    return NextResponse.json({ error: error instanceof Error ? error.message : "Error desconocido" }, { status: 500 });
  }
}

export async function PUT(request: Request) {
  if (isDemoMode()) {
    return NextResponse.json(
      { error: "Modo demo (solo lectura): la edicion de la hoja gold esta deshabilitada." },
      { status: 403 },
    );
  }
  try {
    const body = (await request.json()) as { rows?: GovernanceRow[] };
    if (!Array.isArray(body.rows)) {
      return NextResponse.json({ error: "rows debe ser una lista" }, { status: 400 });
    }
    const errors = validateGovernanceRows(body.rows);
    if (errors.length > 0) {
      return NextResponse.json({ errors }, { status: 400 });
    }
    await writeGovernanceSheet(body.rows);
    return NextResponse.json({ ok: true, rows: await readGovernanceSheet() });
  } catch (error) {
    return NextResponse.json({ error: error instanceof Error ? error.message : "Error desconocido" }, { status: 500 });
  }
}
