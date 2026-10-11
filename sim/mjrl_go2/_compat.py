"""Compat shims: restore pmap-style helpers removed in recent jax."""

import jax

if not hasattr(jax, "device_put_replicated"):

    def _device_put_replicated(tree, devices):
        n = len(devices)
        return jax.tree_util.tree_map(
            lambda v: jax.numpy.broadcast_to(v, (n,) + jax.numpy.shape(v)),
            tree,
        )

    jax.device_put_replicated = _device_put_replicated

if not hasattr(jax, "device_put_sharded"):

    def _device_put_sharded(shards, devices):
        return jax.device_put(jax.numpy.stack(shards, axis=0), devices[0])

    jax.device_put_sharded = _device_put_sharded
