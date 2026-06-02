#!/usr/bin/env python3
"""
一键运行：依次生成全部 HTML 可视化文件。

用法:
    python run_all.py              # 生成全部 HTML
    python run_all.py --skip-map   # 跳过地图（较慢）
    python run_all.py --ai         # 同时重新运行 AI 学科关联分析
"""

import subprocess, sys, os, time

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from common import SRC_DIR, check_python_deps

SCRIPTS = [
    ("generate_trend_viz.py",       "📈 时间趋势图",       True),
    ("generate_map_viz.py",         "🗺️  地理分布热力图",   True),
    ("generate_bar_viz.py",         "📊 国家排名条形图",    True),
    ("generate_visualization.py",   "🥧 学科合作网络",     True),
    ("generate_institution_viz.py", "🏛️  机构排名",        True),
    ("generate_radar_viz.py",       "🕸️  学科雷达图",      True),
]

AI_SCRIPT = ("discipline_correlation.py", "🤖 AI 学科关联分析", False)


def run_script(script_name, label):
    path = os.path.join(SRC_DIR, script_name)
    if not os.path.exists(path):
        print(f"  ✘ File not found: {path}")
        return False
    start = time.time()
    print(f"\n{'='*60}")
    print(f"  {label}")
    print(f"{'='*60}")
    r = subprocess.run([sys.executable, path], cwd=SRC_DIR)
    elapsed = time.time() - start
    if r.returncode == 0:
        print(f"  ✔ Done ({elapsed:.1f}s)")
        return True
    else:
        print(f"  ✘ Failed (exit {r.returncode})")
        return False


def main():
    skip_map = "--skip-map" in sys.argv
    run_ai = "--ai" in sys.argv

    if "--help" in sys.argv or "-h" in sys.argv:
        print(__doc__)
        return

    print("Checking Python deps...")
    if not check_python_deps("pandas", "openpyxl"):
        sys.exit(1)
    print("  ✔ Ready\n")

    results = {}
    for sname, label, _ in SCRIPTS:
        if skip_map and "map" in sname:
            print(f"\n  ⏭ Skipping: {label} (--skip-map)")
            continue
        results[sname] = run_script(sname, label)

    if run_ai:
        sname, label, _ = AI_SCRIPT
        results[sname] = run_script(sname, label)

    print(f"\n{'='*60}")
    print("  Summary")
    print(f"{'='*60}")
    for s, ok in results.items():
        print(f"  {'✔' if ok else '✘'} {s}")
    ok = sum(results.values())
    print(f"\n  Done: {ok}/{len(results)}")

    if ok == len(results):
        from common import OUTPUT_DIR
        print(f"\n  🎉 All generated! Open index.html to view:")
        print(f"     {os.path.join(OUTPUT_DIR, 'index.html')}")


if __name__ == "__main__":
    main()
