# Version: 2.0
# Modified: 11.05.2025
# Author: Sergey Talash
try:
    from lib import plotter, core
except (ImportError, ModuleNotFoundError):
    import plotter, core

if __name__ == "__main__":
    plotter.Main("12")
