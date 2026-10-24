/* =====================================================================
   FraSoHome Live · 02_hr_mkt_fin_ref_xref.sql
   Personas (hr), marketing (mkt), costes (fin), referencia (ref) y
   tablas puente entre dominios (xref).
   Las tablas *_seed guardan tal cual ficheros que no se pueden recalcular
   (puntuaciones de modelos, series agregadas históricas). Llevan los
   nombres de columna del CSV original para que la exportación sea literal.
   ===================================================================== */

IF SCHEMA_ID('hr') IS NULL EXEC('CREATE SCHEMA hr');
GO
IF SCHEMA_ID('mkt') IS NULL EXEC('CREATE SCHEMA mkt');
GO
IF SCHEMA_ID('fin') IS NULL EXEC('CREATE SCHEMA fin');
GO
IF SCHEMA_ID('ref') IS NULL EXEC('CREATE SCHEMA ref');
GO
IF SCHEMA_ID('xref') IS NULL EXEC('CREATE SCHEMA xref');
GO

/* ---------- ref ---------- */

CREATE TABLE ref.department_map (
    department_raw               NVARCHAR(100)   NOT NULL,
    department_std               NVARCHAR(100)   NOT NULL,
    hr_area                      NVARCHAR(100)   NULL,
    business_channel             NVARCHAR(100)   NULL,
    critical_turnover_default    BIT             NOT NULL CONSTRAINT DF_department_map_critical DEFAULT 0,
    CONSTRAINT PK_department_map PRIMARY KEY (department_raw)
);
GO

CREATE TABLE ref.brand_guardrail (
    rule_id                      NVARCHAR(20)    NOT NULL,
    rule_category                NVARCHAR(50)    NOT NULL,
    rule_description             NVARCHAR(500)   NOT NULL,
    applies_to_channel           NVARCHAR(100)   NOT NULL,
    severity                     NVARCHAR(20)    NOT NULL,
    CONSTRAINT PK_brand_guardrail PRIMARY KEY (rule_id)
);
GO

CREATE TABLE ref.calendar (
    date_key                     DATE            NOT NULL,
    year_num                     SMALLINT        NOT NULL,
    month_num                    TINYINT         NOT NULL,
    month_name                   NVARCHAR(20)    NOT NULL,
    quarter_name                 CHAR(2)         NOT NULL,
    period_month                 DATE            NOT NULL,
    month_end                    DATE            NOT NULL,
    CONSTRAINT PK_calendar PRIMARY KEY (date_key)
);
GO

/* Reglas de coste por canal para las transacciones nuevas. Los valores
   salen de las medianas de costes_operativos_transaccion.csv, donde
   margen = ingreso (ya neto de descuento) - coste de producto - costes. */
CREATE TABLE ref.cost_rule (
    channel                      NVARCHAR(20)    NOT NULL,   -- POS | ONLINE
    logistics_eur                DECIMAL(9,2)    NOT NULL,
    packaging_eur                DECIMAL(9,2)    NOT NULL,
    last_mile_eur                DECIMAL(9,2)    NOT NULL,
    payment_pct                  DECIMAL(9,4)    NOT NULL,
    service_eur                  DECIMAL(9,2)    NOT NULL,
    expected_return_pct          DECIMAL(9,4)    NOT NULL,
    cac_pct                      DECIMAL(9,4)    NOT NULL,
    CONSTRAINT PK_cost_rule PRIMARY KEY (channel)
);
GO
INSERT INTO ref.cost_rule (channel, logistics_eur, packaging_eur, last_mile_eur, payment_pct, service_eur, expected_return_pct, cac_pct) VALUES
 (N'POS',    0.00, 1.01, 0.00, 0.0060, 0.89, 0.0360, 0.0024),
 (N'ONLINE', 7.34, 3.81, 6.66, 0.0100, 2.14, 0.0468, 0.0076);
GO

/* ---------- xref ---------- */

CREATE TABLE xref.store_alias (
    alias                        NVARCHAR(100)   NOT NULL,
    canonical_store_id           NVARCHAR(50)    NULL,
    source_context               NVARCHAR(100)   NULL,
    confidence                   NVARCHAR(20)    NULL,
    note                         NVARCHAR(300)   NULL,
    CONSTRAINT PK_store_alias PRIMARY KEY (alias)
);
GO

CREATE TABLE xref.product_alias (
    source_system                NVARCHAR(50)    NOT NULL,
    source_product_id            NVARCHAR(50)    NOT NULL,
    source_product_name          NVARCHAR(150)   NULL,
    source_category_code         NVARCHAR(20)    NULL,
    source_category_name         NVARCHAR(100)   NULL,
    canonical_product_id         NVARCHAR(50)    NULL,
    canonical_product_name       NVARCHAR(255)   NULL,
    canonical_category           NVARCHAR(100)   NULL,
    canonical_subcategory        NVARCHAR(100)   NULL,
    match_method                 NVARCHAR(50)    NULL,
    confidence                   NVARCHAR(20)    NULL,
    note                         NVARCHAR(300)   NULL,
    CONSTRAINT PK_product_alias PRIMARY KEY (source_system, source_product_id)
);
GO

CREATE TABLE xref.employee_alias (
    source_system                NVARCHAR(50)    NOT NULL,
    operational_employee_id      NVARCHAR(50)    NOT NULL,
    canonical_employee_id        NVARCHAR(50)    NOT NULL,
    canonical_employee_location  NVARCHAR(100)   NULL,
    canonical_employee_department NVARCHAR(100)  NULL,
    match_method                 NVARCHAR(50)    NULL,
    confidence                   NVARCHAR(20)    NULL,
    note                         NVARCHAR(300)   NULL,
    CONSTRAINT PK_employee_alias PRIMARY KEY (source_system, operational_employee_id)
);
GO

CREATE TABLE xref.employee_store (
    employee_id                  NVARCHAR(50)    NOT NULL,
    department                   NVARCHAR(100)   NULL,
    location                     NVARCHAR(100)   NULL,
    canonical_store_id           NVARCHAR(50)    NULL,
    assignment_type              NVARCHAR(100)   NULL,
    confidence                   NVARCHAR(20)    NULL,
    CONSTRAINT PK_employee_store PRIMARY KEY (employee_id)
);
GO

/* ---------- hr ---------- */

CREATE TABLE hr.employee (
    employee_id                  NVARCHAR(20)    NOT NULL,
    full_name                    NVARCHAR(200)   NOT NULL,
    gender                       NVARCHAR(20)    NULL,       -- F | M | No declarado
    birth_date                   DATE            NULL,
    hired_at                     DATE            NULL,
    left_at                      DATE            NULL,
    employee_status              NVARCHAR(20)    NOT NULL CONSTRAINT DF_employee_status DEFAULT N'Activo',
    exit_type                    NVARCHAR(50)    NULL,
    exit_reason                  NVARCHAR(200)   NULL,
    department                   NVARCHAR(100)   NULL,
    location                     NVARCHAR(100)   NULL,
    role_name                    NVARCHAR(100)   NULL,
    level_name                   NVARCHAR(50)    NULL,
    contract_type                NVARCHAR(50)    NULL,
    work_schedule                NVARCHAR(20)    NULL,
    manager_id                   NVARCHAR(20)    NULL,
    remote_days_week             TINYINT         NULL,
    commute_km                   DECIMAL(9,1)    NULL,
    source_row_id                NVARCHAR(50)    NULL,
    created_at                   DATETIME2(0)    NOT NULL CONSTRAINT DF_employee_created_at DEFAULT SYSUTCDATETIME(),
    updated_at                   DATETIME2(0)    NOT NULL CONSTRAINT DF_employee_updated_at DEFAULT SYSUTCDATETIME(),
    CONSTRAINT PK_employee PRIMARY KEY (employee_id),
    CONSTRAINT FK_employee_manager FOREIGN KEY (manager_id) REFERENCES hr.employee(employee_id),
    CONSTRAINT CK_employee_status CHECK (employee_status IN (N'Activo', N'Baja')),
    CONSTRAINT CK_employee_dates CHECK (left_at IS NULL OR hired_at IS NULL OR left_at >= hired_at)
);
GO

CREATE TABLE hr.employee_movement (
    movement_id                  NVARCHAR(20)    NOT NULL,
    employee_id                  NVARCHAR(20)    NOT NULL,
    moved_at                     DATE            NULL,
    movement_type                NVARCHAR(50)    NOT NULL,
    department_from              NVARCHAR(100)   NULL,
    department_to                NVARCHAR(100)   NULL,
    level_from                   NVARCHAR(50)    NULL,
    level_to                     NVARCHAR(50)    NULL,
    reason                       NVARCHAR(200)   NULL,
    hr_comment                   NVARCHAR(500)   NULL,
    loaded_by                    NVARCHAR(100)   NULL,
    loaded_at                    DATE            NULL,
    CONSTRAINT PK_employee_movement PRIMARY KEY (movement_id),
    CONSTRAINT FK_employee_movement_employee FOREIGN KEY (employee_id) REFERENCES hr.employee(employee_id)
);
GO

CREATE TABLE hr.absence (
    absence_id                   NVARCHAR(20)    NOT NULL,
    employee_id                  NVARCHAR(20)    NOT NULL,
    start_date                   DATE            NULL,
    end_date                     DATE            NULL,
    absence_type                 NVARCHAR(50)    NOT NULL,
    working_days                 INT             NULL,
    justified                    NVARCHAR(20)    NULL,       -- Sí | No | Pendiente
    notes                        NVARCHAR(300)   NULL,
    CONSTRAINT PK_absence PRIMARY KEY (absence_id),
    CONSTRAINT FK_absence_employee FOREIGN KEY (employee_id) REFERENCES hr.employee(employee_id),
    CONSTRAINT CK_absence_dates CHECK (end_date IS NULL OR start_date IS NULL OR end_date >= start_date)
);
GO

CREATE TABLE hr.overtime (
    overtime_id                  NVARCHAR(20)    NOT NULL,
    employee_id                  NVARCHAR(20)    NOT NULL,
    period_month                 CHAR(7)         NOT NULL,   -- AAAA-MM
    department_reported          NVARCHAR(100)   NULL,
    hours                        DECIMAL(6,2)    NULL,
    reason                       NVARCHAR(100)   NULL,
    approval_status              NVARCHAR(20)    NOT NULL CONSTRAINT DF_overtime_status DEFAULT N'Pendiente',
    approver_id                  NVARCHAR(20)    NULL,
    requested_at                 DATETIME2(0)    NULL,
    decided_at                   DATETIME2(0)    NULL,
    CONSTRAINT PK_overtime PRIMARY KEY (overtime_id),
    CONSTRAINT FK_overtime_employee FOREIGN KEY (employee_id) REFERENCES hr.employee(employee_id),
    CONSTRAINT CK_overtime_status CHECK (approval_status IN (N'Aprobada', N'Pendiente', N'Rechazada')),
    CONSTRAINT CK_overtime_hours CHECK (hours IS NULL OR hours >= 0)
);
GO

CREATE TABLE hr.training (
    training_id                  NVARCHAR(20)    NOT NULL,
    employee_id                  NVARCHAR(20)    NOT NULL,
    course_id                    NVARCHAR(20)    NOT NULL,
    course_name                  NVARCHAR(200)   NULL,
    category                     NVARCHAR(50)    NULL,
    start_date                   DATE            NULL,
    end_date                     DATE            NULL,
    planned_hours                DECIMAL(6,1)    NULL,
    completed_hours              DECIMAL(6,1)    NULL,
    training_status              NVARCHAR(30)    NOT NULL,   -- Completado | En curso | No completado | Inscrito
    cost_eur                     DECIMAL(10,2)   NULL,
    provider                     NVARCHAR(100)   NULL,
    CONSTRAINT PK_training PRIMARY KEY (training_id),
    CONSTRAINT FK_training_employee FOREIGN KEY (employee_id) REFERENCES hr.employee(employee_id)
);
GO

CREATE TABLE hr.performance_review (
    review_id                    NVARCHAR(20)    NOT NULL,
    employee_id                  NVARCHAR(20)    NOT NULL,
    review_cycle                 CHAR(4)         NOT NULL,
    reviewed_at                  DATE            NULL,
    overall_score                DECIMAL(3,1)    NULL,
    objectives_pct               DECIMAL(6,1)    NULL,
    competencies_score           DECIMAL(3,1)    NULL,
    potential                    NVARCHAR(20)    NULL,
    reviewer_id                  NVARCHAR(20)    NULL,
    manager_comment              NVARCHAR(500)   NULL,
    source_system                NVARCHAR(50)    NULL,
    CONSTRAINT PK_performance_review PRIMARY KEY (review_id),
    CONSTRAINT FK_performance_review_employee FOREIGN KEY (employee_id) REFERENCES hr.employee(employee_id),
    CONSTRAINT CK_performance_review_score CHECK (overall_score IS NULL OR overall_score BETWEEN 1 AND 5)
);
GO

CREATE TABLE hr.compensation (
    payroll_id                   NVARCHAR(20)    NOT NULL,
    employee_id                  NVARCHAR(20)    NOT NULL,
    period_month                 CHAR(7)         NOT NULL,
    base_salary_eur              DECIMAL(12,2)   NULL,
    variable_salary_eur          DECIMAL(12,2)   NULL,
    increase_pct                 DECIMAL(6,2)    NULL,
    currency_code                CHAR(3)         NOT NULL CONSTRAINT DF_compensation_currency DEFAULT 'EUR',
    source_system                NVARCHAR(50)    NULL,
    loaded_at                    DATE            NULL,
    CONSTRAINT PK_compensation PRIMARY KEY (payroll_id),
    CONSTRAINT FK_compensation_employee FOREIGN KEY (employee_id) REFERENCES hr.employee(employee_id)
);
GO

/* Foto de frasohome_people_analytics.csv. Las puntuaciones de riesgo
   no se pueden recalcular; la exportación superpone encima los campos
   que gobierna hr.employee (departamento, estado, salida, salario...). */
CREATE TABLE hr.people_analytics_seed (
    employee_id NVARCHAR(20) NOT NULL, nombre_anonimizado NVARCHAR(200) NULL, genero NVARCHAR(20) NULL,
    edad INT NULL, departamento NVARCHAR(100) NULL, ubicacion NVARCHAR(100) NULL, rol NVARCHAR(100) NULL,
    nivel NVARCHAR(50) NULL, tipo_contrato NVARCHAR(50) NULL, jornada NVARCHAR(20) NULL, fecha_alta DATE NULL,
    fecha_salida DATE NULL, estado_actual NVARCHAR(20) NULL, tipo_salida NVARCHAR(50) NULL, motivo_salida NVARCHAR(200) NULL,
    abandono_voluntario_24m BIT NULL, salida_24m BIT NULL, activo_actual BIT NULL, antiguedad_meses INT NULL,
    evaluacion_desempeno_1_5 DECIMAL(3,1) NULL, promociones_24m INT NULL, incremento_salarial_12m_pct DECIMAL(6,2) NULL,
    salario_anual_eur INT NULL, horas_formacion_12m INT NULL, satisfaccion_1_10 DECIMAL(4,1) NULL,
    engagement_1_10 DECIMAL(4,1) NULL, enps INT NULL, calidad_manager_1_5 DECIMAL(3,1) NULL,
    desarrollo_carrera_1_5 DECIMAL(3,1) NULL, reconocimiento_1_5 DECIMAL(3,1) NULL, percepcion_salario_1_5 DECIMAL(3,1) NULL,
    balance_vida_trabajo_1_5 DECIMAL(3,1) NULL, carga_trabajo_1_5 DECIMAL(3,1) NULL, absentismo_dias_12m INT NULL,
    horas_extra_media_mes DECIMAL(6,1) NULL, teletrabajo_dias_semana INT NULL, distancia_casa_trabajo_km DECIMAL(9,1) NULL,
    probabilidad_abandono DECIMAL(6,3) NULL, riesgo_abandono NVARCHAR(20) NULL, alto_riesgo_flag BIT NULL,
    talento_clave_flag BIT NULL, prioridad_retencion NVARCHAR(30) NULL, conteo_empleado INT NULL,
    comentario_salida NVARCHAR(1000) NULL, comentario_clima NVARCHAR(1000) NULL,
    CONSTRAINT PK_people_analytics_seed PRIMARY KEY (employee_id)
);
GO

/* Foto de frasohome_rotacion_mensual.csv. Los meses posteriores al último
   de la foto los calcula la exportación a partir de hr.employee. */
CREATE TABLE hr.turnover_monthly_seed (
    periodo_mes DATE NOT NULL, departamento NVARCHAR(100) NOT NULL, headcount_inicio_mes INT NULL, altas_mes INT NULL,
    bajas_voluntarias_mes INT NULL, bajas_no_voluntarias_mes INT NULL, bajas_totales_mes INT NULL, headcount_fin_mes INT NULL,
    tasa_rotacion_voluntaria_pct DECIMAL(9,2) NULL, tasa_rotacion_total_pct DECIMAL(9,2) NULL,
    empleados_alto_riesgo_fin_mes INT NULL, talento_clave_alto_riesgo_fin_mes INT NULL,
    salario_medio_activos_mes_eur INT NULL, satisfaccion_media_activos_mes DECIMAL(4,2) NULL,
    engagement_medio_activos_mes DECIMAL(4,2) NULL, area_critica_rotacion_flag BIT NULL,
    CONSTRAINT PK_turnover_monthly_seed PRIMARY KEY (periodo_mes, departamento)
);
GO

/* ---------- mkt ---------- */

CREATE TABLE mkt.campaign (
    campaign_id                  NVARCHAR(30)    NOT NULL,
    campaign_name                NVARCHAR(200)   NOT NULL,
    objective                    NVARCHAR(50)    NOT NULL,
    channel                      NVARCHAR(20)    NOT NULL,   -- EMAIL | SMS | PUSH
    starts_at                    DATETIME2(0)    NOT NULL,
    ends_at                      DATETIME2(0)    NOT NULL,
    target_segment               NVARCHAR(50)    NOT NULL,
    target_category              NVARCHAR(100)   NULL,
    target_subcategory           NVARCHAR(100)   NULL,
    target_store_id              NVARCHAR(50)    NULL,
    offer_type                   NVARCHAR(30)    NOT NULL,
    discount_pct                 DECIMAL(5,2)    NOT NULL CONSTRAINT DF_campaign_discount DEFAULT 0,
    budget_eur                   DECIMAL(12,2)   NULL,
    control_group_pct            DECIMAL(5,3)    NOT NULL CONSTRAINT DF_campaign_control DEFAULT 0.10,
    primary_kpi                  NVARCHAR(50)    NULL,
    campaign_status              NVARCHAR(20)    NOT NULL CONSTRAINT DF_campaign_status DEFAULT N'borrador',
    copy_axis                    NVARCHAR(500)   NULL,
    created_by                   NVARCHAR(100)   NULL,
    created_at                   DATETIME2(0)    NOT NULL CONSTRAINT DF_campaign_created DEFAULT SYSUTCDATETIME(),
    updated_at                   DATETIME2(0)    NOT NULL CONSTRAINT DF_campaign_updated DEFAULT SYSUTCDATETIME(),
    CONSTRAINT PK_campaign PRIMARY KEY (campaign_id),
    CONSTRAINT FK_campaign_store FOREIGN KEY (target_store_id) REFERENCES store.store(store_id),
    CONSTRAINT CK_campaign_status CHECK (campaign_status IN (N'borrador', N'audiencia', N'activa', N'finalizada', N'cancelada')),
    CONSTRAINT CK_campaign_channel CHECK (channel IN (N'EMAIL', N'SMS', N'PUSH')),
    CONSTRAINT CK_campaign_dates CHECK (ends_at >= starts_at),
    CONSTRAINT CK_campaign_control CHECK (control_group_pct BETWEEN 0 AND 0.5)
);
GO

CREATE TABLE mkt.campaign_contact (
    contact_id                   NVARCHAR(30)    NOT NULL,
    campaign_id                  NVARCHAR(30)    NOT NULL,
    customer_id                  NVARCHAR(50)    NOT NULL,
    contacted_at                 DATETIME2(0)    NULL,
    contact_channel              NVARCHAR(20)    NOT NULL,
    experiment_group             NVARCHAR(20)    NOT NULL,   -- treatment | control
    is_control                   BIT             NOT NULL,
    assigned_segment             NVARCHAR(50)    NULL,
    offer_code                   NVARCHAR(30)    NULL,
    coupon_instance_id           NVARCHAR(30)    NULL,
    delivery_status              NVARCHAR(30)    NOT NULL,   -- pendiente | entregado | holdout_control | bounce | rechazado | fallido
    contact_cost_eur             DECIMAL(9,3)    NOT NULL CONSTRAINT DF_contact_cost DEFAULT 0,
    contact_priority             NVARCHAR(20)    NULL,
    personalized_store_id        NVARCHAR(50)    NULL,
    recommended_product_1        NVARCHAR(50)    NULL,
    recommended_product_2        NVARCHAR(50)    NULL,
    app_user_id                  NVARCHAR(30)    NULL,
    conversion_30d               BIT             NOT NULL CONSTRAINT DF_contact_conversion DEFAULT 0,
    conversion_order_id          NVARCHAR(50)    NULL,
    conversion_ticket_id         NVARCHAR(50)    NULL,
    revenue_30d_eur              DECIMAL(12,2)   NOT NULL CONSTRAINT DF_contact_revenue DEFAULT 0,
    margin_30d_eur               DECIMAL(12,2)   NOT NULL CONSTRAINT DF_contact_margin DEFAULT 0,
    converted_at                 DATETIME2(0)    NULL,
    CONSTRAINT PK_campaign_contact PRIMARY KEY (contact_id),
    CONSTRAINT FK_campaign_contact_campaign FOREIGN KEY (campaign_id) REFERENCES mkt.campaign(campaign_id),
    CONSTRAINT FK_campaign_contact_customer FOREIGN KEY (customer_id) REFERENCES crm.customer(customer_id),
    CONSTRAINT CK_campaign_contact_group CHECK (experiment_group IN (N'treatment', N'control'))
);
GO

CREATE TABLE mkt.coupon (
    coupon_instance_id           NVARCHAR(30)    NOT NULL,
    coupon_code                  NVARCHAR(30)    NOT NULL,
    campaign_id                  NVARCHAR(30)    NULL,       -- NULL: compensación de atención al cliente
    customer_id                  NVARCHAR(50)    NOT NULL,
    issued_at                    DATETIME2(0)    NOT NULL,
    valid_from                   DATETIME2(0)    NOT NULL,
    valid_to                     DATETIME2(0)    NOT NULL,
    coupon_type                  NVARCHAR(20)    NOT NULL,   -- porcentaje | importe_fijo
    discount_pct                 DECIMAL(5,2)    NULL,
    discount_eur                 DECIMAL(10,2)   NULL,
    min_spend_eur                DECIMAL(10,2)   NOT NULL CONSTRAINT DF_coupon_min_spend DEFAULT 0,
    restricted_category          NVARCHAR(100)   NULL,
    restricted_store_id          NVARCHAR(50)    NULL,
    issue_channel                NVARCHAR(20)    NULL,
    coupon_status                NVARCHAR(20)    NOT NULL CONSTRAINT DF_coupon_status DEFAULT N'emitido',
    redeemed_at                  DATETIME2(0)    NULL,
    order_id                     NVARCHAR(50)    NULL,
    ticket_id                    NVARCHAR(50)    NULL,
    basket_eur                   DECIMAL(12,2)   NULL,
    discount_applied_eur         DECIMAL(12,2)   NULL,
    margin_after_discount_eur    DECIMAL(12,2)   NULL,
    CONSTRAINT PK_coupon PRIMARY KEY (coupon_instance_id),
    CONSTRAINT UQ_coupon_code UNIQUE (coupon_code),
    CONSTRAINT FK_coupon_campaign FOREIGN KEY (campaign_id) REFERENCES mkt.campaign(campaign_id),
    CONSTRAINT FK_coupon_customer FOREIGN KEY (customer_id) REFERENCES crm.customer(customer_id),
    CONSTRAINT CK_coupon_status CHECK (coupon_status IN (N'emitido', N'canjeado', N'expirado', N'anulado')),
    CONSTRAINT CK_coupon_type CHECK (coupon_type IN (N'porcentaje', N'importe_fijo'))
);
GO

CREATE TABLE mkt.promotion (
    promo_id                     NVARCHAR(30)    NOT NULL,
    promo_name                   NVARCHAR(200)   NOT NULL,
    starts_at                    DATETIME2(0)    NOT NULL,
    ends_at                      DATETIME2(0)    NOT NULL,
    scope_type                   NVARCHAR(30)    NOT NULL,   -- categoria | categoria_tienda | campana
    scope_id                     NVARCHAR(150)   NOT NULL,
    promo_type                   NVARCHAR(30)    NOT NULL,
    discount_pct                 DECIMAL(5,2)    NULL,
    discount_eur                 DECIMAL(10,2)   NULL,
    channel                      NVARCHAR(20)    NOT NULL,
    target_segment               NVARCHAR(50)    NULL,
    store_id                     NVARCHAR(50)    NULL,
    combinable                   BIT             NOT NULL CONSTRAINT DF_promotion_combinable DEFAULT 0,
    basket_threshold_eur         DECIMAL(10,2)   NOT NULL CONSTRAINT DF_promotion_threshold DEFAULT 0,
    min_margin_pct               DECIMAL(5,2)    NULL,
    related_campaign_id          NVARCHAR(30)    NULL,
    CONSTRAINT PK_promotion PRIMARY KEY (promo_id),
    CONSTRAINT FK_promotion_campaign FOREIGN KEY (related_campaign_id) REFERENCES mkt.campaign(campaign_id),
    CONSTRAINT FK_promotion_store FOREIGN KEY (store_id) REFERENCES store.store(store_id),
    CONSTRAINT CK_promotion_dates CHECK (ends_at >= starts_at)
);
GO

/* Afinidad cliente-tienda: se siembra desde el CSV y se recalcula a
   demanda con mkt.usp_affinity_recalculate. */
CREATE TABLE mkt.customer_store_affinity (
    customer_id                  NVARCHAR(50)    NOT NULL,
    preferred_store_id           NVARCHAR(50)    NULL,
    nearest_store_id             NVARCHAR(50)    NULL,
    nearest_store_km             DECIMAL(9,1)    NULL,
    store_visits_12m             INT             NULL,
    store_spend_12m_eur          DECIMAL(12,2)   NULL,
    online_spend_12m_eur         DECIMAL(12,2)   NULL,
    click_collect_propensity     DECIMAL(6,3)    NULL,
    visit_probability_30d        DECIMAL(6,3)    NULL,
    local_cluster                NVARCHAR(50)    NULL,
    locally_capturable           BIT             NULL,
    home_city                    NVARCHAR(100)   NULL,
    home_province                NVARCHAR(100)   NULL,
    recalculated_at              DATETIME2(0)    NULL,
    CONSTRAINT PK_customer_store_affinity PRIMARY KEY (customer_id),
    CONSTRAINT FK_affinity_customer FOREIGN KEY (customer_id) REFERENCES crm.customer(customer_id)
);
GO

/* ---------- fin ---------- */

CREATE TABLE fin.transaction_cost (
    transaction_cost_id          NVARCHAR(30)    NOT NULL,
    document_type                NVARCHAR(10)    NOT NULL,   -- TICKET | ORDER
    order_id                     NVARCHAR(50)    NULL,
    ticket_id                    NVARCHAR(50)    NULL,
    customer_id                  NVARCHAR(50)    NULL,
    transaction_at               DATETIME2(0)    NULL,
    channel                      NVARCHAR(20)    NOT NULL,
    store_id                     NVARCHAR(50)    NULL,
    main_category                NVARCHAR(100)   NULL,
    gross_revenue_eur            DECIMAL(12,2)   NULL,
    discount_eur                 DECIMAL(12,2)   NULL,
    product_cost_eur             DECIMAL(12,2)   NULL,
    logistics_cost_eur           DECIMAL(12,2)   NULL,
    packaging_cost_eur           DECIMAL(12,2)   NULL,
    last_mile_cost_eur           DECIMAL(12,2)   NULL,
    payment_cost_eur             DECIMAL(12,2)   NULL,
    service_cost_eur             DECIMAL(12,2)   NULL,
    expected_return_cost_eur     DECIMAL(12,2)   NULL,
    cac_eur                      DECIMAL(12,2)   NULL,
    attributed_campaign_id       NVARCHAR(30)    NULL,
    net_contribution_eur         DECIMAL(12,2)   NULL,
    CONSTRAINT PK_transaction_cost PRIMARY KEY (transaction_cost_id),
    CONSTRAINT CK_transaction_cost_doc CHECK (document_type IN (N'TICKET', N'ORDER'))
);
GO

CREATE INDEX IX_employee_department ON hr.employee(department, employee_status);
CREATE INDEX IX_employee_manager ON hr.employee(manager_id);
CREATE INDEX IX_absence_employee ON hr.absence(employee_id, start_date);
CREATE INDEX IX_overtime_employee ON hr.overtime(employee_id, period_month);
CREATE INDEX IX_overtime_status ON hr.overtime(approval_status);
CREATE INDEX IX_training_employee ON hr.training(employee_id);
CREATE INDEX IX_review_employee ON hr.performance_review(employee_id, review_cycle);
CREATE INDEX IX_compensation_employee ON hr.compensation(employee_id, period_month);
CREATE INDEX IX_movement_employee ON hr.employee_movement(employee_id, moved_at);
CREATE INDEX IX_contact_campaign ON mkt.campaign_contact(campaign_id);
CREATE INDEX IX_contact_customer ON mkt.campaign_contact(customer_id);
CREATE INDEX IX_coupon_customer ON mkt.coupon(customer_id, coupon_status);
CREATE INDEX IX_coupon_campaign ON mkt.coupon(campaign_id);
CREATE INDEX IX_transaction_cost_order ON fin.transaction_cost(order_id);
CREATE INDEX IX_transaction_cost_ticket ON fin.transaction_cost(ticket_id);
GO
