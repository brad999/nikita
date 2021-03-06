"""
Nikita module

Name:           nikita.py

Description:    responds to questions about self (who/what are you,
                what can you do, tell me about yourself, etc)
                by recognizing the words "you" and "yourself"

Dependencies:   none

Author:         Brad Ahlers (github - brad999)
"""

import re
import datetime

WORDS = ["WHO", "WHAT", "ARE", "YOU"]
PRIORITY = 1


def getLastSpeech(db):
    cur = db.cursor()
    SQL = "SELECT speech_text \
           FROM transcript \
           ORDER BY create_timestamp desc LIMIT 1;"
    cur.execute(SQL)

    LastSpeech = cur.fetchall()
    return LastSpeech


def handle(text, mic, profile):
    """
        Responds to user-input, typically speech text.

        Arguments:
        text -- user-input, typically transcribed speech
        mic -- used to interact with the user (for both input and output)
        profile -- contains information related to the user
    """
    # respond to questions about father or parents
    if 'father' in text.lower() or 'parent' in text.lower() \
       or 'dad' in text.lower():
        mic.say('I', "My father and creator is Brad Ahlers. The greatest " +
                "human being to ever live. My mother, by marriage is " +
                "the beautiful Lauren Ahlers.")
    # respond to questions about who/what Nikita is
    elif 'who' in text.lower() or 'what are' in text.lower() \
         or 'yourself' in text.lower():
        mic.say('I', "My name is Nikita. I am a personalized assistance " +
                "developed to provide simple and complete control over " +
                " your home and daily life.")
    # respond to questions about age
    elif 'old' in text.lower() or 'age' in text.lower():
        birthday = datetime.datetime(2015, 04, 06)
        today = datetime.datetime.now()
        age = (today-birthday).days
        age = (age / 365)
        if age > 0:
            mic.say('I', "I am " + str(age) + "years old.")
        else:
            mic.say('I', "I am less than a year old. I was born " +
                    "on April 6th, twenty fifteen.")
    # respond to questions about birthday
    elif 'birth' in text.lower() or 'born' in text.lower():
        mic.say('I', "I was born on April 6th, twenty fifteen.")
    # respond to questions about last actions
    elif 'last' in text.lower() or 'did you' in text.lower():
        mic.say('A', "The last thing I said was, " +
                getLastSpeech(mic.db)[0][0])


def isValid(text):
    """
        Returns True if the input is related to self (Nikita).

        Arguments:
        text -- user-input, typically transcribed speech
    """
    return bool(re.search(r'\b(you|your|yourself)\b', text, re.IGNORECASE))
