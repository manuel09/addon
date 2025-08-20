# -*- coding: utf-8 -*-
# ------------------------------------------------------------
# Canale per AnimeUnity
# ------------------------------------------------------------

import cloudscraper, json, copy, inspect
from core import jsontools, support, httptools, scrapertools
from platformcode import autorenumber, logger

# support.dbg()
host = support.config.get_channel_url()
response = httptools.downloadpage(host + '/archivio')
csrf_token = support.match(response.data, patron='name="csrf-token" content="([^"]+)"').match
headers = {'content-type': 'application/json;charset=UTF-8',
           'x-csrf-token': csrf_token,
           'Cookie' : '; '.join([x.name + '=' + x.value for x in response.cookies])}


@support.menu
def mainlist(item):
    top =  [('Ultimi Episodi', ['', 'news'])]

    menu = [('Anime {bullet bold}',['', 'menu', {}, 'tvshow']),
            ('Film {submenu}',['', 'menu', {'type': 'Movie'}]),
            ('TV {submenu}',['', 'menu', {'type': 'TV'}, 'tvshow']),
            ('OVA {submenu} {tv}',['', 'menu', {'type': 'OVA'}, 'tvshow']),
            ('ONA {submenu} {tv}',['', 'menu', {'type': 'ONA'}, 'tvshow']),
            ('Special {submenu} {tv}',['', 'menu', {'type': 'Special'}, 'tvshow'])]
    search =''
    return locals()

def menu(item):
    item.action = 'peliculas'
    ITA = copy.copy(item.args)
    ITA['title'] = '(ita)'
    InCorso = copy.copy(item.args)
    InCorso['status'] = 'In Corso'
    Terminato = copy.copy(item.args)
    Terminato['status'] = 'Terminato'
    itemlist = [item.clone(title=support.typo('Tutti','bold')),
                item.clone(title=support.typo('ITA','bold'), args=ITA),
                item.clone(title=support.typo('Genere','bold'), action='genres'),
                item.clone(title=support.typo('Anno','bold'), action='years')]
    if item.contentType == 'tvshow':
        itemlist += [item.clone(title=support.typo('In Corso','bold'), args=InCorso),
                     item.clone(title=support.typo('Terminato','bold'), args=Terminato)]
    itemlist +=[item.clone(title=support.typo('Cerca...','bold'), action='search', thumbnail=support.thumb('search'))]
    return itemlist


def genres(item):
    support.info()
    # support.dbg()
    itemlist = []

    genres = json.loads(support.match(response.data, patron='genres="([^"]+)').match.replace('&quot;','"'))

    for genre in genres:
        item.args['genres'] = [genre]
        itemlist.append(item.clone(title=support.typo(genre['name'],'bold'), action='peliculas'))
    return support.thumb(itemlist)

def years(item):
    support.info()
    itemlist = []

    from datetime import datetime
    next_year = datetime.today().year + 1
    oldest_year = int(support.match(response.data, patron='anime_oldest_date="([^"]+)').match)

    for year in list(reversed(range(oldest_year, next_year + 1))):
        item.args['year']=year
        itemlist.append(item.clone(title=support.typo(year,'bold'), action='peliculas'))
    return itemlist


def search(item, text):
    support.info('search', item)
    if not item.args:
        item.args = {'title':text}
    else:
        item.args['title'] = text
    item.search = text

    try:
        return peliculas(item)
    # Continua la ricerca in caso di errore
    except:
        import sys
        for line in sys.exc_info():
            support.info('search log:', line)
        return []


def newest(categoria):
    support.info(categoria)
    itemlist = []
    item = support.Item()
    item.url = host

    try:
        itemlist = news(item)

        if itemlist[-1].action == 'news':
            itemlist.pop()
    # Continua la ricerca in caso di errore
    except:
        import sys
        for line in sys.exc_info():
            support.info(line)
        return []

    return itemlist

def news(item):
    support.info()
    item.contentType = 'episode'
    itemlist = []

    fullJs = json.loads(support.match(httptools.downloadpage(item.url).data, headers=headers, patron=r'items-json="([^"]+)"').match.replace('&quot;','"'))
    js = fullJs['data']

    for it in js:
        if it.get('anime', {}).get('title') or it.get('anime', {}).get('title_eng'):
            title_name = it['anime']['title'] if it.get('anime', {}).get('title') else it['anime']['title_eng']
            pattern = r'[sS](?P<season>\d+)[eE](?P<episode>\d+)'
            match = scrapertools.find_single_match(it['file_name'], pattern)
            full_episode = ''
            if match:
                season, episode = match
                full_episode = ' - S' + season + ' E' + episode
            else:
                pattern = r'[._\s]Ep[._\s]*(?P<episode>\d+)'
                episode = scrapertools.find_single_match(it['file_name'], pattern)
                if episode:
                    full_episode = ' - E' + episode                             
            itemlist.append(
                item.clone(title = support.typo(title_name + full_episode, 'bold'),
                           fulltitle = it['anime']['title'],
                           thumbnail = it['anime']['imageurl'],
                           forcethumb = True,
                           scws_id = it.get('scws_id', ''),
                           url = '{}/anime/{}-{}'.format(item.url, it['anime']['id'],it['anime']['slug']),
                           plot = it['anime']['plot'],
                           action = 'findvideos')
            )
    if 'next_page_url' in fullJs:
        itemlist.append(item.clone(title=support.typo(support.config.get_localized_string(30992), 'color std bold'),thumbnail=support.thumb(), url=fullJs['next_page_url']))
    return itemlist


def peliculas(item):
    support.info()
    itemlist = []

    page = item.page if item.page else 0
    item.args['offset'] = page * 30

    order = support.config.get_setting('order', item.channel)
    if order:
        order_list = [ "Standard", "Lista A-Z", "Lista Z-A", "Popolarità", "Valutazione" ]
        item.args['order'] = order_list[order]

    payload = json.dumps(item.args)
    records = httptools.downloadpage(host + '/archivio/get-animes', headers=headers, post=payload).json['records']
    # support.dbg()
 
    for it in records:
        if not it['title']:
            it['title'] = it['title_eng']

        lang = support.match(it['title'], patron=r'\(([It][Tt][Aa])\)').match
        title = support.re.sub(r'\s*\([^\)]+\)', '', it['title'])
	
        if 'ita' in lang.lower(): 
            language = 'ITA'
        else:
            language = 'Sub-ITA'

        if title:
            itm = item.clone(title=support.typo(title,'bold') + support.typo(language,'_ [] color std') + (support.typo(it['title_eng'],'_ ()') if it['title_eng'] else ''))
        else:
            itm = item.clone(title=support.typo(it['title_eng'],'bold') + support.typo(language,'_ [] color std'))
        itm.contentLanguage = language
        itm.type = it['type']
        itm.thumbnail = it['imageurl']
        itm.plot = it['plot']
        itm.url = '{}/anime/{}-{}'.format(item.url, it.get('id'), it.get('slug'))

        if it['episodes_count'] == 1:
            itm.contentType = 'movie'
            itm.fulltitle = itm.show = itm.contentTitle = title
            itm.contentSerieName = ''
            itm.action = 'findvideos'
            # itm.scws_id = it['episodes'][0].get('scws_id', '')
            # itm.video_url = it['episodes'][0].get('link', '')

        else:
            itm.api_ep_url = '{}/info_api/{}/'.format(item.url, it.get('id'))
            itm.contentType = 'tvshow'
            itm.contentTitle = ''
            itm.fulltitle = itm.show = itm.contentSerieName = title
            itm.action = 'episodios'
            #itm.episodes = it['episodes'] if 'episodes' in it else it.get('scws_id', '')

        itemlist.append(itm)

    autorenumber.start(itemlist)
    if len(itemlist) >= 30:
        itemlist.append(item.clone(title=support.typo(support.config.get_localized_string(30992), 'color std bold'), thumbnail=support.thumb(), page=page + 1))

    return itemlist

def episodios(item):
    support.info()
    itemlist = []
    title = 'Parte' if item.type.lower() == 'movie' else 'Episodio'
    start=1
    limit=120
 
    while True:
        full = json.loads(httptools.downloadpage('{}1?start_range={}&end_range={}'.format(item.api_ep_url,start, start + (limit -1)), headers=headers).data)
        count = full['episodes_count']
        episodes = full['episodes']
        for it in episodes:
            itemlist.append(
                item.clone(title=support.typo('{}. {} {}'.format(it['number'], title, it['number']), 'bold'),
                       episode = it['number'],
                       fulltitle=item.title,
                       show=item.title,
                       contentTitle='',
                       contentSerieName=item.contentSerieName,
                       thumbnail=item.thumbnail,
                       plot=item.plot,
                       action='findvideos',
                       contentType='episode',
                       url = '{}/{}'.format(item.url, it['id'])
                      )
                    #    video_url=it.get('link', ''))
            )
        if count > start:
            start = start + limit
        else:
            break

    if inspect.stack(0)[1][3] not in ['find_episodes']:
        autorenumber.start(itemlist, item)
    support.videolibrary(itemlist, item)
    #support.download(itemlist, item)

    return itemlist


def findvideos(item):
    # if item.scws_id:
    #     from time import time
    #     from base64 import b64encode
    #     from hashlib import md5
    #
    #     client_ip = support.httptools.downloadpage('http://ip-api.com/json/').json.get('query')
    #
    #     expires = int(time() + 172800)
    #     token = b64encode(md5('{}{} Yc8U6r8KjAKAepEA'.format(expires, client_ip).encode('utf-8')).digest()).decode('utf-8').replace('=', '').replace('+', '-').replace('/', '_')
    #
    #     url = 'https://scws.work/master/{}?token={}&expires={}&n=1'.format(item.scws_id, token, expires)
    #
    #     itemlist = [item.clone(title=support.config.get_localized_string(30137), url=url, server='directo', action='play')]

    from core import channeltools
    itemlist = [item.clone(title=channeltools.get_channel_parameters(item.channel)['title'],
                           url=item.url, server='streamingcommunityws')]
    return support.server(item, itemlist=itemlist, referer=False)

    # return support.server(item, itemlist=itemlist)

#
# def play(item):
#     urls = list()
#     info = support.match(item.url, patron=r'(http.*?rendition=(\d+)[^\s]+)').matches
#
#     if info:
#         for url, res in info:
#             urls.append(['hls [{}]'.format(res), url])
#     return urls