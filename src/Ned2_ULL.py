from pyniryo import *
import cv2
import numpy as np
import json



def backup_robot_pose(robot, filename="saved_poses.json"):
    # Get all saved poses
    saved_poses = robot.get_saved_pose_list()  # This returns a list of PoseObjects

    # List to store pose data
    poses_data = []

    # Iterate through the saved poses and convert them into dictionaries
    for pose in saved_poses:
        pose_data = {
            "name" : pose,
            "position": {
                "x": robot.get_pose_saved(pose).x,
                "y": robot.get_pose_saved(pose).y,
                "z": robot.get_pose_saved(pose).z
            },
            "orientation": {
                "roll": robot.get_pose_saved(pose).roll,
                "pitch": robot.get_pose_saved(pose).pitch,
                "yaw": robot.get_pose_saved(pose).yaw,

            }
        }
        poses_data.append(pose_data)

    # Save the poses data to a JSON file
    with open(filename, "w") as f:
        json.dump(poses_data, f, indent=4)

    print(f"All saved poses have been saved to {filename}")

def restore_robot_pose(robot, filename="saved_poses.json"):
    # Load the JSON file containing saved poses
    with open(filename, "r") as f:
        poses_data = json.load(f)

    # Iterate through the poses and save them to the robot
    for pose_data in poses_data:
        # Extract pose name
        pose_name = pose_data["name"]

        # Extract position (x, y, z)
        position = pose_data["position"]
        x = position["x"]
        y = position["y"]
        z = position["z"]

        # Extract orientation (roll, pitch, yaw)
        orientation = pose_data["orientation"]
        roll = orientation["roll"]
        pitch = orientation["pitch"]
        yaw = orientation["yaw"]

        # Create a PoseObject with the position and orientation
        pose = PoseObject(x, y, z, roll, pitch, yaw)

        # Save the pose to the robot
        robot.save_pose(pose_name, pose)

        print(f"Pose '{pose_name}' saved to robot.")

def create_robot_pose(robot,pose_name):
    pose = robot.get_pose()
    print("New position is created")
    print(pose)
    robot.save_pose(pose_name, pose)
    pose = robot.get_pose_saved(pose_name)
    return pose


def calibration_hsv(robot):
    """
    Interactive HSV calibration using the current robot camera frame.
    Press 'q' to finish and return selected HSV ranges.
    """
    img_compressed = robot.get_img_compressed()
    img = image_functions.uncompress_image(img_compressed)
    img_hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)

    window_name = "Calibracion HSV"
    cv2.namedWindow(window_name)
    cv2.createTrackbar("H min", window_name, 0, 179, lambda x: None)
    cv2.createTrackbar("S min", window_name, 0, 255, lambda x: None)
    cv2.createTrackbar("V min", window_name, 0, 255, lambda x: None)
    cv2.createTrackbar("H max", window_name, 179, 179, lambda x: None)
    cv2.createTrackbar("S max", window_name, 255, 255, lambda x: None)
    cv2.createTrackbar("V max", window_name, 255, 255, lambda x: None)

    hsv_min = [0, 0, 0]
    hsv_max = [179, 255, 255]

    try:
        while True:
            h_min = cv2.getTrackbarPos("H min", window_name)
            s_min = cv2.getTrackbarPos("S min", window_name)
            v_min = cv2.getTrackbarPos("V min", window_name)
            h_max = cv2.getTrackbarPos("H max", window_name)
            s_max = cv2.getTrackbarPos("S max", window_name)
            v_max = cv2.getTrackbarPos("V max", window_name)

            hsv_min = [h_min, s_min, v_min]
            hsv_max = [h_max, s_max, v_max]

            lower = np.array(hsv_min)
            upper = np.array(hsv_max)
            mask = cv2.inRange(img_hsv, lower, upper)
            result = cv2.bitwise_and(img, img, mask=mask)

            cv2.imshow("Imagen Original", img)
            cv2.imshow("Mascara", mask)
            cv2.imshow("Resultado", result)

            key = cv2.waitKey(1) & 0xFF
            if key == ord('q'):
                print("\nValores HSV seleccionados:")
                print(f"  hsv_min = {hsv_min}")
                print(f"  hsv_max = {hsv_max}")
                break
    finally:
        cv2.destroyAllWindows()

    return {"hsv_min": hsv_min, "hsv_max": hsv_max}



