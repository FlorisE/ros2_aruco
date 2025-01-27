"""
This node locates Aruco AR markers in images and publishes their ids and poses.

Subscriptions:
   /camera/image_raw (sensor_msgs.msg.Image)
   /camera/camera_info (sensor_msgs.msg.CameraInfo)
   /camera/camera_info (sensor_msgs.msg.CameraInfo)

Published Topics:
    /aruco_poses (geometry_msgs.msg.PoseArray)
       Pose of all detected markers (suitable for rviz visualization)

    /aruco_markers (ros2_aruco_interfaces.msg.ArucoMarkers)
       Provides an array of all poses along with the corresponding
       marker ids.

Parameters:
    marker_size - size of the markers in meters (default .0625)
    aruco_dictionary_id - dictionary that was used to generate markers
                          (default DICT_5X5_250)
    image_topic - image topic to subscribe to (default /camera/image_raw)
    camera_info_topic - camera info topic to subscribe to
                         (default /camera/camera_info)

Author: Nathan Sprague
Version: 10/26/2020

"""

import rclpy
import rclpy.node
from rclpy.qos import qos_profile_sensor_data
from cv_bridge import CvBridge
import numpy as np
import cv2
from ros2_aruco import transformations

from sensor_msgs.msg import CameraInfo
from sensor_msgs.msg import Image
from geometry_msgs.msg import PoseArray, Pose, TransformStamped
from ros2_aruco_interfaces.msg import ArucoMarkers, ChArUcoBoard

from tf2_ros import TransformBroadcaster


class ArucoNode(rclpy.node.Node):

    def __init__(self):
        super().__init__('aruco_node')

        # Declare and read parameters
        self.declare_parameter("marker_size", .0625)
        self.declare_parameter("aruco_dictionary_id", "DICT_5X5_250")
        self.declare_parameter("image_topic", "/camera/image_raw")
        self.declare_parameter("camera_info_topic", "/camera/camera_info")
        self.declare_parameter("camera_frame", None)
        self.declare_parameter("dictionary_bits", -1)
        self.declare_parameter("dictionary_size", -1)
        self.declare_parameter("dictionary_seed", 0)
        self.declare_parameter("do_corner_refinement", False)
        self.declare_parameter("publish_tf", False)
        self.declare_parameter("publish_charuco_pose", False)
        self.declare_parameter("charuco_square_x", 7)
        self.declare_parameter("charuco_square_y", 5)
        self.declare_parameter("charuco_square_length", 0.1)
        self.declare_parameter("corner_refinement_method",
                               "CORNER_REFINE_NONE")

        self.marker_size = self.get_parameter("marker_size").\
            get_parameter_value().double_value
        dictionary_id_name = self.get_parameter(
            "aruco_dictionary_id").get_parameter_value().string_value
        image_topic = self.get_parameter("image_topic").\
            get_parameter_value().string_value
        info_topic = self.get_parameter("camera_info_topic").\
            get_parameter_value().string_value
        self.camera_frame = self.get_parameter("camera_frame").\
            get_parameter_value().string_value

        # Make sure we have a valid dictionary id:
        if dictionary_id_name != "CUSTOM":
            try:
                dictionary_id = cv2.aruco.__getattribute__(dictionary_id_name)
                if type(dictionary_id) != type(cv2.aruco.DICT_5X5_100):
                    raise AttributeError
            except AttributeError:
                self.get_logger().error(
                    'bad aruco_dictionary_id: {}'.format(dictionary_id_name))
                options = "\n".join(
                    [s for s in dir(cv2.aruco) if s.startswith("DICT")])
                self.get_logger().error("valid options: {}".format(options))

            self.aruco_dictionary = cv2.aruco.Dictionary_get(dictionary_id)
        else:
            dict_bits = self.get_parameter("dictionary_bits").\
                get_parameter_value().integer_value
            dict_size = self.get_parameter("dictionary_size").\
                get_parameter_value().integer_value
            dict_seed = self.get_parameter("dictionary_seed").\
                get_parameter_value().integer_value
            self.aruco_dictionary = cv2.aruco.Dictionary_create(dict_bits,
                                                                dict_size,
                                                                dict_seed)

        # Set up subscriptions
        self.info_sub = self.create_subscription(CameraInfo,
                                                 info_topic,
                                                 self.info_callback,
                                                 qos_profile_sensor_data)

        self.create_subscription(Image, image_topic,
                                 self.image_callback, qos_profile_sensor_data)

        # Set up publishers
        self.poses_pub = self.create_publisher(PoseArray, 'aruco_poses', 10)
        self.markers_pub = self.create_publisher(ArucoMarkers,
                                                 'aruco_markers',
                                                 10)

        # Set up fields for camera parameters
        self.info_msg = None
        self.intrinsic_mat = None
        self.distortion = None

        self.aruco_parameters = cv2.aruco.DetectorParameters_create()
        self.bridge = CvBridge()

        if self.get_parameter("do_corner_refinement").\
                get_parameter_value().bool_value:
            corner_refinement_methods = [
                'CORNER_REFINE_NONE',
                'CORNER_REFINE_SUBPIX',
                'CORNER_REFINE_CONTOUR',
                'CORNER_REFINE_APRILTAG'
            ]
            corner_refinement_method_value = self.\
                get_parameter("corner_refinement_method").\
                get_parameter_value().string_value
            corner_refinement_method_index = corner_refinement_methods.\
                index(corner_refinement_method_value)
            self.aruco_parameters.cornerRefinementMethod = \
                corner_refinement_method_index

        self.publish_tf = self.get_parameter("publish_tf").\
            get_parameter_value().bool_value

        if self.publish_tf:
            self.br = TransformBroadcaster(self)

        self.publish_charuco_pose = self.\
            get_parameter("publish_charuco_pose").\
            get_parameter_value().bool_value

        self.charuco_square_x = self.\
            get_parameter("charuco_square_x").\
            get_parameter_value().integer_value

        self.charuco_square_y = self.\
            get_parameter("charuco_square_x").\
            get_parameter_value().integer_value

        self.charuco_square_length = self.\
            get_parameter("charuco_square_length").\
            get_parameter_value().double_value

        if self.publish_charuco_pose:
            self.charuco_pose_pub = self.create_publisher(ChArUcoBoard,
                                                          'charuco_pose',
                                                          10)

    def info_callback(self, info_msg):
        self.info_msg = info_msg
        self.intrinsic_mat = np.reshape(np.array(self.info_msg.k), (3, 3))
        self.distortion = np.array(self.info_msg.d)
        # Assume that camera parameters will remain the same...
        self.destroy_subscription(self.info_sub)

    def image_callback(self, img_msg):
        if self.info_msg is None:
            self.get_logger().warn("No camera info has been received!")
            return

        cv_image = self.bridge.imgmsg_to_cv2(img_msg,
                                             desired_encoding='mono8')
        markers = ArucoMarkers()
        pose_array = PoseArray()
        if self.camera_frame is None:
            markers.header.frame_id = self.info_msg.header.frame_id
            pose_array.header.frame_id = self.info_msg.header.frame_id
        else:
            markers.header.frame_id = self.camera_frame
            pose_array.header.frame_id = self.camera_frame

        markers.header.stamp = img_msg.header.stamp
        pose_array.header.stamp = img_msg.header.stamp

        corners, \
            marker_ids, \
            rejected = \
            cv2.aruco.detectMarkers(cv_image,
                                    self.aruco_dictionary,
                                    parameters=self.aruco_parameters)
        if marker_ids is not None:

            if cv2.__version__ > '4.0.0':
                rvecs, \
                    tvecs, \
                    _ = cv2.aruco.estimatePoseSingleMarkers(corners,
                                                            self.marker_size,
                                                            self.intrinsic_mat,
                                                            self.distortion)
            else:
                rvecs, \
                    tvecs = \
                    cv2.aruco.estimatePoseSingleMarkers(corners,
                                                        self.marker_size,
                                                        self.intrinsic_mat,
                                                        self.distortion)

            for i, marker_id in enumerate(marker_ids):
                pose = Pose()
                pose.position.x = tvecs[i][0][0]
                pose.position.y = tvecs[i][0][1]
                pose.position.z = tvecs[i][0][2]

                rot_matrix = np.eye(4)
                rot_matrix[0:3, 0:3] = cv2.Rodrigues(np.array(rvecs[i][0]))[0]
                quat = transformations.quaternion_from_matrix(rot_matrix)

                pose.orientation.x = quat[0]
                pose.orientation.y = quat[1]
                pose.orientation.z = quat[2]
                pose.orientation.w = quat[3]

                pose_array.poses.append(pose)
                markers.poses.append(pose)
                markers.marker_ids.append(marker_id[0])

                if self.publish_tf:
                    t = TransformStamped()

                    t.header.stamp = img_msg.header.stamp
                    t.header.frame_id = self.camera_frame or \
                        self.info.msg.header.frame_id
                    t.child_frame_id = f"marker_{marker_id[0]}"
                    t.transform.translation.x = pose.position.x
                    t.transform.translation.y = pose.position.y
                    t.transform.translation.z = pose.position.z
                    t.transform.rotation.x = quat[0]
                    t.transform.rotation.y = quat[1]
                    t.transform.rotation.z = quat[2]
                    t.transform.rotation.w = quat[3]

                    self.br.sendTransform(t)

            self.poses_pub.publish(pose_array)
            self.markers_pub.publish(markers)

            if self.publish_charuco_pose:
                board = cv2.aruco.CharucoBoard_create(self.charuco_square_x,
                                                      self.charuco_square_y,
                                                      self.charuco_square_length,
                                                      self.marker_size,
                                                      self.aruco_dictionary)
                n_corners, \
                    ch_corners, \
                    ch_ids = cv2.aruco.interpolateCornersCharuco(corners,
                                                                 marker_ids,
                                                                 cv_image,
                                                                 board=board)

                if n_corners > 0:
                    success, \
                        rvec, \
                        tvec = cv2.aruco.estimatePoseCharucoBoard(
                            ch_corners,
                            ch_ids,
                            board,
                            self.intrinsic_mat,
                            self.distortion,
                            None,
                            None)

                    if success:
                        board_msg = ChArUcoBoard()
                        board_msg.pose.position.x = tvec[0][0]
                        board_msg.pose.position.y = tvec[1][0]
                        board_msg.pose.position.z = tvec[2][0]

                        rot_matrix = np.eye(4)
                        rot_matrix[0:3, 0:3] = cv2.Rodrigues(np.array(rvec))[0]
                        quat = transformations.quaternion_from_matrix(rot_matrix)

                        board_msg.pose.orientation.x = quat[0]
                        board_msg.pose.orientation.y = quat[1]
                        board_msg.pose.orientation.z = quat[2]
                        board_msg.pose.orientation.w = quat[3]

                        self.charuco_pose_pub.publish(board_msg)

                        if self.publish_tf:
                            t = TransformStamped()

                            t.header.stamp = img_msg.header.stamp
                            t.header.frame_id = self.camera_frame or \
                                self.info.msg.header.frame_id
                            t.child_frame_id = "charuco_board"
                            t.transform.translation.x = tvec[0][0]
                            t.transform.translation.y = tvec[1][0]
                            t.transform.translation.z = tvec[2][0]
                            t.transform.rotation.x = quat[0]
                            t.transform.rotation.y = quat[1]
                            t.transform.rotation.z = quat[2]
                            t.transform.rotation.w = quat[3]

                            self.br.sendTransform(t)


def main():
    rclpy.init()
    node = ArucoNode()
    rclpy.spin(node)

    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()
