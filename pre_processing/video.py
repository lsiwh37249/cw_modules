import cv2
import os
from pathlib import Path
from tqdm import tqdm

def extract_frames(
    video_path: str,
    out_dir: str = "frames_2s",
    interval_sec: float = 2.0,
):
    """영상에서 interval_sec 초마다 프레임 저장."""
    video_path = Path(video_path)
    cap = cv2.VideoCapture(str(video_path))

    if not cap.isOpened():
        raise IOError(f"❌  영상 열기 실패: {video_path}")

    fps = cap.get(cv2.CAP_PROP_FPS)          # 초당 프레임 수
    step = int(fps * interval_sec)           # 건너뛸 프레임 수
    total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    frame_idx = 0
    saved_idx = 0

    with tqdm(total=total, desc="Extracting") as pbar:
        while True:
            ret, frame = cap.read()
            if not ret:
                break

            if frame_idx % step == 0:
                fname = out_dir / f"frame_{saved_idx:05d}.jpg"
                cv2.imwrite(str(fname), frame)
                saved_idx += 1

            frame_idx += 1
            pbar.update(1)

    cap.release()
    print(f"🎉  {saved_idx}장 저장 완료 → {out_dir.resolve()}")

if __name__ == "__main__":
    # ▶ 예시 실행: python save_frames.py D_옷소매_붉은_끝동.mp4
    import argparse

    parser = argparse.ArgumentParser(description="2초마다 프레임 추출")
    parser.add_argument("video", help="영상 파일 경로")
    parser.add_argument(
        "-o", "--out", default="frames_2s", help="프레임 저장 폴더"
    )
    parser.add_argument(
        "-t", "--interval", type=float, default=2.0, help="추출 간격(초)"
    )
    args = parser.parse_args()

    extract_frames(args.video, args.out, args.interval)