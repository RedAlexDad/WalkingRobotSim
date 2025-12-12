import sys
if sys.prefix == '/usr':
    sys.real_prefix = sys.prefix
    sys.prefix = sys.exec_prefix = '/home/redalexdad/GitHub/WalkingRobotSim/install/ros2_navigation'
