
from scraper.portals import remoteok, workable, simplyhired, builtin, \
    dice,  weworkremotely as wwr, ziprecruiter, talent, justremote, ycombinator, \
    rubyonremote, monster, indeed, linkedin, glassdoor

PORTALS = {
    "weworkremotely": wwr.weworkremotely,
    "dice": dice.dice,
    "builtin": builtin.builtin,
    "simplyhired": simplyhired.simplyhired,
    "remoteok": remoteok.remoteok,
    "workable": workable.workable,
    "ziprecruiter": ziprecruiter.ziprecruiter,
    "talent": talent.talent,
    "justremote": justremote.just_remote,
    "rubyonremote": rubyonremote.ruby_on_remote,
    "ycombinator": ycombinator.ycombinator,
    "monster": monster.monster,
    "indeed": indeed.indeed,
    "linkedin": linkedin.linkedin,
    "glassdoor": glassdoor.glassdoor
}
