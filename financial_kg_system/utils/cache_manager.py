"""
Cache Management Layer
Implements Redis and NetworkX dual-cache strategy for optimal performance
"""

from typing import Dict, List, Any, Optional, Union
import redis
import networkx as nx
import json
import pickle
from datetime import datetime, timedelta
import hashlib
from functools import wraps


class CacheManager:
    """
    Dual-layer cache system combining Redis (distributed) and NetworkX (in-memory graph)
    for optimal performance in financial model calculations
    """
    
    def __init__(self, redis_host: str = "localhost", redis_port: int = 6379, 
                 redis_password: Optional[str] = None, graph_cache_ttl: int = 3600):
        """
        Initialize the dual cache system
        
        Args:
            redis_host: Redis server hostname
            redis_port: Redis server port 
            redis_password: Password if required
            graph_cache_ttl: Time-to-live for NetworkX graph caches in seconds
        """
        # Redis client for distributed caching
        self.redis_client = redis.Redis(
            host=redis_host,
            port=redis_port,
            password=redis_password,
            decode_responses=False,  # We'll handle serialization ourselves
            socket_connect_timeout=5,
            socket_timeout=5,
            health_check_interval=30
        )
        
        # NetworkX graph cache for dependency structures (fast in-memory operations)
        self.graph_cache: Dict[str, nx.DiGraph] = {}
        self.graph_cache_metadata: Dict[str, Dict[str, Any]] = {}
        self.graph_cache_ttl = graph_cache_ttl
        
        # Initialize Redis connection
        try:
            self.redis_client.ping()
        except redis.ConnectionError:
            raise ConnectionError("Unable to connect to Redis server")
    
    def _generate_cache_key(self, key_prefix: str, identifiers: List[str]) -> str:
        """Generate a consistent cache key from prefix and identifiers"""
        id_str = "_".join(sorted(identifiers))
        full_str = f"{key_prefix}:{id_str}"
        hash_obj = hashlib.md5(full_str.encode())
        return f"{key_prefix}:{hash_obj.hexdigest()}"
    
    def _serialize_networkx_graph(self, graph: nx.DiGraph) -> bytes:
        """Serialize a NetworkX graph to bytes for storage"""
        return pickle.dumps(graph)
    
    def _deserialize_networkx_graph(self, data: bytes) -> nx.DiGraph:
        """Deserialize bytes back to a NetworkX graph"""
        return pickle.loads(data)
    
    def _serialize_value(self, value: Any) -> bytes:
        """Universal serializer for any value"""
        return json.dumps(value).encode('utf-8')
    
    def _deserialize_value(self, data: bytes) -> Any:
        """Universal deserializer for any value"""
        return json.loads(data.decode('utf-8'))
    
    def _is_graph_cache_valid(self, cache_key: str) -> bool:
        """
        Check if NetworkX graph cache is valid and not expired
        """
        if cache_key not in self.graph_cache_metadata:
            return False
        
        metadata = self.graph_cache_metadata[cache_key]
        expiry_time = metadata.get('expiry_time')
        
        if expiry_time:
            return datetime.now() < expiry_time
        
        return True
    
    def cache_graph(self, graph_name: str, graph: nx.DiGraph, tags: Optional[List[str]] = None) -> bool:
        """
        Cache a NetworkX graph in both in-memory and Redis caches
        
        Args:
            graph_name: Unique name for the graph
            graph: NetworkX DiGraph to cache
            tags: Optional list of tags for grouping/cache invalidation
            
        Returns:
            bool: True if successful
        """
        try:
            # Store in NetworkX in-memory cache
            self.graph_cache[graph_name] = graph.copy()
            self.graph_cache_metadata[graph_name] = {
                'created_at': datetime.now(),
                'expiry_time': datetime.now() + timedelta(seconds=self.graph_cache_ttl),
                'tags': tags or []
            }
            
            # Store in Redis as backup/fallback
            key = f"graph:{graph_name}"
            serialized_graph = self._serialize_networkx_graph(graph)
            self.redis_client.setex(key, self.graph_cache_ttl, serialized_graph)
            
            return True
        except Exception as e:
            print(f"Error caching graph {graph_name}: {str(e)}")
            return False
    
    def get_cached_graph(self, graph_name: str) -> Optional[nx.DiGraph]:
        """
        Retrieve a NetworkX graph from the dual cache
        
        Args:
            graph_name: Name of the graph to retrieve
            
        Returns:
            NetworkX DiGraph if found, None otherwise
        """
        # Check in-memory cache first
        if graph_name in self.graph_cache and self._is_graph_cache_valid(graph_name):
            return self.graph_cache[graph_name].copy()
        
        # Fall back to Redis cache
        key = f"graph:{graph_name}"
        try:
            serialized_data = self.redis_client.get(key)
            if serialized_data:
                graph = self._deserialize_networkx_graph(serialized_data)
                
                # Refresh in-memory cache if it was expired
                if graph_name in self.graph_cache_metadata:
                    self.graph_cache[graph_name] = graph.copy()
                    self.graph_cache_metadata[graph_name]['expiry_time'] = (
                        datetime.now() + timedelta(seconds=self.graph_cache_ttl)
                    )
                
                return graph
        except Exception as e:
            print(f"Error retrieving graph {graph_name} from Redis: {str(e)}")
        
        # Graph not found in either cache
        return None
    
    def invalidate_graph_cache(self, graph_name: str) -> bool:
        """Remove graph from both in-memory and Redis caches"""
        success = True
        
        # Remove from in-memory cache
        if graph_name in self.graph_cache:
            del self.graph_cache[graph_name]
        
        if graph_name in self.graph_cache_metadata:
            del self.graph_cache_metadata[graph_name]
        
        # Remove from Redis cache
        key = f"graph:{graph_name}"
        try:
            deleted = self.redis_client.delete(key)
            if deleted == 0:
                print(f"Attempted to delete missing graph cache: {key}")
        except Exception as e:
            print(f"Error deleting Redis key {key}: {str(e)}")
            success = False
        
        return success
    
    def cache_cell_values(self, cell_mapping: Dict[str, Any], ttl: int = 3600) -> bool:
        """
        Cache multiple cell values with a TTL in Redis
        
        Args:
            cell_mapping: Dictionary mapping cell IDs to their values
            ttl: Time-to-live in seconds
            
        Returns:
            bool: True if successful
        """
        try:
            pipe = self.redis_client.pipeline()
            
            for cell_id, value in cell_mapping.items():
                key = f"cell:{cell_id}"
                serialized_value = self._serialize_value({'value': value, 'timestamp': datetime.now().isoformat()})
                pipe.setex(key, ttl, serialized_value)
            
            pipe.execute()
            return True
        except Exception as e:
            print(f"Error caching cell values: {str(e)}")
            return False
    
    def get_cached_cell_values(self, cell_ids: List[str]) -> Dict[str, Any]:
        """
        Get multiple cell values from Redis cache
        
        Args:
            cell_ids: List of cell IDs to retrieve
            
        Returns:
            Dictionary mapping cell IDs to their values
        """
        result = {}
        keys = [f"cell:{cell_id}" for cell_id in cell_ids]
        
        try:
            values = self.redis_client.mget(keys)
            
            for i, cell_id in enumerate(cell_ids):
                value_data = values[i]
                if value_data:
                    try:
                        deserialized = self._deserialize_value(value_data)
                        result[cell_id] = deserialized.get('value')
                    except:
                        # If there's an error in deserialization, skip this value
                        continue
        except Exception as e:
            print(f"Error retrieving cell values from cache: {str(e)}")
        
        return result
    
    def cache_dependencies_for_calculation(self, cell_id: str, dependencies: List[str]) -> bool:
        """
        Cache dependencies for a cell to accelerate recalculation lookups
        """
        try:
            key = f"deps:{cell_id}"
            serialized_deps = self._serialize_value({'dependencies': dependencies, 'timestamp': datetime.now().isoformat()})
            self.redis_client.setex(key, 7200, serialized_deps)  # 2 hour expiry for dependencies
            return True
        except Exception as e:
            print(f"Error caching dependencies for {cell_id}: {str(e)}")
            return False
    
    def get_cached_dependencies(self, cell_id: str) -> List[str]:
        """
        Retrieve cached dependencies for a cell
        """
        try:
            key = f"deps:{cell_id}"
            value = self.redis_client.get(key)
            if value:
                deserialized = self._deserialize_value(value)
                return deserialized.get('dependencies', [])
        except Exception as e:
            print(f"Error retrieving dependencies for {cell_id}: {str(e)}")
        
        return []
    
    def cache_recalculation_result(self, change_signature: str, result: Dict[str, Any], ttl: int = 300) -> bool:
        """
        Cache recalculation results to accelerate similar changes in the future
        """
        try:
            key = f"recalc:{change_signature}"
            serialized_result = self._serialize_value(result)
            self.redis_client.setex(key, ttl, serialized_result)
            return True
        except Exception as e:
            print(f"Error caching recalculation result: {str(e)}")
            return False
    
    def get_cached_recalculation_result(self, change_signature: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve cached recalculation results
        """
        try:
            key = f"recalc:{change_signature}"
            value = self.redis_client.get(key)
            if value:
                return self._deserialize_value(value)
        except Exception as e:
            print(f"Error retrieving cached recalculation result: {str(e)}")
        
        return None
    
    def invalidate_tagged_caches(self, tags: List[str]) -> int:
        """
        Invalidate all caches associated with specific tags
        
        Args:
            tags: List of cache tags to invalidate
            
        Returns:
            Number of invalidated entries
        """
        invalidated_count = 0
        
        # Invalidate in-memory graph caches
        to_remove = []
        for graph_name, metadata in self.graph_cache_metadata.items():
            graph_tags = metadata.get('tags', [])
            if any(tag in graph_tags for tag in tags):
                to_remove.append(graph_name)
        
        for graph_name in to_remove:
            del self.graph_cache[graph_name]
            del self.graph_cache_metadata[graph_name]
            invalidated_count += 1
        
        # We could also implement Redis-based tagging for more sophisticated invalidation
        # but for this implementation, we'll focus on the most important caches
        
        return invalidated_count
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the cache system
        """
        # Count networkx graphs in memory
        graph_count = len(self.graph_cache)
        
        # Check Redis stats
        try:
            redis_info = self.redis_client.info()
            return {
                "networkx_graphs_cached": graph_count,
                "networkx_memory_keys": len(self.graph_cache_metadata),
                "redis_total_commands_processed": redis_info.get('total_commands_processed', 0),
                "redis_used_memory_human": redis_info.get('used_memory_human', 'N/A'),
                "redis_connected_clients": redis_info.get('connected_clients', 0),
                "active_redis_keys": self.redis_client.dbsize(),
            }
        except Exception as e:
            return {
                "networkx_graphs_cached": graph_count,
                "networkx_memory_keys": len(self.graph_cache_metadata),
                "redis_connection_error": str(e)
            }
    
    def cleanup_expired_cache_entries(self) -> int:
        """
        Force cleanup of expired cache entries
        """
        current_time = datetime.now()
        expired_keys = []
        
        # Delete expired NetworkX cache entries
        for graph_name, metadata in self.graph_cache_metadata.items():
            expiry_time = metadata.get('expiry_time')
            if expiry_time and current_time > expiry_time:
                expired_keys.append(graph_name)
        
        for graph_name in expired_keys:
            if graph_name in self.graph_cache:
                del self.graph_cache[graph_name]
            if graph_name in self.graph_cache_metadata:
                del self.graph_cache_metadata[graph_name]
                
        return len(expired_keys)


class DualCacheDependencyManager:
    """
    Higher-level manager that integrates both NetworkX graph cache and Redis value cache
    for optimal dependency tracking and calculation performance
    """
    
    def __init__(self, cache_manager: CacheManager):
        self.cache_manager = cache_manager
    
    def store_calculation_graph_with_cache(self, 
                                         model_id: str, 
                                         graph: nx.DiGraph, 
                                         cell_id_subset: Optional[List[str]] = None) -> bool:
        """
        Store a calculation graph with consideration for cell subset optimization
        """
        if cell_id_subset:
            # Cache only the subgraph of interest
            subgraph = graph.subgraph(cell_id_subset)
            cache_name = self._generate_subgraph_cache_name(model_id, cell_id_subset)
        else:
            # Cache the entire graph
            subgraph = graph
            cache_name = f"full_model:{model_id}"
        
        return self.cache_manager.cache_graph(cache_name, subgraph, tags=['calculation_graph', model_id])
    
    def get_calculation_graph_from_cache(self, 
                                       model_id: str, 
                                       cell_id_subset: Optional[List[str]] = None) -> Optional[nx.DiGraph]:
        """
        Retrieve a calculation graph from cache
        """
        if cell_id_subset:
            cache_name = self._generate_subgraph_cache_name(model_id, cell_id_subset)
        else:
            cache_name = f"full_model:{model_id}"
        
        return self.cache_manager.get_cached_graph(cache_name)
    
    def _generate_subgraph_cache_name(self, model_id: str, cell_ids: List[str]) -> str:
        """Generate a unique name for a subgraph based on the cell IDs involved"""
        sorted_ids = sorted(cell_ids)
        id_combo = ":".join(sorted_ids)
        hash_suffix = hashlib.md5(id_combo.encode()).hexdigest()[:8]
        return f"subgraph:{model_id}:{hash_suffix}"
    
    def store_cell_values_with_dependency_tracking(self, 
                                                  model_id: str, 
                                                  cell_values: Dict[str, Any]) -> bool:
        """
        Store cell values and track dependencies for potential later recalculations
        """
        success = True
        
        # Cache the values themselves
        if not self.cache_manager.cache_cell_values(cell_values):
            success = False
        
        # For each cell, cache its current value signature to detect changes
        for cell_id, value in cell_values.items():
            value_signature = hashlib.md5(str(value).encode()).hexdigest()
            dep_key = f"valsig:{cell_id}"
            try:
                self.cache_manager.redis_client.setex(dep_key, 86400, value_signature)  # 24 hrs
            except Exception:
                success = False
        
        return success
    
    def has_cell_values_changed(self, cell_id: str, new_value: Any) -> bool:
        """
        Check if a cell's value has changed from the last cached state
        """
        try:
            old_signature = self.cache_manager.redis_client.get(f"valsig:{cell_id}")
            new_signature = hashlib.md5(str(new_value).encode()).hexdigest()
            
            if old_signature is None:
                # No previous value cached, treat as though it changed
                return True
            
            return old_signature.decode('utf-8') != new_signature
        except Exception:
            # If there's any error, assume the value has changed to be safe
            return True
    
    def mark_dependent_cells_dirty(self, model_id: str, changed_cell_ids: List[str]) -> List[str]:
        """
        Find all cells that depend on the changed cells and mark them as needing recalculation
        Uses both cached dependency info and real-time graph analysis
        """
        # This would connect to the DependencyGraphBuilder for full dependency analysis
        # For this implementation, we'll outline the approach:
        dirty_cells = []
        
        # Use cached dependency info if available
        for cell_id in changed_cell_ids:
            cached_deps = self.cache_manager.get_cached_dependencies(cell_id)
            if cached_deps:
                dirty_cells.extend(cached_deps)
        
        # This method would typically connect to the graph database for the complete picture
        # as implemented in DependencyGraphBuilder.find_dependent_cells()
        
        return dirty_cells