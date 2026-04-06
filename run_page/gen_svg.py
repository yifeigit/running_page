import argparse  # 导入用于解析命令行参数的库，让我们可以通过终端输入各种配置
import logging  # 导入日志库，用于记录程序运行时的状态或错误信息
import os  # 导入操作系统接口库，用于处理文件路径和目录
import random  # 导入随机数库，用于随机打乱运动轨迹的顺序
import sys  # 导入系统相关的库，用于处理系统退出等操作

from config import SQL_FILE  # 从 config.py 中导入数据库文件路径
# 导入生成海报的核心库 gpxtrackposter 中的各个绘图组件
from gpxtrackposter import (
    circular_drawer,  # 圆形绘图器
    github_drawer,  # GitHub 风格（热力图）绘图器
    grid_drawer,  # 网格绘图器
    poster,  # 海报核心类
    track_loader,  # 轨迹加载器
    month_of_life_drawer,  # 人生月份绘图器
    year_summary_drawer,  # 年度总结绘图器
)
from gpxtrackposter.exceptions import ParameterError, PosterError  # 导入自定义异常类

# 程序基本信息
__app_name__ = "create_poster"
__app_author__ = "flopp.net"


def main():
    """主函数：处理命令行参数并调用其他模块生成海报。"""

    p = poster.Poster()  # 创建一个海报对象实例
    # 定义可用的绘图器字典，方便根据用户输入选择不同的展示风格
    drawers = {
        "grid": grid_drawer.GridDrawer(p),  # 网格风格
        "circular": circular_drawer.CircularDrawer(p),  # 圆形风格
        "github": github_drawer.GithubDrawer(p),  # GitHub 热力图风格
        "monthoflife": month_of_life_drawer.MonthOfLifeDrawer(p),  # 人生月份风格
        "year_summary": year_summary_drawer.YearSummaryDrawer(p),  # 年度总结风格
    }

    args_parser = argparse.ArgumentParser()  # 创建命令行参数解析器
    # 添加各种命令行参数配置
    args_parser.add_argument(
        "--gpx-dir",
        dest="gpx_dir",
        metavar="DIR",
        type=str,
        default=".",
        help="包含 GPX 文件的目录（默认为当前目录）。",
    )
    args_parser.add_argument(
        "--output",
        metavar="FILE",
        type=str,
        default="poster.svg",
        help='生成的 SVG 图像文件名（默认为 "poster.svg"）。',
    )
    args_parser.add_argument(
        "--language",
        metavar="LANGUAGE",
        type=str,
        default="",
        help="语言设置（默认为英文）。",
    )
    args_parser.add_argument(
        "--year",
        metavar="YEAR",
        type=str,
        default="all",
        help='按年份过滤轨迹；例如 "2023", "2020-2023", "all"（默认为所有年份）。',
    )
    args_parser.add_argument(
        "--title", metavar="TITLE", type=str, help="海报上显示的标题。"
    )
    args_parser.add_argument(
        "--athlete",
        metavar="NAME",
        type=str,
        default="John Doe",
        help='显示的运动员姓名（默认为 "John Doe"）。',
    )
    args_parser.add_argument(
        "--special",
        metavar="FILE",
        action="append",
        default=[],
        help="标记 GPX 目录中的特定轨迹文件为特殊；可多次使用以标记多个文件。",
    )
    types = '", "'.join(drawers.keys())
    args_parser.add_argument(
        "--type",
        metavar="TYPE",
        default="grid",
        choices=drawers.keys(),
        help=f'要创建的海报类型（默认为 "grid"，可选："{types}"）。',
    )
    args_parser.add_argument(
        "--background-color",
        dest="background_color",
        metavar="COLOR",
        type=str,
        default="#222222",
        help='海报背景颜色（默认为 "#222222"）。',
    )
    args_parser.add_argument(
        "--track-color",
        dest="track_color",
        metavar="COLOR",
        type=str,
        default="#4DD2FF",
        help='轨迹颜色（默认为 "#4DD2FF"）。',
    )
    args_parser.add_argument(
        "--track-color2",
        dest="track_color2",
        metavar="COLOR",
        type=str,
        help="轨迹的次要颜色（默认为无）。",
    )
    args_parser.add_argument(
        "--text-color",
        dest="text_color",
        metavar="COLOR",
        type=str,
        default="#FFFFFF",
        help='文字颜色（默认为 "#FFFFFF"）。',
    )
    args_parser.add_argument(
        "--special-color",
        dest="special_color",
        metavar="COLOR",
        default="#FFFF00",
        help='特殊轨迹的颜色（默认为 "#FFFF00"）。',
    )
    args_parser.add_argument(
        "--special-color2",
        dest="special_color2",
        metavar="COLOR",
        help="特殊轨迹的次要颜色（默认为无）。",
    )
    args_parser.add_argument(
        "--units",
        dest="units",
        metavar="UNITS",
        type=str,
        choices=["metric", "imperial"],
        default="metric",
        help='距离单位；"metric"（公制）, "imperial"（英制）（默认为 "metric"）。',
    )
    args_parser.add_argument(
        "--verbose", dest="verbose", action="store_true", help="显示详细日志。"
    )
    args_parser.add_argument("--logfile", dest="logfile", metavar="FILE", type=str)
    args_parser.add_argument(
        "--special-distance",
        dest="special_distance",
        metavar="DISTANCE",
        type=float,
        default=10.0,
        help="特殊距离1（公里），超过此距离将使用 special_color 颜色显示",
    )
    args_parser.add_argument(
        "--special-distance2",
        dest="special_distance2",
        metavar="DISTANCE",
        type=float,
        default=20.0,
        help="特殊距离2（公里），超过此距离将使用 special_color2 颜色显示",
    )
    args_parser.add_argument(
        "--min-distance",
        dest="min_distance",
        metavar="DISTANCE",
        type=float,
        default=1.0,
        help="过滤轨迹的最小距离（公里）",
    )
    args_parser.add_argument(
        "--use-localtime",
        dest="use_localtime",
        action="store_true",
        help="使用当地时间还是 UTC 时间",
    )

    args_parser.add_argument(
        "--random",
        dest="random",
        action="store_true",
        help="随机打乱轨迹的显示顺序",
    )

    args_parser.add_argument(
        "--from-db",
        dest="from_db",
        action="store_true",
        help="从数据库文件加载活动数据",
    )

    args_parser.add_argument(
        "--github-style",
        dest="github_style",
        metavar="GITHUB_STYLE",
        type=str,
        default="align-firstday",
        help='GitHub 风格排版；"align-firstday", "align-monday"（默认为 "align-firstday"）。',
    )

    args_parser.add_argument(
        "--sport-type",
        dest="sport_type",
        metavar="SPORT_TYPE",
        type=str,
        default="all",
        help="运动类型过滤（如 running, cycling 等）",
    )

    args_parser.add_argument(
        "--generate-all-years",
        dest="generate_all_years",
        action="store_true",
        help="为每一年生成单独的 SVG 文件（仅限 github 类型）",
    )

    # 为每个绘图器添加其特有的命令行参数
    for _, drawer in drawers.items():
        drawer.create_args(args_parser)

    args = args_parser.parse_args()  # 解析所有输入的参数

    # 让每个绘图器获取其对应的参数值
    for _, drawer in drawers.items():
        drawer.fetch_args(args)

    log = logging.getLogger("gpxtrackposter")  # 获取日志记录器
    log.setLevel(logging.INFO if args.verbose else logging.ERROR)  # 根据 verbose 参数设置日志级别
    if args.logfile:
        handler = logging.FileHandler(args.logfile)  # 如果指定了日志文件，则添加文件处理器
        log.addHandler(handler)

    loader = track_loader.TrackLoader()  # 创建轨迹加载器
    if args.use_localtime:
        loader.use_local_time = True  # 设置是否使用当地时间
    if not loader.year_range.parse(args.year):
        raise ParameterError(f"错误的年份范围格式: {args.year}。")

    loader.special_file_names = args.special  # 设置特殊的轨迹文件名
    loader.min_length = args.min_distance * 1000  # 将公里转换为米，设置最小过滤长度

    if args.from_db:
        # 如果从数据库加载数据（适用于生成 SVG）
        # 如果类型是 grid，则需要加载经纬度数据（polyline）
        tracks = loader.load_tracks_from_db(SQL_FILE, args.type == "grid")
    else:
        # 否则从指定的 GPX 目录加载文件
        tracks = loader.load_tracks(args.gpx_dir)

    # 如果指定了运动类型，则过滤出对应的轨迹
    if args.sport_type != "all":
        tracks = [track for track in tracks if track.type == args.sport_type]

    if args.random:
        random.shuffle(tracks)  # 如果设置了随机，则打乱轨迹顺序

    if not tracks:
        return  # 如果没有找到任何轨迹，直接退出

    # 判断当前选择的海报类型
    is_circular = args.type == "circular"
    is_mol = args.type == "monthoflife"
    is_year_summary = args.type == "year_summary"
    is_github = args.type == "github"

    # 如果不是特定的几种类型，打印生成进度信息
    if not is_circular and not is_mol and not is_year_summary:
        print(
            f"正在创建类型为 {args.type} 的海报，包含 {len(tracks)} 条轨迹，并保存到文件 {args.output}..."
        )
    p.set_language(args.language)  # 设置语言
    p.athlete = args.athlete  # 设置运动员姓名
    if args.title:
        p.title = args.title  # 设置自定义标题
    else:
        p.title = p.trans("MY TRACKS")  # 使用默认翻译后的标题

    # 设置特殊距离配置
    p.special_distance = {
        "special_distance": args.special_distance,
        "special_distance2": args.special_distance2,
    }

    # 设置颜色配置
    p.colors = {
        "background": args.background_color,
        "track": args.track_color,
        "track2": args.track_color2 or args.track_color,
        "special": args.special_color,
        "special2": args.special_color2 or args.special_color,
        "text": args.text_color,
    }
    p.units = args.units  # 设置单位
    p.set_tracks(tracks)  # 将加载的轨迹放入海报对象
    # 根据类型决定是否显示页眉页脚
    p.drawer_type = "plain" if is_circular else "title"
    if is_mol:
        p.drawer_type = "monthoflife"
    if is_year_summary:
        p.drawer_type = "year_summary"
    if args.type == "github":
        p.height = 55 + p.years.real_year * 43  # GitHub 类型根据年份动态计算高度
    p.github_style = args.github_style  # 设置 GitHub 风格排版

    # 如果是圆形风格，使用一套特定的默认配色（如果没有被用户覆盖）
    if args.type == "circular":
        if args.background_color == "#222222":
            p.colors["background"] = "#1a1a1a"
        if args.track_color == "#4DD2FF":
            p.colors["track"] = "red"
        if args.special_color == "#FFFF00":
            p.colors["special"] = "yellow"
        if args.text_color == "#FFFFFF":
            p.colors["text"] = "#e1ed5e"

    # 特殊处理：循环绘制不同年份的图表
    if is_circular:
        years = p.years.all()[:]
        output_dir = os.path.dirname(args.output) or "assets"
        for y in years:
            p.years.from_year, p.years.to_year = y, y
            p.set_tracks(tracks)  # 重新按年份过滤轨迹
            p.draw(drawers[args.type], os.path.join(output_dir, f"year_{str(y)}.svg"))  # 生成每年的圆形图
    elif is_year_summary and args.summary_year is None:
        # 如果是年度总结类型且未指定具体某一年，则为所有年份生成总结图
        years = p.years.all()[:]
        output_dir = os.path.dirname(args.output) or "assets"
        for y in years:
            drawers[args.type].year = y
            p.draw(
                drawers[args.type],
                os.path.join(output_dir, f"year_summary_{str(y)}.svg"),
            )
    elif is_github and args.year == "all" and args.generate_all_years:
        # 如果是 GitHub 类型且设置了生成所有年份
        years = p.years.all()[:]
        output_dir = os.path.dirname(args.output) or "assets"
        for y in years:
            p.years.from_year, p.years.to_year = y, y
            # 重新计算单年份热力图的高度
            p.height = 55 + p.years.real_year * 43
            # 重新设置该年份的数据
            p.set_tracks(tracks)
            # 设置年份标题，如 "2023 Running"
            year_title = args.title if args.title else f"{y} Running"
            original_title = p.title
            p.title = year_title
            p.draw(
                drawers[args.type],
                os.path.join(output_dir, f"github_{str(y)}.svg"),
            )
            # 恢复原始标题，以免影响下次循环
            p.title = original_title
    else:
        # 否则只生成一张指定的总海报
        p.draw(drawers[args.type], args.output)


if __name__ == "__main__":
    try:
        # 开始执行生成 SVG 的逻辑
        main()
    except PosterError as e:
        # 如果发生海报生成错误，打印错误并以状态码 1 退出
        print(e)
        sys.exit(1)
