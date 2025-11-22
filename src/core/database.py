import sqlite3
import os
from pathlib import Path
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from utils.logger import setup_logger

logger = setup_logger(__name__)

class DatabaseManager:
    def __init__(self, db_path="data/deskopt.db"):
        self.db_path = db_path
        self.ensure_database_exists()
    
    def ensure_database_exists(self):
        try:
            db_dir = os.path.dirname(self.db_path)
            if db_dir:  # Only create if there's a directory component
                os.makedirs(db_dir, exist_ok=True)
            if not os.path.exists(self.db_path):
                logger.info(f"Database not found, initializing: {self.db_path}")
                self.initialize_database()
            else:
                logger.info(f"Using existing database: {self.db_path}")
        except Exception as e:
            logger.error(f"Failed to ensure database exists: {e}", exc_info=True)
            raise
    
    def get_connection(self):
        try:
            return sqlite3.connect(self.db_path)
        except sqlite3.Error as e:
            logger.error(f"Database connection failed: {e}", exc_info=True)
            raise
    
    def initialize_database(self):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Profiles table
            cursor.execute('''
                CREATE TABLE profiles (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    role TEXT NOT NULL,
                    handedness TEXT NOT NULL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Item categories table
            cursor.execute('''
                CREATE TABLE item_categories (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    slug TEXT UNIQUE NOT NULL,
                    display_name TEXT NOT NULL
                )
            ''')
            
            # Ergonomic rules table
            cursor.execute('''
                CREATE TABLE ergonomic_rules (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    role_slug TEXT NOT NULL,
                    item_slug TEXT NOT NULL,
                    min_dist_cm REAL,
                    max_dist_cm REAL,
                    ideal_angle INTEGER,
                    priority_level INTEGER,
                    advice_text TEXT,
                    FOREIGN KEY(item_slug) REFERENCES item_categories(slug)
                )
            ''')
            
            # Scans table
            cursor.execute('''
                CREATE TABLE scans (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    profile_id INTEGER,
                    image_path TEXT NOT NULL,
                    scale_factor REAL,
                    desk_bounds TEXT,  -- JSON string of desk corners
                    scan_date DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY(profile_id) REFERENCES profiles(id)
                )
            ''')
            
            # Detected items table
            cursor.execute('''
                CREATE TABLE detected_items (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    scan_id INTEGER,
                    item_slug TEXT,
                    x_pos REAL,
                    y_pos REAL,
                    width REAL,
                    height REAL,
                    rotation REAL,
                    confidence REAL,
                    is_correct BOOLEAN DEFAULT 1,
                    FOREIGN KEY(scan_id) REFERENCES scans(id),
                    FOREIGN KEY(item_slug) REFERENCES item_categories(slug)
                )
            ''')
            
            # Seed data
            self.seed_initial_data(cursor)
            conn.commit()
    
    def seed_initial_data(self, cursor):
        # Item categories
        categories = [
            ('keyboard', 'Keyboard'),
            ('mouse', 'Mouse'),
            ('monitor', 'Monitor'),
            ('laptop', 'Laptop'),
            ('phone', 'Phone'),
            ('tablet', 'Tablet'),
            ('cup', 'Coffee Mug'),
            ('notebook', 'Notebook'),
            ('pen', 'Pen'),
            ('lamp', 'Desk Lamp'),
            ('speaker', 'Speaker'),
            ('headphones', 'Headphones')
        ]
        
        cursor.executemany(
            'INSERT INTO item_categories (slug, display_name) VALUES (?, ?)',
            categories
        )
        
        # Ergonomic rules for coders
        coder_rules = [
            ('keyboard', 10, 30, 0, 1, 'Keep keyboard centered and close to avoid shoulder strain'),
            ('mouse', 15, 35, 15, 1, 'Mouse should be within easy reach, slightly to the right for right-handed users'),
            ('monitor', 40, 70, 0, 1, 'Monitor at arm\'s length, centered with keyboard'),
            ('laptop', 35, 60, 0, 2, 'Laptop should be centered, consider external monitor'),
            ('phone', 20, 40, 45, 3, 'Keep phone within reach but not in primary workspace'),
            ('cup', 25, 50, -30, 3, 'Place drinks to the side to avoid spills')
        ]
        
        cursor.executemany('''
            INSERT INTO ergonomic_rules 
            (role_slug, item_slug, min_dist_cm, max_dist_cm, ideal_angle, priority_level, advice_text)
            VALUES ('coder', ?, ?, ?, ?, ?, ?)
        ''', coder_rules)
        
        # Ergonomic rules for artists
        artist_rules = [
            ('keyboard', 40, 60, -45, 2, 'Move keyboard aside to clear space for drawing tablet'),
            ('tablet', 15, 35, 0, 1, 'Drawing tablet should be centered and close'),
            ('pen', 10, 25, 0, 1, 'Keep pen/pencil within easy reach of tablet'),
            ('monitor', 40, 70, 0, 1, 'Monitor at arm\'s length, slightly above tablet'),
            ('lamp', 30, 50, 45, 2, 'Good lighting is essential for detailed work')
        ]
        
        cursor.executemany('''
            INSERT INTO ergonomic_rules 
            (role_slug, item_slug, min_dist_cm, max_dist_cm, ideal_angle, priority_level, advice_text)
            VALUES ('artist', ?, ?, ?, ?, ?, ?)
        ''', artist_rules)
        
        # Ergonomic rules for gamers
        gamer_rules = [
            ('keyboard', 10, 25, 0, 1, 'Keyboard should be close for quick access'),
            ('mouse', 10, 30, 20, 1, 'Mouse needs space for wide movements, positioned for dominant hand'),
            ('monitor', 35, 60, 0, 1, 'Monitor closer than typical work setup for better focus'),
            ('headphones', 15, 35, -45, 2, 'Headphones within easy reach for communication'),
            ('speaker', 40, 70, 30, 3, 'Speakers positioned for good audio without cluttering workspace')
        ]
        
        cursor.executemany('''
            INSERT INTO ergonomic_rules 
            (role_slug, item_slug, min_dist_cm, max_dist_cm, ideal_angle, priority_level, advice_text)
            VALUES ('gamer', ?, ?, ?, ?, ?, ?)
        ''', gamer_rules)
        
        # Ergonomic rules for admin/general office
        admin_rules = [
            ('keyboard', 15, 35, 0, 1, 'Keyboard centered at comfortable typing distance'),
            ('mouse', 15, 35, 15, 1, 'Mouse positioned for easy access without overreaching'),
            ('monitor', 45, 75, 0, 1, 'Monitor at proper distance to reduce eye strain'),
            ('phone', 10, 30, -30, 2, 'Phone within easy reach for frequent calls'),
            ('notebook', 20, 40, -45, 3, 'Notebook for taking notes during calls'),
            ('lamp', 30, 50, 45, 2, 'Good lighting to reduce eye strain')
        ]
        
        cursor.executemany('''
            INSERT INTO ergonomic_rules
            (role_slug, item_slug, min_dist_cm, max_dist_cm, ideal_angle, priority_level, advice_text)
            VALUES ('admin', ?, ?, ?, ?, ?, ?)
        ''', admin_rules)

        logger.info("Database seeded with initial data successfully")
    
    def create_profile(self, name, role, handedness):
        try:
            if not name or not name.strip():
                raise ValueError("Profile name cannot be empty")
            if role.lower() not in ['coder', 'artist', 'gamer', 'admin']:
                raise ValueError(f"Invalid role: {role}")
            if handedness.lower() not in ['left', 'right']:
                raise ValueError(f"Invalid handedness: {handedness}")

            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    'INSERT INTO profiles (name, role, handedness) VALUES (?, ?, ?)',
                    (name.strip(), role.lower(), handedness.lower())
                )
                profile_id = cursor.lastrowid
                logger.info(f"Created profile '{name}' (ID: {profile_id})")
                return profile_id
        except Exception as e:
            logger.error(f"Failed to create profile: {e}", exc_info=True)
            raise
    
    def get_profiles(self):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM profiles ORDER BY created_at DESC')
            return cursor.fetchall()
    
    def save_scan(self, profile_id, image_path, scale_factor, desk_bounds):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                'INSERT INTO scans (profile_id, image_path, scale_factor, desk_bounds) VALUES (?, ?, ?, ?)',
                (profile_id, image_path, scale_factor, desk_bounds)
            )
            return cursor.lastrowid
    
    def save_detected_items(self, scan_id, items):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            for item in items:
                cursor.execute('''
                    INSERT INTO detected_items 
                    (scan_id, item_slug, x_pos, y_pos, width, height, rotation, confidence)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    scan_id, item['item_slug'], item['x_pos'], item['y_pos'], 
                    item['width'], item['height'], item.get('rotation', 0), item['confidence']
                ))
    
    def get_ergonomic_rules(self, role):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT er.*, ic.display_name 
                FROM ergonomic_rules er
                JOIN item_categories ic ON er.item_slug = ic.slug
                WHERE er.role_slug = ?
                ORDER BY er.priority_level ASC
            ''', (role.lower(),))
            return cursor.fetchall()