"use client";

import { useEffect, useState } from "react";

type Artifact = {
  path: string;
  exists: boolean;
  size: number;
  updatedAt: string | null;
};

export function ArtifactViewer({ initialPath }: { initialPath?: string }) {
  const [artifacts, setArtifacts] = useState<Artifact[]>([]);
  const [selected, setSelected] = useState(initialPath ?? "");
  const [content, setContent] = useState("");
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function loadList() {
      const response = await fetch("/api/artifacts");
      const payload = await response.json();
      setArtifacts(payload.artifacts ?? []);
    }
    void loadList();
  }, []);

  useEffect(() => {
    if (initialPath) {
      void loadContent(initialPath);
    }
  }, [initialPath]);

  async function loadContent(path: string) {
    setSelected(path);
    setContent("");
    setError(null);
    const response = await fetch(`/api/artifacts?path=${encodeURIComponent(path)}`);
    const payload = await response.json();
    if (!response.ok) {
      setError(payload.error ?? "No se pudo leer el artefacto.");
      return;
    }
    setContent(payload.artifact.content);
  }

  return (
    <div className="stack">
      <section className="panel">
        <h2>Artefactos</h2>
        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th>Ruta</th>
                <th>Estado</th>
                <th>Tamaño</th>
                <th>Actualizado</th>
                <th>Acción</th>
              </tr>
            </thead>
            <tbody>
              {artifacts.map((artifact) => (
                <tr key={artifact.path}>
                  <td>{artifact.path}</td>
                  <td>{artifact.exists ? "existe" : "no existe"}</td>
                  <td>{artifact.size}</td>
                  <td>{artifact.updatedAt ?? "-"}</td>
                  <td>
                    <div className="actions">
                      <button disabled={!artifact.exists} onClick={() => loadContent(artifact.path)}>
                        Ver
                      </button>
                      {artifact.exists ? (
                        <a
                          className="text-link"
                          href={`/api/artifacts/raw?path=${encodeURIComponent(artifact.path)}`}
                          target="_blank"
                          rel="noopener noreferrer"
                        >
                          Abrir
                        </a>
                      ) : null}
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>
      {error ? <p className="alert alert-error">{error}</p> : null}
      {content ? (
        <section className="panel">
          <h2>{selected}</h2>
          <pre className="log">{content}</pre>
        </section>
      ) : null}
    </div>
  );
}
