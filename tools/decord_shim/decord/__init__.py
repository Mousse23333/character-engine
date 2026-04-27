"""Minimal decord-API shim using imageio[ffmpeg] backend, for ARM64 systems where
decord has no wheel available. Implements the slice of decord API that
Wan 2.2 (wan/animate.py, wan/speech2video.py) actually uses:

    VideoReader(path)
        - len(vr)
        - vr.get_batch(idxs).asnumpy()  → ndarray [N, H, W, 3] uint8 RGB
        - vr.get_avg_fps()                → float

    cpu()                                  → "cpu" tag (no-op)
    bridge.set_bridge('torch')             → no-op (we always return numpy)
"""
import numpy as np
from PIL import Image


class _NDArrayWrapper:
    """Mimics the NDArray returned by decord; main use is .asnumpy()."""
    def __init__(self, arr):
        self._arr = arr
    def asnumpy(self):
        return self._arr
    def __array__(self):
        return self._arr


class VideoReader:
    def __init__(self, path, ctx=None, num_threads=0, width=-1, height=-1):
        # Lazy-import so this shim costs nothing if not used
        import imageio.v3 as iio
        self._path = str(path)
        # imageio.v3.improps gives frame count + fps without loading video
        try:
            props = iio.improps(self._path)
            self._n_frames = int(props.n_frames) if props.n_frames > 0 else None
        except Exception:
            self._n_frames = None
        # Get fps via metadata
        try:
            meta = iio.immeta(self._path)
            self._fps = float(meta.get("fps") or meta.get("framerate") or 30.0)
            self._duration = float(meta.get("duration") or 0.0)
            if self._n_frames is None and self._duration:
                self._n_frames = int(round(self._duration * self._fps))
        except Exception:
            self._fps = 30.0
        # Cache iterator if needed (avoid re-opening every get_batch)
        self._iio = iio
        self._frame_cache = None

    def __len__(self):
        if self._n_frames is None:
            # Force load to count
            self._populate_cache()
            return len(self._frame_cache)
        return self._n_frames

    def _populate_cache(self):
        if self._frame_cache is None:
            self._frame_cache = list(self._iio.imiter(self._path))
            self._n_frames = len(self._frame_cache)

    def get_batch(self, idxs):
        """Return frames at indices `idxs` as a wrapped ndarray [N, H, W, 3] uint8 RGB."""
        self._populate_cache()
        idxs_list = list(idxs)
        out = np.stack([np.asarray(self._frame_cache[i]) for i in idxs_list], axis=0)
        # Ensure RGB uint8
        if out.dtype != np.uint8:
            out = out.astype(np.uint8)
        return _NDArrayWrapper(out)

    def get_avg_fps(self):
        return self._fps

    def __getitem__(self, idx):
        self._populate_cache()
        if isinstance(idx, slice):
            idxs = list(range(*idx.indices(len(self._frame_cache))))
            return self.get_batch(idxs)
        return _NDArrayWrapper(np.asarray(self._frame_cache[idx]))

    def __iter__(self):
        self._populate_cache()
        for f in self._frame_cache:
            yield _NDArrayWrapper(np.asarray(f))


def cpu(idx=0):
    return "cpu"


class _Bridge:
    @staticmethod
    def set_bridge(name):
        pass  # decord supports tensor bridge to torch; we always return numpy


bridge = _Bridge()


# Common decord-style direct imports
ndarray = _NDArrayWrapper
