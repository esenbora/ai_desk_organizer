import math
import json
import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from config import Config
from utils.logger import setup_logger

logger = setup_logger(__name__)

class ErgonomicEngine:
    def __init__(self, database_manager):
        self.db = database_manager
    
    def analyze_ergonomics(self, scan_id, role, desk_width_cm, desk_height_cm, handedness='right'):
        """
        Analyze detected items against ergonomic rules
        Returns recommendations and violations
        """
        # Get ergonomic rules for the role
        rules = self.db.get_ergonomic_rules(role)
        
        # Get detected items for this scan
        detected_items = self.get_detected_items(scan_id)
        
        recommendations = []
        violations = []
        
        for rule in rules:
            rule_id, role_slug, item_slug, min_dist, max_dist, ideal_angle, priority, advice_text, display_name = rule
            
            # Find items matching this rule
            matching_items = [item for item in detected_items if item['item_slug'] == item_slug]
            
            for item in matching_items:
                # Calculate distance from desk center (user position)
                distance = math.sqrt(item['x_pos']**2 + item['y_pos']**2)
                
                # Check if item violates rules
                violation = None
                
                if min_dist and distance < min_dist:
                    violation = {
                        'type': 'too_close',
                        'item': display_name,
                        'current_distance': distance,
                        'recommended_min': min_dist,
                        'advice': advice_text,
                        'priority': priority,
                        'item_data': item
                    }
                elif max_dist and distance > max_dist:
                    violation = {
                        'type': 'too_far',
                        'item': display_name,
                        'current_distance': distance,
                        'recommended_max': max_dist,
                        'advice': advice_text,
                        'priority': priority,
                        'item_data': item
                    }
                
                if violation:
                    violations.append(violation)
                    
                    # Calculate optimal position
                    optimal_distance = (min_dist + max_dist) / 2 if min_dist and max_dist else min_dist or max_dist
                    
                    # Calculate optimal position based on ideal angle and handedness
                    angle_rad = math.radians(ideal_angle or 0)
                    
                    # Adjust angle for left-handed users (mirror horizontally)
                    if handedness == 'left' and item_slug in ['mouse', 'keyboard']:
                        angle_rad = math.radians(-(ideal_angle or 0))
                    
                    optimal_x = optimal_distance * math.cos(angle_rad)
                    optimal_y = optimal_distance * math.sin(angle_rad)
                    
                    recommendations.append({
                        'item': display_name,
                        'current_pos': (item['x_pos'], item['y_pos']),
                        'optimal_pos': (optimal_x, optimal_y),
                        'move_vector': (optimal_x - item['x_pos'], optimal_y - item['y_pos']),
                        'advice': advice_text,
                        'priority': priority,
                        'violation_type': violation['type']
                    })
        
        # Sort by priority (1 = highest)
        recommendations.sort(key=lambda x: x['priority'])
        violations.sort(key=lambda x: x['priority'])
        
        return {
            'recommendations': recommendations,
            'violations': violations,
            'score': self.calculate_ergonomic_score(violations)
        }
    
    def get_detected_items(self, scan_id):
        """Get detected items for a scan"""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT item_slug, x_pos, y_pos, width, height, rotation, confidence
                FROM detected_items 
                WHERE scan_id = ?
            ''', (scan_id,))
            
            items = []
            for row in cursor.fetchall():
                items.append({
                    'item_slug': row[0],
                    'x_pos': row[1], 
                    'y_pos': row[2],
                    'width': row[3],
                    'height': row[4],
                    'rotation': row[5],
                    'confidence': row[6]
                })
            return items
    
    def calculate_ergonomic_score(self, violations):
        """
        Calculate ergonomic score (0-100)
        Higher priority violations reduce score more
        Now includes severity multiplier based on deviation magnitude
        """
        if not violations:
            return 100

        # Map priority to base penalty using Config
        penalty_map = {
            1: Config.PRIORITY_1_PENALTY,
            2: Config.PRIORITY_2_PENALTY,
            3: Config.PRIORITY_3_PENALTY
        }

        total_penalty = 0
        max_penalty = 0

        for violation in violations:
            priority = violation['priority']
            base_penalty = penalty_map.get(priority, Config.PRIORITY_3_PENALTY)

            # Calculate severity multiplier based on deviation
            severity_multiplier = self._calculate_severity_multiplier(violation)

            # Final penalty with severity adjustment
            penalty = base_penalty * severity_multiplier
            total_penalty += penalty
            max_penalty += base_penalty * 2.0  # Max possible is 2x multiplier

        score = max(0, 100 - (total_penalty / max_penalty * 100))
        return round(score, 1)

    def _calculate_severity_multiplier(self, violation):
        """
        Calculate severity multiplier based on how far off the item is
        Returns 1.0 for minor deviation, up to 2.0 for severe deviation
        """
        if violation['type'] == 'too_close':
            current = violation['current_distance']
            recommended = violation['recommended_min']
            deviation = (recommended - current) / recommended
        elif violation['type'] == 'too_far':
            current = violation['current_distance']
            recommended = violation['recommended_max']
            deviation = (current - recommended) / recommended
        else:
            return 1.0

        # Map deviation to multiplier
        # 0-10% deviation: 1.0x (minor)
        # 10-30% deviation: 1.0-1.5x (moderate)
        # 30-50% deviation: 1.5-2.0x (severe)
        # >50% deviation: 2.0x (critical)
        if deviation < 0.1:
            return 1.0
        elif deviation < 0.3:
            return 1.0 + (deviation - 0.1) * 2.5  # Linear interpolation
        elif deviation < 0.5:
            return 1.5 + (deviation - 0.3) * 2.5
        else:
            return 2.0
    
    def generate_overlay_data(self, recommendations, desk_width_cm, desk_height_cm):
        """
        Generate data for visual overlay
        Returns positions for arrows, zones, and labels
        """
        overlay_data = {
            'arrows': [],
            'zones': [],
            'labels': []
        }
        
        for rec in recommendations:
            current_x, current_y = rec['current_pos']
            optimal_x, optimal_y = rec['optimal_pos']
            
            # Convert to pixel coordinates (assuming desk center at 0,0)
            # This would need calibration data to convert properly
            
            overlay_data['arrows'].append({
                'from': (current_x, current_y),
                'to': (optimal_x, optimal_y),
                'color': 'green' if rec['priority'] <= 2 else 'yellow',
                'item': rec['item']
            })
            
            # Add warning zone for items that are too close
            if rec['violation_type'] == 'too_close':
                overlay_data['zones'].append({
                    'center': (current_x, current_y),
                    'radius': 30,  # cm
                    'color': 'red',
                    'alpha': 0.3,
                    'label': f'{rec["item"]} too close'
                })
            
            overlay_data['labels'].append({
                'position': (optimal_x, optimal_y),
                'text': rec['advice'],
                'color': 'white',
                'background': 'rgba(0,0,0,0.7)'
            })
        
        return overlay_data