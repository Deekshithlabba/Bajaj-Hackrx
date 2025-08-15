"""
Advanced Gemini API Manager with Multi-Key Support and Rate Limiting

This module provides intelligent API key management and rate limiting
for different Gemini services to optimize performance and avoid quotas.
"""

import time
import logging
import hashlib
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from collections import defaultdict
import google.generativeai as genai
from config import config

logger = logging.getLogger(__name__)

@dataclass
class APIKeyUsage:
    """Track usage statistics for an API key"""
    calls_made: int = 0
    last_call_time: datetime = field(default_factory=datetime.now)
    rate_limit_per_minute: int = 100  # Will be overridden per service
    errors_count: int = 0
    
    def can_make_call(self) -> bool:
        """Check if we can make another API call without hitting rate limits"""
        now = datetime.now()
        time_since_last = (now - self.last_call_time).total_seconds()
        
        # Reset counter if more than a minute has passed
        if time_since_last > 60:
            self.calls_made = 0
            
        # Allow call if we haven't hit the rate limit OR if enough time has passed
        if self.calls_made < self.rate_limit_per_minute:
            return True
            
        # If we've hit the limit, check if we should wait
        # Only wait if the last call was very recent (less than 60 seconds ago)
        if time_since_last < 60:
            return False  # Need to wait
        else:
            # More than 60 seconds have passed, reset and allow
            self.calls_made = 0
            return True
    
    def record_call(self, success: bool = True):
        """Record an API call"""
        self.calls_made += 1
        self.last_call_time = datetime.now()
        if not success:
            self.errors_count += 1


class GeminiAPIManager:
    """
    Advanced Gemini API Manager with intelligent key rotation and rate limiting
    
    Features:
    - Multi-API-key support for different services
    - Automatic rate limiting and quota management
    - Intelligent fallback between keys
    - Performance monitoring and optimization
    """
    
    def __init__(self):
        """Initialize the API manager with available keys"""
        self.service_keys = {
            'embedding': self._get_api_key('embedding'),
            'analyzer': self._get_api_key('analyzer'),
            'expert': self._get_api_key('expert'),
            'vision': self._get_api_key('vision')
        }
        
        # Track usage for each key (will set proper rate limits below)
        self.key_usage = defaultdict(APIKeyUsage)
        
        # Service-specific rate limits (calls per minute) - Mixed architecture
        self.rate_limits = {
            'embedding': 90,   # More aggressive but safe (100 RPM actual limit)
            'analyzer': 15,    # Gemini 2.0 Flash rate limit
            'expert': 15,      # Gemini 2.0 Flash rate limit  
            'vision': 15       # Gemini 2.0 Flash rate limit
        }
        
        # Daily quota tracking
        self.daily_usage = defaultdict(int)
        self.last_reset_date = datetime.now().date()
        
        # Embedding cache to avoid regenerating same content
        self.embedding_cache = {}
        self.cache_hits = 0
        self.cache_misses = 0
        
        self._initialize_models()
        self._initialize_rate_limits()
        logger.info(f"🔑 Gemini API Manager initialized with {len([k for k in self.service_keys.values() if k])} active keys")
    
    def _get_api_key(self, service: str) -> Optional[str]:
        """Get API key for a specific service with fallback logic"""
        service_key_map = {
            'embedding': config.GEMINI_EMBEDDING_API_KEY,
            'analyzer': config.GEMINI_ANALYZER_API_KEY,
            'expert': config.GEMINI_EXPERT_API_KEY,
            'vision': config.GEMINI_VISION_API_KEY
        }
        
        # Try service-specific key first, then fallback to master key
        return service_key_map.get(service) or config.GEMINI_MASTER_API_KEY
    
    def _initialize_models(self):
        """Initialize Gemini models for each service"""
        self.models = {}
        
        for service, api_key in self.service_keys.items():
            if api_key:
                try:
                    # Configure API key
                    genai.configure(api_key=api_key)
                    
                    # Initialize appropriate model
                    if service == 'embedding':
                        # Embedding service doesn't need a generative model
                        self.models[service] = None
                    elif service == 'analyzer':
                        self.models[service] = genai.GenerativeModel(config.TASK_ANALYZER_MODEL)
                    elif service == 'expert':
                        self.models[service] = genai.GenerativeModel(config.DOMAIN_EXPERT_MODEL)
                    elif service == 'vision':
                        self.models[service] = genai.GenerativeModel(config.VISION_MODEL)
                        
                    # Set rate limit for this key
                    if api_key in self.key_usage:
                        self.key_usage[api_key].rate_limit_per_minute = self.rate_limits.get(service, 15)
                        
                    logger.info(f"✅ {service.title()} service initialized with dedicated API key")
                    
                except Exception as e:
                    logger.warning(f"⚠️ Failed to initialize {service} service: {e}")
                    self.models[service] = None
    
    def _initialize_rate_limits(self):
        """Set proper rate limits for each service key"""
        for service, limit in self.rate_limits.items():
            api_key = self.service_keys.get(service)
            if api_key:
                # Set the correct rate limit for this service
                self.key_usage[api_key].rate_limit_per_minute = limit
                logger.info(f"🎯 Set {service} rate limit: {limit} RPM for key ...{api_key[-8:]}")
    
    def _wait_for_rate_limit(self, api_key: str, service: str):
        """Wait if we're approaching rate limits"""
        # Check daily quota for embedding service
        if service == 'embedding':
            self._check_daily_quota(api_key)
        
        usage = self.key_usage[api_key]
        
        # DEBUG: Log rate limit status
        logger.debug(f"🔍 DEBUG: Rate limit check for {service}: calls_made={usage.calls_made}, limit={usage.rate_limit_per_minute}")
        
        if not usage.can_make_call():
            wait_time = 60 - (datetime.now() - usage.last_call_time).total_seconds()
            if wait_time > 0:
                # Much shorter wait - spread calls over time instead of blocking
                smart_wait = min(wait_time, 1.0)  # Max 1 second wait
                logger.info(f"⏳ Rate limit reached for {service}. Brief wait: {smart_wait:.1f}s...")
                time.sleep(smart_wait)
        else:
            logger.debug(f"✅ Rate limit OK for {service}: {usage.calls_made}/{self.rate_limits.get(service)}")
    
    def _check_daily_quota(self, api_key: str):
        """Check if daily quota for embedding service is exceeded"""
        # Emergency bypass for testing
        if config.DISABLE_QUOTA_CHECK:
            logger.warning("🚨 QUOTA CHECK DISABLED FOR TESTING - Set DISABLE_QUOTA_CHECK=false to re-enable")
            return
        
        current_date = datetime.now().date()
        
        # Reset daily counter if new day
        if current_date != self.last_reset_date:
            self.daily_usage.clear()
            self.last_reset_date = current_date
            logger.info("📅 Daily quota counters reset for new day")
        
        # DEBUG: Log current usage for debugging
        current_usage = self.daily_usage[api_key]
        logger.info(f"🔍 DEBUG: Current daily usage for embedding: {current_usage}/{config.EMBEDDING_DAILY_QUOTA}")
        
        # Check daily usage for embedding service
        if current_usage >= config.EMBEDDING_DAILY_QUOTA:
            logger.error(f"🚨 DAILY QUOTA EXCEEDED: {current_usage}/{config.EMBEDDING_DAILY_QUOTA} embedding requests used today")
            logger.error("💡 Solutions: 1) Upgrade to paid tier, 2) Process tomorrow, 3) Reduce chunks")
            logger.error("🛠️ TEMP FIX: Set DISABLE_QUOTA_CHECK=true to test without quota limits")
            raise Exception(f"Daily embedding quota exceeded: {current_usage}/{config.EMBEDDING_DAILY_QUOTA}")
        
        # Show remaining quota
        remaining = config.EMBEDDING_DAILY_QUOTA - current_usage
        logger.info(f"✅ Daily quota OK: {remaining} requests remaining today")
        
        # Warn when approaching daily limit
        if current_usage > 0:
            usage_percentage = (current_usage / config.EMBEDDING_DAILY_QUOTA) * 100
            if usage_percentage > 80:
                logger.warning(f"⚠️ Approaching daily quota: {current_usage}/{config.EMBEDDING_DAILY_QUOTA} ({usage_percentage:.1f}%)")
    
    def generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings using optimized batch processing with caching"""
        api_key = self.service_keys['embedding']
        if not api_key:
            raise ValueError("No embedding API key available")
        
        # Configure for embedding service
        genai.configure(api_key=api_key)
        
        embeddings = []
        texts_to_process = []
        cache_indices = []
        
        # Check cache first to avoid redundant API calls
        for i, text in enumerate(texts):
            text_hash = hashlib.md5(text.encode()).hexdigest()
            if text_hash in self.embedding_cache:
                embeddings.append(self.embedding_cache[text_hash])
                self.cache_hits += 1
            else:
                embeddings.append(None)  # Placeholder
                texts_to_process.append(text)
                cache_indices.append(i)
                self.cache_misses += 1
        
        if not texts_to_process:
            logger.info(f"🎯 All {len(texts)} embeddings found in cache (100% cache hit rate)")
            return embeddings
        
        logger.info(f"📊 Cache stats: {self.cache_hits} hits, {self.cache_misses} misses ({len(texts_to_process)} new embeddings needed)")
        
        batch_size = config.EMBEDDING_BATCH_SIZE  # Now 20 instead of 5
        processed_embeddings = []
        
        # Process only uncached texts in batches
        for i in range(0, len(texts_to_process), batch_size):
            batch_texts = texts_to_process[i:i + batch_size]
            
            # Rate limiting (one call per batch instead of per text)
            self._wait_for_rate_limit(api_key, 'embedding')
            
            try:
                # Process entire batch in single API call
                if len(batch_texts) == 1:
                    # Single text
                    response = genai.embed_content(
                        model=config.EMBEDDING_MODEL,
                        content=batch_texts[0],
                        task_type="retrieval_document"
                    )
                    batch_embeddings = [response['embedding']]
                else:
                    # Multiple texts in batch
                    response = genai.embed_content(
                        model=config.EMBEDDING_MODEL,
                        content=batch_texts,
                        task_type="retrieval_document"
                    )
                    batch_embeddings = response['embedding'] if isinstance(response['embedding'][0], list) else [response['embedding']]
                
                # Cache new embeddings
                for text, embedding in zip(batch_texts, batch_embeddings):
                    text_hash = hashlib.md5(text.encode()).hexdigest()
                    self.embedding_cache[text_hash] = embedding
                
                processed_embeddings.extend(batch_embeddings)
                
                # Record successful call (one call for entire batch)
                self.key_usage[api_key].record_call(success=True)
                
                # Track daily usage (one call, not per text)
                self.daily_usage[api_key] += 1
                
                # Progress logging
                processed_count = min(i + batch_size, len(texts_to_process))
                logger.info(f"📊 Generated embeddings for {processed_count}/{len(texts_to_process)} new texts (batch {i//batch_size + 1})")
                    
            except Exception as e:
                logger.error(f"❌ Batch embedding generation failed for batch {i//batch_size + 1}: {e}")
                self.key_usage[api_key].record_call(success=False)
                
                # Fallback: Try individual texts in this batch
                logger.info(f"🔄 Trying individual texts for failed batch...")
                for text in batch_texts:
                    try:
                        self._wait_for_rate_limit(api_key, 'embedding')
                        response = genai.embed_content(
                            model=config.EMBEDDING_MODEL,
                            content=text,
                            task_type="retrieval_document"
                        )
                        embedding = response['embedding']
                        
                        # Cache the embedding
                        text_hash = hashlib.md5(text.encode()).hexdigest()
                        self.embedding_cache[text_hash] = embedding
                        
                        processed_embeddings.append(embedding)
                        self.key_usage[api_key].record_call(success=True)
                        self.daily_usage[api_key] += 1
                    except Exception as text_error:
                        logger.error(f"❌ Individual text embedding failed: {text_error}")
                        # Add zero vector as fallback
                        processed_embeddings.append([0.0] * config.EMBEDDING_DIMENSION)
        
        # Fill in the processed embeddings at correct positions
        processed_idx = 0
        for cache_idx in cache_indices:
            embeddings[cache_idx] = processed_embeddings[processed_idx]
            processed_idx += 1
        
        # Clean up cache if it gets too large (keep last 1000 entries)
        if len(self.embedding_cache) > 1000:
            # Remove oldest entries (simple cleanup)
            cache_items = list(self.embedding_cache.items())
            self.embedding_cache = dict(cache_items[-800:])  # Keep newest 800
        
        api_calls_saved = len(texts) - len(texts_to_process)
        logger.info(f"✅ Generated {len(embeddings)} embeddings with caching (saved {api_calls_saved} API calls)")
        return embeddings
    
    def generate_query_embedding(self, query: str) -> List[float]:
        """Generate embedding for a single query using proper embedding model"""
        api_key = self.service_keys['embedding']
        if not api_key:
            raise ValueError("No embedding API key available")
        
        genai.configure(api_key=api_key)
        self._wait_for_rate_limit(api_key, 'embedding')
        
        try:
            # Use proper embedding model
            response = genai.embed_content(
                model=config.EMBEDDING_MODEL,
                content=query,
                task_type="retrieval_query"
            )
            self.key_usage[api_key].record_call(success=True)
            return response['embedding']
            
        except Exception as e:
            logger.error(f"❌ Query embedding generation failed: {e}")
            self.key_usage[api_key].record_call(success=False)
            raise
    
    def analyze_task(self, prompt: str) -> str:
        """Use fast analyzer model for task analysis (Stage 1)"""
        api_key = self.service_keys['analyzer']
        model = self.models['analyzer']
        
        if not api_key or not model:
            raise ValueError("No analyzer API key or model available")
        
        genai.configure(api_key=api_key)
        self._wait_for_rate_limit(api_key, 'analyzer')
        
        try:
            response = model.generate_content(prompt)
            self.key_usage[api_key].record_call(success=True)
            return response.text
            
        except Exception as e:
            logger.error(f"❌ Task analysis failed: {e}")
            self.key_usage[api_key].record_call(success=False)
            raise
    
    def generate_expert_response(self, prompt: str) -> str:
        """Use high-quality expert model for final responses (Stage 2)"""
        api_key = self.service_keys['expert']
        model = self.models['expert']
        
        if not api_key or not model:
            raise ValueError("No expert API key or model available")
        
        genai.configure(api_key=api_key)
        self._wait_for_rate_limit(api_key, 'expert')
        
        try:
            response = model.generate_content(prompt)
            self.key_usage[api_key].record_call(success=True)
            return response.text
            
        except Exception as e:
            logger.error(f"❌ Expert response generation failed: {e}")
            self.key_usage[api_key].record_call(success=False)
            raise
    
    def process_vision(self, prompt: str, image_data) -> str:
        """Process image using vision model"""
        api_key = self.service_keys['vision']
        model = self.models['vision']
        
        if not api_key or not model:
            raise ValueError("No vision API key or model available")
        
        genai.configure(api_key=api_key)
        self._wait_for_rate_limit(api_key, 'vision')
        
        try:
            response = model.generate_content([prompt, image_data])
            self.key_usage[api_key].record_call(success=True)
            return response.text
            
        except Exception as e:
            logger.error(f"❌ Vision processing failed: {e}")
            self.key_usage[api_key].record_call(success=False)
            raise
    
    def get_usage_stats(self) -> Dict[str, Any]:
        """Get usage statistics for monitoring"""
        stats = {}
        
        for service, api_key in self.service_keys.items():
            if api_key and api_key in self.key_usage:
                usage = self.key_usage[api_key]
                stats[service] = {
                    'calls_made': usage.calls_made,
                    'last_call': usage.last_call_time.isoformat(),
                    'rate_limit': usage.rate_limit_per_minute,
                    'errors': usage.errors_count,
                    'available': usage.can_make_call()
                }
        
        return stats


# Global instance
gemini_api_manager = GeminiAPIManager()