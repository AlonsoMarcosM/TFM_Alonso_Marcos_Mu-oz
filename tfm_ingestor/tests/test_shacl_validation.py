import hashlib
import json
import warnings
from pathlib import Path

from tfm_ingestor.config import CatalogDefaults, DefaultsConfig
from tfm_ingestor.dcat_export import build_catalog_jsonld
from tfm_ingestor.shacl_validation import (
    bundled_base_shapes_path,
    bundled_base_shapes_paths,
    bundled_dataservice_shape_path,
    bundled_hvd_shapes_paths,
    bundled_shacl_manifest_path,
    validate_jsonld_file,
)


def _defaults() -> DefaultsConfig:
    return DefaultsConfig(
        catalog=CatalogDefaults(
            title="Plataforma de Gobierno del Dato",
            description="Catálogo de validación",
            publisher_name="UCLM",
            publisher_uri="http://datos.gob.es/recurso/sector-publico/org/Organismo/U03400001",
            homepage="https://example.org",
            theme_taxonomy="http://datos.gob.es/kos/sector-publico/sector",
            issued="2026-02-05",
            modified="2026-02-05",
            language="http://publications.europa.eu/resource/authority/language/SPA",
            license_default="https://example.org/legal",
        ),
        dataset_defaults={
            "access_url_base": "https://example.org/datos/plataforma-gobierno-dato",
            "hvd_category_by_theme_tag": {
                "dcat_theme.transporte": "movilidad",
            },
        },
        hvd_defaults={
            "enabled": True,
            "applicable_legislation": "http://data.europa.eu/eli/reg_impl/2023/138/oj",
            "distribution_license": "http://publications.europa.eu/resource/authority/licence/CC_BY_4_0",
            "access_rights": "http://publications.europa.eu/resource/authority/access-right/PUBLIC",
            "service_endpoint_url_base": "https://example.org/api",
            "service_endpoint_description_base": "https://example.org/api-docs",
            "service_documentation_base": "https://example.org/docs",
            "contact": {
                "organization_name": "UCLM",
                "fn": "Oficina de datos abiertos",
                "has_uid": "http://datos.gob.es/recurso/sector-publico/org/Organismo/U03400001",
                "has_email": "mailto:opendata-gobierno-dato@example.org",
                "has_url": "https://example.org/contacto",
                "has_telephone": "tel:+34902000000",
            },
        },
    )


def _doc() -> dict:
    return build_catalog_jsonld(
        tables=[
            {
                "fullyQualifiedName": "svc.db.gold.bici_uso_raw",
                "name": "bici_uso_raw",
                "displayName": "Bici uso",
                "description": "Dataset de uso de bicis",
                "tags": [{"tagFQN": "dcat_theme.transporte"}],
                "extension": {
                    "dcat_publisher_name": "UCLM",
                    "dcat_access_url": "https://example.org/datos/bici-uso",
                },
                "databaseSchema": {"name": "gold"},
            }
        ],
        defaults=_defaults(),
    )


def test_bundled_shapes_exist():
    assert bundled_base_shapes_path().exists()
    assert bundled_shacl_manifest_path().exists()
    assert len(bundled_base_shapes_paths()) == 8
    assert all(path.exists() for path in bundled_base_shapes_paths())
    assert bundled_dataservice_shape_path().exists()
    assert len(bundled_hvd_shapes_paths()) == 4
    assert all(path.exists() for path in bundled_hvd_shapes_paths())


def test_bundled_shapes_manifest_freezes_official_commit():
    manifest_path = bundled_shacl_manifest_path()
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert manifest["source_commit"] == "f2c8a88868b89239c9f54bffdf621cded2401b9f"
    assert manifest["source_path"] == "shacl/1.0.0"
    assert manifest["frozen_date"] == "2026-04-13"
    assert len(manifest["files"]) == 12

    root = manifest_path.parent
    for item in manifest["files"]:
        file_path = root / item["path"]
        assert file_path.exists(), item["path"]
        assert hashlib.sha256(file_path.read_bytes()).hexdigest() == item["sha256"]


def test_validate_jsonld_file_reports_no_violations_for_hvd_profile_and_warnings_can_be_allowed(tmp_path: Path):
    input_path = tmp_path / "catalog.jsonld"
    input_path.write_text(json.dumps(_doc(), ensure_ascii=False, indent=2), encoding="utf-8")

    with warnings.catch_warnings():
        warnings.simplefilter("ignore", DeprecationWarning)
        result_without_allow = validate_jsonld_file(
            input_path=input_path,
            profile_case="hvd",
            allow_warnings=False,
        )
    assert result_without_allow["violations"] == 0
    assert result_without_allow["warnings"] >= 1
    assert result_without_allow["conforms"] is False
    assert result_without_allow["profile_case"] == "hvd"
    assert result_without_allow["shacl_bundle"]["source_commit"] == "f2c8a88868b89239c9f54bffdf621cded2401b9f"
    assert result_without_allow["shacl_bundle"]["files"] == 12

    report_output = tmp_path / "report.ttl"
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", DeprecationWarning)
        result_with_allow = validate_jsonld_file(
            input_path=input_path,
            profile_case="hvd",
            allow_warnings=True,
            report_output=report_output,
        )
    assert result_with_allow["violations"] == 0
    assert result_with_allow["warnings"] >= 1
    assert result_with_allow["conforms"] is True
    assert report_output.exists()
