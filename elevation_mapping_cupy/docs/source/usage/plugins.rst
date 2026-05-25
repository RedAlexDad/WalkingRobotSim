.. _plugins:

Plugins
******************************************************************

Plugins are optional post-processing steps that run on the GPU and produce additional map layers
(e.g. smoothing, inpainting).

In this repository, plugins are configured via:

* ``elevation_mapping_cupy/config/core/plugin_config.yaml``

and implemented as Python modules under:

* ``elevation_mapping_cupy/elevation_mapping_cupy/plugins/``


Built-in Plugins
==================================================================

The default plugin configuration enables:

* ``min_filter``: fills invalid holes using a local minimum.
* ``smooth_filter``: smooths a height layer.
* ``inpainting``: inpaints using OpenCV (CPU-side).
* ``erosion``: simple erosion/dilation on traversability-like layers.


Creating a Plugin
==================================================================

1. Add a new Python module under ``elevation_mapping_cupy/elevation_mapping_cupy/plugins/``
2. Implement a class deriving from ``PluginBase`` (see ``plugin_manager.py``)
3. Enable it in ``plugin_config.yaml`` (with ``type``, ``layer_name``, and ``extra_params``)

Minimal example:

.. code-block:: python

  import cupy as cp
  from elevation_mapping_cupy.plugins.plugin_manager import PluginBase

  class ExamplePlugin(PluginBase):
      def __init__(self, add_value: float = 1.0, **kwargs):
          self.add_value = float(add_value)

      def __call__(self, elevation_map, layer_names, plugin_layers, plugin_layer_names, semantic_map, semantic_layer_names):
          # elevation_map[0] is the elevation layer
          return elevation_map[0] + self.add_value

