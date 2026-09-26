"""python -m v2k <command> - see README.md."""
from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

from v2k.env import MAX_THREADS, limit_cpu


def _parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="python -m v2k", description="Video2Knowledge training and evaluation")
    sub = p.add_subparsers(dest="cmd", required=True)

    sub.add_parser("apps", help="list CUA-Suite apps on Hugging Face and what is local")

    d = sub.add_parser("download", help="download and unpack apps' recordings")
    d.add_argument("apps", nargs="+", help='app names as `apps` lists them, e.g. NetBeans "IntelliJ IDEA"')

    f = sub.add_parser("frames", help="stage 1: frames -> vectors, cached on disk")
    f.add_argument("--apps", nargs="*", help="default: every app under the root")
    f.add_argument("--root", type=Path,
                   help="a dataset folder laid out as <root>/<app>/<task_id>/ (default: data/VideoCUA)")
    f.add_argument("--no-parity-ocr", action="store_true",
                   help="skip the backend's 640x480 OCR pass and keep only the full-resolution one "
                        "(halves the time; the main150 feature set then needs a re-extract)")
    f.add_argument("--workers", type=int, default=4, help="parallel processes (default 4)")
    f.add_argument("--threads", type=int, default=4, help="threads per process (default 4)")
    f.add_argument("--no-cnn", action="store_true", help="skip the ResNet-18 frame embedding")
    f.add_argument("--no-grid", action="store_true", help="skip the 1-fps grid frames, keyframes only")
    f.add_argument("--limit", type=int, help="stop after this many tasks (for a rehearsal or a timing test)")
    f.add_argument("--grid-ocr", action="store_true", help="also OCR grid frames at 640x480 (slow)")
    f.add_argument("--no-native-ocr", action="store_true",
                   help="skip OCR of keyframes at full resolution (saves about two thirds of the time)")

    t = sub.add_parser("train", help="stage 2+3: cross-validate the 14 models and save the best")
    t.add_argument("--apps", nargs="*", help="default: every cached app")
    t.add_argument("--labels", default="keyword", help="keyword | app | csv:PATH (default keyword)")
    t.add_argument("--features", nargs="+", default=["main150", "native150", "cnn", "native150+cnn"],
                   help="feature sets: presets main150 / native150, or blocks ocr ocr_native ui visual "
                        "interaction cnn joined by + (default: main150 native150 cnn native150+cnn)")
    t.add_argument("--models", nargs="+", default=["all"], help="default: all 14")
    t.add_argument("--folds", type=int, default=5)
    t.add_argument("--min-tasks", type=int, default=2, help="drop classes with fewer tasks (default 2)")
    t.add_argument("--augment", type=int, default=0, help="noise copies per training row (backend uses 5)")
    t.add_argument("--sample-tasks", type=int, default=0,
                   help="cross-validate on about this many recordings instead of every cached one, "
                        "sampled per class so the balance is unchanged (0 = all). Whole recordings are "
                        "sampled, so folds stay task-grouped")
    t.add_argument("--balance", type=float, default=0.0, metavar="CAP",
                   help="oversample rare classes in each training fold until no class has fewer than "
                        "1/CAP of the largest (e.g. 2 = within 2x). Training folds only, models untouched. "
                        "Raises macro-F1 and usually lowers plain accuracy - report both")
    t.add_argument("--level", choices=["segment", "task"], default="segment",
                   help="segment: one row per segment carrying its recording's label, as the backend does. "
                        "task: one row per recording, its segments averaged - the granularity the labels "
                        "actually have (default segment)")
    t.add_argument("--name", default="", help="suffix for the run folder")
    t.add_argument("--save-all", action="store_true", help="save every model, not just the best per feature set")
    t.add_argument("--threads", type=int, default=MAX_THREADS)

    tu = sub.add_parser("tune", help="stage A: grid-search the hyperparameters the backend's classes expose")
    tu.add_argument("--prepare", action="store_true",
                    help="load the cache, freeze the folds and write the grid, then stop")
    tu.add_argument("--shard", metavar="I/N", help="run configurations I, I+N, I+2N ... of a prepared run")
    tu.add_argument("--collect", action="store_true", help="merge the shards into tuning.csv and tuning.md")
    tu.add_argument("--run-dir", type=Path, help="the prepared run folder (needed by --shard and --collect)")
    tu.add_argument("--ids", type=int, nargs="*",
                    help="with --shard: only these grid ids, to re-check a shortlist cheaply")
    tu.add_argument("--apps", nargs="*")
    tu.add_argument("--labels", default="keyword", help="keyword | app | csv:PATH")
    tu.add_argument("--features", default="native150", help="one feature set (default native150)")
    tu.add_argument("--models", nargs="+", default=["lightgbm", "xgboost", "stacking"],
                    help="models that have a grid (default lightgbm xgboost stacking)")
    tu.add_argument("--folds", type=int, default=5)
    tu.add_argument("--min-tasks", type=int, default=2)
    tu.add_argument("--augment", type=int, default=0)
    tu.add_argument("--level", choices=["segment", "task"], default="task")
    tu.add_argument("--balance", type=float, default=0.0, metavar="CAP")
    tu.add_argument("--split", choices=["grouped", "random"], default="grouped",
                    help="grouped: a recording never spans folds, as every reported run uses. "
                         "random: ignore recordings, the leaky split the backend's own code does - "
                         "for the comparison that quantifies the leak, never for a reported score")
    tu.add_argument("--name", default="tuned")
    tu.add_argument("--threads", type=int, default=MAX_THREADS)

    pr = sub.add_parser("predict", help="step B: classify a recording with a saved bundle")
    pr.add_argument("--bundle", type=Path, required=True)
    pr.add_argument("--video", type=Path, required=True)
    pr.add_argument("--actions", type=Path, help="action_log.json for the recording, if there is one")
    pr.add_argument("--threads", type=int, default=MAX_THREADS)

    pa = sub.add_parser("parity", help="check the cache reproduces the backend's live vectors for one task")
    pa.add_argument("--app", required=True)
    pa.add_argument("--task", type=int, required=True)

    so = sub.add_parser("sop", help="step-by-step procedure with timestamps for one cached recording")
    so.add_argument("--app", required=True)
    so.add_argument("--task", type=int, required=True)
    so.add_argument("--out", type=Path, help="write markdown here (default: print)")
    so.add_argument("--bundle", type=Path,
                    help="a trained bundle from runs/*/models/; its per-segment predictions then name "
                         "each section instead of the rule-based label")
    so.add_argument("--no-merge", action="store_true",
                    help="keep one heading per segment; by default a run of segments carrying the same "
                         "activity becomes one step block, since repeated identical headings carry no "
                         "information and make the procedure look longer than it is")

    tx = sub.add_parser("taxonomy", help="propose a label set from the instructions, and write a labels csv")
    tx.add_argument("--root", type=Path, required=True)
    tx.add_argument("--out", type=Path, default=Path("labels"))
    tx.add_argument("--version", default="v2", help="suffix for the written files (never overwrites)")

    sv = sub.add_parser("survey", help="label coverage and extraction cost of a dataset folder, no video decoding")
    sv.add_argument("--root", type=Path, required=True)
    sv.add_argument("--apps-detail", type=int, default=12)
    return p


def main(argv: list[str] | None = None) -> None:
    args = _parser().parse_args(argv)

    if args.cmd == "frames":
        if args.workers * args.threads > MAX_THREADS:
            raise SystemExit(f"--workers x --threads = {args.workers * args.threads} is over the {MAX_THREADS}-thread cap")
        limit_cpu(args.threads)
    else:
        limit_cpu(min(getattr(args, "threads", MAX_THREADS), MAX_THREADS))

    logging.basicConfig(level=logging.WARNING, format="%(message)s", stream=sys.stdout)
    logging.getLogger("v2k").setLevel(logging.INFO)

    if args.cmd == "apps":
        from v2k.download import remote_apps, safe_name
        from v2k.env import frame_cache_dir
        from v2k.tasks import local_apps

        local = set(local_apps())
        cache = frame_cache_dir()
        remote = remote_apps()
        print(f"{'app':<28}{'zip MB':>8}  local  cached tasks")
        for app, size in sorted(remote.items(), key=lambda x: x[1]):
            folder = safe_name(app)
            n_cached = len(list((cache / folder).glob("*.json"))) if (cache / folder).is_dir() else 0
            print(f"{app:<28}{size / 1e6:>8.0f}  {'yes' if folder in local else '-':>5}  {n_cached or '-':>12}")
        print(f"total {sum(remote.values()) / 1e9:.1f} GB in {len(remote)} apps")

    elif args.cmd == "download":
        from v2k.download import download

        download(args.apps)

    elif args.cmd == "frames":
        from v2k.frames import run
        from v2k.tasks import discover

        from v2k.frames import is_cached
        from v2k.tasks import interleave_by_app

        pairs = interleave_by_app(discover(args.apps, args.root))
        if args.limit:
            pairs = [p for p in pairs if not is_cached(p[0], p[1].task_id)][: args.limit]
        run(pairs, args.workers, args.threads, with_cnn=not args.no_cnn,
            grid=not args.no_grid, grid_ocr=args.grid_ocr, native_ocr=not args.no_native_ocr,
            parity_ocr=not args.no_parity_ocr)

    elif args.cmd == "train":
        from v2k.download import safe_name
        from v2k.evaluate import train
        from v2k.models import parse_models

        apps = [safe_name(a) for a in args.apps] if args.apps else None
        train(apps, args.labels, args.features, parse_models(args.models), args.folds,
              args.min_tasks, args.augment, args.name, args.save_all, args.sample_tasks, args.level,
              args.balance)

    elif args.cmd == "tune":
        from v2k.download import safe_name
        from v2k.tune import collect, prepare, run_shard

        if args.collect:
            if not args.run_dir:
                raise SystemExit("--collect needs --run-dir")
            collect(args.run_dir)
        elif args.shard:
            if not args.run_dir:
                raise SystemExit("--shard needs --run-dir")
            i, _, n = args.shard.partition("/")
            if not n.isdigit() or not i.isdigit() or int(i) >= int(n):
                raise SystemExit(f"--shard wants I/N with I < N, got '{args.shard}'")
            run_shard(args.run_dir, int(i), int(n), args.ids or None)
        else:
            apps = [safe_name(a) for a in args.apps] if args.apps else None
            prepare(apps, args.labels, args.features, args.models, args.folds, args.min_tasks,
                    args.augment, args.level, args.balance, args.name, 42, args.split)

    elif args.cmd == "predict":
        import torch

        from v2k.predict import predict

        torch.set_num_threads(min(args.threads, MAX_THREADS))
        rows = predict(args.bundle, args.video, args.actions)
        print(f"\n{'segment':>7}  {'start':>6}  {'end':>6}  {'label':<22} confidence")
        for r in rows:
            print(f"{r['segment']:>7}  {r['start']:>6}  {r['end']:>6}  {r['label']:<22} {r['confidence']}")

    elif args.cmd == "sop":
        from v2k.download import safe_name
        from v2k.sop import build, predicted_activities, to_markdown

        app = safe_name(args.app)
        preds, confs = predicted_activities(args.bundle, app, args.task) if args.bundle else (None, None)
        meta, sections = build(app, args.task, preds, confs, merge=not args.no_merge)
        text = to_markdown(meta, sections)
        if args.out:
            if args.out.exists():
                raise SystemExit(f"{args.out} exists; pick another name so earlier ones are kept")
            args.out.write_text(text, encoding="utf-8")
            print(f"wrote {args.out}")
        else:
            print(text)

    elif args.cmd == "taxonomy":
        from v2k.taxonomy import report

        args.out.mkdir(parents=True, exist_ok=True)
        md = args.out / f"taxonomy_{args.version}.md"
        csv_path = args.out / f"labels_{args.version}.csv"
        for path in (md, csv_path):
            if path.exists():
                raise SystemExit(f"{path} exists; pass a new --version so earlier ones are kept")
        out = report(args.root, md, csv_path)
        for name, n in sorted(out["counts"].items(), key=lambda x: -x[1]):
            print(f"  {name:<18}{n:>5}{n / out['tasks']:>7.1%}")
        print(f"wrote {md} and {csv_path}")

    elif args.cmd == "survey":
        from v2k.survey import survey

        survey(args.root, per_app_detail=args.apps_detail)

    elif args.cmd == "parity":
        from v2k.download import safe_name
        from v2k.parity import check

        check(safe_name(args.app), args.task)


if __name__ == "__main__":
    main()
