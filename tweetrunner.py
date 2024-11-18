# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function
import tweepy
import time
import sys
import random

no_of_seasons = 9
no_of_episodes=6


# Define the root directory for the script
root = "/home/MattDaniells1/peep_show_bot/scripts/"

class Extract:
    def __init__(self, filepath: str):
        """
        Initialize the Extract class with a file path, call listify to create an episode transcript.

        Args:
            filepath (str): The path to the file to be extracted.
        """
        self.filepath = filepath
        self.transcript = self.listify()

    def listify(self):
        """
        Reads the file and returns a list of non-empty lines.

        Returns:
            list[str]: A list containing non-empty lines from the file.
        """
        lines = []
        try:
            with open(self.filepath, 'r') as file:
                for line in file:
                    stripped_line = line.rstrip("\n")  # Remove newline character
                    if stripped_line:  # Ignore empty lines
                        lines.append(stripped_line)  # Add non-empty lines
        except (OSError, IOError) as e:
            print(f"Error: {e}")
            print("The file you're trying to open doesn't exist.")
        print("Transcript created from file.")
        return lines

class Run:
    def __init__(self, tw, season_no: int, episode_no: int, cust_start: int):
        """
        Initialize the Run class to manage tweeting.

        Args:
            tw: The Tweepy API object.
            season_no (int): The season number.
            episode_no (int): The episode number.
            cust_start (int): The starting line number for custom starting point.
        """
        self.season_no = season_no
        self.episode_no = episode_no
        self.tw = tw
        self.filepath = self.get_filepath()
        self.transcript = Extract(self.filepath + "/" + str(self.episode_no) + ".txt").transcript
        self.cust_start = cust_start
        self.handle()

    def get_filepath(self) -> str:
        """Constructs the file path based on season and episode numbers."""
        return f"{root}{self.season_no}/{self.episode_no}"

    def insert_zero_width_space(self, original_string: str):
        """Insert a zero width space character randomly in the line to prevent duplicate tweets being blocked."""
        if not original_string:
            return original_string  # Return the original string if it's empty

        # Generate a random index to insert the zero-width space
        random_index = random.randint(0, (len(original_string)-1))

        # Insert the zero-width space at the random index
        modified_string = original_string[:random_index] + '\u200B' + original_string[random_index:]

        return modified_string

    def handle(self):
        """Handles the tweeting process line by line from the transcript."""
        for i, line in enumerate(self.transcript):
            # Update current position in a file
            with open("/home/MattDaniells1/peep_show_bot/cur.txt", "w") as f:
                f.write(f"{self.season_no} {self.episode_no} {i}")

            if i < self.cust_start:
                continue  # Skip to the next line if before custom start

            print("\n")
            print(f"{line} @ {time.ctime()}\n")

            # Check if the line contains an image reference
            words = line.split()
            if words[0] == "img":
                img_no = str(words[1])
                self.tweet_with_image(img_no, line)
            else:
                self.tweet(line)

            time.sleep(60 * 60)  # Wait for an hour before the next tweet
            print(i)

    def handle_rate_limit(self, exception):
        """
        Handle rate limits dynamically using the reset time from the exception.

        Args:
            exception (tweepy.TooManyRequests): The exception raised due to rate limiting.
        """
        try:
            # Extract the rate limit reset time from the response headers
            reset_time = int(exception.response.headers.get("x-rate-limit-reset", 0))
            print(str(reset_time))
            current_time = int(time.time())

            if reset_time > current_time:
                wait_time = reset_time - current_time
                print(f"Rate limit reached. Waiting for {wait_time} seconds until reset.")
                time.sleep(wait_time + 5)  # Add a buffer of 5 seconds
            else:
                # If no reset time is available, use a default wait time
                print("Rate limit reached. Waiting for 15 minutes...")
                time.sleep(15 * 60)
        except Exception as e:
            print(f"Failed to handle rate limit gracefully: {e}")
            print("Using default wait time of 15 minutes...")
            time.sleep(15 * 60)

    def tweet(self, line: str):
        """Posts a tweet with the given line of text."""
        while True:
            try:
                line = self.insert_zero_width_space(line)
                return self.tw.api.create_tweet(text=line)
            except tweepy.Forbidden:
                print("Duplicate tweet!")
                return None
            except tweepy.TooManyRequests as e:
                print(f"Rate limit error for tweet upload: {e}")
                self.handle_rate_limit(e)
            except Exception as e:
                print(f"An error occurred: {e}")
                break

    def tweet_with_image(self, img_no: str, line: str):
        """
        Post a tweet with an image.

        Args:
            img_no (str): The image number used to construct the image path.
            line (str): The text of the tweet, with the first two words removed.

        Returns:
            tweepy.Status: The status object of the created tweet.
        """
        img_path = f"{self.filepath}/img/{img_no}.jpg"
        stripped_line = ' '.join(line.split()[2:])  # Remove the first two words
        stripped_line = self.insert_zero_width_space(stripped_line)
        print("Tweet Text:", stripped_line)
        print("Image Path:", img_path)

        try:
            media = self.tw.auth.media_upload(img_path)  # Upload the image
            media_ids = [media.media_id]  # Get media ID
            return self.tw.api.create_tweet(text=stripped_line, media_ids=media_ids)
        except tweepy.TooManyRequests as e:
            print(f"Rate limit error for media upload: {e}")
            self.handle_rate_limit(e)
        except tweepy.Forbidden:
            print("Duplicate!")
        except FileNotFoundError:
            print(f"Error: The image file {img_path} does not exist.")
        except tweepy.errors.TweepyException as e:
            print(f"Failed to post tweet: {e}")
        except Exception as e:
            print(f"An unexpected error occurred: {e}")

def run_tweets(tw, season_startpoint, episode_startpoint, line_startpoint):
    seasons = [6,6,6,6,6,6,6,6,6]

    for season in range(season_startpoint, (len(seasons)+1)):
            no_of_episodes = seasons[(season-1)]
            for episode in range(episode_startpoint, (no_of_episodes+1)):
                print(f"{season} : {episode}")
                Run(tw, season, episode, line_startpoint)
                line_startpoint = 0  # Reset custom start
                time.sleep(60 * 60)
            episode_startpoint = 1
    season_startpoint = 1

def main(tw):
    """Main function to handle command line arguments and start the tweeting process."""
    startpoints = sys.argv
    # Command line argument to continue from the previous line specified in cur.txt
    if startpoints[1] == "continue":
        # Read current position from file
        with open('/home/MattDaniells1/peep_show_bot/cur.txt', 'r') as f:
            position_string = f.readline()

        continued_startpoint = position_string.split()
        season_startpoint = int(continued_startpoint[0])
        episode_startpoint = int(continued_startpoint[1])
        line_startpoint = int(continued_startpoint[2]) + 1  # Increment custom start

        run_tweets(tw, season_startpoint, episode_startpoint, line_startpoint)
    else:
    # Command line argument to start from a specified point. I.e calling python control.py 1 2 3 Would start from the 3rd line of the 2nd episode of the first season
        season_startpoint = int(startpoints[1])
        episode_startpoint = int(startpoints[2])
        line_startpoint = int(startpoints[3])

        run_tweets(tw, season_startpoint, episode_startpoint, line_startpoint)

if __name__ == "__main__":
    main(tw)