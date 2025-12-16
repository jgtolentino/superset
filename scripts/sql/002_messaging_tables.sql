-- ============================================================================
-- Messaging & Collaboration Tables
-- Tables: users, channels, channel_members, messages, threads, users_channels
-- ============================================================================

SET search_path TO examples, public;

-- ----------------------------------------------------------------------------
-- Users table
-- ----------------------------------------------------------------------------
DROP TABLE IF EXISTS examples.users CASCADE;
CREATE TABLE examples.users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(100) NOT NULL UNIQUE,
    email VARCHAR(255),
    full_name VARCHAR(200),
    avatar_url TEXT,
    status VARCHAR(20) DEFAULT 'active',
    timezone VARCHAR(50) DEFAULT 'UTC',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_active_at TIMESTAMP WITH TIME ZONE
);

CREATE INDEX idx_users_username ON examples.users(username);
CREATE INDEX idx_users_status ON examples.users(status);

-- ----------------------------------------------------------------------------
-- Channels table
-- ----------------------------------------------------------------------------
DROP TABLE IF EXISTS examples.channels CASCADE;
CREATE TABLE examples.channels (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    channel_type VARCHAR(20) DEFAULT 'public', -- public, private, direct
    created_by INTEGER REFERENCES examples.users(id),
    member_count INTEGER DEFAULT 0,
    message_count INTEGER DEFAULT 0,
    is_archived BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_channels_name ON examples.channels(name);
CREATE INDEX idx_channels_type ON examples.channels(channel_type);

-- ----------------------------------------------------------------------------
-- Channel Members (junction table)
-- ----------------------------------------------------------------------------
DROP TABLE IF EXISTS examples.channel_members CASCADE;
CREATE TABLE examples.channel_members (
    id SERIAL PRIMARY KEY,
    channel_id INTEGER REFERENCES examples.channels(id) ON DELETE CASCADE,
    user_id INTEGER REFERENCES examples.users(id) ON DELETE CASCADE,
    role VARCHAR(20) DEFAULT 'member', -- owner, admin, member
    joined_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_read_at TIMESTAMP WITH TIME ZONE,
    notifications_enabled BOOLEAN DEFAULT TRUE,
    UNIQUE(channel_id, user_id)
);

CREATE INDEX idx_channel_members_channel ON examples.channel_members(channel_id);
CREATE INDEX idx_channel_members_user ON examples.channel_members(user_id);

-- ----------------------------------------------------------------------------
-- Users Channels (alternative junction with more metadata)
-- ----------------------------------------------------------------------------
DROP TABLE IF EXISTS examples.users_channels CASCADE;
CREATE TABLE examples.users_channels (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES examples.users(id) ON DELETE CASCADE,
    channel_id INTEGER REFERENCES examples.channels(id) ON DELETE CASCADE,
    is_favorite BOOLEAN DEFAULT FALSE,
    is_muted BOOLEAN DEFAULT FALSE,
    unread_count INTEGER DEFAULT 0,
    last_visited_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(user_id, channel_id)
);

-- ----------------------------------------------------------------------------
-- Threads table
-- ----------------------------------------------------------------------------
DROP TABLE IF EXISTS examples.threads CASCADE;
CREATE TABLE examples.threads (
    id SERIAL PRIMARY KEY,
    channel_id INTEGER REFERENCES examples.channels(id) ON DELETE CASCADE,
    parent_message_id INTEGER,
    title VARCHAR(255),
    reply_count INTEGER DEFAULT 0,
    participant_count INTEGER DEFAULT 0,
    last_reply_at TIMESTAMP WITH TIME ZONE,
    created_by INTEGER REFERENCES examples.users(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    is_resolved BOOLEAN DEFAULT FALSE
);

CREATE INDEX idx_threads_channel ON examples.threads(channel_id);

-- ----------------------------------------------------------------------------
-- Messages table
-- ----------------------------------------------------------------------------
DROP TABLE IF EXISTS examples.messages CASCADE;
CREATE TABLE examples.messages (
    id SERIAL PRIMARY KEY,
    channel_id INTEGER REFERENCES examples.channels(id) ON DELETE CASCADE,
    thread_id INTEGER REFERENCES examples.threads(id) ON DELETE SET NULL,
    user_id INTEGER REFERENCES examples.users(id) ON DELETE SET NULL,
    content TEXT NOT NULL,
    message_type VARCHAR(20) DEFAULT 'text', -- text, file, image, system
    is_edited BOOLEAN DEFAULT FALSE,
    is_deleted BOOLEAN DEFAULT FALSE,
    reaction_count INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_messages_channel ON examples.messages(channel_id);
CREATE INDEX idx_messages_user ON examples.messages(user_id);
CREATE INDEX idx_messages_created ON examples.messages(created_at);
CREATE INDEX idx_messages_thread ON examples.messages(thread_id);
