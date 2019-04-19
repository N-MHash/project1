import requests

class GoodreadsAPI:

    def review_data_isbn(isbn):
        res = requests.get("https://www.goodreads.com/book/review_counts.json", params={"key": "HUinjUdkKCnQ9QDVlgazgw", "isbns": isbn})

        data = res.json()

        parsed_data = {"rating_count": data["books"][0]["work_ratings_count"],
                            "avg_rating": data["books"][0]["average_rating"]}

        return parsed_data
