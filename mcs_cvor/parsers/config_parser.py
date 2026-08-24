"""Config file parsers for .ini, .sys and .LDA formats."""
import configparser
import os
import re
from typing import Dict, Any


def parse_ini_file(filepath: str) -> Dict[str, Any]:
    """Parse a standard .ini file."""
    parser = configparser.ConfigParser()
    parser.read(filepath)
    result = {}
    for section in parser.sections():
        result[section] = dict(parser[section])
    return result


def parse_sys_file(filepath: str) -> Dict[str, Any]:
    """Parse KEY=VALUE .sys file with optional [SECTION] headers."""
    result = {}
    current_section = "DEFAULT"
    section_pattern = re.compile(r"^\[(.+)\]$")
    kv_pattern = re.compile(r"^([A-Za-z0-9_\-]+)\s*=\s*(.*)$")

    with open(filepath, "r", encoding="utf-8", errors="replace") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or line.startswith(";"):
                continue
            m = section_pattern.match(line)
            if m:
                current_section = m.group(1)
                if current_section not in result:
                    result[current_section] = {}
                continue
            m = kv_pattern.match(line)
            if m:
                if current_section not in result:
                    result[current_section] = {}
                result[current_section][m.group(1)] = m.group(2).strip()
    return result


def parse_lda_file(filepath: str) -> Dict[str, Any]:
    """Parse Thales LDA format: TAG:length:value records."""
    result = {}
    lda_pattern = re.compile(r"^([A-Z0-9_]+):(\d+):(.*)$")

    with open(filepath, "r", encoding="utf-8", errors="replace") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            m = lda_pattern.match(line)
            if m:
                tag = m.group(1)
                expected_len = int(m.group(2))
                value = m.group(3)[:expected_len]
                result[tag] = value
    return result


def detect_and_parse(filepath: str) -> Dict[str, Any]:
    """Auto-detect file type from extension and parse."""
    ext = os.path.splitext(filepath)[1].lower()
    if ext == ".ini":
        return parse_ini_file(filepath)
    elif ext in (".sys", ".cfg"):
        return parse_sys_file(filepath)
    elif ext == ".lda":
        return parse_lda_file(filepath)
    else:
        # Try each parser
        for parser in (parse_ini_file, parse_sys_file, parse_lda_file):
            try:
                return parser(filepath)
            except Exception:
                continue
        return {}
