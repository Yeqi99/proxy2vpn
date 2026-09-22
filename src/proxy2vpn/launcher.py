"""Shortcut entry point: launch on demand while preserving startup choice."""
import argparse
from pathlib import Path
from .shortcuts import open_console


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--home',type=Path,default=Path.home()/'.proxy2vpn')
    args=parser.parse_args()
    open_console(args.home)


if __name__=='__main__': main()
