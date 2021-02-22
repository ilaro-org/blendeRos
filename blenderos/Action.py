import bpy
import time
from collections import UserDict

from bpy.types import Operator

# try: import roslibpy
# except: print("roslibpy did not load")

import roslibpy
import roslibpy.actionlib

trajectory = []

def sendAction():

    c=bpy.context.scene.controls
    print("ip " + c.ip_address)
    print("port " + c.ip_port)

    client = roslibpy.Ros(host='localhost', port=9090)
    client.run()

    now_sec = client.get_time().to_sec()

    action_client = roslibpy.actionlib.ActionClient(client,
                                                    '/joint_trajectory_action',
                                                    'control_msgs/FollowJointTrajectoryAction')

    # l = len(trajectory)
    point_array = []
    for i, joint_position in enumerate(trajectory):
        point_array.append(
            dict(
                    positions=joint_position,
                    #velocities=[1,1,1,1,1,1],
                    #accelerations=[1,1,1,1,1,1],
                    # effort=[],
                    time_from_start=roslibpy.Time(i*2, 0),
                )
        )
    print(point_array)

    goal = roslibpy.actionlib.Goal(action_client,
        roslibpy.Message(
            dict(
                # header=roslibpy.Header(seq=1, stamp=roslibpy.Time(now_sec, 0), frame_id=''),
                # goal_id= dict(stamp='', id=''), #stamp=roslibpy.Time(now_sec, 0), frame_id='holi'),
#                goal=dict(
                    trajectory=
                    dict(
                        header=roslibpy.Header(seq=1, stamp=roslibpy.Time(now_sec+1, 0), frame_id=''), #roslibpy.Time.now()
                        joint_names=['joint_1','joint_2','joint_3','joint_4', 'joint_5', 'joint_6'],
                        points=point_array,
                        ),
                    # control_msgs/JointTolerance[] path_tolerance
                    # control_msgs/JointTolerance[] goal_tolerance
                    goal_time_tolerance = roslibpy.Time(100, 0),
#                    ),
                )
            )
        )

    goal.on('feedback', lambda f: print(f['sequence']))
    goal.send()

    result = goal.wait(10)
    action_client.dispose()

    # print('Result: {}'.format(result['sequence']))
    client.terminate()


def calculateAction():
    global trajectory
    trajectory = []
    print("clean trajectory")
    print(trajectory)
    bpy.app.handlers.frame_change_post.append(frameChange)
    #start animation
    bpy.ops.screen.animation_play()
    print("playing")


def frameChange(scene):
    print("Frame %i" % scene.frame_current)

    global trajectory
    joints = []
    if bpy.context.scene.controls.ik_control:
        # get join rotations in inverse kinematics mode
        b0 = bpy.data.objects['staubliTX60'].pose.bones["base_link"]
        b1 = bpy.data.objects['staubliTX60'].pose.bones["joint_1"]
        b2 = bpy.data.objects['staubliTX60'].pose.bones["joint_2"]
        b3 = bpy.data.objects['staubliTX60'].pose.bones["joint_3"]
        b4 = bpy.data.objects['staubliTX60'].pose.bones["joint_4"]
        b5 = bpy.data.objects['staubliTX60'].pose.bones["joint_5"]
        b6 = bpy.data.objects['staubliTX60'].pose.bones["joint_6"]

        joints.append((b0.matrix.inverted()@b1.matrix).to_euler()[1])
        joints.append((b1.matrix.inverted()@b2.matrix).to_euler()[2])
        joints.append((b2.matrix.inverted()@b3.matrix).to_euler()[2])
        joints.append((b3.matrix.inverted()@b4.matrix).to_euler()[1])
        joints.append((b4.matrix.inverted()@b5.matrix).to_euler()[2])
        joints.append((b5.matrix.inverted()@b6.matrix).to_euler()[1])
        # print("IK *>")
    else:
        # get join rotations in fordware kinematics mode
        joints.append(bpy.data.objects['staubliTX60'].pose.bones["joint_1"].matrix_basis.to_euler()[1])
        joints.append(bpy.data.objects['staubliTX60'].pose.bones["joint_2"].matrix_basis.to_euler()[2])
        joints.append(bpy.data.objects['staubliTX60'].pose.bones["joint_3"].matrix_basis.to_euler()[2])
        joints.append(bpy.data.objects['staubliTX60'].pose.bones["joint_4"].matrix_basis.to_euler()[1])
        joints.append(bpy.data.objects['staubliTX60'].pose.bones["joint_5"].matrix_basis.to_euler()[2])
        joints.append(bpy.data.objects['staubliTX60'].pose.bones["joint_6"].matrix_basis.to_euler()[1])
        # print("FK *>")

    trajectory.append(joints)

    if scene.frame_current == scene.frame_end:
        bpy.ops.screen.animation_cancel(restore_frame=False)
        # bpy.app.handlers.frame_change_post.remove(self)
        for h in bpy.app.handlers.frame_change_post:
            if h.__name__ == 'frameChange':
                bpy.app.handlers.frame_change_post.remove(h)
        print(trajectory)
        sendAction()

class ROS_OT_action(Operator):
    bl_label = "build trajectory and set action"
    bl_idname = "ros.action"
    bl_description = "play and stream joint angles"

    @classmethod
    def poll(cls, context):
        return True

    def execute(self, context):
        print("streaming!")
        calculateAction()
        return {'FINISHED'}
