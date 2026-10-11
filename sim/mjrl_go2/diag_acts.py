"""Diagnostics: do actuators move joints, and does a hand trot translate?"""

import numpy as np
import jax
import go2_env

DEF = np.array([0.0, 0.9, -1.8] * 4)


def run(act_fn, n=250):
    env = go2_env.load_env(go2_env.default_config())
    st = env.reset(jax.random.PRNGKey(0))
    xs = []
    for i in range(n):
        st = st.replace(info={
            **st.info,
            "command": jax.numpy.array([0.0, 0.0, 0.0]),
            "steps_until_next_cmd": jax.numpy.int32(10**7),
        })
        st = env.step(st, jax.numpy.array(act_fn(i), dtype=jax.numpy.float32))
        if i > 50:
            xs.append(float(np.asarray(st.data.qpos)[0]))
    return xs, np.asarray(st.data.qpos), np.asarray(st.data.qvel)


def hand_trot(i):
    t = i * 0.02
    ph = 2 * np.pi * 2.0 * t
    a = [0.0] * 12
    for leg, off in [(0, 0.0), (1, np.pi), (2, np.pi), (3, 0.0)]:
        a[leg * 3 + 1] = 0.6 * np.sin(ph + off)
        a[leg * 3 + 2] = -0.6 * np.sin(ph + off)
    return a


def main():
    xs, q, qv = run(lambda i: [1.0] * 12)
    print("const act=1: dx=%.3f d_qpos7=%s" % (xs[-1] - xs[0], np.round(q[7:] - DEF, 2)), flush=True)
    print("const act=1: |qvel|max=%.3f" % np.abs(qv).max(), flush=True)

    xs, q, qv = run(hand_trot, 350)
    print("hand trot: dx=%.3f z=%.3f |vx|=%.3f" % (
        xs[-1] - xs[0], q[2], np.abs(qv[0])), flush=True)

    xs, q, qv = run(lambda i: [0, -1.0, 0] * 4)
    print("thigh-1: dx=%.3f" % (xs[-1] - xs[0]), flush=True)


if __name__ == "__main__":
    main()
