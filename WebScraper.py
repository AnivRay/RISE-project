import urllib2
from bs4 import BeautifulSoup
import time

main_page = "https://kodi.tv/addons/browse?keyword=&category=All&author=&sort=field_download_count_value%20DESC&page=3"
opener = urllib2.build_opener()
opener.addheaders = [('User-Agent', 'Mozilla/5.0')]
page = opener.open(main_page)
# print page.read()
soup = BeautifulSoup(page, "html.parser")
soup.findAll("a")
for i in range(30, 66):  # 66
    addon_url = "https://kodi.tv" + soup.findAll("a")[i].get("href")
    urllist = str(addon_url).split("/")
    addon_name = urllist[-1]
    print "Downloaded " + addon_name + " from:"
    # addon_page = opener.open(addon_url)
    addon_page = urllib2.Request(addon_url, headers={"User-Agent" : "Mozilla/5.0"})
    addon_page_content = urllib2.urlopen(addon_page).read()
    soup2 = BeautifulSoup(addon_page_content, "html.parser")
    for x in soup2.findAll("a"):
        download_url = x.get("href")
        if str(download_url).startswith("http://mirrors.kodi.tv"):
            print download_url
            request = urllib2.Request(download_url, headers={"User-Agent": "Mozilla/5.0"})
            filedata = urllib2.urlopen(request)
            data = filedata.read()
            with open("C:\\Users\\anivr\\OneDrive\\Desktop\\Kodi Add-Ons\\AutoDownload2\\" + addon_name + ".zip", "wb") as f:
                f.write(data)
    time.sleep(1)
