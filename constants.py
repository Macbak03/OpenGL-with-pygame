from dataclasses import dataclass, field
# Window dimensions
@dataclass
class WindowSize:
    x: int = 1920
    y: int = 1080

# Global default window size instance
default_window_size = WindowSize()

# Alias for direct import as windowSize
windowSize = default_window_size

