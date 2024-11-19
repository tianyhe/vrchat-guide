from datetime import datetime
from typing import Dict, List, Optional, Any
import json
from pathlib import Path
import pandas as pd
from loguru import logger

class MetricsLogger:
    """Logger for tracking conversation metrics and system performance."""
    
    def __init__(self, output_dir: str = "logs/metrics"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.current_session: Optional[Dict] = None
        self.sessions: List[Dict] = []
        
    def start_session(self, user_id: str):
        """Start a new conversation session."""
        self.current_session = {
            "session_id": f"{user_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "user_id": user_id,
            "start_time": datetime.now(),
            "tasks": [],
            "current_task": None,
            "clarification_questions": 0,
            "total_queries": 0,
            "successful_queries": 0,
            "knowledge_retrievals": [],
            "response_times": [],
            "context_switches": 0
        }
    
    def start_task(self, task_type: str, task_description: str):
        """Start tracking a new task."""
        if self.current_session:
            self.current_session["current_task"] = {
                "task_type": task_type,
                "description": task_description,
                "start_time": datetime.now(),
                "steps": [],
                "clarification_questions": 0,
                "completed": False
            }
    
    def log_clarification(self):
        """Log when the system asks for clarification."""
        if self.current_session:
            self.current_session["clarification_questions"] += 1
            if self.current_session["current_task"]:
                self.current_session["current_task"]["clarification_questions"] += 1
    
    def log_query(self, query: str, successful: bool, response_time: float, context: Optional[Dict] = None):
        """Log information about a query."""
        if self.current_session:
            self.current_session["total_queries"] += 1
            if successful:
                self.current_session["successful_queries"] += 1
            self.current_session["response_times"].append(response_time)
            
            # Track context switches
            if context and self.current_session["tasks"]:
                last_task = self.current_session["tasks"][-1]
                if last_task.get("context") != context:
                    self.current_session["context_switches"] += 1
    
    def log_knowledge_retrieval(self, query: str, relevance_score: float):
        """Log knowledge retrieval attempts and their relevance."""
        if self.current_session:
            self.current_session["knowledge_retrievals"].append({
                "query": query,
                "relevance_score": relevance_score,
                "timestamp": datetime.now()
            })
    
    def complete_task(self, success: bool, notes: str = ""):
        """Mark the current task as complete."""
        if self.current_session and self.current_session["current_task"]:
            task = self.current_session["current_task"]
            task["end_time"] = datetime.now()
            task["duration"] = (task["end_time"] - task["start_time"]).total_seconds()
            task["completed"] = success
            task["notes"] = notes
            self.current_session["tasks"].append(task)
            self.current_session["current_task"] = None
    
    def end_session(self):
        """End the current session and save metrics."""
        if self.current_session:
            self.current_session["end_time"] = datetime.now()
            self.current_session["duration"] = (
                self.current_session["end_time"] - 
                self.current_session["start_time"]
            ).total_seconds()
            
            # Calculate session metrics
            self.current_session["metrics"] = {
                "total_duration": self.current_session["duration"],
                "avg_response_time": sum(self.current_session["response_times"]) / 
                    len(self.current_session["response_times"]) if self.current_session["response_times"] else 0,
                "task_completion_rate": len([t for t in self.current_session["tasks"] if t["completed"]]) / 
                    len(self.current_session["tasks"]) if self.current_session["tasks"] else 0,
                "query_success_rate": self.current_session["successful_queries"] / 
                    self.current_session["total_queries"] if self.current_session["total_queries"] else 0,
                "context_switches": self.current_session["context_switches"],
                "total_clarifications": self.current_session["clarification_questions"]
            }
            
            # Save session data
            self._save_session()
            self.sessions.append(self.current_session)
            self.current_session = None
    
    def _save_session(self):
        """Save the current session data to file."""
        if self.current_session:
            session_file = self.output_dir / f"session_{self.current_session['session_id']}.json"
            with open(session_file, 'w') as f:
                json.dump(self.current_session, f, default=str, indent=2)
    
    def export_metrics(self, format: str = 'csv') -> str:
        """Export all sessions metrics to CSV or JSON."""
        if not self.sessions:
            return "No sessions to export"
            
        metrics_data = []
        for session in self.sessions:
            metrics_data.append({
                "session_id": session["session_id"],
                "user_id": session["user_id"],
                "duration": session["duration"],
                "tasks_completed": len([t for t in session["tasks"] if t["completed"]]),
                "total_tasks": len(session["tasks"]),
                "clarification_questions": session["clarification_questions"],
                "query_success_rate": session["metrics"]["query_success_rate"],
                "avg_response_time": session["metrics"]["avg_response_time"],
                "context_switches": session["metrics"]["context_switches"]
            })
        
        if format == 'csv':
            df = pd.DataFrame(metrics_data)
            output_file = self.output_dir / "metrics_export.csv"
            df.to_csv(output_file, index=False)
            return str(output_file)
        else:
            output_file = self.output_dir / "metrics_export.json"
            with open(output_file, 'w') as f:
                json.dump(metrics_data, f, indent=2)
            return str(output_file)