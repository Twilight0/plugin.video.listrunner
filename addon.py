# -*- coding: utf-8 -*-

"""
    Listrunner Add-on
    Author: Twilight0

        This program is free software: you can redistribute it and/or modify
        it under the terms of the GNU General Public License as published by
        the Free Software Foundation, either version 3 of the License, or
        (at your option) any later version.

        This program is distributed in the hope that it will be useful,
        but WITHOUT ANY WARRANTY; without even the implied warranty of
        MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
        GNU General Public License for more details.

        You should have received a copy of the GNU General Public License
        along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""

import re
from tulip import client, youtube, cache, control, directory
from tulip.init import params
from tulip.compat import OrderedDict, quote, urlencode
from tulip.log import log_debug

action = params.get('action')
url = params.get('url')

try:
    import YDStreamExtractor
except ImportError:
    YDStreamExtractor = None

try:
    import resolveurl
except ImportError:
    resolveurl = None

try:
    import streamlink.session
except ImportError:
    streamlink = None


def yt_playlist_getter(pid):

    if 'playlist?list=' in pid:
        pid = pid.partition('list=')[2]

    yt_list = youtube.youtube(key='AIzaSyA8k1OyLGf03HBNl0byD511jr9cFWo2GR4', replace_url=False).playlist(pid)

    if not yt_list:
        return

    for count, i in enumerate(yt_list, start=1):
        i.update({'action': 'play', 'isFolder': 'False', 'code': count})

    return yt_list


def constructor():

    items_list = [] ;  groups = []

    if control.setting('local_or_remote') == '0':
        try:
            with open (control.setting('local')) as f:
                text = f.read()
                f.close()
        except IOError:
            return
    elif control.setting('local_or_remote') == '1':
        try:
            text = client.request(control.setting('remote'))
            if text is None:
                raise ValueError
        except ValueError:
            text = client.request(control.setting('remote'), close=False)
            if text is None:
                return
    else:
        return cache.get(
            yt_playlist_getter, int(control.setting('caching')) if int(control.setting('caching')) > 0 else 0,
            control.setting('youtube_url')
        )

    if not text.startswith('#EXTM3U'):
        return

    result = text.replace('\t', ' ')
    items = re.compile('EXTINF:(-? ?\d*)(.*?)$\r?\n?(.*?)$', re.U + re.S + re.M).findall(result)

    for number, (duration, item, uri) in enumerate(items, start=1):

        duration = duration.strip()
        item = item.strip()
        uri= uri.strip()

        count = item.count(',')

        if count == 1:
            title = item.partition(',')[2]
        else:
            title = item.rpartition(',')[2]

        try:
            title = title.decode('utf-8').strip()
        except Exception:
            title = title.strip()

        duration = int(duration)

        if 'tvg-logo' in item:
            icon = re.findall('tvg-logo="(.*?)"', item, re.U)[0]
        elif 'icon' in item:
            icon = re.findall('icon="(.*?)"', item, re.U)[0]
        elif 'image' in item:
            icon = re.findall('image="(.*?)"', item, re.U)[0]
        else:
            icon = control.addonInfo('icon')

        if 'group-title' in item:
            group = re.findall('group-title="(.*?)"', item, re.U)[0]
        else:
            group = control.lang(30033)

        try:
            group = group.decode('utf-8')
        except Exception:
            pass

        data = (
            {
                'title': title, 'image': icon, 'group': group, 'genre': group, 'url': uri, 'code': str(number),
                'duration': duration if duration > 0 else None, 'action': 'play', 'isFolder': 'False'
            }
        )
        items_list.append(data)


        try:
            groups.append(group.decode('utf-8'))
        except Exception:
            groups.append(group)

    trimmed_groups = list(OrderedDict.fromkeys(groups))

    trimmed_groups.sort()

    if len(trimmed_groups) == 1:
        control.setSetting('group', 'ALL')
        return items_list
    else:
        return items_list, trimmed_groups


def switcher():

    def seq(choose):

        control.setSetting('group', choose)
        control.idle()
        control.sleep(50)
        control.execute('Container.Refresh')

    groups = [control.lang(30016)] + constructor()[1]

    choices = control.dialog.select(heading=control.lang(30017), list=groups)

    if choices == 0:
        seq('ALL')
    elif choices <= len(groups) and not choices == -1:
        seq(groups.pop(choices))
    else:
        control.execute('Dialog.Close(busydialog)')
        control.dialog.notification(heading=control.addonInfo('name'), message=control.lang(30019), icon=control.addonInfo('icon'), sound=False)


def main_menu():

    if control.setting('show_root') == 'false' and not control.setting('local') and not control.setting('remote') and not control.setting('youtube_url'):
        return

    try:
        group_setting = control.setting('group').decode('utf-8')
    except Exception:
        group_setting = control.setting('group')

    root_menu = [
        {
            'title': control.lang(30011),
            'image': control.join(control.addonPath, 'resources', 'media', 'settings.png'),
            'action': 'settings'
        }
    ]

    null = [
        {
            'title': control.lang(30013),
            'image': control.join(control.addonPath, 'resources', 'media', 'null.png'),
            'action': None
        }
    ]

    if control.setting('show_root') == 'false':
        root_menu = []
        null = []

    switcher_menu = [
        {
            'title': control.lang(30015).format(control.lang(30016) if control.setting('group') == 'ALL' else group_setting),
            'image': control.join(control.addonPath, 'resources', 'media', 'switcher.png'),
            'action': 'switcher'
        }
    ]

    if control.setting('show_switcher') == 'false':
        switcher_menu = []

    if not control.setting('local') and not control.setting('remote') and not control.setting('youtube_url'):
        items = root_menu + null
    else:
        try:
            if not constructor():
                items = root_menu + null
            elif len(constructor()) == 2:
                filtered = [
                    i for i in constructor()[0] if any(i['group'] == selected for selected in [group_setting])
                ] if not control.setting('group') == 'ALL' else constructor()[0]
                items = root_menu + switcher_menu + filtered
            else:
                items = root_menu + constructor()
        except Exception:
            items = root_menu + null

    for i in items:
        i.update(
            {
                'cm': [
                    {'title': 30012, 'query': {'action': 'refresh'}}, {'title': 30038, 'query': {'action': 'settings'}}
                ]
            }
        )

    control.sortmethods('production_code')
    control.sortmethods('title')
    if len(constructor()) == 2:
        control.sortmethods('genre')
    directory.add(items)


if action is None:

    main_menu()

elif action == 'play':

    yt_prefix = 'plugin://plugin.video.youtube/play/?video_id='

    if (not resolveurl and not YDStreamExtractor and not streamlink) or control.setting('yt_addon') == 'true':
        url = re.sub(
            r'''https?://(?:[0-9A-Z-]+\.)?(?:(youtu\.be|youtube(?:-nocookie)?\.com)/?\S*?[^\w\s-])([\w-]{11})(?=[^\w-]|$)(?![?=&+%\w.-]*(?:['"][^<>]*>|</a>))[?=&+%\w.-]*''',
            yt_prefix + r'\2', url, flags=re.I
        )

    if url.startswith(yt_prefix):
        log_debug('Youtube addon is used for playback')
        directory.resolve(url)

    else:

        for i in ['resolveurl', 'youtube-dl', 'streamlink', 'unresolvable']:
            if resolveurl is not None and i == 'resolveurl':
                if resolveurl.HostedMediaFile(url).valid_url():
                    try:
                        link = resolveurl.resolve(url)
                        directory.resolve(link, dash=('.mpd' in link or 'dash' in link))
                        break
                    except Exception:
                        continue
            elif YDStreamExtractor is not None and i == 'youtube-dl':
                try:
                    stream = YDStreamExtractor.getVideoInfo(url)
                    link = stream.streamURL()
                    # title = stream.selectedStream()['title']
                    # icon = stream.selectedStream()['thumbnail']
                    directory.resolve(link, dash=('.mpd' in link or 'dash' in link))
                    break
                except Exception:
                    continue
            elif streamlink is not None and i == 'streamlink':
                try:
                    session = streamlink.session.Streamlink()
                    plugin = session.resolve_url(url)
                    streams = plugin.streams()
                    try:
                        args = streams['best'].args
                        append = '|'
                        if 'headers' in args:
                            headers = quote(streams['best'].args['headers'])
                            append += urlencode(headers)
                        else:
                            append = ''
                    except AttributeError:
                        append = ''

                    link = streams['best'].to_url() + append
                    directory.resolve(link, dash=('.mpd' in link or 'dash' in link))
                    break
                except Exception:
                    continue
            else:
                try:
                    log_debug('Resolvers failed to resolve stream, trying playing it directly')
                    directory.resolve(url, dash=('.mpd' in url or 'dash' in url))
                    break
                except Exception:
                    log_debug('Playback failed')
                    break

elif action == 'install_youtube-dl':

    if control.condVisibility('System.HasAddon(script.module.youtube.dl)'):
        control.infoDialog(control.lang(30030))
    else:
        control.execute('RunPlugin(plugin://script.module.youtube.dl)')

elif action == 'install_resolveurl':

    if control.condVisibility('System.HasAddon(script.module.resolveurl)'):
        control.infoDialog(control.lang(30031))
    else:
        control.execute('RunPlugin(plugin://script.module.resolveurl)')

elif action == 'install_streamlink':

    if control.condVisibility('System.HasAddon(script.module.streamlink.base)'):
        control.infoDialog(control.lang(30026))
    else:
        control.execute('RunPlugin(plugin://script.module.streamlink.base)')

elif action == 'ytdl_settings':

    if not control.condVisibility('System.HasAddon(script.module.youtube.dl)'):
        control.infoDialog(control.lang(30036))
    else:
        control.Settings('script.module.youtube.dl')

elif action == 'resolveurl_settings':

    if not control.condVisibility('System.HasAddon(script.module.resolveurl)'):
        control.infoDialog(control.lang(30037))
    else:
        control.Settings('script.module.resolveurl')

elif action == 'settings':

    control.openSettings()

elif action == 'refresh':

    control.refresh()

elif action == 'switcher':

    control.dialog.notification(heading=control.addonInfo('name'), message=control.lang(30020), time=1500, sound=False)
    control.busy()
    switcher()

elif action == 'cache_clear':

    if control.yesnoDialog(line1=control.lang(30028), line2='', line3=''):

        control.deleteFile(control.cacheFile)

    else:

        control.infoDialog(control.lang(30029))

elif action == 'quit':

    control.quit_kodi()
