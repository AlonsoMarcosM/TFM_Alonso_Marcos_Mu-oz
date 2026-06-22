"use client";

import { useEffect, useState } from "react";

import { DEMO_MODE } from "@/shared/demoFlag";
import {
  allowedHvdCategoryValues,
  allowedThemeValues,
  defaultSuggestionsByTable,
  fallbackSuggestion,
  fieldGuidance,
  hvdCategoryOptions,
  publishOptions,
  themeOptions,
} from "@/shared/governanceOptions";

type GovernanceRow = Record<string, string>;

const columns = [
  "publicar",
  "schema_name",
  "table_name",
  "table_fqn",
  "titulo_dataset",
  "descripcion_dataset",
  "publicador",
  "tematica_dcat",
  "categoria_hvd",
  "access_url_distribucion",
];

const readonlyColumns = new Set(["schema_name", "table_name", "table_fqn"]);

function validateRows(rows: GovernanceRow[]): string[] {
  const nextErrors: string[] = [];
  rows.forEach((row, index) => {
    const line = index + 2;
    const publish = row.publicar?.trim().toLowerCase();
    if (!["si", "no"].includes(publish)) {
      nextErrors.push(`Fila ${line}: publicar debe ser si o no.`);
    }
    if (publish !== "si") {
      return;
    }
    if (!row.titulo_dataset?.trim()) {
      nextErrors.push(`Fila ${line}: titulo_dataset es obligatorio.`);
    }
    if (!row.descripcion_dataset?.trim()) {
      nextErrors.push(`Fila ${line}: descripcion_dataset es obligatoria.`);
    }
    if (!row.tematica_dcat?.trim()) {
      nextErrors.push(`Fila ${line}: tematica_dcat es obligatoria.`);
    } else if (!allowedThemeValues.includes(row.tematica_dcat.trim())) {
      nextErrors.push(`Fila ${line}: tematica_dcat no está en el vocabulario NTI-RISP permitido.`);
    }
    if (!row.categoria_hvd?.trim()) {
      nextErrors.push(`Fila ${line}: categoria_hvd es obligatoria.`);
    } else if (!allowedHvdCategoryValues.includes(row.categoria_hvd.trim())) {
      nextErrors.push(`Fila ${line}: categoria_hvd no está en el vocabulario HVD permitido.`);
    }
    try {
      const url = new URL(row.access_url_distribucion);
      if (!["http:", "https:"].includes(url.protocol)) {
        nextErrors.push(`Fila ${line}: access_url_distribucion debe ser http(s).`);
      }
    } catch {
      nextErrors.push(`Fila ${line}: access_url_distribucion debe ser una URL válida.`);
    }
  });
  return nextErrors;
}

export function GovernanceEditor() {
  const [rows, setRows] = useState<GovernanceRow[]>([]);
  const [message, setMessage] = useState<string | null>(null);
  const [errors, setErrors] = useState<string[]>([]);
  const [loading, setLoading] = useState(true);

  async function load() {
    setLoading(true);
    const response = await fetch("/api/governance");
    const payload = await response.json();
    setLoading(false);
    if (!response.ok) {
      setErrors([payload.error ?? "No se pudo leer la hoja."]);
      return;
    }
    setRows(payload.rows);
  }

  useEffect(() => {
    void load();
  }, []);

  function update(rowIndex: number, column: string, value: string) {
    setRows((current) =>
      current.map((row, index) => (index === rowIndex ? { ...row, [column]: value } : row)),
    );
  }

  async function save() {
    setMessage(null);
    setErrors([]);
    if (DEMO_MODE) {
      setErrors(["Modo demo (solo lectura): los cambios no se guardan."]);
      return;
    }
    const localErrors = validateRows(rows);
    if (localErrors.length > 0) {
      setErrors(localErrors);
      return;
    }
    const response = await fetch("/api/governance", {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ rows }),
    });
    const payload = await response.json();
    if (!response.ok) {
      setErrors(payload.errors ?? [payload.error ?? "No se pudo guardar."]);
      return;
    }
    setRows(payload.rows);
    setMessage("Hoja guardada correctamente.");
  }

  function fillDefaults() {
    setRows((current) =>
      current.map((row) => {
        const suggestion = defaultSuggestionsByTable[row.table_name] ?? fallbackSuggestion(row.table_name, row.schema_name);
        return {
          ...row,
          publicar: row.publicar?.trim() ? row.publicar : suggestion.publicar,
          titulo_dataset: row.titulo_dataset?.trim() ? row.titulo_dataset : suggestion.titulo_dataset,
          descripcion_dataset: row.descripcion_dataset?.trim() ? row.descripcion_dataset : suggestion.descripcion_dataset,
          publicador: row.publicador?.trim() ? row.publicador : suggestion.publicador,
          tematica_dcat: row.tematica_dcat?.trim() ? row.tematica_dcat : suggestion.tematica_dcat,
          categoria_hvd: row.categoria_hvd?.trim() ? row.categoria_hvd : suggestion.categoria_hvd,
          access_url_distribucion: row.access_url_distribucion?.trim()
            ? row.access_url_distribucion
            : suggestion.access_url_distribucion,
        };
      }),
    );
    setMessage("Sugerencias aplicadas solo en campos vacíos.");
  }

  if (loading) {
    return <p>Cargando hoja gold...</p>;
  }

  return (
    <section className="panel">
      <h2>Hoja gold</h2>
      <p className="muted">
        Los identificadores técnicos son solo lectura. La validación autoritativa la hace Python; la web bloquea los
        errores de vocabulario y formato más frecuentes antes de guardar.
      </p>
      <div className="guidance-grid">
        {fieldGuidance.map((item) => (
          <div className="guidance-item" key={item.field}>
            <strong>{item.field}</strong>
            <span>{item.text}</span>
          </div>
        ))}
      </div>
      {message ? <p className="alert alert-ok">{message}</p> : null}
      {errors.length > 0 ? (
        <div className="alert alert-error">
          {errors.map((error) => (
            <div key={error}>{error}</div>
          ))}
        </div>
      ) : null}
      <div className="table-wrap">
        <table>
          <thead>
            <tr>
              {columns.map((column) => (
                <th key={column}>{column}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {rows.map((row, rowIndex) => (
              <tr key={`${row.table_fqn}-${rowIndex}`}>
                {columns.map((column) => (
                  <td key={column}>
                    {readonlyColumns.has(column) ? (
                      <span className="readonly">{row[column]}</span>
                    ) : column === "publicar" ? (
                      <select value={row[column] ?? "si"} onChange={(event) => update(rowIndex, column, event.target.value)}>
                        {publishOptions.map((option) => (
                          <option key={option.value} value={option.value}>
                            {option.label}
                          </option>
                        ))}
                      </select>
                    ) : column === "tematica_dcat" ? (
                      <select value={row[column] ?? ""} onChange={(event) => update(rowIndex, column, event.target.value)}>
                        <option value="">Seleccionar</option>
                        {themeOptions.map((option) => (
                          <option key={option.value} title={option.uri} value={option.value}>
                            {option.label}
                          </option>
                        ))}
                      </select>
                    ) : column === "categoria_hvd" ? (
                      <select value={row[column] ?? ""} onChange={(event) => update(rowIndex, column, event.target.value)}>
                        <option value="">Seleccionar</option>
                        {hvdCategoryOptions.map((option) => (
                          <option key={option.value} title={option.uri} value={option.value}>
                            {option.label}
                          </option>
                        ))}
                      </select>
                    ) : column === "descripcion_dataset" ? (
                      <textarea value={row[column] ?? ""} onChange={(event) => update(rowIndex, column, event.target.value)} />
                    ) : (
                      <input
                        type={column === "access_url_distribucion" ? "url" : "text"}
                        value={row[column] ?? ""}
                        onChange={(event) => update(rowIndex, column, event.target.value)}
                      />
                    )}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <div className="actions">
        <button onClick={fillDefaults} type="button">
          Autorrellenar vacíos
        </button>
        <button onClick={save} disabled={DEMO_MODE}>Guardar hoja</button>
        <button onClick={load} type="button">
          Recargar
        </button>
      </div>
      {DEMO_MODE ? (
        <p className="demo-note">Solo lectura: en la demo puedes explorar y validar la hoja gold, pero no guardarla.</p>
      ) : null}
    </section>
  );
}
