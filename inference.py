import argparse
import os
from datetime import datetime

import cv2
from ultralytics import YOLO


def parse_args():
    parser = argparse.ArgumentParser(description="PPE detection with YOLOv8")
    parser.add_argument(
        "--source",
        default="0",
        help="Input source. Use 0/1/... for webcam index, or provide image/video file path.",
    )
    parser.add_argument(
        "--model",
        default="models/best.pt",
        help="Path to trained YOLO model weights.",
    )
    parser.add_argument(
        "--conf",
        type=float,
        default=0.5,
        help="Confidence threshold.",
    )
    parser.add_argument(
        "--imgsz",
        type=int,
        default=640,
        help="Inference image size.",
    )
    parser.add_argument(
        "--save",
        action="store_true",
        help="Save annotated output. For webcam/video, saves an mp4 in output/live.",
    )
    return parser.parse_args()


def as_source(value):
    # Allow webcam index as string (default "0") for easy CLI usage.
    return int(value) if value.isdigit() else value


def draw_boxes(frame, result):
    for box in result.boxes:
        x1, y1, x2, y2 = map(int, box.xyxy[0].tolist())
        class_id = int(box.cls[0])
        confidence = float(box.conf[0])
        class_name = result.names[class_id]
        label = f"{class_name} {confidence:.2f}"

        cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
        cv2.putText(
            frame,
            label,
            (x1, max(25, y1 - 10)),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            (255, 255, 255),
            2,
            cv2.LINE_AA,
        )
    return frame


def run_image(model, image_path, conf, imgsz, save):
    image = cv2.imread(image_path)
    if image is None:
        raise RuntimeError(f"Failed to load image at: {image_path}")

    result = model(image, conf=conf, imgsz=imgsz, verbose=False)[0]
    annotated = draw_boxes(image.copy(), result)

    print(f"Detected objects: {len(result.boxes)}")
    for box in result.boxes:
        class_id = int(box.cls[0])
        confidence = float(box.conf[0])
        class_name = result.names[class_id]
        print(f"- {class_name}: {confidence:.2f}")

    if save:
        os.makedirs("output", exist_ok=True)
        out_path = os.path.join("output", "image_output.jpg")
        cv2.imwrite(out_path, annotated)
        print(f"Saved output image to: {out_path}")

    cv2.imshow("PPE Detection", annotated)
    cv2.waitKey(0)
    cv2.destroyAllWindows()


def run_stream(model, source, conf, imgsz, save):
    cap = cv2.VideoCapture(source)
    if not cap.isOpened():
        raise RuntimeError("Cannot open source. Check webcam connection or file path.")

    writer = None
    out_path = None

    if save:
        os.makedirs(os.path.join("output", "live"), exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        out_path = os.path.join("output", "live", f"ppe_live_{timestamp}.mp4")

        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)) or 640
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)) or 480
        fps = cap.get(cv2.CAP_PROP_FPS)
        if fps <= 0:
            fps = 20.0

        fourcc = cv2.VideoWriter_fourcc(*"mp4v")
        writer = cv2.VideoWriter(out_path, fourcc, fps, (width, height))

    print("Starting live PPE detection. Press q to quit.")

    try:
        while True:
            ok, frame = cap.read()
            if not ok:
                break

            result = model(frame, conf=conf, imgsz=imgsz, verbose=False)[0]
            annotated = draw_boxes(frame, result)

            cv2.imshow("PPE Detection", annotated)

            if writer is not None:
                writer.write(annotated)

            if cv2.waitKey(1) & 0xFF == ord("q"):
                break
    finally:
        cap.release()
        if writer is not None:
            writer.release()
            print(f"Saved output video to: {out_path}")
        cv2.destroyAllWindows()


def main():
    args = parse_args()
    source = as_source(args.source)

    model = YOLO(args.model)

    if isinstance(source, str):
        lower = source.lower()
        is_image = lower.endswith((".jpg", ".jpeg", ".png", ".bmp", ".webp", ".jfif"))
        if is_image:
            run_image(model, source, args.conf, args.imgsz, args.save)
            return

    run_stream(model, source, args.conf, args.imgsz, args.save)


if __name__ == "__main__":
    main()