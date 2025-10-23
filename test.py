from ultralytics import YOLO
import cv2
import numpy as np
import time
import os
from datetime import datetime
import sys

# Add sort directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'sort'))
from sort import Sort

class LicensePlateTracker:
    """
    License Plate Detection and Tracking System
    - RTSP stream acquisition
    - Frame sampling (every 10 frames)
    - YOLO-based plate detection
    - SORT-based tracking and deduplication
    - New plate image saving
    """
    
    def __init__(self, 
                 rtsp_url,
                 model_path="license_plate_detector.pt",
                 confidence_threshold=0.5,
                 frame_skip=10,
                 output_dir="detected_plates"):
        """
        Initialize the License Plate Tracker
        
        Args:
            rtsp_url: RTSP stream URL or video file path
            model_path: Path to YOLOv8 model
            confidence_threshold: Minimum confidence for detection
            frame_skip: Process every N frames
            output_dir: Directory to save detected plate images
        """
        # Load YOLO model
        print(f"Loading YOLO model from {model_path}...")
        self.model = YOLO(model_path)
        
        # Parameters
        self.rtsp_url = rtsp_url
        self.confidence_threshold = confidence_threshold
        self.frame_skip = frame_skip
        self.output_dir = output_dir
        
        # Create output directory
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
            print(f"Created output directory: {output_dir}")
        
        # Initialize SORT tracker
        # max_age: frames to keep alive a track without detections
        # min_hits: minimum detections before track is confirmed
        # iou_threshold: minimum IOU for matching
        self.tracker = Sort(max_age=30, min_hits=3, iou_threshold=0.3)
        
        # Track history - store track IDs that have been saved
        self.saved_track_ids = set()
        
        # Statistics
        self.frame_count = 0
        self.processed_count = 0
        self.detection_count = 0
        self.new_plate_count = 0
        
    def process_stream(self):
        """
        Main processing loop for RTSP stream
        """
        # Open video stream
        print(f"Opening stream: {self.rtsp_url}")
        cap = cv2.VideoCapture(self.rtsp_url)
        
        if not cap.isOpened():
            print(f"Error: Could not open stream {self.rtsp_url}")
            return
        
        print("Stream opened successfully")
        print(f"Processing every {self.frame_skip} frames")
        print(f"Confidence threshold: {self.confidence_threshold}")
        print(f"Press 'q' to quit\n")
        
        start_time = time.time()
        
        try:
            while True:
                ret, frame = cap.read()
                
                if not ret:
                    print("End of stream or error reading frame")
                    break
                
                self.frame_count += 1
                
                # Frame sampling - process every N frames
                if self.frame_count % self.frame_skip != 0:
                    continue
                
                self.processed_count += 1
                
                # Detect license plates
                detections = self.detect_plates(frame)
                
                # Update tracker with detections
                tracked_objects = self.tracker.update(detections)
                
                # Process tracked objects
                self.process_tracked_plates(frame, tracked_objects)
                
                # Display frame with annotations
                display_frame = self.draw_results(frame, tracked_objects)
                
                # Show statistics
                self.draw_statistics(display_frame)
                
                # Display the frame
                cv2.imshow('License Plate Tracking', display_frame)
                
                # Check for quit
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    print("\nQuitting...")
                    break
                
                # Print progress every 100 processed frames
                if self.processed_count % 100 == 0:
                    elapsed = time.time() - start_time
                    fps = self.processed_count / elapsed
                    print(f"Processed: {self.processed_count} frames, "
                          f"Detected: {self.detection_count} plates, "
                          f"New plates: {self.new_plate_count}, "
                          f"FPS: {fps:.2f}")
        
        finally:
            # Cleanup
            cap.release()
            cv2.destroyAllWindows()
            
            # Final statistics
            elapsed = time.time() - start_time
            print("\n" + "="*50)
            print("Processing Complete")
            print("="*50)
            print(f"Total frames: {self.frame_count}")
            print(f"Processed frames: {self.processed_count}")
            print(f"Total detections: {self.detection_count}")
            print(f"Unique plates saved: {self.new_plate_count}")
            print(f"Total time: {elapsed:.2f} seconds")
            print(f"Average FPS: {self.processed_count / elapsed:.2f}")
            print("="*50)
    
    def detect_plates(self, frame):
        """
        Detect license plates in frame using YOLO
        
        Args:
            frame: Input image frame
            
        Returns:
            numpy array of detections in format [[x1,y1,x2,y2,score], ...]
        """
        # Run YOLO detection
        results = self.model(frame, verbose=False)
        
        # Extract detections
        detections = []
        result = results[0]
        boxes = result.boxes
        
        for box in boxes:
            conf = box.conf[0].item()
            
            # Filter by confidence threshold
            if conf >= self.confidence_threshold:
                x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                detections.append([x1, y1, x2, y2, conf])
        
        if detections:
            self.detection_count += len(detections)
            return np.array(detections)
        else:
            return np.empty((0, 5))
    
    def process_tracked_plates(self, frame, tracked_objects):
        """
        Process tracked objects and save new plates
        
        Args:
            frame: Current frame
            tracked_objects: Array of tracked objects from SORT
                            Format: [[x1,y1,x2,y2,track_id], ...]
        """
        for obj in tracked_objects:
            x1, y1, x2, y2, track_id = obj
            track_id = int(track_id)
            
            # Check if this is a new track (not saved before)
            if track_id not in self.saved_track_ids:
                # Save the plate image
                self.save_plate_image(frame, x1, y1, x2, y2, track_id)
                
                # Mark this track as saved
                self.saved_track_ids.add(track_id)
                self.new_plate_count += 1
                
                print(f"New plate detected! Track ID: {track_id}, Total unique: {self.new_plate_count}")
    
    def save_plate_image(self, frame, x1, y1, x2, y2, track_id):
        """
        Save cropped plate image to disk
        
        Args:
            frame: Full frame
            x1, y1, x2, y2: Bounding box coordinates
            track_id: Track ID from SORT
        """
        # Convert coordinates to integers
        x1, y1, x2, y2 = int(x1), int(y1), int(x2), int(y2)
        
        # Ensure coordinates are within frame bounds
        h, w = frame.shape[:2]
        x1 = max(0, x1)
        y1 = max(0, y1)
        x2 = min(w, x2)
        y2 = min(h, y2)
        
        # Crop plate region
        plate_img = frame[y1:y2, x1:x2]
        
        # Generate filename with timestamp and track ID
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        filename = f"plate_track{track_id:04d}_{timestamp}.jpg"
        filepath = os.path.join(self.output_dir, filename)
        
        # Save image
        cv2.imwrite(filepath, plate_img)
        print(f"  Saved: {filename}")
    
    def draw_results(self, frame, tracked_objects):
        """
        Draw bounding boxes and track IDs on frame
        
        Args:
            frame: Input frame
            tracked_objects: Tracked objects from SORT
            
        Returns:
            Annotated frame
        """
        display_frame = frame.copy()
        
        for obj in tracked_objects:
            x1, y1, x2, y2, track_id = obj
            x1, y1, x2, y2 = int(x1), int(y1), int(x2), int(y2)
            track_id = int(track_id)
            
            # Choose color based on whether it's saved or not
            if track_id in self.saved_track_ids:
                color = (0, 255, 0)  # Green for saved plates
                status = "Saved"
            else:
                color = (0, 165, 255)  # Orange for tracking
                status = "Tracking"
            
            # Draw bounding box
            cv2.rectangle(display_frame, (x1, y1), (x2, y2), color, 2)
            
            # Draw track ID and status
            label = f"ID:{track_id} [{status}]"
            cv2.putText(display_frame, label, (x1, y1 - 10),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)
        
        return display_frame
    
    def draw_statistics(self, frame):
        """
        Draw statistics overlay on frame
        
        Args:
            frame: Frame to draw on
        """
        # Create semi-transparent background for text
        overlay = frame.copy()
        h, w = frame.shape[:2]
        
        # Statistics text
        stats = [
            f"Total Frames: {self.frame_count}",
            f"Processed: {self.processed_count}",
            f"Detections: {self.detection_count}",
            f"Unique Plates: {self.new_plate_count}",
            f"Active Tracks: {len(self.tracker.trackers)}"
        ]
        
        # Draw background rectangle
        cv2.rectangle(overlay, (10, 10), (350, 30 + len(stats) * 30), 
                     (0, 0, 0), -1)
        cv2.addWeighted(overlay, 0.6, frame, 0.4, 0, frame)
        
        # Draw text
        for i, stat in enumerate(stats):
            cv2.putText(frame, stat, (20, 35 + i * 30),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)


def main():
    """
    Main function - configure and run the tracker
    """
    # Configuration
    # For RTSP stream, use format: "rtsp://username:password@ip:port/stream"
    # For testing with video file or image, provide the file path
    
    # Example configurations:
    # RTSP_URL = "rtsp://admin:admin@192.168.6.136:554/11"
    RTSP_URL = "25fps_smaller.mp4"  # Video file
    # RTSP_URL = "K77RsKINcX.jpg"  # Image file (will process once)
    
    MODEL_PATH = "license_plate_detector.pt"
    CONFIDENCE_THRESHOLD = 0.5
    FRAME_SKIP = 1  # Process every 10 frames
    OUTPUT_DIR = "detected_plates"
    
    # Create tracker
    tracker = LicensePlateTracker(
        rtsp_url=RTSP_URL,
        model_path=MODEL_PATH,
        confidence_threshold=CONFIDENCE_THRESHOLD,
        frame_skip=FRAME_SKIP,
        output_dir=OUTPUT_DIR
    )
    
    # Start processing
    tracker.process_stream()


if __name__ == "__main__":
    main()
