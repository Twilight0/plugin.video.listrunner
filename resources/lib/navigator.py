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
from tulip import client, youtube, cache, control
from tulip.directory import add
from tulip.compat import OrderedDict

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
    elif control.setting('local_or_remote') == '2':
        if not control.setting('youtube_url'):
            return
        else:
            return cache.get(
                yt_playlist_getter, int(control.setting('caching')) if int(control.setting('caching')) > 0 else 0,
                control.setting('youtube_url')
            )
    else:
        return

    if not text.startswith(('#EXTM3U', '#EXTCPlayListM3U::M3U')):
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

    # trimmed_groups.sort()

    if len(trimmed_groups) == 1:
        control.setSetting('group', 'ALL')
        return items_list
    else:
        return items_list, trimmed_groups


def switcher():

    def seq(choose):

        control.setSetting('group', choose)
        control.sleep(50)
        control.refresh()

    groups = [control.lang(30016)] + cache.get(constructor, int(control.setting('caching')) if int(control.setting('caching')) > 0 else 0)[1]

    choice = control.dialog.select(heading=control.lang(30017), list=groups)

    if choice == 0:
        seq('ALL')
    elif choice <= len(groups) and not choice == -1:
        seq(groups[choice])
    else:
        control.idle()


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

    if control.setting('show_switcher') == 'false':

        switcher_menu = []

    else:

        switcher_menu = [
            {
                'title': control.lang(30015).format(control.lang(30016) if control.setting('group') == 'ALL' else group_setting),
                'image': control.join(control.addonPath, 'resources', 'media', 'switcher.png'), 'action': 'switcher'
            }
        ]

    if not control.setting('local') and not control.setting('remote') and not control.setting('youtube_url'):

        items = root_menu + null

    else:

        try:

            output = cache.get(constructor, int(control.setting('caching')) if int(control.setting('caching')) > 0 else 0)

            if not output:
                items = root_menu + null
            elif len(output) == 2:
                filtered = [
                    i for i in output[0] if any(i['group'] == selected for selected in [group_setting])
                ] if not control.setting('group') == 'ALL' else output[0]
                items = root_menu + switcher_menu + filtered
            else:
                items = root_menu + output

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

    try:
        if len(output) == 2:
            control.sortmethods('genre')
    except Exception:
        pass

    add(items)
