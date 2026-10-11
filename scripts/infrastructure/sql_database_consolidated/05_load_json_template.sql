-- Plantilla de carga JSON.
-- Sustituye @json_payload por el contenido del archivo JSON.

EXEC [admin].[load_json_document]
    @source_path = N'01_datos/ejemplo.json',
    @document_type = N'ejemplo',
    @json_payload = N'{
        "caso": "FraSoHome",
        "descripcion": "Payload JSON de ejemplo",
        "dominio": "demo"
    }';
GO
