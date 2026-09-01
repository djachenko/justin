from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


class Category(str, Enum):
    # General
    CIRCUS = "Circus"
    CONFERENCE = "Conference"
    EXHIBITION = "Exhibition"
    FAIR = "Fair"
    FESTIVAL = "Festival"
    FLASH_MOB = "Flash mob"
    HUMOR = "Humor"
    LECTURE = "Lecture, training, master class"
    LIVE_STREAM = "Live stream"
    MOVIE = "Movie"
    PARTY = "Party"
    PRESENTATION = "Presentation"
    SALE = "Sale"
    SPORTING_EVENTS = "Sporting events"
    TASTING = "Tasting"
    TOURNAMENT = "Tournament"
    # Concert
    BLUES = "Blues"
    CLASSICAL = "Classical"
    DANCE = "Dance"
    ELECTRONIC = "Electronic"
    FOLK = "Folk"
    INDIE = "Indie"
    JAZZ = "Jazz"
    LATIN_MUSIC = "Latin music"
    METAL = "Metal"
    OTHER = "Other"
    RNB = "R&B"
    RAP_HIP_HOP = "Rap, Hip-Hop"
    ROCK = "Rock"
    # Personal events
    BIRTHDAY = "Birthday"
    HOUSEWARMING_PARTY = "Housewarming Party"
    MEETING = "Meeting"
    WEDDING = "Wedding"
    # Recreation
    CAMPING = "Camping"
    GUIDED_TOUR = "Guided Tour"
    PICNIC = "Picnic"
    TRAVEL = "Travel"
    # Theatre
    BALLET_DANCING = "Ballet, Dancing"
    FOR_KIDS = "For kids"
    MUSICAL = "Musical"
    OPERA = "Opera"
    PLAY = "Play"


@dataclass
class EventStep1Settings:
    title: str
    start_dt: datetime
    is_closed: bool = True
    end_dt: datetime | None = None
    organiser_id: int | None = None


@dataclass
class EventStep2Settings:
    category: Category = Category.CIRCUS


@dataclass
class EventCreationSettings:
    step1: EventStep1Settings
    step2: EventStep2Settings = field(default_factory=EventStep2Settings)
