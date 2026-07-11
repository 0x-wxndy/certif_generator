#!/usr/bin/env python3
"""Command-line certificate generator."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from certificate_generator import generate_certificate, generate_from_csv, list_templates


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate certificates from templates")
    parser.add_argument("--list", action="store_true", help="List available templates")
    parser.add_argument("--template", "-t", help="Template ID")
    parser.add_argument("--data", "-d", help="JSON file or inline JSON with field values")
    parser.add_argument("--csv", help="CSV file for batch generation")
    parser.add_argument("--output", "-o", help="Output file path")
    args = parser.parse_args()

    if args.list:
        for template in list_templates():
            fields = ", ".join(f.id for f in template.fields)
            print(f"{template.id:22}  {template.name_ar}  [{template.output_format}]  fields: {fields}")
        return

    if not args.template:
        parser.error("--template is required (or use --list)")

    if args.csv:
        outputs = generate_from_csv(args.template, args.csv)
        print(f"Generated {len(outputs)} files in {outputs[0].parent}")
        for path in outputs:
            print(path)
        return

    if not args.data:
        parser.error("--data is required for single generation")

    data_path = Path(args.data)
    if data_path.exists():
        payload = json.loads(data_path.read_text(encoding="utf-8"))
    else:
        payload = json.loads(args.data)

    output = generate_certificate(args.template, payload, Path(args.output) if args.output else None)
    print(output)


if __name__ == "__main__":
    main()
