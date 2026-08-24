"""Tests for config parsers."""
import os
import tempfile
from mcs_cvor.parsers.config_parser import (
    parse_ini_file, parse_sys_file, parse_lda_file, detect_and_parse
)


def test_parse_ini_file():
    content = "[CVOR]\nFREQ=113.8\nMORSE=WAT\n"
    with tempfile.NamedTemporaryFile(mode="w", suffix=".ini", delete=False) as f:
        f.write(content)
        path = f.name
    try:
        result = parse_ini_file(path)
        assert "CVOR" in result
        assert result["CVOR"]["freq"] == "113.8"
        assert result["CVOR"]["morse"] == "WAT"
    finally:
        os.unlink(path)


def test_parse_sys_file():
    content = "[NETWORK]\nIP=192.168.1.1\nMASK=255.255.255.0\n[CVOR]\nFREQ=115.2\n"
    with tempfile.NamedTemporaryFile(mode="w", suffix=".sys", delete=False) as f:
        f.write(content)
        path = f.name
    try:
        result = parse_sys_file(path)
        assert "NETWORK" in result
        assert result["NETWORK"]["IP"] == "192.168.1.1"
        assert result["CVOR"]["FREQ"] == "115.2"
    finally:
        os.unlink(path)


def test_parse_sys_file_no_section():
    content = "KEY=VALUE\nFOO=BAR\n"
    with tempfile.NamedTemporaryFile(mode="w", suffix=".sys", delete=False) as f:
        f.write(content)
        path = f.name
    try:
        result = parse_sys_file(path)
        assert result["DEFAULT"]["KEY"] == "VALUE"
    finally:
        os.unlink(path)


def test_parse_lda_file():
    content = "FREQ:5:113.8\nMORSE:3:WAT\nSTATUS:6:ACTIVE\n"
    with tempfile.NamedTemporaryFile(mode="w", suffix=".lda", delete=False) as f:
        f.write(content)
        path = f.name
    try:
        result = parse_lda_file(path)
        assert result["FREQ"] == "113.8"
        assert result["MORSE"] == "WAT"
        assert result["STATUS"] == "ACTIVE"
    finally:
        os.unlink(path)


def test_detect_and_parse_ini():
    content = "[SECTION]\nKEY=VALUE\n"
    with tempfile.NamedTemporaryFile(mode="w", suffix=".ini", delete=False) as f:
        f.write(content)
        path = f.name
    try:
        result = detect_and_parse(path)
        assert "SECTION" in result
    finally:
        os.unlink(path)


def test_detect_and_parse_lda():
    content = "TAG:3:val\n"
    with tempfile.NamedTemporaryFile(mode="w", suffix=".lda", delete=False) as f:
        f.write(content)
        path = f.name
    try:
        result = detect_and_parse(path)
        assert result["TAG"] == "val"
    finally:
        os.unlink(path)
