from __future__ import annotations
import dataclasses
import math
import random
import typing

import numpy
import requests
from urllib.request import urlopen
from io import BytesIO
from PIL import Image
import numpy as np
import itertools
import typing

angle_horizontal: typing.TypeAlias = int
angle_vertical: typing.TypeAlias = int
power: typing.TypeAlias = int


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


class Painter:
    def __init__(self, base_url: str, token: str):
        self._token = token
        self._base_url = base_url
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

    def current_colors(self) -> dict:
        url = f"{self._base_url}art/colors/info"
        headers = {"Authorization": f"Bearer {self._token}"}
        payload = {}
        response = requests.post(url, headers=headers, data=payload)
        res = response.json()
        print(res)

    def shoot_params(self, weight: int, x: int, y: int, m: int) -> (angle_horizontal, angle_vertical, power):
        cata_distance_to_point = ((weight // 2 - x), self._distance_to_art + y)
        tan = cata_distance_to_point[0] / cata_distance_to_point[1]
        current_angle_horizontal = (tan * 180 / self._pi)

        current_path = math.sqrt(cata_distance_to_point[0] ** 2 + cata_distance_to_point[1] ** 2)
        v0 = math.sqrt(current_path * self._g)  # sin (2*45) = 1
        current_power = m * v0

        return current_angle_horizontal, 45, current_power

    # def get_distances(self, pixels_art: list[list[Pixel]]) -> dict[int, dict[int, float]]:
    #     uniq_colors = set(list(itertools.chain(*pixels_art)))
    #     result: dict[int, dict[int, float]] = dict()
    #     url = f"{self._base_url}art/stage/next"
    #     headers = {"Authorization": f"Bearer {self._token}"}
    #     payload = {}
    #     response = requests.post(url, headers=headers, data=payload)
    #     storage_colors: list[int] = response.json().get('response')

    @staticmethod
    def pixel_array_from_url(url: str) -> list[list[Pixel]]:
        response = urlopen(url)
        image_data = response.read()
        image = Image.open(BytesIO(image_data))
        image_array = np.array(image)
        return [[Pixel(p[0], p[1], p[2]) for p in row] for row in image_array]


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
    base_url = "http://api.datsart.dats.team/"
    painter = Painter(
        base_url=base_url,
        token="643b227165f03643b227165f07",
    )
    painter.shoot_params(40, 10, 10, 2)
    painter.collect_colors()
    test_url = "http://s.datsart.dats.team/game/image/shared/1.png"
    # test = painter.pixel_array_from_url(test_url)[200][200]
    # print(test)
    # print(test.to_24_bit())
    # print(test.from_24_bit(test.to_24_bit()))
    # test2 = get_uniq_pixels_dict(painter.pixel_array_from_url(test_url))
    # print(test2)
    # print(len(test2))
    # print(Pixel.from_24_bit(16777215))
    p1 = Pixel.from_24_bit(16777215)
    p2 = Pixel.from_24_bit(16_522_178)
    print(f"{ p1 = } {p2 = }")
    print(p1 - p2)
    # catalpulata
    # catalpulata.launch(Pixel(123, 123, 123), x, y)