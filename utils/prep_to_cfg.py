#!/usr/bin/env python3
import sys
import re

def main():
    if len(sys.argv) < 2:
        print("Usage: python prep_to_cfg.py <input_file> [output_file]")
        sys.exit(1)

    input_file = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else None

    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            content = f.read()

        # Remove spaces around = signs
        cleaned_content = re.sub(r'\s*=\s*', '=', content)

        if output_file:
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(cleaned_content)
            print(f"Successfully processed {input_file} -> {output_file}")
        else:
            print(cleaned_content)

    except FileNotFoundError:
        print(f"Error: Input file '{input_file}' not found")
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
