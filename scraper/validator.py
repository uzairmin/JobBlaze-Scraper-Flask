from typing import List
from pydantic import BaseModel, HttpUrl, validator, Field
from enum import Enum


class SourceEnum(str, Enum):
    weworkremotely = "weworkremotely"
    dice = "dice"
    glassdoor = "glassdoor"
    builtin = "builtin"
    simplyhired = "simplyhired"
    remoteok = "remoteok"
    workable = "workable"
    ziprecruiter = "ziprecruiter"
    talent = "talent"
    justremote = "justremote"
    ycombinator = "ycombinator"
    rubyonremote = "rubyonremote"
    monster = "monster"
    indeed = "indeed"
    linkedin = "linkedin"


class JobLink(BaseModel):
    job_url: HttpUrl
    job_type: str


class ScraperData(BaseModel):
    source: SourceEnum
    links: List[JobLink] = Field(..., min_items=1)

    @validator("links", pre=False, each_item=True)
    def validate_links(cls, value):
        if not value:
            raise ValueError(
                'There must be at least one link in the "links" list.')
        return value
