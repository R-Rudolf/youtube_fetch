import json
import csv

from_file = "all_data.json"
to_file = "all_data.csv"

# Output will be a csv
# All line is a video
# All video data is a column:
#  - playlist name
#  - playlist id
#  - title
#  - youtube id
#  - date
#  - length
#  - nview
#  - nlike
#  - ndislike

header = [
          'playlist_name',
          'playlist_id',
          'title',
          'video_id',
          'date',
          'length',
          'nview',
          'nlike',
          'ndislike'
          ]

month_names = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
         'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']


def main():

    with open(from_file, "r") as f:
        raw_data = json.loads(f.read())
    print "Input file readed: ", from_file

    # Extracts the hierarchical data to a plain list
    deflated_data = deflate(raw_data)

    new_data = map(clean_data, deflated_data)

    final_data = filter(lambda x: x[2] != "[Private Video]", new_data)

    print "Data converted"

    save_data(final_data, to_file)
    print "Output file created: ", to_file

    # Print out for manual check
    # for video in new_data:
    #     # print "------------------"
    #     i = -1
    #     for name in header:
    #         i += 1
    #         # if name != "length":
    #         #     continue
    #         print "{:<15}{}".format(name, video[i].encode('utf-8'))


def save_data(data, filename):
    with open(filename, 'wt') as f:
        writer = csv.writer(f)
        writer.writerow(header)
        for video in data:
            writer.writerow(video)


def clean_data(data):
    """
    "title": "Let's play World of Warcraft",
    "href": "/playlist?list=PLT0hfPWJS6_sJmK5m_4R99RIswmKSO8_g",
        "title": "\n      World of Warcraft: A Change Of Plans - Ep. 8! (Let's Play WoW)\n    ",
        "nlike": "70",
        "length": "41:52",
        "href": "/watch?v=Y-4HdfdDi5g&list=LLZNTsLA6t6bRoj-5QRmqt_w&index=1",
        "nviews": "657 views",
        "date": "Published on Jul 19, 2016",
        "attrib": "{'href': '/watch?v=Y-4HdfdDi5g&list=LLZNTsLA6t6bRoj-5QRmqt_w&index=1', 'class': 'pl-video-title-link yt-uix-tile-link yt-uix-sessionlink  spf-link ', 'dir': 'ltr', 'data-sessionlink': 'ei=2GOOV87mOYODoQO4-YqIBA&feature=plpp_video&ved=CBUQxjQYACITCM6ytJiHgM4CFYNBaAoduLwCQSj6LA'}",
        "ndislike": "3"
    """
    for i in range(len(data)):
        data[i] = data[i].encode('utf-8')

    #  Playlist ID
    data[1] = data[1]#[str(data[1]).find("=")+1:]

    # Video title
    data[2] = data[2].strip().lstrip()

    # Video ID
    data[3] = data[3]#[str(data[3]).find("=")+1:str(data[3]).find("&")]

    # Date
    if data[4] != "n.a.":
        year = data[4][-4:]
        if "live" in data[4]:
            day = data[4].split(" ")[4].replace(",", "")
            month = data[4].split(" ")[3]
            month = str(month_names.index(month)+1)
        else:
            day = data[4].split(" ")[3].replace(",", "")
            month = data[4].split(" ")[2]
            month = str(month_names.index(month)+1)
        data[4] = year+"."+month+"."+day

    # Length
    if data[5] != "n.a.":
        time_splits = str(data[5]).split(":")
        # hom many times should be the first number multiplied by 60
        split_mult = len(time_splits)
        length = 0
        for split in time_splits:
            split_mult -= 1
            length += (60**split_mult)*int(split)
        data[5] = str(length)

    # Views
    data[6] = data[6][:data[6].find(' ')].replace(",", "")

    # Likes
    data[7] = data[7].replace(",", "")

    # Dislikes
    data[8] = data[8].replace(",", "")

    return data


def deflate(data_in):
    data_out = []

    for playlist in data_in:
        if playlist["title"] == "Liked videos":
            continue
        for video in playlist["video"]:
            if "date" not in video:
                continue
            if "length" not in video:
                continue

            new_video = [
                playlist["title"],  # playlist name
                playlist["id"],  # playlist link --> includes playlist ID
                video["title"],  # video name
                video["id"],  # video link --> includes video ID
                video["date"],  # video release date
                video["length"],  # video length
                video["nviews"],  # number of video views
                video["nlike"],  # number of video likes
                video["ndislike"]  # number of video dislikes
            ]
            data_out.append(new_video)
            #return data_out

    return data_out


if __name__ == '__main__':
    main()
