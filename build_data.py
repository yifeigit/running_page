#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
从 raw/ 目录下的原始 MCP 响应合并生成前端数据文件 data/runs.js
- raw/summary_*.json : 各时间段跑步摘要（由子代理逐字落盘）
- raw/segments/<activityId>.json : 每次跑步的每公里分段
输出: data/runs.js  (window.RUNS / window.RUN_META)
该脚本在自动刷新时也会被重新执行，因此必须可由 agent 独立运行。
"""
import json
import glob
import os
import datetime

HERE = os.path.dirname(os.path.abspath(__file__))
RAW = os.path.join(HERE, "raw")
OUT = os.path.join(HERE, "data")


def load_summaries():
    runs = {}
    for f in sorted(glob.glob(os.path.join(RAW, "summary_*.json"))):
        with open(f, encoding="utf-8") as fh:
            d = json.load(fh)
        for s in d.get("summaries", []):
            runs[s["activityId"]] = s
    return runs


def load_segments(aid):
    p = os.path.join(RAW, "segments", aid + ".json")
    if not os.path.exists(p):
        return []
    with open(p, encoding="utf-8") as fh:
        d = json.load(fh)
    segs = []
    for sg in d.get("segments", []):
        if sg.get("segmentCategory") != "DISTANCE":
            continue
        segs.append({
            "km": sg.get("segmentIndex"),
            "pace": sg.get("avgPace"),
            "hr": sg.get("avgHeartRate"),
            "cad": sg.get("avgCadence"),
            "egain": sg.get("elevationGain"),
            "dist": sg.get("distanceInMeters"),
        })
    segs.sort(key=lambda x: (x["km"] is None, x["km"]))
    return segs


def to_iso(ts):
    try:
        return datetime.datetime.strptime(ts, "%Y%m%d%H%M%S").strftime("%Y-%m-%dT%H:%M:%S")
    except Exception:
        return ts


def main():
    runs_raw = load_summaries()
    out = []
    for aid, s in runs_raw.items():
        # 跳过明显异常的记录（如距离为 0 或严重缺失）
        dist = s.get("distanceInMeters") or 0
        if dist <= 0:
            continue
        rec = {
            "id": aid,
            "date": to_iso(s.get("startTimeInSeconds")),
            "dist": round(dist / 1000.0, 3),
            "dur": s.get("durationInSeconds"),
            "pace": s.get("averagePace"),
            "ahr": s.get("averageHeartRate"),
            "mhr": s.get("maxHeartRate"),
            "cad": s.get("averageRunCadence"),
            "egain": s.get("totalElevationGain"),
            "kcal": s.get("activeKilocalories"),
            "stride": s.get("averageStrideLength"),
            "power": s.get("averagePower"),
            "lat": s.get("startLatitude"),
            "lng": s.get("startLongitude"),
            "segs": load_segments(aid),
        }
        out.append(rec)
    out.sort(key=lambda r: r["date"])

    total_km = round(sum(r["dist"] for r in out), 2)
    meta = {
        "count": len(out),
        "total_km": total_km,
        "generated": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
        "source": "yayarun (COROS)",
        "has_gps": False,
    }
    os.makedirs(OUT, exist_ok=True)
    with open(os.path.join(OUT, "runs.js"), "w", encoding="utf-8") as fh:
        fh.write("window.RUNS = " + json.dumps(out, ensure_ascii=False) + ";\n")
        fh.write("window.RUN_META = " + json.dumps(meta, ensure_ascii=False) + ";\n")
    print("OK wrote %d runs, total %.2f km -> %s" % (len(out), total_km, os.path.join(OUT, "runs.js")))


if __name__ == "__main__":
    main()
