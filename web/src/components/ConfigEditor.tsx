"use client";

import { useEffect, useState } from "react";

import { DEMO_MODE } from "@/shared/demoFlag";

type ConfigFile = {
  id: string;
  title: string;
  description: string;
};

export function ConfigEditor() {
  const [files, setFiles] = useState<ConfigFile[]>([]);
  const [selected, setSelected] = useState("governance_defaults.yaml");
  const [content, setContent] = useState("");
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function loadFiles() {
    const response = await fetch("/api/config");
    const payload = await response.json();
    if (response.ok) {
      setFiles(payload.files);
    }
  }

  async function loadConfig(id = selected) {
    setLoading(true);
    setError(null);
    setMessage(null);
    const response = await fetch(`/api/config/${encodeURIComponent(id)}`);
    const payload = await response.json();
    setLoading(false);
    if (!response.ok) {
      setError(payload.error ?? "No se pudo leer la configuracion.");
      return;
    }
    setContent(payload.content);
  }

  useEffect(() => {
    void loadFiles();
  }, []);

  useEffect(() => {
    void loadConfig(selected);
  }, [selected]);

  async function save() {
    if (DEMO_MODE) {
      setError("Modo demo (solo lectura): los cambios no se guardan.");
      return;
    }
    setSaving(true);
    setError(null);
    setMessage(null);
    const response = await fetch(`/api/config/${encodeURIComponent(selected)}`, {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ content }),
    });
    const payload = await response.json();
    setSaving(false);
    if (!response.ok) {
      setError(payload.error ?? "No se pudo guardar la configuracion.");
      return;
    }
    setContent(payload.content);
    setMessage("Configuracion guardada correctamente.");
  }

  const current = files.find((file) => file.id === selected);

  return (
    <section className="panel">
      <h2>Configuracion de gobierno</h2>
      <p className="muted">
        Edita solo los YAML versionados que controlan defaults DCAT/HVD, reglas de mapeo y perfil operativo. Tras
        guardar, ejecuta el dry-run o la validacion correspondiente.
      </p>
      <div className="actions">
        <select value={selected} onChange={(event) => setSelected(event.target.value)}>
          {files.map((file) => (
            <option key={file.id} value={file.id}>
              {file.title}
            </option>
          ))}
        </select>
        <button onClick={() => void loadConfig()} type="button" disabled={loading}>
          Recargar configuracion
        </button>
        <button onClick={save} type="button" disabled={saving || loading || DEMO_MODE}>
          {saving ? "Guardando" : "Guardar configuracion"}
        </button>
      </div>
      {DEMO_MODE ? (
        <p className="demo-note">Solo lectura: en la demo puedes inspeccionar la configuración, pero no guardarla.</p>
      ) : null}
      {current ? (
        <p className="muted">
          <strong>{current.id}</strong>: {current.description}
        </p>
      ) : null}
      {message ? <p className="alert alert-ok">{message}</p> : null}
      {error ? <p className="alert alert-error">{error}</p> : null}
      {loading ? (
        <p>Cargando configuracion...</p>
      ) : (
        <textarea
          className="config-editor"
          value={content}
          onChange={(event) => setContent(event.target.value)}
          spellCheck={false}
        />
      )}
    </section>
  );
}
