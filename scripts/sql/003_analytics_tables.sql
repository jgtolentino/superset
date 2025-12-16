-- ============================================================================
-- Analytics & Sales Tables
-- Tables: cleaned_sales_data, video_game_sales, exported_stats, FCC 2018 Survey
-- ============================================================================

SET search_path TO examples, public;

-- ----------------------------------------------------------------------------
-- Cleaned Sales Data
-- ----------------------------------------------------------------------------
DROP TABLE IF EXISTS examples.cleaned_sales_data CASCADE;
CREATE TABLE examples.cleaned_sales_data (
    id SERIAL PRIMARY KEY,
    order_id VARCHAR(50),
    order_date DATE,
    ship_date DATE,
    ship_mode VARCHAR(50),
    customer_id VARCHAR(50),
    customer_name VARCHAR(200),
    segment VARCHAR(50), -- Consumer, Corporate, Home Office
    country VARCHAR(100),
    city VARCHAR(100),
    state VARCHAR(100),
    postal_code VARCHAR(20),
    region VARCHAR(50),
    product_id VARCHAR(50),
    category VARCHAR(100),
    sub_category VARCHAR(100),
    product_name VARCHAR(500),
    sales NUMERIC(12, 2),
    quantity INTEGER,
    discount NUMERIC(5, 2),
    profit NUMERIC(12, 2),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_sales_date ON examples.cleaned_sales_data(order_date);
CREATE INDEX idx_sales_customer ON examples.cleaned_sales_data(customer_id);
CREATE INDEX idx_sales_category ON examples.cleaned_sales_data(category);
CREATE INDEX idx_sales_region ON examples.cleaned_sales_data(region);

-- ----------------------------------------------------------------------------
-- Video Game Sales
-- ----------------------------------------------------------------------------
DROP TABLE IF EXISTS examples.video_game_sales CASCADE;
CREATE TABLE examples.video_game_sales (
    id SERIAL PRIMARY KEY,
    rank INTEGER,
    name VARCHAR(500) NOT NULL,
    platform VARCHAR(50),
    year INTEGER,
    genre VARCHAR(50),
    publisher VARCHAR(200),
    na_sales NUMERIC(10, 2), -- North America sales (millions)
    eu_sales NUMERIC(10, 2), -- Europe sales (millions)
    jp_sales NUMERIC(10, 2), -- Japan sales (millions)
    other_sales NUMERIC(10, 2), -- Other regions sales (millions)
    global_sales NUMERIC(10, 2) -- Total global sales (millions)
);

CREATE INDEX idx_vg_year ON examples.video_game_sales(year);
CREATE INDEX idx_vg_platform ON examples.video_game_sales(platform);
CREATE INDEX idx_vg_genre ON examples.video_game_sales(genre);
CREATE INDEX idx_vg_publisher ON examples.video_game_sales(publisher);

-- ----------------------------------------------------------------------------
-- Exported Stats (generic stats export table)
-- ----------------------------------------------------------------------------
DROP TABLE IF EXISTS examples.exported_stats CASCADE;
CREATE TABLE examples.exported_stats (
    id SERIAL PRIMARY KEY,
    stat_date DATE NOT NULL,
    metric_name VARCHAR(100) NOT NULL,
    metric_value NUMERIC(18, 4),
    dimension_1 VARCHAR(100),
    dimension_2 VARCHAR(100),
    dimension_3 VARCHAR(100),
    source VARCHAR(100),
    export_timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_stats_date ON examples.exported_stats(stat_date);
CREATE INDEX idx_stats_metric ON examples.exported_stats(metric_name);

-- ----------------------------------------------------------------------------
-- FCC 2018 Survey (Developer Survey Data)
-- ----------------------------------------------------------------------------
DROP TABLE IF EXISTS examples."FCC 2018 Survey" CASCADE;
CREATE TABLE examples."FCC 2018 Survey" (
    id SERIAL PRIMARY KEY,
    respondent_id INTEGER,
    age INTEGER,
    age_range VARCHAR(50),
    gender VARCHAR(50),
    country_citizen VARCHAR(100),
    country_live VARCHAR(100),
    employment_status VARCHAR(100),
    employment_field VARCHAR(200),
    school_degree VARCHAR(100),
    school_major VARCHAR(200),
    bootcamp_name VARCHAR(200),
    bootcamp_finished BOOLEAN,
    bootcamp_loan BOOLEAN,
    bootcamp_recommend BOOLEAN,
    job_role_interest VARCHAR(500),
    job_where_interest VARCHAR(200),
    job_apply_when VARCHAR(100),
    job_relocation BOOLEAN,
    learning_hours_per_week INTEGER,
    money_for_learning NUMERIC(10, 2),
    months_programming INTEGER,
    resources_used TEXT,
    podcast_listen TEXT,
    youtube_watch TEXT,
    income NUMERIC(12, 2),
    expected_earn_after INTEGER,
    survey_date DATE DEFAULT '2018-01-01'
);

CREATE INDEX idx_fcc_country ON examples."FCC 2018 Survey"(country_live);
CREATE INDEX idx_fcc_employment ON examples."FCC 2018 Survey"(employment_status);

-- ----------------------------------------------------------------------------
-- Unicode Test (for testing special characters)
-- ----------------------------------------------------------------------------
DROP TABLE IF EXISTS examples.unicode_test CASCADE;
CREATE TABLE examples.unicode_test (
    id SERIAL PRIMARY KEY,
    text_value TEXT,
    description VARCHAR(500),
    language VARCHAR(50),
    script_type VARCHAR(50),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
