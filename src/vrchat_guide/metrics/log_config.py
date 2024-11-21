from pathlib import Path

class LogConfig:
    def __init__(self, base_dir: str = "logs"):
        self.base_dir = Path(base_dir)
        self.metrics_dir = self.base_dir / "metrics"
        self.conversation_dir = self.base_dir / "conversation"  
        self.debug_dir = self.base_dir / "debug"
        self.prompts_dir = self.base_dir / "prompts"
        
        # Create all directories
        for dir in [self.metrics_dir, self.conversation_dir, 
                   self.debug_dir, self.prompts_dir]:
            dir.mkdir(parents=True, exist_ok=True)
            
    def get_session_path(self, session_timestamp: str, log_type: str) -> Path:
        """Get path for specific session log file"""
        type_dir = getattr(self, f"{log_type}_dir")
        return type_dir / f"{log_type}_{session_timestamp}.json"