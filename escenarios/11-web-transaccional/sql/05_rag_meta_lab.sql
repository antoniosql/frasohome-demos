/* =====================================================================
   FraSoHome Live · 07_rag_meta_lab.sql
   rag:  semilla del universo de Copilot Studio (identificadores propios:
         MAD01, FSH-MUE-SOF-1000...). Las vistas exp_rag añaden después la
         actividad nueva traducida con xref.
   meta: catálogos, diccionarios y material docente, fila a fila.
   lab:  material de laboratorio (verdad conocida, juegos de evaluación).
   Las columnas conservan el nombre del CSV de origen.
   ===================================================================== */

IF SCHEMA_ID('rag') IS NULL EXEC('CREATE SCHEMA rag');
GO
IF SCHEMA_ID('meta') IS NULL EXEC('CREATE SCHEMA meta');
GO
IF SCHEMA_ID('lab') IS NULL EXEC('CREATE SCHEMA lab');
GO

CREATE TABLE rag.customer (
    CustomerID NVARCHAR(20) NOT NULL, Tier NVARCHAR(20) NULL, JoinDate DATE NULL,
    City NVARCHAR(100) NULL, ConsentMarketing NVARCHAR(5) NULL,
    CONSTRAINT PK_rag_customer PRIMARY KEY (CustomerID)
);
GO
CREATE TABLE rag.product (
    ProductID NVARCHAR(30) NOT NULL, ProductName NVARCHAR(150) NULL, CategoryFamily NVARCHAR(10) NULL,
    CategoryCode NVARCHAR(10) NULL, CategoryName NVARCHAR(50) NULL, Material NVARCHAR(50) NULL, Color NVARCHAR(50) NULL,
    BulkyFlag NVARCHAR(5) NULL, StandardCostEUR DECIMAL(12,2) NULL, ListPriceEUR DECIMAL(12,2) NULL, Status NVARCHAR(20) NULL,
    CONSTRAINT PK_rag_product PRIMARY KEY (ProductID)
);
GO
CREATE TABLE rag.store (
    StoreID NVARCHAR(20) NOT NULL, StoreName NVARCHAR(100) NULL, City NVARCHAR(100) NULL, Region NVARCHAR(50) NULL,
    CONSTRAINT PK_rag_store PRIMARY KEY (StoreID)
);
GO
CREATE TABLE rag.stock_daily (
    [Date] DATE NOT NULL, StoreID NVARCHAR(20) NOT NULL, ProductID NVARCHAR(30) NOT NULL,
    OnHandUnits INT NULL, ReservedUnits INT NULL, BlockedUnits INT NULL, AvailableUnits INT NULL,
    CONSTRAINT PK_rag_stock_daily PRIMARY KEY ([Date], StoreID, ProductID)
);
GO
CREATE TABLE rag.sales_daily (
    [Date] DATE NOT NULL, Channel NVARCHAR(20) NOT NULL, StoreID NVARCHAR(20) NOT NULL,
    GrossSalesEUR DECIMAL(12,2) NULL, DiscountsEUR DECIMAL(12,2) NULL, PointsDiscountEUR DECIMAL(12,2) NULL,
    ReturnsEUR DECIMAL(12,2) NULL, NetSalesEUR DECIMAL(12,2) NULL, Orders INT NULL,
    CONSTRAINT PK_rag_sales_daily PRIMARY KEY ([Date], Channel, StoreID)
);
GO
CREATE TABLE rag.return_fact (
    ReturnID NVARCHAR(30) NOT NULL, ReturnDate DATE NULL, Channel NVARCHAR(20) NULL, StoreID NVARCHAR(20) NULL,
    CustomerID NVARCHAR(20) NULL, ProductID NVARCHAR(30) NULL, Units INT NULL, RefundAmountEUR DECIMAL(12,2) NULL,
    ReasonCode NVARCHAR(10) NULL, ReasonDesc NVARCHAR(100) NULL, Condition NVARCHAR(20) NULL, Approved NVARCHAR(5) NULL,
    CONSTRAINT PK_rag_return_fact PRIMARY KEY (ReturnID)
);
GO
CREATE TABLE rag.stockout_alert (
    AlertDate DATE NOT NULL, StoreID NVARCHAR(20) NOT NULL, ProductID NVARCHAR(30) NOT NULL,
    AvailableUnits INT NULL, SalesUnitsLast7d INT NULL, Priority NVARCHAR(10) NULL,
    CONSTRAINT PK_rag_stockout_alert PRIMARY KEY (AlertDate, StoreID, ProductID)
);
GO

/* Ficheros de metadatos: cada fila como objeto JSON con las columnas del CSV
   (nvarchar, no el tipo json, para que el mirroring futuro la admita). */
CREATE TABLE meta.reference_file (
    file_path                    NVARCHAR(260)   NOT NULL,   -- ruta relativa a datos/
    column_list                  NVARCHAR(2000)  NOT NULL,   -- cabecera original, separada por comas
    has_bom                      BIT             NOT NULL,
    description                  NVARCHAR(300)   NULL,
    CONSTRAINT PK_reference_file PRIMARY KEY (file_path)
);
GO
CREATE TABLE meta.reference_row (
    file_path                    NVARCHAR(260)   NOT NULL,
    row_num                      INT             NOT NULL,
    row_json                     NVARCHAR(MAX)   NOT NULL,
    CONSTRAINT PK_reference_row PRIMARY KEY (file_path, row_num),
    CONSTRAINT FK_reference_row_file FOREIGN KEY (file_path) REFERENCES meta.reference_file(file_path),
    CONSTRAINT CK_reference_row_json CHECK (ISJSON(row_json) = 1)
);
GO

CREATE TABLE lab.identity_ground_truth (
    identity_signal_id NVARCHAR(30) NOT NULL, customer_id_canonico NVARCHAR(20) NOT NULL,
    CONSTRAINT PK_identity_ground_truth PRIMARY KEY (identity_signal_id)
);
GO
CREATE TABLE lab.rag_test_case (
    test_set                     NVARCHAR(30)    NOT NULL,   -- Documental | Metrico_Mixto
    row_num                      INT             NOT NULL,
    question                     NVARCHAR(1000)  NOT NULL,
    expected_response            NVARCHAR(2000)  NOT NULL,
    updated_by                   NVARCHAR(100)   NULL,
    updated_at                   DATETIME2(0)    NULL,
    CONSTRAINT PK_rag_test_case PRIMARY KEY (test_set, row_num)
);
GO
CREATE TABLE lab.prompt_sample (
    employee_id NVARCHAR(20) NOT NULL, departamento NVARCHAR(100) NULL, ubicacion NVARCHAR(100) NULL,
    rol NVARCHAR(100) NULL, nivel NVARCHAR(50) NULL, fecha_salida DATE NULL, tipo_salida NVARCHAR(50) NULL,
    motivo_salida_sistema NVARCHAR(200) NULL, comentario_salida NVARCHAR(1000) NULL,
    satisfaccion_1_10 DECIMAL(4,1) NULL, probabilidad_abandono DECIMAL(6,3) NULL,
    CONSTRAINT PK_prompt_sample PRIMARY KEY (employee_id)
);
GO

CREATE PROCEDURE lab.usp_rag_test_case_upsert
    @test_set NVARCHAR(30), @row_num INT = NULL, @question NVARCHAR(1000), @expected_response NVARCHAR(2000), @user_login NVARCHAR(100)
AS
BEGIN
    SET NOCOUNT ON;
    IF @test_set NOT IN (N'Documental', N'Metrico_Mixto') THROW 50030, N'Juego de evaluación desconocido.', 1;
    IF LEN(LTRIM(@question)) = 0 OR LEN(LTRIM(@expected_response)) = 0 THROW 50031, N'Pregunta y respuesta esperada son obligatorias.', 1;
    IF @row_num IS NULL
        SET @row_num = 1 + ISNULL((SELECT MAX(row_num) FROM lab.rag_test_case WHERE test_set = @test_set), 0);
    MERGE lab.rag_test_case AS t
    USING (SELECT @test_set AS test_set, @row_num AS row_num) AS s
       ON t.test_set = s.test_set AND t.row_num = s.row_num
    WHEN MATCHED THEN UPDATE SET question = @question, expected_response = @expected_response,
                                 updated_by = @user_login, updated_at = SYSUTCDATETIME()
    WHEN NOT MATCHED THEN INSERT (test_set, row_num, question, expected_response, updated_by, updated_at)
                          VALUES (@test_set, @row_num, @question, @expected_response, @user_login, SYSUTCDATETIME());
    SELECT @row_num AS row_num;
END
GO

CREATE PROCEDURE lab.usp_rag_test_case_delete @test_set NVARCHAR(30), @row_num INT
AS
BEGIN
    SET NOCOUNT ON;
    DELETE FROM lab.rag_test_case WHERE test_set = @test_set AND row_num = @row_num;
END
GO
