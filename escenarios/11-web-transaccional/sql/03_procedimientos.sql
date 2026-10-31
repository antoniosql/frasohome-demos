/* =====================================================================
   FraSoHome Live · 03_procedimientos.sql
   Transacciones de la web: venta online y en tienda, devoluciones, stock,
   catálogo, tiendas, CRM, campañas, promociones y RR. HH.

   - Toda escritura de la aplicación pasa por un procedimiento: el usuario
     SQL de la API (fsh_api) solo tiene SELECT y EXECUTE.
   - Errores de negocio: THROW 50100-50599 con un mensaje en español que la
     API muestra tal cual al usuario.
   - Los documentos para Cosmos DB se encolan en app.outbox dentro de la
     misma transacción; la API los envía después (primero SQL, la verdad del
     dinero; después Cosmos).
   - CREATE OR ALTER: se puede volver a aplicar sin tocar los datos
     (seed/load_sql.py --solo-procedimientos, que lanza tools/configurar_api.ps1).
   ===================================================================== */

/* ---------- utilidades ---------- */

/* Aplica un movimiento de stock y lo registra. Crea la fila de stock si no
   existe. En VENTA y ENVIO exige stock disponible (en mano - reservado). */
CREATE OR ALTER PROCEDURE inventory.usp_apply_stock_delta
    @store_id NVARCHAR(50), @product_id NVARCHAR(50), @movement_type NVARCHAR(30),
    @on_hand_delta INT = 0, @reserved_delta INT = 0, @in_transit_delta INT = 0,
    @document_type NVARCHAR(30) = NULL, @document_id NVARCHAR(50) = NULL,
    @user_login NVARCHAR(100) = NULL, @notes NVARCHAR(500) = NULL
AS
BEGIN
    SET NOCOUNT ON;
    SET XACT_ABORT ON;
    IF NOT EXISTS (SELECT 1 FROM inventory.stock_level WITH (UPDLOCK, HOLDLOCK) WHERE store_id = @store_id AND product_id = @product_id)
        INSERT INTO inventory.stock_level (store_id, product_id) VALUES (@store_id, @product_id);

    DECLARE @on_hand INT, @reserved INT, @transit INT;
    SELECT @on_hand = on_hand_qty, @reserved = reserved_qty, @transit = in_transit_qty
    FROM inventory.stock_level WITH (UPDLOCK) WHERE store_id = @store_id AND product_id = @product_id;

    IF @movement_type IN (N'VENTA', N'ENVIO') AND (@on_hand + @on_hand_delta) - (@reserved + @reserved_delta) < 0
    BEGIN
        DECLARE @msg NVARCHAR(300) = CONCAT(N'Stock insuficiente de ', @product_id, N' en ', @store_id,
            N': disponibles ', @on_hand - @reserved, N', pedidas ', -@on_hand_delta, N'.');
        THROW 50100, @msg, 1;
    END
    IF @on_hand + @on_hand_delta < 0 OR @reserved + @reserved_delta < 0 OR @transit + @in_transit_delta < 0
    BEGIN
        DECLARE @msg2 NVARCHAR(300) = CONCAT(N'El movimiento dejaría stock negativo de ', @product_id, N' en ', @store_id, N'.');
        THROW 50101, @msg2, 1;
    END

    UPDATE inventory.stock_level
       SET on_hand_qty = on_hand_qty + @on_hand_delta,
           reserved_qty = reserved_qty + @reserved_delta,
           in_transit_qty = in_transit_qty + @in_transit_delta,
           updated_at = SYSUTCDATETIME()
     WHERE store_id = @store_id AND product_id = @product_id;

    INSERT INTO inventory.stock_movement (store_id, product_id, movement_type, on_hand_delta, reserved_delta, in_transit_delta,
                                          document_type, document_id, user_login, notes)
    VALUES (@store_id, @product_id, @movement_type, @on_hand_delta, @reserved_delta, @in_transit_delta,
            @document_type, @document_id, @user_login, @notes);
END
GO

/* Registra el coste operativo de una venta con las reglas de ref.cost_rule.
   margen = ingreso neto - coste de producto - costes operativos. */
CREATE OR ALTER PROCEDURE fin.usp_record_transaction_cost
    @document_type NVARCHAR(10), @order_id NVARCHAR(50) = NULL, @ticket_id NVARCHAR(50) = NULL,
    @customer_id NVARCHAR(50) = NULL, @transaction_at DATETIME2(0), @channel NVARCHAR(20),
    @store_id NVARCHAR(50) = NULL, @main_category NVARCHAR(100) = NULL,
    @revenue_eur DECIMAL(12,2), @discount_eur DECIMAL(12,2), @product_cost_eur DECIMAL(12,2),
    @cash_payment BIT = 0, @campaign_id NVARCHAR(30) = NULL
AS
BEGIN
    SET NOCOUNT ON;
    DECLARE @first BIGINT, @prefix NVARCHAR(30), @width TINYINT;
    EXEC app.usp_reserve_ids N'cost', 1, @first OUTPUT, @prefix OUTPUT, @width OUTPUT;

    INSERT INTO fin.transaction_cost (transaction_cost_id, document_type, order_id, ticket_id, customer_id, transaction_at,
        channel, store_id, main_category, gross_revenue_eur, discount_eur, product_cost_eur, logistics_cost_eur,
        packaging_cost_eur, last_mile_cost_eur, payment_cost_eur, service_cost_eur, expected_return_cost_eur, cac_eur,
        attributed_campaign_id, net_contribution_eur)
    SELECT app.fn_format_id(@prefix, @width, @first), @document_type, @order_id, @ticket_id, @customer_id, @transaction_at,
           @channel, @store_id, @main_category, @revenue_eur, @discount_eur, @product_cost_eur,
           r.logistics_eur, r.packaging_eur, r.last_mile_eur,
           CASE WHEN @cash_payment = 1 THEN 0 ELSE ROUND(@revenue_eur * r.payment_pct, 2) END,
           r.service_eur, ROUND(@revenue_eur * r.expected_return_pct, 2), ROUND(@revenue_eur * r.cac_pct, 2),
           @campaign_id,
           @revenue_eur - @product_cost_eur - r.logistics_eur - r.packaging_eur - r.last_mile_eur
             - CASE WHEN @cash_payment = 1 THEN 0 ELSE ROUND(@revenue_eur * r.payment_pct, 2) END
             - r.service_eur - ROUND(@revenue_eur * r.expected_return_pct, 2) - ROUND(@revenue_eur * r.cac_pct, 2)
    FROM ref.cost_rule r WHERE r.channel = @channel;
END
GO

/* Valora una cesta que el llamador ha dejado en #basket(product_id, quantity):
   precio de catálogo, mejor promoción activa (respetando el margen mínimo)
   y cupón. Lo usan el checkout, el TPV y la vista previa del carrito. */
CREATE OR ALTER PROCEDURE sales.usp_price_basket
    @store_id NVARCHAR(50), @customer_id NVARCHAR(50) = NULL, @coupon_code NVARCHAR(30) = NULL,
    @at DATETIME2(0) = NULL,
    @coupon_instance_id NVARCHAR(30) = NULL OUTPUT, @coupon_discount DECIMAL(18,2) = 0 OUTPUT
AS
BEGIN
    SET NOCOUNT ON;
    SET @at = ISNULL(@at, SYSUTCDATETIME());
    SET @coupon_discount = 0;
    SET @coupon_instance_id = NULL;

    IF NOT EXISTS (SELECT 1 FROM #basket) THROW 50110, N'La cesta está vacía.', 1;
    IF EXISTS (SELECT 1 FROM #basket WHERE quantity < 1 OR quantity > 20)
        THROW 50111, N'Cada línea debe tener entre 1 y 20 unidades.', 1;

    UPDATE b SET product_name = p.product_name, category = p.category, subcategory = p.subcategory,
                 unit_price = p.sale_price, unit_cost = p.unit_cost, vat_pct = p.vat_pct, weight_kg = p.weight_kg
    FROM #basket b JOIN catalog.product p ON p.product_id = b.product_id
    WHERE p.product_status = N'Activo' AND p.sale_price IS NOT NULL;

    DECLARE @missing NVARCHAR(50) = (SELECT TOP 1 product_id FROM #basket WHERE unit_price IS NULL);
    IF @missing IS NOT NULL
    BEGIN
        DECLARE @msg NVARCHAR(200) = CONCAT(N'El producto ', @missing, N' no está a la venta.');
        THROW 50112, @msg, 1;
    END

    UPDATE #basket SET gross_amount = unit_price * quantity;
    DECLARE @basket_gross DECIMAL(18,2) = (SELECT SUM(gross_amount) FROM #basket);

    -- Mejor promoción de descuento porcentual activa para la categoría (y tienda).
    UPDATE b SET promo_id = p.promo_id, promo_combinable = p.combinable,
           promo_pct = CASE
               WHEN p.min_margin_pct IS NULL OR b.unit_cost IS NULL THEN p.discount_pct / 100.0
               ELSE (SELECT MIN(v) FROM (VALUES (p.discount_pct / 100.0),
                        (CASE WHEN 1 - b.unit_cost / (b.unit_price * (1 - p.min_margin_pct / 100.0)) < 0 THEN 0
                              ELSE 1 - b.unit_cost / (b.unit_price * (1 - p.min_margin_pct / 100.0)) END)) AS x(v)) END
    FROM #basket b
    CROSS APPLY (SELECT TOP 1 pr.promo_id, pr.discount_pct, pr.combinable, pr.min_margin_pct
                 FROM mkt.promotion pr
                 WHERE pr.promo_type = N'descuento_pct' AND pr.discount_pct > 0
                   AND @at BETWEEN pr.starts_at AND pr.ends_at
                   AND pr.basket_threshold_eur <= @basket_gross
                   AND (pr.store_id IS NULL OR pr.store_id = @store_id)
                   AND ((pr.scope_type = N'categoria' AND pr.scope_id = b.category)
                     OR (pr.scope_type = N'categoria_tienda' AND pr.scope_id = b.category + N'|' + @store_id))
                 ORDER BY pr.discount_pct DESC, pr.promo_id) p;

    UPDATE #basket SET discount_amount = ROUND(gross_amount * ISNULL(promo_pct, 0), 2), coupon_share = 0;
    UPDATE #basket SET promo_id = NULL, promo_pct = NULL WHERE discount_amount = 0;

    IF @coupon_code IS NOT NULL AND LEN(LTRIM(@coupon_code)) > 0
    BEGIN
        DECLARE @c_id NVARCHAR(30), @c_customer NVARCHAR(50), @c_status NVARCHAR(20), @c_from DATETIME2(0), @c_to DATETIME2(0),
                @c_type NVARCHAR(20), @c_pct DECIMAL(5,2), @c_eur DECIMAL(10,2), @c_min DECIMAL(10,2),
                @c_category NVARCHAR(100), @c_store NVARCHAR(50);
        SELECT @c_id = coupon_instance_id, @c_customer = customer_id, @c_status = coupon_status, @c_from = valid_from,
               @c_to = valid_to, @c_type = coupon_type, @c_pct = discount_pct, @c_eur = discount_eur, @c_min = min_spend_eur,
               @c_category = restricted_category, @c_store = restricted_store_id
        FROM mkt.coupon WITH (UPDLOCK) WHERE coupon_code = UPPER(LTRIM(RTRIM(@coupon_code)));

        IF @c_id IS NULL THROW 50120, N'El cupón no existe.', 1;
        IF @customer_id IS NULL OR @c_customer <> @customer_id THROW 50121, N'El cupón pertenece a otro cliente.', 1;
        IF @c_status <> N'emitido' THROW 50122, N'El cupón ya no está disponible.', 1;
        IF @at < @c_from OR @at > @c_to THROW 50123, N'El cupón está fuera de su periodo de validez.', 1;
        IF @c_store IS NOT NULL AND @c_store <> @store_id
        BEGIN
            DECLARE @msg3 NVARCHAR(200) = CONCAT(N'El cupón solo vale en la tienda ', @c_store, N'.');
            THROW 50124, @msg3, 1;
        END

        DECLARE @eligible DECIMAL(18,2) = (
            SELECT SUM(gross_amount - discount_amount) FROM #basket
            WHERE (@c_category IS NULL OR category = @c_category) AND (promo_id IS NULL OR promo_combinable = 1));
        IF ISNULL(@eligible, 0) = 0
            THROW 50125, N'Ningún producto de la cesta admite este cupón.', 1;
        IF @eligible < @c_min
        BEGIN
            DECLARE @msg4 NVARCHAR(200) = CONCAT(N'El cupón exige un gasto mínimo de ', FORMAT(@c_min, 'N2', 'es-ES'), N' €.');
            THROW 50126, @msg4, 1;
        END

        SET @coupon_discount = CASE WHEN @c_type = N'porcentaje' THEN ROUND(@eligible * @c_pct / 100.0, 2)
                                    ELSE CASE WHEN @c_eur > @eligible THEN @eligible ELSE @c_eur END END;
        SET @coupon_instance_id = @c_id;

        UPDATE #basket SET coupon_share = ROUND(@coupon_discount * (gross_amount - discount_amount) / @eligible, 2)
        WHERE (@c_category IS NULL OR category = @c_category) AND (promo_id IS NULL OR promo_combinable = 1);

        -- El redondeo se ajusta en la línea mayor para que el reparto cuadre al céntimo.
        DECLARE @diff DECIMAL(18,2) = @coupon_discount - (SELECT SUM(coupon_share) FROM #basket);
        IF @diff <> 0
            UPDATE TOP (1) #basket SET coupon_share = coupon_share + @diff
            WHERE line_no = (SELECT TOP 1 line_no FROM #basket WHERE coupon_share > 0 ORDER BY gross_amount DESC, line_no);
    END

    UPDATE #basket SET line_amount = gross_amount - discount_amount - coupon_share;
END
GO

/* Vista previa de una cesta (carrito o TPV) sin escribir nada. */
CREATE OR ALTER PROCEDURE sales.usp_quote_basket
    @store_id NVARCHAR(50), @customer_id NVARCHAR(50) = NULL, @lines_json NVARCHAR(MAX), @coupon_code NVARCHAR(30) = NULL
AS
BEGIN
    SET NOCOUNT ON;
    CREATE TABLE #basket (line_no INT IDENTITY(1,1), product_id NVARCHAR(50), quantity INT, product_name NVARCHAR(255),
        category NVARCHAR(100), subcategory NVARCHAR(100), unit_price DECIMAL(18,2), unit_cost DECIMAL(18,2), vat_pct DECIMAL(9,4),
        weight_kg DECIMAL(18,3), gross_amount DECIMAL(18,2), promo_id NVARCHAR(30), promo_pct DECIMAL(9,4), promo_combinable BIT,
        discount_amount DECIMAL(18,2), coupon_share DECIMAL(18,2), line_amount DECIMAL(18,2));
    INSERT INTO #basket (product_id, quantity)
    SELECT product_id, SUM(quantity) FROM OPENJSON(@lines_json) WITH (product_id NVARCHAR(50) '$.product_id', quantity INT '$.quantity')
    GROUP BY product_id;

    DECLARE @coupon_id NVARCHAR(30), @coupon_discount DECIMAL(18,2);
    EXEC sales.usp_price_basket @store_id, @customer_id, @coupon_code, NULL, @coupon_id OUTPUT, @coupon_discount OUTPUT;

    SELECT b.line_no, b.product_id, b.product_name, b.category, b.quantity, b.unit_price, b.gross_amount, b.promo_id,
           b.discount_amount, b.coupon_share, b.line_amount,
           ISNULL(s.on_hand_qty - s.reserved_qty, 0) AS available_qty
    FROM #basket b LEFT JOIN inventory.stock_level s ON s.store_id = @store_id AND s.product_id = b.product_id
    ORDER BY b.line_no;
    SELECT SUM(gross_amount) AS gross_total, SUM(discount_amount) AS promo_discount, @coupon_discount AS coupon_discount,
           SUM(line_amount) AS net_total, @coupon_id AS coupon_instance_id, MAX(weight_kg) AS max_weight_kg
    FROM #basket;
END
GO

/* Gastos de envío: gratis desde 150 €, 9,99 € si hay bultos de más de 20 kg, 6,99 € el resto. */
CREATE OR ALTER FUNCTION sales.fn_shipping_amount (@net_total DECIMAL(18,2), @max_weight_kg DECIMAL(18,3))
RETURNS DECIMAL(18,2)
AS
BEGIN
    RETURN CASE WHEN @net_total >= 150 THEN 0
                WHEN @max_weight_kg > 20 THEN 9.99
                ELSE 6.99 END;
END
GO

/* ---------- compra online ---------- */

CREATE OR ALTER PROCEDURE sales.usp_checkout
    @customer_id NVARCHAR(50), @lines_json NVARCHAR(MAX),
    @shipping_address NVARCHAR(255), @shipping_postal_code NVARCHAR(20), @shipping_city NVARCHAR(100),
    @shipping_province NVARCHAR(100), @payment_method NVARCHAR(50), @coupon_code NVARCHAR(30) = NULL,
    @order_origin NVARCHAR(50) = N'web', @session_id NVARCHAR(30) = NULL, @online_user_id NVARCHAR(50) = NULL,
    @user_login NVARCHAR(100) = NULL, @ordered_at DATETIME2(0) = NULL
AS
BEGIN
    SET NOCOUNT ON;
    SET XACT_ABORT ON;
    DECLARE @now DATETIME2(0) = ISNULL(@ordered_at, SYSUTCDATETIME());

    IF NOT EXISTS (SELECT 1 FROM crm.customer WHERE customer_id = @customer_id AND customer_status = N'Activo')
        THROW 50130, N'El cliente no existe o no está activo.', 1;
    IF @payment_method NOT IN (N'Tarjeta', N'PayPal', N'Bizum', N'ApplePay', N'Transferencia', N'ContraReembolso')
        THROW 50131, N'Método de pago no admitido.', 1;
    IF LEN(ISNULL(@shipping_address, N'')) < 5 OR @shipping_postal_code NOT LIKE N'[0-9][0-9][0-9][0-9][0-9]'
        THROW 50132, N'Dirección o código postal de envío no válidos.', 1;
    IF @order_origin NOT IN (N'web', N'app', N'marketplace') SET @order_origin = N'web';

    CREATE TABLE #basket (line_no INT IDENTITY(1,1), product_id NVARCHAR(50), quantity INT, product_name NVARCHAR(255),
        category NVARCHAR(100), subcategory NVARCHAR(100), unit_price DECIMAL(18,2), unit_cost DECIMAL(18,2), vat_pct DECIMAL(9,4),
        weight_kg DECIMAL(18,3), gross_amount DECIMAL(18,2), promo_id NVARCHAR(30), promo_pct DECIMAL(9,4), promo_combinable BIT,
        discount_amount DECIMAL(18,2), coupon_share DECIMAL(18,2), line_amount DECIMAL(18,2));
    INSERT INTO #basket (product_id, quantity)
    SELECT UPPER(LTRIM(RTRIM(product_id))), SUM(quantity)
    FROM OPENJSON(@lines_json) WITH (product_id NVARCHAR(50) '$.product_id', quantity INT '$.quantity')
    GROUP BY UPPER(LTRIM(RTRIM(product_id)));

    BEGIN TRAN;

    DECLARE @coupon_id NVARCHAR(30), @coupon_discount DECIMAL(18,2);
    EXEC sales.usp_price_basket N'ONLINE', @customer_id, @coupon_code, @now, @coupon_id OUTPUT, @coupon_discount OUTPUT;

    DECLARE @net DECIMAL(18,2), @gross DECIMAL(18,2), @discount DECIMAL(18,2), @cost DECIMAL(18,2), @max_weight DECIMAL(18,3),
            @lines INT, @main_category NVARCHAR(100);
    SELECT @net = SUM(line_amount), @gross = SUM(gross_amount), @discount = SUM(discount_amount + coupon_share),
           @cost = SUM(ISNULL(unit_cost, 0) * quantity), @max_weight = MAX(weight_kg), @lines = COUNT(*)
    FROM #basket;
    SET @main_category = (SELECT TOP 1 category FROM #basket ORDER BY line_amount DESC);
    DECLARE @shipping DECIMAL(18,2) = sales.fn_shipping_amount(@net, @max_weight);

    DECLARE @first BIGINT, @prefix NVARCHAR(30), @width TINYINT, @order_id NVARCHAR(50);
    EXEC app.usp_reserve_ids N'order', 1, @first OUTPUT, @prefix OUTPUT, @width OUTPUT;
    SET @order_id = app.fn_format_id(@prefix, @width, @first);
    EXEC app.usp_reserve_ids N'order_line', @lines, @first OUTPUT, @prefix OUTPUT, @width OUTPUT;

    INSERT INTO sales.online_order (order_id, ordered_at, customer_id, online_user_id, order_total, shipping_amount,
        shipping_address, shipping_postal_code, shipping_city, shipping_province, shipping_country_code, payment_method,
        order_status, order_origin, coupon_instance_id, source_updated_at)
    VALUES (@order_id, @now, @customer_id, @online_user_id, @net + @shipping, @shipping, @shipping_address, @shipping_postal_code,
        @shipping_city, @shipping_province, 'ES', @payment_method, N'Pendiente', @order_origin, @coupon_id, @now);

    INSERT INTO sales.online_order_line (order_line_id, order_id, product_id, product_description, category, subcategory, quantity,
        unit_price, discount_pct, discount_amount, line_amount, vat_pct, promo_id)
    SELECT app.fn_format_id(@prefix, @width, @first + line_no - 1), @order_id, product_id, product_name, category, subcategory,
           quantity, unit_price, CAST(ROUND(100.0 * (discount_amount + coupon_share) / NULLIF(gross_amount, 0), 2) AS DECIMAL(9,4)),
           discount_amount + coupon_share, line_amount, vat_pct, promo_id
    FROM #basket;

    -- Stock del almacén online, línea a línea.
    DECLARE @p NVARCHAR(50), @q INT;
    DECLARE c CURSOR LOCAL FAST_FORWARD FOR SELECT product_id, quantity FROM #basket ORDER BY product_id;
    OPEN c; FETCH NEXT FROM c INTO @p, @q;
    WHILE @@FETCH_STATUS = 0
    BEGIN
        DECLARE @neg INT = -@q;
        EXEC inventory.usp_apply_stock_delta N'ONLINE', @p, N'VENTA', @neg, 0, 0, N'ORDER', @order_id, @user_login, NULL;
        FETCH NEXT FROM c INTO @p, @q;
    END
    CLOSE c; DEALLOCATE c;

    IF @coupon_id IS NOT NULL
        UPDATE mkt.coupon SET coupon_status = N'canjeado', redeemed_at = @now, order_id = @order_id, basket_eur = @gross,
               discount_applied_eur = @coupon_discount, margin_after_discount_eur = @net - @cost
        WHERE coupon_instance_id = @coupon_id;

    UPDATE crm.customer SET loyalty_points = ISNULL(loyalty_points, 0) + CAST(FLOOR(@net) AS INT), updated_at = SYSUTCDATETIME()
    WHERE customer_id = @customer_id;

    DECLARE @campaign NVARCHAR(30) = (SELECT campaign_id FROM mkt.coupon WHERE coupon_instance_id = @coupon_id);
    DECLARE @revenue DECIMAL(12,2) = @net;
    EXEC fin.usp_record_transaction_cost N'ORDER', @order_id, NULL, @customer_id, @now, N'ONLINE', NULL, @main_category,
         @revenue, @discount, @cost, 0, @campaign;

    -- Documentos para Cosmos DB: evento de compra y señal de identidad.
    DECLARE @event_id NVARCHAR(50), @signal_id NVARCHAR(50);
    EXEC app.usp_reserve_ids N'web_event', 1, @first OUTPUT, @prefix OUTPUT, @width OUTPUT;
    SET @event_id = app.fn_format_id(@prefix, @width, @first);
    IF @session_id IS NULL
    BEGIN
        EXEC app.usp_reserve_ids N'web_session', 1, @first OUTPUT, @prefix OUTPUT, @width OUTPUT;
        SET @session_id = app.fn_format_id(@prefix, @width, @first);
    END
    EXEC app.usp_reserve_ids N'identity', 1, @first OUTPUT, @prefix OUTPUT, @width OUTPUT;
    SET @signal_id = app.fn_format_id(@prefix, @width, @first);

    DECLARE @email NVARCHAR(255), @consent BIT;
    SELECT @email = email, @consent = marketing_consent FROM crm.customer WHERE customer_id = @customer_id;

    INSERT INTO app.outbox (container_name, document_json)
    SELECT N'eventos_web', (SELECT @event_id AS id, @session_id AS pk, @event_id AS event_id,
            CONVERT(NVARCHAR(19), @now, 126) AS fecha_hora_evento, @session_id AS session_id, @customer_id AS customer_id,
            CAST(NULL AS NVARCHAR(10)) AS cookie_id, CAST(NULL AS NVARCHAR(10)) AS device_id, @online_user_id AS usuario_online_id,
            CASE WHEN @campaign IS NULL THEN N'direct' ELSE N'crm' END AS canal_adquisicion,
            CASE WHEN @order_origin = N'app' THEN N'app' ELSE N'direct' END AS utm_source,
            N'(none)' AS utm_medium, @campaign AS utm_campaign, N'purchase' AS tipo_evento, N'checkout' AS page_type,
            CAST(NULL AS NVARCHAR(10)) AS product_id, @main_category AS categoria, CAST(NULL AS NVARCHAR(10)) AS subcategoria,
            CAST(NULL AS NVARCHAR(10)) AS search_term, CAST(NULL AS NVARCHAR(10)) AS store_id_interes,
            @net + @shipping AS valor_evento_eur, @order_id AS order_id, CAST(1 AS BIT) AS consent_analytics, CAST(1 AS BIT) AS logged_in_flag, N'web' AS origen
           FOR JSON PATH, WITHOUT_ARRAY_WRAPPER, INCLUDE_NULL_VALUES)
    UNION ALL
    SELECT N'senales_identidad', (SELECT @signal_id AS id, @customer_id AS pk, @signal_id AS identity_signal_id,
            CONVERT(NVARCHAR(19), @now, 126) AS fecha_evento, N'ECOM' AS fuente_sistema, N'checkout_email' AS tipo_senal,
            @customer_id AS customer_id_raw, @customer_id AS customer_id_candidato,
            LOWER(LEFT(CONVERT(VARCHAR(64), HASHBYTES('SHA2_256', LOWER(@email)), 2), 16)) AS email_hash,
            CAST(NULL AS NVARCHAR(10)) AS telefono_hash, CAST(NULL AS NVARCHAR(10)) AS tarjeta_fidelizacion_id,
            CAST(NULL AS NVARCHAR(10)) AS cookie_id, CAST(NULL AS NVARCHAR(10)) AS device_id,
            CAST(NULL AS NVARCHAR(10)) AS app_user_id, @online_user_id AS usuario_online_id, @order_id AS order_id,
            CAST(NULL AS NVARCHAR(10)) AS ticket_id, CAST(NULL AS NVARCHAR(10)) AS store_id,
            @consent AS consentimiento_snapshot, 0.95 AS confianza_origen, N'web' AS origen
           FOR JSON PATH, WITHOUT_ARRAY_WRAPPER, INCLUDE_NULL_VALUES);

    COMMIT;

    SELECT @order_id AS order_id, @net AS net_total, @shipping AS shipping_amount, @net + @shipping AS order_total,
           @discount AS discount_total, @coupon_id AS coupon_instance_id, @session_id AS session_id;
END
GO

/* Ciclo de vida del pedido. Cancelar devuelve el stock, los puntos y el cupón. */
CREATE OR ALTER PROCEDURE sales.usp_order_set_status
    @order_id NVARCHAR(50), @new_status NVARCHAR(50), @user_login NVARCHAR(100) = NULL
AS
BEGIN
    SET NOCOUNT ON;
    SET XACT_ABORT ON;
    BEGIN TRAN;
    DECLARE @status NVARCHAR(50), @customer NVARCHAR(50), @total DECIMAL(18,2), @shipping DECIMAL(18,2), @coupon NVARCHAR(30);
    SELECT @status = order_status, @customer = customer_id, @total = order_total, @shipping = shipping_amount, @coupon = coupon_instance_id
    FROM sales.online_order WITH (UPDLOCK) WHERE order_id = @order_id;
    IF @status IS NULL THROW 50140, N'El pedido no existe.', 1;

    IF NOT ((@status = N'Pendiente' AND @new_status IN (N'En preparación', N'Cancelado'))
         OR (@status = N'En preparación' AND @new_status IN (N'Entregado', N'Cancelado')))
    BEGIN
        DECLARE @msg NVARCHAR(200) = CONCAT(N'No se puede pasar un pedido de «', @status, N'» a «', @new_status, N'».');
        THROW 50141, @msg, 1;
    END

    UPDATE sales.online_order SET order_status = @new_status, source_updated_at = SYSUTCDATETIME(), updated_at = SYSUTCDATETIME()
    WHERE order_id = @order_id;

    IF @new_status = N'Cancelado'
    BEGIN
        DECLARE @p NVARCHAR(50), @q INT;
        DECLARE c CURSOR LOCAL FAST_FORWARD FOR
            SELECT product_id, SUM(quantity) FROM sales.online_order_line WHERE order_id = @order_id AND product_id IS NOT NULL GROUP BY product_id;
        OPEN c; FETCH NEXT FROM c INTO @p, @q;
        WHILE @@FETCH_STATUS = 0
        BEGIN
            EXEC inventory.usp_apply_stock_delta N'ONLINE', @p, N'CANCELACION', @q, 0, 0, N'ORDER', @order_id, @user_login, NULL;
            FETCH NEXT FROM c INTO @p, @q;
        END
        CLOSE c; DEALLOCATE c;

        IF @customer IS NOT NULL
            UPDATE crm.customer
               SET loyalty_points = CASE WHEN ISNULL(loyalty_points, 0) >= FLOOR(@total - ISNULL(@shipping, 0))
                                         THEN loyalty_points - CAST(FLOOR(@total - ISNULL(@shipping, 0)) AS INT) ELSE 0 END,
                   updated_at = SYSUTCDATETIME()
             WHERE customer_id = @customer;
        IF @coupon IS NOT NULL
            UPDATE mkt.coupon SET coupon_status = CASE WHEN valid_to >= SYSUTCDATETIME() THEN N'emitido' ELSE N'expirado' END,
                   redeemed_at = NULL, order_id = NULL, basket_eur = NULL, discount_applied_eur = NULL, margin_after_discount_eur = NULL
            WHERE coupon_instance_id = @coupon;
    END
    EXEC app.usp_audit @user_login, N'order_status', N'online_order', @order_id, @new_status;
    COMMIT;
END
GO

/* ---------- TPV ---------- */

CREATE OR ALTER PROCEDURE store.usp_till_open
    @store_id NVARCHAR(50), @till_id NVARCHAR(50), @cashier_id NVARCHAR(50), @opening_cash DECIMAL(18,2) = 0
AS
BEGIN
    SET NOCOUNT ON;
    IF NOT EXISTS (SELECT 1 FROM store.store WHERE store_id = @store_id AND store_status = N'Activa')
        THROW 50150, N'La tienda no existe o no está activa.', 1;
    IF NOT EXISTS (SELECT 1 FROM hr.employee WHERE employee_id = @cashier_id AND employee_status = N'Activo')
        THROW 50151, N'El cajero no es un empleado activo.', 1;
    IF @till_id NOT LIKE N'CAJ[0-9][0-9]' THROW 50152, N'Caja no válida (formato CAJ01).', 1;
    IF EXISTS (SELECT 1 FROM store.till_session WHERE store_id = @store_id AND till_id = @till_id AND session_status = N'Abierta')
        THROW 50153, N'Esa caja ya está abierta.', 1;
    INSERT INTO store.till_session (store_id, till_id, cashier_id, opening_cash) VALUES (@store_id, @till_id, @cashier_id, @opening_cash);
    SELECT CAST(SCOPE_IDENTITY() AS BIGINT) AS till_session_id;
END
GO

CREATE OR ALTER PROCEDURE store.usp_till_close @till_session_id BIGINT, @counted_cash DECIMAL(18,2)
AS
BEGIN
    SET NOCOUNT ON;
    DECLARE @opening DECIMAL(18,2), @status NVARCHAR(20);
    SELECT @opening = opening_cash, @status = session_status FROM store.till_session WHERE till_session_id = @till_session_id;
    IF @status IS NULL THROW 50154, N'La sesión de caja no existe.', 1;
    IF @status <> N'Abierta' THROW 50155, N'La caja ya está cerrada.', 1;
    DECLARE @cash DECIMAL(18,2) = (
        SELECT ISNULL(SUM(p.paid_amount), 0) FROM sales.store_payment p JOIN sales.pos_ticket t ON t.ticket_id = p.ticket_id
        WHERE t.till_session_id = @till_session_id AND p.payment_method = N'Efectivo' AND p.payment_status = N'OK');
    UPDATE store.till_session SET closed_at = SYSUTCDATETIME(), expected_cash = @opening + @cash, counted_cash = @counted_cash,
           session_status = N'Cerrada'
    WHERE till_session_id = @till_session_id;
    SELECT @opening + @cash AS expected_cash, @counted_cash AS counted_cash, @counted_cash - (@opening + @cash) AS difference;
END
GO

CREATE OR ALTER PROCEDURE sales.usp_pos_ticket
    @store_id NVARCHAR(50), @till_id NVARCHAR(50), @cashier_id NVARCHAR(50), @customer_id NVARCHAR(50) = NULL,
    @lines_json NVARCHAR(MAX), @payments_json NVARCHAR(MAX), @coupon_code NVARCHAR(30) = NULL,
    @user_login NVARCHAR(100) = NULL, @ticket_at DATETIME2(0) = NULL
AS
BEGIN
    SET NOCOUNT ON;
    SET XACT_ABORT ON;
    DECLARE @now DATETIME2(0) = ISNULL(@ticket_at, SYSUTCDATETIME());

    IF NOT EXISTS (SELECT 1 FROM store.store WHERE store_id = @store_id AND store_status = N'Activa' AND channel = N'FISICO')
        THROW 50160, N'La tienda no existe o no vende en físico.', 1;
    IF NOT EXISTS (SELECT 1 FROM hr.employee WHERE employee_id = @cashier_id AND employee_status = N'Activo')
        THROW 50161, N'El cajero no es un empleado activo.', 1;
    IF @customer_id IS NOT NULL AND NOT EXISTS (SELECT 1 FROM crm.customer WHERE customer_id = @customer_id AND customer_status = N'Activo')
        THROW 50162, N'El cliente no existe o no está activo.', 1;

    CREATE TABLE #basket (line_no INT IDENTITY(1,1), product_id NVARCHAR(50), quantity INT, product_name NVARCHAR(255),
        category NVARCHAR(100), subcategory NVARCHAR(100), unit_price DECIMAL(18,2), unit_cost DECIMAL(18,2), vat_pct DECIMAL(9,4),
        weight_kg DECIMAL(18,3), gross_amount DECIMAL(18,2), promo_id NVARCHAR(30), promo_pct DECIMAL(9,4), promo_combinable BIT,
        discount_amount DECIMAL(18,2), coupon_share DECIMAL(18,2), line_amount DECIMAL(18,2));
    INSERT INTO #basket (product_id, quantity)
    SELECT UPPER(LTRIM(RTRIM(product_id))), SUM(quantity)
    FROM OPENJSON(@lines_json) WITH (product_id NVARCHAR(50) '$.product_id', quantity INT '$.quantity')
    GROUP BY UPPER(LTRIM(RTRIM(product_id)));

    DECLARE @payments TABLE (pay_no INT IDENTITY(1,1), payment_method NVARCHAR(50), amount DECIMAL(18,2), reference NVARCHAR(100));
    INSERT INTO @payments (payment_method, amount, reference)
    SELECT payment_method, amount, reference
    FROM OPENJSON(@payments_json) WITH (payment_method NVARCHAR(50) '$.payment_method', amount DECIMAL(18,2) '$.amount',
                                        reference NVARCHAR(100) '$.reference');
    IF NOT EXISTS (SELECT 1 FROM @payments) THROW 50163, N'Falta el cobro.', 1;
    IF EXISTS (SELECT 1 FROM @payments WHERE payment_method NOT IN (N'Tarjeta', N'Efectivo', N'Bizum', N'Tarjeta regalo',
               N'Vale', N'Cupón', N'Financiación') OR amount <= 0)
        THROW 50164, N'Hay un cobro con método no admitido o importe no positivo.', 1;

    BEGIN TRAN;

    DECLARE @coupon_id NVARCHAR(30), @coupon_discount DECIMAL(18,2);
    EXEC sales.usp_price_basket @store_id, @customer_id, @coupon_code, @now, @coupon_id OUTPUT, @coupon_discount OUTPUT;

    DECLARE @net DECIMAL(18,2), @gross DECIMAL(18,2), @discount DECIMAL(18,2), @cost DECIMAL(18,2), @lines INT, @main_category NVARCHAR(100);
    SELECT @net = SUM(line_amount), @gross = SUM(gross_amount), @discount = SUM(discount_amount + coupon_share),
           @cost = SUM(ISNULL(unit_cost, 0) * quantity), @lines = COUNT(*)
    FROM #basket;
    SET @main_category = (SELECT TOP 1 category FROM #basket ORDER BY line_amount DESC);

    DECLARE @paid DECIMAL(18,2) = (SELECT SUM(amount) FROM @payments);
    IF ABS(@paid - @net) > 0.009
    BEGIN
        DECLARE @msg NVARCHAR(200) = CONCAT(N'Los cobros (', FORMAT(@paid, 'N2', 'es-ES'), N' €) no cuadran con el total (',
                                            FORMAT(@net, 'N2', 'es-ES'), N' €).');
        THROW 50165, @msg, 1;
    END

    DECLARE @first BIGINT, @prefix NVARCHAR(30), @width TINYINT, @ticket_id NVARCHAR(50);
    EXEC app.usp_reserve_ids N'ticket', 1, @first OUTPUT, @prefix OUTPUT, @width OUTPUT;
    SET @ticket_id = app.fn_format_id(@prefix, @width, @first);

    -- El TPV registra el código de caja del empleado (EMP###) si lo tiene; si no, su FSH####.
    DECLARE @cashier_code NVARCHAR(50) = ISNULL((
        SELECT TOP 1 CASE WHEN operational_employee_id LIKE N'EM[0-9]%' THEN N'EMP' + SUBSTRING(operational_employee_id, 3, 10)
                          ELSE operational_employee_id END
        FROM xref.employee_alias WHERE source_system = N'POS' AND canonical_employee_id = @cashier_id
        ORDER BY operational_employee_id), @cashier_id);

    DECLARE @session BIGINT = (SELECT TOP 1 till_session_id FROM store.till_session
                               WHERE store_id = @store_id AND till_id = @till_id AND session_status = N'Abierta' ORDER BY opened_at DESC);

    INSERT INTO sales.pos_ticket (ticket_id, ticket_at, store_id, till_id, cashier_id, cashier_employee_id, customer_id, channel,
        ticket_gross_amount, ticket_discount_amount, ticket_net_amount, coupon_instance_id, till_session_id)
    VALUES (@ticket_id, @now, @store_id, @till_id, @cashier_code, @cashier_id, @customer_id, N'POS', @gross, @discount, @net,
        @coupon_id, @session);

    EXEC app.usp_reserve_ids N'ticket_line', @lines, @first OUTPUT, @prefix OUTPUT, @width OUTPUT;
    INSERT INTO sales.pos_ticket_line (ticket_line_id, ticket_id, product_id, product_description, category, subcategory, quantity,
        unit_price, discount_pct, discount_amount, line_amount, promo_id)
    SELECT app.fn_format_id(@prefix, @width, @first + line_no - 1), @ticket_id, product_id, product_name, category, subcategory,
           quantity, unit_price, CAST(ROUND(100.0 * (discount_amount + coupon_share) / NULLIF(gross_amount, 0), 2) AS DECIMAL(9,4)),
           discount_amount + coupon_share, line_amount, promo_id
    FROM #basket;

    DECLARE @pays INT = (SELECT COUNT(*) FROM @payments);
    EXEC app.usp_reserve_ids N'payment', @pays, @first OUTPUT, @prefix OUTPUT, @width OUTPUT;
    INSERT INTO sales.store_payment (payment_id, ticket_id, paid_at, store_id, till_id, cashier_id, cashier_employee_id,
        payment_method, paid_amount, authorization_reference, payment_status)
    SELECT app.fn_format_id(@prefix, @width, @first + pay_no - 1), @ticket_id, @now, @store_id, @till_id, @cashier_code, @cashier_id,
           payment_method, amount,
           CASE WHEN payment_method = N'Efectivo' THEN NULL
                ELSE ISNULL(reference, UPPER(LEFT(CONVERT(VARCHAR(64), HASHBYTES('SHA2_256', CONCAT(@ticket_id, pay_no)), 2), 10))) END,
           N'OK'
    FROM @payments;

    DECLARE @p NVARCHAR(50), @q INT;
    DECLARE c CURSOR LOCAL FAST_FORWARD FOR SELECT product_id, quantity FROM #basket ORDER BY product_id;
    OPEN c; FETCH NEXT FROM c INTO @p, @q;
    WHILE @@FETCH_STATUS = 0
    BEGIN
        DECLARE @neg INT = -@q;
        EXEC inventory.usp_apply_stock_delta @store_id, @p, N'VENTA', @neg, 0, 0, N'TICKET', @ticket_id, @user_login, NULL;
        FETCH NEXT FROM c INTO @p, @q;
    END
    CLOSE c; DEALLOCATE c;

    IF @coupon_id IS NOT NULL
        UPDATE mkt.coupon SET coupon_status = N'canjeado', redeemed_at = @now, ticket_id = @ticket_id, basket_eur = @gross,
               discount_applied_eur = @coupon_discount, margin_after_discount_eur = @net - @cost
        WHERE coupon_instance_id = @coupon_id;

    IF @customer_id IS NOT NULL
        UPDATE crm.customer SET loyalty_points = ISNULL(loyalty_points, 0) + CAST(FLOOR(@net) AS INT), updated_at = SYSUTCDATETIME()
        WHERE customer_id = @customer_id;

    DECLARE @campaign NVARCHAR(30) = (SELECT campaign_id FROM mkt.coupon WHERE coupon_instance_id = @coupon_id);
    DECLARE @cash BIT = CASE WHEN NOT EXISTS (SELECT 1 FROM @payments WHERE payment_method <> N'Efectivo') THEN 1 ELSE 0 END;
    EXEC fin.usp_record_transaction_cost N'TICKET', NULL, @ticket_id, @customer_id, @now, N'POS', @store_id, @main_category,
         @net, @discount, @cost, @cash, @campaign;

    IF @customer_id IS NOT NULL
    BEGIN
        DECLARE @signal_id NVARCHAR(50);
        EXEC app.usp_reserve_ids N'identity', 1, @first OUTPUT, @prefix OUTPUT, @width OUTPUT;
        SET @signal_id = app.fn_format_id(@prefix, @width, @first);
        INSERT INTO app.outbox (container_name, document_json)
        SELECT N'senales_identidad', (SELECT @signal_id AS id, @customer_id AS pk, @signal_id AS identity_signal_id,
                CONVERT(NVARCHAR(19), @now, 126) AS fecha_evento, N'POS' AS fuente_sistema, N'captura_ticket' AS tipo_senal,
                @customer_id AS customer_id_raw, @customer_id AS customer_id_candidato, CAST(NULL AS NVARCHAR(10)) AS email_hash,
                CASE WHEN c.phone IS NULL THEN NULL
                     ELSE LOWER(LEFT(CONVERT(VARCHAR(64), HASHBYTES('SHA2_256', REPLACE(REPLACE(REPLACE(c.phone, N' ', N''), N'-', N''), N'+34', N'')), 2), 16)) END AS telefono_hash,
                CAST(NULL AS NVARCHAR(10)) AS tarjeta_fidelizacion_id, CAST(NULL AS NVARCHAR(10)) AS cookie_id,
                CAST(NULL AS NVARCHAR(10)) AS device_id, CAST(NULL AS NVARCHAR(10)) AS app_user_id,
                CAST(NULL AS NVARCHAR(10)) AS usuario_online_id, CAST(NULL AS NVARCHAR(10)) AS order_id, @ticket_id AS ticket_id,
                @store_id AS store_id, c.marketing_consent AS consentimiento_snapshot, 0.9 AS confianza_origen, N'web' AS origen
               FOR JSON PATH, WITHOUT_ARRAY_WRAPPER, INCLUDE_NULL_VALUES)
        FROM crm.customer c WHERE c.customer_id = @customer_id;
    END

    COMMIT;
    SELECT @ticket_id AS ticket_id, @net AS net_total, @discount AS discount_total, @coupon_id AS coupon_instance_id;
END
GO

/* ---------- devoluciones ---------- */

/* Unidades ya devueltas (o en curso) de una línea, sin contar las rechazadas. */
CREATE OR ALTER FUNCTION [returns].fn_returned_qty (@order_line_id NVARCHAR(50), @ticket_line_id NVARCHAR(50))
RETURNS INT
AS
BEGIN
    RETURN ISNULL((SELECT SUM(l.returned_quantity)
                   FROM [returns].return_line l JOIN [returns].return_header h ON h.return_id = l.return_id
                   WHERE h.return_status <> N'Rechazada'
                     AND ((@order_line_id IS NOT NULL AND l.original_order_line_id = @order_line_id)
                       OR (@ticket_line_id IS NOT NULL AND l.original_ticket_line_id = @ticket_line_id))), 0);
END
GO

CREATE OR ALTER PROCEDURE [returns].usp_return_online_request
    @order_id NVARCHAR(50), @order_line_id NVARCHAR(50), @quantity INT, @return_reason NVARCHAR(200),
    @return_method NVARCHAR(50), @customer_id NVARCHAR(50) = NULL, @user_login NVARCHAR(100) = NULL
AS
BEGIN
    SET NOCOUNT ON;
    SET XACT_ABORT ON;
    DECLARE @o_customer NVARCHAR(50), @o_status NVARCHAR(50);
    SELECT @o_customer = customer_id, @o_status = order_status FROM sales.online_order WHERE order_id = @order_id;
    IF @o_status IS NULL THROW 50170, N'El pedido no existe.', 1;
    IF @customer_id IS NOT NULL AND ISNULL(@o_customer, N'') <> @customer_id THROW 50171, N'El pedido no es de este cliente.', 1;
    IF @o_status NOT IN (N'Entregado', N'Devuelto Parcial') THROW 50172, N'Solo se pueden devolver pedidos entregados.', 1;
    IF @return_method NOT IN (N'Envío', N'Tienda', N'Punto Pack') THROW 50173, N'Método de devolución no admitido.', 1;

    DECLARE @bought INT, @line_amount DECIMAL(18,2), @product NVARCHAR(50);
    SELECT @bought = quantity, @line_amount = line_amount, @product = product_id
    FROM sales.online_order_line WHERE order_line_id = @order_line_id AND order_id = @order_id;
    IF @bought IS NULL THROW 50174, N'La línea no pertenece al pedido.', 1;
    IF @quantity < 1 OR @quantity > @bought - [returns].fn_returned_qty(@order_line_id, NULL)
        THROW 50175, N'No quedan tantas unidades por devolver en esa línea.', 1;

    BEGIN TRAN;
    DECLARE @first BIGINT, @prefix NVARCHAR(30), @width TINYINT, @return_id NVARCHAR(50);
    EXEC app.usp_reserve_ids N'return_online', 1, @first OUTPUT, @prefix OUTPUT, @width OUTPUT;
    SET @return_id = app.fn_format_id(@prefix, @width, @first);
    INSERT INTO [returns].return_header (return_id, returned_at, return_channel, store_id, customer_id, original_order_id,
        return_status, return_method)
    VALUES (@return_id, SYSUTCDATETIME(), N'ONLINE', NULL, @o_customer, @order_id, N'Pendiente', @return_method);
    INSERT INTO [returns].return_line (return_line_id, return_id, product_id, original_order_line_id, returned_quantity,
        refund_amount, return_reason, original_sales_channel)
    VALUES (@return_id + N'-1', @return_id, @product, @order_line_id, @quantity,
        CAST(ROUND(@line_amount * @quantity / @bought, 2) AS DECIMAL(18,2)), @return_reason, N'ONLINE');
    EXEC app.usp_audit @user_login, N'return_request', N'return_header', @return_id, @order_id;
    COMMIT;
    SELECT @return_id AS return_id, CAST(ROUND(@line_amount * @quantity / @bought, 2) AS DECIMAL(18,2)) AS refund_amount;
END
GO

/* Resolución de una devolución online: aceptar repone stock del almacén online,
   rechazar no mueve nada, reembolsar cierra el ciclo. */
CREATE OR ALTER PROCEDURE [returns].usp_return_set_status
    @return_id NVARCHAR(50), @new_status NVARCHAR(50), @user_login NVARCHAR(100) = NULL
AS
BEGIN
    SET NOCOUNT ON;
    SET XACT_ABORT ON;
    BEGIN TRAN;
    DECLARE @status NVARCHAR(50), @channel NVARCHAR(50), @order_id NVARCHAR(50), @store NVARCHAR(50);
    SELECT @status = return_status, @channel = return_channel, @order_id = original_order_id, @store = store_id
    FROM [returns].return_header WITH (UPDLOCK) WHERE return_id = @return_id;
    IF @status IS NULL THROW 50176, N'La devolución no existe.', 1;
    IF NOT ((@status = N'Pendiente' AND @new_status IN (N'Aceptada', N'Rechazada'))
         OR (@status = N'Aceptada' AND @new_status = N'Reembolsada'))
    BEGIN
        DECLARE @msg NVARCHAR(200) = CONCAT(N'No se puede pasar una devolución de «', @status, N'» a «', @new_status, N'».');
        THROW 50177, @msg, 1;
    END

    UPDATE [returns].return_header SET return_status = @new_status, updated_at = SYSUTCDATETIME() WHERE return_id = @return_id;

    IF @new_status = N'Aceptada'
    BEGIN
        DECLARE @restock NVARCHAR(50) = ISNULL(@store, N'ONLINE');
        DECLARE @p NVARCHAR(50), @q INT;
        DECLARE c CURSOR LOCAL FAST_FORWARD FOR
            SELECT product_id, SUM(returned_quantity) FROM [returns].return_line WHERE return_id = @return_id AND product_id IS NOT NULL GROUP BY product_id;
        OPEN c; FETCH NEXT FROM c INTO @p, @q;
        WHILE @@FETCH_STATUS = 0
        BEGIN
            EXEC inventory.usp_apply_stock_delta @restock, @p, N'DEVOLUCION', @q, 0, 0, N'RETURN', @return_id, @user_login, NULL;
            FETCH NEXT FROM c INTO @p, @q;
        END
        CLOSE c; DEALLOCATE c;

        IF @order_id IS NOT NULL
        BEGIN
            DECLARE @bought INT = (SELECT SUM(quantity) FROM sales.online_order_line WHERE order_id = @order_id);
            DECLARE @returned INT = (SELECT SUM(l.returned_quantity) FROM [returns].return_line l
                                     JOIN [returns].return_header h ON h.return_id = l.return_id
                                     WHERE h.original_order_id = @order_id AND h.return_status IN (N'Aceptada', N'Reembolsada'));
            UPDATE sales.online_order
               SET order_status = CASE WHEN @returned >= @bought THEN N'Devuelto Total' ELSE N'Devuelto Parcial' END,
                   source_updated_at = SYSUTCDATETIME(), updated_at = SYSUTCDATETIME()
             WHERE order_id = @order_id AND order_status IN (N'Entregado', N'Devuelto Parcial');
        END
    END
    EXEC app.usp_audit @user_login, N'return_status', N'return_header', @return_id, @new_status;
    COMMIT;
END
GO

/* Devolución en tienda de un ticket o de un pedido online: se acepta en el
   acto, se repone en la tienda y se reembolsa con el método elegido. */
CREATE OR ALTER PROCEDURE [returns].usp_return_store
    @store_id NVARCHAR(50), @original_ticket_line_id NVARCHAR(50) = NULL, @original_order_line_id NVARCHAR(50) = NULL,
    @quantity INT, @return_reason NVARCHAR(200), @refund_method NVARCHAR(50), @cashier_id NVARCHAR(50) = NULL,
    @user_login NVARCHAR(100) = NULL, @notes NVARCHAR(500) = NULL
AS
BEGIN
    SET NOCOUNT ON;
    SET XACT_ABORT ON;
    IF NOT EXISTS (SELECT 1 FROM store.store WHERE store_id = @store_id AND channel = N'FISICO' AND store_status = N'Activa')
        THROW 50180, N'La tienda no existe o no está activa.', 1;
    IF (@original_ticket_line_id IS NULL AND @original_order_line_id IS NULL) OR (@original_ticket_line_id IS NOT NULL AND @original_order_line_id IS NOT NULL)
        THROW 50181, N'Indica una línea de ticket o una línea de pedido.', 1;
    IF @refund_method NOT IN (N'Tarjeta', N'Efectivo', N'Vale', N'Tarjeta regalo', N'Transferencia', N'Cupón')
        THROW 50182, N'Método de reembolso no admitido.', 1;

    DECLARE @bought INT, @line_amount DECIMAL(18,2), @product NVARCHAR(50), @customer NVARCHAR(50),
            @ticket NVARCHAR(50), @order NVARCHAR(50), @origin NVARCHAR(10);
    IF @original_ticket_line_id IS NOT NULL
        SELECT @bought = l.quantity, @line_amount = l.line_amount, @product = l.product_id, @customer = t.customer_id,
               @ticket = t.ticket_id, @origin = N'POS'
        FROM sales.pos_ticket_line l JOIN sales.pos_ticket t ON t.ticket_id = l.ticket_id
        WHERE l.ticket_line_id = @original_ticket_line_id;
    ELSE
        SELECT @bought = l.quantity, @line_amount = l.line_amount, @product = l.product_id, @customer = o.customer_id,
               @order = o.order_id, @origin = N'OMNI'
        FROM sales.online_order_line l JOIN sales.online_order o ON o.order_id = l.order_id
        WHERE l.order_line_id = @original_order_line_id AND o.order_status IN (N'Entregado', N'Devuelto Parcial');
    IF @bought IS NULL THROW 50183, N'No se encuentra la línea original (o el pedido no está entregado).', 1;
    IF @quantity < 1 OR @quantity > @bought - [returns].fn_returned_qty(@original_order_line_id, @original_ticket_line_id)
        THROW 50184, N'No quedan tantas unidades por devolver en esa línea.', 1;

    BEGIN TRAN;
    DECLARE @first BIGINT, @prefix NVARCHAR(30), @width TINYINT, @return_id NVARCHAR(50);
    EXEC app.usp_reserve_ids N'return_store', 1, @first OUTPUT, @prefix OUTPUT, @width OUTPUT;
    SET @return_id = app.fn_format_id(@prefix, @width, @first);
    INSERT INTO [returns].return_header (return_id, returned_at, return_channel, store_id, customer_id, original_ticket_id,
        original_order_id, return_status, refund_method, notes)
    VALUES (@return_id, SYSUTCDATETIME(), N'TIENDA', @store_id, @customer, @ticket, @order, N'Pendiente', @refund_method, @notes);
    INSERT INTO [returns].return_line (return_line_id, return_id, product_id, original_ticket_line_id, original_order_line_id,
        returned_quantity, refund_amount, return_reason, original_sales_channel)
    VALUES (@return_id + N'-1', @return_id, @product, @original_ticket_line_id, @original_order_line_id, @quantity,
        CAST(ROUND(@line_amount * @quantity / @bought, 2) AS DECIMAL(18,2)), @return_reason, @origin);
    EXEC [returns].usp_return_set_status @return_id, N'Aceptada', @user_login;
    COMMIT;
    SELECT @return_id AS return_id, CAST(ROUND(@line_amount * @quantity / @bought, 2) AS DECIMAL(18,2)) AS refund_amount;
END
GO

/* ---------- inventario ---------- */

CREATE OR ALTER PROCEDURE inventory.usp_stock_adjust
    @store_id NVARCHAR(50), @product_id NVARCHAR(50), @delta INT, @reason NVARCHAR(300), @user_login NVARCHAR(100) = NULL
AS
BEGIN
    SET NOCOUNT ON;
    SET XACT_ABORT ON;
    IF @delta = 0 THROW 50190, N'El ajuste no puede ser cero.', 1;
    IF LEN(ISNULL(@reason, N'')) < 3 THROW 50191, N'Indica el motivo del ajuste.', 1;
    IF NOT EXISTS (SELECT 1 FROM catalog.product WHERE product_id = @product_id) THROW 50192, N'El producto no existe.', 1;
    BEGIN TRAN;
        EXEC inventory.usp_apply_stock_delta @store_id, @product_id, N'AJUSTE', @delta, 0, 0, N'AJUSTE', NULL, @user_login, @reason;
    COMMIT;
END
GO

/* Reposición desde el almacén central (ONLINE): sale de su stock y queda en tránsito hacia la tienda. */
CREATE OR ALTER PROCEDURE inventory.usp_stock_replenish
    @store_id NVARCHAR(50), @product_id NVARCHAR(50), @quantity INT, @user_login NVARCHAR(100) = NULL
AS
BEGIN
    SET NOCOUNT ON;
    SET XACT_ABORT ON;
    IF @store_id = N'ONLINE' THROW 50193, N'El almacén central no se repone a sí mismo.', 1;
    IF @quantity < 1 THROW 50194, N'La cantidad debe ser positiva.', 1;
    DECLARE @neg INT = -@quantity;
    BEGIN TRAN;
        EXEC inventory.usp_apply_stock_delta N'ONLINE', @product_id, N'ENVIO', @neg, 0, 0, N'REPOSICION', @store_id, @user_login, NULL;
        EXEC inventory.usp_apply_stock_delta @store_id, @product_id, N'ENVIO', 0, 0, @quantity, N'REPOSICION', N'ONLINE', @user_login, NULL;
    COMMIT;
END
GO

CREATE OR ALTER PROCEDURE inventory.usp_stock_receive
    @store_id NVARCHAR(50), @product_id NVARCHAR(50), @quantity INT, @user_login NVARCHAR(100) = NULL
AS
BEGIN
    SET NOCOUNT ON;
    SET XACT_ABORT ON;
    IF @quantity < 1 THROW 50195, N'La cantidad debe ser positiva.', 1;
    DECLARE @neg INT = -@quantity;
    BEGIN TRAN;
        EXEC inventory.usp_apply_stock_delta @store_id, @product_id, N'RECEPCION', @quantity, 0, @neg, N'RECEPCION', NULL, @user_login, NULL;
    COMMIT;
END
GO

CREATE OR ALTER PROCEDURE inventory.usp_stock_set_minimum
    @store_id NVARCHAR(50), @product_id NVARCHAR(50), @minimum INT, @user_login NVARCHAR(100) = NULL
AS
BEGIN
    SET NOCOUNT ON;
    IF @minimum < 0 OR @minimum > 500 THROW 50196, N'El mínimo debe estar entre 0 y 500.', 1;
    IF NOT EXISTS (SELECT 1 FROM inventory.stock_level WHERE store_id = @store_id AND product_id = @product_id)
        INSERT INTO inventory.stock_level (store_id, product_id) VALUES (@store_id, @product_id);
    UPDATE inventory.stock_level SET minimum_qty = @minimum, updated_at = SYSUTCDATETIME()
    WHERE store_id = @store_id AND product_id = @product_id;
    EXEC app.usp_audit @user_login, N'stock_minimum', N'stock_level', @product_id, @store_id;
END
GO

/* Cierre diario: fotografía el stock vivo en stock_snapshot (idempotente por fecha). */
CREATE OR ALTER PROCEDURE inventory.usp_stock_close_day @snapshot_date DATE = NULL, @user_login NVARCHAR(100) = NULL
AS
BEGIN
    SET NOCOUNT ON;
    SET @snapshot_date = ISNULL(@snapshot_date, CAST(SYSUTCDATETIME() AS DATE));
    MERGE inventory.stock_snapshot AS t
    USING (SELECT store_id, product_id, on_hand_qty, reserved_qty, in_transit_qty, minimum_qty FROM inventory.stock_level) AS s
       ON t.snapshot_date = @snapshot_date AND t.store_id = s.store_id AND t.product_id = s.product_id
    WHEN MATCHED THEN UPDATE SET closing_stock_qty = s.on_hand_qty, reserved_stock_qty = s.reserved_qty,
         in_transit_stock_qty = s.in_transit_qty, minimum_stock_qty = s.minimum_qty
    WHEN NOT MATCHED THEN INSERT (snapshot_date, store_id, product_id, closing_stock_qty, reserved_stock_qty, in_transit_stock_qty,
         minimum_stock_qty, source_system)
         VALUES (@snapshot_date, s.store_id, s.product_id, s.on_hand_qty, s.reserved_qty, s.in_transit_qty, s.minimum_qty, N'ERP');
    SELECT @@ROWCOUNT AS rows_written;
    EXEC app.usp_audit @user_login, N'stock_close_day', N'stock_snapshot', NULL, NULL;
END
GO

/* ---------- catálogo y tiendas ---------- */

CREATE OR ALTER PROCEDURE catalog.usp_product_upsert
    @product_id NVARCHAR(50) = NULL, @product_name NVARCHAR(255), @category NVARCHAR(100), @subcategory NVARCHAR(100) = NULL,
    @brand NVARCHAR(100) = NULL, @supplier NVARCHAR(100) = NULL, @material NVARCHAR(100) = NULL, @color NVARCHAR(100) = NULL,
    @sale_price DECIMAL(18,2), @unit_cost DECIMAL(18,2) = NULL, @vat_pct DECIMAL(9,4) = 21, @weight_kg DECIMAL(18,3) = NULL,
    @length_cm DECIMAL(18,2) = NULL, @width_cm DECIMAL(18,2) = NULL, @height_cm DECIMAL(18,2) = NULL,
    @product_status NVARCHAR(50) = N'Activo', @ean NVARCHAR(30) = NULL, @user_login NVARCHAR(100) = NULL
AS
BEGIN
    SET NOCOUNT ON;
    IF LEN(ISNULL(@product_name, N'')) < 3 THROW 50200, N'El nombre es obligatorio.', 1;
    IF @category NOT IN (N'Muebles', N'Decoración', N'Iluminación', N'Textil hogar') THROW 50201, N'Categoría no válida.', 1;
    IF @sale_price IS NULL OR @sale_price <= 0 THROW 50202, N'El precio debe ser positivo.', 1;
    IF @unit_cost IS NOT NULL AND @unit_cost >= @sale_price THROW 50203, N'El coste no puede igualar ni superar el precio.', 1;
    IF @ean IS NOT NULL AND @ean NOT LIKE N'[0-9][0-9][0-9][0-9][0-9][0-9][0-9][0-9][0-9][0-9][0-9][0-9][0-9]'
        THROW 50204, N'El EAN debe tener 13 dígitos.', 1;

    IF @product_id IS NULL
    BEGIN
        DECLARE @first BIGINT, @prefix NVARCHAR(30), @width TINYINT;
        EXEC app.usp_reserve_ids N'product', 1, @first OUTPUT, @prefix OUTPUT, @width OUTPUT;
        SET @product_id = app.fn_format_id(@prefix, @width, @first);
        INSERT INTO catalog.product (product_id, product_name, category, subcategory, brand, supplier, material, color, sale_price,
            unit_cost, vat_pct, weight_kg, length_cm, width_cm, height_cm, catalog_start_date, product_status, ean)
        VALUES (@product_id, @product_name, @category, @subcategory, @brand, @supplier, @material, @color, @sale_price, @unit_cost,
            @vat_pct, @weight_kg, @length_cm, @width_cm, @height_cm, CAST(SYSUTCDATETIME() AS DATE), @product_status, @ean);
    END
    ELSE
    BEGIN
        UPDATE catalog.product
           SET product_name = @product_name, category = @category, subcategory = @subcategory, brand = @brand, supplier = @supplier,
               material = @material, color = @color, sale_price = @sale_price, unit_cost = @unit_cost, vat_pct = @vat_pct,
               weight_kg = @weight_kg, length_cm = @length_cm, width_cm = @width_cm, height_cm = @height_cm,
               product_status = @product_status, ean = @ean, updated_at = SYSUTCDATETIME()
         WHERE product_id = @product_id;
        IF @@ROWCOUNT = 0 THROW 50205, N'El producto no existe.', 1;
    END
    EXEC app.usp_audit @user_login, N'product_upsert', N'product', @product_id, NULL;
    SELECT @product_id AS product_id;
END
GO

CREATE OR ALTER PROCEDURE store.usp_store_update
    @store_id NVARCHAR(50), @store_name NVARCHAR(150), @opening_hours NVARCHAR(100) = NULL, @phone NVARCHAR(50) = NULL,
    @manager_name NVARCHAR(150) = NULL, @store_status NVARCHAR(50), @opened_at DATE = NULL, @user_login NVARCHAR(100) = NULL
AS
BEGIN
    SET NOCOUNT ON;
    IF @store_status NOT IN (N'Activa', N'Planificada', N'Cerrada') THROW 50206, N'Estado de tienda no válido.', 1;
    UPDATE store.store SET store_name = @store_name, opening_hours = @opening_hours, phone = @phone, manager_name = @manager_name,
           store_status = @store_status, opened_at = ISNULL(@opened_at, opened_at), updated_at = SYSUTCDATETIME()
    WHERE store_id = @store_id;
    IF @@ROWCOUNT = 0 THROW 50207, N'La tienda no existe.', 1;
    EXEC app.usp_audit @user_login, N'store_update', N'store', @store_id, @store_status;
END
GO

/* ---------- CRM ---------- */

CREATE OR ALTER PROCEDURE crm.usp_customer_upsert
    @customer_id NVARCHAR(50) = NULL, @first_name NVARCHAR(100), @last_name NVARCHAR(150), @email NVARCHAR(255) = NULL,
    @phone NVARCHAR(50) = NULL, @birth_date DATE = NULL, @gender NVARCHAR(30) = NULL, @city NVARCHAR(100) = NULL,
    @province NVARCHAR(100) = NULL, @postal_code NVARCHAR(20) = NULL, @marketing_consent BIT = 0,
    @preferred_channel NVARCHAR(50) = NULL, @acquisition_source NVARCHAR(50) = N'tienda', @loyalty_tier NVARCHAR(50) = NULL,
    @user_login NVARCHAR(100) = NULL
AS
BEGIN
    SET NOCOUNT ON;
    SET XACT_ABORT ON;
    IF LEN(ISNULL(@first_name, N'')) < 2 OR LEN(ISNULL(@last_name, N'')) < 2 THROW 50210, N'Nombre y apellidos son obligatorios.', 1;
    IF @email IS NOT NULL AND @email NOT LIKE N'_%@_%._%' THROW 50211, N'El email no es válido.', 1;
    IF @email IS NOT NULL AND EXISTS (SELECT 1 FROM crm.customer WHERE email = LOWER(@email) AND customer_id <> ISNULL(@customer_id, N''))
        THROW 50212, N'Ya hay otro cliente con ese email.', 1;
    IF @postal_code IS NOT NULL AND @postal_code NOT LIKE N'[0-9][0-9][0-9][0-9][0-9]' THROW 50213, N'Código postal no válido.', 1;
    IF @gender IS NOT NULL AND @gender NOT IN (N'F', N'M', N'No binario') THROW 50214, N'Género no válido.', 1;
    IF @loyalty_tier IS NOT NULL AND @loyalty_tier NOT IN (N'Bronce', N'Plata', N'Oro', N'Platino') THROW 50215, N'Nivel no válido.', 1;
    IF @preferred_channel IS NOT NULL AND @preferred_channel NOT IN (N'Online', N'Tienda', N'Mixto') THROW 50216, N'Canal no válido.', 1;

    BEGIN TRAN;
    DECLARE @is_new BIT = CASE WHEN @customer_id IS NULL THEN 1 ELSE 0 END;
    IF @is_new = 1
    BEGIN
        DECLARE @first BIGINT, @prefix NVARCHAR(30), @width TINYINT;
        EXEC app.usp_reserve_ids N'customer', 1, @first OUTPUT, @prefix OUTPUT, @width OUTPUT;
        SET @customer_id = app.fn_format_id(@prefix, @width, @first);
        INSERT INTO crm.customer (customer_id, first_name, last_name, email, email_is_valid, phone, loyalty_joined_at, loyalty_tier,
            loyalty_points, birth_date, gender, city, province, postal_code, country_code, marketing_consent, customer_status,
            acquisition_source, preferred_channel, source_updated_at)
        VALUES (@customer_id, @first_name, @last_name, LOWER(@email), CASE WHEN @email IS NULL THEN NULL ELSE 1 END, @phone,
            CAST(SYSUTCDATETIME() AS DATE), ISNULL(@loyalty_tier, N'Bronce'), 0, @birth_date, @gender, @city, @province, @postal_code,
            'ES', @marketing_consent, N'Activo', @acquisition_source, @preferred_channel, SYSUTCDATETIME());
    END
    ELSE
    BEGIN
        UPDATE crm.customer
           SET first_name = @first_name, last_name = @last_name, email = LOWER(@email),
               email_is_valid = CASE WHEN @email IS NULL THEN NULL ELSE 1 END, phone = @phone, birth_date = @birth_date,
               gender = @gender, city = @city, province = @province, postal_code = @postal_code,
               marketing_consent = @marketing_consent, preferred_channel = @preferred_channel,
               loyalty_tier = ISNULL(@loyalty_tier, loyalty_tier),
               source_updated_at = SYSUTCDATETIME(), updated_at = SYSUTCDATETIME()
         WHERE customer_id = @customer_id;
        IF @@ROWCOUNT = 0 THROW 50217, N'El cliente no existe.', 1;
    END

    -- Toda alta o cambio de consentimiento deja una señal de identidad del CRM.
    DECLARE @signal_id NVARCHAR(50), @f BIGINT, @px NVARCHAR(30), @w TINYINT;
    EXEC app.usp_reserve_ids N'identity', 1, @f OUTPUT, @px OUTPUT, @w OUTPUT;
    SET @signal_id = app.fn_format_id(@px, @w, @f);
    INSERT INTO app.outbox (container_name, document_json)
    SELECT N'senales_identidad', (SELECT @signal_id AS id, @customer_id AS pk, @signal_id AS identity_signal_id,
            CONVERT(NVARCHAR(19), SYSUTCDATETIME(), 126) AS fecha_evento, N'CRM' AS fuente_sistema,
            CASE WHEN @is_new = 1 THEN N'alta_programa' ELSE N'actualizacion_crm' END AS tipo_senal,
            @customer_id AS customer_id_raw, @customer_id AS customer_id_candidato,
            CASE WHEN c.email IS NULL THEN NULL ELSE LOWER(LEFT(CONVERT(VARCHAR(64), HASHBYTES('SHA2_256', c.email), 2), 16)) END AS email_hash,
            CASE WHEN c.phone IS NULL THEN NULL
                 ELSE LOWER(LEFT(CONVERT(VARCHAR(64), HASHBYTES('SHA2_256', REPLACE(REPLACE(REPLACE(c.phone, N' ', N''), N'-', N''), N'+34', N'')), 2), 16)) END AS telefono_hash,
            CAST(NULL AS NVARCHAR(10)) AS tarjeta_fidelizacion_id, CAST(NULL AS NVARCHAR(10)) AS cookie_id,
            CAST(NULL AS NVARCHAR(10)) AS device_id, CAST(NULL AS NVARCHAR(10)) AS app_user_id,
            CAST(NULL AS NVARCHAR(10)) AS usuario_online_id, CAST(NULL AS NVARCHAR(10)) AS order_id,
            CAST(NULL AS NVARCHAR(10)) AS ticket_id, CAST(NULL AS NVARCHAR(10)) AS store_id,
            c.marketing_consent AS consentimiento_snapshot, 0.98 AS confianza_origen, N'web' AS origen
           FOR JSON PATH, WITHOUT_ARRAY_WRAPPER, INCLUDE_NULL_VALUES)
    FROM crm.customer c WHERE c.customer_id = @customer_id;

    EXEC app.usp_audit @user_login, N'customer_upsert', N'customer', @customer_id, NULL;
    COMMIT;
    SELECT @customer_id AS customer_id;
END
GO

CREATE OR ALTER PROCEDURE crm.usp_customer_set_status
    @customer_id NVARCHAR(50), @customer_status NVARCHAR(50), @user_login NVARCHAR(100) = NULL
AS
BEGIN
    SET NOCOUNT ON;
    IF @customer_status NOT IN (N'Activo', N'Inactivo', N'Bloqueado') THROW 50218, N'Estado no válido.', 1;
    UPDATE crm.customer
       SET customer_status = @customer_status,
           churned_at = CASE WHEN @customer_status = N'Inactivo' THEN CAST(SYSUTCDATETIME() AS DATE)
                             WHEN @customer_status = N'Activo' THEN NULL ELSE churned_at END,
           marketing_consent = CASE WHEN @customer_status = N'Activo' THEN marketing_consent ELSE 0 END,
           source_updated_at = SYSUTCDATETIME(), updated_at = SYSUTCDATETIME()
     WHERE customer_id = @customer_id;
    IF @@ROWCOUNT = 0 THROW 50217, N'El cliente no existe.', 1;
    EXEC app.usp_audit @user_login, N'customer_status', N'customer', @customer_id, @customer_status;
END
GO

CREATE OR ALTER PROCEDURE crm.usp_customer_adjust_points
    @customer_id NVARCHAR(50), @delta INT, @reason NVARCHAR(300), @user_login NVARCHAR(100) = NULL
AS
BEGIN
    SET NOCOUNT ON;
    IF @delta = 0 OR LEN(ISNULL(@reason, N'')) < 3 THROW 50219, N'Indica un ajuste distinto de cero y su motivo.', 1;
    UPDATE crm.customer SET loyalty_points = ISNULL(loyalty_points, 0) + @delta, updated_at = SYSUTCDATETIME()
    WHERE customer_id = @customer_id AND ISNULL(loyalty_points, 0) + @delta >= 0;
    IF @@ROWCOUNT = 0 THROW 50220, N'El cliente no existe o el saldo de puntos quedaría negativo.', 1;
    DECLARE @detail NVARCHAR(400) = CONCAT(@delta, N' · ', @reason);
    EXEC app.usp_audit @user_login, N'customer_points', N'customer', @customer_id, @detail;
END
GO

/* =========================== marketing =========================== */

CREATE OR ALTER PROCEDURE mkt.usp_campaign_upsert
    @campaign_id NVARCHAR(30) = NULL, @campaign_name NVARCHAR(200), @objective NVARCHAR(50), @channel NVARCHAR(20),
    @starts_at DATETIME2(0), @ends_at DATETIME2(0), @target_segment NVARCHAR(50), @target_category NVARCHAR(100) = NULL,
    @target_store_id NVARCHAR(50) = NULL, @offer_type NVARCHAR(30), @discount_pct DECIMAL(5,2) = 0, @budget_eur DECIMAL(12,2) = NULL,
    @control_group_pct DECIMAL(5,3) = 0.10, @primary_kpi NVARCHAR(50) = NULL, @copy_axis NVARCHAR(500) = NULL,
    @user_login NVARCHAR(100) = NULL
AS
BEGIN
    SET NOCOUNT ON;
    IF LEN(ISNULL(@campaign_name, N'')) < 5 THROW 50300, N'El nombre de la campaña es obligatorio.', 1;
    IF @objective NOT IN (N'trafico_tienda', N'reactivacion', N'cross_sell', N'promocion', N'upsell', N'retencion', N'captacion', N'onboarding')
        THROW 50301, N'Objetivo no válido.', 1;
    IF @channel NOT IN (N'EMAIL', N'SMS', N'PUSH') THROW 50302, N'Canal no válido.', 1;
    IF @ends_at < @starts_at THROW 50303, N'La campaña termina antes de empezar.', 1;
    IF @offer_type NOT IN (N'descuento_pct', N'cupon_importe', N'puntos', N'acceso_anticipado', N'financiacion')
        THROW 50304, N'Tipo de oferta no válido.', 1;
    IF @offer_type IN (N'descuento_pct', N'cupon_importe') AND ISNULL(@discount_pct, 0) <= 0
        THROW 50305, N'La oferta necesita un descuento.', 1;
    IF @offer_type = N'descuento_pct' AND @discount_pct > 40 THROW 50306, N'El descuento máximo es del 40 %.', 1;
    IF @target_category IS NOT NULL AND @target_category NOT IN (N'Muebles', N'Decoración', N'Iluminación', N'Textil hogar')
        THROW 50307, N'Categoría no válida.', 1;
    IF @target_segment = N'LOCAL_STORE' AND @target_store_id IS NULL THROW 50308, N'Una campaña local necesita tienda.', 1;

    IF @campaign_id IS NULL
    BEGIN
        DECLARE @first BIGINT, @prefix NVARCHAR(30), @width TINYINT;
        EXEC app.usp_reserve_ids N'campaign', 1, @first OUTPUT, @prefix OUTPUT, @width OUTPUT;
        SET @campaign_id = app.fn_format_id(@prefix, @width, @first);
        INSERT INTO mkt.campaign (campaign_id, campaign_name, objective, channel, starts_at, ends_at, target_segment, target_category,
            target_store_id, offer_type, discount_pct, budget_eur, control_group_pct, primary_kpi, campaign_status, copy_axis, created_by)
        VALUES (@campaign_id, @campaign_name, @objective, @channel, @starts_at, @ends_at, @target_segment, @target_category,
            @target_store_id, @offer_type, ISNULL(@discount_pct, 0), @budget_eur, @control_group_pct, @primary_kpi, N'borrador',
            @copy_axis, @user_login);
    END
    ELSE
    BEGIN
        UPDATE mkt.campaign
           SET campaign_name = @campaign_name, objective = @objective, channel = @channel, starts_at = @starts_at, ends_at = @ends_at,
               target_segment = @target_segment, target_category = @target_category, target_store_id = @target_store_id,
               offer_type = @offer_type, discount_pct = ISNULL(@discount_pct, 0), budget_eur = @budget_eur,
               control_group_pct = @control_group_pct, primary_kpi = @primary_kpi, copy_axis = @copy_axis, updated_at = SYSUTCDATETIME()
         WHERE campaign_id = @campaign_id AND campaign_status = N'borrador';
        IF @@ROWCOUNT = 0 THROW 50309, N'Solo se puede editar una campaña en borrador.', 1;
    END
    EXEC app.usp_audit @user_login, N'campaign_upsert', N'campaign', @campaign_id, NULL;
    SELECT @campaign_id AS campaign_id;
END
GO

/* Clientes que cumplen un segmento. Reglas explícitas para poder explicarlas en clase. */
CREATE OR ALTER FUNCTION mkt.fn_segment_customers (@segment NVARCHAR(50), @store_id NVARCHAR(50), @category NVARCHAR(100), @at DATETIME2(0))
RETURNS TABLE
AS
RETURN
    SELECT c.customer_id
    FROM crm.customer c
    WHERE c.customer_status = N'Activo' AND c.marketing_consent = 1
      AND (
           (@segment = N'VIP_OMNICANAL' AND c.loyalty_tier IN (N'Oro', N'Platino'))
        OR (@segment = N'LOCAL_STORE' AND EXISTS (SELECT 1 FROM mkt.customer_store_affinity a
                WHERE a.customer_id = c.customer_id AND (a.preferred_store_id = @store_id OR a.nearest_store_id = @store_id)))
        OR (@segment = N'NUEVO_CONTACTABLE' AND c.loyalty_joined_at >= DATEADD(DAY, -365, @at))
        OR (@segment = N'RIESGO_CHURN'
            AND NOT EXISTS (SELECT 1 FROM sales.online_order o WHERE o.customer_id = c.customer_id AND o.ordered_at >= DATEADD(DAY, -180, @at))
            AND NOT EXISTS (SELECT 1 FROM sales.pos_ticket t WHERE t.customer_id = c.customer_id AND t.ticket_at >= DATEADD(DAY, -180, @at))
            AND (EXISTS (SELECT 1 FROM sales.online_order o WHERE o.customer_id = c.customer_id)
              OR EXISTS (SELECT 1 FROM sales.pos_ticket t WHERE t.customer_id = c.customer_id)))
        OR (@segment = N'ALTO_TICKET_MUEBLES' AND (
                EXISTS (SELECT 1 FROM sales.online_order_line l JOIN sales.online_order o ON o.order_id = l.order_id
                        WHERE o.customer_id = c.customer_id AND l.category = N'Muebles' AND l.line_amount >= 300)
             OR EXISTS (SELECT 1 FROM sales.pos_ticket_line l JOIN sales.pos_ticket t ON t.ticket_id = l.ticket_id
                        WHERE t.customer_id = c.customer_id AND l.category = N'Muebles' AND l.line_amount >= 300)))
        OR (@segment = N'POST_DEVOLUCION' AND EXISTS (SELECT 1 FROM [returns].return_header r
                WHERE r.customer_id = c.customer_id AND r.returned_at >= DATEADD(DAY, -120, @at)))
        OR (@segment = N'PROMO_SENSIBLE_TEXTIL' AND (
                EXISTS (SELECT 1 FROM sales.online_order_line l JOIN sales.online_order o ON o.order_id = l.order_id
                        WHERE o.customer_id = c.customer_id AND l.category = N'Textil hogar' AND l.discount_amount > 0)
             OR EXISTS (SELECT 1 FROM sales.pos_ticket_line l JOIN sales.pos_ticket t ON t.ticket_id = l.ticket_id
                        WHERE t.customer_id = c.customer_id AND l.category = N'Textil hogar' AND l.discount_amount > 0)))
        OR (@segment = N'ACTIVO_BASE' AND (
                EXISTS (SELECT 1 FROM sales.online_order o WHERE o.customer_id = c.customer_id AND o.ordered_at >= DATEADD(DAY, -365, @at))
             OR EXISTS (SELECT 1 FROM sales.pos_ticket t WHERE t.customer_id = c.customer_id AND t.ticket_at >= DATEADD(DAY, -365, @at))))
        OR (@segment = N'TODOS')
      );
GO

/* Construye la audiencia: segmento + consentimiento, grupo de control
   determinista (hash de cliente y campaña) y recomendaciones de producto. */
CREATE OR ALTER PROCEDURE mkt.usp_campaign_build_audience
    @campaign_id NVARCHAR(30), @max_contacts INT = 300, @user_login NVARCHAR(100) = NULL
AS
BEGIN
    SET NOCOUNT ON;
    SET XACT_ABORT ON;
    DECLARE @status NVARCHAR(20), @segment NVARCHAR(50), @store NVARCHAR(50), @category NVARCHAR(100), @channel NVARCHAR(20),
            @control DECIMAL(5,3), @starts DATETIME2(0);
    SELECT @status = campaign_status, @segment = target_segment, @store = target_store_id, @category = target_category,
           @channel = channel, @control = control_group_pct, @starts = starts_at
    FROM mkt.campaign WHERE campaign_id = @campaign_id;
    IF @status IS NULL THROW 50310, N'La campaña no existe.', 1;
    IF @status NOT IN (N'borrador', N'audiencia') THROW 50311, N'La audiencia ya no se puede rehacer.', 1;

    DECLARE @audience TABLE (customer_id NVARCHAR(50) PRIMARY KEY, is_control BIT, rn INT);
    INSERT INTO @audience (customer_id, is_control, rn)
    SELECT TOP (@max_contacts) s.customer_id,
           CASE WHEN ABS(CHECKSUM(s.customer_id, @campaign_id)) % 1000 < @control * 1000 THEN 1 ELSE 0 END,
           ROW_NUMBER() OVER (ORDER BY s.customer_id)
    FROM mkt.fn_segment_customers(@segment, @store, @category, SYSUTCDATETIME()) s
    JOIN crm.customer c ON c.customer_id = s.customer_id
    WHERE (@channel <> N'EMAIL' OR (c.email IS NOT NULL AND c.email_is_valid = 1))
      AND (@channel <> N'SMS' OR c.phone IS NOT NULL)
    ORDER BY s.customer_id;

    DECLARE @n INT = (SELECT COUNT(*) FROM @audience);
    IF @n = 0 THROW 50312, N'La audiencia está vacía: ningún cliente con consentimiento cumple el segmento.', 1;

    -- Los dos productos más vendidos de la categoría objetivo (o de todo el catálogo).
    DECLARE @rec1 NVARCHAR(50), @rec2 NVARCHAR(50);
    WITH sold AS (
        SELECT l.product_id, SUM(l.quantity) AS units FROM sales.online_order_line l
        JOIN catalog.product p ON p.product_id = l.product_id
        WHERE p.product_status = N'Activo' AND (@category IS NULL OR p.category = @category) GROUP BY l.product_id
        UNION ALL
        SELECT l.product_id, SUM(l.quantity) FROM sales.pos_ticket_line l
        JOIN catalog.product p ON p.product_id = l.product_id
        WHERE p.product_status = N'Activo' AND (@category IS NULL OR p.category = @category) GROUP BY l.product_id),
    ranked AS (SELECT product_id, ROW_NUMBER() OVER (ORDER BY SUM(units) DESC, product_id) AS rn FROM sold GROUP BY product_id)
    SELECT @rec1 = MAX(CASE WHEN rn = 1 THEN product_id END), @rec2 = MAX(CASE WHEN rn = 2 THEN product_id END) FROM ranked;

    BEGIN TRAN;
    DELETE FROM mkt.campaign_contact WHERE campaign_id = @campaign_id;
    DECLARE @first BIGINT, @prefix NVARCHAR(30), @width TINYINT;
    EXEC app.usp_reserve_ids N'contact', @n, @first OUTPUT, @prefix OUTPUT, @width OUTPUT;

    INSERT INTO mkt.campaign_contact (contact_id, campaign_id, customer_id, contacted_at, contact_channel, experiment_group, is_control,
        assigned_segment, offer_code, delivery_status, contact_cost_eur, contact_priority, personalized_store_id,
        recommended_product_1, recommended_product_2)
    SELECT app.fn_format_id(@prefix, @width, @first + a.rn - 1), @campaign_id, a.customer_id, NULL, @channel,
           CASE WHEN a.is_control = 1 THEN N'control' ELSE N'treatment' END, a.is_control, @segment,
           N'OFF-' + RIGHT(@campaign_id, 3),
           CASE WHEN a.is_control = 1 THEN N'holdout_control' ELSE N'pendiente' END,
           CASE WHEN a.is_control = 1 THEN 0 WHEN @channel = N'EMAIL' THEN 0.018 WHEN @channel = N'SMS' THEN 0.055 ELSE 0.009 END,
           CASE WHEN c.loyalty_tier IN (N'Oro', N'Platino') THEN N'Alta' ELSE N'Media' END,
           ISNULL(@store, af.preferred_store_id), @rec1, @rec2
    FROM @audience a
    JOIN crm.customer c ON c.customer_id = a.customer_id
    LEFT JOIN mkt.customer_store_affinity af ON af.customer_id = a.customer_id;

    UPDATE mkt.campaign SET campaign_status = N'audiencia', updated_at = SYSUTCDATETIME() WHERE campaign_id = @campaign_id;
    EXEC app.usp_audit @user_login, N'campaign_audience', N'campaign', @campaign_id, NULL;
    COMMIT;
    SELECT @n AS contacts, SUM(CAST(is_control AS INT)) AS control_contacts FROM @audience;
END
GO

/* Emite un cupón por contacto del grupo de tratamiento. */
CREATE OR ALTER PROCEDURE mkt.usp_campaign_issue_coupons
    @campaign_id NVARCHAR(30), @valid_days INT = 15, @min_spend_eur DECIMAL(10,2) = 0, @user_login NVARCHAR(100) = NULL
AS
BEGIN
    SET NOCOUNT ON;
    SET XACT_ABORT ON;
    DECLARE @status NVARCHAR(20), @offer NVARCHAR(30), @discount DECIMAL(5,2), @category NVARCHAR(100), @store NVARCHAR(50),
            @channel NVARCHAR(20), @starts DATETIME2(0);
    SELECT @status = campaign_status, @offer = offer_type, @discount = discount_pct, @category = target_category,
           @store = target_store_id, @channel = channel, @starts = starts_at
    FROM mkt.campaign WHERE campaign_id = @campaign_id;
    IF @status IS NULL THROW 50310, N'La campaña no existe.', 1;
    IF @status <> N'audiencia' THROW 50313, N'Primero construye la audiencia.', 1;
    IF @offer NOT IN (N'descuento_pct', N'cupon_importe') THROW 50314, N'Esta oferta no usa cupones.', 1;
    IF @valid_days NOT BETWEEN 1 AND 90 THROW 50315, N'La validez debe estar entre 1 y 90 días.', 1;

    DECLARE @targets TABLE (contact_id NVARCHAR(30) PRIMARY KEY, customer_id NVARCHAR(50), rn INT);
    INSERT INTO @targets SELECT contact_id, customer_id, ROW_NUMBER() OVER (ORDER BY contact_id)
    FROM mkt.campaign_contact WHERE campaign_id = @campaign_id AND is_control = 0 AND coupon_instance_id IS NULL;
    DECLARE @n INT = (SELECT COUNT(*) FROM @targets);
    IF @n = 0 THROW 50316, N'No hay contactos de tratamiento sin cupón.', 1;

    DECLARE @from DATETIME2(0) = CASE WHEN @starts > SYSUTCDATETIME() THEN @starts ELSE SYSUTCDATETIME() END;
    BEGIN TRAN;
    DECLARE @f1 BIGINT, @p1 NVARCHAR(30), @w1 TINYINT, @f2 BIGINT, @p2 NVARCHAR(30), @w2 TINYINT;
    EXEC app.usp_reserve_ids N'coupon', @n, @f1 OUTPUT, @p1 OUTPUT, @w1 OUTPUT;
    EXEC app.usp_reserve_ids N'coupon_code', @n, @f2 OUTPUT, @p2 OUTPUT, @w2 OUTPUT;
    INSERT INTO mkt.coupon (coupon_instance_id, coupon_code, campaign_id, customer_id, issued_at, valid_from, valid_to, coupon_type,
        discount_pct, discount_eur, min_spend_eur, restricted_category, restricted_store_id, issue_channel, coupon_status)
    SELECT app.fn_format_id(@p1, @w1, @f1 + rn - 1), app.fn_format_id(@p2, @w2, @f2 + rn - 1), @campaign_id, customer_id,
           SYSUTCDATETIME(), @from, DATEADD(DAY, @valid_days, @from),
           CASE WHEN @offer = N'descuento_pct' THEN N'porcentaje' ELSE N'importe_fijo' END,
           CASE WHEN @offer = N'descuento_pct' THEN @discount END,
           CASE WHEN @offer = N'cupon_importe' THEN @discount END,
           @min_spend_eur, @category, @store, @channel, N'emitido'
    FROM @targets;
    UPDATE cc SET coupon_instance_id = app.fn_format_id(@p1, @w1, @f1 + t.rn - 1)
    FROM mkt.campaign_contact cc JOIN @targets t ON t.contact_id = cc.contact_id;
    EXEC app.usp_audit @user_login, N'campaign_coupons', N'campaign', @campaign_id, NULL;
    COMMIT;
    SELECT @n AS coupons_issued;
END
GO

/* Lanzamiento simulado: entrega, aperturas y clics con probabilidades
   fijas por canal y un hash determinista, para que la demo sea repetible. */
CREATE OR ALTER PROCEDURE mkt.usp_campaign_launch @campaign_id NVARCHAR(30), @user_login NVARCHAR(100) = NULL
AS
BEGIN
    SET NOCOUNT ON;
    SET XACT_ABORT ON;
    DECLARE @status NVARCHAR(20), @channel NVARCHAR(20);
    SELECT @status = campaign_status, @channel = channel FROM mkt.campaign WHERE campaign_id = @campaign_id;
    IF @status IS NULL THROW 50310, N'La campaña no existe.', 1;
    IF @status <> N'audiencia' THROW 50317, N'Solo se lanza una campaña con audiencia preparada.', 1;

    DECLARE @now DATETIME2(0) = SYSUTCDATETIME();
    DECLARE @open_rate INT = CASE @channel WHEN N'EMAIL' THEN 380 WHEN N'PUSH' THEN 250 ELSE 0 END;     -- por mil entregados
    DECLARE @click_rate INT = CASE @channel WHEN N'SMS' THEN 120 ELSE 300 END;                          -- por mil abiertos (SMS: por mil entregados)

    BEGIN TRAN;
    UPDATE mkt.campaign_contact
       SET contacted_at = DATEADD(MINUTE, ABS(CHECKSUM(contact_id)) % 240, @now),
           delivery_status = CASE WHEN ABS(CHECKSUM(contact_id, N'd')) % 1000 < 10 THEN N'bounce'
                                  WHEN ABS(CHECKSUM(contact_id, N'd')) % 1000 < 18 THEN N'rechazado'
                                  WHEN ABS(CHECKSUM(contact_id, N'd')) % 1000 < 20 THEN N'fallido'
                                  ELSE N'entregado' END
     WHERE campaign_id = @campaign_id AND is_control = 0 AND delivery_status = N'pendiente';
    UPDATE mkt.campaign_contact SET contacted_at = DATEADD(MINUTE, ABS(CHECKSUM(contact_id)) % 240, @now)
     WHERE campaign_id = @campaign_id AND is_control = 1;

    -- Eventos simulados: uno por estado de entrega, apertura, clic y visita a la landing.
    DECLARE @events TABLE (rn INT IDENTITY(1,1), contact_id NVARCHAR(30), customer_id NVARCHAR(50), tipo_evento NVARCHAR(30),
                           fecha_evento DATETIME2(0), origen NVARCHAR(20), device NVARCHAR(10));
    INSERT INTO @events (contact_id, customer_id, tipo_evento, fecha_evento, origen, device)
    SELECT contact_id, customer_id, CASE WHEN delivery_status = N'entregado' THEN N'delivered' ELSE delivery_status END,
           contacted_at, @channel, CASE WHEN @channel = N'EMAIL' AND ABS(CHECKSUM(contact_id, N'm')) % 2 = 0 THEN N'desktop' ELSE N'mobile' END
    FROM mkt.campaign_contact WHERE campaign_id = @campaign_id AND is_control = 0;

    INSERT INTO @events (contact_id, customer_id, tipo_evento, fecha_evento, origen, device)
    SELECT contact_id, customer_id, N'open', DATEADD(MINUTE, 30 + ABS(CHECKSUM(contact_id, N'o')) % 600, contacted_at), N'tracking',
           CASE WHEN @channel = N'EMAIL' AND ABS(CHECKSUM(contact_id, N'm')) % 2 = 0 THEN N'desktop' ELSE N'mobile' END
    FROM mkt.campaign_contact
    WHERE campaign_id = @campaign_id AND is_control = 0 AND delivery_status = N'entregado'
      AND ABS(CHECKSUM(contact_id, N'o')) % 1000 < @open_rate;

    INSERT INTO @events (contact_id, customer_id, tipo_evento, fecha_evento, origen, device)
    SELECT e.contact_id, e.customer_id, v.tipo, DATEADD(MINUTE, v.offset_min, e.fecha_evento), N'web', e.device
    FROM @events e
    CROSS APPLY (VALUES (N'click', 5), (N'landing_visit', 6)) AS v(tipo, offset_min)
    WHERE ((@channel = N'SMS' AND e.tipo_evento = N'delivered') OR (@channel <> N'SMS' AND e.tipo_evento = N'open'))
      AND ABS(CHECKSUM(e.contact_id, N'c')) % 1000 < @click_rate;

    DECLARE @n INT = (SELECT COUNT(*) FROM @events);
    DECLARE @first BIGINT, @prefix NVARCHAR(30), @width TINYINT;
    EXEC app.usp_reserve_ids N'campaign_event', @n, @first OUTPUT, @prefix OUTPUT, @width OUTPUT;

    INSERT INTO app.outbox (container_name, document_json)
    SELECT N'eventos_campana',
           (SELECT app.fn_format_id(@prefix, @width, @first + e.rn - 1) AS id, @campaign_id AS pk,
                   app.fn_format_id(@prefix, @width, @first + e.rn - 1) AS event_id, e.contact_id, @campaign_id AS campaign_id,
                   e.customer_id, CONVERT(NVARCHAR(19), e.fecha_evento, 126) AS fecha_evento, e.tipo_evento,
                   CAST(NULL AS NVARCHAR(10)) AS order_id, CAST(NULL AS NVARCHAR(10)) AS ticket_id,
                   CAST(NULL AS NVARCHAR(10)) AS store_id, 0.0 AS revenue_atribuido_eur, 0.0 AS margen_atribuido_eur,
                   e.device AS device_type, e.origen AS origen_evento, N'web' AS origen
            FOR JSON PATH, WITHOUT_ARRAY_WRAPPER, INCLUDE_NULL_VALUES)
    FROM @events e;

    UPDATE mkt.campaign SET campaign_status = N'activa', updated_at = SYSUTCDATETIME() WHERE campaign_id = @campaign_id;
    EXEC app.usp_audit @user_login, N'campaign_launch', N'campaign', @campaign_id, NULL;
    COMMIT;
    SELECT @n AS events_generated;
END
GO

/* Atribución a 30 días: primera compra (pedido o ticket) del cliente en los
   30 días siguientes al contacto, para tratamiento y control. Genera los
   eventos de compra y de canje de cupón que todavía no existían. */
CREATE OR ALTER PROCEDURE mkt.usp_campaign_attribute @campaign_id NVARCHAR(30), @user_login NVARCHAR(100) = NULL
AS
BEGIN
    SET NOCOUNT ON;
    SET XACT_ABORT ON;
    DECLARE @status NVARCHAR(20);
    SELECT @status = campaign_status FROM mkt.campaign WHERE campaign_id = @campaign_id;
    IF @status IS NULL THROW 50310, N'La campaña no existe.', 1;
    IF @status NOT IN (N'activa', N'finalizada') THROW 50318, N'La campaña todavía no se ha lanzado.', 1;

    DECLARE @conv TABLE (rn INT IDENTITY(1,1), contact_id NVARCHAR(30), customer_id NVARCHAR(50), is_control BIT,
        order_id NVARCHAR(50), ticket_id NVARCHAR(50), store_id NVARCHAR(50), bought_at DATETIME2(0), revenue DECIMAL(12,2),
        margin DECIMAL(12,2), coupon_redeemed BIT);

    INSERT INTO @conv (contact_id, customer_id, is_control, order_id, ticket_id, store_id, bought_at, revenue, margin, coupon_redeemed)
    SELECT cc.contact_id, cc.customer_id, cc.is_control, x.order_id, x.ticket_id, x.store_id, x.bought_at, x.revenue, x.margin,
           CASE WHEN cp.coupon_status = N'canjeado' AND (cp.order_id = x.order_id OR cp.ticket_id = x.ticket_id) THEN 1 ELSE 0 END
    FROM mkt.campaign_contact cc
    LEFT JOIN mkt.coupon cp ON cp.coupon_instance_id = cc.coupon_instance_id
    CROSS APPLY (
        SELECT TOP 1 * FROM (
            SELECT o.order_id, CAST(NULL AS NVARCHAR(50)) AS ticket_id, CAST(NULL AS NVARCHAR(50)) AS store_id, o.ordered_at AS bought_at,
                   o.order_total - ISNULL(o.shipping_amount, 0) AS revenue,
                   o.order_total - ISNULL(o.shipping_amount, 0)
                     - ISNULL((SELECT SUM(l.quantity * ISNULL(p.unit_cost, 0)) FROM sales.online_order_line l
                               LEFT JOIN catalog.product p ON p.product_id = l.product_id WHERE l.order_id = o.order_id), 0) AS margin
            FROM sales.online_order o
            WHERE o.customer_id = cc.customer_id AND o.order_status <> N'Cancelado'
              AND o.ordered_at > cc.contacted_at AND o.ordered_at <= DATEADD(DAY, 30, cc.contacted_at)
            UNION ALL
            SELECT NULL, t.ticket_id, t.store_id, t.ticket_at, t.ticket_net_amount,
                   t.ticket_net_amount - ISNULL((SELECT SUM(l.quantity * ISNULL(p.unit_cost, 0)) FROM sales.pos_ticket_line l
                                                 LEFT JOIN catalog.product p ON p.product_id = l.product_id WHERE l.ticket_id = t.ticket_id), 0)
            FROM sales.pos_ticket t
            WHERE t.customer_id = cc.customer_id AND t.ticket_at > cc.contacted_at AND t.ticket_at <= DATEADD(DAY, 30, cc.contacted_at)
        ) AS purchases ORDER BY bought_at) AS x
    WHERE cc.campaign_id = @campaign_id AND cc.contacted_at IS NOT NULL AND cc.conversion_30d = 0
      AND cc.delivery_status IN (N'entregado', N'holdout_control');

    DECLARE @n INT = (SELECT COUNT(*) FROM @conv);
    BEGIN TRAN;
    UPDATE cc SET conversion_30d = 1, conversion_order_id = c.order_id, conversion_ticket_id = c.ticket_id,
           revenue_30d_eur = c.revenue, margin_30d_eur = c.margin, converted_at = c.bought_at
    FROM mkt.campaign_contact cc JOIN @conv c ON c.contact_id = cc.contact_id;

    UPDATE tc SET attributed_campaign_id = @campaign_id
    FROM fin.transaction_cost tc JOIN @conv c ON (tc.order_id = c.order_id OR tc.ticket_id = c.ticket_id)
    WHERE c.is_control = 0 AND tc.attributed_campaign_id IS NULL;

    -- Eventos: compra para cada conversión de tratamiento y canje cuando usó el cupón.
    DECLARE @events TABLE (rn INT IDENTITY(1,1), contact_id NVARCHAR(30), customer_id NVARCHAR(50), tipo NVARCHAR(30),
        fecha DATETIME2(0), order_id NVARCHAR(50), ticket_id NVARCHAR(50), store_id NVARCHAR(50), revenue DECIMAL(12,2), margin DECIMAL(12,2));
    INSERT INTO @events (contact_id, customer_id, tipo, fecha, order_id, ticket_id, store_id, revenue, margin)
    SELECT contact_id, customer_id, N'purchase', bought_at, order_id, ticket_id, store_id, revenue, margin FROM @conv WHERE is_control = 0
    UNION ALL
    SELECT contact_id, customer_id, N'redeem_coupon', bought_at, order_id, ticket_id, store_id, 0, 0 FROM @conv WHERE is_control = 0 AND coupon_redeemed = 1;

    DECLARE @m INT = (SELECT COUNT(*) FROM @events);
    IF @m > 0
    BEGIN
        DECLARE @first BIGINT, @prefix NVARCHAR(30), @width TINYINT;
        EXEC app.usp_reserve_ids N'campaign_event', @m, @first OUTPUT, @prefix OUTPUT, @width OUTPUT;
        INSERT INTO app.outbox (container_name, document_json)
        SELECT N'eventos_campana',
               (SELECT app.fn_format_id(@prefix, @width, @first + e.rn - 1) AS id, @campaign_id AS pk,
                       app.fn_format_id(@prefix, @width, @first + e.rn - 1) AS event_id, e.contact_id, @campaign_id AS campaign_id,
                       e.customer_id, CONVERT(NVARCHAR(19), e.fecha, 126) AS fecha_evento, e.tipo AS tipo_evento,
                       e.order_id, e.ticket_id, e.store_id, e.revenue AS revenue_atribuido_eur, e.margin AS margen_atribuido_eur,
                       CASE WHEN e.ticket_id IS NULL THEN N'desktop' ELSE N'mobile' END AS device_type, N'attribution' AS origen_evento, N'web' AS origen
                FOR JSON PATH, WITHOUT_ARRAY_WRAPPER, INCLUDE_NULL_VALUES)
        FROM @events e;
    END
    EXEC app.usp_audit @user_login, N'campaign_attribute', N'campaign', @campaign_id, NULL;
    COMMIT;
    SELECT @n AS new_conversions, @m AS events_generated;
END
GO

CREATE OR ALTER PROCEDURE mkt.usp_campaign_close @campaign_id NVARCHAR(30), @user_login NVARCHAR(100) = NULL
AS
BEGIN
    SET NOCOUNT ON;
    SET XACT_ABORT ON;
    DECLARE @status NVARCHAR(20) = (SELECT campaign_status FROM mkt.campaign WHERE campaign_id = @campaign_id);
    IF @status IS NULL THROW 50310, N'La campaña no existe.', 1;
    IF @status NOT IN (N'activa', N'borrador', N'audiencia') THROW 50319, N'La campaña ya está cerrada.', 1;
    BEGIN TRAN;
    UPDATE mkt.campaign SET campaign_status = CASE WHEN @status = N'activa' THEN N'finalizada' ELSE N'cancelada' END,
           updated_at = SYSUTCDATETIME()
    WHERE campaign_id = @campaign_id;
    UPDATE mkt.coupon SET coupon_status = CASE WHEN @status = N'activa' THEN N'expirado' ELSE N'anulado' END
    WHERE campaign_id = @campaign_id AND coupon_status = N'emitido';
    EXEC app.usp_audit @user_login, N'campaign_close', N'campaign', @campaign_id, NULL;
    COMMIT;
END
GO

/* Cupón suelto de compensación (atención al cliente). */
CREATE OR ALTER PROCEDURE mkt.usp_coupon_issue_single
    @customer_id NVARCHAR(50), @coupon_type NVARCHAR(20), @value DECIMAL(10,2), @valid_days INT = 30,
    @issue_channel NVARCHAR(20) = N'ATENCION', @user_login NVARCHAR(100) = NULL
AS
BEGIN
    SET NOCOUNT ON;
    SET XACT_ABORT ON;
    IF NOT EXISTS (SELECT 1 FROM crm.customer WHERE customer_id = @customer_id) THROW 50320, N'El cliente no existe.', 1;
    IF @coupon_type NOT IN (N'porcentaje', N'importe_fijo') THROW 50321, N'Tipo de cupón no válido.', 1;
    IF @value <= 0 OR (@coupon_type = N'porcentaje' AND @value > 30) OR (@coupon_type = N'importe_fijo' AND @value > 100)
        THROW 50322, N'Compensación fuera de límites (máx. 30 % o 100 €).', 1;
    BEGIN TRAN;
    DECLARE @f1 BIGINT, @p1 NVARCHAR(30), @w1 TINYINT, @f2 BIGINT, @p2 NVARCHAR(30), @w2 TINYINT;
    EXEC app.usp_reserve_ids N'coupon', 1, @f1 OUTPUT, @p1 OUTPUT, @w1 OUTPUT;
    EXEC app.usp_reserve_ids N'coupon_code', 1, @f2 OUTPUT, @p2 OUTPUT, @w2 OUTPUT;
    DECLARE @id NVARCHAR(30) = app.fn_format_id(@p1, @w1, @f1), @code NVARCHAR(30) = app.fn_format_id(@p2, @w2, @f2);
    INSERT INTO mkt.coupon (coupon_instance_id, coupon_code, campaign_id, customer_id, issued_at, valid_from, valid_to, coupon_type,
        discount_pct, discount_eur, min_spend_eur, issue_channel, coupon_status)
    VALUES (@id, @code, NULL, @customer_id, SYSUTCDATETIME(), SYSUTCDATETIME(), DATEADD(DAY, @valid_days, SYSUTCDATETIME()),
        @coupon_type, CASE WHEN @coupon_type = N'porcentaje' THEN @value END, CASE WHEN @coupon_type = N'importe_fijo' THEN @value END,
        0, @issue_channel, N'emitido');
    EXEC app.usp_audit @user_login, N'coupon_single', N'coupon', @id, @customer_id;
    COMMIT;
    SELECT @id AS coupon_instance_id, @code AS coupon_code;
END
GO

CREATE OR ALTER PROCEDURE mkt.usp_promotion_upsert
    @promo_id NVARCHAR(30) = NULL, @promo_name NVARCHAR(200), @starts_at DATETIME2(0), @ends_at DATETIME2(0),
    @scope_type NVARCHAR(30), @scope_id NVARCHAR(150), @promo_type NVARCHAR(30), @discount_pct DECIMAL(5,2) = NULL,
    @discount_eur DECIMAL(10,2) = NULL, @channel NVARCHAR(20), @target_segment NVARCHAR(50) = NULL, @store_id NVARCHAR(50) = NULL,
    @combinable BIT = 0, @basket_threshold_eur DECIMAL(10,2) = 0, @min_margin_pct DECIMAL(5,2) = NULL,
    @related_campaign_id NVARCHAR(30) = NULL, @user_login NVARCHAR(100) = NULL
AS
BEGIN
    SET NOCOUNT ON;
    IF LEN(ISNULL(@promo_name, N'')) < 5 THROW 50330, N'El nombre de la promoción es obligatorio.', 1;
    IF @ends_at < @starts_at THROW 50331, N'La promoción termina antes de empezar.', 1;
    IF @scope_type NOT IN (N'categoria', N'categoria_tienda', N'campana') THROW 50332, N'Ámbito no válido.', 1;
    IF @promo_type NOT IN (N'descuento_pct', N'bundle', N'envio_gratis', N'2a_unidad', N'cupon_importe', N'puntos', N'regalo', N'outlet')
        THROW 50333, N'Tipo de promoción no válido.', 1;
    IF @promo_type = N'descuento_pct' AND (ISNULL(@discount_pct, 0) <= 0 OR @discount_pct > 50) THROW 50334, N'Descuento entre 0 y 50 %.', 1;
    IF @channel NOT IN (N'EMAIL', N'SMS', N'PUSH', N'WEB') THROW 50335, N'Canal no válido.', 1;
    IF @scope_type = N'categoria_tienda' AND @scope_id NOT LIKE N'%|%' THROW 50336, N'El ámbito categoría-tienda es «Categoría|S00X».', 1;
    IF @min_margin_pct IS NOT NULL AND (@min_margin_pct < 0 OR @min_margin_pct > 80) THROW 50337, N'Margen mínimo entre 0 y 80 %.', 1;

    IF @promo_id IS NULL
    BEGIN
        DECLARE @first BIGINT, @prefix NVARCHAR(30), @width TINYINT;
        EXEC app.usp_reserve_ids N'promo', 1, @first OUTPUT, @prefix OUTPUT, @width OUTPUT;
        SET @promo_id = app.fn_format_id(@prefix, @width, @first);
        INSERT INTO mkt.promotion (promo_id, promo_name, starts_at, ends_at, scope_type, scope_id, promo_type, discount_pct, discount_eur,
            channel, target_segment, store_id, combinable, basket_threshold_eur, min_margin_pct, related_campaign_id)
        VALUES (@promo_id, @promo_name, @starts_at, @ends_at, @scope_type, @scope_id, @promo_type, @discount_pct, @discount_eur,
            @channel, @target_segment, @store_id, @combinable, ISNULL(@basket_threshold_eur, 0), @min_margin_pct, @related_campaign_id);
    END
    ELSE
    BEGIN
        UPDATE mkt.promotion
           SET promo_name = @promo_name, starts_at = @starts_at, ends_at = @ends_at, scope_type = @scope_type, scope_id = @scope_id,
               promo_type = @promo_type, discount_pct = @discount_pct, discount_eur = @discount_eur, channel = @channel,
               target_segment = @target_segment, store_id = @store_id, combinable = @combinable,
               basket_threshold_eur = ISNULL(@basket_threshold_eur, 0), min_margin_pct = @min_margin_pct,
               related_campaign_id = @related_campaign_id
         WHERE promo_id = @promo_id;
        IF @@ROWCOUNT = 0 THROW 50338, N'La promoción no existe.', 1;
    END
    EXEC app.usp_audit @user_login, N'promotion_upsert', N'promotion', @promo_id, NULL;
    SELECT @promo_id AS promo_id;
END
GO

/* Recalcula la afinidad cliente-tienda con las compras de los últimos 12 meses.
   Los clientes sin compras en ese periodo conservan sus valores. */
CREATE OR ALTER PROCEDURE mkt.usp_affinity_recalculate @user_login NVARCHAR(100) = NULL
AS
BEGIN
    SET NOCOUNT ON;
    DECLARE @since DATETIME2(0) = DATEADD(MONTH, -12, SYSUTCDATETIME());
    WITH store_activity AS (
        SELECT t.customer_id, t.store_id, COUNT(*) AS visits, SUM(t.ticket_net_amount) AS spend
        FROM sales.pos_ticket t WHERE t.customer_id IS NOT NULL AND t.ticket_at >= @since GROUP BY t.customer_id, t.store_id),
    store_totals AS (
        SELECT customer_id, SUM(visits) AS visits, SUM(spend) AS spend,
               (SELECT TOP 1 s2.store_id FROM store_activity s2 WHERE s2.customer_id = s.customer_id ORDER BY s2.visits DESC, s2.spend DESC) AS top_store
        FROM store_activity s GROUP BY customer_id),
    online AS (
        SELECT customer_id, SUM(order_total) AS spend FROM sales.online_order
        WHERE customer_id IS NOT NULL AND ordered_at >= @since AND order_status <> N'Cancelado' GROUP BY customer_id),
    activity AS (
        SELECT ISNULL(s.customer_id, o.customer_id) AS customer_id, s.visits, s.spend AS store_spend, s.top_store, o.spend AS online_spend
        FROM store_totals s FULL OUTER JOIN online o ON o.customer_id = s.customer_id)
    MERGE mkt.customer_store_affinity AS t
    USING (SELECT a.*, c.city, c.province FROM activity a JOIN crm.customer c ON c.customer_id = a.customer_id) AS s
       ON t.customer_id = s.customer_id
    WHEN MATCHED THEN UPDATE SET
        preferred_store_id = ISNULL(s.top_store, t.preferred_store_id),
        store_visits_12m = ISNULL(s.visits, 0), store_spend_12m_eur = ISNULL(s.store_spend, 0),
        online_spend_12m_eur = ISNULL(s.online_spend, 0),
        click_collect_propensity = CASE WHEN ISNULL(s.visits, 0) > 0 AND ISNULL(s.online_spend, 0) > 0 THEN 0.7
                                        WHEN ISNULL(s.online_spend, 0) > 0 THEN 0.4 ELSE 0.2 END,
        visit_probability_30d = CAST(CASE WHEN ISNULL(s.visits, 0) >= 12 THEN 0.9 ELSE ISNULL(s.visits, 0) / 13.0 END AS DECIMAL(6,3)),
        recalculated_at = SYSUTCDATETIME()
    WHEN NOT MATCHED THEN INSERT (customer_id, preferred_store_id, store_visits_12m, store_spend_12m_eur, online_spend_12m_eur,
        click_collect_propensity, visit_probability_30d, local_cluster, locally_capturable, home_city, home_province, recalculated_at)
        VALUES (s.customer_id, s.top_store, ISNULL(s.visits, 0), ISNULL(s.store_spend, 0), ISNULL(s.online_spend, 0),
        CASE WHEN ISNULL(s.visits, 0) > 0 AND ISNULL(s.online_spend, 0) > 0 THEN 0.7 WHEN ISNULL(s.online_spend, 0) > 0 THEN 0.4 ELSE 0.2 END,
        CAST(CASE WHEN ISNULL(s.visits, 0) >= 12 THEN 0.9 ELSE ISNULL(s.visits, 0) / 13.0 END AS DECIMAL(6,3)),
        CASE WHEN s.top_store IS NULL THEN N'digital' ELSE N'urbano_proximo' END, CASE WHEN s.top_store IS NULL THEN 0 ELSE 1 END,
        s.city, s.province, SYSUTCDATETIME());
    DECLARE @rows INT = @@ROWCOUNT;
    EXEC app.usp_audit @user_login, N'affinity_recalculate', N'customer_store_affinity', NULL, NULL;
    SELECT @rows AS rows_merged;
END
GO

/* =========================== RR. HH. =========================== */

/* Valida los valores de catálogo de un empleado (departamento estándar, nivel, contrato, jornada). */
CREATE OR ALTER PROCEDURE hr.usp_validate_employee_values
    @department NVARCHAR(100), @level_name NVARCHAR(50), @contract_type NVARCHAR(50) = NULL, @work_schedule NVARCHAR(20) = NULL
AS
BEGIN
    SET NOCOUNT ON;
    IF @department IS NOT NULL AND NOT EXISTS (SELECT 1 FROM ref.department_map WHERE department_std = @department)
        THROW 50400, N'Departamento no válido: usa uno de ref.department_map.', 1;
    IF @level_name IS NOT NULL AND @level_name NOT IN (N'Junior', N'Semi Senior', N'Senior', N'Manager')
        THROW 50401, N'Nivel no válido (Junior, Semi Senior, Senior o Manager).', 1;
    IF @contract_type IS NOT NULL AND @contract_type NOT IN (N'Indefinido', N'Temporal', N'Fijo discontinuo')
        THROW 50402, N'Tipo de contrato no válido.', 1;
    IF @work_schedule IS NOT NULL AND @work_schedule NOT IN (N'Completa', N'Parcial')
        THROW 50403, N'Jornada no válida (Completa o Parcial).', 1;
END
GO

CREATE OR ALTER PROCEDURE hr.usp_record_movement
    @employee_id NVARCHAR(20), @moved_at DATE, @movement_type NVARCHAR(50),
    @department_from NVARCHAR(100) = NULL, @department_to NVARCHAR(100) = NULL,
    @level_from NVARCHAR(50) = NULL, @level_to NVARCHAR(50) = NULL,
    @reason NVARCHAR(200) = NULL, @hr_comment NVARCHAR(500) = NULL, @user_login NVARCHAR(100) = NULL
AS
BEGIN
    SET NOCOUNT ON;
    DECLARE @first BIGINT, @prefix NVARCHAR(30), @width TINYINT;
    EXEC app.usp_reserve_ids N'movement', 1, @first OUTPUT, @prefix OUTPUT, @width OUTPUT;
    INSERT INTO hr.employee_movement (movement_id, employee_id, moved_at, movement_type, department_from, department_to,
        level_from, level_to, reason, hr_comment, loaded_by, loaded_at)
    VALUES (app.fn_format_id(@prefix, @width, @first), @employee_id, @moved_at, @movement_type, @department_from, @department_to,
        @level_from, @level_to, @reason, @hr_comment, @user_login, CAST(SYSUTCDATETIME() AS DATE));
END
GO

/* Alta de empleado: ficha, movimiento de alta y, si trabaja en tienda, su asignación. */
CREATE OR ALTER PROCEDURE hr.usp_employee_hire
    @full_name NVARCHAR(200), @gender NVARCHAR(20) = NULL, @birth_date DATE = NULL, @hired_at DATE = NULL,
    @department NVARCHAR(100), @location NVARCHAR(100), @role_name NVARCHAR(100), @level_name NVARCHAR(50) = N'Junior',
    @contract_type NVARCHAR(50) = N'Indefinido', @work_schedule NVARCHAR(20) = N'Completa', @manager_id NVARCHAR(20) = NULL,
    @remote_days_week TINYINT = 0, @commute_km DECIMAL(9,1) = NULL, @store_id NVARCHAR(50) = NULL,
    @user_login NVARCHAR(100) = NULL
AS
BEGIN
    SET NOCOUNT ON;
    SET XACT_ABORT ON;
    SET @hired_at = ISNULL(@hired_at, CAST(SYSUTCDATETIME() AS DATE));
    IF LEN(ISNULL(@full_name, N'')) < 5 THROW 50404, N'Nombre y apellidos obligatorios.', 1;
    IF @gender IS NOT NULL AND @gender NOT IN (N'F', N'M', N'No declarado') THROW 50405, N'Género no válido.', 1;
    IF @birth_date IS NOT NULL AND DATEDIFF(YEAR, @birth_date, @hired_at) < 16 THROW 50406, N'La persona debe tener al menos 16 años.', 1;
    IF @hired_at > DATEADD(DAY, 90, CAST(SYSUTCDATETIME() AS DATE)) THROW 50407, N'La fecha de alta no puede ser tan lejana.', 1;
    IF @remote_days_week > 5 THROW 50408, N'Como mucho 5 días de teletrabajo.', 1;
    EXEC hr.usp_validate_employee_values @department, @level_name, @contract_type, @work_schedule;
    IF @manager_id IS NOT NULL AND NOT EXISTS (SELECT 1 FROM hr.employee WHERE employee_id = @manager_id AND employee_status = N'Activo')
        THROW 50409, N'El responsable no es un empleado activo.', 1;
    IF @store_id IS NOT NULL AND NOT EXISTS (SELECT 1 FROM store.store WHERE store_id = @store_id)
        THROW 50410, N'La tienda no existe.', 1;

    BEGIN TRAN;
    DECLARE @first BIGINT, @prefix NVARCHAR(30), @width TINYINT, @employee_id NVARCHAR(20);
    EXEC app.usp_reserve_ids N'employee', 1, @first OUTPUT, @prefix OUTPUT, @width OUTPUT;
    SET @employee_id = app.fn_format_id(@prefix, @width, @first);
    INSERT INTO hr.employee (employee_id, full_name, gender, birth_date, hired_at, employee_status, department, location, role_name,
        level_name, contract_type, work_schedule, manager_id, remote_days_week, commute_km, source_row_id)
    VALUES (@employee_id, @full_name, @gender, @birth_date, @hired_at, N'Activo', @department, @location, @role_name,
        @level_name, @contract_type, @work_schedule, @manager_id, @remote_days_week, @commute_km, N'WEB');
    EXEC hr.usp_record_movement @employee_id, @hired_at, N'Alta', NULL, @department, NULL, @level_name, N'Nueva contratación',
         N'Alta desde la web', @user_login;
    IF @store_id IS NOT NULL
        INSERT INTO xref.employee_store (employee_id, department, location, canonical_store_id, assignment_type, confidence)
        VALUES (@employee_id, @department, @location, @store_id, N'store_employee', N'alta');
    EXEC app.usp_audit @user_login, N'employee_hire', N'employee', @employee_id, @department;
    COMMIT;
    SELECT @employee_id AS employee_id;
END
GO

/* Promoción o movilidad interna: cambia departamento y/o nivel y deja el movimiento. */
CREATE OR ALTER PROCEDURE hr.usp_employee_move
    @employee_id NVARCHAR(20), @movement_type NVARCHAR(50), @department_to NVARCHAR(100) = NULL, @level_to NVARCHAR(50) = NULL,
    @role_to NVARCHAR(100) = NULL, @location_to NVARCHAR(100) = NULL, @manager_to NVARCHAR(20) = NULL,
    @reason NVARCHAR(200), @effective_date DATE = NULL, @user_login NVARCHAR(100) = NULL
AS
BEGIN
    SET NOCOUNT ON;
    SET XACT_ABORT ON;
    SET @effective_date = ISNULL(@effective_date, CAST(SYSUTCDATETIME() AS DATE));
    IF @movement_type NOT IN (N'Promoción', N'Movilidad interna') THROW 50411, N'Movimiento no válido (Promoción o Movilidad interna).', 1;
    IF @department_to IS NULL AND @level_to IS NULL AND @role_to IS NULL AND @location_to IS NULL AND @manager_to IS NULL
        THROW 50412, N'El movimiento no cambia nada.', 1;
    IF LEN(ISNULL(@reason, N'')) < 3 THROW 50413, N'Indica el motivo.', 1;
    EXEC hr.usp_validate_employee_values @department_to, @level_to;
    IF @manager_to = @employee_id THROW 50414, N'Un empleado no puede ser su propio responsable.', 1;
    IF @manager_to IS NOT NULL AND NOT EXISTS (SELECT 1 FROM hr.employee WHERE employee_id = @manager_to AND employee_status = N'Activo')
        THROW 50409, N'El responsable no es un empleado activo.', 1;

    BEGIN TRAN;
    DECLARE @dep NVARCHAR(100), @lvl NVARCHAR(50), @status NVARCHAR(20);
    SELECT @dep = department, @lvl = level_name, @status = employee_status FROM hr.employee WITH (UPDLOCK) WHERE employee_id = @employee_id;
    IF @status IS NULL THROW 50415, N'El empleado no existe.', 1;
    IF @status <> N'Activo' THROW 50416, N'El empleado está de baja.', 1;
    UPDATE hr.employee
       SET department = ISNULL(@department_to, department), level_name = ISNULL(@level_to, level_name),
           role_name = ISNULL(@role_to, role_name), location = ISNULL(@location_to, location),
           manager_id = ISNULL(@manager_to, manager_id), updated_at = SYSUTCDATETIME()
     WHERE employee_id = @employee_id;
    DECLARE @dep_to NVARCHAR(100) = ISNULL(@department_to, @dep), @lvl_to NVARCHAR(50) = ISNULL(@level_to, @lvl);
    EXEC hr.usp_record_movement @employee_id, @effective_date, @movement_type, @dep, @dep_to, @lvl, @lvl_to, @reason, NULL, @user_login;
    EXEC app.usp_audit @user_login, N'employee_move', N'employee', @employee_id, @movement_type;
    COMMIT;
END
GO

/* Revisión salarial: nueva nómina anual con el incremento respecto a la anterior. */
CREATE OR ALTER PROCEDURE hr.usp_salary_review
    @employee_id NVARCHAR(20), @base_salary_eur DECIMAL(12,2), @variable_salary_eur DECIMAL(12,2) = 0,
    @period_month CHAR(7) = NULL, @reason NVARCHAR(200) = N'Revisión salarial', @user_login NVARCHAR(100) = NULL
AS
BEGIN
    SET NOCOUNT ON;
    SET XACT_ABORT ON;
    SET @period_month = ISNULL(@period_month, CONVERT(CHAR(7), SYSUTCDATETIME(), 126));
    IF @period_month NOT LIKE N'[12][0-9][0-9][0-9]-[01][0-9]' THROW 50417, N'Periodo con formato AAAA-MM.', 1;
    IF @base_salary_eur < 8000 OR @base_salary_eur > 250000 THROW 50418, N'Salario base fuera de rango (8.000 a 250.000 € al año).', 1;
    IF @variable_salary_eur < 0 THROW 50419, N'El variable no puede ser negativo.', 1;
    IF NOT EXISTS (SELECT 1 FROM hr.employee WHERE employee_id = @employee_id AND employee_status = N'Activo')
        THROW 50416, N'El empleado no existe o está de baja.', 1;

    BEGIN TRAN;
    DECLARE @previous DECIMAL(12,2) = (SELECT TOP 1 base_salary_eur FROM hr.compensation
                                       WHERE employee_id = @employee_id ORDER BY period_month DESC, payroll_id DESC);
    DECLARE @increase DECIMAL(6,2) = CASE WHEN ISNULL(@previous, 0) = 0 THEN 0
                                          ELSE ROUND(100.0 * (@base_salary_eur - @previous) / @previous, 2) END;
    DECLARE @first BIGINT, @prefix NVARCHAR(30), @width TINYINT, @payroll_id NVARCHAR(20);
    EXEC app.usp_reserve_ids N'payroll', 1, @first OUTPUT, @prefix OUTPUT, @width OUTPUT;
    SET @payroll_id = app.fn_format_id(@prefix, @width, @first);
    INSERT INTO hr.compensation (payroll_id, employee_id, period_month, base_salary_eur, variable_salary_eur, increase_pct,
        source_system, loaded_at)
    VALUES (@payroll_id, @employee_id, @period_month, @base_salary_eur, @variable_salary_eur, @increase, N'Web RR. HH.',
        CAST(SYSUTCDATETIME() AS DATE));
    DECLARE @today DATE = CAST(SYSUTCDATETIME() AS DATE);
    EXEC hr.usp_record_movement @employee_id, @today, N'Revisión salarial', NULL, NULL, NULL, NULL, @reason, NULL, @user_login;
    EXEC app.usp_audit @user_login, N'salary_review', N'employee', @employee_id, @payroll_id;
    COMMIT;
    SELECT @payroll_id AS payroll_id, @previous AS previous_base_salary_eur, @increase AS increase_pct;
END
GO

/* Baja: cierra la ficha, deja el movimiento, encola la entrevista de salida para
   Cosmos DB y desactiva los usuarios de la web atados al empleado. */
CREATE OR ALTER PROCEDURE hr.usp_employee_terminate
    @employee_id NVARCHAR(20), @left_at DATE = NULL, @exit_type NVARCHAR(50), @exit_reason NVARCHAR(200),
    @interview_comment NVARCHAR(2000) = NULL, @recommend_1_10 TINYINT = NULL, @interview_channel NVARCHAR(50) = NULL,
    @interviewer NVARCHAR(100) = NULL, @user_login NVARCHAR(100) = NULL
AS
BEGIN
    SET NOCOUNT ON;
    SET XACT_ABORT ON;
    SET @left_at = ISNULL(@left_at, CAST(SYSUTCDATETIME() AS DATE));
    IF @exit_type NOT IN (N'Voluntaria', N'Involuntaria/fin contrato') THROW 50420, N'Tipo de salida no válido.', 1;
    IF LEN(ISNULL(@exit_reason, N'')) < 3 THROW 50421, N'Indica el motivo de salida.', 1;
    IF @recommend_1_10 IS NOT NULL AND @recommend_1_10 > 10 THROW 50422, N'La recomendación va de 0 a 10.', 1;

    BEGIN TRAN;
    DECLARE @hired DATE, @status NVARCHAR(20), @dep NVARCHAR(100), @lvl NVARCHAR(50);
    SELECT @hired = hired_at, @status = employee_status, @dep = department, @lvl = level_name
    FROM hr.employee WITH (UPDLOCK) WHERE employee_id = @employee_id;
    IF @status IS NULL THROW 50415, N'El empleado no existe.', 1;
    IF @status <> N'Activo' THROW 50416, N'El empleado ya está de baja.', 1;
    IF @left_at < @hired THROW 50423, N'La fecha de salida es anterior a la de alta.', 1;

    UPDATE hr.employee SET employee_status = N'Baja', left_at = @left_at, exit_type = @exit_type, exit_reason = @exit_reason,
           updated_at = SYSUTCDATETIME()
    WHERE employee_id = @employee_id;
    -- Sus colaboradores pasan a no tener responsable hasta que RR. HH. lo reasigne.
    UPDATE hr.employee SET manager_id = NULL, updated_at = SYSUTCDATETIME() WHERE manager_id = @employee_id;
    EXEC hr.usp_record_movement @employee_id, @left_at, N'Baja', @dep, NULL, @lvl, NULL, @exit_reason, NULL, @user_login;

    IF @interview_comment IS NOT NULL OR @recommend_1_10 IS NOT NULL
    BEGIN
        DECLARE @first BIGINT, @prefix NVARCHAR(30), @width TINYINT, @exit_id NVARCHAR(30);
        EXEC app.usp_reserve_ids N'exit', 1, @first OUTPUT, @prefix OUTPUT, @width OUTPUT;
        SET @exit_id = app.fn_format_id(@prefix, @width, @first);
        INSERT INTO app.outbox (container_name, document_json)
        SELECT N'entrevistas_salida', (SELECT @exit_id AS id, @employee_id AS pk, @exit_id AS exit_interview_id,
                @employee_id AS employee_id, CONVERT(NVARCHAR(10), @left_at, 126) AS fecha_salida,
                CONVERT(NVARCHAR(10), SYSUTCDATETIME(), 126) AS fecha_entrevista, @exit_type AS tipo_salida,
                @exit_reason AS motivo_salida_rrhh, @interview_comment AS comentario_salida,
                @recommend_1_10 AS recomendaria_empresa_1_10, @interview_channel AS canal_entrevista,
                @interviewer AS entrevistador, N'web' AS origen
               FOR JSON PATH, WITHOUT_ARRAY_WRAPPER, INCLUDE_NULL_VALUES);
    END

    UPDATE u SET is_active = 0 FROM app.app_user u
    WHERE EXISTS (SELECT 1 FROM app.user_scope s WHERE s.user_id = u.user_id AND s.scope_type = N'employee' AND s.scope_value = @employee_id);
    DELETE ss FROM app.user_session ss
    WHERE EXISTS (SELECT 1 FROM app.user_scope s WHERE s.user_id = ss.user_id AND s.scope_type = N'employee' AND s.scope_value = @employee_id);

    EXEC app.usp_audit @user_login, N'employee_terminate', N'employee', @employee_id, @exit_type;
    COMMIT;
END
GO

/* Días laborables (lunes a viernes) entre dos fechas, ambas incluidas. */
CREATE OR ALTER FUNCTION hr.fn_working_days (@start DATE, @end DATE)
RETURNS INT
AS
BEGIN
    DECLARE @days INT = DATEDIFF(DAY, @start, @end) + 1;
    DECLARE @weeks INT = @days / 7, @rest INT = @days % 7;
    -- 1 = lunes con independencia de SET DATEFIRST
    DECLARE @dow INT = (DATEDIFF(DAY, '19000101', @start) % 7) + 1;
    DECLARE @extra INT = 0, @i INT = 0;
    WHILE @i < @rest
    BEGIN
        IF ((@dow + @i - 1) % 7) + 1 <= 5 SET @extra += 1;
        SET @i += 1;
    END
    RETURN @weeks * 5 + @extra;
END
GO

CREATE OR ALTER PROCEDURE hr.usp_absence_register
    @employee_id NVARCHAR(20), @start_date DATE, @end_date DATE, @absence_type NVARCHAR(50),
    @justified NVARCHAR(20) = N'Pendiente', @notes NVARCHAR(300) = NULL, @user_login NVARCHAR(100) = NULL
AS
BEGIN
    SET NOCOUNT ON;
    IF @absence_type NOT IN (N'Enfermedad común', N'Permiso retribuido', N'Cuidado familiar', N'Accidente laboral',
                             N'Ausencia injustificada', N'Vacaciones')
        THROW 50430, N'Tipo de ausencia no válido.', 1;
    IF @end_date < @start_date THROW 50431, N'La ausencia termina antes de empezar.', 1;
    IF DATEDIFF(DAY, @start_date, @end_date) > 365 THROW 50432, N'Una ausencia no puede durar más de un año.', 1;
    IF @justified NOT IN (N'Sí', N'No', N'Pendiente') THROW 50433, N'Justificación no válida (Sí, No o Pendiente).', 1;
    IF NOT EXISTS (SELECT 1 FROM hr.employee WHERE employee_id = @employee_id AND employee_status = N'Activo')
        THROW 50416, N'El empleado no existe o está de baja.', 1;
    IF EXISTS (SELECT 1 FROM hr.absence WHERE employee_id = @employee_id AND start_date <= @end_date AND end_date >= @start_date)
        THROW 50434, N'Se solapa con otra ausencia registrada.', 1;
    DECLARE @first BIGINT, @prefix NVARCHAR(30), @width TINYINT, @absence_id NVARCHAR(20);
    EXEC app.usp_reserve_ids N'absence', 1, @first OUTPUT, @prefix OUTPUT, @width OUTPUT;
    SET @absence_id = app.fn_format_id(@prefix, @width, @first);
    INSERT INTO hr.absence (absence_id, employee_id, start_date, end_date, absence_type, working_days, justified, notes)
    VALUES (@absence_id, @employee_id, @start_date, @end_date, @absence_type, hr.fn_working_days(@start_date, @end_date),
        @justified, @notes);
    EXEC app.usp_audit @user_login, N'absence_register', N'absence', @absence_id, @employee_id;
    SELECT @absence_id AS absence_id, hr.fn_working_days(@start_date, @end_date) AS working_days;
END
GO

/* Solicitud de horas extra: queda pendiente del responsable del empleado. */
CREATE OR ALTER PROCEDURE hr.usp_overtime_request
    @employee_id NVARCHAR(20), @period_month CHAR(7), @hours DECIMAL(6,2), @reason NVARCHAR(100), @user_login NVARCHAR(100) = NULL
AS
BEGIN
    SET NOCOUNT ON;
    IF @period_month NOT LIKE N'[12][0-9][0-9][0-9]-[01][0-9]' THROW 50417, N'Periodo con formato AAAA-MM.', 1;
    IF @hours <= 0 OR @hours > 80 THROW 50435, N'Entre 0,5 y 80 horas al mes.', 1;
    IF @reason NOT IN (N'Inventario', N'Pico e-commerce', N'Cobertura de turnos', N'Proyecto interno', N'Campaña comercial')
        THROW 50436, N'Motivo no válido.', 1;
    DECLARE @dep NVARCHAR(100), @manager NVARCHAR(20);
    SELECT @dep = department, @manager = manager_id FROM hr.employee WHERE employee_id = @employee_id AND employee_status = N'Activo';
    IF @dep IS NULL THROW 50416, N'El empleado no existe o está de baja.', 1;
    DECLARE @first BIGINT, @prefix NVARCHAR(30), @width TINYINT, @overtime_id NVARCHAR(20);
    EXEC app.usp_reserve_ids N'overtime', 1, @first OUTPUT, @prefix OUTPUT, @width OUTPUT;
    SET @overtime_id = app.fn_format_id(@prefix, @width, @first);
    INSERT INTO hr.overtime (overtime_id, employee_id, period_month, department_reported, hours, reason, approval_status,
        approver_id, requested_at)
    VALUES (@overtime_id, @employee_id, @period_month, @dep, @hours, @reason, N'Pendiente', @manager, SYSUTCDATETIME());
    EXEC app.usp_audit @user_login, N'overtime_request', N'overtime', @overtime_id, @employee_id;
    SELECT @overtime_id AS overtime_id, @manager AS approver_id;
END
GO

/* Decisión sobre horas extra. Si llega @manager_id, solo puede decidir el
   responsable directo; sin él (rol RR. HH.), cualquiera pendiente. */
CREATE OR ALTER PROCEDURE hr.usp_overtime_decide
    @overtime_id NVARCHAR(20), @approve BIT, @manager_id NVARCHAR(20) = NULL, @user_login NVARCHAR(100) = NULL
AS
BEGIN
    SET NOCOUNT ON;
    DECLARE @status NVARCHAR(20), @employee NVARCHAR(20);
    SELECT @status = o.approval_status, @employee = o.employee_id FROM hr.overtime o WHERE o.overtime_id = @overtime_id;
    IF @status IS NULL THROW 50437, N'La solicitud no existe.', 1;
    IF @status <> N'Pendiente' THROW 50438, N'La solicitud ya está decidida.', 1;
    IF @manager_id IS NOT NULL AND NOT EXISTS (SELECT 1 FROM hr.employee WHERE employee_id = @employee AND manager_id = @manager_id)
        THROW 50439, N'Solo puede decidir el responsable directo del empleado.', 1;
    UPDATE hr.overtime
       SET approval_status = CASE WHEN @approve = 1 THEN N'Aprobada' ELSE N'Rechazada' END,
           approver_id = ISNULL(@manager_id, approver_id), decided_at = SYSUTCDATETIME()
     WHERE overtime_id = @overtime_id;
    EXEC app.usp_audit @user_login, N'overtime_decide', N'overtime', @overtime_id, @approve;
END
GO

CREATE OR ALTER PROCEDURE hr.usp_training_enroll
    @employee_id NVARCHAR(20), @course_id NVARCHAR(20), @start_date DATE, @end_date DATE, @planned_hours DECIMAL(6,1),
    @user_login NVARCHAR(100) = NULL
AS
BEGIN
    SET NOCOUNT ON;
    IF @end_date < @start_date THROW 50440, N'El curso termina antes de empezar.', 1;
    IF @planned_hours <= 0 OR @planned_hours > 200 THROW 50441, N'Horas planificadas entre 0,5 y 200.', 1;
    IF NOT EXISTS (SELECT 1 FROM hr.employee WHERE employee_id = @employee_id AND employee_status = N'Activo')
        THROW 50416, N'El empleado no existe o está de baja.', 1;
    -- Los datos del curso (nombre, categoría, proveedor y coste por hora) salen de la última edición registrada.
    DECLARE @name NVARCHAR(200), @category NVARCHAR(50), @provider NVARCHAR(100), @cost_hour DECIMAL(10,2);
    SELECT TOP 1 @name = course_name, @category = category, @provider = provider,
           @cost_hour = cost_eur / NULLIF(planned_hours, 0)
    FROM hr.training WHERE course_id = @course_id ORDER BY start_date DESC, training_id DESC;
    IF @name IS NULL THROW 50442, N'El curso no existe en el catálogo de formación.', 1;
    IF EXISTS (SELECT 1 FROM hr.training WHERE employee_id = @employee_id AND course_id = @course_id
               AND training_status IN (N'Inscrito', N'En curso'))
        THROW 50443, N'Ya está inscrito en ese curso.', 1;
    DECLARE @first BIGINT, @prefix NVARCHAR(30), @width TINYINT, @training_id NVARCHAR(20);
    EXEC app.usp_reserve_ids N'training', 1, @first OUTPUT, @prefix OUTPUT, @width OUTPUT;
    SET @training_id = app.fn_format_id(@prefix, @width, @first);
    INSERT INTO hr.training (training_id, employee_id, course_id, course_name, category, start_date, end_date, planned_hours,
        completed_hours, training_status, cost_eur, provider)
    VALUES (@training_id, @employee_id, @course_id, @name, @category, @start_date, @end_date, @planned_hours, 0, N'Inscrito',
        ROUND(ISNULL(@cost_hour, 0) * @planned_hours, 2), @provider);
    EXEC app.usp_audit @user_login, N'training_enroll', N'training', @training_id, @employee_id;
    SELECT @training_id AS training_id;
END
GO

CREATE OR ALTER PROCEDURE hr.usp_training_complete
    @training_id NVARCHAR(20), @completed_hours DECIMAL(6,1), @completed BIT = 1, @user_login NVARCHAR(100) = NULL
AS
BEGIN
    SET NOCOUNT ON;
    DECLARE @status NVARCHAR(30), @planned DECIMAL(6,1);
    SELECT @status = training_status, @planned = planned_hours FROM hr.training WHERE training_id = @training_id;
    IF @status IS NULL THROW 50444, N'La inscripción no existe.', 1;
    IF @status NOT IN (N'Inscrito', N'En curso') THROW 50445, N'La formación ya está cerrada.', 1;
    IF @completed_hours < 0 OR @completed_hours > @planned * 1.5 THROW 50446, N'Horas realizadas fuera de rango.', 1;
    UPDATE hr.training SET completed_hours = @completed_hours,
           training_status = CASE WHEN @completed = 1 THEN N'Completado' ELSE N'No completado' END
    WHERE training_id = @training_id;
    EXEC app.usp_audit @user_login, N'training_complete', N'training', @training_id, @completed;
END
GO

/* Evaluación anual: una por empleado y ciclo (se puede corregir mientras dure el ciclo). */
CREATE OR ALTER PROCEDURE hr.usp_review_upsert
    @employee_id NVARCHAR(20), @review_cycle CHAR(4), @overall_score DECIMAL(3,1), @objectives_pct DECIMAL(6,1) = NULL,
    @competencies_score DECIMAL(3,1) = NULL, @potential NVARCHAR(20) = NULL, @reviewer_id NVARCHAR(20) = NULL,
    @manager_comment NVARCHAR(500) = NULL, @user_login NVARCHAR(100) = NULL
AS
BEGIN
    SET NOCOUNT ON;
    IF @overall_score NOT BETWEEN 1 AND 5 OR (@competencies_score IS NOT NULL AND @competencies_score NOT BETWEEN 1 AND 5)
        THROW 50450, N'Las puntuaciones van de 1 a 5.', 1;
    IF @objectives_pct IS NOT NULL AND @objectives_pct NOT BETWEEN 0 AND 200 THROW 50451, N'Cumplimiento de objetivos entre 0 y 200 %.', 1;
    IF @potential IS NOT NULL AND @potential NOT IN (N'Bajo', N'Medio', N'Alto', N'Muy alto') THROW 50452, N'Potencial no válido.', 1;
    IF @review_cycle NOT LIKE N'20[0-9][0-9]' OR CAST(@review_cycle AS INT) > YEAR(SYSUTCDATETIME())
        THROW 50453, N'Ciclo de evaluación no válido.', 1;
    IF NOT EXISTS (SELECT 1 FROM hr.employee WHERE employee_id = @employee_id) THROW 50415, N'El empleado no existe.', 1;
    DECLARE @review_id NVARCHAR(20) = (SELECT review_id FROM hr.performance_review WHERE employee_id = @employee_id AND review_cycle = @review_cycle);
    IF @review_id IS NULL
    BEGIN
        DECLARE @first BIGINT, @prefix NVARCHAR(30), @width TINYINT;
        EXEC app.usp_reserve_ids N'review', 1, @first OUTPUT, @prefix OUTPUT, @width OUTPUT;
        SET @review_id = app.fn_format_id(@prefix, @width, @first);
        INSERT INTO hr.performance_review (review_id, employee_id, review_cycle, reviewed_at, overall_score, objectives_pct,
            competencies_score, potential, reviewer_id, manager_comment, source_system)
        VALUES (@review_id, @employee_id, @review_cycle, CAST(SYSUTCDATETIME() AS DATE), @overall_score, @objectives_pct,
            @competencies_score, @potential, @reviewer_id, @manager_comment, N'Web RR. HH.');
    END
    ELSE
        UPDATE hr.performance_review
           SET reviewed_at = CAST(SYSUTCDATETIME() AS DATE), overall_score = @overall_score, objectives_pct = @objectives_pct,
               competencies_score = @competencies_score, potential = @potential, reviewer_id = ISNULL(@reviewer_id, reviewer_id),
               manager_comment = @manager_comment
         WHERE review_id = @review_id;
    EXEC app.usp_audit @user_login, N'review_upsert', N'performance_review', @review_id, @employee_id;
    SELECT @review_id AS review_id;
END
GO

/* =========================== aplicación =========================== */

/* Vuelve a poner en cola los documentos del outbox que agotaron sus reintentos. */
CREATE OR ALTER PROCEDURE app.usp_outbox_retry @user_login NVARCHAR(100) = NULL
AS
BEGIN
    SET NOCOUNT ON;
    UPDATE app.outbox SET attempts = 0, last_error = NULL WHERE sent_at IS NULL AND attempts > 0;
    DECLARE @rows INT = @@ROWCOUNT;
    EXEC app.usp_audit @user_login, N'outbox_retry', N'outbox', NULL, @rows;
    SELECT @rows AS rows_reset;
END
GO
