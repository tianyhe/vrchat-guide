import time
import json
from typing import Optional, Dict
from vrchat_guide.metrics.logger import MetricsLogger
from worksheets.modules import CurrentDialogueTurn
from vrchat_guide.metrics.log_config import LogConfig

class MetricsManager:
    """Manager class to handle metrics logging for the VRChat Guide."""
    
    def __init__(self, metrics_dir: str, session_timestamp: str):
        self.logger = MetricsLogger(
            output_dir=metrics_dir,
            session_timestamp=session_timestamp
        )
        self.log_config = LogConfig()
        self.prompts_file = self.log_config.get_session_path(session_timestamp, "prompts")
        self.current_task: Optional[str] = None
        self.task_start_time: Optional[float] = None
    
    def detect_task_type(self, dialogue_turn: CurrentDialogueTurn) -> Optional[str]:
        """Detect the type of task from the dialogue turn."""
        user_utterance = dialogue_turn.user_utterance.lower()
        
        # Task type detection logic
        if any(word in user_utterance for word in ["profile", "preferences", "settings"]):
            return "profile_update"
        elif any(word in user_utterance for word in ["event", "activity", "session"]):
            return "event_search"
        elif "add" in user_utterance and "calendar" in user_utterance:
            return "calendar_add"
        return "general_query"
    
    def detect_clarification(self, dialogue_turn: CurrentDialogueTurn) -> bool:
        """Detect if the system is asking for clarification."""
        if dialogue_turn.system_action:
            for action in dialogue_turn.system_action.actions:
                if "ask" in str(action).lower() or "clarif" in str(action).lower():
                    return True
        return False
    
    def handle_dialogue_turn(self, dialogue_turn: CurrentDialogueTurn, response_time: float):
        """Process a dialogue turn and log relevant metrics."""
        # Detect task type if no current task
        if not self.current_task:
            task_type = self.detect_task_type(dialogue_turn)
            if task_type:
                self.current_task = task_type
                self.logger.start_task(task_type, dialogue_turn.user_utterance)
        
        # Log query
        successful = True if dialogue_turn.system_response else False
        self.logger.log_query(
            query=dialogue_turn.user_utterance,
            successful=successful,
            response_time=response_time,
            context={"task_type": self.current_task} if self.current_task else None
        )
        
        # Check for clarifications
        if self.detect_clarification(dialogue_turn):
            self.logger.log_clarification()
        
        # Check for task completion
        if self._is_task_complete(dialogue_turn):
            self.logger.complete_task(
                success=True,
                notes=f"Completed task: {self.current_task}"
            )
            self.current_task = None
        
        # Log the prompt details
        self.log_prompt(dialogue_turn)
    
    def log_prompt(self, dialogue_turn: CurrentDialogueTurn):
        """Log the prompt details."""
        prompt_data = {
            "user_utterance": dialogue_turn.user_utterance,
            "system_response": dialogue_turn.system_response,
            "user_target_sp": dialogue_turn.user_target_sp,
            "user_target": dialogue_turn.user_target,
            "user_target_suql": dialogue_turn.user_target_suql,
        }
        
        # Read existing prompts or initialize empty array
        try:
            with open(self.prompts_file, 'r') as f:
                prompts = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            prompts = []
        
        # Append new prompt
        prompts.append(prompt_data)
        
        # Write back entire array with proper formatting
        with open(self.prompts_file, 'w') as f:
            json.dump(prompts, f, indent=2)
    
    def _is_task_complete(self, dialogue_turn: CurrentDialogueTurn) -> bool:
        """Detect if the current task is complete based on common response patterns."""
        if not self.current_task:
            return False
            
        response = dialogue_turn.system_response.lower()
        
        # Calendar task completion indicators
        calendar_markers = [
            "added to your calendar",
            "you'll receive a reminder",
            "i've added the"
        ]
        
        # General completion indicators 
        general_markers = [
            "all set",
            "completed",
            "done",
            "I've confirmed",
            "anything else",
            "let me know if",
            "feel free to",
            "need any more help",
            "would you like me to"
        ]
        
        # Check calendar-specific completions
        if self.current_task == "calendar_add":
            return any(marker in response for marker in calendar_markers)
        
        # Check general task completions
        return any(marker in response for marker in general_markers)