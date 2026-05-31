import { describe, expect, it } from "vitest";

import { validateGovernanceRows, type GovernanceRow } from "./governanceCsv";

function row(overrides: Partial<GovernanceRow> = {}): GovernanceRow {
  return {
    publicar: "si",
    schema_name: "gold",
    table_name: "movilidad_resumen_municipio",
    table_fqn: "svc.db.gold.movilidad_resumen_municipio",
    titulo_dataset: "Movilidad",
    descripcion_dataset: "Descripcion",
    publicador: "UCLM",
    tematica_dcat: "transporte",
    categoria_hvd: "movilidad",
    access_url_distribucion: "https://example.org/datos",
    ...overrides,
  };
}

describe("validateGovernanceRows", () => {
  it("accepts the basic valid gold row", () => {
    expect(validateGovernanceRows([row()])).toEqual([]);
  });

  it("requires functional fields when publicar is si", () => {
    const errors = validateGovernanceRows([
      row({ titulo_dataset: "", descripcion_dataset: "", tematica_dcat: "", categoria_hvd: "", access_url_distribucion: "nota" }),
    ]);

    expect(errors.join("\n")).toContain("titulo_dataset");
    expect(errors.join("\n")).toContain("descripcion_dataset");
    expect(errors.join("\n")).toContain("tematica_dcat");
    expect(errors.join("\n")).toContain("categoria_hvd");
    expect(errors.join("\n")).toContain("URL");
  });

  it("rejects values outside controlled theme and HVD lists", () => {
    const errors = validateGovernanceRows([
      row({ tematica_dcat: "sanidad", categoria_hvd: "energia" }),
    ]);

    expect(errors.join("\n")).toContain("tematica_dcat debe ser una de");
    expect(errors.join("\n")).toContain("categoria_hvd debe ser una de");
  });

  it("accepts controlled vocabulary values beyond the two reference rows", () => {
    expect(
      validateGovernanceRows([
        row({ tematica_dcat: "medio_ambiente", categoria_hvd: "observacion_de_la_tierra_y_medio_ambiente" }),
      ]),
    ).toEqual([]);
  });
});
