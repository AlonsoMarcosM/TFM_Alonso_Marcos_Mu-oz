-- database: opendata_demo

CREATE SCHEMA IF NOT EXISTS bronze;
CREATE SCHEMA IF NOT EXISTS silver;
CREATE SCHEMA IF NOT EXISTS gold;

-- BRONZE (crudo)
CREATE TABLE IF NOT EXISTS bronze.bici_uso_raw (
  event_id        BIGSERIAL PRIMARY KEY,
  ts              TIMESTAMP NOT NULL,
  estacion_id     INT NOT NULL,
  viajes          INT NOT NULL,
  fuente          TEXT NOT NULL DEFAULT 'sensor'
);

CREATE TABLE IF NOT EXISTS bronze.eventos_raw (
  evento_id       BIGSERIAL PRIMARY KEY,
  titulo          TEXT NOT NULL,
  fecha           DATE NOT NULL,
  municipio       TEXT NOT NULL,
  categoria       TEXT NOT NULL,
  asistentes_est  INT
);

-- SILVER (limpio)
CREATE TABLE IF NOT EXISTS silver.bici_uso_diario (
  fecha           DATE NOT NULL,
  estacion_id     INT NOT NULL,
  viajes_totales  INT NOT NULL,
  PRIMARY KEY (fecha, estacion_id)
);

CREATE TABLE IF NOT EXISTS silver.eventos_normalizados (
  evento_id       BIGINT PRIMARY KEY,
  titulo          TEXT NOT NULL,
  fecha           DATE NOT NULL,
  municipio       TEXT NOT NULL,
  categoria_std   TEXT NOT NULL,
  asistentes_est  INT
);

-- GOLD (publicable)
CREATE TABLE IF NOT EXISTS gold.movilidad_resumen_municipio (
  fecha           DATE NOT NULL,
  municipio       TEXT NOT NULL,
  viajes_totales  INT NOT NULL,
  PRIMARY KEY (fecha, municipio)
);

CREATE TABLE IF NOT EXISTS gold.agenda_cultural_publica (
  evento_id       BIGINT PRIMARY KEY,
  titulo          TEXT NOT NULL,
  fecha           DATE NOT NULL,
  municipio       TEXT NOT NULL,
  categoria       TEXT NOT NULL,
  asistentes_est  INT
);

-- DATOS INVENTADOS (pocos, solo para demo)
INSERT INTO bronze.bici_uso_raw (ts, estacion_id, viajes, fuente) VALUES
('2026-01-10 08:00:00', 101, 12, 'sensor'),
('2026-01-10 09:00:00', 101, 18, 'sensor'),
('2026-01-10 10:00:00', 202,  7, 'sensor');

INSERT INTO bronze.eventos_raw (titulo, fecha, municipio, categoria, asistentes_est) VALUES
('Concierto Plaza Mayor', '2026-02-15', 'Albacete', 'musica', 1200),
('Feria de Innovacion',   '2026-03-02', 'Ciudad Real', 'tecnologia', 800),
('Teatro Familiar',       '2026-02-20', 'Toledo', 'teatro', 350);

