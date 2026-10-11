"""Open-loop test: does a trot reference itself translate the Go2?"""

import numpy as np
import jax
import go2_env

DEF = np.array([0.0, 0.9, -1.8] * 4)
OFF = np.array([0.0, np.pi, np.pi, 0.0])


def ref_action(i, freq, A, B, dt=0.02, scale=0.25):
    ph = 2 * np.pi * freq * dt * i
    a = np.zeros(12)
    for leg in range(4):
        p = ph + OFF[leg]
        a[leg * 3 + 1] = A * np.sin(p) / scale
        a[leg * 3 + 2] = -B * np.sin(p) / scale
    return a


def run(act_fn, n=500):
    env = go2_env.load_env(go2_env.default_config())
    st = env.reset(jax.random.PRNGKey(0))
    xs = []
    for i in range(n):
        st = st.replace(info={**st.info, "command": jax.numpy.array([0.0, 0.0, 0.0]),
                              "steps_until_next_cmd": jax.numpy.int32(10**7)})
        st = env.step(st, jax.numpy.array(act_fn(i), dtype=jax.numpy.float32))
        if i > 50:
            xs.append(float(np.asarray(st.data.qpos)[0]))
    return xs[-1] - xs[0], float(np.asarray(st.data.qpos)[2])


def main():
    for name, kw in [("ref A=B=0.3 f1.75", dict(freq=1.75, A=0.3, B=0.3)),
                     ("ref A=B=0.5 f2.0", dict(freq=2.0, A=0.5, B=0.5)),
                     ("ref A=0.6 B=0.3 f2.0", dict(freq=2.0, A=0.6, B=0.3))]:
        dx, z = run(lambda i: ref_action(i, **kw))
        print("%-24s dx=%+.3f z=%.3f" % (name, dx, z), flush=True)


if __name__ == "__main__":
    main()
