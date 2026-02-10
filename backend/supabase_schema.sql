
CREATE TABLE IF NOT EXISTS reviews (
    id TEXT PRIMARY KEY,
    mr_url TEXT NOT NULL,
    mr_title TEXT NOT NULL,
    author TEXT NOT NULL,
    files_changed INTEGER,
    lines_added INTEGER,
    lines_removed INTEGER,
    review_time TEXT,
    status TEXT CHECK (status IN ('passed', 'warnings', 'failed')),
    issues JSONB DEFAULT '[]'::jsonb,
    summary TEXT,
    reviewed_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    gitlab_token TEXT,
    project_id TEXT,
    merge_request_iid INTEGER
);

-- Create settings table
CREATE TABLE IF NOT EXISTS settings (
    id TEXT PRIMARY KEY,
    user_id TEXT DEFAULT 'default',
    github_token TEXT,
    gitlab_token TEXT,
    telegram_enabled BOOLEAN DEFAULT true,
    email_enabled BOOLEAN DEFAULT true,
    auto_review_enabled BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create telegram_actions table
CREATE TABLE IF NOT EXISTS telegram_actions (
    id TEXT PRIMARY KEY,
    review_id TEXT REFERENCES reviews(id),
    mr_url TEXT NOT NULL,
    action TEXT CHECK (action IN ('approve', 'decline')),
    user_id TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    status TEXT CHECK (status IN ('pending', 'success', 'failed')),
    error_message TEXT
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_reviews_reviewed_at ON reviews(reviewed_at DESC);
CREATE INDEX IF NOT EXISTS idx_reviews_status ON reviews(status);
CREATE INDEX IF NOT EXISTS idx_settings_user_id ON settings(user_id);
CREATE INDEX IF NOT EXISTS idx_telegram_actions_review_id ON telegram_actions(review_id);
CREATE INDEX IF NOT EXISTS idx_telegram_actions_created_at ON telegram_actions(created_at DESC);

-- Enable Row Level Security (RLS)
ALTER TABLE reviews ENABLE ROW LEVEL SECURITY;
ALTER TABLE settings ENABLE ROW LEVEL SECURITY;
ALTER TABLE telegram_actions ENABLE ROW LEVEL SECURITY;

-- Create policies for public access (adjust as needed for your security requirements)
CREATE POLICY \"Allow all operations on reviews\" ON reviews FOR ALL USING (true) WITH CHECK (true);
CREATE POLICY \"Allow all operations on settings\" ON settings FOR ALL USING (true) WITH CHECK (true);
CREATE POLICY \"Allow all operations on telegram_actions\" ON telegram_actions FOR ALL USING (true) WITH CHECK (true);

