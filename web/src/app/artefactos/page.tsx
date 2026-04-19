import { ArtifactViewer } from "@/components/ArtifactViewer";

export default async function ArtefactosPage({ searchParams }: { searchParams: Promise<{ path?: string }> }) {
  const params = await searchParams;

  return (
    <div className="stack">
      <header>
        <h1 className="page-title">Artefactos</h1>
        <p className="lead">Ficheros reproducibles generados por los comandos y scripts de la PoC.</p>
      </header>
      <ArtifactViewer initialPath={params.path} />
    </div>
  );
}
