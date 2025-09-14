import logging
from typing import List, Dict, Any, Optional
from .base_service import BaseService
from models.exceptions import ValidationError, DatabaseError, NotFoundError

logger = logging.getLogger(__name__)

class MaterialService(BaseService):
    """Service for material-related operations"""
    
    def __init__(self, db_client):
        super().__init__(db_client)
        
    def search_materials(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Search materials by name"""
        if not query or not query.strip():
            raise ValidationError("Search query cannot be empty")
            
        try:
            response = self.db.table('materials').select(
                'material_id, material_name, carbon_footprint, declaration_unit'
            ).ilike('material_name', f'%{query.strip()}%').limit(limit).execute()
            
            return response.data if response.data else []
            
        except Exception as e:
            self.handle_db_error(e, "search materials")
    
    def batch_match_materials(self, queries: List[str]) -> List[Dict[str, Any]]:
        """Perform batch material matching"""
        if not queries:
            raise ValidationError("No queries provided for batch matching")
            
        results = []
        
        for query in queries:
            try:
                search_results = self.search_materials(query)
                
                # Format matches for frontend compatibility
                formatted_matches = []
                for material in search_results:
                    formatted_matches.append({
                        "name": self.safe_get(material, 'material_name', ''),
                        "id": self.safe_get(material, 'material_id', ''),
                        "carbon_footprint": self.safe_get(material, 'carbon_footprint', 0),
                        "declaration_unit": self.safe_get(material, 'declaration_unit', ''),
                        "score": self._calculate_match_score(query, material.get('material_name', ''))
                    })
                
                results.append({
                    "query": query,
                    "matches": formatted_matches,
                    "default": 0 if formatted_matches else None
                })
                
            except Exception as e:
                logger.error(f"Error matching query '{query}': {str(e)}")
                # Add empty result for failed query to maintain order
                results.append({
                    "query": query,
                    "matches": [],
                    "default": None
                })
        
        return results
    
    def create_material(self, material_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new material"""
        required_fields = ['material_name', 'carbon_footprint', 'declaration_unit']
        self.validate_required_fields(material_data, required_fields)
        
        # Validate numeric fields
        try:
            material_data['carbon_footprint'] = float(material_data['carbon_footprint'])
            if 'announcement_year' in material_data and material_data['announcement_year']:
                material_data['announcement_year'] = int(material_data['announcement_year'])
        except (ValueError, TypeError) as e:
            raise ValidationError("Invalid numeric values provided")
        
        try:
            response = self.db.table('materials').insert(material_data).execute()
            
            if not response.data:
                raise DatabaseError("Failed to create material - no data returned")
                
            return response.data[0]
            
        except Exception as e:
            self.handle_db_error(e, "create material")
    
    def list_materials(self, limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
        """List materials with pagination"""
        try:
            response = self.db.table('materials').select('*').range(offset, offset + limit - 1).execute()
            
            return response.data if response.data else []
            
        except Exception as e:
            self.handle_db_error(e, "list materials")
    
    def get_all_materials(self) -> List[Dict[str, Any]]:
        """Get all materials without pagination limits"""
        try:
            print("🚀 Starting to fetch ALL materials from database...")
            
            # First, get total count using a simple count query
            try:
                count_response = self.db.table('materials').select('material_id', count='exact').execute()
                total_count = count_response.count if hasattr(count_response, 'count') else 'unknown'
                print(f"📊 Database reports {total_count} total materials")
            except Exception as e:
                print(f"⚠️ Could not get count: {e}")
                total_count = 'unknown'
            
            # Fetch ALL materials using progressive pagination with improved logic
            all_materials = []
            batch_size = 500  # Reduced batch size for better Supabase compatibility
            current_offset = 0
            batch_number = 1
            consecutive_empty_batches = 0

            while True:
                print(f"🔄 Batch {batch_number}: Requesting range [{current_offset}, {current_offset + batch_size - 1}]")

                try:
                    # Use range() instead of offset() for Supabase Python client compatibility
                    response = self.db.table('materials').select('*').range(current_offset, current_offset + batch_size - 1).execute()

                    batch_data = response.data if response.data else []
                    batch_count = len(batch_data)

                    print(f"✅ Batch {batch_number}: Received {batch_count} materials (expected up to {batch_size})")

                    # If we get no data, increment empty batch counter
                    if batch_count == 0:
                        consecutive_empty_batches += 1
                        print(f"📭 Empty batch #{consecutive_empty_batches}")

                        # Stop only after getting 2 consecutive empty batches to be sure
                        if consecutive_empty_batches >= 2:
                            print("🏁 No more materials found (2 consecutive empty batches), stopping pagination")
                            break
                    else:
                        # Reset empty batch counter when we get data
                        consecutive_empty_batches = 0
                        all_materials.extend(batch_data)
                        print(f"📊 Total accumulated: {len(all_materials)} materials")

                    # Continue to next batch regardless of batch_count
                    # This fixes the issue where we stopped at 999 records
                    current_offset += batch_size
                    batch_number += 1

                    # Safety break for very large databases (increased for your 2,394+ materials)
                    if current_offset >= 50000:
                        print(f"⚠️ Safety limit: stopped at {current_offset} records to prevent timeouts")
                        break

                except Exception as batch_error:
                    print(f"❌ Error in batch {batch_number}: {batch_error}")
                    consecutive_empty_batches += 1
                    if consecutive_empty_batches >= 3:
                        print("❌ Too many consecutive errors, stopping pagination")
                        break
                    current_offset += batch_size
                    batch_number += 1
            
            final_count = len(all_materials)
            print(f"🎉 SUCCESS: Retrieved {final_count} materials total")
            
            if total_count != 'unknown' and final_count != total_count:
                print(f"⚠️ WARNING: Retrieved {final_count} but database has {total_count}")
            
            return all_materials
            
        except Exception as e:
            print(f"❌ CRITICAL ERROR in get_all_materials: {e}")
            import traceback
            print(f"Full traceback: {traceback.format_exc()}")
            self.handle_db_error(e, "get all materials")
    
    def get_material_by_id(self, material_id: str) -> Dict[str, Any]:
        """Get material by ID"""
        if not material_id:
            raise ValidationError("Material ID is required")
            
        try:
            response = self.db.table('materials').select('*').eq('material_id', material_id).execute()
            
            if not response.data:
                raise NotFoundError(f"Material with ID {material_id} not found")
                
            return response.data[0]
            
        except NotFoundError:
            raise
        except Exception as e:
            self.handle_db_error(e, "get material")
    
    def update_material(self, material_id: str, update_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update material by ID"""
        if not material_id:
            raise ValidationError("Material ID is required")
            
        # Validate numeric fields if present
        try:
            if 'carbon_footprint' in update_data:
                update_data['carbon_footprint'] = float(update_data['carbon_footprint'])
            if 'announcement_year' in update_data and update_data['announcement_year']:
                update_data['announcement_year'] = int(update_data['announcement_year'])
        except (ValueError, TypeError):
            raise ValidationError("Invalid numeric values provided")
        
        try:
            response = self.db.table('materials').update(update_data).eq('material_id', material_id).execute()
            
            if not response.data:
                raise NotFoundError(f"Material with ID {material_id} not found")
                
            return response.data[0]
            
        except NotFoundError:
            raise
        except Exception as e:
            self.handle_db_error(e, "update material")
    
    def delete_material(self, material_id: str) -> bool:
        """Delete material by ID"""
        if not material_id:
            raise ValidationError("Material ID is required")
            
        try:
            response = self.db.table('materials').delete().eq('material_id', material_id).execute()
            return True
            
        except Exception as e:
            self.handle_db_error(e, "delete material")
    
    def _calculate_match_score(self, query: str, material_name: str) -> float:
        """Calculate basic match score between query and material name"""
        if not query or not material_name:
            return 0.0
            
        query_lower = query.lower().strip()
        material_lower = material_name.lower().strip()
        
        # Simple scoring algorithm - can be improved with fuzzy matching
        if query_lower == material_lower:
            return 1.0
        elif query_lower in material_lower or material_lower in query_lower:
            return 0.8
        else:
            # Basic word overlap scoring
            query_words = set(query_lower.split())
            material_words = set(material_lower.split())
            
            if not query_words or not material_words:
                return 0.2
                
            overlap = len(query_words.intersection(material_words))
            total_words = len(query_words.union(material_words))
            
            return (overlap / total_words) * 0.7 + 0.1  # Base score + overlap score