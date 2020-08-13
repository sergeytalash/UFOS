from lib.plotter import *
import sys

if __name__ == "__main__":
    args = sys.argv[1:]
    if args:
        show_ozone_pairs = [i for i in args if i in ["1", "2"]]
    else:
        show_ozone_pairs = ["2"]
    Main(show_ozone_pairs).init_gui()
