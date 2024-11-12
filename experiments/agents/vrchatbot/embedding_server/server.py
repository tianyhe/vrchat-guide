import os
from typing import Dict, List, Optional, Union
from pathlib import Path
from enum import Enum
from datetime import datetime

import faiss
import numpy as np
from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel
from sentence_transformers import SentenceTransformer
from loguru import logger
import psycopg2
from psycopg2.extras import RealDictCursor

class ContentType(str, Enum):
    EVENT = "event"
    GENERAL_INFO = "general_info"
    WORLD = "world"
    GUIDE = "guide"
    COMMUNITY = "community"
    CUSTOM = "custom"

class ContentSource(BaseModel):
    type: ContentType
    text: str
    metadata: Optional[dict] = None
    timestamp: datetime = datetime.now()

class SearchRequest(BaseModel):
    query: str
    content_types: Optional[List[ContentType]] = None
    top_k: int = 5
    min_score: float = 0.0

class VRChatEmbeddingServer:
    def __init__(
        self, 
        model_name: str = "all-MiniLM-L6-v2",
        db_config: dict = None,
        index_path: str = "embeddings",
        text_sources: Optional[Dict[str, str]] = None
    ):
        self.model = SentenceTransformer(model_name)
        self.indexes: Dict[str, faiss.IndexFlatL2] = {}
        self.text_store: Dict[str, List[ContentSource]] = {}
        self.db_config = db_config
        self.index_path = Path(index_path)
        self.index_path.mkdir(parents=True, exist_ok=True)
        self.text_sources = text_sources or {}
        
    def create_embeddings(self, texts: List[str]) -> np.ndarray:
        """Create embeddings for a list of texts."""
        return self.model.encode(texts, convert_to_tensor=False)
    
    def sync_with_database(self):
        """Sync embeddings with current database content."""
        try:
            with psycopg2.connect(**self.db_config) as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cur:
                    # Fetch all events
                    cur.execute("""
                        SELECT _id, summary, description, location, start_time, end_time 
                        FROM events 
                        WHERE end_time >= CURRENT_TIMESTAMP
                    """)
                    events = cur.fetchall()

                    # Create text content for indexing
                    for event in events:
                        text_content = (
                            f"Event: {event['summary']}\n"
                            f"Description: {event['description']}\n"
                            f"Location: {event['location']}\n"
                            f"Time: {event['start_time']} to {event['end_time']}"
                        )
                        self.add_content(
                            ContentSource(
                                type=ContentType.EVENT,
                                text=text_content,
                                metadata=event
                            )
                        )

            logger.info(f"Successfully synced {len(events)} events to embedding index")
            
        except Exception as e:
            logger.error(f"Error syncing with database: {e}")
            raise

    def load_text_sources(self):
        """Load and index content from text files."""
        try:
            for source_type, file_path in self.text_sources.items():
                if not os.path.exists(file_path):
                    logger.warning(f"Source file not found: {file_path}")
                    continue

                with open(file_path, 'r') as f:
                    content = f.read()

                # Split content into chunks for better search results
                chunks = self._chunk_text(content)
                
                for i, chunk in enumerate(chunks):
                    self.add_content(
                        ContentSource(
                            type=ContentType(source_type),
                            text=chunk,
                            metadata={
                                "source": file_path,
                                "chunk_id": i,
                                "total_chunks": len(chunks)
                            }
                        )
                    )

                logger.info(f"Loaded and indexed {len(chunks)} chunks from {file_path}")

        except Exception as e:
            logger.error(f"Error loading text sources: {e}")
            raise

    def _chunk_text(
        self, 
        text: str, 
        chunk_size: int = 1000, 
        overlap: int = 100
    ) -> List[str]:
        """Split text into overlapping chunks for better search."""
        chunks = []
        text_len = len(text)

        # If the text is small, return it as a single chunk
        if text_len <= chunk_size:
            return [text]

        start = 0
        while start < text_len:
            end = min(start + chunk_size, text_len)  # Ensure `end` doesn't exceed text length
            chunk = text[start:end]
            
            # Adjust chunk to end at a sentence boundary if possible
            if end < text_len:
                last_period = chunk.rfind('.')
                if last_period != -1 and last_period + 1 > chunk_size // 2:
                    end = start + last_period + 1
                    chunk = text[start:end]

            chunks.append(chunk)

            # Update `start` for the next chunk; ensure it advances sufficiently
            start = end - overlap if end - overlap > start else end

        return chunks


    
    def add_content(self, content: ContentSource):
        """Add content to appropriate index based on type."""
        collection = f"{content.type.value}_index"
        
        # Create embeddings for the text
        embedding = self.create_embeddings([content.text])
        
        # Initialize index if it doesn't exist
        if collection not in self.indexes:
            self.indexes[collection] = faiss.IndexFlatL2(embedding.shape[1])
            self.text_store[collection] = []
            
        # Add to FAISS index
        self.indexes[collection].add(embedding)
        self.text_store[collection].append(content)
        
        # Save metadata
        self._save_metadata(collection, len(self.text_store[collection]) - 1, content)
        
        return {"status": "success", "collection": collection}
    
    # def _save_metadata(self, collection: str, idx: int, content: ContentSource):
    #     """Save metadata for a content item."""
    #     metadata_path = self.index_path / f"{collection}_metadata.json"
    #     import json
        
    #     try:
    #         if metadata_path.exists():
    #             with open(metadata_path, "r") as f:
    #                 metadata = json.load(f)
    #         else:
    #             metadata = {}
            
    #         metadata[str(idx)] = {
    #             "type": content.type,
    #             "metadata": content.metadata if content.metadata is not None else {},  # default to empty dict if None
    #             "timestamp": content.timestamp.isoformat() if content.timestamp else ""  # default to empty string if None
    #         }
            
    #         with open(metadata_path, "w") as f:
    #             json.dump(metadata, f, indent=4)
                
    #     except Exception as e:
    #         logger.error(f"Error saving metadata: {e}")

    def _save_metadata(self, collection: str, idx: int, content: ContentSource):
        """Save metadata for a content item."""
        metadata_path = self.index_path / f"{collection}_metadata.json"
        import json

        def convert_datetime(obj):
            """Helper function to convert datetime objects to strings in metadata."""
            if isinstance(obj, dict):
                return {k: convert_datetime(v) for k, v in obj.items()}
            elif isinstance(obj, datetime):
                return obj.isoformat()
            return obj

        try:
            # Load existing metadata
            if metadata_path.exists():
                with open(metadata_path, "r") as f:
                    metadata = json.load(f)
            else:
                metadata = {}

            # Process metadata to convert datetime fields
            metadata[str(idx)] = {
                "type": content.type,
                "metadata": convert_datetime(content.metadata) if content.metadata else {},  # Converts any datetime in metadata
                "timestamp": content.timestamp.isoformat() if content.timestamp else ""  # Converts timestamp if not None
            }

            # Write to file
            with open(metadata_path, "w") as f:
                json.dump(metadata, f, indent=4)

        except Exception as e:
            logger.error(f"Error saving metadata: {e}")
    
    def search(
        self, 
        query: str, 
        content_types: Optional[List[ContentType]] = None,
        top_k: int = 5,
        min_score: float = 0.0
    ) -> List[Dict]:
        """Search for similar content across specified types."""
        query_embedding = self.create_embeddings([query])
        results = []
        
        # Determine which collections to search
        if content_types:
            collections = [f"{ct.value}_index" for ct in content_types]
        else:
            collections = list(self.indexes.keys())
            
        for collection in collections:
            if collection not in self.indexes:
                continue
                
            D, I = self.indexes[collection].search(query_embedding, top_k)
            
            # Load metadata
            metadata_path = self.index_path / f"{collection}_metadata.json"
            metadata_dict = {}
            if metadata_path.exists():
                import json
                with open(metadata_path, "r") as f:
                    metadata_dict = json.load(f)
            
            for score, idx in zip(D[0], I[0]):
                if score > min_score and idx < len(self.text_store[collection]):
                    content = self.text_store[collection][idx]
                    result = {
                        "text": content.text,
                        "score": float(score),
                        "type": content.type,
                        "collection": collection,
                        "metadata": content.metadata
                    }
                    
                    # Add saved metadata if available
                    if str(idx) in metadata_dict:
                        result["saved_metadata"] = metadata_dict[str(idx)]
                        
                    results.append(result)
                    
        # Sort by score across all collections
        results.sort(key=lambda x: x["score"])
        return results[:top_k]

# Initialize FastAPI app
app = FastAPI(title="VRChat Enhanced Embedding Server")

# Initialize embedding server with database config
db_config = {
    "host": os.getenv("POSTGRES_HOST", "localhost"),
    "port": os.getenv("POSTGRES_PORT", "5432"),
    "dbname": os.getenv("POSTGRES_DB", "vrchat_events"),
    "user": os.getenv("POSTGRES_USER", "vrchat_user"),
    "password": os.getenv("POSTGRES_PASSWORD"),
}

# Define text sources
text_sources = {
    "general_info": "data/vrchat_general_info.txt",
    "community": "data/vrchat_community_guidelines.txt",
    "guide": "data/vrchat_user_guide.txt"
}

embedding_server = VRChatEmbeddingServer(
    db_config=db_config,
    text_sources=text_sources
)

@app.on_event("startup")
async def startup_event():
    """Initial sync with database and load text sources on startup."""
    embedding_server.sync_with_database()
    embedding_server.load_text_sources()

@app.post("/search")
async def search(request: SearchRequest):
    """Search across multiple content types."""
    try:
        results = embedding_server.search(
            request.query,
            request.content_types,
            request.top_k,
            request.min_score
        )
        return {"results": results}
    except Exception as e:
        logger.error(f"Error searching: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/sync")
async def force_sync():
    """Force a sync with all sources."""
    try:
        embedding_server.sync_with_database()
        embedding_server.load_text_sources()
        return {"status": "success", "message": "Successfully synced all content"}
    except Exception as e:
        logger.error(f"Error syncing: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/content_types")
async def get_content_types():
    """Get available content types."""
    return {"content_types": [ct.value for ct in ContentType]}