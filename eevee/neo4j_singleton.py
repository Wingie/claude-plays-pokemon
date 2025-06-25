"""
Neo4j Singleton for Eevee Memory System
Provides global scope Neo4j writer with proper lifecycle management
"""

import atexit
from typing import Optional
from neo4j_writer import Neo4jWriter


class Neo4jSingleton:
    """Singleton pattern for Neo4j writer with global scope and automatic cleanup"""
    
    _instance: Optional['Neo4jSingleton'] = None
    _writer: Optional[Neo4jWriter] = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            # Initialize the writer only once
            try:
                cls._writer = Neo4jWriter()
                # Register cleanup function to run on exit
                atexit.register(cls._cleanup)
            except Exception as e:
                print(f"⚠️ Failed to initialize Neo4j writer: {e}")
                cls._writer = None
        return cls._instance
    
    def get_writer(self) -> Optional[Neo4jWriter]:
        """Get the Neo4j writer instance"""
        return self._writer
    
    def is_available(self) -> bool:
        """Check if Neo4j writer is available and connected"""
        return self._writer is not None and self._writer.driver is not None
    
    def close(self) -> None:
        """Close the Neo4j writer connection"""
        if self._writer:
            self._writer.close()
            self._writer = None
    
    @classmethod
    def _cleanup(cls) -> None:
        """Cleanup function called on exit"""
        if cls._instance and cls._writer:
            try:
                cls._writer.close()
                cls._writer = None
                print("✅ Neo4j singleton cleaned up on exit")
            except Exception as e:
                print(f"⚠️ Error during Neo4j cleanup: {e}")


# Global function for easy access
def get_neo4j_writer() -> Optional[Neo4jWriter]:
    """Get the global Neo4j writer instance"""
    singleton = Neo4jSingleton()
    return singleton.get_writer()


def is_neo4j_available() -> bool:
    """Check if Neo4j is available globally"""
    singleton = Neo4jSingleton()
    return singleton.is_available()