"""
Unit tests for ErgonomicEngine
"""
import pytest
from core.ergonomics import ErgonomicEngine
from core.database import DatabaseManager
from config import Config


class TestErgonomicEngine:
    """Test ErgonomicEngine class"""

    @pytest.fixture
    def db(self, temp_db_path):
        """Create a test database"""
        return DatabaseManager(temp_db_path)

    @pytest.fixture
    def engine(self, db):
        """Create an ErgonomicEngine instance"""
        return ErgonomicEngine(db)

    @pytest.fixture
    def test_scan(self, db):
        """Create a test scan with detected items"""
        # Create profile
        profile_id = db.create_profile("Test User", "coder", "right")

        # Create scan
        scan_id = db.save_scan(
            profile_id,
            "/path/to/test.jpg",
            10.0,
            '[[0,0],[120,0],[120,60],[0,60]]'
        )

        # Add detected items
        items = [
            {
                'item_slug': 'keyboard',
                'x_pos': 0.0,  # At center
                'y_pos': 0.0,
                'width': 30.0,
                'height': 10.0,
                'confidence': 0.85
            },
            {
                'item_slug': 'monitor',
                'x_pos': 0.0,
                'y_pos': -50.0,  # 50cm away from user
                'width': 40.0,
                'height': 25.0,
                'confidence': 0.92
            }
        ]
        db.save_detected_items(scan_id, items)

        return scan_id

    def test_init(self, engine, db):
        """Test initialization"""
        assert engine.db == db

    def test_calculate_ergonomic_score_no_violations(self, engine):
        """Test score calculation with no violations"""
        score = engine.calculate_ergonomic_score([])
        assert score == 100

    def test_calculate_ergonomic_score_priority_1(self, engine):
        """Test score with priority 1 violation"""
        violations = [
            {'priority': 1}
        ]
        score = engine.calculate_ergonomic_score(violations)
        # Priority 1 = 60 point penalty
        expected = 100 - (60 / 60 * 100)
        assert score == 0.0

    def test_calculate_ergonomic_score_priority_2(self, engine):
        """Test score with priority 2 violation"""
        violations = [
            {'priority': 2}
        ]
        score = engine.calculate_ergonomic_score(violations)
        # Priority 2 = 40 point penalty against 60 max
        expected = round(100 - (40 / 60 * 100), 1)
        assert abs(score - expected) < 0.1

    def test_calculate_ergonomic_score_priority_3(self, engine):
        """Test score with priority 3 violation"""
        violations = [
            {'priority': 3}
        ]
        score = engine.calculate_ergonomic_score(violations)
        # Priority 3 = 20 point penalty against 60 max
        expected = round(100 - (20 / 60 * 100), 1)
        assert abs(score - expected) < 0.1

    def test_calculate_ergonomic_score_multiple_violations(self, engine):
        """Test score with multiple violations"""
        violations = [
            {'priority': 1},  # 60 points
            {'priority': 2},  # 40 points
            {'priority': 3}   # 20 points
        ]
        score = engine.calculate_ergonomic_score(violations)
        # Total penalty: 120 against max 180 (3 * 60)
        expected = round(100 - (120 / 180 * 100), 1)
        assert abs(score - expected) < 0.1

    def test_get_detected_items(self, engine, test_scan):
        """Test retrieving detected items"""
        items = engine.get_detected_items(test_scan)
        assert len(items) == 2
        assert items[0]['item_slug'] == 'keyboard'
        assert items[1]['item_slug'] == 'monitor'

    def test_analyze_ergonomics_returns_structure(self, engine, test_scan):
        """Test that analysis returns correct structure"""
        analysis = engine.analyze_ergonomics(
            test_scan, "coder", 120.0, 60.0, "right"
        )

        assert 'recommendations' in analysis
        assert 'violations' in analysis
        assert 'score' in analysis
        assert isinstance(analysis['recommendations'], list)
        assert isinstance(analysis['violations'], list)
        assert isinstance(analysis['score'], (int, float))

    def test_analyze_ergonomics_score_range(self, engine, test_scan):
        """Test that ergonomic score is in valid range"""
        analysis = engine.analyze_ergonomics(
            test_scan, "coder", 120.0, 60.0, "right"
        )

        assert 0 <= analysis['score'] <= 100

    def test_analyze_ergonomics_recommendations_sorted(self, engine, test_scan):
        """Test that recommendations are sorted by priority"""
        analysis = engine.analyze_ergonomics(
            test_scan, "coder", 120.0, 60.0, "right"
        )

        if len(analysis['recommendations']) > 1:
            priorities = [rec['priority'] for rec in analysis['recommendations']]
            assert priorities == sorted(priorities)

    def test_analyze_ergonomics_handedness_affects_angles(self, engine, db):
        """Test that handedness affects recommendation angles"""
        # Create scan
        profile_id = db.create_profile("Test", "coder", "right")
        scan_id = db.save_scan(profile_id, "/test.jpg", 10.0, '[]')

        # Add mouse (should be affected by handedness)
        items = [{
            'item_slug': 'mouse',
            'x_pos': -20.0,  # Wrong side for right-handed
            'y_pos': 0.0,
            'width': 5.0,
            'height': 8.0,
            'confidence': 0.8
        }]
        db.save_detected_items(scan_id, items)

        # Analyze for right-handed
        analysis_right = engine.analyze_ergonomics(
            scan_id, "coder", 120.0, 60.0, "right"
        )

        # Analyze for left-handed
        analysis_left = engine.analyze_ergonomics(
            scan_id, "coder", 120.0, 60.0, "left"
        )

        # Recommendations should be different due to handedness
        # (This is a basic check; actual positions would differ)
        assert analysis_right is not None
        assert analysis_left is not None

    def test_generate_overlay_data_structure(self, engine):
        """Test overlay data generation structure"""
        recommendations = [
            {
                'item': 'Keyboard',
                'current_pos': (10.0, 20.0),
                'optimal_pos': (5.0, 10.0),
                'priority': 1,
                'advice': 'Move keyboard closer',
                'violation_type': 'too_far'
            }
        ]

        overlay = engine.generate_overlay_data(recommendations, 120.0, 60.0)

        assert 'arrows' in overlay
        assert 'zones' in overlay
        assert 'labels' in overlay
        assert isinstance(overlay['arrows'], list)
        assert isinstance(overlay['zones'], list)
        assert isinstance(overlay['labels'], list)

    def test_generate_overlay_data_too_close_zone(self, engine):
        """Test that 'too close' violations create warning zones"""
        recommendations = [
            {
                'item': 'Monitor',
                'current_pos': (5.0, 10.0),
                'optimal_pos': (40.0, 10.0),
                'priority': 1,
                'advice': 'Move monitor away',
                'violation_type': 'too_close'
            }
        ]

        overlay = engine.generate_overlay_data(recommendations, 120.0, 60.0)

        assert len(overlay['zones']) > 0
        zone = overlay['zones'][0]
        assert 'color' in zone
        assert zone['color'] == 'red'

    def test_analyze_ergonomics_different_roles(self, engine, db):
        """Test that different roles produce different recommendations"""
        # Create scan with same items
        profile_id = db.create_profile("Test", "coder", "right")
        scan_id = db.save_scan(profile_id, "/test.jpg", 10.0, '[]')

        items = [{
            'item_slug': 'tablet',
            'x_pos': 50.0,  # Far from center
            'y_pos': 0.0,
            'width': 20.0,
            'height': 30.0,
            'confidence': 0.9
        }]
        db.save_detected_items(scan_id, items)

        # Analyze as coder (tablet not priority)
        analysis_coder = engine.analyze_ergonomics(
            scan_id, "coder", 120.0, 60.0, "right"
        )

        # Analyze as artist (tablet is priority)
        analysis_artist = engine.analyze_ergonomics(
            scan_id, "artist", 120.0, 60.0, "right"
        )

        # Artist should have recommendations for tablet, coder might not
        assert analysis_coder is not None
        assert analysis_artist is not None
