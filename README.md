
# PeepScript

## A Twitter Bot for tweeting the script to a tv show line by line, at 90 minute intervals.

PeepScript is a Python-based Twitter bot that sequentially posts lines from a TV show script (or any text transcript), including support for image tweets. Originally designed for Channel 4 program Peep Show, I've rewritten the code to be adaptable if you would like to use the code for your own bot. Written with Tweepy.

----------------------------------------------------------------------------------------------------------

## 📁 Project Structure
<br/><br/>
project/

  - tweetrunner.py
  > Main bot runner script

  - auth.py
  > Tweepy API and client initialization

  - scripts/ `Folder of scripts`
    - 1/ `Season 1`
      - 1 `Episode 1`
        - 1.txt `Transcript`
        - img/ `Image folder`
          - 1.jpg `Image file`

  - cur.txt
  > Saved state: current season, episode, and line

<br/><br/>
_I've included an exemplar folder for scripts in the repository, based on a show with 4 seasons of 5 episodes each. You can add more folders depending on the size of the show._


**In tweetrunner.py, line 245 `seasons = [6,6,6,6,6,6,6,6,6]` is a list that determines the number of episodes per season and number of seasons of the show to loop through. Peep Show has 9 seasons of 6 episodes, which is why this list is the way it is, however you can customise it based on any given show. For example, Breaking Bad would be [7, 13, 13, 13, 16].**

----------------------------------------------------------------------------------------------------------

## ⚙️ Environment Variables

### Set these environment variables in your system, they are required for authentication between X API and Tweepy. You can get these tokens by creating an X developer account.

`API_KEY=*Example consumer_key*`

`API_KEY_SECRET=*Example consumer_key_secret*`

`ACCESS_TOKEN=*Example access_token*`

`ACCESS_TOKEN_SECRET=*Example access_token_secret*`

`BEARER_TOKEN=*Example bearer_token*`
<br/><br/>
### These environment variables are the absolute filepath for your 'scripts' folder and your 'saved state' folder:

`SCRIPT_ROOT=/absolute/path/to/transcripts/`

`CUR_TXT_PATH=/absolute/path/to/cur.txt`
<br/><br/>
### These are optional timing settings:

`TWEET_INTERVAL_SECS=5400`      # Wait between tweets (default: 90 minutes)

`RECOVERY_SLEEP_SECS=5400`      # Wait after failed tweet (default: 90 minutes)
<br/><br/>
_The wait period of 90 minutes is based on the currently allowed number of POST requests in a 24 hour period under X's free API package. You're allowed 17, and the 90 minute wait limits the bot to 16 per day. This can be adjusted if you choose to pay for improved access._

----------------------------------------------------------------------------------------------------------
## 🚀 Startup

You can run the bot from the command line:

`python auth.py 1 1 -1`       # Start from Season 1, Episode 1, Line 0

`python auth.py 2 4 27`      # Start from Season 2, Episode 4, Line 55

`python auth.py continue`    # Resume from saved position in cur.txt, the easiest option.
<br/><br/>
**NOTE: Because the raw text files have spaces between the lines, to start at the correct line if not using 'continue': take the line number in the file, then subtract 1 and halve it. For example, if you want to start at line 201 (in the raw text file) from season 1 episode 1, use `1 1 100`**


_OR you can pay a bit of money to host the code online, this makes it more reliable and frees up your system. I used the Always On Tasks from PythonAnywhere._

----------------------------------------------------------------------------------------------------------

## 📸 Image Tweets

To include images in tweets:

Begin the transcript line with img <number>, e.g.:

`img 1 This is the line of dialogue.`
*Image must exist at SCRIPT_ROOT/<season>/<episode>/img/<number>.jpg*

_If the image is missing, it will fallback to text-only._

----------------------------------------------------------------------------------------------------------

## 🛠️ Requirements

`Python 3.7+`

`Tweepy (pip install tweepy)`

----------------------------------------------------------------------------------------------------------

## 🧪 Tips & Troubleshooting

Ensure environment variables are set correctly before launch.
Check the console logs for tweet success, failures, and detailed error messages.

If rate-limited by Twitter's Free Tier, your bot will be blocked from for accessing the API for 24 hours. The best thing to do when the bot stops working for an extended period of time is to manually stop it and continue after 24 hours. Issues with Twitter's servers may cause rate limit errors and require a 24 hour pause. It's important to make sure your scripts are all set up before starting to avoid problems.

----------------------------------------------------------------------------------------------------------
## 📜 License
MIT License – use, fork, modify freely. Give me a shoutout at some point if you feel like it.
