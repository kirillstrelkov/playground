import codecs
import json
import os
import traceback

from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

# The CLIENT_SECRETS_FILE variable specifies the name of a file that contains
# the OAuth 2.0 information for this application, including its client_id and
# client_secret.
from utils.csv import save_dicts

CLIENT_SECRETS_FILE = "client_secret.json"

# This OAuth 2.0 access scope allows for full read/write access to the
# authenticated user's account and requires requests to use an SSL connection.
SCOPES = ["https://www.googleapis.com/auth/youtube.force-ssl"]
API_SERVICE_NAME = "youtube"
API_VERSION = "v3"


def get_authenticated_service():
    flow = InstalledAppFlow.from_client_secrets_file(CLIENT_SECRETS_FILE, SCOPES)
    credentials = flow.run_console()
    return build(API_SERVICE_NAME, API_VERSION, credentials=credentials)


def get_youtube_stats(client, id):
    response = (
        client.videos().list(part="snippet,contentDetails,statistics", id=id).execute()
    )
    data = {}

    try:
        print(response)
        statistics = response["items"][0]["statistics"]
        print(statistics)
        likes = int(statistics["likeCount"])
        dislikes = int(statistics["dislikeCount"])
        views = int(statistics["viewCount"])
        data["likes"] = likes
        data["dislikes"] = dislikes
        data["views"] = views
    except:
        traceback.print_exc()
        pass

    return data


def __main():
    # When running locally, disable OAuthlib's HTTPs verification. When
    # running in production *do not* leave this option enabled.
    os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"
    client = get_authenticated_service()

    with codecs.open("contenders.json", "r", encoding="utf8") as f:
        initial_contenders = json.load(f)
        contenders_with_rating = []

        for country, links in initial_contenders.items():
            print("Checking country: {}".format(country))
            youtube_data = {
                "likes": 0,
                "dislikes": 0,
                "views": 0,
            }

            ids = []
            for link in links:
                print("Checking link: {}".format(link))
                if "embed" in link:
                    id = link[link.rindex("/") + 1 : link.index("?")]
                else:
                    id = link[link.rindex("v=") + 2 :]
                print("ID: {}".format(id))
                ids.append(id)

            ids = list(set(ids))
            for id in ids:
                data = get_youtube_stats(client, id)
                for k in youtube_data.keys():
                    youtube_data[k] += data.get(k, 0)

            contender = {
                "country": country,
                "youtube_ids": ", ".join(ids),
                "youtube_links_count": len(ids),
            }
            contender.update(youtube_data)
            contenders_with_rating.append(contender)

        print(contenders_with_rating)
        save_dicts("contenders.csv", contenders_with_rating)


if __name__ == "__main__":
    __main()
