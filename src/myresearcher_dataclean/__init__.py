"""Deterministic RAW-to-CLEAN baseline for MyResearcher Collector records."""

from .pipeline import CLEANING_VERSION, CleaningResult, clean_records

__all__ = ["CLEANING_VERSION", "CleaningResult", "clean_records"]
