create table if not exists practilizate_meta (
    key text primary key,
    value text not null
);

create table if not exists dim_fecha (
    date_id integer primary key,
    date date not null unique,
    year integer not null,
    month integer not null,
    day integer not null,
    weekday integer not null,
    is_weekend boolean not null
);

create table if not exists dim_empresa (
    company_id bigint primary key,
    name text not null,
    normalized_name text not null
);

create unique index if not exists ux_dim_empresa_normalized
    on dim_empresa (normalized_name);

create table if not exists dim_ubicacion (
    location_id bigint primary key,
    district text,
    province text,
    department text
);

create unique index if not exists ux_dim_ubicacion_key
    on dim_ubicacion (district, department);

create table if not exists dim_carrera (
    career_id bigint primary key,
    name text not null,
    normalized_name text not null
);

create unique index if not exists ux_dim_carrera_normalized
    on dim_carrera (normalized_name);

create table if not exists dim_habilidad (
    skill_id bigint primary key,
    name text not null,
    normalized_name text not null
);

create unique index if not exists ux_dim_habilidad_normalized
    on dim_habilidad (normalized_name);

create table if not exists dim_modalidad (
    modality_id bigint primary key,
    name text not null unique
);

create table if not exists dim_asistencia (
    attendance_id bigint primary key,
    name text not null unique
);

create table if not exists fact_ofertas (
    offer_id bigint primary key,
    title text not null,
    company_id bigint references dim_empresa (company_id),
    location_id bigint references dim_ubicacion (location_id),
    date_id integer references dim_fecha (date_id),
    modality_id bigint references dim_modalidad (modality_id),
    attendance_id bigint references dim_asistencia (attendance_id),
    salary_amount numeric(12, 2),
    salary_text text,
    published_at date,
    deadline_at date,
    status text not null,
    url text not null unique,
    quality_score numeric(5, 4) not null
);

create index if not exists ix_fact_ofertas_company on fact_ofertas (company_id);
create index if not exists ix_fact_ofertas_location on fact_ofertas (location_id);
create index if not exists ix_fact_ofertas_date on fact_ofertas (date_id);
create index if not exists ix_fact_ofertas_status on fact_ofertas (status);
create index if not exists ix_fact_ofertas_deadline on fact_ofertas (deadline_at);

create table if not exists bridge_oferta_carrera (
    offer_id bigint not null references fact_ofertas (offer_id) on delete cascade,
    career_id bigint not null references dim_carrera (career_id),
    primary key (offer_id, career_id)
);

create index if not exists ix_bridge_carrera_career
    on bridge_oferta_carrera (career_id);

create table if not exists bridge_oferta_habilidad (
    offer_id bigint not null references fact_ofertas (offer_id) on delete cascade,
    skill_id bigint not null references dim_habilidad (skill_id),
    primary key (offer_id, skill_id)
);

create index if not exists ix_bridge_habilidad_skill
    on bridge_oferta_habilidad (skill_id);

create or replace view v_dashboard_ofertas as
select
    f.offer_id,
    f.title,
    f.url,
    f.status,
    f.salary_amount,
    f.salary_text,
    f.published_at,
    f.deadline_at,
    f.quality_score,
    e.name as company,
    u.district,
    u.province,
    u.department,
    d.year as published_year,
    d.month as published_month,
    m.name as modality,
    a.name as attendance,
    (
        select string_agg(c.name, '; ' order by c.name)
        from bridge_oferta_carrera bc
        join dim_carrera c on c.career_id = bc.career_id
        where bc.offer_id = f.offer_id
    ) as careers,
    (
        select string_agg(h.name, '; ' order by h.name)
        from bridge_oferta_habilidad bh
        join dim_habilidad h on h.skill_id = bh.skill_id
        where bh.offer_id = f.offer_id
    ) as skills
from fact_ofertas f
left join dim_empresa e on e.company_id = f.company_id
left join dim_ubicacion u on u.location_id = f.location_id
left join dim_fecha d on d.date_id = f.date_id
left join dim_modalidad m on m.modality_id = f.modality_id
left join dim_asistencia a on a.attendance_id = f.attendance_id;

insert into practilizate_meta (key, value)
values ('schema_version', '1')
on conflict (key) do update set value = excluded.value;
