"use client";

import { useEffect, useState } from "react";

import type { Operation } from "@/server/operations";

type Job = {
  id: string;
  status: "pending" | "running" | "success" | "error";
  exitCode?: number | null;
  log: string;
  artifacts: string[];
  result?: JobResult;
};

type JobResult = {
  ok: boolean;
  message: string;
  details: string[];
  artifacts: JobArtifactResult[];
};

type JobArtifactResult = {
  path: string;
  exists: boolean;
  size: number;
  updatedAt: string | null;
  viewable: boolean;
  kind: string;
  summary: string[];
  preview?: string;
};

const statusLabels: Record<Job["status"], string> = {
  pending: "pendiente",
  running: "en ejecución",
  success: "correcto",
  error: "error",
};

export function OperationCard({ operation }: { operation: Operation }) {
  const [job, setJob] = useState<Job | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function run() {
    setError(null);
    if (operation.confirmText && !window.confirm(operation.confirmText)) {
      return;
    }
    try {
      setLoading(true);
      const response = await fetch("/api/jobs", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ operationId: operation.id }),
      });
      const payload = await response.json();
      if (!response.ok) {
        setError(payload.error ?? "No se pudo crear el job.");
        return;
      }
      setJob(payload.job);
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : "No se pudo crear el job.");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    if (!job || !["pending", "running"].includes(job.status)) {
      return;
    }
    const timer = window.setInterval(async () => {
      const response = await fetch(`/api/jobs/${job.id}`);
      const payload = await response.json();
      if (response.ok) {
        setJob(payload.job);
      }
    }, 1500);
    return () => window.clearInterval(timer);
  }, [job]);

  const command = [operation.command, ...operation.args].join(" ");

  return (
    <article className="card">
      <h2>{operation.title}</h2>
      <p className="muted">{operation.description}</p>
      {operation.risk ? <p className="alert alert-warn">{operation.risk}</p> : null}
      <code className="command">{command}</code>
      <div className="actions">
        <button onClick={run} disabled={loading || job?.status === "running" || job?.status === "pending"}>
          {loading ? "Creando job" : "Ejecutar"}
        </button>
        {job ? <span className={`status status-${job.status}`}>{statusLabels[job.status]}</span> : null}
      </div>
      {error ? <p className="alert alert-error">{error}</p> : null}
      {job ? (
        <div className="stack" style={{ marginTop: "1rem" }}>
          {job.result ? (
            <section className={`result result-${job.result.ok ? "success" : "error"}`}>
              <h3>Resultado</h3>
              <p>{job.result.message}</p>
              {job.result.details.length > 0 ? (
                <ul>
                  {job.result.details.map((detail) => (
                    <li key={detail}>{detail}</li>
                  ))}
                </ul>
              ) : null}
              {job.result.artifacts.length > 0 ? (
                <div className="artifact-list">
                  {job.result.artifacts.map((artifact) => (
                    <div key={artifact.path} className="artifact-item">
                      <div className="artifact-head">
                        <strong>{artifact.path}</strong>
                        <span>{artifact.exists ? `${artifact.kind} · ${artifact.size} bytes` : "no generado"}</span>
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
          <p className="muted">
            Job: {job.id} {job.exitCode !== undefined ? `Salida: ${job.exitCode}` : ""}
          </p>
          <pre className="log">{job.log || "Esperando salida..."}</pre>
        </div>
      ) : null}
    </article>
  );
}
