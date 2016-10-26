# This fetch tries to load all the videos,
# not just which are in playlists,
# and not just the first 100 from a playlist
import hashlib
import zlib
import os
import requests
from lxml import html
import re
import json

hollywoodNewsAgency_user = "HollywoodNewsAgency"
thevr_user = "thevrhu"

user_to_fetch = thevr_user


base_url = 'https://www.youtube.com'
user_playlists_url = "/user/{}/playlists"
user_videos_url = "/user/{}/videos"
video_id_url = "/watch?v={}"
playlist_id_url = "/playlist?list={}"

video_selectors = {
    "nviews": '//*[@id="watch7-views-info"]/div[1]',
    "nlike": '//*[@id="watch8-sentiment-actions"]/span/span[1]/button/span',
    "ndislike": '//*[@id="watch8-sentiment-actions"]/span/span[3]/button/span',
    "date": '//*[@id="watch-uploader-info"]/strong',
}

video_fetch_data = {
    'selector_global': '//*[@id="channels-browse-content-grid"]/li[*]/div/div[1]',
    'selector_relative': 'li[*]/div/div[1]',
    'more_selector': '//*[@id="browse-items-primary"]/li[2]/button',
    'more_attrib': 'data-uix-load-more-href',
    'more_regex': 'data-uix-load-more-href="([^"]*)"'
}

user_playlists_fetch_data = {
    'selector_global': '//*[@id="channels-browse-content-grid"]/li[*]/div/div[1]/div[2]/h3/a',
    'selector_relative': 'li[*]/div/div[1]/div[2]/h3/a',
    'more_selector': '//*[@id="browse-items-primary"]/li[2]/button',
    'more_attrib': 'data-uix-load-more-href',
    'more_regex': 'data-uix-load-more-href="([^"]*)"'
}

playlist_fetch_data = {
    'selector_global': '//*[@id="pl-load-more-destination"]/tr[*]',
    'selector_relative': 'tr[*]',
    'more_selector': '//*[@id="pl-video-list"]/button',
    'more_attrib': 'data-uix-load-more-href',
    'more_regex': 'data-uix-load-more-href="([^"]*)"'
}


def main():
    playlists_url = base_url + user_playlists_url.format(user_to_fetch)
    videos_url = base_url + user_videos_url.format(user_to_fetch)

    print("Fetch all playlist title and name")
    res = fetch_all(playlists_url, **user_playlists_fetch_data)
    playlist_data = map(extract_playlist_id_name, res)
    print len(playlist_data), " playlist data fetched."

    print("\nFetch all video id in all playlist")
    for playlist in playlist_data:
        playlist_url = base_url + playlist_id_url.format(playlist["id"])
        res = fetch_all(playlist_url, **playlist_fetch_data)
        playlist["video"] = [extract_playlist_video(x) for x in res]
        print len(playlist["video"]), " video data fetched for playlist: ",\
              playlist["title"]

    print("\nFetch all video id, title and length")
    res = fetch_all(videos_url, **video_fetch_data)
    video_data = map(extract_video_id_length_name, res)
    print len(video_data), " video data fetched"


    # with open("video.json", "w") as f:
    #     f.write(json.dumps(video_data, indent=2))
    #
    # with open("playlist.json", "w") as f:
    #     f.write(json.dumps(playlist_data, indent=2))

    # with open("video.json", "r") as f:
    #     video_data = json.loads(f.read())
    #
    # with open("playlist.json", "r") as f:
    #     playlist_data = json.loads(f.read())

    all_video = set([x["id"] for x in video_data])
    playlist_video = set()

    for playlist in playlist_data:
        for video in playlist["video"]:
            playlist_video.add(video["id"])

    not_in_any_playlist = all_video - playlist_video
    print "\nnot_in_any_playlist ", len(not_in_any_playlist)

    print "\nAdding extra playlist, with the name and id n.a. " \
          "to easily store videos not in any playlist"
    extra_playlist = {
        "id": "n.a.",
        "title": "Not in any playlist",
        "video": list(not_in_any_playlist)
    }

    i = 0
    print("\nFetch video data: like, dislike, view, date")
    for playlist in playlist_data:
        i += 1
        j = 0
        for video in playlist["video"]:
            j += 1
            print "playlist {} from {}, video {} from {} playlist: ".format(
                i, len(playlist_data),
                j, len(playlist["video"])),\
                playlist["title"],\
                " video: ",\
                video["title"]
            playlist_video.add(video["id"])
            video.update(get_video_data(video["id"]))

    # with open("playlist.json", "w") as f:
    #     f.write(json.dumps(playlist_data, indent=2))

    # with open("playlist.json", "r") as f:
    #     playlist_data = json.loads(f.read())

    with open("all_data.json", "w") as f:
         f.write(json.dumps(playlist_data, indent=2))


def fetch_video_comments(video_id):
    comment_reply_fetch_skeleton = "https://www.googleapis.com/youtube/v3/commentThreads?part=replies&maxResults=100&textFormat=plainText&videoId={}&key=AIzaSyDZkl-q8jZPEymHlAbsPVefLKH4l0V-r8s"
    comment_fetch_skeleton = "https://www.googleapis.com/youtube/v3/commentThreads?part=snippet&maxResults=100&textFormat=plainText&videoId={}&key=AIzaSyDZkl-q8jZPEymHlAbsPVefLKH4l0V-r8s"
    url = comment_fetch_skeleton.format(video_id)
    page = zip_cache_page(url)
    data = json.loads(page)
    comment = [x["snippet"]["topLevelComment"]["snippet"]["textDisplay"]
                    for x in data["items"]]
    other_keys = ["textDisplay", "publishedAt", "likeCount", "authorChannelId", "authorDisplayName"]

    while "nextPageToken" in data:
        url = comment_fetch_skeleton.format(video_id) +\
              "&nextPageToken="+data["nextPageToken"]
        page = zip_cache_page(url)
        data = json.loads(page)

        comment.extend([x["snippet"]["topLevelComment"]["snippet"]["textDisplay"]
                   for x in data["items"]])

    return comment


def extract_playlist_video(htmlTree):
    relative_name_selector = 'td[4]/a'
    relative_length_selector = 'td[7]/div/div[1]/span'
    name = htmlTree.xpath(relative_name_selector)[0]
    length_field = htmlTree.xpath(relative_length_selector)
    return {
        "title": name.text.strip().rstrip(),
        "length": length_field[0].text if len(length_field) > 0 else "n.a.",
        "id": name.attrib["href"].split("=")[1].split("&")[0]
    }


def extract_playlist_id_name(htmlTree):
    return {
        "id": htmlTree.attrib["href"].split("=")[1],
        "title": htmlTree.text
    }


def extract_video_id_length_name(htmlTree):
    return {
        "id": htmlTree.xpath('div[2]/h3/a')[0].attrib["href"].split("=")[1],
        "length": htmlTree.xpath('div[1]/span/span[1]/span')[0].text,
        "title": htmlTree.xpath('div[2]/h3/a')[0].text.strip().rstrip()
    }


def get_video_data(video_id):
    url = base_url + video_id_url.format(video_id)
    page = zip_cache_page(url)
    tree = html.fromstring(page)
    video_data = {}

    for key, selector in video_selectors.items():
        data = tree.xpath(selector)
        data = data[0].text if len(data) > 0 else "n.a."
        video_data[key] = data

    video_data["ncomments"] = len(fetch_video_comments(video_id))

    return video_data


def fetch_more(url, selector, more_regex):
    # Download content
    page = zip_cache_page(url)
    content = json.loads(page)
    load_more_btn = content["load_more_widget_html"]
    more_content = content["content_html"]

    # Extract received videos
    tree = html.fromstring(more_content)
    loaded = tree.xpath(selector)

    # Extract link to further more video
    matched_groups = re.search(more_regex, load_more_btn)

    # When no more data, return with None link
    if matched_groups is None:
        return loaded, None

    load_more_link = base_url + matched_groups.group(1).replace("&amp;", "&")

    return loaded, load_more_link


def fetch_all(url, selector_global, selector_relative,
              more_selector, more_attrib, more_regex):
    # Loading page
    page = zip_cache_page(url)
    tree = html.fromstring(page)

    # Extracting
    all_items = tree.xpath(selector_global)

    # Extracting link for loading more
    load_more_btn = tree.xpath(more_selector)
    if len(load_more_btn) > 0:
        load_more_link = load_more_btn[0].attrib[more_attrib]
        load_more_link = base_url + load_more_link
    else:
        load_more_link = None

    # Fetch more until we got them all
    while load_more_link is not None:
        more_items, load_more_link = fetch_more(load_more_link,
                                                selector_relative,
                                                more_regex)
        all_items.extend(more_items)

    return all_items


def my_hash(text):
    hash_digest = hashlib.sha1(text.encode('utf-8')).hexdigest()
    return hash_digest


def zip_cache_page(url):
    url_hash = my_hash(url)
    filename = "zip_cache/" + url_hash + ".html"

    # If webpage was cached before, load it from cache
    if os.path.isfile(filename):
        with open(filename, 'rb') as f:
            return zlib.decompress(f.read()).decode("utf-8")

    # Else download it and save to cache
    page = requests.get(url, headers={"Accept-Language": "en-US"})
    with open(filename, 'wb') as f:
        text = zlib.compress(page.content, 9)
        f.write(text)
    return page.content


if __name__ == '__main__':
    main()