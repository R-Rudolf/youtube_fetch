import requests
from lxml import html
import json
import hashlib
import os.path
import zlib
import time

lowko_channel = 'lowkotv'
gameDay_user = "GameDayIroda"
hollywoodNewsAgency_user = "HollywoodNewsAgency"
# A legtobb video nincs kulon lejatszasi listaban :(
videomania_user = "VideomaniaFCS"

playlists_url_channel = "/c/{}/playlists"
playlists_url_user = "/user/{}/playlists"

playlists_url_skeleton = playlists_url_user
fetched_channel = videomania_user


base_url = 'https://www.youtube.com'

playlist_selector = '//*[@id="channels-browse-content-grid"]/li[*]/div/div[1]/div[2]/h3/a'

video_selector = '//*[@id="pl-load-more-destination"]/tr[*]/td[4]/a'
video_line_selector = '//*[@id="pl-load-more-destination"]/tr[{}]'
relative_name_selector = '/td[4]/a'
relative_length_selector = '/td[7]/div/div[1]/span'

video_selectors = {
    "nviews": '//*[@id="watch7-views-info"]/div[1]',
    "nlike": '//*[@id="watch8-sentiment-actions"]/span/span[1]/button/span',
    "ndislike": '//*[@id="watch8-sentiment-actions"]/span/span[3]/button/span',
    "date": '//*[@id="watch-uploader-info"]/strong',
    #"length": '//*[@id="movie_player"]/div[24]/div[2]/div[1]/div/span[3]'
    #"ncomment": '//*[@id="comment-section-renderer"]/h2'
}


def main():

    # get playlist list with url, title, maybe with id
    playlists = get_playlists(fetched_channel)
    print("Playlists of channel " + fetched_channel + " successfully loaded.")

    # print("Playlist data example:")
    # print(json.dumps(playlists, indent=2) + "\n")
    # exit(0)

    # in a loop get the videos of the playlists with url, title, maybe with id
    #videos = get_playlist_videos(playlists[0]["href"])

    # print("Video basic data example:")
    # print(json.dumps(videos[0], indent=2) + "\n")
    # exit(0)

    videos = []
    for playlist in playlists:
       new_videos = get_playlist_videos(playlist["href"])
       videos.extend(new_videos)
       playlist["video"] = new_videos
       print("Playlist successfully loaded: "+playlist["title"])

    print("\n------\nNext step: Downloading video data like views...")
    # in a loop get the details of the videos, likes, dislikes, views, date
    # video_data = get_video_data(videos[-1]["href"])
    #
    # print("Video extra data example:")
    # print(json.dumps(video_data, indent=2))

    i = 0
    for video in videos:
        extra_data = get_video_data(video["href"])
        video.update(extra_data)
        print(str(i+1)+". from "+str(len(videos))+" Video data loaded for: "+
              video["title"].replace("\n", ""))
        i += 1

    # Save fetched data into json
    with open("all_data.json", "w") as f:
        f.write(json.dumps(playlists, indent=2))


def get_video_data(video_url):
    url = base_url + video_url
    page = cache_page(url)
    video_data = {}

    for key, selector in video_selectors.items():
        data = get_text_attrib_list(page, selector)
        if len(data) < 1:
            print("Data not found for selector: "+key+" on webpage: "+url)
            continue
        data = data[0]["title"]
        video_data[key] = data
    return video_data


def get_playlist_videos(playlist_url):
    url = base_url + playlist_url
    page = cache_page(url)
    #video_data = get_text_attrib_list(page, video_selector)
    video_data = get_video_with_length(page)

    for video in video_data:
        video.update(extract_data(video["attrib"], ["href"]))

    return video_data


def get_playlists(channel_name):
    url = base_url + playlists_url_skeleton.format(channel_name)
    page = cache_page(url)
    playlist_data = get_text_attrib_list(page, playlist_selector)

    for data in playlist_data:
        data.update(extract_data(data["attrib"], ["href"]))

    return playlist_data


def get_video_with_length(page):
    tree = html.fromstring(page)
    selected_items = tree.xpath(video_line_selector.format('*'))
    length = len(selected_items)
    results = []
    for i in range(length):
        xpath = video_line_selector.format(i+1)  # HTML element numbering starts from 1
        name = tree.xpath(xpath+relative_name_selector)[0]
        length = tree.xpath(xpath+relative_length_selector)
        length = length[0].text if len(length) > 0 else "n.a."
        results.append({
            "title": name.text,
            "attrib": str(name.attrib),
            "length": length
        })

    return results


def cache_page(url):
    return zip_cache_page(url)

    url_hash = my_hash(url)
    filename = "cache/" + url_hash + ".html"

    # If webpage was cached before, load it from cache
    if os.path.isfile(filename):
        with open(filename, 'r') as f:
            return f.read()

    # Else download it and save to cache
    page = my_get(url)
    with open(filename, 'w') as f:
        f.write(page.content)
    return page.content


def my_get(url):
    i = 1
    while True:
        try:
            page = requests.get(url, headers = {"Accept-Language": "en-US"})
            break
        except Exception:
            i += 1
            if i % 80 == 0:
                print ".",
            if i > 80*60:
                i = 1
                print "\n"
                print url
    return page


def get_text_attrib_list(page, xpath):
    tree = html.fromstring(page)
    selected_items = tree.xpath(xpath)
    result = [{   "title": x.text,
                  "attrib": str(x.attrib)
              } for x in selected_items]
    return result


def extract_data(attributes, keys):
    extracted = {}
    for attribute in attributes.split(", "):
        attribute = attribute.replace("'", "")
        colonIndex = attribute.find(": ")

        key = attribute[:colonIndex]
        value = attribute[colonIndex+2:]

        for needed_key in keys:
            if needed_key in key:
                extracted[needed_key] = value

    return extracted


def my_hash(text):
    hash_digest = hashlib.sha1(text.encode('utf-8')).hexdigest()
    return hash_digest


def zip_cache_page(url):
    url_hash = my_hash(url)
    filename = "zip_cache/" + url_hash + ".html"

    # If webpage was cached before, load it from cache
    if os.path.isfile(filename):
        with open(filename, 'rb') as f:
            return zlib.decompress(f.read())

    # Else download it and save to cache
    page = my_get(url)
    with open(filename, 'w') as f:
        text = zlib.compress(page.content, 9)
        f.write(text)
    return page.content


def zip_cache_convert():
    files = os.listdir('cache/')
    i = 0
    for file in files:
        with open('cache/'+file, "r")as f:
            text = f.read()
            with open('zip_cache/'+file, "wb") as fz:
                fz.write(zlib.compress(text, 9))
        i += 1
        print("{} out of {} done: {}".format(i, len(files), file))


if __name__ == '__main__':
    start = time.time()

    #  zip_cache_convert()
    main()

    end = time.time()
    print("Time: "+str(end-start))
