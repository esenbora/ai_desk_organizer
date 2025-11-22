"""
Unit tests for DatabaseManager
"""
import pytest
import os
import sqlite3
from core.database import DatabaseManager


class TestDatabaseManager:
    """Test DatabaseManager class"""

    @pytest.fixture
    def db(self, temp_db_path):
        """Create a DatabaseManager instance with temp database"""
        return DatabaseManager(temp_db_path)

    def test_init_creates_database(self, temp_db_path):
        """Test that initialization creates database file"""
        assert not os.path.exists(temp_db_path)
        db = DatabaseManager(temp_db_path)
        assert os.path.exists(temp_db_path)

    def test_database_schema(self, db):
        """Test that all tables are created"""
        with db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            )
            tables = {row[0] for row in cursor.fetchall()}

        expected_tables = {
            'profiles', 'item_categories', 'ergonomic_rules',
            'scans', 'detected_items'
        }
        assert expected_tables.issubset(tables)

    def test_item_categories_seeded(self, db):
        """Test that item categories are seeded"""
        with db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM item_categories")
            count = cursor.fetchone()[0]

        assert count >= 12  # At least 12 item categories

    def test_ergonomic_rules_seeded(self, db):
        """Test that ergonomic rules are seeded"""
        with db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM ergonomic_rules")
            count = cursor.fetchone()[0]

        assert count > 0  # Should have some rules

    def test_create_profile_valid(self, db):
        """Test creating a valid profile"""
        profile_id = db.create_profile("Test User", "coder", "right")
        assert profile_id is not None
        assert isinstance(profile_id, int)

    def test_create_profile_empty_name(self, db):
        """Test creating profile with empty name"""
        with pytest.raises(ValueError, match="cannot be empty"):
            db.create_profile("", "coder", "right")

        with pytest.raises(ValueError, match="cannot be empty"):
            db.create_profile("   ", "coder", "right")

    def test_create_profile_invalid_role(self, db):
        """Test creating profile with invalid role"""
        with pytest.raises(ValueError, match="Invalid role"):
            db.create_profile("Test User", "invalid_role", "right")

    def test_create_profile_invalid_handedness(self, db):
        """Test creating profile with invalid handedness"""
        with pytest.raises(ValueError, match="Invalid handedness"):
            db.create_profile("Test User", "coder", "middle")

    def test_create_profile_normalizes_case(self, db):
        """Test that profile creation normalizes role and handedness"""
        profile_id = db.create_profile("Test User", "CODER", "RIGHT")

        with db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT role, handedness FROM profiles WHERE id = ?",
                (profile_id,)
            )
            role, handedness = cursor.fetchone()

        assert role == "coder"
        assert handedness == "right"

    def test_get_profiles_empty(self, db):
        """Test getting profiles when none exist"""
        profiles = db.get_profiles()
        assert profiles == []

    def test_get_profiles_ordered_by_date(self, db):
        """Test that profiles are ordered by creation date (newest first)"""
        id1 = db.create_profile("User 1", "coder", "right")
        id2 = db.create_profile("User 2", "artist", "left")
        id3 = db.create_profile("User 3", "gamer", "right")

        profiles = db.get_profiles()
        assert len(profiles) == 3
        # Newest first
        assert profiles[0][0] == id3
        assert profiles[1][0] == id2
        assert profiles[2][0] == id1

    def test_save_scan(self, db):
        """Test saving a scan"""
        profile_id = db.create_profile("Test User", "coder", "right")
        scan_id = db.save_scan(
            profile_id,
            "/path/to/image.jpg",
            10.5,
            '[[0,0],[100,0],[100,100],[0,100]]'
        )

        assert scan_id is not None
        assert isinstance(scan_id, int)

        # Verify scan was saved
        with db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM scans WHERE id = ?", (scan_id,))
            row = cursor.fetchone()

        assert row is not None
        assert row[1] == profile_id  # profile_id
        assert row[2] == "/path/to/image.jpg"  # image_path
        assert row[3] == 10.5  # scale_factor

    def test_save_detected_items(self, db):
        """Test saving detected items"""
        profile_id = db.create_profile("Test User", "coder", "right")
        scan_id = db.save_scan(profile_id, "/path/to/image.jpg", 10.0, '[]')

        items = [
            {
                'item_slug': 'keyboard',
                'x_pos': 10.0,
                'y_pos': 20.0,
                'width': 30.0,
                'height': 10.0,
                'confidence': 0.85
            },
            {
                'item_slug': 'mouse',
                'x_pos': 50.0,
                'y_pos': 25.0,
                'width': 5.0,
                'height': 8.0,
                'confidence': 0.78
            }
        ]

        db.save_detected_items(scan_id, items)

        # Verify items were saved
        with db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT COUNT(*) FROM detected_items WHERE scan_id = ?",
                (scan_id,)
            )
            count = cursor.fetchone()[0]

        assert count == 2

    def test_get_ergonomic_rules(self, db):
        """Test getting ergonomic rules for a role"""
        rules = db.get_ergonomic_rules("coder")
        assert len(rules) > 0

        # Check that rules are ordered by priority
        priorities = [rule[6] for rule in rules]  # priority_level column
        assert priorities == sorted(priorities)

    def test_get_ergonomic_rules_case_insensitive(self, db):
        """Test that role is case-insensitive"""
        rules_lower = db.get_ergonomic_rules("coder")
        rules_upper = db.get_ergonomic_rules("CODER")
        assert len(rules_lower) == len(rules_upper)

    def test_get_ergonomic_rules_invalid_role(self, db):
        """Test getting rules for non-existent role"""
        rules = db.get_ergonomic_rules("nonexistent")
        assert len(rules) == 0

    def test_connection_error_handling(self, temp_dir):
        """Test database connection error handling"""
        # Try to create database in non-existent directory with strict permissions
        invalid_path = "/root/impossible/path/db.db"
        with pytest.raises(Exception):
            DatabaseManager(invalid_path)

    def test_multiple_profiles_same_name(self, db):
        """Test that multiple profiles can have the same name"""
        id1 = db.create_profile("John Doe", "coder", "right")
        id2 = db.create_profile("John Doe", "artist", "left")

        assert id1 != id2
        profiles = db.get_profiles()
        assert len(profiles) == 2

    def test_profile_name_trimming(self, db):
        """Test that profile names are trimmed"""
        profile_id = db.create_profile("  Test User  ", "coder", "right")

        with db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT name FROM profiles WHERE id = ?",
                (profile_id,)
            )
            name = cursor.fetchone()[0]

        assert name == "Test User"
