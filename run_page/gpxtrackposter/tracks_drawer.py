"""Contains the base class TracksDrawer, which other Drawers inherit from."""

# Copyright 2016-2019 Florian Pigorsch & Contributors. All rights reserved.
#
# Use of this source code is governed by a MIT-style
# license that can be found in the LICENSE file.

import argparse

import svgwrite

from .poster import Poster
from .utils import interpolate_color
from .value_range import ValueRange
from .xy import XY


class TracksDrawer:
    """Base class that other drawer classes inherit from."""

    def __init__(self, the_poster: Poster):
        self.poster = the_poster

    def create_args(self, args_parser: argparse.ArgumentParser):
        pass

    def fetch_args(self, args):
        pass

    def draw(self, dr: svgwrite.Drawing, size: XY, offset: XY):
        pass

    def color(
        self, length_range: ValueRange, length: float, is_special: bool = False
    ) -> str:
        assert length_range.is_valid()

        # 特殊区间（special_distance < 距离 < special_distance2）统一返回纯 special 色，不做插值。
        # 原因：图例（poster.__draw_footer）画的就是纯 special 色方块，如果这里在
        # special -> special2 之间按长度插值，实际轨迹会落在中间的橙色段上，与图例对不上。
        # 超过 special_distance2 的轨迹由各 drawer 自行赋 special2（纯色）。
        if is_special:
            return self.poster.colors["special"]

        color1 = self.poster.colors["track"]
        color2 = self.poster.colors["track2"]

        diff = length_range.diameter()
        if diff == 0:
            return color1
        if (
            self.poster.length_range.upper() / 1000
            < self.poster.special_distance["special_distance2"]
        ):
            return color1

        return interpolate_color(color1, color2, (length - length_range.lower()) / diff)
