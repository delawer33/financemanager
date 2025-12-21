-- Группы пользователей
create table if not exists user_group (
    id serial primary key,
    name varchar(150) not null unique
);

-- Типы контента
create table if not exists content_type (
    id serial primary key,
    app_label varchar(100) not null,
    model varchar(100) not null,
    unique(app_label, model)
);

-- Разрешения
create table if not exists permission (
    id serial primary key,
    name varchar(255) not null,
    content_type_id integer not null,
    codename varchar(100) not null,
    foreign key (content_type_id) references content_type(id) on delete cascade,
    unique(content_type_id, codename)
);

-- Таблица связи групп и разрешений
create table if not exists group_permissions (
    id serial primary key,
    group_id integer not null,
    permission_id integer not null,
    foreign key (group_id) references user_group(id) on delete cascade,
    foreign key (permission_id) references permission(id) on delete cascade,
    unique(group_id, permission_id)
);

-- Валюты
create table if not exists currency (
    id serial primary key,
    name varchar(50) not null,
    symbol varchar(3) not null
);

-- Пользователь
create table if not exists "user" (
    id serial primary key,
    password varchar(128) not null,
    last_login timestamp with time zone,
    is_superuser boolean not null default false,
    email varchar(255) not null unique,
    firstname varchar(50),
    lastname varchar(50),
    is_admin boolean not null default false,
    is_active boolean not null default true,
    currency_id integer,
    foreign key (currency_id) references currency(id) on delete set null
);

-- Индекс для email
create index if not exists user_email_idx on "user"(email);

-- Таблица связи пользователей и групп
create table if not exists user_groups (
    id serial primary key,
    user_id integer not null,
    group_id integer not null,
    foreign key (user_id) references "user"(id) on delete cascade,
    foreign key (group_id) references user_group(id) on delete cascade,
    unique(user_id, group_id)
);

-- Таблица связи пользователей и разрешений
create table if not exists user_permissions (
    id serial primary key,
    user_id integer not null,
    permission_id integer not null,
    foreign key (user_id) references "user"(id) on delete cascade,
    foreign key (permission_id) references permission(id) on delete cascade,
    unique(user_id, permission_id)
);

-- TRASNSACTIONS

-- Категории
create table if not exists category (
    id serial primary key,
    name varchar(50) not null,
    type varchar(20) not null default 'OUTCOME',
    is_system boolean not null default false,
    user_id integer,
    check (type in ('INCOME', 'OUTCOME')),
    foreign key (user_id) references "user"(id) on delete cascade,
    unique(name, user_id)
);

-- Счет
create table if not exists account (
    id serial primary key,
    name varchar(100) not null,
    account_type varchar(20) not null,
    balance numeric(16, 2) not null default 0,
    initial_balance numeric(16, 2) not null default 0,
    currency varchar(3) not null default 'USD',
    is_active boolean not null default true,
    created_at timestamp with time zone not null default current_timestamp,
    updated_at timestamp with time zone not null default current_timestamp,
    user_id integer not null,
    check (account_type in ('BANK', 'CASH', 'CREDIT_CARD', 'INVESTMENT', 'SAVINGS', 'WALLET')),
    foreign key (user_id) references "user"(id) on delete cascade,
    unique(name, user_id)
);

-- Индекс для счетов по имени
create index if not exists account_name_idx on account(name);

-- Транзакции
create table if not exists transaction (
    id serial primary key,
    type varchar(20) not null default 'OUTCOME',
    amount numeric(16, 2) not null,
    date date not null default current_date,
    description text,
    category_id integer,
    user_id integer,
    account_id integer,
    check (type in ('INCOME', 'OUTCOME')),
    foreign key (category_id) references category(id) on delete cascade,
    foreign key (user_id) references "user"(id) on delete cascade,
    foreign key (account_id) references account(id) on delete cascade
);

-- Индексы для транзакций
create index if not exists transaction_user_id_idx on transaction(user_id);
create index if not exists transaction_category_id_idx on transaction(category_id);
create index if not exists transaction_account_id_idx on transaction(account_id);
create index if not exists transaction_date_idx on transaction(date);

-- Повторяющиеся транзакции транзакций
create table if not exists recurring_transaction (
    id serial primary key,
    amount numeric(16, 2) not null,
    type varchar(20) not null default 'OUTCOME',
    description text,
    start_date date not null default current_date,
    end_date date,
    frequency varchar(10) not null default 'monthly',
    category_id integer,
    user_id integer not null,
    account_id integer,
    check (type in ('INCOME', 'OUTCOME')),
    check (frequency in ('daily', 'weekly', 'monthly', 'yearly')),
    foreign key (category_id) references category(id) on delete set null,
    foreign key (user_id) references "user"(id) on delete cascade,
    foreign key (account_id) references account(id) on delete cascade
);

-- Индексы для повторяющихся транзакций
create index if not exists recurring_transaction_user_id_idx on recurring_transaction(user_id);
create index if not exists recurring_transaction_category_id_idx on recurring_transaction(category_id);
create index if not exists recurring_transaction_account_id_idx on recurring_transaction(account_id);

-- Бюджет
create table if not exists budget (
    id serial primary key,
    name varchar(100) not null,
    period_type varchar(20) not null,
    start_date date not null,
    end_date date not null,
    total_expense_limit numeric(16, 2),
    is_active boolean not null default true,
    created_at timestamp with time zone not null default current_timestamp,
    user_id integer not null,
    check (period_type in ('MONTHLY', 'QUARTERLY', 'YEARLY', 'CUSTOM')),
    check (end_date > start_date),
    foreign key (user_id) references "user"(id) on delete cascade
);

-- Индекс для бюджета по дате начала
create index if not exists budget_start_date_idx on budget(start_date desc);
create index if not exists budget_user_id_idx on budget(user_id);

-- Лимиты категорий в бюджетах
create table if not exists budget_category_limit (
    id serial primary key,
    limit_amount numeric(16, 2) not null,
    budget_id integer not null,
    category_id integer not null,
    foreign key (budget_id) references budget(id) on delete cascade,
    foreign key (category_id) references category(id) on delete cascade,
    unique(budget_id, category_id)
);

-- Вставка начальных данных

-- Инициализация валют
insert into currency (name, symbol) 
values 
    ('US Dollar', 'USD'),
    ('Euro', 'EUR'),
    ('Russian Ruble', 'RUB'),
    ('British Pound', 'GBP'),
    ('Japanese Yen', 'JPY'),
    ('Chinese Yuan', 'CNY')
on conflict do nothing;




-- Таблицы истории изменений

-- История изменений счетов
create table if not exists account_history (
    id serial primary key,
    account_id integer not null,
    changed_at timestamp with time zone not null default current_timestamp,
    changed_by integer,
    action varchar(20) not null check (action in ('insert', 'update', 'delete')),
    old_data jsonb,
    new_data jsonb,
    foreign key (account_id) references account(id) on delete cascade,
    foreign key (changed_by) references "user"(id) on delete set null
);

create index if not exists account_history_account_id_idx 
    on account_history(account_id);
create index if not exists account_history_changed_at_idx 
    on account_history(changed_at);

-- История изменений бюджетов
create table if not exists budget_history (
    id serial primary key,
    budget_id integer not null,
    changed_at timestamp with time zone not null default current_timestamp,
    changed_by integer,
    action varchar(20) not null check (action in ('insert', 'update', 'delete')),
    old_data jsonb,
    new_data jsonb,
    foreign key (budget_id) references budget(id) on delete cascade,
    foreign key (changed_by) references "user"(id) on delete set null
);

create index if not exists budget_history_budget_id_idx 
    on budget_history(budget_id);
create index if not exists budget_history_changed_at_idx 
    on budget_history(changed_at);



-- VIEWS

-- Отчет по доходам и расходам по месяцам
create or replace view v_monthly_income_expense_report as
select 
    u.id as user_id,
    u.email,
    date_trunc('month', t.date) as month,
    coalesce(sum(case when t.type = 'INCOME' then t.amount else 0 end), 0) as total_income,
    coalesce(sum(case when t.type = 'OUTCOME' then t.amount else 0 end), 0) as total_expense,
    coalesce(sum(case when t.type = 'INCOME' then t.amount else 0 end), 0) - 
    coalesce(sum(case when t.type = 'OUTCOME' then t.amount else 0 end), 0) as net_amount,
    count(case when t.type = 'INCOME' then 1 end) as income_count,
    count(case when t.type = 'OUTCOME' then 1 end) as expense_count
from "user" u
left join transaction t on u.id = t.user_id
group by u.id, u.email, date_trunc('month', t.date)
order by u.id, month desc;


-- Отчет по категориям за период
create or replace view v_category_report as
select 
    u.id as user_id,
    u.email,
    c.id as category_id,
    c.name as category_name,
    c.type as category_type,
    date_trunc('month', t.date) as month,
    count(t.id) as transaction_count,
    coalesce(sum(t.amount), 0) as total_amount,
    coalesce(avg(t.amount), 0) as avg_amount,
    coalesce(min(t.amount), 0) as min_amount,
    coalesce(max(t.amount), 0) as max_amount
from "user" u
left join category c on u.id = c.user_id or c.is_system = true
left join transaction t on c.id = t.category_id and u.id = t.user_id
group by u.id, u.email, c.id, c.name, c.type, date_trunc('month', t.date)
order by u.id, month desc, total_amount desc;


-- Отчет по счетам с балансами и статистикой
create or replace view v_account_balance_report as
select 
    a.id as account_id,
    a.name as account_name,
    a.account_type,
    a.currency,
    a.balance as current_balance,
    a.initial_balance,
    u.id as user_id,
    u.email,
    coalesce(sum(case when t.type = 'INCOME' then t.amount else 0 end), 0) as total_income,
    coalesce(sum(case when t.type = 'OUTCOME' then t.amount else 0 end), 0) as total_expense,
    count(t.id) as transaction_count,
    min(t.date) as first_transaction_date,
    max(t.date) as last_transaction_date
from account a
join "user" u on a.user_id = u.id
left join transaction t on a.id = t.account_id
where a.is_active = true
group by a.id, a.name, a.account_type, a.currency, a.balance, a.initial_balance, u.id, u.email
order by u.id, a.name;


-- Отчет по исполнению бюджета
create or replace view v_budget_execution_report as
select 
    b.id as budget_id,
    b.name as budget_name,
    b.period_type,
    b.start_date,
    b.end_date,
    b.total_expense_limit,
    u.id as user_id,
    u.email,
    coalesce(sum(case when t.type = 'INCOME' then t.amount else 0 end), 0) as actual_income,
    coalesce(sum(case when t.type = 'OUTCOME' then t.amount else 0 end), 0) as actual_expense,
    case 
        when b.total_expense_limit is not null 
        then b.total_expense_limit - coalesce(sum(case when t.type = 'OUTCOME' then t.amount else 0 end), 0)
        else null 
    end as expense_remaining,
    case 
        when b.total_expense_limit is not null 
        then round(
            (coalesce(sum(case when t.type = 'OUTCOME' then t.amount else 0 end), 0) / b.total_expense_limit) * 100, 
            2
        )
        else null 
    end as expense_percentage_used
from budget b
join "user" u on b.user_id = u.id
left join transaction t on b.user_id = t.user_id 
    and t.date between b.start_date and b.end_date
where b.is_active = true
group by b.id, b.name, b.period_type, b.start_date, b.end_date, 
         b.total_expense_limit, u.id, u.email
order by b.start_date desc;



-- ПРОЦЕДУРЫ

-- Создание транзакции с автоматическим обновлением баланса счета
create or replace procedure sp_create_transaction_with_balance_update(
    p_user_id integer,
    p_account_id integer,
    p_category_id integer,
    p_type varchar(20),
    p_amount numeric(16, 2),
    p_date date,
    p_description text,
    out p_transaction_id integer
)
language plpgsql
as $$
declare
    v_account_balance numeric(16, 2);
begin
    if p_type not in ('INCOME', 'OUTCOME') then
        raise exception 'Invalid transaction type: %. Must be INCOME or OUTCOME', p_type;
    end if;
    
    if p_account_id is not null then
        select balance into v_account_balance
        from account
        where id = p_account_id and user_id = p_user_id;
        
        if not found then
            raise exception 'Account not found or access denied';
        end if;
    end if;
    
    insert into transaction (
        user_id, account_id, category_id, type, amount, date, description
    ) values (
        p_user_id, p_account_id, p_category_id, p_type, p_amount, p_date, p_description
    ) returning id into p_transaction_id;
    
    if p_account_id is not null then
        if p_type = 'INCOME' then
            update account
            set balance = balance + p_amount,
                updated_at = current_timestamp
            where id = p_account_id;
        elsif p_type = 'OUTCOME' then
            update account
            set balance = balance - p_amount,
                updated_at = current_timestamp
            where id = p_account_id;
        end if;
    end if;
    
    commit;
end;
$$;

-- Закрытие бюджета
create or replace procedure sp_close_budget(
    p_budget_id integer
)
language plpgsql
as $$
declare
    v_is_active boolean;
begin
    select is_active into v_is_active
    from budget
    where id = p_budget_id;
    
    if not FOUND then
        raise exception 'Budget not found: %', p_budget_id;
    end if;
    
    if not v_is_active then
        raise exception 'Budget % is already closed', p_budget_id;
    end if;
    
    update budget
    set is_active = false
    where id = p_budget_id;
end;
$$;



-- ФУНКЦИИ

-- Расчет баланса счета на определенную дату
create or replace function fn_get_account_balance_on_date(
    p_account_id integer,
    p_date date default current_date
)
returns numeric(16, 2)
language plpgsql
stable
as $$
declare
    v_balance numeric(16, 2);
    v_initial_balance numeric(16, 2);
    v_income numeric(16, 2);
    v_expense numeric(16, 2);
begin
    select initial_balance into v_initial_balance
    from account
    where id = p_account_id;
    
    if not FOUND then
        raise exception 'Account not found: %', p_account_id;
    end if;
    
    select coalesce(sum(amount), 0) into v_income
    from transaction
    where account_id = p_account_id
        and type = 'INCOME'
        and date <= p_date;
    
    select coalesce(sum(amount), 0) into v_expense
    from transaction
    where account_id = p_account_id
        and type = 'OUTCOME'
        and date <= p_date;
    
    v_balance := v_initial_balance + v_income - v_expense;
    
    return v_balance;
end;
$$;


-- Проверка лимитов бюджета по категориям
create or replace function fn_check_budget_limits(
    p_budget_id integer
)
returns table (
    category_id integer,
    category_name varchar(50),
    limit_amount numeric(16, 2),
    spent_amount numeric(16, 2),
    remaining_amount numeric(16, 2),
    percentage_used numeric(5, 2),
    is_exceeded boolean
)
language plpgsql
stable
as $$
declare
    v_budget record;
begin
    select * into v_budget
    from budget
    where id = p_budget_id;
    
    if not FOUND then
        raise exception 'Budget not found: %', p_budget_id;
    end if;
    
    return query
    select 
        bcl.category_id::integer,
        c.name as category_name,
        bcl.limit_amount,
        coalesce(sum(case when t.type = 'OUTCOME' then t.amount else 0 end), 0) as spent_amount,
        bcl.limit_amount - coalesce(sum(case when t.type = 'OUTCOME' then t.amount else 0 end), 0) as remaining_amount,
        round(
            (coalesce(sum(case when t.type = 'OUTCOME' then t.amount else 0 end), 0) / bcl.limit_amount) * 100, 
            2
        ) as percentage_used,
        case 
            when coalesce(sum(case when t.type = 'OUTCOME' then t.amount else 0 end), 0) > bcl.limit_amount 
            then true 
            else false 
        end as is_exceeded
    from budget_category_limit bcl
    join category c on bcl.category_id = c.id
    left join transaction t on c.id = t.category_id
        and t.user_id = v_budget.user_id
        and t.date between v_budget.start_date and v_budget.end_date
    where bcl.budget_id = p_budget_id
    group by bcl.category_id, c.name, bcl.limit_amount
    order by percentage_used desc;
end;
$$;



-- Триггеры

-- Функция для логирования изменений счетов
create or replace function fn_log_account_changes()
returns trigger
language plpgsql
as $$
declare
    v_changed_by integer;
begin
    v_changed_by := new.user_id;
    
    if tg_op = 'insert' then
        insert into account_history (
            account_id, action, new_data, changed_by
        ) values (
            new.id, 'insert', row_to_json(new), v_changed_by
        );
        return new;
    elsif tg_op = 'update' then
        insert into account_history (
            account_id, action, old_data, new_data, changed_by
        ) values (
            new.id, 'update', row_to_json(old), row_to_json(new), v_changed_by
        );
        return new;
    elsif tg_op = 'delete' then
        insert into account_history (
            account_id, action, old_data, changed_by
        ) values (
            old.id, 'delete', row_to_json(old), v_changed_by
        );
        return old;
    end if;
    return null;
end;
$$;

-- Триггеры для счетов
drop trigger if exists trg_account_history on account;
drop trigger if exists trg_account_history_insert_update on account;
drop trigger if exists trg_account_history_delete on account;

create trigger trg_account_history_insert_update
    after insert or update on account
    for each row execute function fn_log_account_changes();
create trigger trg_account_history_delete
    before delete on account
    for each row execute function fn_log_account_changes();

-- Функция для логирования изменений бюджетов
create or replace function fn_log_budget_changes()
returns trigger
language plpgsql
as $$
declare
    v_changed_by integer;
begin
    v_changed_by := coalesce(new.user_id, old.user_id);
    
    if tg_op = 'insert' then
        insert into budget_history (
            budget_id, action, new_data, changed_by
        ) values (
            new.id, 'insert', row_to_json(new), v_changed_by
        );
        return new;
    elsif tg_op = 'update' then
        insert into budget_history (
            budget_id, action, old_data, new_data, changed_by
        ) values (
            new.id, 'update', row_to_json(old), row_to_json(new), v_changed_by
        );
        return new;
    elsif tg_op = 'delete' then
        insert into budget_history (
            budget_id, action, old_data, changed_by
        ) values (
            old.id, 'delete', row_to_json(old), v_changed_by
        );
        return old;
    end if;
    return null;
end;
$$;
-- TODO: id changer
-- Триггеры для бюджетов
drop trigger if exists trg_budget_history on budget;
drop trigger if exists trg_budget_history_insert_update on budget;
drop trigger if exists trg_budget_history_delete on budget;

create trigger trg_budget_history_insert_update
    after insert or update on budget
    for each row execute function fn_log_budget_changes();
create trigger trg_budget_history_delete
    before delete on budget
    for each row execute function fn_log_budget_changes();


-- РОЛИ И РАЗРЕШЕНИЯ


-- Создание ролей
do $$
begin
    -- Админ
    if not exists (select from pg_roles where rolname = 'admin_role') then
        create role admin_role;
    end if;
    
    -- Оператор
    if not exists (select from pg_roles where rolname = 'operator_role') then
        create role operator_role;
    end if;
    
    -- Клиент
    if not exists (select from pg_roles where rolname = 'client_role') then
        create role client_role;
    end if;
end
$$;

-- Права для администратора (полный доступ ко всем таблицам)
grant all privileges on all tables in schema public to admin_role;
grant all privileges on all sequences in schema public to admin_role;
grant all privileges on all functions in schema public to admin_role;
grant all privileges on all procedures in schema public to admin_role;

-- Права для оператора (доступ к транзакциям, счетам, категориям, но не к пользователям)
grant select, insert, update, delete on transaction to operator_role;
grant select, insert, update, delete on account to operator_role;
grant select, insert, update, delete on category to operator_role;
grant select, insert, update, delete on budget to operator_role;
grant select, insert, update, delete on budget_category_limit to operator_role;
grant select, insert, update, delete on recurring_transaction to operator_role;
grant select on "user" to operator_role;
grant select on currency to operator_role;
grant select on account_history to operator_role;
grant select on budget_history to operator_role;

-- Права на представления для оператора
grant select on v_monthly_income_expense_report to operator_role;
grant select on v_category_report to operator_role;
grant select on v_account_balance_report to operator_role;
grant select on v_budget_execution_report to operator_role;

-- Права на функции и процедуры для оператора
grant execute on function fn_get_account_balance_on_date to operator_role;
grant execute on function fn_check_budget_limits to operator_role;
grant execute on procedure sp_create_transaction_with_balance_update to operator_role;
grant execute on procedure sp_close_budget to operator_role;

-- Права для клиента (только чтение)
grant select on transaction to client_role;
grant select on account to client_role;
grant select on category to client_role;
grant select on budget to client_role;
grant select on budget_category_limit to client_role;
grant select on recurring_transaction to client_role;
grant select on currency to client_role;

-- Права на представления для клиента
grant select on v_monthly_income_expense_report to client_role;
grant select on v_category_report to client_role;
grant select on v_account_balance_report to client_role;
grant select on v_budget_execution_report to client_role;

-- Права на функции для клиента (только чтение)
grant execute on function fn_get_account_balance_on_date to client_role;
grant execute on function fn_check_budget_limits to client_role;
