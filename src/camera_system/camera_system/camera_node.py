import math
import time
from pathlib import Path

import cv2
import mediapipe as mp
import numpy as np
import rclpy
from cv_bridge import CvBridge
from rclpy.node import Node
from geometry_msgs.msg import Vector3Stamped
from sensor_msgs.msg import Image
from std_msgs.msg import Float32


def _estimate_face_geometry(
    center_x,
    center_y,
    frame_width,
    frame_height,
    face_box_width_px,
    focal_length_px,
    known_face_width_m,
):
    if face_box_width_px <= 0:
        raise ValueError('face_box_width_px must be positive')
    distance_m = focal_length_px * known_face_width_m / face_box_width_px
    x_m = (center_x - frame_width / 2.0) * distance_m / focal_length_px
    y_m = (center_y - frame_height / 2.0) * distance_m / focal_length_px
    horizontal_bearing_rad = math.atan2(x_m, distance_m)
    vertical_bearing_rad = math.atan2(-y_m, distance_m)
    return distance_m, horizontal_bearing_rad, vertical_bearing_rad

class CameraNode(Node):
    def __init__(self):
        super().__init__('camera_node')

        self.image_pub = self.create_publisher(Image, 'head_camera/image_raw', 10)
        self.annotated_image_pub = self.create_publisher(
            Image, 'head_camera/image_detections', 10
        )
        self.target_bearing_pub = self.create_publisher(
            Vector3Stamped, 'head_camera/target_bearing', 10
        )
        self.target_distance_pub = self.create_publisher(
            Float32, 'head_camera/target_distance_m', 10
        )

        self.bridge = CvBridge()
        self.focal_length_px = float(
            self.declare_parameter('focal_length_px', 600.0).value
        )
        self.known_face_width_m = float(
            self.declare_parameter('known_face_width_m', 0.16).value
        )
        min_confidence = float(
            self.declare_parameter('min_detection_confidence', 0.5).value
        )
        if self.focal_length_px <= 0 or self.known_face_width_m <= 0:
            raise ValueError('focal_length_px and known_face_width_m must be positive')
        if not 0.0 <= min_confidence <= 1.0:
            raise ValueError('min_detection_confidence must be between 0 and 1')

        model_path = Path(
            str(
                self.declare_parameter(
                    'face_model_path',
                    str(
                        Path.home()
                        / '.ros'
                        / 'models'
                        / 'blaze_face_short_range.tflite'
                    ),
                ).value
            )
        ).expanduser()
        self.face_detector = None
        if model_path.is_file():
            options = mp.tasks.vision.FaceDetectorOptions(
                base_options=mp.tasks.BaseOptions(
                    model_asset_path=str(model_path)
                ),
                running_mode=mp.tasks.vision.RunningMode.VIDEO,
                min_detection_confidence=min_confidence,
            )
            self.face_detector = mp.tasks.vision.FaceDetector.create_from_options(
                options
            )
            self.get_logger().info(f'Loaded face detector model: {model_path}')
        else:
            self.get_logger().error(
                f'Face model not found at {model_path}; face detection is disabled. '
                'Download blaze_face_short_range.tflite from '
                'https://storage.googleapis.com/mediapipe-models/face_detector/'
                'blaze_face_short_range/float16/1/blaze_face_short_range.tflite '
                'or set the face_model_path parameter.'
            )

        self._last_timestamp_ms = 0
        self.camera_port = 0
        self.cap = cv2.VideoCapture(self.camera_port, cv2.CAP_V4L2)
        self.cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*'MJPG'))
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

        if not self.cap.isOpened():
            self.cap.release()
            raise RuntimeError(
                'Cannot open camera. Is it attached to WSL via usbipd?'
            )
        self.get_logger().info(
            'Camera opened successfully. Publishing to /head_camera/image_raw...'
        )
        self.timer = self.create_timer(0.033, self.timer_callback)

    def timer_callback(self):
        if not self.cap.isOpened():
            return

        ret, frame = self.cap.read()
        if not ret:
            self.get_logger().warning('Failed to capture frame from camera.')
            return

        frame = np.ascontiguousarray(frame)
        image_msg = self.bridge.cv2_to_imgmsg(frame, encoding='bgr8')
        image_msg.header.stamp = self.get_clock().now().to_msg()
        image_msg.header.frame_id = 'head_camera_link'
        self.image_pub.publish(image_msg)

        annotated = frame.copy()
        target_bearing = None
        distance_msg = Float32(data=0.0)

        if self.face_detector is not None:
            rgb_frame = np.ascontiguousarray(
                cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            )
            timestamp_ms = max(
                time.monotonic_ns() // 1_000_000,
                self._last_timestamp_ms + 1,
            )
            self._last_timestamp_ms = timestamp_ms
            mp_image = mp.Image(
                image_format=mp.ImageFormat.SRGB,
                data=rgb_frame,
            )
            results = self.face_detector.detect_for_video(mp_image, timestamp_ms)
            if results.detections:
                detection = max(
                    results.detections,
                    key=lambda item: (
                        item.bounding_box.width * item.bounding_box.height
                    ),
                )
                box = detection.bounding_box
                if box.width > 0:
                    center_x = box.origin_x + box.width / 2.0
                    center_y = box.origin_y + box.height / 2.0
                    distance_m, horizontal_bearing, vertical_bearing = (
                        _estimate_face_geometry(
                            center_x,
                            center_y,
                            frame.shape[1],
                            frame.shape[0],
                            box.width,
                            self.focal_length_px,
                            self.known_face_width_m,
                        )
                    )
                    target_bearing = Vector3Stamped()
                    target_bearing.header = image_msg.header
                    target_bearing.vector.x = horizontal_bearing
                    target_bearing.vector.y = vertical_bearing
                    target_bearing.vector.z = 0.0
                    distance_msg = Float32(data=float(distance_m))

                    x1 = max(0, min(frame.shape[1] - 1, box.origin_x))
                    y1 = max(0, min(frame.shape[0] - 1, box.origin_y))
                    x2 = max(0, min(frame.shape[1] - 1, box.origin_x + box.width))
                    y2 = max(0, min(frame.shape[0] - 1, box.origin_y + box.height))
                    cv2.rectangle(annotated, (x1, y1), (x2, y2), (0, 255, 0), 2)
                    cv2.putText(
                        annotated,
                        f'{distance_m:.2f} m',
                        (x1, max(20, y1 - 8)),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.6,
                        (0, 255, 0),
                        2,
                    )

        if target_bearing is not None:
            self.target_bearing_pub.publish(target_bearing)
        self.target_distance_pub.publish(distance_msg)

        annotated_msg = self.bridge.cv2_to_imgmsg(annotated, encoding='bgr8')
        annotated_msg.header = image_msg.header
        self.annotated_image_pub.publish(annotated_msg)

    def destroy_node(self):
        if self.face_detector is not None:
            self.face_detector.close()
        if self.cap.isOpened():
            self.cap.release()
        super().destroy_node()

def main(args=None):
    rclpy.init(args=args)
    node = CameraNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()

if __name__ == '__main__':
    main()
