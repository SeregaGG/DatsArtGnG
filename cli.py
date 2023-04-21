from __future__ import annotations
import dataclasses
import requests


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


class Painter:
    def __init__(self, base_url: str, token: str):
        self._token = token
        self._base_url = base_url

    def get_levels(self) -> dict:
        url = f"{self._base_url}art/stage/next"
        headers = {"Authorization": f"Bearer {self._token}"}
        payload = {}
        response = requests.post(url, headers=headers, data=payload)
        return response.json()


if __name__ == "__main__":
    # base_url = "http://api.datsart.dats.team/"
    # painter = Painter(
    #     base_url=base_url,
    #     token="643b227165f03643b227165f07",
    # )
    # levels = painter.get_levels()
    # pprint.pprint(levels)
    p1 = Pixel(123, 23, 55)
    p2 = Pixel(44, 1, 100)
    p3 = p1 * 2 + p2 * 3
    print(p3)
