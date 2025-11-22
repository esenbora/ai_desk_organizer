-- 1. Profiles: Who is using the app?
CREATE TABLE profiles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    role TEXT NOT NULL,       -- 'Coder', 'Artist', 'Gamer'
    handedness TEXT NOT NULL, -- 'Left', 'Right'
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- 2. Item_Categories: What objects do we know about?
-- We define them here so we can attach rules to them.
CREATE TABLE item_categories (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    slug TEXT UNIQUE NOT NULL,  -- 'keyboard', 'mouse', 'monitor'
    display_name TEXT NOT NULL  -- 'Mechanical Keyboard'
);

-- 3. Ergonomic_Rules: The core logic.
-- This table defines "Good" placement based on the Profile's Role.
-- Example: If Role='Coder' and Item='Mouse', Ideal Zone is 10-25cm.
CREATE TABLE ergonomic_rules (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    role_slug TEXT NOT NULL,        -- 'coder'
    item_slug TEXT NOT NULL,        -- 'mouse'
    min_dist_cm REAL,               -- Minimum distance from user edge
    max_dist_cm REAL,               -- Maximum distance from user edge
    ideal_angle INTEGER,            -- e.g., 0 for center, 45 for side
    priority_level INTEGER,         -- 1=Must Move, 3=Nice to have
    advice_text TEXT,               -- "Keep mouse close to avoid shoulder strain"
    FOREIGN KEY(item_slug) REFERENCES item_categories(slug)
);

-- 4. Scans: History of user uploads.
CREATE TABLE scans (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    profile_id INTEGER,
    image_path TEXT NOT NULL,     -- Local file path to the user's photo
    scale_factor REAL,            -- Pixels per CM (calculated via card)
    scan_date DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(profile_id) REFERENCES profiles(id)
);

-- 5. Detected_Items: What we found in a specific scan.
CREATE TABLE detected_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    scan_id INTEGER,
    item_slug TEXT,               -- What did AI think this was?
    x_pos REAL,                   -- X coordinate (cm)
    y_pos REAL,                   -- Y coordinate (cm)
    rotation REAL,                -- Angle on desk
    is_correct BOOLEAN DEFAULT 1, -- User verification flag (Triage step)
    FOREIGN KEY(scan_id) REFERENCES scans(id),
    FOREIGN KEY(item_slug) REFERENCES item_categories(slug)
);

-- SEED DATA: This populates your app with initial intelligence.
INSERT INTO item_categories (slug, display_name) VALUES 
('keyboard', 'Keyboard'), ('mouse', 'Mouse'), ('monitor', 'Monitor');

-- Rule: Coders need the keyboard centered (0 degrees) and close (10-30cm).
INSERT INTO ergonomic_rules (role_slug, item_slug, min_dist_cm, max_dist_cm, ideal_angle, advice_text)
VALUES ('coder', 'keyboard', 10, 30, 0, 'Your keyboard is your primary tool. Keep it centered.');

-- Rule: Artists need the keyboard off to the side (to make room for tablet).
INSERT INTO ergonomic_rules (role_slug, item_slug, min_dist_cm, max_dist_cm, ideal_angle, advice_text)
VALUES ('artist', 'keyboard', 40, 60, -45, 'Move keyboard aside to clear space for your drawing tablet.');