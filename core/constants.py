# character groupings for networks
network_scopes = ('*:all',  # all
                  'w:roshar', 'w:nalthis', 'w:scadrial', 'w:first_of_the_sun',  # worlds
                  'w:taldain', 'w:threnody', 'w:yolen', 'w:sel',  # worlds (continued)
                  'b:mistborn', 'b:mistborn_1', 'b:mistborn_2', 'b:stormlight',  # book series
                  'f:kholin',  # families
                  )

# relevant fields in the character info dictionary
info_fields = ('name', 'aliases', 'titles',
               'books', 'world', 'abilities', 'universe',
               'family', 'parents', 'siblings', 'relatives', 'spouse', 'children', 'bonded', 'descendants', 'ancestors',
               'residence', 'groups', 'nation', 'nationality', 'profession', 'ethnicity',
               'species', 'occupation', 'unnamed')

# mapping of typos and alternate names of standard info fields in character dictionary
cleansed_fields = {
    'residnece':  'residence',
    'residency':  'residence',
    'nantion':    'nation',
    'group':      'groups',
    'nickname':   'aliases',
    'powers':     'abilities',
    'title':      'titles',
    'occupation': 'profession'
}

# list of world on which cosmere novels take place
cosmere_planets = ('roshar', 'nalthis', 'scadrial', 'first of the sun', 'taldain', 'threnody', 'yolen', 'sel')

book_keys = ['arcanum',
             'elantris',
             'emperors-soul',
             'mistborn/era1/final-empire',
             'mistborn/era1/well-of-ascension',
             'mistborn/era1/hero-of-ages',
             'mistborn/era2/alloy-of-law',
             'mistborn/era2/shadows-of-self',
             'mistborn/era2/bands-of-mourning',
             'mistborn/secret-history',
             'shadows-for-silence',
             'sixth-of-the-dusk',
             'stormlight/way-of-kings',
             'stormlight/words-of-radiance',
             'stormlight/edgedancer',
             'stormlight/oathbringer',
             'warbreaker',
             'white-sand'
             ]
worlds = {
    'arcanum':                         None,
    'dragonsteel':                     'yolen',
    'elantris':                        'sel',
    'emperors-soul':                   'sel',
    'mistborn/era1/final-empire':      'scadrial',
    'mistborn/era1/well-of-ascension': 'scadrial',
    'mistborn/era1/hero-of-ages':      'scadrial',
    'mistborn/era2/alloy-of-law':      'scadrial',
    'mistborn/era2/shadows-of-self':   'scadrial',
    'mistborn/era2/bands-of-mourning': 'scadrial',
    'mistborn/secret-history':         'scadrial',
    'shadows-for-silence':             'threnody',
    'sixth-of-the-dusk':               'first of the sun',
    'stormlight/way-of-kings':         'roshar',
    'stormlight/words-of-radiance':    'roshar',
    'stormlight/edgedancer':           'roshar',
    'stormlight/oathbringer':          'roshar',
    'warbreaker':                      'nalthis',
    'white-sand':                      'taldain',
}
books = {
    'Arcanum Unbounded':                          'arcanum',
    'Elantris':                                   'elantris',
    'The Hope of Elantris':                       'elantris',
    "The Emperor's Soul":                         'emperors-soul',
    'Mistborn':                                   'mistborn',
    'Mistborn Era 1':                             'mistborn',
    'Mistborn Era 2':                             'mistborn',
    'Shadows of Self':                            'mistborn',
    'Mistborn: Birthright':                       'mistborn',
    'The Eleventh Metal':                         'mistborn',
    'Shadows for Silence in the Forests of Hell': 'shadows-for-silence',
    'Shadows for Silence':                        'shadows-for-silence',
    'Sixth of the Dusk':                          'sixth-of-the-dusk',
    'Stormlight Archive':                         'stormlight',
    'The Stormlight Archive':                     'stormlight',
    'The Liar of Partinel':                       None,
    'Warbreaker':                                 'warbreaker',
    'White Sand':                                 'white-sand',
}

# case-insensitive mapping of demonyms for nations in the cosmere
nationalities = {
    'aimia':         'Aimian',
    'alethi':        'Alethi',
    'alethkar':      'Alethi',
    'arelish':       'Arelish',
    'arelon':        'Arelish',
    'azir':          'Azish',
    'azish':         'Azish',
    'elis':          'Elisian',
    'elisian':       'Elisian',
    'emul':          'Emuli',
    'emuli':         'Emuli',
    'fjordell':      'Fjordell',
    'fjorden':       'Fjordell',
    'hallandren':    'Hallandren',
    'herdaz':        'Herdazian',
    'herdazian':     'Herdazian',
    'hrovell':       'Hroven',
    'hroven':        'Hroven',
    'idrian':        'Idrian',
    'idris':         'Idrian',
    'iri':           'Iriali',
    'iriali':        'Iriali',
    'jah keved':     'Veden',
    'jindo':         'JinDo',
    'kharbranth':    'Kharbranthian',
    'kharbranthian': 'Kharbranthian',
    'khlenni':       'Khlenni',
    'khlennium':     'Khlenni',
    'liafor':        'Liaforan',
    'liaforan':      'Liaforan',
    'listener':      'Listener',
    'lossand':       'Lossandin',
    'lossandin':     'Lossandin',
    'maipon':        'MaiPon',
    'malwish':       'Malwish',
    "mulla'dil":     "Mulla'dil",
    'natan':         'Natan',
    'natanatan':     'Natan',
    'pahn kahl':     'Pahn Kahl',
    'parshendi':     'Listener',
    'purelake':      'Purelaker',
    'purelaker':     'Purelaker',
    'reshi':         'Reshi',
    'reshi isles':   'Reshi',
    'rira':          'Riran',
    'riran':         'Riran',
    'rose empire':   'Rose Empire',
    'shin':          'Shin',
    'shinovar':      'Shin',
    'svorden':       'Svordish',
    'svordish':      'Svordish',
    'tashikk':       'Tashikki',
    'tashikki':      'Tashikki',
    'teod':          'Teoish',
    'teoish':        'Teoish',
    'terris':        'Terris',
    'thaylen':       'Thaylen',
    'thaylenah':     'Thaylen',
    'unkalaki':      'Unkalaki',
    'uvara':         'Uvara',
    'veden':         'Veden'
}
nations = {
    'Aimian':        'Aimia',
    'Alethi':        'Alethkar',
    'Arelish':       'Arelon',
    'Azish':         'Azir',
    'Elisian':       'Elis',
    'Emuli':         'Emul',
    'Fjordell':      'Fjorden',
    'Hallandren':    'Hallandren',
    'Herdazian':     'Herdaz',
    'Hroven':        'Hrovell',
    'Idrian':        'Idris',
    'Iriali':        'Iri',
    'JinDo':         'JinDo',
    'Kharbranthian': 'Kharbranth',
    'Khlenni':       'Khlennium',
    'Liaforan':      'Liafor',
    'Listener':      None,
    'Lossandin':     'Lossand',
    'MaiPon':        'MaiPon',
    'Malwish':       'South Scadrial',  # todo: update after W&W4
    "Mulla'dil":     "Mulla'dil",
    'Natan':         'Natanatan',
    'Pahn Kahl':     'Pahn Kahl',
    'Purelaker':     'Purelake',
    'Reshi':         'Reshi Isles',
    'Riran':         'Rira',
    'Rose Empire':   'Rose Empire',
    'Shin':          'Shinovar',
    'Svordish':      'Svorden',
    'Tashikki':      'Tashikk',
    'Teoish':        'Teod',
    'Terris':        'Terris',
    'Thaylen':       'Thaylenah',
    'Unkalaki':      'Horneater Peaks',  # todo: do horneaters have an official nation?
    'Uvara':         None,
    'Veden':         'Jah Keved'
}
