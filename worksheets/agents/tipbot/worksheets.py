import datetime
import os
from enum import Enum
from typing import List

from worksheets.agents.tipbot.common import (
    api_list,
    botname,
    prompt_dir,
    starting_prompt,
)
from worksheets.environment import Action, GenieField, GenieRuntime, GenieWorksheet

tipbot = GenieRuntime(
    botname, prompt_dir=prompt_dir, starting_prompt=starting_prompt, apis=api_list
)


class SubjectArea(str, Enum):
    academics = "academics"
    scitech = "Science and Technology"
    campus_life = "Campus Life"
    university = "University"
    sports = "Sports"
    arts_life = "Arts and Life"
    crime_safety = "Crime and Safety"
    other = "Other"


class ConfidentialityLevel(str, Enum):
    low = "low"
    medium = "medium"
    high = "high"
    absolute = "absolute"


class ContactMethod(str, Enum):
    email = "email"
    phone = "phone"
    social_media = "social_media"


class UrgencyLevel(str, Enum):
    low = "low"
    medium = "medium"
    high = "high"


@tipbot.geniews()
class Profile(GenieWorksheet):
    full_name = GenieField(
        str,
        "full_name",
        description="The full name of the person.",
        optional=True,
    )
    email = GenieField(
        str,
        "email",
        description="The email address of the person.",
        optional=True,
    )
    phone_number = GenieField(
        str,
        "phone_number",
        description="The phone number of the person.",
        optional=True,
    )
    affiliation = GenieField(
        str,
        "affiliation",
        description="The organization or company the person is affiliated with.",
        optional=True,
    )


@tipbot.geniews()
class Source(GenieWorksheet):
    profile = GenieField(
        Profile,
        "profile",
        description="The person who is the source.",
    )
    anonymous = GenieField(
        bool,
        "anonymous",
        description="Whether the source wishes to remain anonymous.",
        ask=False,
    )


@tipbot.geniews()
class Suspect(GenieWorksheet):
    profile = GenieField(
        Profile,
        "profile",
        description="The person who is suspected.",
    )
    description = GenieField(
        str,
        "description",
        description="A description of the suspect.",
    )


@tipbot.geniews()
class Tipster(GenieWorksheet):
    # profile = GenieField(
    #     Profile,
    #     "profile",
    #     description="The person giving the tip.",
    # )
    full_name = GenieField(
        str,
        "full_name",
        description="The full name of the tipster.",
        optional=True,
    )
    email = GenieField(
        str,
        "email",
        description="The email address of the tipster.",
        optional=True,
    )
    phone_number = GenieField(
        str,
        "phone_number",
        description="The phone number of the tipster.",
        optional=True,
    )
    affiliation = GenieField(
        str,
        "affiliation",
        description="The organization or company the tipster is affiliated with.",
        optional=True,
    )
    anonymous = GenieField(
        bool,
        "anonymous",
        description="Whether the person giving the tip wishes to remain anonymous.",
        ask=False,
        optional=True,
    )


class StoryType(str, Enum):
    campus_news = "Campus News"
    feature_profile = "Feature Profile"
    research_innovation = "Research and Innovation"
    opinion_column = "Opinion and Column"


@tipbot.geniews()
class CampusNewsStory(GenieWorksheet):
    people_involved = GenieField(
        List[Profile],
        "people_involved",
        description="The people involved in the story.",
    )
    news_location = GenieField(
        str,
        "news_location",
        description="The location of the story.",
    )
    date_of_event = GenieField(
        datetime.date,
        "date_of_event",
        description="The date of the event.",
    )
    time_of_event = GenieField(
        datetime.time,
        "time_of_event",
        description="The time of the event.",
    )
    contacts = GenieField(
        List[Profile],
        "contacts",
        description="The relevant contacts for the story.",
    )
    news_story = GenieField(
        str, "news_story", description="Detailed description of the campus news story"
    )


@tipbot.geniews()
class FeatureProfileStory(GenieWorksheet):
    feature_profile = GenieField(
        Profile,
        "feature_profile",
        description="The person who is the subject of the story.",
    )
    background_information = GenieField(
        str,
        "background_information",
        description="Background information about the person.",
    )
    achievements = GenieField(
        str,
        "achievements",
        description="The achievements of the person.",
    )
    reason_for_feature = GenieField(
        str,
        "reason_for_feature",
        description="The reason for the feature.",
    )


@tipbot.geniews()
class ResearchInnovationStory(GenieWorksheet):
    research_description = GenieField(
        str,
        "research_description",
        description="A description of the research.",
    )
    research_significance = GenieField(
        str,
        "research_significance",
        description="The significance of the research.",
    )
    research_impact = GenieField(
        str,
        "research_impact",
        description="The impact of the research.",
    )
    researchers_involved = GenieField(
        List[Profile],
        "researchers_involved",
        description="The researchers involved in the research.",
    )
    relevant_studies = GenieField(
        str,
        "relevant_studies",
        description="Any relevant studies.",
    )
    publications = GenieField(
        str,
        "publications",
        description="Any publications.",
    )


@tipbot.geniews()
class OpinionColumnStory(GenieWorksheet):
    issue_description = GenieField(
        str,
        "issue_description",
        description="A description of the issue.",
    )
    opinion = GenieField(
        str,
        "opinion",
        description="The opinion.",
    )
    relevant_experiences = GenieField(
        str,
        "relevant_experiences",
        description="Any relevant experiences.",
    )
    supporting_information = GenieField(
        str,
        "supporting_information",
        description="Any supporting information.",
    )


@tipbot.geniews(requires_confirmation=True, actions=Action("@send_tip(self.to_json())"))
class Tip(GenieWorksheet):
    tipster = GenieField(
        Tipster, "tipster", description="The person who is giving the tip"
    )
    story_type = GenieField(
        StoryType,
        "story_type",
        description="The type of story.",
    )
    campus_news_story = GenieField(
        CampusNewsStory,
        "campus_news_story",
        description="The campus news story.",
        predicate="story_type == 'Campus News'",
    )
    feature_profile_story = GenieField(
        FeatureProfileStory,
        "feature_profile_story",
        description="The feature profile story.",
        predicate="story_type == 'Feature Profile'",
    )
    research_innovation_story = GenieField(
        ResearchInnovationStory,
        "research_innovation_story",
        description="The research and innovation story.",
        predicate="story_type == 'Research and Innovation'",
    )
    opinion_column_story = GenieField(
        OpinionColumnStory,
        "opinion_column_story",
        description="The opinion and column story.",
        predicate="story_type == 'Opinion and Column'",
    )
    other_sources = GenieField(
        bool,
        "other_sources",
        description="Whether there are other sources.",
        ask=False,
    )
    other_sources_identity = GenieField(
        List[Source],
        "other_sources_identity",
        description="The person(s) or organization(s) that can provide additional information about the story.",
        predicate="other_sources == True",
    )
    additional_notes = GenieField(
        str,
        "additional_notes",
        description="Any additional notes or information that may be helpful in reporting the story.",
        optional=True,
    )
