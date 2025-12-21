CREATE TABLE IF NOT EXISTS transaction_account_history (
    id SERIAL PRIMARY KEY,
    account_id INTEGER NOT NULL,
    changed_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    changed_by INTEGER,
    action VARCHAR(20) NOT NULL CHECK (action IN ('INSERT', 'UPDATE', 'DELETE')),
    old_data JSONB,
    new_data JSONB,
    CONSTRAINT transaction_account_history_account_id_fkey 
        FOREIGN KEY (account_id) 
        REFERENCES transaction_account(id) 
        ON DELETE CASCADE,
    CONSTRAINT transaction_account_history_changed_by_fkey 
        FOREIGN KEY (changed_by) 
        REFERENCES authapp_usermodel(id) 
        ON DELETE SET NULL
);

CREATE INDEX IF NOT EXISTS transaction_account_history_account_id_idx 
    ON transaction_account_history(account_id);
CREATE INDEX IF NOT EXISTS transaction_account_history_changed_at_idx 
    ON transaction_account_history(changed_at);

CREATE TABLE IF NOT EXISTS transaction_budget_history (
    id SERIAL PRIMARY KEY,
    budget_id INTEGER NOT NULL,
    changed_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    changed_by INTEGER,
    action VARCHAR(20) NOT NULL CHECK (action IN ('INSERT', 'UPDATE', 'DELETE')),
    old_data JSONB,
    new_data JSONB,
    CONSTRAINT transaction_budget_history_budget_id_fkey 
        FOREIGN KEY (budget_id) 
        REFERENCES transaction_budget(id) 
        ON DELETE CASCADE,
    CONSTRAINT transaction_budget_history_changed_by_fkey 
        FOREIGN KEY (changed_by) 
        REFERENCES authapp_usermodel(id) 
        ON DELETE SET NULL
);

CREATE INDEX IF NOT EXISTS transaction_budget_history_budget_id_idx 
    ON transaction_budget_history(budget_id);
CREATE INDEX IF NOT EXISTS transaction_budget_history_changed_at_idx 
    ON transaction_budget_history(changed_at);



-- Отчет по доходам и расходам по месяцам
CREATE OR REPLACE VIEW v_monthly_income_expense_report AS
SELECT 
    u.id AS user_id,
    u.email,
    DATE_TRUNC('month', t.date) AS month,
    COALESCE(SUM(CASE WHEN t.type = 'INCOME' THEN t.amount ELSE 0 END), 0) AS total_income,
    COALESCE(SUM(CASE WHEN t.type = 'OUTCOME' THEN t.amount ELSE 0 END), 0) AS total_expense,
    COALESCE(SUM(CASE WHEN t.type = 'INCOME' THEN t.amount ELSE 0 END), 0) - 
    COALESCE(SUM(CASE WHEN t.type = 'OUTCOME' THEN t.amount ELSE 0 END), 0) AS net_amount,
    COUNT(CASE WHEN t.type = 'INCOME' THEN 1 END) AS income_count,
    COUNT(CASE WHEN t.type = 'OUTCOME' THEN 1 END) AS expense_count
FROM authapp_usermodel u
LEFT JOIN transaction_transaction t ON u.id = t.user_id
GROUP BY u.id, u.email, DATE_TRUNC('month', t.date)
ORDER BY u.id, month DESC;


-- Отчет по категориям за период
CREATE OR REPLACE VIEW v_category_report AS
SELECT 
    u.id AS user_id,
    u.email,
    c.id AS category_id,
    c.name AS category_name,
    c.type AS category_type,
    DATE_TRUNC('month', t.date) AS month,
    COUNT(t.id) AS transaction_count,
    COALESCE(SUM(t.amount), 0) AS total_amount,
    COALESCE(AVG(t.amount), 0) AS avg_amount,
    COALESCE(MIN(t.amount), 0) AS min_amount,
    COALESCE(MAX(t.amount), 0) AS max_amount
FROM authapp_usermodel u
LEFT JOIN transaction_category c ON u.id = c.user_id OR c.is_system = TRUE
LEFT JOIN transaction_transaction t ON c.id = t.category_id AND u.id = t.user_id
GROUP BY u.id, u.email, c.id, c.name, c.type, DATE_TRUNC('month', t.date)
ORDER BY u.id, month DESC, total_amount DESC;


-- Отчет по счетам с балансами и статистикой
CREATE OR REPLACE VIEW v_account_balance_report AS
SELECT 
    a.id AS account_id,
    a.name AS account_name,
    a.account_type,
    a.currency,
    a.balance AS current_balance,
    a.initial_balance,
    u.id AS user_id,
    u.email,
    COALESCE(SUM(CASE WHEN t.type = 'INCOME' THEN t.amount ELSE 0 END), 0) AS total_income,
    COALESCE(SUM(CASE WHEN t.type = 'OUTCOME' THEN t.amount ELSE 0 END), 0) AS total_expense,
    COUNT(t.id) AS transaction_count,
    MIN(t.date) AS first_transaction_date,
    MAX(t.date) AS last_transaction_date
FROM transaction_account a
JOIN authapp_usermodel u ON a.user_id = u.id
LEFT JOIN transaction_transaction t ON a.id = t.account_id
WHERE a.is_active = TRUE
GROUP BY a.id, a.name, a.account_type, a.currency, a.balance, a.initial_balance, u.id, u.email
ORDER BY u.id, a.name;


-- Отчет по выполнению бюджетов
CREATE OR REPLACE VIEW v_budget_execution_report AS
SELECT 
    b.id AS budget_id,
    b.name AS budget_name,
    b.period_type,
    b.start_date,
    b.end_date,
    b.total_expense_limit,
    u.id AS user_id,
    u.email,
    COALESCE(SUM(CASE WHEN t.type = 'INCOME' THEN t.amount ELSE 0 END), 0) AS actual_income,
    COALESCE(SUM(CASE WHEN t.type = 'OUTCOME' THEN t.amount ELSE 0 END), 0) AS actual_expense,
    CASE 
        WHEN b.total_expense_limit IS NOT NULL 
        THEN b.total_expense_limit - COALESCE(SUM(CASE WHEN t.type = 'OUTCOME' THEN t.amount ELSE 0 END), 0)
        ELSE NULL 
    END AS expense_remaining,
    CASE 
        WHEN b.total_expense_limit IS NOT NULL 
        THEN ROUND(
            (COALESCE(SUM(CASE WHEN t.type = 'OUTCOME' THEN t.amount ELSE 0 END), 0) / b.total_expense_limit) * 100, 
            2
        )
        ELSE NULL 
    END AS expense_percentage_used
FROM transaction_budget b
JOIN authapp_usermodel u ON b.user_id = u.id
LEFT JOIN transaction_transaction t ON b.user_id = t.user_id 
    AND t.date BETWEEN b.start_date AND b.end_date
WHERE b.is_active = TRUE
GROUP BY b.id, b.name, b.period_type, b.start_date, b.end_date, 
         b.total_expense_limit, u.id, u.email
ORDER BY b.start_date DESC;


-- Создание транзакции с автоматическим обновлением баланса счета
CREATE OR REPLACE PROCEDURE sp_create_transaction_with_balance_update(
    p_user_id INTEGER,
    p_account_id INTEGER,
    p_category_id INTEGER,
    p_type VARCHAR(20),
    p_amount NUMERIC(16, 2),
    p_date DATE,
    p_description TEXT,
    OUT p_transaction_id INTEGER
)
LANGUAGE plpgsql
AS $$
DECLARE
    v_account_balance NUMERIC(16, 2);
BEGIN
    IF p_type NOT IN ('INCOME', 'OUTCOME') THEN
        RAISE EXCEPTION 'Invalid transaction type: %. Must be INCOME or OUTCOME', p_type;
    END IF;
    
    IF p_account_id IS NOT NULL THEN
        SELECT balance INTO v_account_balance
        FROM transaction_account
        WHERE id = p_account_id AND user_id = p_user_id;
        
        IF NOT FOUND THEN
            RAISE EXCEPTION 'Account not found or access denied';
        END IF;
    END IF;
    
    INSERT INTO transaction_transaction (
        user_id, account_id, category_id, type, amount, date, description
    ) VALUES (
        p_user_id, p_account_id, p_category_id, p_type, p_amount, p_date, p_description
    ) RETURNING id INTO p_transaction_id;
    
    IF p_account_id IS NOT NULL THEN
        IF p_type = 'INCOME' THEN
            UPDATE transaction_account
            SET balance = balance + p_amount,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = p_account_id;
        ELSIF p_type = 'OUTCOME' THEN
            UPDATE transaction_account
            SET balance = balance - p_amount,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = p_account_id;
        END IF;
    END IF;
    
    COMMIT;
END;
$$;

-- Закрытие бюджета
CREATE OR REPLACE PROCEDURE sp_close_budget(
    p_budget_id INTEGER
)
LANGUAGE plpgsql
AS $$
DECLARE
    v_is_active BOOLEAN;
BEGIN
    SELECT is_active INTO v_is_active
    FROM transaction_budget
    WHERE id = p_budget_id;
    
    IF NOT FOUND THEN
        RAISE EXCEPTION 'Budget not found: %', p_budget_id;
    END IF;
    
    IF NOT v_is_active THEN
        RAISE EXCEPTION 'Budget % is already closed', p_budget_id;
    END IF;
    
    UPDATE transaction_budget
    SET is_active = FALSE
    WHERE id = p_budget_id;
END;
$$;

-- Расчет баланса счета на определенную дату
CREATE OR REPLACE FUNCTION fn_get_account_balance_on_date(
    p_account_id INTEGER,
    p_date DATE DEFAULT CURRENT_DATE
)
RETURNS NUMERIC(16, 2)
LANGUAGE plpgsql
STABLE
AS $$
DECLARE
    v_balance NUMERIC(16, 2);
    v_initial_balance NUMERIC(16, 2);
    v_income NUMERIC(16, 2);
    v_expense NUMERIC(16, 2);
BEGIN
    SELECT initial_balance INTO v_initial_balance
    FROM transaction_account
    WHERE id = p_account_id;
    
    IF NOT FOUND THEN
        RAISE EXCEPTION 'Account not found: %', p_account_id;
    END IF;
    
    SELECT COALESCE(SUM(amount), 0) INTO v_income
    FROM transaction_transaction
    WHERE account_id = p_account_id
        AND type = 'INCOME'
        AND date <= p_date;
    
    SELECT COALESCE(SUM(amount), 0) INTO v_expense
    FROM transaction_transaction
    WHERE account_id = p_account_id
        AND type = 'OUTCOME'
        AND date <= p_date;
    
    v_balance := v_initial_balance + v_income - v_expense;
    
    RETURN v_balance;
END;
$$;

-- Проверка лимитов бюджета
CREATE OR REPLACE FUNCTION fn_check_budget_limits(
    p_budget_id INTEGER
)
RETURNS TABLE (
    category_id INTEGER,
    category_name VARCHAR(50),
    limit_amount NUMERIC(16, 2),
    spent_amount NUMERIC(16, 2),
    remaining_amount NUMERIC(16, 2),
    percentage_used NUMERIC(5, 2),
    is_exceeded BOOLEAN
)
LANGUAGE plpgsql
STABLE
AS $$
DECLARE
    v_budget RECORD;
BEGIN
    -- Получаем информацию о бюджете
    SELECT * INTO v_budget
    FROM transaction_budget
    WHERE id = p_budget_id;
    
    IF NOT FOUND THEN
        RAISE EXCEPTION 'Budget not found: %', p_budget_id;
    END IF;
    
    -- Возвращаем информацию о лимитах категорий
    RETURN QUERY
    SELECT 
        bcl.category_id::INTEGER,
        c.name AS category_name,
        bcl.limit_amount,
        COALESCE(SUM(CASE WHEN t.type = 'OUTCOME' THEN t.amount ELSE 0 END), 0) AS spent_amount,
        bcl.limit_amount - COALESCE(SUM(CASE WHEN t.type = 'OUTCOME' THEN t.amount ELSE 0 END), 0) AS remaining_amount,
        ROUND(
            (COALESCE(SUM(CASE WHEN t.type = 'OUTCOME' THEN t.amount ELSE 0 END), 0) / bcl.limit_amount) * 100, 
            2
        ) AS percentage_used,
        CASE 
            WHEN COALESCE(SUM(CASE WHEN t.type = 'OUTCOME' THEN t.amount ELSE 0 END), 0) > bcl.limit_amount 
            THEN TRUE 
            ELSE FALSE 
        END AS is_exceeded
    FROM transaction_budgetcategorylimit bcl
    JOIN transaction_category c ON bcl.category_id = c.id
    LEFT JOIN transaction_transaction t ON c.id = t.category_id
        AND t.user_id = v_budget.user_id
        AND t.date BETWEEN v_budget.start_date AND v_budget.end_date
    WHERE bcl.budget_id = p_budget_id
    GROUP BY bcl.category_id, c.name, bcl.limit_amount
    ORDER BY percentage_used DESC;
END;
$$;

-- Функция для логирования изменений счетов
CREATE OR REPLACE FUNCTION fn_log_account_changes()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
DECLARE
    v_changed_by INTEGER;
BEGIN
    v_changed_by := COALESCE(current_setting('app.current_user_id', TRUE)::INTEGER, 
                             COALESCE(NEW.user_id, OLD.user_id));
    
    IF TG_OP = 'INSERT' THEN
        INSERT INTO transaction_account_history (
            account_id, action, new_data, changed_by
        ) VALUES (
            NEW.id, 'INSERT', row_to_json(NEW), v_changed_by
        );
        RETURN NEW;
    ELSIF TG_OP = 'UPDATE' THEN
        INSERT INTO transaction_account_history (
            account_id, action, old_data, new_data, changed_by
        ) VALUES (
            NEW.id, 'UPDATE', row_to_json(OLD), row_to_json(NEW), v_changed_by
        );
        RETURN NEW;
    ELSIF TG_OP = 'DELETE' THEN
        INSERT INTO transaction_account_history (
            account_id, action, old_data, changed_by
        ) VALUES (
            OLD.id, 'DELETE', row_to_json(OLD), v_changed_by
        );
        RETURN OLD;
    END IF;
    RETURN NULL;
END;
$$;

DROP TRIGGER IF EXISTS trg_account_history ON transaction_account;
DROP TRIGGER IF EXISTS trg_account_history_insert_update ON transaction_account;
DROP TRIGGER IF EXISTS trg_account_history_delete ON transaction_account;

CREATE TRIGGER trg_account_history_insert_update
    AFTER INSERT OR UPDATE ON transaction_account
    FOR EACH ROW EXECUTE FUNCTION fn_log_account_changes();

CREATE TRIGGER trg_account_history_delete
    BEFORE DELETE ON transaction_account
    FOR EACH ROW EXECUTE FUNCTION fn_log_account_changes();

-- Функция для логирования изменений бюджетов
CREATE OR REPLACE FUNCTION fn_log_budget_changes()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
DECLARE
    v_changed_by INTEGER;
BEGIN
    v_changed_by := COALESCE(current_setting('app.current_user_id', TRUE)::INTEGER, 
                             COALESCE(NEW.user_id, OLD.user_id));
    
    IF TG_OP = 'INSERT' THEN
        INSERT INTO transaction_budget_history (
            budget_id, action, new_data, changed_by
        ) VALUES (
            NEW.id, 'INSERT', row_to_json(NEW), v_changed_by
        );
        RETURN NEW;
    ELSIF TG_OP = 'UPDATE' THEN
        INSERT INTO transaction_budget_history (
            budget_id, action, old_data, new_data, changed_by
        ) VALUES (
            NEW.id, 'UPDATE', row_to_json(OLD), row_to_json(NEW), v_changed_by
        );
        RETURN NEW;
    ELSIF TG_OP = 'DELETE' THEN
        INSERT INTO transaction_budget_history (
            budget_id, action, old_data, changed_by
        ) VALUES (
            OLD.id, 'DELETE', row_to_json(OLD), v_changed_by
        );
        RETURN OLD;
    END IF;
    RETURN NULL;
END;
$$;


DROP TRIGGER IF EXISTS trg_budget_history ON transaction_budget;
DROP TRIGGER IF EXISTS trg_budget_history_insert_update ON transaction_budget;
DROP TRIGGER IF EXISTS trg_budget_history_delete ON transaction_budget;

CREATE TRIGGER trg_budget_history_insert_update
    AFTER INSERT OR UPDATE ON transaction_budget
    FOR EACH ROW EXECUTE FUNCTION fn_log_budget_changes();
CREATE TRIGGER trg_budget_history_delete
    BEFORE DELETE ON transaction_budget
    FOR EACH ROW EXECUTE FUNCTION fn_log_budget_changes();

-- Создание ролей
DO $$
BEGIN
    -- Admin
    IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'admin_role') THEN
        CREATE ROLE admin_role;
    END IF;
    
    -- Operator
    IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'operator_role') THEN
        CREATE ROLE operator_role;
    END IF;
    
    -- Client
    IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'client_role') THEN
        CREATE ROLE client_role;
    END IF;
END
$$;

GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO admin_role;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO admin_role;
GRANT ALL PRIVILEGES ON ALL FUNCTIONS IN SCHEMA public TO admin_role;
GRANT ALL PRIVILEGES ON ALL PROCEDURES IN SCHEMA public TO admin_role;

GRANT SELECT, INSERT, UPDATE, DELETE ON transaction_transaction TO operator_role;
GRANT SELECT, INSERT, UPDATE, DELETE ON transaction_account TO operator_role;
GRANT SELECT, INSERT, UPDATE, DELETE ON transaction_category TO operator_role;
GRANT SELECT, INSERT, UPDATE, DELETE ON transaction_budget TO operator_role;
GRANT SELECT, INSERT, UPDATE, DELETE ON transaction_budgetcategorylimit TO operator_role;
GRANT SELECT, INSERT, UPDATE, DELETE ON transaction_recurringtransaction TO operator_role;
GRANT SELECT ON authapp_usermodel TO operator_role;
GRANT SELECT ON authapp_currency TO operator_role;
GRANT SELECT ON transaction_account_history TO operator_role;
GRANT SELECT ON transaction_budget_history TO operator_role;

GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO operator_role;

GRANT SELECT ON v_monthly_income_expense_report TO operator_role;
GRANT SELECT ON v_category_report TO operator_role;
GRANT SELECT ON v_account_balance_report TO operator_role;
GRANT SELECT ON v_budget_execution_report TO operator_role;

GRANT EXECUTE ON FUNCTION fn_get_account_balance_on_date TO operator_role;
GRANT EXECUTE ON FUNCTION fn_check_budget_limits TO operator_role;
GRANT EXECUTE ON PROCEDURE sp_create_transaction_with_balance_update TO operator_role;
GRANT EXECUTE ON PROCEDURE sp_close_budget TO operator_role;

GRANT SELECT ON transaction_transaction TO client_role;
GRANT SELECT ON transaction_account TO client_role;
GRANT SELECT ON transaction_category TO client_role;
GRANT SELECT ON transaction_budget TO client_role;
GRANT SELECT ON transaction_budgetcategorylimit TO client_role;
GRANT SELECT ON transaction_recurringtransaction TO client_role;
GRANT SELECT ON authapp_currency TO client_role;

GRANT SELECT ON v_monthly_income_expense_report TO client_role;
GRANT SELECT ON v_category_report TO client_role;
GRANT SELECT ON v_account_balance_report TO client_role;
GRANT SELECT ON v_budget_execution_report TO client_role;

GRANT EXECUTE ON FUNCTION fn_get_account_balance_on_date TO client_role;
GRANT EXECUTE ON FUNCTION fn_check_budget_limits TO client_role;
