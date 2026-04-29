import { NextResponse } from "next/server";

import { readEditableConfig, writeEditableConfig } from "@/server/configFiles";

export const dynamic = "force-dynamic";

export async function GET(_request: Request, context: { params: Promise<{ id: string }> }) {
  const { id } = await context.params;
  try {
    return NextResponse.json({ id, content: await readEditableConfig(id) });
  } catch (error) {
    return NextResponse.json({ error: error instanceof Error ? error.message : "Error desconocido" }, { status: 404 });
  }
}

export async function PUT(request: Request, context: { params: Promise<{ id: string }> }) {
  const { id } = await context.params;
  try {
    const body = (await request.json()) as { content?: unknown };
    if (typeof body.content !== "string") {
      return NextResponse.json({ error: "content debe ser texto" }, { status: 400 });
    }
    await writeEditableConfig(id, body.content);
    return NextResponse.json({ ok: true, id, content: await readEditableConfig(id) });
  } catch (error) {
    return NextResponse.json({ error: error instanceof Error ? error.message : "Error desconocido" }, { status: 400 });
  }
}
