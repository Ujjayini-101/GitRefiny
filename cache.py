"""Simple in-memory cache for repository analysis results."""
from typing import Optional, Dict
from datetime import datetime, timedelta
from models import AnalysisResult
import hashlib


class CacheManager:
    """Manages caching of analysis results with TTL."""
    
    def __init__(self, ttl_seconds: int = 3600):
        """
        Initialize cache manager.
        
        Args:
            ttl_seconds: Time-to-live for cache entries (default 1 hour)
        """
        self.cache: Dict[str, tuple] = {}  # key -> (result, expiry_time)
        self.ttl = timedelta(seconds=ttl_seconds)
    
    def _generate_key(self, repo_url: str) -> str:
        """
        Generate cache key from repository URL.
        
        Args:
            repo_url: Repository URL
        
        Returns:
            Cache key (hash of URL)
        """
        return hashlib.md5(repo_url.lower().encode()).hexdigest()
    
    def get_cached_analysis(self, repo_url: str) -> Optional[AnalysisResult]:
        """
        Retrieve cached analysis if available and not expired.
        
        Args:
            repo_url: Repository URL
        
        Returns:
            AnalysisResult if cached and valid, None otherwise
        """
        key = self._generate_key(repo_url)
        
        if key not in self.cache:
            return None
        
        result, expiry_time = self.cache[key]
        
        # Check if expired
        if datetime.now() > expiry_time:
            # Remove expired entry
            del self.cache[key]
            return None
        
        return result
    
    def cache_analysis(self, repo_url: str, analysis: AnalysisResult) -> None:
        """
        Cache analysis result with TTL.
        
        Args:
            repo_url: Repository URL
            analysis: AnalysisResult to cache
        """
        key = self._generate_key(repo_url)
        expiry_time = datetime.now() + self.ttl
        self.cache[key] = (analysis, expiry_time)
    
    def invalidate_cache(self, repo_url: str) -> None:
        """
        Invalidate cache entry for a repository.
        
        Args:
            repo_url: Repository URL
        """
        key = self._generate_key(repo_url)
        if key in self.cache:
            del self.cache[key]
    
    def clear_all(self) -> None:
        """Clear all cache entries."""
        self.cache.clear()
    
    def cleanup_expired(self) -> int:
        """
        Remove all expired cache entries.
        
        Returns:
            Number of entries removed
        """
        now = datetime.now()
        expired_keys = [
            key for key, (_, expiry) in self.cache.items()
            if now > expiry
        ]
        
        for key in expired_keys:
            del self.cache[key]
        
        return len(expired_keys)


# Global cache instance
cache_manager = CacheManager()
