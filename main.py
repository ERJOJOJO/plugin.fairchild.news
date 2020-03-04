import sys
import re
from collections import defaultdict
import xbmcgui
import xbmcplugin
import xbmc
import json
import simplecache
import datetime
import calendar
import requests
from bs4 import BeautifulSoup

# import parse
# from urllib.parse import urlencode
# from urllib.parse import parse_qsl

# Get the plugin url in plugin:// notation.
_url = sys.argv[0]
# Get the plugin handle as an integer number.
_handle = int(sys.argv[1])
# instantiate the cache
_cache = simplecache.SimpleCache()

class NewsUrl:  
    def __init__(self, newsArea, newsAreaUrl):
        self.newsArea = newsArea
        self.newsAreaUrl = newsAreaUrl
class NewsVideoList:
    def __init__(self, videos):
        self.videos = videos
    @classmethod
    def from_json(cls, data):
        videos = list(map(NewsDetail.from_json, data["videos"]))
        return cls(videos)

class NewsDetail:  
    def __init__(self, newsArea, newsDate, newsText, newsUrl, thumb, genre, newsVideo):
        self.newsArea = newsArea
        self.newsDate = newsDate
        self.newsText = newsText
        self.newsUrl = newsUrl
        self.thumb = thumb
        self.genre = genre
        self.newsVideo = newsVideo
    def __eq__(self, other):
        return self.newsArea == other.newsArea and self.newsDate == other.newsDate and self.newsText == other.newsText and self.newsUrl == other.newsUrl and self.thumb == other.thumb and self.genre == other.genre and self.newsVideo == other.newsVideo
    def __lt__(self, other):
        return self.newsDate < other.newsDate 
    def setNewsVideo(self, newsVideo):
        self.newsVideo = newsVideo
    @classmethod
    def from_json(cls, data):
        return cls(**data)

westernUrl = 'https://www.fairchildtv.com/english/news.php'
easternUrl = 'https://www.fairchildtv.com/english/news.php?prov=toronto&type=eastern'
canadaUrl = 'https://www.fairchildtv.com/english/news.php?prov=toronto&type=whole_canada'
internationalUrl = 'https://www.fairchildtv.com/english/news.php?prov=toronto&type=international'
otherUrl = 'https://www.fairchildtv.com/english/news.php?prov=toronto&type=other'

links = []
links.append(NewsUrl('west', westernUrl))
links.append(NewsUrl('east', easternUrl))
links.append(NewsUrl('canada', canadaUrl))
links.append(NewsUrl('international', internationalUrl))
links.append(NewsUrl('other', otherUrl))

newsLists = []
videosList = defaultdict(list)
newsVideo = NewsVideoList(None)

def setVideoList(newsList):
    for news in newsList:
        monthDay = news.newsDate.split(" ")
        monthNumber = list(calendar.month_abbr).index(monthDay[0])
    	videosList[str(monthNumber) + "-" + monthDay[1] + ": " + news.newsArea].append(news)
    xbmc.log('videosList: ' + json.dumps(videosList, default=lambda o: o.__dict__))

def getNewLists():
	for url in links:
		response = requests.get(url.newsAreaUrl)
		soup = BeautifulSoup(response.text, "html.parser")

		for newsULs in soup.findAll('ul', attrs={'class':'newsList'}):
			for newsLis in newsULs.find_all('li'):
				for newsPs in newsLis.find_all('p'):
					for newsSpans in newsPs.find_all('span'):
						newsDate = newsSpans.text
					for newsAs in newsPs.find_all('a'):
						newsText = newsAs.text
						newsUrl = newsAs['href']
				newsLists.append(NewsDetail(url.newsArea, newsDate, newsText, newsUrl, 'https://www.fairchildtv.com/images/site-logo.png', 'News', ''))
    
	newsSortedLists = sorted(newsLists)
    
	for news in newsSortedLists:
		response = requests.get('https://www.fairchildtv.com/english/' + news.newsUrl)
		soup = BeautifulSoup(response.text, "html.parser")
    
		for video in soup.findAll('video'):
			news.setNewsVideo('https:' + video.source['src'])

	newsVideo.videos = newsSortedLists
	setVideoList(newsVideo.videos)

def play_video(path):
    """
    Play a video by the provided path.

    :param path: Fully-qualified video URL
    :type path: str
    """
    # Create a playable item with a path to play.
    play_item = xbmcgui.ListItem(path=path)
    # Pass the item to the Kodi player.
    xbmcplugin.setResolvedUrl(_handle, True, listitem=play_item)

def get_categories():
    """
    Get the list of video categories.

    Here you can insert some parsing code that retrieves
    the list of video categories (e.g. 'Movies', 'TV-shows', 'Documentaries' etc.)
    from some site or server.

    .. note:: Consider using `generator functions <https://wiki.python.org/moin/Generators>`_
        instead of returning lists.

    :return: The list of video categories
    :rtype: types.GeneratorType
    """
    return sorted(videosList.keys(), reverse=True)

def get_videos(category):
    """
    Get the list of videofiles/streams.

    Here you can insert some parsing code that retrieves
    the list of video streams in the given category from some site or server.

    .. note:: Consider using `generators functions <https://wiki.python.org/moin/Generators>`_
        instead of returning lists.

    :param category: Category name
    :type category: str
    :return: the list of videos in the category
    :rtype: list
    """
    return videosList[category]

def get_url(paramstring):
    """
    Create a URL for calling the plugin recursively from the given set of keyword arguments.

    :param paramstring: "argument=value"
    :return: plugin call URL
    :rtype: str
    """
    # return '{0}?{1}'.format(_url, parse.urlencode(kwargs))
    return '{0}?{1}'.format(_url, paramstring)

def list_categories():
    """
    Create the list of video categories in the Kodi interface.
    """
    # Set plugin category. It is displayed in some skins as the name
    # of the current section.
    xbmcplugin.setPluginCategory(_handle, 'Fairchild News Video Collection')
    # Set plugin content. It allows Kodi to select appropriate views
    # for this type of content.
    xbmcplugin.setContent(_handle, 'videos')
    # Get video categories
    categories = get_categories()
    # Iterate through categories
    for category in categories:
        # Create a list item with a text label and a thumbnail image.
        list_item = xbmcgui.ListItem(label=category)
        # Set graphics (thumbnail, fanart, banner, poster, landscape etc.) for the list item.
        # Here we use the same image for all items for simplicity's sake.
        # In a real-life plugin you need to set each image accordingly.
        list_item.setArt({'thumb': videosList[category][0].thumb,
                          'icon': videosList[category][0].thumb,
                          'fanart': videosList[category][0].thumb})
        # Set additional info for the list item.
        # Here we use a category name for both properties for for simplicity's sake.
        # setInfo allows to set various information for an item.
        # For available properties see the following link:
        # https://codedocs.xyz/xbmc/xbmc/group__python__xbmcgui__listitem.html#ga0b71166869bda87ad744942888fb5f14
        # 'mediatype' is needed for a skin to display info for this ListItem correctly.
        list_item.setInfo('video', {'title': category,
                                    'genre': category,
                                    'mediatype': 'video'})
        # Create a URL for a plugin recursive call.
        # Example: plugin://plugin.video.example/?action=listing&category=Animals
        url = get_url("action=listing&category=" + category)
        # is_folder = True means that this item opens a sub-list of lower level items.
        is_folder = True
        # Add our item to the Kodi virtual folder listing.
        xbmcplugin.addDirectoryItem(_handle, url, list_item, is_folder)
    # Add a sort method for the virtual folder items (alphabetically, ignore articles)
    xbmcplugin.addSortMethod(_handle, xbmcplugin.SORT_METHOD_NONE)
    # Finish creating a virtual folder.
    xbmcplugin.endOfDirectory(_handle)
	
def list_videos(category):
    """
    Create the list of playable videos in the Kodi interface.

    :param category: Category name
    :type category: str
    """
    # Set plugin category. It is displayed in some skins as the name
    # of the current section.
    xbmcplugin.setPluginCategory(_handle, category)
    # Set plugin content. It allows Kodi to select appropriate views
    # for this type of content.
    xbmcplugin.setContent(_handle, 'videos')
    # Get the list of videos in the category.
    videos = get_videos(category.replace("%3a%20", ": "))
    # Iterate through videos.
    for video in videos:
        # Create a list item with a text label and a thumbnail image.
        list_item = xbmcgui.ListItem(label=video.newsText)
        # Set additional info for the list item.
        # 'mediatype' is needed for skin to display info for this ListItem correctly.
        list_item.setInfo('video', {'title': video.newsText,
                                    'genre': video.genre,
                                    'mediatype': 'video'})
        # Set graphics (thumbnail, fanart, banner, poster, landscape etc.) for the list item.
        # Here we use the same image for all items for simplicity's sake.
        # In a real-life plugin you need to set each image accordingly.
        list_item.setArt({'thumb': video.thumb, 'icon': video.thumb, 'fanart': video.thumb})
        # Set 'IsPlayable' property to 'true'.
        # This is mandatory for playable items!
        list_item.setProperty('IsPlayable', 'true')
        # Create a URL for a plugin recursive call.
        # Example: plugin://plugin.video.example/?action=play&video=http://www.vidsplay.com/wp-content/uploads/2017/04/crab.mp4
        url = get_url("action=play&video=" + video.newsVideo)
        # Add the list item to a virtual Kodi folder.
        # is_folder = False means that this item won't open any sub-list.
        is_folder = False
        # Add our item to the Kodi virtual folder listing.
        xbmcplugin.addDirectoryItem(_handle, url, list_item, is_folder)
    # Add a sort method for the virtual folder items (alphabetically, ignore articles)
    xbmcplugin.addSortMethod(_handle, xbmcplugin.SORT_METHOD_LABEL_IGNORE_THE)
    # Finish creating a virtual folder.
    xbmcplugin.endOfDirectory(_handle)

def router(paramstring):
    """
    Router function that calls other functions
    depending on the provided paramstring

    :param paramstring: URL encoded plugin paramstring
    :type paramstring: str
    """
    # Parse a URL-encoded paramstring to the dictionary of
    # {<parameter>: <value>} elements
    # params = dict(parse.parse_qsl(paramstring))
    
    if paramstring != '':
        params = dict(pair.split('=') for pair in paramstring.split('&'))
    else:
        params = ''
    
    # Check the parameters passed to the plugin
    if params:
        if params['action'] == 'listing':
            # Display the list of videos in a provided category.
            xbmc.log('list_videos')
            list_videos(params['category'])
        elif params['action'] == 'play':
            # Play a video from a provided URL.
            xbmc.log('play_video')
            play_video(params['video'])
        else:
            # If the provided paramstring does not contain a supported action
            # we raise an exception. This helps to catch coding errors,
            # e.g. typos in action names.
            raise ValueError('Invalid paramstring: {0}!'.format(paramstring))
    else:
        # If the plugin is called from Kodi UI without any parameters,
        # display the list of video categories
        xbmc.log('list_categories')
        list_categories()

if __name__ == '__main__':
    # Call the router function and pass the plugin call parameters to it.
    # We use string slicing to trim the leading '?' from the plugin call paramstring
    cachedVideoJson = _cache.get("cached.video.json")
    
    if cachedVideoJson:
        xbmc.log('Cached newsVideo exist')
        xbmc.log(cachedVideoJson)
        newsVideo = NewsVideoList.from_json(json.loads(cachedVideoJson))
        setVideoList(newsVideo.videos)
        xbmc.log(json.dumps(newsVideo, default=lambda o: o.__dict__, sort_keys=True))
        router(sys.argv[2][1:])
    
    if not newsVideo.videos:
        xbmc.log('newsVideo is empty')
        getNewLists()
        cachedVideoJson = json.dumps(newsVideo, default=lambda o: o.__dict__, sort_keys=True)
        xbmc.log(cachedVideoJson)
        _cache.set("cached.video.json", cachedVideoJson, expiration=datetime.timedelta(hours=1))
        router(sys.argv[2][1:])