#!/usr/bin/env python3
"""
Скрипт для удаления записей из JSON файла с пустым третьим полем в downloaded_text.
"""

import json
import sys
import os
import argparse

from configs import cfg


def cfg_print():
    print("Global variables imported from config.cfg:")
    for name, value in cfg.__dict__.items():
        if not name.startswith('__') and not callable(value) and not isinstance(value, type) and not name in sys.modules:
                print(f"{name}={value}")

def main():
    cfg_print()
    
    

if __name__ == "__main__":
    main()
