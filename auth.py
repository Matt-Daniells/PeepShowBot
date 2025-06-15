import os
import tweepy
import logging

# Configure logging for the module
# Logs will display the time, log level, and message
logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')

# Helper function to enforce required environment variables
# Raises a RuntimeError if the variable is missing

def get_required_env(var_name):
    """
    Retrieves an environment variable or raises a RuntimeError if not found.

    Args:
        var_name (str): The name of the environment variable to fetch.

    Returns:
        str: The value of the environment variable.

    Raises:
        RuntimeError: If the environment variable is not set.
    """
    value = os.environ.get(var_name)
    if not value:
        raise RuntimeError(f"Missing required environment variable: {var_name}")
    return value

class TweepyInitialisation:
    """
    Handles Tweepy client and API initialization using credentials stored in environment variables.
    Provides access to both OAuth1.1 (API) and OAuth2 (Client) for interacting with Twitter.

    Attributes:
        auth (tweepy.API): Tweepy API object for v1.1 endpoints.
        api (tweepy.Client): Tweepy Client object for v2 endpoints.
    """

    def __init__(self):
        """
        Initializes both OAuth1.1 and OAuth2 API clients.
        """
        self.auth = self.authorise()
        self.api = self.connect_api()
        logging.info("TweepyInitialisation complete.")

    def authorise(self):
        """
        Authorizes the application using OAuth1.1 credentials.

        Returns:
            tweepy.API: Authenticated API object for v1.1 endpoints.

        Raises:
            Exception: If authentication fails.
        """
        try:
            api_key = get_required_env("API_KEY")
            api_key_secret = get_required_env("API_KEY_SECRET")
            access_token = get_required_env("ACCESS_TOKEN")
            access_token_secret = get_required_env("ACCESS_TOKEN_SECRET")

            # Create OAuth1 handler and authenticate
            auth = tweepy.OAuth1UserHandler(api_key, api_key_secret, access_token, access_token_secret)
            logging.info("OAuth1 authentication created.")
            return tweepy.API(auth)
        except Exception as e:
            logging.error(f"Failed to authorize: {e}")
            raise

    def connect_api(self):
        """
        Connects to the Twitter API using Tweepy's v2 Client.
        Uses both OAuth2 bearer token and OAuth1 keys for full access.

        Returns:
            tweepy.Client: Authenticated Client object for v2 endpoints.

        Raises:
            Exception: If client connection fails.
        """
        try:
            api = tweepy.Client(
                bearer_token=os.environ.get("BEARER_TOKEN"),
                consumer_key=os.environ.get("API_KEY"),
                consumer_secret=os.environ.get("API_KEY_SECRET"),
                access_token=os.environ.get("ACCESS_TOKEN"),
                access_token_secret=os.environ.get("ACCESS_TOKEN_SECRET")
            )
            logging.info("Tweepy Client API connected.")
            return api
        except Exception as e:
            logging.error(f"Failed to connect to Tweepy Client API: {e}")
            raise

# --- Entry point for standalone execution ---
if __name__ == "__main__":
    import tweetrunner

    # Initialize Twitter credentials and pass the connection object to the main runner
    tw = TweepyInitialisation()
    tweetrunner.main(tw)