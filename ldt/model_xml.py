"""Programmatic MJCF for a 12-DoF quadruped (torso + 4 legs x [abduction, hip, knee]).

Only the foot spheres and the trunk collide with the floor (contype/conaffinity bitmasks),
so contact mode is fully described by the four binary foot-contact indicators.
"""

LEGS = [("FL", +1, +1), ("FR", +1, -1), ("RL", -1, +1), ("RR", -1, -1)]  # name, sx, sy
L_THIGH = 0.21
L_CALF = 0.21
FOOT_R = 0.02


def _leg(name: str, sx: int, sy: int) -> str:
    return f"""
      <body name="{name}_hip" pos="{sx * 0.18} {sy * 0.09} 0">
        <joint name="{name}_abd" type="hinge" axis="1 0 0" range="-0.7 0.7"/>
        <geom type="capsule" fromto="0 0 0 0 {sy * 0.06} 0" size="0.03" mass="0.5"/>
        <body name="{name}_thigh" pos="0 {sy * 0.06} 0">
          <joint name="{name}_hip" type="hinge" axis="0 1 0" range="-1.2 2.6"/>
          <geom type="capsule" fromto="0 0 0 0 0 -{L_THIGH}" size="0.02" mass="0.7"/>
          <body name="{name}_calf" pos="0 0 -{L_THIGH}">
            <joint name="{name}_knee" type="hinge" axis="0 1 0" range="-2.75 -0.4"/>
            <geom type="capsule" fromto="0 0 0 0 0 -{L_CALF}" size="0.015" mass="0.15"/>
            <geom name="{name}_foot" type="sphere" pos="0 0 -{L_CALF}" size="{FOOT_R}" mass="0.05"
                  contype="2" conaffinity="1"/>
          </body>
        </body>
      </body>"""


def build_xml() -> str:
    legs = "".join(_leg(*l) for l in LEGS)
    acts = "".join(
        f'\n    <motor name="{n}_{j}" joint="{n}_{j}" gear="1"/>'
        for n, _, _ in LEGS for j in ("abd", "hip", "knee")
    )
    return f"""<mujoco model="quadruped12">
  <compiler angle="radian"/>
  <option timestep="0.001" gravity="0 0 -9.81" integrator="implicitfast" cone="pyramidal"/>
  <default>
    <geom contype="0" conaffinity="0" friction="0.8 0.005 0.0001" solref="0.02 1" solimp="0.95 0.99 0.001"/>
    <joint armature="0.01" limited="true"/>
    <motor ctrllimited="true" ctrlrange="-33.5 33.5"/>
  </default>
  <worldbody>
    <geom name="floor" type="plane" size="30 30 0.1" contype="1" conaffinity="2"/>
    <body name="trunk" pos="0 0 0.32">
      <freejoint name="root"/>
      <geom name="trunk_geom" type="box" size="0.2 0.09 0.05" mass="8" contype="2" conaffinity="1"/>{legs}
    </body>
  </worldbody>
  <actuator>{acts}
  </actuator>
</mujoco>"""
