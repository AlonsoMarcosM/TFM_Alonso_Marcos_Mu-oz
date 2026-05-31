import { readArtifactRaw } from "@/server/artifacts";

export const dynamic = "force-dynamic";

// Sirve un artefacto con su tipo MIME real y disposición "inline" para poder
// visualizarlo directamente en el navegador (HTML renderizado, PDF en el visor,
// JSON/TTL como texto) sin pasar por la previsualización de la consola.
export async function GET(request: Request) {
  const url = new URL(request.url);
  const path = url.searchParams.get("path");
  if (!path) {
    return new Response("Falta el parámetro 'path'.", { status: 400 });
  }
  try {
    const { buffer, contentType, filename } = await readArtifactRaw(path);
    return new Response(new Uint8Array(buffer), {
      headers: {
        "Content-Type": contentType,
        "Content-Disposition": `inline; filename="${filename}"`,
        "Cache-Control": "no-store",
      },
    });
  } catch (error) {
    return new Response(error instanceof Error ? error.message : "Error desconocido", { status: 400 });
  }
}
