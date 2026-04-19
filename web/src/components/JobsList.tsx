"use client";

import { useEffect, useState } from "react";

type Job = {
  id: string;
  title: string;
  status: string;
  command: string;
  createdAt: string;
  exitCode?: number | null;
  log: string;
  result?: {
    ok: boolean;
    message: string;
    details: string[];
    artifacts: Array<{
      path: string;
      exists: boolean;
      size: number;
      viewable: boolean;
      summary: string[];
      preview?: string;
    }>;
  };
};

const statusLabels: Record<string, string> = {
  pending: "pendiente",
  running: "en ejecución",
  success: "correcto",
  error: "error",
};

export function JobsList() {
  const [jobs, setJobs] = useState<Job[]>([]);
  const [selected, setSelected] = useState<Job | null>(null);

  async function load() {
    const response = await fetch("/api/jobs");
    const payload = await response.json();
    setJobs(payload.jobs ?? []);
  }

  useEffect(() => {
    void load();
    const timer = window.setInterval(() => void load(), 3000);
    return () => window.clearInterval(timer);
  }, []);

  return (
    <div className="stack">
      <section className="panel">
        <h2>Historial</h2>
        <div className="actions">
          <button onClick={load}>Actualizar</button>
        </div>
        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th>Operacion</th>
                <th>Estado</th>
                <th>Creado</th>
                <th>Salida</th>
                <th>Log</th>
              </tr>
            </thead>
            <tbody>
              {jobs.map((job) => (
                <tr key={job.id}>
                  <td>{job.title}</td>
                  <td><span className={`status status-${job.status}`}>{statusLabels[job.status] ?? job.status}</span></td>
                  <td>{job.createdAt}</td>
                  <td>{job.exitCode ?? "-"}</td>
                  <td>
                    <button onClick={() => setSelected(job)}>Ver</button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>
      {selected ? (
        <section className="panel">
          <h2>{selected.title}</h2>
          <code className="command">{selected.command}</code>
          {selected.result ? (
            <section className={`result result-${selected.result.ok ? "success" : "error"}`}>
              <h3>Resultado</h3>
              <p>{selected.result.message}</p>
              {selected.result.details.length > 0 ? (
                <ul>
                  {selected.result.details.map((detail) => (
                    <li key={detail}>{detail}</li>
                  ))}
                </ul>
              ) : null}
              {selected.result.artifacts.length > 0 ? (
                <div className="artifact-list">
                  {selected.result.artifacts.map((artifact) => (
                    <div key={artifact.path} className="artifact-item">
                      <div className="artifact-head">
                        <strong>{artifact.path}</strong>
                        <span>{artifact.exists ? `${artifact.size} bytes` : "no generado"}</span>
                      </div>
                      {artifact.summary.length > 0 ? (
                        <ul>
                          {artifact.summary.map((line) => (
                            <li key={line}>{line}</li>
                          ))}
                        </ul>
                      ) : null}
                      {artifact.viewable && artifact.exists ? (
                        <a className="text-link" href={`/artefactos?path=${encodeURIComponent(artifact.path)}`}>
                          Ver en artefactos
                        </a>
                      ) : null}
                      {artifact.preview ? <pre className="artifact-preview">{artifact.preview}</pre> : null}
                    </div>
                  ))}
                </div>
              ) : null}
            </section>
          ) : null}
          <pre className="log">{selected.log || "Sin salida registrada."}</pre>
        </section>
      ) : null}
    </div>
  );
}
