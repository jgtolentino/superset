-- ============================================================================
-- Geographic & Demographic Tables
-- Tables: flights, birth_names, birth_france_by_region, long_lat,
--         bart_lines, sf_population_polygons, covid_vaccines, wb_health_population
-- ============================================================================

SET search_path TO examples, public;

-- ----------------------------------------------------------------------------
-- Flights (air traffic data)
-- ----------------------------------------------------------------------------
DROP TABLE IF EXISTS examples.flights CASCADE;
CREATE TABLE examples.flights (
    id SERIAL PRIMARY KEY,
    flight_date DATE,
    dep_time INTEGER, -- departure time HHMM
    arr_time INTEGER, -- arrival time HHMM
    carrier VARCHAR(10),
    flight_num INTEGER,
    origin VARCHAR(10),
    origin_city VARCHAR(100),
    origin_state VARCHAR(50),
    dest VARCHAR(10),
    dest_city VARCHAR(100),
    dest_state VARCHAR(50),
    distance INTEGER,
    dep_delay NUMERIC(8, 2),
    arr_delay NUMERIC(8, 2),
    cancelled BOOLEAN DEFAULT FALSE,
    diverted BOOLEAN DEFAULT FALSE,
    air_time INTEGER,
    weather_delay NUMERIC(8, 2),
    carrier_delay NUMERIC(8, 2),
    nas_delay NUMERIC(8, 2),
    security_delay NUMERIC(8, 2),
    late_aircraft_delay NUMERIC(8, 2)
);

CREATE INDEX idx_flights_date ON examples.flights(flight_date);
CREATE INDEX idx_flights_carrier ON examples.flights(carrier);
CREATE INDEX idx_flights_origin ON examples.flights(origin);
CREATE INDEX idx_flights_dest ON examples.flights(dest);

-- ----------------------------------------------------------------------------
-- Birth Names (US baby names data)
-- ----------------------------------------------------------------------------
DROP TABLE IF EXISTS examples.birth_names CASCADE;
CREATE TABLE examples.birth_names (
    id SERIAL PRIMARY KEY,
    ds DATE, -- date/year
    gender VARCHAR(10),
    name VARCHAR(100),
    num INTEGER, -- count of births with this name
    state VARCHAR(50),
    sum_boys INTEGER,
    sum_girls INTEGER
);

CREATE INDEX idx_birth_names_ds ON examples.birth_names(ds);
CREATE INDEX idx_birth_names_name ON examples.birth_names(name);
CREATE INDEX idx_birth_names_state ON examples.birth_names(state);
CREATE INDEX idx_birth_names_gender ON examples.birth_names(gender);

-- ----------------------------------------------------------------------------
-- Birth France by Region
-- ----------------------------------------------------------------------------
DROP TABLE IF EXISTS examples.birth_france_by_region CASCADE;
CREATE TABLE examples.birth_france_by_region (
    id SERIAL PRIMARY KEY,
    year INTEGER,
    region VARCHAR(100),
    region_code VARCHAR(10),
    department VARCHAR(100),
    department_code VARCHAR(10),
    births INTEGER,
    deaths INTEGER,
    natural_growth INTEGER,
    population INTEGER
);

CREATE INDEX idx_france_birth_year ON examples.birth_france_by_region(year);
CREATE INDEX idx_france_birth_region ON examples.birth_france_by_region(region);

-- ----------------------------------------------------------------------------
-- Long Lat (geographic coordinates for mapping)
-- ----------------------------------------------------------------------------
DROP TABLE IF EXISTS examples.long_lat CASCADE;
CREATE TABLE examples.long_lat (
    id SERIAL PRIMARY KEY,
    city VARCHAR(100),
    state VARCHAR(50),
    country VARCHAR(100),
    latitude NUMERIC(10, 6),
    longitude NUMERIC(10, 6),
    population INTEGER,
    elevation INTEGER,
    timezone VARCHAR(50)
);

CREATE INDEX idx_long_lat_country ON examples.long_lat(country);
CREATE INDEX idx_long_lat_coords ON examples.long_lat(latitude, longitude);

-- ----------------------------------------------------------------------------
-- BART Lines (San Francisco Bay Area Rapid Transit)
-- ----------------------------------------------------------------------------
DROP TABLE IF EXISTS examples.bart_lines CASCADE;
CREATE TABLE examples.bart_lines (
    id SERIAL PRIMARY KEY,
    line_name VARCHAR(100),
    line_code VARCHAR(20),
    color VARCHAR(50),
    station_start VARCHAR(100),
    station_end VARCHAR(100),
    num_stations INTEGER,
    line_length_miles NUMERIC(8, 2),
    avg_daily_ridership INTEGER,
    year_opened INTEGER,
    coordinates TEXT -- GeoJSON or WKT for line geometry
);

-- ----------------------------------------------------------------------------
-- SF Population Polygons (San Francisco census areas)
-- ----------------------------------------------------------------------------
DROP TABLE IF EXISTS examples.sf_population_polygons CASCADE;
CREATE TABLE examples.sf_population_polygons (
    id SERIAL PRIMARY KEY,
    neighborhood VARCHAR(100),
    census_tract VARCHAR(50),
    population INTEGER,
    households INTEGER,
    median_income NUMERIC(12, 2),
    median_age NUMERIC(5, 2),
    area_sq_miles NUMERIC(10, 4),
    population_density NUMERIC(12, 2),
    geometry TEXT -- GeoJSON polygon
);

CREATE INDEX idx_sf_pop_neighborhood ON examples.sf_population_polygons(neighborhood);

-- ----------------------------------------------------------------------------
-- COVID Vaccines
-- ----------------------------------------------------------------------------
DROP TABLE IF EXISTS examples.covid_vaccines CASCADE;
CREATE TABLE examples.covid_vaccines (
    id SERIAL PRIMARY KEY,
    date DATE,
    country VARCHAR(100),
    iso_code VARCHAR(10),
    total_vaccinations BIGINT,
    people_vaccinated BIGINT,
    people_fully_vaccinated BIGINT,
    daily_vaccinations INTEGER,
    daily_vaccinations_per_million NUMERIC(12, 2),
    total_vaccinations_per_hundred NUMERIC(8, 2),
    people_vaccinated_per_hundred NUMERIC(8, 2),
    people_fully_vaccinated_per_hundred NUMERIC(8, 2),
    vaccines_used TEXT,
    source_url TEXT
);

CREATE INDEX idx_covid_vax_date ON examples.covid_vaccines(date);
CREATE INDEX idx_covid_vax_country ON examples.covid_vaccines(country);

-- ----------------------------------------------------------------------------
-- World Bank Health Population
-- ----------------------------------------------------------------------------
DROP TABLE IF EXISTS examples.wb_health_population CASCADE;
CREATE TABLE examples.wb_health_population (
    id SERIAL PRIMARY KEY,
    country_name VARCHAR(100),
    country_code VARCHAR(10),
    year INTEGER,
    population BIGINT,
    population_growth NUMERIC(8, 4),
    life_expectancy NUMERIC(6, 2),
    fertility_rate NUMERIC(6, 3),
    infant_mortality_rate NUMERIC(8, 3),
    birth_rate NUMERIC(8, 3),
    death_rate NUMERIC(8, 3),
    urban_population_pct NUMERIC(6, 2),
    gdp_per_capita NUMERIC(15, 2),
    health_expenditure_pct_gdp NUMERIC(6, 2),
    region VARCHAR(100),
    income_group VARCHAR(100)
);

CREATE INDEX idx_wb_health_country ON examples.wb_health_population(country_code);
CREATE INDEX idx_wb_health_year ON examples.wb_health_population(year);
CREATE INDEX idx_wb_health_region ON examples.wb_health_population(region);
