from ..backend import xp


class TestImageKernels:
    def test_import_all_functions(self):
        from ..kernels import (
            average_correspondences_to_map_kernel,
            color_correspondences_to_map_kernel,
            exponential_correspondences_to_map_kernel,
            image_to_map_correspondence_kernel,
        )

        assert callable(image_to_map_correspondence_kernel)
        assert callable(average_correspondences_to_map_kernel)
        assert callable(exponential_correspondences_to_map_kernel)
        assert callable(color_correspondences_to_map_kernel)

    def test_image_to_map_correspondence_no_crash(self):
        from ..kernels import image_to_map_correspondence_kernel

        w, h = 4, 4
        res = 0.2
        kernel = image_to_map_correspondence_kernel(res, w, h, 0.1)
        assert callable(kernel)

        map_ = xp.zeros((3, w, h), dtype=xp.float32)
        map_[2] = 1.0
        map_[0, 2, 2] = 0.5

        x1 = xp.array([2.0], dtype=xp.float32)
        y1 = xp.array([2.0], dtype=xp.float32)
        z1 = xp.array([1.0], dtype=xp.float32)

        P = xp.array([500, 0, 0, 0, 0, 500, 0, 0, 0, 0, 1, 0], dtype=xp.float64)
        K = xp.array([500, 0, 320, 0, 500, 240, 0, 0, 1], dtype=xp.float64)
        D = xp.zeros(5, dtype=xp.float64)
        img_h = xp.array([480], dtype=xp.float32)
        img_w = xp.array([640], dtype=xp.float32)
        center = xp.array([0.0, 0.0, 0.0], dtype=xp.float32)

        uv = xp.zeros((2, w, h), dtype=xp.float32)
        valid = xp.zeros((1, w, h), dtype=xp.float32)

        kernel(map_, x1, y1, z1, P, K, D, img_h, img_w, center, uv, valid)

        assert uv.shape == (2, w, h)
        assert valid.shape == (1, w, h)

    def test_image_to_map_correspondence_distortion(self):
        from ..kernels import image_to_map_correspondence_kernel

        w, h = 4, 4
        kernel = image_to_map_correspondence_kernel(0.2, w, h, 0.1)
        map_ = xp.zeros((3, w, h), dtype=xp.float32)
        map_[2] = 1.0
        map_[0, 2, 2] = 0.5

        x1 = xp.array([2.0], dtype=xp.float32)
        y1 = xp.array([2.0], dtype=xp.float32)
        z1 = xp.array([1.0], dtype=xp.float32)
        P = xp.array([500, 0, 0, 0, 0, 500, 0, 0, 0, 0, 1, 0], dtype=xp.float64)
        K = xp.array([500, 0, 320, 0, 500, 240, 0, 0, 1], dtype=xp.float64)
        D = xp.array([0.1, -0.05, 0.001, 0.002, 0.01], dtype=xp.float64)
        img_h = xp.array([480], dtype=xp.float32)
        img_w = xp.array([640], dtype=xp.float32)
        center = xp.array([0.0, 0.0, 0.0], dtype=xp.float32)

        uv = xp.zeros((2, w, h), dtype=xp.float32)
        valid = xp.zeros((1, w, h), dtype=xp.float32)

        kernel(map_, x1, y1, z1, P, K, D, img_h, img_w, center, uv, valid)
        assert uv.shape == (2, w, h)
        assert valid.shape == (1, w, h)

    def test_average_correspondences_to_map(self):
        from ..kernels import average_correspondences_to_map_kernel

        w, h = 4, 4
        kernel = average_correspondences_to_map_kernel(w, h)
        assert callable(kernel)

        sem_map = xp.zeros((3, w, h), dtype=xp.float32)
        sem_map[0] = 0.5
        sem_map[2] = 1.0

        map_idx = xp.array([0], dtype=xp.float32)
        img_w, img_h = 8, 8
        image_mono = xp.ones((img_h, img_w), dtype=xp.float32) * 0.3

        uv = xp.ones((2, w, h), dtype=xp.float32) * 3.0
        valid = xp.ones((1, w, h), dtype=xp.float32)
        valid[0, 0, 0] = 0.0

        new_sem_map = xp.zeros((3, w, h), dtype=xp.float32)

        kernel(
            sem_map,
            map_idx,
            image_mono,
            uv,
            valid,
            xp.array([img_h], dtype=xp.float32),
            xp.array([img_w], dtype=xp.float32),
            new_sem_map,
        )

        assert new_sem_map.shape == (3, w, h)
        assert xp.any(new_sem_map != 0)

    def test_exponential_correspondences_to_map(self):
        from ..kernels import exponential_correspondences_to_map_kernel

        w, h = 4, 4
        alpha = 0.3
        kernel = exponential_correspondences_to_map_kernel(w, h, alpha)
        assert callable(kernel)

        sem_map = xp.ones((3, w, h), dtype=xp.float32) * 1.0
        sem_map[2] = 1.0

        map_idx = xp.array([0], dtype=xp.float32)
        img_w, img_h = 8, 8
        image_mono = xp.ones((img_h, img_w), dtype=xp.float32) * 0.0

        uv = xp.ones((2, w, h), dtype=xp.float32) * 3.0
        valid = xp.ones((1, w, h), dtype=xp.float32)

        new_sem_map = xp.ones((3, w, h), dtype=xp.float32) * 0.5

        kernel(
            sem_map,
            map_idx,
            image_mono,
            uv,
            valid,
            xp.array([img_h], dtype=xp.float32),
            xp.array([img_w], dtype=xp.float32),
            new_sem_map,
        )

        expected = 1.0 * (1 - alpha) + 0.0 * alpha
        assert xp.allclose(new_sem_map[0], expected)

    def test_exponential_no_valid_same_as_sem_map(self):
        from ..kernels import exponential_correspondences_to_map_kernel

        w, h = 4, 4
        kernel = exponential_correspondences_to_map_kernel(w, h, 0.3)
        sem_map = xp.ones((3, w, h), dtype=xp.float32) * 2.0
        sem_map[2] = 1.0

        map_idx = xp.array([0], dtype=xp.float32)
        image_mono = xp.ones((8, 8), dtype=xp.float32) * 0.0
        uv = xp.ones((2, w, h), dtype=xp.float32)
        valid = xp.zeros((1, w, h), dtype=xp.float32)
        new_sem_map = xp.zeros((3, w, h), dtype=xp.float32)

        kernel(
            sem_map,
            map_idx,
            image_mono,
            uv,
            valid,
            xp.array([8], dtype=xp.float32),
            xp.array([8], dtype=xp.float32),
            new_sem_map,
        )

        assert xp.allclose(new_sem_map, sem_map)

    def test_color_correspondences_to_map(self):
        from ..kernels import color_correspondences_to_map_kernel

        w, h = 4, 4
        kernel = color_correspondences_to_map_kernel(w, h)
        assert callable(kernel)

        sem_map = xp.zeros((3, w, h), dtype=xp.float32)
        sem_map[2] = 1.0

        map_idx = xp.array([0], dtype=xp.float32)
        img_w, img_h = 8, 8

        image_rgb = xp.zeros((3, img_h, img_w), dtype=xp.float32)
        image_rgb[0, 3, 3] = 255
        image_rgb[1, 3, 3] = 128
        image_rgb[2, 3, 3] = 64

        uv = xp.ones((2, w, h), dtype=xp.float32) * 3.0
        valid = xp.ones((1, w, h), dtype=xp.float32)

        new_sem_map = xp.zeros((3, w, h), dtype=xp.float32)

        kernel(
            sem_map,
            map_idx,
            image_rgb,
            uv,
            valid,
            xp.array([img_h], dtype=xp.float32),
            xp.array([img_w], dtype=xp.float32),
            new_sem_map,
        )

        assert new_sem_map.shape == (3, w, h)

    def test_color_invalid_correspondence(self):
        from ..kernels import color_correspondences_to_map_kernel

        w, h = 4, 4
        kernel = color_correspondences_to_map_kernel(w, h)
        sem_map = xp.ones((3, w, h), dtype=xp.float32) * 1.5
        new_sem_map = xp.zeros((3, w, h), dtype=xp.float32)

        kernel(
            sem_map,
            xp.array([0], dtype=xp.float32),
            xp.zeros((3, 8, 8), dtype=xp.float32),
            xp.ones((2, w, h), dtype=xp.float32),
            xp.zeros((1, w, h), dtype=xp.float32),
            xp.array([8], dtype=xp.float32),
            xp.array([8], dtype=xp.float32),
            new_sem_map,
        )

        assert xp.allclose(new_sem_map, sem_map)
