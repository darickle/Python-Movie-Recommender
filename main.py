from watchmode_client import WatchmodeClient

def main():
    client = WatchmodeClient()

    # Example: Search for a title
    search_results = client.search_title("Inception")
    print("Search Results:", search_results)

    # Example: Get details for a specific title
    if search_results and "title_results" in search_results:
        title_id = search_results["title_results"][0]["id"]
        title_details = client.get_title_details(title_id)
        print("Title Details:", title_details)

if __name__ == "__main__":
    main()
