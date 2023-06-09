from __future__ import annotations
import dataclasses
import math
import random
import time

import numpy
import requests
from urllib.request import urlopen
from io import BytesIO
from PIL import Image
import numpy as np
import typing
from dotenv import load_dotenv
import os

AngleHorizontal: typing.TypeAlias = int
AngleVertical: typing.TypeAlias = int
Power: typing.TypeAlias = int

Color: typing.TypeAlias = int


@dataclasses.dataclass
class Pixel:
    r: int
    b: int
    g: int
    amount: int = 1

    def __add__(self, other: Pixel) -> Pixel:
        r = (self.r * self.amount + other.r * other.amount) // (self.amount + other.amount)
        b = (self.b * self.amount + other.b * other.amount) // (self.amount + other.amount)
        g = (self.g * self.amount + other.g * other.amount) // (self.amount + other.amount)
        return Pixel(r=r, b=b, g=g, amount=self.amount + other.amount)

    def __mul__(self, other: int) -> Pixel:
        self.amount *= other
        return self

    def __repr__(self) -> str:
        return f"{self.amount} ({self.r}, {self.g}, {self.b})"

    def __sub__(self, other: Pixel) -> float:
        return numpy.sqrt((self.r - other.r) ** 2 + (self.g - other.g) ** 2 + (self.b - other.b) ** 2)

    @classmethod
    def from_24_bit(cls, value: int) -> Pixel:
        red = (value >> 16) & 0xFF
        green = (value >> 8) & 0xFF
        blue = value & 0xFF
        return cls(r=red, g=green, b=blue)

    def to_24_bit(self) -> int:
        return (self.r << 16) | (self.g << 8) | self.b

    def is_white(self) -> bool:
        if self.r == 255 and self.b == 255 and self.g == 255:
            return True
        return False


class Painter:
    STATUS_SUCCESS = 20

    def __init__(self, base_url: str, token: str):
        self._token = token
        self._base_url = base_url
        self.current_colors = {}
        self._distance_to_art = 300
        self._pi = 3.1415926535898
        self._g = 9.80665

    def get_levels(self) -> dict:
        url = f"{self._base_url}art/stage/next"
        headers = {"Authorization": f"Bearer {self._token}"}
        payload = {}
        response = requests.post(url, headers=headers, data=payload)
        return response.json()

    def collect_colors(self) -> typing.NoReturn:
        while True:
            url = f"{self._base_url}art/factory/generate"
            headers = {"Authorization": f"Bearer {self._token}"}
            payload = {}
            response = requests.post(url, headers=headers, data=payload)
            res = response.json()
            tick = res['info']['tick']
            url = f"{self._base_url}art/factory/pick"
            payload = {"num": random.randint(1, 3), "tick": tick}
            response = requests.post(url, headers=headers, data=payload)
            print("Working")

    def _get_current_colors(self) -> dict[Color, Pixel]:
        url = f"{self._base_url}art/colors/list"
        headers = {"Authorization": f"Bearer {self._token}"}
        payload = {}
        response = requests.post(url, headers=headers, data=payload)
        res = response.json()
        return {int(color): Pixel.from_24_bit(int(color)) * amount for color, amount in res['response'].items()}

    def wait_for_queue(self, current_id: int) -> bool:
        url = f"{self._base_url}art/state/queue"
        headers = {"Authorization": f"Bearer {self._token}"}
        payload = {"id": current_id}
        response = requests.post(url, headers=headers, data=payload)
        res = response.json()
        queue = res.get("response")
        for command_data in queue:
            if command_data.get("id") == current_id:
                return command_data.get("status") == self.STATUS_SUCCESS
        return False

    def seva_shoot_params(self, width: int, x: int, y: int, mass: int) -> (AngleHorizontal, AngleVertical, Power):
        mass_reduce_coef = 0.001
        fixed_angle = 45

        a, b = (width // 2 - x), self._distance_to_art + y
        theta = math.atan(a / b)
        angle = math.degrees(theta)
        current_angle_horizontal = angle

        distance = math.sqrt(a**2 + b**2)
        power = (self._g * distance * mass * mass_reduce_coef) / 2
        return current_angle_horizontal, fixed_angle, power

    @staticmethod
    def pixel_array_from_url(url: str) -> list[list[Pixel]]:
        response = urlopen(url)
        image_data = response.read()
        image = Image.open(BytesIO(image_data))
        image_array = np.array(image)
        return [[Pixel(p[0], p[1], p[2]) for p in row] for row in image_array]

    def _get_best_color(self, pixel: Pixel) -> Color:
        min_distance = float("inf")
        color = None
        for c, p in self.current_colors.items():
            distance = pixel - p
            if distance < min_distance:
                min_distance = distance
                color = c
        return color

    def _fire(self, angle_horizon: float, angle_vertical: float, force: float, colors: dict[Color, int]):
        url = f"{self._base_url}art/ballista/shoot"
        headers = {"Authorization": f"Bearer {self._token}"}
        payload = {
            "angleHorizontal": angle_horizon,
            "angleVertical": angle_vertical,
            "power": force,
        }
        for c, amount in colors.items():
            payload[f'colors[{c}]'] = amount
        while True:
            response = requests.post(url, headers=headers, data=payload)
            res = response.json()
            if res['status'] != 200:
                time.sleep(0.1)
            else:
                break

    def _fire_single_pixel(self, image: list[list[Pixel]], pixel: Pixel, x: int, y: int) -> None:
        color = self._get_best_color(pixel)
        self.current_colors[color].amount -= 1
        angle_horizon, angle_vertical, force = self.seva_shoot_params(
            width=len(image[0]),
            x=x,
            y=y,
            mass=10,
        )
        colors = {color: 1}
        self._fire(
            angle_horizon=angle_horizon,
            angle_vertical=angle_vertical,
            force=force,
            colors=colors,
        )

    def cheap_and_angry(self, url: str, ) -> None:
        image = self.pixel_array_from_url(url)
        self.current_colors = self._get_current_colors()
        for x, row in enumerate(image):
            for y, pixel in enumerate(row):
                if pixel.is_white():
                    continue
                self._fire_single_pixel(pixel=pixel, x=x, y=y, image=image)
                print("Colored!")

    def test_shot(self, url: str) -> None:
        image = self.pixel_array_from_url(url)
        self.current_colors = self._get_current_colors()
        pixel = image[125][100]
        if pixel.is_white():
            raise ValueError()
        self._fire_single_pixel(pixel=pixel, x=10, y=10, image=image)

    def get_current_url(self) -> str:
        url = f"{self._base_url}art/stage/info"
        headers = {"Authorization": f"Bearer {self._token}"}
        payload = {}
        response = requests.post(url, headers=headers, data=payload)
        res = response.json()
        return res['response']['canvas']['url']


def get_uniq_pixels_dict(art: list[list[Pixel]]) -> dict[int, int]:
    pixels_art: dict[int, int] = dict()

    for pixels in art:
        for pixel in pixels:
            if not pixels_art.get(pixel.to_24_bit()) is None:
                pixels_art[pixel.to_24_bit()] += 1
            else:
                pixels_art[pixel.to_24_bit()] = 1

    return pixels_art


if __name__ == "__main__":
    load_dotenv()
    base_url = "http://api.datsart.dats.team/"
    painter = Painter(
        base_url=base_url,
        token=os.getenv("TOKEN"),
    )
    picture_url = "http://s.datsart.dats.team/game/image/shared/2.png"
    painter.test_shot(picture_url)
    # painter.cheap_and_angry(picture_url)
    print(painter.get_current_url())
    # painter.collect_colors()
