from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Any
from pydantic import BaseModel
from loguru import logger
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from difflib import SequenceMatcher

class EventData(BaseModel):
    """Event data model exactly matching worksheet definition"""
    id: str                    # Matches GenieDB primary key
    summary: str               # Event title/summary
    start: datetime           # Start time
    end: datetime             # End time
    location: str             # Location/VRChat world
    description: str          # Event description


class EventStore:
    def __init__(self, credentials: Credentials, calendar_id: str = 'vrchateventsdotcom@gmail.com', private_calendar_id: str = 'primary'):
        self.credentials = credentials
        self.calendar_id = calendar_id # The public calendar ID - the one we want to read from
        self.private_calendar_id = private_calendar_id # The private calendar ID - the one we want to write to
        self._events: Dict[str, EventData] = {}
        self.last_sync: Optional[datetime] = None
        self.service = build('calendar', 'v3', credentials=credentials)
    
    def _convert_api_event(self, event: Dict) -> EventData:
        """Convert Google Calendar API event to our simplified format"""
        return EventData(
            id=event['iCalUID'],
            summary=event.get('summary', ''),
            start=datetime.fromisoformat(event['start'].get('dateTime', event['start'].get('date'))),
            end=datetime.fromisoformat(event['end'].get('dateTime', event['end'].get('date'))),
            location=event.get('location', ''),
            description=event.get('description', '')
        )
    
    def sync_events(self, force: bool = False) -> None:
        """Sync events from Google Calendar API - now synchronous"""
        # Only sync if forced or last sync was more than 5 minutes ago
        if not force and self.last_sync and (datetime.now(timezone.utc) - self.last_sync) < timedelta(minutes=5):
            logger.debug("Skipping sync - last sync was less than 5 minutes ago")
            return
            
        try:
            events_result = self.service.events().list(
                calendarId=self.calendar_id,
                timeMin=datetime.now(timezone.utc).isoformat(),
                singleEvents=True,
                orderBy='startTime'
            ).execute()
            
            self._events = {
                event['iCalUID']: self._convert_api_event(event)
                for event in events_result.get('items', [])
            }
            
            self.last_sync = datetime.now(timezone.utc)
            logger.info(f"Synced {len(self._events)} events from Google Calendar")
            
        except Exception as e:
            logger.error(f"Error syncing events: {e}")
            raise
    

    def list_events_from_primary(
        self,
        calendar_id: str = 'primary',
        timeMin: datetime = datetime.now(timezone.utc),
        singleEvents: bool = True,
        orderBy: str = 'startTime',
        ) -> List[EventData]:
        """List all events from Primary calendar"""
        events_result = self.service.events().list(
            calendarId=calendar_id,
            timeMin=timeMin.isoformat(),
            singleEvents=singleEvents,
            orderBy=orderBy
        ).execute()
        
        return [
            self._convert_api_event(event)
            for event in events_result.get('items', [])
       ]

    def add_event(
        self,
        summary: str,
        start: datetime,
        end: datetime,
        location: str,
        description: str,
        attendees: List[str] = ['vrchat.hhh@gmail.com'],
        note: Optional[str] = None
    ) -> EventData:
        """Add event - now synchronous"""
        try:
            event_data = {
                'summary': summary,
                'location': location,
                'description': f"{description}\n\nNote: {note}" if note else description,
                'start': {
                    'dateTime': start.isoformat(),
                    'timeZone': 'UTC',
                },
                'end': {
                    'dateTime': end.isoformat(),
                    'timeZone': 'UTC',
                },
                'attendees': [{'email': email} for email in attendees] if attendees else []
            }
            
            event = self.service.events().insert(
                calendarId=self.private_calendar_id, # Write to private calendar
                body=event_data,
                sendUpdates='all'
            ).execute()
            
            event_obj = self._convert_api_event(event)
            self._events[event_obj.id] = event_obj
            
            return event_obj
            
        except Exception as e:
            logger.error(f"Error adding event: {e}")
            raise
    

    def query_events(
        self, 
        filters: Optional[Dict[str, Any]] = None,
        time_range: Optional[tuple[datetime, datetime]] = None,
        keywords: Optional[List[str]] = None,
        location_prefix: Optional[str] = None,
        attendees: Optional[List[str]] = None,
        limit: Optional[int] = None
    ) -> List[EventData]:
        """Query events - now synchronous"""
        results = []
        
        for event in self._events.values():
            if time_range:
                start_time, end_time = time_range
                if not (start_time <= event.start <= end_time):
                    continue
            
            if keywords:
                event_text = f"{event.summary} {event.description}".lower()
                if not all(keyword.lower() in event_text for keyword in keywords):
                    continue
            
            if location_prefix:
                if not event.location.lower().startswith(location_prefix.lower()):
                    continue
            
            if filters:
                skip = False
                for field, value in filters.items():
                    if not hasattr(event, field):
                        skip = True
                        break
                    field_value = getattr(event, field)
                    
                    if isinstance(value, (list, tuple)):
                        if field_value not in value:
                            skip = True
                            break
                    elif isinstance(value, dict):
                        if 'gt' in value and field_value <= value['gt']:
                            skip = True
                            break
                        if 'lt' in value and field_value >= value['lt']:
                            skip = True
                            break
                        if 'gte' in value and field_value < value['gte']:
                            skip = True
                            break
                        if 'lte' in value and field_value > value['lte']:
                            skip = True
                            break
                    elif field_value != value:
                        skip = True
                        break
                if skip:
                    continue
            
            results.append(event)
        
        results.sort(key=lambda x: x.start)
        
        if limit:
            results = results[:limit]
        
        return results

    def get_upcoming_events(
        self, 
        days: int = 7, 
        location: Optional[str] = None,
        limit: Optional[int] = None
    ) -> List[EventData]:
        """Get upcoming events within specified days"""
        now = datetime.now(timezone.utc)
        time_range = (now, now + timedelta(days=days))
        
        filters = {}
        if location:
            filters['location'] = location
        
        return self.query_events(
            time_range=time_range,
            filters=filters,
            limit=limit
        )

    def search_text(
        self, 
        text: str,
        fields: Optional[List[str]] = None
    ) -> List[EventData]:
        """
        Search for events containing text in specified fields.
        
        Args:
            text: Text to search for
            fields: List of fields to search in. Defaults to ['summary', 'description', 'location']
        """
        if fields is None:
            fields = ['summary', 'description', 'location']
            
        results = []
        search_text = text.lower()
        
        for event in self._events.values():
            for field in fields:
                if not hasattr(event, field):
                    continue
                    
                field_value = str(getattr(event, field)).lower()
                if search_text in field_value:
                    results.append(event)
                    break
        
        return sorted(results, key=lambda x: x.start)

    def query_by_example(
        self, 
        example_event: EventData, 
        similarity_threshold: float = 0.7
    ) -> List[EventData]:
        """Find events similar to the provided example"""
        def similarity(a: str, b: str) -> float:
            return SequenceMatcher(None, a.lower(), b.lower()).ratio()
        
        results = []
        for event in self._events.values():
            # Check similarity of summary and description
            summary_sim = similarity(event.summary, example_event.summary)
            desc_sim = similarity(event.description, example_event.description)
            
            # Calculate average similarity
            avg_sim = (summary_sim + desc_sim) / 2
            
            if avg_sim >= similarity_threshold:
                results.append(event)
        
        return sorted(results, key=lambda x: x.start)

    def to_suql_format(self, events: List[EventData]) -> List[Dict]:
        """Convert events to SUQL-compatible format matching GenieDB structure"""
        return [{
            '_id': event.id,              # Primary key as defined in worksheet
            'id': event.id,               # Regular field
            'summary': event.summary,
            'start': event.start,
            'end': event.end,
            'location': event.location,
            'description': event.description
        } for event in events]