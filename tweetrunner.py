import os
import sys
import time
import random
import tweepy
import logging
from typing import List

# --- Configurable Settings ---
# Helper function to safely read integer environment variables with a fallback

def get_env_int(name: str, default: int) -> int:
    """
    Attempts to fetch an environment variable and convert it to an int.
    Logs a warning and returns the default if not valid.

    Args:
        name (str): The name of the environment variable.
        default (int): The default value to use if the env var is not set or invalid.

    Returns:
        int: The integer value of the environment variable or the default.
    """
    try:
        return int(os.getenv(name, default))
    except ValueError:
        logging.warning(f"Invalid int value for {name}, using default {default}.")
        return default

# Environment-based configurable paths and timing intervals
SCRIPT_ROOT = os.getenv("SCRIPT_ROOT") # Can optionally hard-code a fallback here
CURRENT_POSITION_FILE = os.getenv("CUR_TXT_PATH") # Can optionally hard-code a fallback here
TWEET_INTERVAL = get_env_int("TWEET_INTERVAL_SECS", 90 * 60)  # Default: 90 minutes
RECOVERY_SLEEP = get_env_int("RECOVERY_SLEEP_SECS", 90 * 60)

# Basic logger with timestamps and severity level
logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')

class Extract:
    """
    Extracts and cleans lines from the transcript txt file

    Attributes:
        filepath (str): Path to the transcript file.
        transcript (List[str]): List of non-empty lines extracted from the file.
    """

    def __init__(self, filepath: str):
        self.filepath = filepath
        self.transcript = self.listify()

    def listify(self) -> List[str]:
        """
        Reads a file line by line, filtering out blank lines.

        Returns:
            List[str]: A list of cleaned transcript lines.
        """
        lines = []
        try:
            with open(self.filepath, 'r', encoding='utf-8') as file:
                for line in file:
                    stripped_line = line.rstrip("\n")
                    if stripped_line:
                        lines.append(stripped_line)
        except (OSError, IOError) as e:
            logging.error(f"Error reading file: {e}")

        if not lines:
            logging.warning(f"Transcript file is empty or unreadable: {self.filepath}")
        else:
            logging.info("Transcript created from file.")
        return lines

class Run:
    """
    Manages tweeting for a given season and episode, tracking progress line by line.

    Attributes:
        tw: Tweepy API wrapper with both v1.1 and v2 clients.
        season_no (int): Current season number.
        episode_no (int): Current episode number.
        cust_start (int): Custom line number to start from.
        filepath (str): Path to the season/episode directory.
        transcript (List[str]): List of lines to tweet.
    """

    def __init__(self, tw, season_no: int, episode_no: int, cust_start: int):
        self.season_no = season_no
        self.episode_no = episode_no
        self.tw = tw
        self.filepath = self.get_filepath()
        self.transcript = Extract(self.filepath + "/" + str(self.episode_no) + ".txt").transcript
        self.cust_start = cust_start

    def get_filepath(self) -> str:
        """
        Builds the path to the folder containing the episode's transcript and images.

        Returns:
            str: Full path to the episode folder.
        """
        return f"{SCRIPT_ROOT}{self.season_no}/{self.episode_no}"

    def insert_zero_width_space(self, original_string: str):
        """
        Randomly inserts a zero-width space into the string to bypass duplicate tweet detection.

        Args:
            original_string (str): The text to modify.

        Returns:
            str: Modified string with an invisible character.
        """
        if not original_string:
            return original_string
        random_index = random.randint(0, (len(original_string)-1))
        return original_string[:random_index] + '\u200B' + original_string[random_index:]

    def extract_image_line_text(self, line: str) -> str:
        """
        Extracts the text portion of a line that begins with an image command.

        Args:
            line (str): A line starting with 'img <number>'

        Returns:
            str: The remaining line text once the image reference has been stripped.
        """
        return ' '.join(line.split()[2:])

    def handle(self):
        """
        Loops through transcript lines and posts them to Twitter, handling image and text-only cases.
        Logs each tweet and resumes position in case of failures or interruptions.
        """
        if not self.transcript:
            return

        for i, line in enumerate(self.transcript):
            try:
                with open(CURRENT_POSITION_FILE, "w") as f:
                    f.write(f"{self.season_no} {self.episode_no} {i}")
            except Exception as e:
                logging.error(f"Failed to write to current position file: {e}")

            if i < self.cust_start:
                continue

            logging.info(f"{line} @ {time.ctime()}")

            try:
                if line.startswith("img"):
                    img_no = line.split()[1]
                    self.tweet_with_image(img_no, line)
                else:
                    self.tweet(line)
            except Exception as e:
                logging.error(f"Failed to send tweet: {e}")
                logging.warning("Waiting before retrying due to failure...")
                time.sleep(RECOVERY_SLEEP)
                continue

            try:
                time.sleep(TWEET_INTERVAL)
            except KeyboardInterrupt:
                logging.warning("Interrupted by user. Saving state and exiting.")
                break
            logging.info(f"Line {i} tweeted.")

    def tweet(self, line: str):
        """
        Sends a text-only tweet using the Twitter API.

        Args:
            line (str): Text to tweet.

        Returns:
            Any: API response object.
        """
        line = self.insert_zero_width_space(line)
        return api_call_with_recovery(self.tw.api.create_tweet, text=line)

    def tweet_with_image(self, img_no: str, line: str):
        """
        Attempts to send a tweet with an image. Falls back to text-only if image upload fails.

        Args:
            img_no (str): Image file identifier.
            line (str): Full line of tweet content.

        Returns:
            Any: API response object.
        """
        img_path = f"{self.filepath}/img/{img_no}.jpg"
        text = self.extract_image_line_text(line)
        text = self.insert_zero_width_space(text)
        logging.info(f"Tweet Text: {text}")
        logging.info(f"Image Path: {img_path}")

        try:
            media = api_call_with_recovery(self.tw.auth.media_upload, img_path)
            return api_call_with_recovery(self.tw.api.create_tweet, text=text, media_ids=[media.media_id])
        except FileNotFoundError:
            logging.warning(f"Image file not found: {img_path}. Tweeting text only.")
            return api_call_with_recovery(self.tw.api.create_tweet, text=text)
        except tweepy.TweepyException as e:
            logging.error(f"Twitter error while uploading image: {e}. Tweeting text only.")
            return api_call_with_recovery(self.tw.api.create_tweet, text=text)

def api_call_with_recovery(api_func, *args, **kwargs):
    """
    Wraps an API call and introduces a wait if an exception occurs.
    Prevents hammering the API and enables safe retry on next line.

    Args:
        api_func (Callable): API function to call.
        *args: Positional arguments to pass to the function.
        **kwargs: Keyword arguments to pass.

    Returns:
        Any: Result of the API call.

    Raises:
        Exception: Re-raises any exception after delay.
    """
    try:
        return api_func(*args, **kwargs)
    except Exception as e:
        logging.error(f"API call failed: {e}. Entering recovery wait period.")
        time.sleep(RECOVERY_SLEEP)
        raise

def run_tweets(tw, season_startpoint, episode_startpoint, line_startpoint):
    """
    Iterates through seasons and episodes, delegating tweet handling to the Run class.
    Automatically resets line and episode counters after each step.

    Args:
        tw: Tweepy authentication and API wrapper.
        season_startpoint (int): Season number to start from.
        episode_startpoint (int): Episode number to start from.
        line_startpoint (int): Line index to start from.
    """
    seasons = [6,6,6,6,6,6,6,6,6]  # Number of episodes per season

    for season in range(season_startpoint, (len(seasons)+1)):
        no_of_episodes = seasons[(season-1)]
        for episode in range(episode_startpoint, (no_of_episodes+1)):
            logging.info(f"Running Season {season}, Episode {episode}")
            runner = Run(tw, season, episode, line_startpoint)
            runner.handle()
            line_startpoint = 0
            try:
                time.sleep(RECOVERY_SLEEP)
            except KeyboardInterrupt:
                logging.warning("Interrupted during inter-episode delay. Exiting.")
                return
        episode_startpoint = 1

def main(tw):
    """
    Entry point for CLI. Can either continue from saved position or start fresh.
    Accepts command-line arguments: <season> <episode> <line> or 'continue'.

    Args:
        tw: Tweepy authentication and API wrapper.
    """
    startpoints = sys.argv
    try:
        if len(startpoints) < 2:
            raise ValueError("Insufficient arguments provided.")

        if startpoints[1] == "continue":
            with open(CURRENT_POSITION_FILE, 'r') as f:
                position_string = f.readline()
            continued_startpoint = position_string.split()
            if len(continued_startpoint) != 3:
                raise ValueError("Invalid format in cur.txt")
            season_startpoint = int(continued_startpoint[0])
            episode_startpoint = int(continued_startpoint[1])
            line_startpoint = int(continued_startpoint[2]) + 1
            run_tweets(tw, season_startpoint, episode_startpoint, line_startpoint)
        else:
            season_startpoint = int(startpoints[1])
            episode_startpoint = int(startpoints[2])
            line_startpoint = int(startpoints[3])
            run_tweets(tw, season_startpoint, episode_startpoint, line_startpoint)
    except Exception as e:
        logging.error(f"Invalid usage: {e}")
        print("Usage: python tweetrunner.py <season> <episode> <line> or 'continue'")

# --- Main script execution ---
if __name__ == "__main__":
    try:
        main(tw)
    except KeyboardInterrupt:
        logging.warning("Script manually interrupted. Exiting.")

