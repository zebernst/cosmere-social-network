# character groupings for networks
network_scopes = ('*:all',  # all
                  'w:roshar', 'w:nalthis', 'w:scadrial', 'w:first_of_the_sun',  # worlds
                  'w:taldain', 'w:threnody', 'w:yolen', 'w:sel',  # worlds (continued)
                  'b:mistborn', 'b:mistborn_1', 'b:mistborn_2', 'b:stormlight',  # book series
                  'f:kholin',  # families
                  )

# relevant fields in the character info dictionary
info_fields = ('name', 'aliases', 'titles',
               'books', 'world', 'abilities',
               'family', 'parents', 'siblings', 'relatives', 'spouse', 'children', 'bonded', 'descendants', 'ancestors',
               'residence', 'groups', 'nation', 'nationality', 'profession', 'ethnicity',
               'species', 'occupation', 'unnamed')

# list of world on which cosmere novels take place
cosmere_planets = ('roshar', 'nalthis', 'scadrial', 'first of the sun', 'taldain', 'threnody', 'yolen', 'sel')

# case-insensitive mapping of demonyms for nations in the cosmere
nationalities = {
    'hallandren':    'Hallandren',
    'idris':         'Idrian',
    'idrian':        'Idrian',
    'pahn kahl':     'Pahn Kahl',
    'reshi isles':   'Reshi',
    'reshi':         'Reshi',
    'thaylenah':     'Thaylen',
    'thaylen':       'Thaylen',
    'purelake':      'Purelaker',
    'purelaker':     'Purelaker',
    'jah keved':     'Veden',
    'veden':         'Veden',
    'alethkar':      'Alethi',
    'alethi':        'Alethi',
    'azir':          'Azish',
    'azish':         'Azish',
    'shinovar':      'Shin',
    'shin':          'Shin',
    'natanatan':     'Natan',
    'natan':         'Natan',
    'herdaz':        'Herdazian',
    'herdazian':     'Herdazian',
    'unkalaki':      'Unkalaki',
    'tashikk':       'Tashikki',
    'tashikki':      'Tashikki',
    'parshendi':     'Listener',
    'listener':      'Listener',
    'kharbranth':    'Kharbranthian',
    'kharbranthian': 'Kharbranthian',
    'liafor':        'Liaforan',
    'liaforan':      'Liaforan',
    'iri':           'Iriali',
    'iriali':        'Iriali',
    'uvara':         'Uvara',
    'aimia':         'Aimian',
    'emul':          'Emuli',
    'emuli':         'Emuli',
    'rira':          'Riran',
    'riran':         'Riran',
    'terris':        'Terris',
    'khlennium':     'Khlenni',
    'khlenni':       'Khlenni',
    'arelon':        'Arelish',
    'arelish':       'Arelish',
    'fjorden':       'Fjordell',
    'fjordell':      'Fjordell',
    'hrovell':       'Hroven',
    'hroven':        'Hroven',
    'rose empire':   'Rose Empire',
    'maipon':        'MaiPon',
    "mulla'dil":     "Mulla'dil",
    'jindo':         'JinDo',
    'teod':          'Teoish',
    'teoish':        'Teoish',
    'svorden':       'Svordish',
    'svordish':      'Svordish',
    'lossand':       'Lossandin',
    'lossandin':     'Lossandin',
    'elis':          'Elisian',
    'elisian':       'Elisian',
    'malwish':       'Malwish',
}
