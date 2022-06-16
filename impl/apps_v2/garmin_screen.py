import datetime
import time
from PIL import Image, ImageFont, ImageDraw
from InputStatus import InputStatusEnum
from ast import literal_eval
import math


medium_blue = (0, 77, 179)
light_blue = (50, 145, 168)
white = (230, 255, 255)


class GarminScreen:
    def __init__(self, config, modules, default_actions):
        self.modules = modules
        self.default_actions = default_actions

        self.font = ImageFont.truetype("fonts/tiny.otf", 5)

        self.canvas_width = config.getint("System", "canvas_width", fallback=64)
        self.canvas_height = config.getint("System", "canvas_height", fallback=32)

        self.text_color = literal_eval(
            config.get("Garmin Screen", "text_color", fallback="(255,255,255)")
        )
        self.control_mode = False

        self.bgs = {"road": Image.open("apps_v2/res/garmin/road.png").convert("RGB")}

        self.theme_list = [self.lastActivity, self.healthStats]

        self.currentIdx = 0
        self.selectMode = False

        self.queued_frames = []

    def generate(self, isHorizontal, inputStatus):
        if inputStatus is InputStatusEnum.LONG_PRESS:
            self.control_mode = not self.control_mode

        if inputStatus == InputStatusEnum.LONG_PRESS:
            self.selectMode = not self.selectMode

        if self.selectMode:
            if inputStatus is InputStatusEnum.ENCODER_INCREASE:
                self.currentIdx += 1
                self.queued_frames = []
            elif inputStatus is InputStatusEnum.ENCODER_DECREASE:
                self.currentIdx -= 1
                self.queued_frames = []

        if not self.control_mode:
            if inputStatus is InputStatusEnum.SINGLE_PRESS:
                self.default_actions["toggle_display"]()
                self.title_animation_cnt = 0
                self.artist_animation_cnt = 0
            elif inputStatus is InputStatusEnum.ENCODER_INCREASE:
                self.default_actions["switch_next_app"]()
            elif inputStatus is InputStatusEnum.ENCODER_DECREASE:
                self.default_actions["switch_prev_app"]()

        frame = self.theme_list[self.currentIdx % len(self.theme_list)]()

        if self.selectMode:
            draw = ImageDraw.Draw(frame)
            draw.rectangle(
                (0, 0, self.canvas_width - 1, self.canvas_height - 1), outline=white
            )

        return frame

    def lastActivity(self):

        garmin_module = self.modules["garmin"]

        frame = Image.new("RGB", (self.canvas_width, self.canvas_height), (0, 0, 0))
        # frame = self.bgs['road'].copy()
        frame.paste(self.bgs["road"], (0, 0))
        draw = ImageDraw.Draw(frame)
        garmin_module = self.modules["garmin"]

        response = garmin_module.getLastActivity()
        if response is not None:
            (distance, duration, speed, hr, cadence) = response
            draw.text((0, 2), convertToMiles(distance), white, font=self.font)
            draw.text((49, 2), "MILES", medium_blue, font=self.font)

            draw.text((0, 8), str(int(hr)), white, font=self.font)
            draw.text((57, 8), "HR", medium_blue, font=self.font)

            draw.text((0, 14), convertDuration(duration), white, font=self.font)
            draw.text((53, 14), "DUR", medium_blue, font=self.font)

            draw.text((0, 20), convertPace(speed), white, font=self.font)
            draw.text((17, 20), "/mile", light_blue, font=self.font)
            draw.text((49, 20), "PACE", medium_blue, font=self.font)

            draw.text((0, 26), str(int(cadence)), white, font=self.font)
            draw.text((37, 26), "CADENCE", medium_blue, font=self.font)

        return frame

    def healthStats(self):
        frame = Image.new("RGB", (self.canvas_width, self.canvas_height), (0, 0, 0))
        draw = ImageDraw.Draw(frame)
        draw.text((0, 2), "Test health screen", white, font=self.font)

        garmin_module = self.modules["garmin"]
        response = garmin_module.getSleedData()
        if response is not None:
            (
                unmeasurableSleep,
                deepSleep,
                lightSleep,
                remSleep,
                respiration,
                awakeSleep,
            ) = response
        return frame


def roundValues(num, digits):
    return str(round(num, digits))


def convertToMiles(meters):
    return str(roundValues(meters * 0.000621371192, 2))


def convertDuration(seconds):
    hours = math.floor(seconds / 3600)
    minutes = math.floor((seconds / 60) % 60)
    seconds = seconds % 60
    duration_text = (
        (str(hours + ":") if hours > 0 else "")
        + str(minutes)
        + ":"
        + str(padToTwoDigit(seconds))
    )
    return duration_text


def convertPace(speed):
    p = 60 / (speed / 0.44704)
    minutes_pace = math.floor(p)
    seconds_pace = p - minutes_pace
    return str(minutes_pace) + ":" + str(padToTwoDigit(round(seconds_pace * 60, 0)))


def padToTwoDigit(num):
    num = int(num)
    if num < 10:
        return "0" + str(num)
    else:
        return str(num)
