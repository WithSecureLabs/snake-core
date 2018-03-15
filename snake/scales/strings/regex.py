# pylint: disable=missing-docstring

import re


# pylint: disable=anomalous-backslash-in-string


TLD = ['XN--CLCHC0EA0B2G2A9GCD', 'XN--MGBERP4A5D4AR', 'XN--XKC2DL3A5EE0H', 'XN--XKC2AL3HYE2A', 'XN--I1B6B1A6A2E',
       'XN--LGBBAT1AD8J', 'XN--MGBA3A4F16A', 'XN--MGBC0A9AZCG', 'XN--NQV7FS00EMA', 'XN--6QQ986B3XL', 'XN--FIQ228C5HS',
       'XN--MGBAAM7A8H', 'XN--MGBAYH7GPA', 'XN--MGBBH1A71E', 'XN--MGBX4CD0AB', 'INTERNATIONAL', 'XN--FPCRJ9C3D',
       'XN--FZC2C9E2C', 'XN--YFRO4I67O', 'XN--YGBI2AMMX', 'CONSTRUCTION', 'XN--3E0B707E', 'XN--80ASEHDB',
       'XN--MGB9AWBF', 'XN--MGBAB2BD', 'XN--NGBC5AZD', 'XN--OGBPF8FL', 'CONTRACTORS', 'ENTERPRISES', 'PHOTOGRAPHY',
       'PRODUCTIONS', 'XN--3BST00M', 'XN--3DS443G', 'XN--45BRJ9C', 'XN--55QW42G', 'XN--6FRZ82G', 'XN--80AO21A',
       'XN--D1ACJ3B', 'XN--GECRJ9C', 'XN--H2BRJ9C', 'XN--J6W193G', 'XN--KPRW13D', 'XN--KPRY57D', 'XN--PGBS0DH',
       'XN--Q9JYB4C', 'XN--RHQV96G', 'XN--S9BRJ9C', 'XN--ZFR164B', 'FOUNDATION', 'IMMOBILIEN', 'INDUSTRIES',
       'MANAGEMENT', 'PROPERTIES', 'TECHNOLOGY', 'XN--55QX5D', 'XN--80ASWG', 'XN--90A3AC', 'XN--CG4BKI', 'XN--FIQ64B',
       'XN--FIQS8S', 'XN--FIQZ9S', 'XN--IO0A7I', 'XN--O3CW4H', 'XN--UNUP4Y', 'XN--WGBH1C', 'XN--WGBL6A', 'CHRISTMAS',
       'COMMUNITY', 'DIRECTORY', 'EDUCATION', 'EQUIPMENT', 'INSTITUTE', 'MARKETING', 'SOLUTIONS', 'VACATIONS',
       'XN--C1AVG', 'XN--J1AMH', 'XN--L1ACC', 'XN--NQV7F', 'BARGAINS', 'BOUTIQUE', 'BUILDERS', 'CATERING', 'CLEANING',
       'CLOTHING', 'COMPUTER', 'DEMOCRAT', 'DIAMONDS', 'GRAPHICS', 'HOLDINGS', 'LIGHTING', 'PARTNERS', 'PLUMBING',
       'SUPPLIES', 'TRAINING', 'VENTURES', 'XN--P1AI', 'ACADEMY', 'CAREERS', 'COMPANY', 'CRUISES', 'DOMAINS', 'EXPOSED',
       'FLIGHTS', 'FLORIST', 'GALLERY', 'GUITARS', 'HOLIDAY', 'KITCHEN', 'NEUSTAR', 'OKINAWA', 'RECIPES', 'RENTALS',
       'REVIEWS', 'SHIKSHA', 'SINGLES', 'SUPPORT', 'SYSTEMS', 'AGENCY', 'BERLIN', 'CAMERA', 'CENTER', 'COFFEE',
       'CONDOS', 'DATING', 'ESTATE', 'EVENTS', 'EXPERT', 'FUTBOL', 'KAUFEN', 'LUXURY', 'MAISON', 'MONASH', 'MUSEUM',
       'NAGOYA', 'PHOTOS', 'REPAIR', 'REPORT', 'SOCIAL', 'SUPPLY', 'TATTOO', 'TIENDA', 'TRAVEL', 'VIAJES', 'VILLAS',
       'VISION', 'VOTING', 'VOYAGE', 'ACTOR', 'BUILD', 'CARDS', 'CHEAP', 'CODES', 'DANCE', 'EMAIL', 'GLASS', 'HOUSE',
       'KOELN', 'MANGO', 'NINJA', 'ONION', 'PARTS', 'PHOTO', 'SHOES', 'SOLAR', 'TODAY', 'TOKYO', 'TOOLS', 'WATCH',
       'WORKS', 'AERO', 'ARPA', 'ASIA', 'BEST', 'BIKE', 'BLUE', 'BUZZ', 'CAMP', 'CLUB', 'COOL', 'COOP', 'FARM', 'FISH',
       'GIFT', 'GURU', 'INFO', 'JOBS', 'KIWI', 'KRED', 'LAND', 'LIMO', 'LINK', 'MENU', 'MOBI', 'MODA', 'NAME', 'PICS',
       'PINK', 'POST', 'QPON', 'RICH', 'RUHR', 'SEXY', 'TIPS', 'VOTE', 'VOTO', 'WANG', 'WIEN', 'WIKI', 'ZONE', 'BAR',
       'BID', 'BIZ', 'CAB', 'CAT', 'CEO', 'COM', 'DNP', 'EDU', 'GOV', 'INK', 'INT', 'KIM', 'MIL', 'NET', 'ONL', 'ORG',
       'PRO', 'PUB', 'RED', 'TEL', 'UNO', 'WED', 'XXX', 'XYZ', 'AC', 'AD', 'AE', 'AF', 'AG', 'AI', 'AL', 'AM', 'AN',
       'AO', 'AQ', 'AR', 'AS', 'AT', 'AU', 'AW', 'AX', 'AZ', 'BA', 'BB', 'BD', 'BE', 'BF', 'BG', 'BH', 'BI', 'BJ', 'BM',
       'BN', 'BO', 'BR', 'BS', 'BT', 'BV', 'BW', 'BY', 'BZ', 'CA', 'CC', 'CD', 'CF', 'CG', 'CH', 'CI', 'CK', 'CL', 'CM',
       'CN', 'CO', 'CR', 'CU', 'CV', 'CW', 'CX', 'CY', 'CZ', 'DE', 'DJ', 'DK', 'DM', 'DO', 'DZ', 'EC', 'EE', 'EG', 'ER',
       'ES', 'ET', 'EU', 'FI', 'FJ', 'FK', 'FM', 'FO', 'FR', 'GA', 'GB', 'GD', 'GE', 'GF', 'GG', 'GH', 'GI', 'GL', 'GM',
       'GN', 'GP', 'GQ', 'GR', 'GS', 'GT', 'GU', 'GW', 'GY', 'HK', 'HM', 'HN', 'HR', 'HT', 'HU', 'ID', 'IE', 'IL', 'IM',
       'IN', 'IO', 'IQ', 'IR', 'IS', 'IT', 'JE', 'JM', 'JO', 'JP', 'KE', 'KG', 'KH', 'KI', 'KM', 'KN', 'KP', 'KR', 'KW',
       'KY', 'KZ', 'LA', 'LB', 'LC', 'LI', 'LK', 'LR', 'LS', 'LT', 'LU', 'LV', 'LY', 'MA', 'MC', 'MD', 'ME', 'MG', 'MH',
       'MK', 'ML', 'MM', 'MN', 'MO', 'MP', 'MQ', 'MR', 'MS', 'MT', 'MU', 'MV', 'MW', 'MX', 'MY', 'MZ', 'NA', 'NC', 'NE',
       'NF', 'NG', 'NI', 'NL', 'NO', 'NP', 'NR', 'NU', 'NZ', 'OM', 'PA', 'PE', 'PF', 'PG', 'PH', 'PK', 'PL', 'PM', 'PN',
       'PR', 'PS', 'PT', 'PW', 'PY', 'QA', 'RE', 'RO', 'RS', 'RU', 'RW', 'SA', 'SB', 'SC', 'SD', 'SE', 'SG', 'SH', 'SI',
       'SJ', 'SK', 'SL', 'SM', 'SN', 'SO', 'SR', 'ST', 'SU', 'SV', 'SX', 'SY', 'SZ', 'TC', 'TD', 'TF', 'TG', 'TH', 'TJ',
       'TK', 'TL', 'TM', 'TN', 'TO', 'TP', 'TR', 'TT', 'TV', 'TW', 'TZ', 'UA', 'UG', 'UK', 'US', 'UY', 'UZ', 'VA', 'VC',
       'VE', 'VG', 'VI', 'VN', 'VU', 'WF', 'WS', 'YE', 'YT', 'ZA', 'ZM', 'ZW']

# regex tested against full string extraction of binary as well as inserted custom strings,
# this allows for accuracy checking against binary string dumps and inserted true values.
# unix path regex still collects some values that are not unix paths but I couldn't figure
# additional filters. As true positive strings inserted were done manually and not extracted
# as part of the string extraction this may have obscured accuracy due to insertion of hidden
# chars possibly. Needs testing against string extraction covering all cases, did not have such
# a sample at hand.

IPV4_REGEX = re.compile('[12]?[0-9]{1,2}\.[12]?[0-9]{1,2}\.[12]?[0-9]{1,2}\.[12]?[0-9]{1,2}')
IPV6_REGEX = re.compile('[a-fA-F0-9]{1,4}:([:a-fA-F0-9]{0,4}:|0:)+([a-fA-F0-9]{1,4})?')
WINDOWS_PATH_REGEX = re.compile('([a-zA-Z]{1}:\\\\|%[a-zA-Z]+%\\\\)([a-zA-Z0-9]+\\\\?)+(\\.[a-zA-Z0-9]{0,5})?')
UNIX_PATH_REGEX = re.compile('[^\\n\\r\\s]+/([^\\s]+/?)+(\\.[a-zA-Z]{2,5})?')
EMAIL_REGEX = re.compile('([\\w\\d\\.-]?)+@\\w+\\.[a-zA-Z]{2,5}[^\\w\\d]')
URL_REGEX = re.compile('[\\w]{1,5}://(\\w+\\.){1,2}([\\w-]+/?)*(\\.\\w{1,6})?')
DOMAIN_REGEX = re.compile('(h?t?t?p?s?://)?([\\w-]+\\.)+(' + '|'.join(TLD) + ')+[\\s/]', re.IGNORECASE)
MAC_REGEX = re.compile('[a-zA-Z0-9]{2}([:-][a-zA-Z0-9]{2}){5}')
DATE1_REGEX = re.compile('((?:19|20)\\d\\d)[- /.](0[1-9]|1[012])[- /.](0[1-9]|[12][0-9]|3[01])')
DATE2_REGEX = re.compile('(0[1-9]|[12][0-9]|3[01])[- /.](0[1-9]|1[012])[- /.]((?:19|20)\\d\\d)')
DATE3_REGEX = re.compile('(0[1-9]|1[012])[- /.](0[1-9]|[12][0-9]|3[01])[- /.]((?:19|20)\\d\\d)')
