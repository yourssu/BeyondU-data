"""Data cleaning and normalization utilities."""

import re

import pandas as pd


class DataCleaner:
    """Clean and normalize extracted Excel data."""

    def __init__(self, df: pd.DataFrame):
        self.df = df.copy()

    def clean(self) -> pd.DataFrame:
        """Run all cleaning steps and return cleaned DataFrame."""
        self._clean_program_type()
        self._clean_whitespace()
        self._normalize_gpa()
        self._forward_fill_merged_columns()
        self._remove_invalid_rows()
        return self.df

    def _clean_program_type(self) -> None:
        """Clean program type values."""
        if "program_type" in self.df.columns:
            self.df["program_type"] = self.df["program_type"].apply(
                lambda x: str(x).strip().replace("\n", "") if pd.notna(x) else x
            )

    def _clean_whitespace(self) -> None:
        """Remove extra whitespace from string columns."""
        for col in self.df.columns:
            if self.df[col].dtype == "object":
                self.df[col] = self.df[col].apply(
                    lambda x: " ".join(str(x).split()) if pd.notna(x) and str(x).strip() else x
                )

    def _normalize_gpa(self) -> None:
        """Normalize GPA values to consistent format."""
        if "min_gpa" in self.df.columns:
            self.df["min_gpa"] = self.df["min_gpa"].apply(self._parse_gpa)

    def _parse_gpa(self, value: str | None) -> str | None:
        """Parse GPA value to normalized format."""
        if value is None or pd.isna(value):
            return None

        value_str = str(value).strip()
        if not value_str:
            return None

        # Already in X.X/X.X format
        if re.match(r"^\d+\.?\d*/\d+\.?\d*$", value_str):
            return value_str

        # "3.0 이상" format
        match = re.search(r"(\d+\.?\d*)\s*이상", value_str)
        if match:
            return f"{match.group(1)}/4.5"

        # Just a number
        match = re.search(r"^(\d+\.?\d*)$", value_str)
        if match:
            return f"{match.group(1)}/4.5"

        # Return original if can't parse
        return value_str

    def _forward_fill_merged_columns(self) -> None:
        """Forward fill columns that typically have merged cells."""
        merge_columns = ["country", "region", "program_type", "institution"]
        for col in merge_columns:
            if col in self.df.columns:
                self.df[col] = self.df[col].ffill()

    def _remove_invalid_rows(self) -> None:
        """Remove rows without essential data."""
        essential_cols = ["name_kr", "country"]
        existing = [col for col in essential_cols if col in self.df.columns]

        if existing:
            # Remove rows where essential columns are all empty
            mask = self.df[existing].notna().any(axis=1)
            self.df = self.df[mask]

            # Remove summary rows
            if "name_kr" in self.df.columns:
                self.df = self.df[
                    ~self.df["name_kr"]
                    .astype(str)
                    .str.contains("합계|소계|총계|nan", case=False, na=False)
                ]

        self.df = self.df.reset_index(drop=True)
