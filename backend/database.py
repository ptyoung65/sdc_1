import os
import asyncpg
from typing import Optional, List, Dict, Any
from datetime import datetime
import json
import logging

logger = logging.getLogger(__name__)

class DatabaseService:
    def __init__(self):
        self.db_url = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/sdc")
        self.pool: Optional[asyncpg.Pool] = None
    
    async def initialize(self):
        """Initialize database connection pool"""
        try:
            self.pool = await asyncpg.create_pool(
                self.db_url,
                min_size=5,
                max_size=20,
                server_settings={
                    'jit': 'off'
                }
            )
            
            # Create tables if they don't exist
            await self._create_tables()
            
            logger.info("Database connection pool initialized")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize database: {str(e)}")
            return False
    
    async def _create_tables(self):
        """Create database tables"""
        if not self.pool:
            raise RuntimeError("Database pool not initialized")
            
        async with self.pool.acquire() as conn:
            # Users table
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    username VARCHAR(100) UNIQUE NOT NULL,
                    email VARCHAR(255) UNIQUE,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
                );
            """)
            
            # Conversations table
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS conversations (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
                    title VARCHAR(500),
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
                );
            """)
            
            # Messages table
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS messages (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    conversation_id UUID REFERENCES conversations(id) ON DELETE CASCADE,
                    role VARCHAR(20) NOT NULL CHECK (role IN ('user', 'assistant')),
                    content TEXT NOT NULL,
                    metadata JSONB,
                    sources JSONB,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
                );
            """)
            
            # Ratings table
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS message_ratings (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    message_id UUID REFERENCES messages(id) ON DELETE CASCADE,
                    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
                    rating INTEGER NOT NULL CHECK (rating >= 1 AND rating <= 5),
                    feedback TEXT,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(message_id, user_id)
                );
            """)
            
            # Create indexes
            await conn.execute("CREATE INDEX IF NOT EXISTS idx_conversations_user_id ON conversations(user_id);")
            await conn.execute("CREATE INDEX IF NOT EXISTS idx_messages_conversation_id ON messages(conversation_id);")
            await conn.execute("CREATE INDEX IF NOT EXISTS idx_messages_created_at ON messages(created_at);")
            await conn.execute("CREATE INDEX IF NOT EXISTS idx_ratings_message_id ON message_ratings(message_id);")
            
            logger.info("Database tables created successfully")
    
    async def create_user(self, username: str, email: Optional[str] = None) -> Optional[str]:
        """Create a new user and return user_id"""
        if not self.pool:
            return None
            
        try:
            async with self.pool.acquire() as conn:
                # Check if user exists
                existing_user = await conn.fetchrow(
                    "SELECT id FROM users WHERE username = $1", username
                )
                
                if existing_user:
                    return str(existing_user['id'])
                
                # Create new user
                user_id = await conn.fetchval(
                    "INSERT INTO users (username, email) VALUES ($1, $2) RETURNING id",
                    username, email
                )
                
                return str(user_id)
                
        except Exception as e:
            logger.error(f"Failed to create user: {str(e)}")
            return None
    
    async def get_or_create_user(self, username: str) -> Optional[str]:
        """Get existing user or create new one"""
        if not self.pool:
            return None
            
        try:
            async with self.pool.acquire() as conn:
                # Try to get existing user
                user = await conn.fetchrow(
                    "SELECT id FROM users WHERE username = $1", username
                )
                
                if user:
                    return str(user['id'])
                
                # Create new user
                user_id = await conn.fetchval(
                    "INSERT INTO users (username) VALUES ($1) RETURNING id",
                    username
                )
                
                return str(user_id)
                
        except Exception as e:
            logger.error(f"Failed to get or create user: {str(e)}")
            return None
    
    async def create_conversation(self, user_id: str, title: str = None) -> Optional[str]:
        """Create a new conversation"""
        if not self.pool:
            return None
            
        try:
            async with self.pool.acquire() as conn:
                conversation_id = await conn.fetchval(
                    "INSERT INTO conversations (user_id, title) VALUES ($1, $2) RETURNING id",
                    user_id, title
                )
                
                return str(conversation_id)
                
        except Exception as e:
            logger.error(f"Failed to create conversation: {str(e)}")
            return None
    
    async def save_message(
        self, 
        conversation_id: str, 
        role: str, 
        content: str,
        metadata: Dict[str, Any] = None,
        sources: List[Dict] = None
    ) -> Optional[str]:
        """Save a message to the database"""
        if not self.pool:
            return None
            
        try:
            async with self.pool.acquire() as conn:
                message_id = await conn.fetchval(
                    """INSERT INTO messages (conversation_id, role, content, metadata, sources) 
                       VALUES ($1, $2, $3, $4, $5) RETURNING id""",
                    conversation_id, 
                    role, 
                    content,
                    json.dumps(metadata) if metadata else None,
                    json.dumps(sources) if sources else None
                )
                
                return str(message_id)
                
        except Exception as e:
            logger.error(f"Failed to save message: {str(e)}")
            return None
    
    async def get_conversations(self, user_id: str, limit: int = 50, offset: int = 0) -> List[Dict]:
        """Get user's conversations with pagination"""
        if not self.pool:
            return []
            
        try:
            async with self.pool.acquire() as conn:
                rows = await conn.fetch(
                    """SELECT c.id, c.title, c.created_at, c.updated_at,
                              (SELECT COUNT(*) FROM messages WHERE conversation_id = c.id) as message_count
                       FROM conversations c 
                       WHERE c.user_id = $1 
                       ORDER BY c.updated_at DESC 
                       LIMIT $2 OFFSET $3""",
                    user_id, limit, offset
                )
                
                return [dict(row) for row in rows]
                
        except Exception as e:
            logger.error(f"Failed to get conversations: {str(e)}")
            return []
    
    async def get_conversations_count(self, user_id: str) -> int:
        """Get total count of user's conversations"""
        if not self.pool:
            return 0
            
        try:
            async with self.pool.acquire() as conn:
                count = await conn.fetchval(
                    "SELECT COUNT(*) FROM conversations WHERE user_id = $1",
                    user_id
                )
                
                return count or 0
                
        except Exception as e:
            logger.error(f"Failed to get conversations count: {str(e)}")
            return 0
    
    async def get_conversation_messages(self, conversation_id: str) -> List[Dict]:
        """Get messages for a conversation"""
        if not self.pool:
            return []
            
        try:
            async with self.pool.acquire() as conn:
                rows = await conn.fetch(
                    """SELECT m.id, m.role, m.content, m.metadata, m.sources, m.created_at,
                              r.rating, r.feedback
                       FROM messages m
                       LEFT JOIN message_ratings r ON m.id = r.message_id
                       WHERE m.conversation_id = $1
                       ORDER BY m.created_at ASC""",
                    conversation_id
                )
                
                messages = []
                for row in rows:
                    message = dict(row)
                    # Parse JSON fields
                    if message['metadata']:
                        message['metadata'] = json.loads(message['metadata'])
                    if message['sources']:
                        message['sources'] = json.loads(message['sources'])
                    messages.append(message)
                
                return messages
                
        except Exception as e:
            logger.error(f"Failed to get conversation messages: {str(e)}")
            return []
    
    async def rate_message(
        self, 
        message_id: str, 
        user_id: str, 
        rating: int, 
        feedback: str = None
    ) -> bool:
        """Rate a message (1-5 stars)"""
        if not self.pool:
            return False
            
        try:
            async with self.pool.acquire() as conn:
                await conn.execute(
                    """INSERT INTO message_ratings (message_id, user_id, rating, feedback)
                       VALUES ($1, $2, $3, $4)
                       ON CONFLICT (message_id, user_id) 
                       DO UPDATE SET rating = EXCLUDED.rating, 
                                     feedback = EXCLUDED.feedback,
                                     created_at = CURRENT_TIMESTAMP""",
                    message_id, user_id, rating, feedback
                )
                
                return True
                
        except Exception as e:
            logger.error(f"Failed to rate message: {str(e)}")
            return False
    
    async def get_message_rating(self, message_id: str, user_id: str) -> Optional[Dict]:
        """Get rating for a specific message by user"""
        if not self.pool:
            return None
            
        try:
            async with self.pool.acquire() as conn:
                row = await conn.fetchrow(
                    "SELECT rating, feedback, created_at FROM message_ratings WHERE message_id = $1 AND user_id = $2",
                    message_id, user_id
                )
                
                return dict(row) if row else None
                
        except Exception as e:
            logger.error(f"Failed to get message rating: {str(e)}")
            return None
    
    async def update_conversation_title(self, conversation_id: str, title: str) -> bool:
        """Update conversation title"""
        if not self.pool:
            return False
            
        try:
            async with self.pool.acquire() as conn:
                await conn.execute(
                    "UPDATE conversations SET title = $1, updated_at = CURRENT_TIMESTAMP WHERE id = $2",
                    title, conversation_id
                )
                
                return True
                
        except Exception as e:
            logger.error(f"Failed to update conversation title: {str(e)}")
            return False
    
    async def delete_conversation(self, conversation_id: str, user_id: str) -> bool:
        """Delete a conversation (only if owned by user)"""
        if not self.pool:
            return False
            
        try:
            async with self.pool.acquire() as conn:
                result = await conn.execute(
                    "DELETE FROM conversations WHERE id = $1 AND user_id = $2",
                    conversation_id, user_id
                )
                
                return result == "DELETE 1"
                
        except Exception as e:
            logger.error(f"Failed to delete conversation: {str(e)}")
            return False
    
    async def close(self):
        """Close database connection pool"""
        if self.pool:
            await self.pool.close()
            logger.info("Database connection pool closed")

# Global database service instance
db_service = DatabaseService()