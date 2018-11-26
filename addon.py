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

# TODO: Add support for more playlist formats

import re
from tulip import control
from tulip.directory import resolve
from tulip.init import params
from tulip.compat import quote, urlencode
from tulip.log import log_debug
from resources.lib.navigator import main_menu, switcher

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
        resolve(url)

    else:

        for i in ['resolveurl', 'youtube-dl', 'streamlink', 'unresolvable']:
            if resolveurl is not None and i == 'resolveurl':
                if resolveurl.HostedMediaFile(url).valid_url():
                    try:
                        link = resolveurl.resolve(url)
                        resolve(link, dash=('.mpd' in link or 'dash' in link))
                        break
                    except Exception:
                        continue
            elif YDStreamExtractor is not None and i == 'youtube-dl':
                try:
                    stream = YDStreamExtractor.getVideoInfo(url)
                    link = stream.streamURL()
                    # title = stream.selectedStream()['title']
                    # icon = stream.selectedStream()['thumbnail']
                    resolve(link, dash=('.mpd' in link or 'dash' in link))
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
                    resolve(link, dash=('.mpd' in link or 'dash' in link))
                    break
                except Exception:
                    continue
            else:
                try:
                    log_debug('Resolvers failed to resolve stream, trying playing it directly')
                    resolve(url, dash=('.mpd' in url or 'dash' in url))
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

    switcher()

elif action == 'cache_clear':

    if control.yesnoDialog(line1=control.lang(30028), line2='', line3=''):

        control.deleteFile(control.cacheFile)

    else:

        control.infoDialog(control.lang(30029))

elif action == 'quit':

    control.quit_kodi()
