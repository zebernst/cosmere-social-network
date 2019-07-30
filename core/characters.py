import re
from typing import Generator, Set, Optional, List, Dict

import mwparserfromhell as mwp
from mwparserfromhell.nodes.template import Template
from mwparserfromhell.nodes.wikilink import Wikilink

from core.constants import books, cleansed_fields, demonyms, info_fields, nations, species, titles
from utils.datastructures import CharacterLookup
from utils.logs import create_logger
from utils.regex import possession, punctuation
from utils.wiki import coppermind_query, extract_relevant_info


logger = create_logger('csn.core.characters')


class Character:
    """representation of a character in the Cosmere."""

    def __init__(self, query_result: dict):
        """construct character from coppermind.net api query results."""
        page = extract_relevant_info(query_result)

        self._keep: bool = True
        self._pageid: int = page['pageid']

        infobox = self._parse_infobox(page)
        self.name: str = page['title']
        self.common_name: str = infobox.pop('common_name', '')
        self.surname: str = infobox.pop('surname', '')
        self.unnamed: bool = True if 'unnamed' in infobox else False
        self.alive: bool = True if 'died' not in infobox else False

        self.aliases: Optional[List[str]] = infobox.pop('aliases', [])
        self.titles: Optional[List[str]] = infobox.pop('titles', [])

        self.world: Optional[str] = infobox.pop('world', None)
        self.books: Optional[List[str]] = infobox.pop('books', [])
        self.abilities: Optional[List[str]] = infobox.pop('abilities', [])

        self.residence: Optional[str] = infobox.pop('residence', None)
        self.nationality: Optional[str] = infobox.pop('nationality', None)
        self.ethnicity: Optional[str] = infobox.pop('ethnicity', None)
        self.species: Optional[str] = infobox.pop('species', None)
        self.subspecies: Optional[str] = infobox.pop('subspecies', None)

        self.family: Optional[str] = infobox.pop('family', None)
        self.relatives: Dict[str, List[str]] = {
            'bonded': infobox.pop('bonded', []),
            'spouse': infobox.pop('spouse', []),
            'parents': infobox.pop('parents', []),
            'children': infobox.pop('children', []),
            'siblings': infobox.pop('siblings', []),
            'ancestors': infobox.pop('ancestors', []),
            'descendants': infobox.pop('descendants', []),
            'others': infobox.pop('relatives', [])
        }

        self.misc = {
            # todo: fully parse these fields
            'profession': infobox.pop('profession', None),
            'groups': infobox.pop('groups', '')
        }

        # discard unofficial character pages
        if 'User:' in self.name:
            self._keep = False

        # sanitize name
        if '(' in self.name:
            self.misc['original_name'] = self.name
            self.name = re.sub(r"\s\([\w\s]+\)", '', self.name)

        if self._keep:
            logger.debug(f"Created  {self.name} ({self.world if self.world else 'Unknown'}).")
        else:
            logger.debug(f"Ignored {self.name} ({self.world if self.world else 'Unknown'}).")

    def __eq__(self, other):
        """return self == value."""
        if isinstance(other, self.__class__):
            return self._pageid == other._pageid
        else:
            return False

    def __ne__(self, other):
        """return self != value."""
        return not self.__eq__(other)

    def __hash__(self):
        """return hash(self._pageid)."""
        return hash(self._pageid)

    def __repr__(self):
        """return repr(self)."""
        return f"<{self.name} (#{self._pageid}): {self.world}>"

    def __str__(self):
        """return str(self)."""
        return self.name

    @property
    def id(self) -> int:
        return self._pageid

    @property
    def monikers(self) -> Set[str]:
        """return a set of monikers that the character is known by."""
        return set(n for n in [self.name, self.common_name, self.surname] + self.aliases + self.titles if n)

    @property
    def coppermind_url(self) -> str:
        """return the url of the character's page on coppermind.net"""
        return f"https://coppermind.net/wiki?curid={self._pageid}"

    @property
    def details(self) -> str:

        location = []
        if self.residence is not None:
            location.append(self.residence)
        if self.nationality is not None:
            nation = nations.get(self.nationality)
            if nation is not None:
                location.append(nation)
        location.append(self.world if self.world is not None else 'Unknown')
        location = ', '.join(location)

        species_ethnicity = []
        if self.ethnicity is not None:
            species_ethnicity.append(self.ethnicity)
        if self.species is not None:
            if self.subspecies is not None:
                species_ethnicity.append(self.subspecies)
            else:
                species_ethnicity.append(self.species)
        species_ethnicity = ' '.join(species_ethnicity) if species_ethnicity else ''

        physical_info = []
        if species_ethnicity:
            physical_info.append(species_ethnicity)
        if not self.alive:
            physical_info.append("deceased")

        return (
            f"{self.name} -- {location}"
            f"{f' (' + ', '.join(physical_info) + ')' if physical_info else ''}"
        )

    def _parse_infobox(self, result: dict) -> dict:
        """parse the wikitext infobox for character attributes"""

        content = result['content']
        char_name = result['title']

        # set defaults
        char_info = {}

        # define local utility functions
        def parse_markup(wikicode: mwp.wikicode.Wikicode):
            templates = wikicode.filter_templates()
            links = wikicode.filter_wikilinks()
            for t in templates:
                # remove references
                if 'ref' in t.name or 'wob' in t.name:
                    wikicode.remove(t)
            for l in links:
                # simplify links
                text = l.text if l.text else l.title
                wikicode.replace(l, Wikilink(text))

            # todo
            return wikicode

        def parse_names(wikicode: mwp.wikicode.Wikicode):
            wikicode = parse_markup(wikicode)
            for t in wikicode.filter(forcetype=Template):
                if len(t.params) == 1:
                    wikicode.replace(t, t.params[0])
                elif len(t.params) > 1:
                    if 'highprince' in t.params[0].lower():
                        wikicode.replace(t, "{0} of {1}".format(*t.params))
                    elif 'army' in t.params[0].lower():
                        wikicode.replace(t, "{1} {0}".format(*t.params))

            return [n for n in (n.strip() for n in wikicode.strip_code().split(',')) if n]

        def parse_books(wikicode: mwp.wikicode.Wikicode):
            return [b for b in (books.get(b.text.strip_code() if b.text else b.title.strip_code())
                                for b in wikicode.nodes
                                if isinstance(b, mwp.wikicode.Wikilink))
                    if b is not None]

        def parse_abilities(wikicode: mwp.wikicode.Wikicode):
            wikicode = parse_markup(wikicode)
            abilities = []
            for wc in wikicode.filter(forcetype=(Template, Wikilink)):
                if isinstance(wc, Template):
                    if 'tag' in wc.name:
                        params = tuple(p.lower()
                                       for p in (p.name.strip_code()
                                                 if p.showkey is True
                                                 else p.value.strip_code()
                                                 for p in wc.params)
                                       if p != 'cat')

                        if len(params) == 1:
                            abilities.append(params[0])
                        elif len(params) > 1:
                            if any(params[0] == s for s in ('shard', 'vessel', 'splinter')):
                                abilities.extend((params[0], f"{params[0]} of {params[1]}"))
                            elif params[0] == 'squire':
                                abilities.append(f'squire ({params[1].split()[-1]})')
                            else:
                                print("unknown ability while parsing character: ", params)

                elif isinstance(wc, Wikilink):
                    abilities.append(wc.title.strip_code().lower())

            return abilities

        def parse_profession(wikicode: mwp.wikicode.Wikicode):
            # todo: parse with simple NLP
            return str(wikicode.strip_code().lower().strip())

        def parse_groups(wikicode: mwp.wikicode.Wikicode):
            # todo: parse in same manner as parse_names
            return wikicode

        def parse_nation(wikicode: mwp.wikicode.Wikicode):
            return demonyms.get(wikicode.strip_code().lower().strip(), None)

        def parse_residence(wikicode: mwp.wikicode.Wikicode):
            wikicode = parse_markup(wikicode)
            wikicode_elements = wikicode.filter(forcetype=(Template, Wikilink))
            if "<br>" in wikicode:
                wikicode.replace("<br>", ", ")
            if not wikicode_elements:
                residence = wikicode.strip_code().strip()
            else:
                for wc in wikicode_elements:
                    if isinstance(wc, Wikilink):
                        wikicode.replace(wc, wc.title.strip_code().strip().title())
                    elif isinstance(wc, Template):
                        params = tuple(p
                                       for p in (p.name.strip_code()
                                                 if p.showkey is True
                                                 else p.value.strip_code()
                                                 for p in wc.params)
                                       if p != 'cat')
                        if len(params) == 1:
                            wikicode.replace(wc, params[0])
                        else:
                            wikicode.replace(wc, params)
                residence = wikicode.strip_code().strip()

            residence = re.sub(r"\s?\([\w\s]+\)", '', residence)
            # special cases
            if residence.startswith("15 Stranat Place"):
                residence = "Elendel"
            return residence

        def parse_ethnicity(wikicode: mwp.wikicode.Wikicode):
            wikicode = parse_markup(wikicode)
            wikicode_elements = wikicode.filter(forcetype=(Template, Wikilink))
            if ' and ' in wikicode:
                wikicode.replace(' and ', ', ')

            if not wikicode_elements:
                ethnicity = wikicode.strip_code().strip().title()
            else:
                for wc in wikicode_elements:
                    if isinstance(wc, Wikilink):
                        wikicode.replace(wc, wc.title.strip_code().strip())
                    elif isinstance(wc, Template):
                        params = tuple(p
                                       for p in (p.name.strip_code()
                                                 if p.showkey is True
                                                 else p.value.strip_code()
                                                 for p in wc.params)
                                       if p != 'cat')
                        if len(params) == 1:
                            wikicode.replace(wc, params[0])
                        elif 'Noble' in params or 'noble' in params:
                            wikicode.replace(wc, 'Noble')
                        else:
                            wikicode.replace(wc, params)
                ethnicity = wikicode.strip_code().strip().title()

            if ethnicity == 'Skaa, Noble':
                ethnicity = 'Half-Skaa'
            return ethnicity

        def parse_species(wikicode: mwp.wikicode.Wikicode):
            spec = species.get(wikicode.strip_code().lower().strip(), None)
            if spec is not None and any(s in val.lower() for s in ('spren', 'cryptic')):
                char_info['subspecies'] = spec
                spec = 'Spren'
            return spec

        def parse_family(wikicode: mwp.wikicode.Wikicode):
            wikicode = parse_markup(wikicode)

            links = [l for l in wikicode.filter_wikilinks() if 'category' not in l.lower()]
            if not links:
                print('unable to find family', wikicode)
                return None
            elif len(links) == 1:
                family = links[0].title.strip_code().strip()
            else:
                print('unexpected number of wikilinks', wikicode)
                for wc in links:
                    wikicode.replace(wc, wc.title.strip_code().strip())
                family = wikicode.strip_code().strip()

            return family

        def parse_relatives(wikicode: mwp.wikicode.Wikicode):
            relatives = []
            for link in mwp.parse(wikicode).filter_wikilinks():
                relation = link.title.strip_code()
                if "_" in relation:
                    relation = relation.replace('_', ' ')
                relatives.append(relation)
            return relatives

        # parse infobox
        if content:
            # select outermost wiki template
            wiki_template = mwp.parse(content).filter_templates()
            if wiki_template:
                infobox = next((t for t in wiki_template if t.name.strip().lower() == 'character'), None)

                # ignore non-character pages
                if infobox is None:
                    self._keep = False
                    return {}

                # ignore deleted characters (i.e. from early drafts)
                if any('deleted' in t.name.lower() for t in wiki_template):
                    self._keep = False
                    return {}

                # split into key/value pairs
                for entry in infobox.params:
                    key, val = re.sub(r'[^a-z\-]', '', str(entry.name).lower()), entry.value

                    # normalize non-linking field names
                    if key.endswith('-raw'):
                        key = key[:-4]

                    # clean field names and correct typos
                    key = cleansed_fields.get(key, key)

                    if key not in info_fields:
                        pass
                        # continue

                    # sanitize and process specific fields
                    elif key == 'books':
                        val = parse_books(val)

                    elif key == 'nationality':
                        val = parse_nation(val)

                    elif key == 'residence':
                        val = parse_residence(val)

                    elif key == 'abilities':
                        val = parse_abilities(val)

                    elif key == 'profession':
                        val = parse_profession(val)

                    elif key == 'groups':
                        val = parse_groups(val)

                    elif key == 'ethnicity':
                        val = parse_ethnicity(val)

                    elif key == 'species':
                        val = parse_species(val)

                    elif key == 'family':
                        val = parse_family(val)

                    elif key in ('bonded', 'spouse', 'parents', 'children', 'siblings', 'ancestors', 'descendants', 'relatives'):
                        val = parse_relatives(val)

                    elif key in ('titles', 'aliases', 'name'):
                        val = parse_names(val)

                    elif key in ('world', 'universe'):
                        val = val.strip_code()

                    elif key == 'unnamed':
                        val = True if val.strip_code().lower().startswith('y') else False

                    elif key == 'died':
                        val = True

                    else:
                        print("unknown key/value pair found!", key, ": ", val)

                    char_info[key] = val

                # combine nickname with aliases
                if char_info.get('name'):
                    if char_info.get('aliases'):
                        char_info['aliases'].extend(char_info.pop('name'))
                    else:
                        char_info['aliases'] = char_info.pop('name')

                # isolate common name and surname
                names = char_name.split()
                if names[0] in titles:
                    char_info['common_name'] = ''
                    char_info['surname'] = names[-1]
                elif "'s" in char_name:
                    char_info['common_name'] = char_name
                    char_info['surname'] = ''
                else:
                    char_info['common_name'] = names[0]
                    char_info['surname'] = names[-1] if len(names) > 1 else ''

                # ignore non-cosmere characters
                if char_info.get('universe', '').lower() != 'cosmere':
                    self._keep = False

            # no valid template to parse
            else:
                self._keep = False

        return char_info


def explicit_modify(ch: Character):
    if ch.name == 'Waxillium Ladrian':
        ch.aliases.append('Wax')
    elif ch.name == 'Hoid':
        # todo: manually specify locations where hoid appears but is unnamed (i.e. wb storyteller, mb beggar, etc)
        ch.aliases.remove('others')
        ch.aliases.append('Roamer')
        ch.aliases.append('Dust')
        ch.aliases.append('Fool')
        ch.aliases.append('Topaz')
        ch.aliases.append('Drifter')
        ch.aliases.append('Cephandrius')
        ch.aliases.append("Lunu'anaki")
    elif ch.name == 'Gave Entrone':
        ch.common_name = ''
    elif ch.name == 'Wulfden the First':
        ch.surname = ''
    elif ch.name == 'Bloody Tan':
        ch.common_name = 'Bloody Tan'
        ch.surname = ''
    elif ch.name == 'Push':
        ch._keep = False
    elif ch.name == 'Red' and ch.world == 'Scadrial':
        ch._keep = False
    elif ch.name == 'William Ann Montane':
        ch.common_name = 'William Ann'
    elif ch.name == 'Sixth of the Dusk':
        ch.common_name = 'Dusk'
    elif ch.name == 'Wan ShaiLu':
        ch.common_name = 'Shai'
    elif ch.name == 'Rock':
        ch.name = 'Rock, Jr.'
        ch.common_name = "Rock, Jr."
    elif ch.name == 'Sylphrena':
        ch.common_name = 'Syl'
    elif ch.name == 'Ten':
        ch._keep = False
    elif ch.name == 'Meridas Amaram':
        ch.titles.append('Highmarshal')
    elif ch.name == 'Drummer brothers':
        ch._keep = False
    elif ch.name == 'Herdazian general':
        ch._keep = False


def _generate_characters() -> Generator[Character, None, None]:
    """generator wrapped over coppermind_query() in order to delay execution of http query"""
    logger.debug('Character generator initialized.')

    for result in coppermind_query():
        char = Character(result)
        explicit_modify(char)
        if char._keep:
            yield char


# provide direct access to character generator
characters_ = _generate_characters()

characters = list(_generate_characters())

lookup = CharacterLookup()
for c in characters:
    for name in c.monikers:
        name = re.sub(possession, '', name)
        name = re.sub(punctuation, '', name)
        lookup[name] = c

if __name__ == '__main__':
    print('debugging!')
