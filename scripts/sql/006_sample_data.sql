-- ============================================================================
-- Sample Data for Example Datasets
-- ============================================================================

SET search_path TO examples, public;

-- ----------------------------------------------------------------------------
-- Users
-- ----------------------------------------------------------------------------
INSERT INTO examples.users (username, email, full_name, status, timezone) VALUES
('alice', 'alice@example.com', 'Alice Johnson', 'active', 'America/New_York'),
('bob', 'bob@example.com', 'Bob Smith', 'active', 'America/Los_Angeles'),
('charlie', 'charlie@example.com', 'Charlie Brown', 'active', 'Europe/London'),
('diana', 'diana@example.com', 'Diana Prince', 'active', 'Asia/Tokyo'),
('eve', 'eve@example.com', 'Eve Wilson', 'away', 'America/Chicago'),
('frank', 'frank@example.com', 'Frank Miller', 'active', 'Europe/Paris'),
('grace', 'grace@example.com', 'Grace Lee', 'active', 'Asia/Singapore'),
('henry', 'henry@example.com', 'Henry Davis', 'inactive', 'Australia/Sydney'),
('iris', 'iris@example.com', 'Iris Chen', 'active', 'America/Denver'),
('jack', 'jack@example.com', 'Jack Taylor', 'active', 'Europe/Berlin');

-- ----------------------------------------------------------------------------
-- Channels
-- ----------------------------------------------------------------------------
INSERT INTO examples.channels (name, description, channel_type, created_by, member_count, message_count) VALUES
('general', 'General discussion for everyone', 'public', 1, 10, 250),
('engineering', 'Engineering team discussions', 'public', 2, 6, 180),
('design', 'Design team channel', 'public', 3, 4, 95),
('random', 'Random fun stuff', 'public', 1, 8, 320),
('announcements', 'Company announcements', 'public', 1, 10, 45),
('project-alpha', 'Project Alpha team', 'private', 2, 5, 120),
('project-beta', 'Project Beta team', 'private', 4, 4, 85),
('leadership', 'Leadership discussions', 'private', 1, 3, 60),
('alice-bob', 'Direct message', 'direct', 1, 2, 150),
('support', 'Customer support team', 'public', 5, 7, 210);

-- ----------------------------------------------------------------------------
-- Channel Members
-- ----------------------------------------------------------------------------
INSERT INTO examples.channel_members (channel_id, user_id, role, joined_at) VALUES
-- General channel (everyone)
(1, 1, 'owner', NOW() - INTERVAL '90 days'),
(1, 2, 'admin', NOW() - INTERVAL '85 days'),
(1, 3, 'member', NOW() - INTERVAL '80 days'),
(1, 4, 'member', NOW() - INTERVAL '75 days'),
(1, 5, 'member', NOW() - INTERVAL '70 days'),
(1, 6, 'member', NOW() - INTERVAL '60 days'),
(1, 7, 'member', NOW() - INTERVAL '50 days'),
(1, 8, 'member', NOW() - INTERVAL '40 days'),
(1, 9, 'member', NOW() - INTERVAL '30 days'),
(1, 10, 'member', NOW() - INTERVAL '20 days'),
-- Engineering channel
(2, 2, 'owner', NOW() - INTERVAL '80 days'),
(2, 1, 'admin', NOW() - INTERVAL '78 days'),
(2, 4, 'member', NOW() - INTERVAL '70 days'),
(2, 7, 'member', NOW() - INTERVAL '60 days'),
(2, 9, 'member', NOW() - INTERVAL '45 days'),
(2, 10, 'member', NOW() - INTERVAL '30 days'),
-- Design channel
(3, 3, 'owner', NOW() - INTERVAL '75 days'),
(3, 5, 'admin', NOW() - INTERVAL '70 days'),
(3, 6, 'member', NOW() - INTERVAL '50 days'),
(3, 8, 'member', NOW() - INTERVAL '35 days');

-- ----------------------------------------------------------------------------
-- Users Channels
-- ----------------------------------------------------------------------------
INSERT INTO examples.users_channels (user_id, channel_id, is_favorite, is_muted, unread_count) VALUES
(1, 1, true, false, 0),
(1, 2, true, false, 5),
(2, 1, false, false, 12),
(2, 2, true, false, 0),
(3, 1, false, true, 45),
(3, 3, true, false, 2);

-- ----------------------------------------------------------------------------
-- Threads
-- ----------------------------------------------------------------------------
INSERT INTO examples.threads (channel_id, title, reply_count, participant_count, created_by) VALUES
(1, 'Welcome new team members!', 15, 8, 1),
(2, 'Code review best practices', 23, 5, 2),
(2, 'New CI/CD pipeline proposal', 18, 4, 4),
(3, 'Design system updates Q4', 12, 3, 3),
(1, 'Holiday schedule 2024', 8, 6, 1);

-- ----------------------------------------------------------------------------
-- Messages
-- ----------------------------------------------------------------------------
INSERT INTO examples.messages (channel_id, thread_id, user_id, content, message_type, reaction_count, created_at) VALUES
(1, 1, 1, 'Welcome everyone to the team!', 'text', 10, NOW() - INTERVAL '30 days'),
(1, 1, 2, 'Great to be here!', 'text', 5, NOW() - INTERVAL '30 days' + INTERVAL '1 hour'),
(1, 1, 3, 'Looking forward to working with you all', 'text', 3, NOW() - INTERVAL '30 days' + INTERVAL '2 hours'),
(2, 2, 2, 'Lets discuss our code review process', 'text', 8, NOW() - INTERVAL '25 days'),
(2, 2, 4, 'I think we should use conventional commits', 'text', 12, NOW() - INTERVAL '25 days' + INTERVAL '30 minutes'),
(2, NULL, 7, 'Quick question about the API', 'text', 2, NOW() - INTERVAL '5 days'),
(3, 4, 3, 'Here are the design system updates for Q4', 'text', 6, NOW() - INTERVAL '15 days'),
(1, NULL, 5, 'Good morning everyone!', 'text', 4, NOW() - INTERVAL '1 day'),
(1, NULL, 6, 'Has anyone seen the latest metrics?', 'text', 1, NOW() - INTERVAL '12 hours'),
(2, 3, 4, 'New CI/CD proposal attached', 'file', 7, NOW() - INTERVAL '10 days');

-- ----------------------------------------------------------------------------
-- Video Game Sales (sample data)
-- ----------------------------------------------------------------------------
INSERT INTO examples.video_game_sales (rank, name, platform, year, genre, publisher, na_sales, eu_sales, jp_sales, other_sales, global_sales) VALUES
(1, 'Wii Sports', 'Wii', 2006, 'Sports', 'Nintendo', 41.49, 29.02, 3.77, 8.46, 82.74),
(2, 'Super Mario Bros.', 'NES', 1985, 'Platform', 'Nintendo', 29.08, 3.58, 6.81, 0.77, 40.24),
(3, 'Mario Kart Wii', 'Wii', 2008, 'Racing', 'Nintendo', 15.85, 12.88, 3.79, 3.31, 35.82),
(4, 'Wii Sports Resort', 'Wii', 2009, 'Sports', 'Nintendo', 15.75, 11.01, 3.28, 2.96, 33.00),
(5, 'Pokemon Red/Blue', 'GB', 1996, 'Role-Playing', 'Nintendo', 11.27, 8.89, 10.22, 1.00, 31.37),
(6, 'Tetris', 'GB', 1989, 'Puzzle', 'Nintendo', 23.20, 2.26, 4.22, 0.58, 30.26),
(7, 'New Super Mario Bros.', 'DS', 2006, 'Platform', 'Nintendo', 11.38, 9.23, 6.50, 2.90, 30.01),
(8, 'Wii Play', 'Wii', 2006, 'Misc', 'Nintendo', 14.03, 9.20, 2.93, 2.85, 29.02),
(9, 'Duck Hunt', 'NES', 1984, 'Shooter', 'Nintendo', 26.93, 0.63, 0.28, 0.47, 28.31),
(10, 'New Super Mario Bros. Wii', 'Wii', 2009, 'Platform', 'Nintendo', 14.59, 7.06, 4.70, 2.26, 28.62),
(11, 'Grand Theft Auto V', 'PS3', 2013, 'Action', 'Rockstar Games', 7.01, 9.27, 0.97, 4.14, 21.40),
(12, 'Grand Theft Auto V', 'X360', 2013, 'Action', 'Rockstar Games', 9.63, 5.31, 0.06, 1.38, 16.38),
(13, 'Call of Duty: Modern Warfare 3', 'X360', 2011, 'Shooter', 'Activision', 9.03, 4.28, 0.13, 1.32, 14.76),
(14, 'Call of Duty: Black Ops', 'X360', 2010, 'Shooter', 'Activision', 9.67, 3.73, 0.11, 1.13, 14.64),
(15, 'Call of Duty: Black Ops II', 'X360', 2012, 'Shooter', 'Activision', 8.25, 4.30, 0.07, 1.12, 13.73);

-- ----------------------------------------------------------------------------
-- Cleaned Sales Data (sample retail data)
-- ----------------------------------------------------------------------------
INSERT INTO examples.cleaned_sales_data (order_id, order_date, ship_date, ship_mode, customer_id, customer_name, segment, country, city, state, region, category, sub_category, product_name, sales, quantity, discount, profit) VALUES
('CA-2023-001', '2023-01-05', '2023-01-07', 'Standard', 'CG-001', 'Claire Gute', 'Consumer', 'United States', 'Henderson', 'Kentucky', 'South', 'Furniture', 'Bookcases', 'Bush Somerset Collection Bookcase', 261.96, 2, 0.00, 41.91),
('CA-2023-002', '2023-01-10', '2023-01-14', 'Standard', 'SO-002', 'Sean ODonnell', 'Consumer', 'United States', 'Fort Worth', 'Texas', 'Central', 'Office Supplies', 'Storage', 'Eldon Stackable Tray', 22.37, 3, 0.20, 6.87),
('CA-2023-003', '2023-01-15', '2023-01-17', 'Second Class', 'BH-003', 'Brosina Hoffman', 'Consumer', 'United States', 'Los Angeles', 'California', 'West', 'Technology', 'Phones', 'Samsung Galaxy Phone', 907.15, 5, 0.00, 68.04),
('CA-2023-004', '2023-01-20', '2023-01-25', 'Standard', 'AG-004', 'Andrew Allen', 'Corporate', 'United States', 'New York City', 'New York', 'East', 'Office Supplies', 'Labels', 'Self-Adhesive Labels', 14.62, 2, 0.00, 6.87),
('CA-2023-005', '2023-02-01', '2023-02-03', 'First Class', 'ZC-005', 'Zuschuss Carroll', 'Consumer', 'United States', 'San Francisco', 'California', 'West', 'Technology', 'Accessories', 'Logitech Keyboard', 256.99, 1, 0.10, 51.40),
('CA-2023-006', '2023-02-10', '2023-02-12', 'Same Day', 'KB-006', 'Ken Black', 'Corporate', 'United States', 'Chicago', 'Illinois', 'Central', 'Furniture', 'Tables', 'Chromcraft Table', 957.58, 2, 0.45, -383.03),
('CA-2023-007', '2023-02-15', '2023-02-17', 'Standard', 'SP-007', 'Sandra Pratt', 'Home Office', 'United States', 'Philadelphia', 'Pennsylvania', 'East', 'Office Supplies', 'Paper', 'Xerox Copy Paper', 15.55, 5, 0.00, 5.44),
('CA-2023-008', '2023-03-01', '2023-03-05', 'Second Class', 'HP-008', 'Hunter Preston', 'Consumer', 'United States', 'Seattle', 'Washington', 'West', 'Technology', 'Machines', 'HP Printer', 500.00, 1, 0.20, 75.00),
('CA-2023-009', '2023-03-10', '2023-03-12', 'Standard', 'JS-009', 'Jim Sink', 'Corporate', 'United States', 'Houston', 'Texas', 'Central', 'Furniture', 'Chairs', 'HON Executive Chair', 1200.00, 3, 0.15, 180.00),
('CA-2023-010', '2023-03-20', '2023-03-22', 'First Class', 'TB-010', 'Tracy Blumstein', 'Consumer', 'United States', 'Miami', 'Florida', 'South', 'Office Supplies', 'Binders', 'Avery Binders', 45.99, 10, 0.00, 18.40);

-- ----------------------------------------------------------------------------
-- Birth Names (US baby names sample)
-- ----------------------------------------------------------------------------
INSERT INTO examples.birth_names (ds, gender, name, num, state) VALUES
('2020-01-01', 'boy', 'Liam', 19659, 'CA'),
('2020-01-01', 'boy', 'Noah', 18252, 'CA'),
('2020-01-01', 'boy', 'Oliver', 14147, 'CA'),
('2020-01-01', 'boy', 'Elijah', 13034, 'CA'),
('2020-01-01', 'boy', 'William', 12541, 'CA'),
('2020-01-01', 'girl', 'Olivia', 17535, 'CA'),
('2020-01-01', 'girl', 'Emma', 15581, 'CA'),
('2020-01-01', 'girl', 'Ava', 13084, 'CA'),
('2020-01-01', 'girl', 'Charlotte', 13003, 'CA'),
('2020-01-01', 'girl', 'Sophia', 12976, 'CA'),
('2021-01-01', 'boy', 'Liam', 20456, 'CA'),
('2021-01-01', 'boy', 'Noah', 18739, 'CA'),
('2021-01-01', 'girl', 'Olivia', 17728, 'CA'),
('2021-01-01', 'girl', 'Emma', 15433, 'CA'),
('2020-01-01', 'boy', 'Liam', 9876, 'TX'),
('2020-01-01', 'boy', 'Noah', 8765, 'TX'),
('2020-01-01', 'girl', 'Olivia', 8654, 'TX'),
('2020-01-01', 'girl', 'Emma', 7543, 'TX'),
('2020-01-01', 'boy', 'Liam', 7654, 'NY'),
('2020-01-01', 'girl', 'Olivia', 6987, 'NY');

-- ----------------------------------------------------------------------------
-- Flights (sample data)
-- ----------------------------------------------------------------------------
INSERT INTO examples.flights (flight_date, dep_time, arr_time, carrier, flight_num, origin, origin_city, origin_state, dest, dest_city, dest_state, distance, dep_delay, arr_delay, air_time) VALUES
('2023-01-15', 800, 1130, 'AA', 100, 'JFK', 'New York', 'NY', 'LAX', 'Los Angeles', 'CA', 2475, 5, -10, 330),
('2023-01-15', 900, 1200, 'UA', 200, 'SFO', 'San Francisco', 'CA', 'ORD', 'Chicago', 'IL', 1846, -5, 0, 240),
('2023-01-15', 1000, 1430, 'DL', 300, 'ATL', 'Atlanta', 'GA', 'SEA', 'Seattle', 'WA', 2182, 15, 20, 300),
('2023-01-15', 1100, 1330, 'SW', 400, 'DEN', 'Denver', 'CO', 'PHX', 'Phoenix', 'AZ', 602, 0, -5, 120),
('2023-01-15', 1200, 1500, 'AA', 500, 'DFW', 'Dallas', 'TX', 'MIA', 'Miami', 'FL', 1121, 30, 45, 180),
('2023-01-16', 700, 1000, 'UA', 600, 'LAX', 'Los Angeles', 'CA', 'JFK', 'New York', 'NY', 2475, -10, -15, 320),
('2023-01-16', 800, 1030, 'DL', 700, 'ORD', 'Chicago', 'IL', 'ATL', 'Atlanta', 'GA', 606, 5, 10, 120),
('2023-01-16', 900, 1130, 'SW', 800, 'PHX', 'Phoenix', 'AZ', 'DEN', 'Denver', 'CO', 602, 0, 0, 110),
('2023-01-16', 1400, 1730, 'AA', 900, 'MIA', 'Miami', 'FL', 'DFW', 'Dallas', 'TX', 1121, 60, 75, 175),
('2023-01-16', 1500, 1830, 'UA', 1000, 'SEA', 'Seattle', 'WA', 'SFO', 'San Francisco', 'CA', 679, 10, 15, 100);

-- ----------------------------------------------------------------------------
-- COVID Vaccines (sample data)
-- ----------------------------------------------------------------------------
INSERT INTO examples.covid_vaccines (date, country, iso_code, total_vaccinations, people_vaccinated, people_fully_vaccinated, daily_vaccinations, vaccines_used) VALUES
('2021-12-01', 'United States', 'USA', 450000000, 230000000, 195000000, 1500000, 'Pfizer, Moderna, Johnson&Johnson'),
('2021-12-01', 'United Kingdom', 'GBR', 120000000, 52000000, 48000000, 400000, 'Pfizer, AstraZeneca, Moderna'),
('2021-12-01', 'Germany', 'DEU', 130000000, 60000000, 55000000, 800000, 'Pfizer, Moderna, AstraZeneca'),
('2021-12-01', 'France', 'FRA', 110000000, 52000000, 50000000, 500000, 'Pfizer, Moderna, AstraZeneca'),
('2021-12-01', 'Japan', 'JPN', 195000000, 100000000, 98000000, 300000, 'Pfizer, Moderna'),
('2022-06-01', 'United States', 'USA', 580000000, 260000000, 222000000, 500000, 'Pfizer, Moderna, Johnson&Johnson'),
('2022-06-01', 'United Kingdom', 'GBR', 150000000, 54000000, 51000000, 100000, 'Pfizer, AstraZeneca, Moderna'),
('2022-06-01', 'Germany', 'DEU', 180000000, 65000000, 63000000, 200000, 'Pfizer, Moderna'),
('2022-06-01', 'France', 'FRA', 145000000, 55000000, 54000000, 150000, 'Pfizer, Moderna'),
('2022-06-01', 'Japan', 'JPN', 300000000, 103000000, 102000000, 400000, 'Pfizer, Moderna');

-- ----------------------------------------------------------------------------
-- World Bank Health Population (sample data)
-- ----------------------------------------------------------------------------
INSERT INTO examples.wb_health_population (country_name, country_code, year, population, life_expectancy, fertility_rate, gdp_per_capita, region, income_group) VALUES
('United States', 'USA', 2022, 331900000, 76.4, 1.66, 76330, 'North America', 'High income'),
('China', 'CHN', 2022, 1412000000, 77.9, 1.16, 12720, 'East Asia & Pacific', 'Upper middle income'),
('India', 'IND', 2022, 1417000000, 70.4, 2.03, 2380, 'South Asia', 'Lower middle income'),
('Germany', 'DEU', 2022, 84080000, 80.9, 1.58, 48720, 'Europe & Central Asia', 'High income'),
('United Kingdom', 'GBR', 2022, 67510000, 80.7, 1.61, 45850, 'Europe & Central Asia', 'High income'),
('France', 'FRA', 2022, 67750000, 82.5, 1.83, 42330, 'Europe & Central Asia', 'High income'),
('Japan', 'JPN', 2022, 125100000, 84.8, 1.20, 34020, 'East Asia & Pacific', 'High income'),
('Brazil', 'BRA', 2022, 215300000, 75.4, 1.65, 8920, 'Latin America & Caribbean', 'Upper middle income'),
('Nigeria', 'NGA', 2022, 218500000, 53.9, 5.14, 2180, 'Sub-Saharan Africa', 'Lower middle income'),
('Australia', 'AUS', 2022, 26010000, 83.5, 1.70, 59930, 'East Asia & Pacific', 'High income');

-- ----------------------------------------------------------------------------
-- Long Lat (geographic coordinates)
-- ----------------------------------------------------------------------------
INSERT INTO examples.long_lat (city, state, country, latitude, longitude, population) VALUES
('New York', 'NY', 'United States', 40.7128, -74.0060, 8336817),
('Los Angeles', 'CA', 'United States', 34.0522, -118.2437, 3979576),
('Chicago', 'IL', 'United States', 41.8781, -87.6298, 2693976),
('Houston', 'TX', 'United States', 29.7604, -95.3698, 2320268),
('Phoenix', 'AZ', 'United States', 33.4484, -112.0740, 1680992),
('San Francisco', 'CA', 'United States', 37.7749, -122.4194, 873965),
('Seattle', 'WA', 'United States', 47.6062, -122.3321, 753675),
('Denver', 'CO', 'United States', 39.7392, -104.9903, 727211),
('Miami', 'FL', 'United States', 25.7617, -80.1918, 467963),
('Atlanta', 'GA', 'United States', 33.7490, -84.3880, 498044);

-- ----------------------------------------------------------------------------
-- BART Lines (San Francisco Bay Area)
-- ----------------------------------------------------------------------------
INSERT INTO examples.bart_lines (line_name, line_code, color, station_start, station_end, num_stations, line_length_miles, avg_daily_ridership, year_opened) VALUES
('Richmond-Millbrae', 'RED', 'Red', 'Richmond', 'Millbrae', 23, 38.5, 85000, 1972),
('Fremont-Daly City', 'GREEN', 'Green', 'Fremont', 'Daly City', 18, 33.2, 72000, 1972),
('Dublin/Pleasanton-Daly City', 'BLUE', 'Blue', 'Dublin/Pleasanton', 'Daly City', 17, 35.8, 65000, 1997),
('Pittsburg/Bay Point-SFO', 'YELLOW', 'Yellow', 'Pittsburg/Bay Point', 'SFO Airport', 24, 43.7, 95000, 1996),
('Richmond-Fremont', 'ORANGE', 'Orange', 'Richmond', 'Fremont', 19, 32.1, 55000, 1972);

-- ----------------------------------------------------------------------------
-- SF Population Polygons (sample neighborhoods)
-- ----------------------------------------------------------------------------
INSERT INTO examples.sf_population_polygons (neighborhood, census_tract, population, households, median_income, median_age, area_sq_miles) VALUES
('Mission', '020100', 58391, 22145, 85000, 33.5, 1.2),
('Castro', '020200', 18123, 9876, 125000, 39.2, 0.6),
('SoMa', '017600', 32456, 18765, 95000, 35.8, 1.8),
('Financial District', '061100', 8976, 4532, 175000, 38.1, 0.5),
('Chinatown', '010700', 15234, 6543, 45000, 42.3, 0.2),
('Marina', '012800', 23456, 12345, 145000, 36.7, 0.9),
('Sunset', '035301', 67890, 24567, 105000, 41.2, 3.8),
('Richmond', '048100', 54321, 19876, 98000, 40.5, 3.2),
('Noe Valley', '020800', 21098, 8765, 165000, 38.9, 0.7),
('Pacific Heights', '013400', 19876, 9234, 215000, 42.1, 0.8);

-- ----------------------------------------------------------------------------
-- Birth France by Region (sample data)
-- ----------------------------------------------------------------------------
INSERT INTO examples.birth_france_by_region (year, region, region_code, department, births, deaths, population) VALUES
(2022, 'Île-de-France', 'IDF', 'Paris', 28500, 22100, 2165000),
(2022, 'Île-de-France', 'IDF', 'Hauts-de-Seine', 21800, 14200, 1632000),
(2022, 'Auvergne-Rhône-Alpes', 'ARA', 'Rhône', 22100, 17500, 1889000),
(2022, 'Provence-Alpes-Côte dAzur', 'PACA', 'Bouches-du-Rhône', 23400, 19800, 2043000),
(2022, 'Nouvelle-Aquitaine', 'NAQ', 'Gironde', 17200, 14100, 1632000),
(2021, 'Île-de-France', 'IDF', 'Paris', 29100, 23200, 2148000),
(2021, 'Île-de-France', 'IDF', 'Hauts-de-Seine', 22300, 14800, 1619000),
(2021, 'Auvergne-Rhône-Alpes', 'ARA', 'Rhône', 22800, 17900, 1874000),
(2020, 'Île-de-France', 'IDF', 'Paris', 27800, 24500, 2161000),
(2020, 'Provence-Alpes-Côte dAzur', 'PACA', 'Bouches-du-Rhône', 22900, 21200, 2030000);

-- ----------------------------------------------------------------------------
-- Unicode Test (internationalization testing)
-- ----------------------------------------------------------------------------
INSERT INTO examples.unicode_test (text_value, description, language, script_type) VALUES
('Hello World', 'English greeting', 'English', 'Latin'),
('你好世界', 'Chinese greeting', 'Chinese', 'Han'),
('こんにちは世界', 'Japanese greeting', 'Japanese', 'Hiragana/Kanji'),
('مرحبا بالعالم', 'Arabic greeting', 'Arabic', 'Arabic'),
('Привет мир', 'Russian greeting', 'Russian', 'Cyrillic'),
('שלום עולם', 'Hebrew greeting', 'Hebrew', 'Hebrew'),
('สวัสดีโลก', 'Thai greeting', 'Thai', 'Thai'),
('Γειά σου Κόσμε', 'Greek greeting', 'Greek', 'Greek'),
('🌍🌎🌏', 'Earth emojis', 'Emoji', 'Emoji'),
('Ü Ö Ä ß', 'German umlauts', 'German', 'Latin Extended');

-- ----------------------------------------------------------------------------
-- Exported Stats (sample metrics)
-- ----------------------------------------------------------------------------
INSERT INTO examples.exported_stats (stat_date, metric_name, metric_value, dimension_1, dimension_2, source) VALUES
('2024-01-01', 'daily_active_users', 15234, 'web', 'US', 'analytics'),
('2024-01-01', 'daily_active_users', 8765, 'mobile', 'US', 'analytics'),
('2024-01-01', 'daily_active_users', 4321, 'web', 'EU', 'analytics'),
('2024-01-01', 'revenue', 125000.50, 'subscription', 'US', 'billing'),
('2024-01-01', 'revenue', 45000.25, 'subscription', 'EU', 'billing'),
('2024-01-02', 'daily_active_users', 16100, 'web', 'US', 'analytics'),
('2024-01-02', 'daily_active_users', 9012, 'mobile', 'US', 'analytics'),
('2024-01-02', 'revenue', 132500.75, 'subscription', 'US', 'billing'),
('2024-01-03', 'daily_active_users', 15890, 'web', 'US', 'analytics'),
('2024-01-03', 'page_views', 456789, 'web', 'global', 'analytics');

-- Update timestamps for realistic data
UPDATE examples.users SET last_active_at = NOW() - (random() * INTERVAL '7 days');
UPDATE examples.channels SET updated_at = NOW() - (random() * INTERVAL '3 days');
