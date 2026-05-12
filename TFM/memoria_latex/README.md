# Memoria TFM en LaTeX (borrador)

Este directorio contiene un borrador inicial de memoria con el contenido técnico ya implementado.

Regla de redacción actual: no presentar CKAN como fuente externa operativa del TFM. CKAN debe aparecer, si procede, solo como alternativa analizada y descartada o como posible destino/federación futura. La memoria debe justificar que PostgreSQL de referencia es el origen canónico porque permite evidenciar gobierno de metadatos desde activos técnicos reproducibles en OpenMetadata, con argumentos DAMA sobre gobierno, gestión de metadatos, linaje, propiedad, calidad y trazabilidad.

Compilación (si tienes LaTeX instalado):

```powershell
pdflatex .\main.tex
```

Diagramas Mermaid:
- Ver `anexos/anexo_e_diagramas_mermaid.tex` para codigo fuente.
- Opcional: convertir Mermaid a SVG con:

```powershell
npx @mermaid-js/mermaid-cli -i .\diagrama.mmd -o .\diagrama.svg
```

Cuando compartas el formato/plantilla oficial, se adaptara esta base.
