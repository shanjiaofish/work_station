import os
import time
import datetime
from typing import List, Dict, Any, Tuple
import googlemaps

from .base_service import BaseService
from models.exceptions import ValidationError, ExternalAPIError
from config.config import get_config

class GMapService(BaseService):
    """Service for Google Maps operations"""
    
    def __init__(self, api_key: str = None):
        super().__init__()
        self.config = get_config()
        self.api_key = api_key or self.config.GOOGLE_MAPS_API_KEY
        self.gmaps_client = None
        self.robot = None
        
        if not self.api_key:
            raise ValidationError("Google Maps API key is required")
            
        try:
            self.gmaps_client = googlemaps.Client(key=self.api_key)
        except Exception as e:
            raise ExternalAPIError(f"Failed to initialize Google Maps client: {str(e)}")
    
    def process_routes(self, origin: str, destinations: List[str]) -> Tuple[str, List[Dict[str, Any]]]:
        """Process multiple routes and generate screenshots"""
        if not origin or not origin.strip():
            raise ValidationError("Origin location is required")
            
        if not destinations:
            raise ValidationError("At least one destination is required")
        
        # Clean destinations
        destinations = [dest.strip() for dest in destinations if dest.strip()]
        if not destinations:
            raise ValidationError("No valid destinations provided")
        
        # Create session and directories
        session_id = f"session_{int(time.time())}"
        today_str = datetime.datetime.now().strftime("%Y-%m-%d")
        image_folder_path = os.path.join(
            self.config.SCREENSHOTS_FOLDER, 
            today_str, 
            session_id
        )
        os.makedirs(image_folder_path, exist_ok=True)
        
        try:
            # Initialize Google Maps robot
            robot_results = self._process_with_robot(origin, destinations, image_folder_path)
            
            # Format results for frontend
            results = []
            for robot_result in robot_results:
                screenshot_url = ""
                if "image_filename" in robot_result:
                    screenshot_url = f"screenshots/{today_str}/{session_id}/{robot_result['image_filename']}"
                
                results.append({
                    "origin": robot_result["origin"],
                    "destination": robot_result["destination"],
                    "distance": robot_result["distance"],
                    "image_filename": robot_result.get("image_filename", ""),
                    "image_local_path": robot_result.get("image_local_path", ""),
                    "screenshot_url": screenshot_url,
                    "duration": robot_result.get("duration", ""),
                    "travel_mode": robot_result.get("travel_mode", "driving")
                })
            
            return session_id, results
            
        except Exception as e:
            raise ExternalAPIError(f"Failed to process routes: {str(e)}")
    
    def _process_with_robot(self, origin: str, destinations: List[str], 
                          image_folder_path: str) -> List[Dict[str, Any]]:
        """Process routes using Google Maps robot"""
        try:
            # Import robot here to avoid circular imports
            from gmap_robot import GoogleMapsRobot
            
            robot = GoogleMapsRobot(headless=True)
            results = robot.process_multiple_routes(origin, destinations, image_folder_path)
            
            return results
            
        except Exception as e:
            raise ExternalAPIError(f"Google Maps robot processing failed: {str(e)}")
    
    def get_distance_matrix(self, origins: List[str], destinations: List[str], 
                           mode: str = "driving") -> Dict[str, Any]:
        """Get distance matrix using Google Maps API"""
        if not origins or not destinations:
            raise ValidationError("Origins and destinations are required")
        
        try:
            result = self.gmaps_client.distance_matrix(
                origins=origins,
                destinations=destinations,
                mode=mode,
                units="metric",
                language="zh-TW"
            )
            
            return result
            
        except Exception as e:
            raise ExternalAPIError(f"Failed to get distance matrix: {str(e)}")
    
    def geocode_address(self, address: str) -> Dict[str, Any]:
        """Geocode an address to get coordinates"""
        if not address or not address.strip():
            raise ValidationError("Address is required for geocoding")
        
        try:
            result = self.gmaps_client.geocode(address, language="zh-TW")
            
            if not result:
                raise ValidationError(f"No results found for address: {address}")
            
            return result[0]
            
        except ValidationError:
            raise
        except Exception as e:
            raise ExternalAPIError(f"Failed to geocode address: {str(e)}")
    
    def reverse_geocode(self, lat: float, lng: float) -> Dict[str, Any]:
        """Reverse geocode coordinates to get address"""
        try:
            result = self.gmaps_client.reverse_geocode((lat, lng), language="zh-TW")
            
            if not result:
                raise ValidationError(f"No results found for coordinates: {lat}, {lng}")
            
            return result[0]
            
        except ValidationError:
            raise
        except Exception as e:
            raise ExternalAPIError(f"Failed to reverse geocode coordinates: {str(e)}")
    
    def get_directions(self, origin: str, destination: str, 
                      mode: str = "driving") -> Dict[str, Any]:
        """Get directions between two points"""
        if not origin or not destination:
            raise ValidationError("Origin and destination are required")
        
        try:
            result = self.gmaps_client.directions(
                origin=origin,
                destination=destination,
                mode=mode,
                language="zh-TW",
                units="metric"
            )
            
            if not result:
                raise ValidationError(f"No routes found from {origin} to {destination}")
            
            return result[0]
            
        except ValidationError:
            raise
        except Exception as e:
            raise ExternalAPIError(f"Failed to get directions: {str(e)}")
    
    def get_place_details(self, place_id: str) -> Dict[str, Any]:
        """Get detailed information about a place"""
        if not place_id:
            raise ValidationError("Place ID is required")
        
        try:
            result = self.gmaps_client.place(
                place_id=place_id,
                language="zh-TW"
            )
            
            return result
            
        except Exception as e:
            raise ExternalAPIError(f"Failed to get place details: {str(e)}")
    
    def search_places(self, query: str, location: str = None, 
                     radius: int = 5000) -> List[Dict[str, Any]]:
        """Search for places using text search"""
        if not query:
            raise ValidationError("Search query is required")
        
        try:
            result = self.gmaps_client.places(
                query=query,
                location=location,
                radius=radius,
                language="zh-TW"
            )
            
            return result.get('results', [])
            
        except Exception as e:
            raise ExternalAPIError(f"Failed to search places: {str(e)}")
    
    @staticmethod
    def get_origin_city(origin: str) -> str:
        """Extract city name from full origin address"""
        city_keywords = [
            "台北市", "新北市", "桃園市", "台中市", "台南市", "高雄市",
            "基隆市", "新竹市", "嘉義市", "宜蘭縣", "新竹縣", "苗栗縣",
            "彰化縣", "南投縣", "雲林縣", "嘉義縣", "屏東縣", "花蓮縣",
            "台東縣", "澎湖縣", "金門縣", "連江縣"
        ]
        
        for city in city_keywords:
            if city in origin:
                return city
        
        return ""
    
    def validate_locations(self, locations: List[str]) -> List[Dict[str, Any]]:
        """Validate that locations can be geocoded"""
        results = []
        
        for location in locations:
            try:
                geocode_result = self.geocode_address(location)
                results.append({
                    "location": location,
                    "valid": True,
                    "formatted_address": geocode_result.get("formatted_address", ""),
                    "coordinates": geocode_result.get("geometry", {}).get("location", {})
                })
            except Exception as e:
                results.append({
                    "location": location,
                    "valid": False,
                    "error": str(e)
                })
        
        return results