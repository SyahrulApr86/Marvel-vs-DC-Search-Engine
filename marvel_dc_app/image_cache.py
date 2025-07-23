"""
Redis-based image caching service for Wikidata images
Caches both film posters and person profile images
"""
import redis
import json
import hashlib
import logging
from typing import Optional, Dict, Any
from django.conf import settings
import os

logger = logging.getLogger(__name__)

class ImageCacheService:
    """
    Redis-based caching service for Wikidata images
    """
    
    def __init__(self):
        self.redis_client = None
        self.cache_enabled = True
        self._connect_redis()
    
    def _connect_redis(self):
        """Initialize Redis connection with fallback to disabled caching"""
        try:
            redis_host = os.getenv('REDIS_HOST', 'localhost')
            redis_port = int(os.getenv('REDIS_PORT', 6379))
            redis_db = int(os.getenv('REDIS_DB', 0))
            redis_password = os.getenv('REDIS_PASSWORD', None)
            
            self.redis_client = redis.Redis(
                host=redis_host,
                port=redis_port,
                db=redis_db,
                password=redis_password,
                decode_responses=True,
                socket_timeout=5,
                socket_connect_timeout=5,
                retry_on_timeout=True
            )
            
            # Test connection
            self.redis_client.ping()
            logger.info("Redis cache connected successfully")
            
        except Exception as e:
            logger.warning(f"Redis connection failed: {e}. Caching disabled.")
            self.cache_enabled = False
            self.redis_client = None
    
    def _generate_cache_key(self, entity_uri: str, image_type: str) -> str:
        """Generate consistent cache key for entity URI and image type"""
        # Create a hash to handle long URIs
        uri_hash = hashlib.md5(entity_uri.encode()).hexdigest()
        return f"wikidata_image:{image_type}:{uri_hash}"
    
    def get_cached_image(self, entity_uri: str, image_type: str = 'film') -> Optional[str]:
        """
        Retrieve cached image URL for entity
        
        Args:
            entity_uri: Wikidata URI (e.g., http://www.wikidata.org/entity/Q123)
            image_type: Type of image ('film' or 'person')
            
        Returns:
            Image URL if cached, None otherwise
        """
        if not self.cache_enabled:
            return None
            
        try:
            cache_key = self._generate_cache_key(entity_uri, image_type)
            cached_data = self.redis_client.get(cache_key)
            
            if cached_data:
                data = json.loads(cached_data)
                logger.debug(f"Cache HIT for {entity_uri}")
                return data.get('image_url')
                
        except Exception as e:
            logger.error(f"Error retrieving cached image for {entity_uri}: {e}")
            
        return None
    
    def cache_image(self, entity_uri: str, image_url: Optional[str], 
                   image_type: str = 'film', ttl: int = 86400) -> bool:
        """
        Cache image URL for entity
        
        Args:
            entity_uri: Wikidata URI
            image_url: Image URL (can be None for entities without images)
            image_type: Type of image ('film' or 'person')
            ttl: Time to live in seconds (default 24 hours)
            
        Returns:
            True if cached successfully, False otherwise
        """
        if not self.cache_enabled:
            return False
            
        try:
            cache_key = self._generate_cache_key(entity_uri, image_type)
            cache_data = {
                'entity_uri': entity_uri,
                'image_url': image_url,
                'image_type': image_type,
                'cached_at': int(time.time()) if 'time' in globals() else 0
            }
            
            import time
            cache_data['cached_at'] = int(time.time())
            
            self.redis_client.setex(
                cache_key, 
                ttl, 
                json.dumps(cache_data)
            )
            
            logger.debug(f"Cache SET for {entity_uri} -> {image_url}")
            return True
            
        except Exception as e:
            logger.error(f"Error caching image for {entity_uri}: {e}")
            return False
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        if not self.cache_enabled:
            return {'enabled': False, 'message': 'Redis cache disabled'}
            
        try:
            info = self.redis_client.info()
            keys_count = len(self.redis_client.keys('wikidata_image:*'))
            
            return {
                'enabled': True,
                'redis_version': info.get('redis_version'),
                'used_memory_human': info.get('used_memory_human'),
                'connected_clients': info.get('connected_clients'),
                'cached_images': keys_count,
                'uptime_in_seconds': info.get('uptime_in_seconds')
            }
        except Exception as e:
            return {'enabled': False, 'error': str(e)}
    
    def clear_cache(self, image_type: Optional[str] = None) -> int:
        """
        Clear cached images
        
        Args:
            image_type: If specified, only clear this type ('film' or 'person')
                       If None, clear all cached images
            
        Returns:
            Number of keys deleted
        """
        if not self.cache_enabled:
            return 0
            
        try:
            if image_type:
                pattern = f'wikidata_image:{image_type}:*'
            else:
                pattern = 'wikidata_image:*'
                
            keys = self.redis_client.keys(pattern)
            if keys:
                deleted = self.redis_client.delete(*keys)
                logger.info(f"Cleared {deleted} cached images for type: {image_type or 'all'}")
                return deleted
            return 0
            
        except Exception as e:
            logger.error(f"Error clearing cache: {e}")
            return 0

# Global instance
image_cache = ImageCacheService()