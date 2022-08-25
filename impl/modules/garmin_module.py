import configparser
from queue import LifoQueue
from threading import Thread
import time
import datetime

from garminconnect import (
    Garmin,
    GarminConnectConnectionError,
    GarminConnectTooManyRequestsError,
    GarminConnectAuthenticationError,
)

today = datetime.date.today()
yesterday = today - datetime.timedelta(days=1)
lastweek = today - datetime.timedelta(days=7)


class GarminModule:
    def __init__(self, config):
        self.last_activity = None
        self.sleep_data = None
        self.activity_queue = LifoQueue()
        self.sleep_queue = LifoQueue()

        self.invalid = False
        print("Garmin Module has been initiated")

        ## Initialize Garmin api with your credentials
        try:
            self.thread = Thread(
                target=garminLogin,
                args=(
                    self.activity_queue,
                    self.sleep_queue,
                    config["Garmin"]["email"],
                    config["Garmin"]["password"],
                ),
            )
            self.thread.start()
            print("Garmin Log in successful")
        except Exception as e:
            print("[Garmin Module] error trying to authenticate", e)
            self.invalid = True

    def getLastActivity(self):
        if not self.activity_queue.empty():
            self.last_activity = self.activity_queue.get()
            self.activity_queue.queue.clear()
        print("lastActivity", self.last_activity)
        return (
            self.last_activity["distance"],
            self.last_activity["duration"],
            self.last_activity["averageSpeed"],
            self.last_activity["averageHR"],
            self.last_activity["averageRunningCadenceInStepsPerMinute"],
        )

    def getSleedData(self):
        if not self.sleep_queue.empty():
            self.sleep_data = self.sleep_queue.get()
            self.sleep_queue.queue.clear()
        sleep = self.sleep_data["dailySleepDTO"]
        sleeplevels = self.sleep_data["sleepLevels"]
        return (
            get_attribute(sleep, "unmeasurableSleepSeconds", 0),
            get_attribute(sleep, "deepSleepSeconds", 0),
            get_attribute(sleep, "lightSleepSeconds", 0),
            get_attribute(sleep, "remSleepSeconds", 0),
            get_attribute(sleep, "averageRespirationValue", ""),
            get_attribute(sleep, "awakeSleepSeconds", 0),
            get_attribute(sleep, "sleepStartTimestampGMT", 0),
            get_attribute(sleep, "sleepEndTimestampGMT", 0),
            sleeplevels,
        )


def garminLogin(activity_queue, sleep_queue, email, pw):
    lastTimeCall = 0
    while True:
        currTime = time.time()
        if currTime - lastTimeCall >= 600:
            try:
                api_call = Garmin(email, pw)
                api_call.login()
                activity_queue.put(api_call.get_last_activity())
                sleep_queue.put(api_call.get_sleep_data(today))
                lastTimeCall = currTime
            except Exception as e:
                #             print("[Garmin Module] error trying to authenticate", e)
                pass


def get_attribute(data, attribute, default_value):
    return data.get(attribute) or default_value
