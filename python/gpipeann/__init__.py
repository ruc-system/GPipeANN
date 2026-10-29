"""NumPy interface for GPipeANN GPU-SSD approximate nearest neighbor search."""

from .index import IndexGPipeANN, GPipeANNError

__all__ = ["IndexGPipeANN", "GPipeANNError"]
__version__ = "0.1.0"
