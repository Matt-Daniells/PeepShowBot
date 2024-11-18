import tweepy
import tweetrunner
import os


class TweepyInitialisation:
    """
    Class to initialize and authenticate with the Twitter API using Tweepy.
    """
    _instance = None
    # Singleton to avoid rate limit issues
    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super().__new__(cls, *args, **kwargs)
            cls._instance.auth = cls._instance.authorise()
            cls._instance.api = cls._instance.connect_api()
        return cls._instance

    def __init__(self):
        # Initialize authorization and API connection
        self.auth = self.authorise()  # Authorization handler
        self.api = self.connect_api()  # API client connection
        print("Authorization created: " + str(self.auth) + "\n")
        print("API client created: " + str(self.api) + "\n")

    def authorise(self):
        """
        Authorize the application to access Twitter's API.

        Uses OAuth1UserHandler for authorization by retrieving credentials from
        environment variables. Returns an API handler on success or None on failure.
        """
        try:
            # Using OAuth1 for user authentication
            auth = tweepy.OAuth1UserHandler(
                consumer_key=os.environ.get("CONSUMER_KEY"),
                consumer_secret=os.environ.get("CONSUMER_SECRET"),
                access_token=os.environ.get("ACCESS_TOKEN"),
                access_token_secret=os.environ.get("ACCESS_SECRET")
            )

        except Exception as error:
            # Error handling if authorization fails
            print("Failed to authorise.")
            print("Error: " + str(error))
            return None
        else:
            # Return the authenticated API handler
            return tweepy.API(auth)

    def connect_api(self):
        """
        Connect to the Twitter API using the tweepy Client.

        Initializes a Client with both OAuth1 and OAuth2 details retrieved from
        environment variables.
        """
        try:
            # Tweepy Client initialization with OAuth1 and OAuth2 tokens
            api = tweepy.Client(
                bearer_token=os.environ.get("BEARER_TOKEN"),
                consumer_key=os.environ.get("CONSUMER_KEY"),
                consumer_secret=os.environ.get("CONSUMER_SECRET"),
                access_token=os.environ.get("ACCESS_TOKEN"),
                access_token_secret=os.environ.get("ACCESS_SECRET")
            )
        except tweepy.errors.TweepyException as error:
            # Error handling if connection fails
            print("Failed to connect to API.")
            print("Error: " + str(error))
            return None
        else:
            # Return the API client if successful
            return api

# Entry point for script execution
if __name__ == "__main__":
    # Initialize Tweepy and retrieve API client
    tw = TweepyInitialisation()
    print("Beginning tweeting...")
    tweetrunner.main(tw)
