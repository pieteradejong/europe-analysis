"""Integration tests for Eurostat data acquisition pipeline."""

from typing import Any
from unittest.mock import MagicMock, patch

from backend.src.data_acquisition.eurostat.acquirer import EurostatAcquirer
from backend.src.data_acquisition.eurostat.datasets import (
    DATASETS,
    DEMO_PJAN,
    STS_INPR_M,
    EurostatDatasetConfig,
)


class TestEurostatAcquirer:
    """Tests for EurostatAcquirer."""

    def test_init_with_dataset_id(self) -> None:
        """Test acquirer initialization with dataset ID."""
        acquirer = EurostatAcquirer(source="demo_pjan")

        assert acquirer.dataset_id == "demo_pjan"
        assert acquirer.config_obj == DEMO_PJAN

    def test_init_with_params(self) -> None:
        """Test acquirer initialization with parameters."""
        params = {"geo": "DE", "time": "2023"}
        acquirer = EurostatAcquirer(source="demo_pjan", params=params)

        assert acquirer.params == params

    def test_init_with_custom_base_url(self) -> None:
        """Test acquirer initialization with custom base URL."""
        acquirer = EurostatAcquirer(
            source="demo_pjan",
            base_url="https://custom.api.com/",
        )

        assert acquirer.client.base_url == "https://custom.api.com/"

    def test_init_unknown_dataset_uses_default_config(self) -> None:
        """Test that unknown dataset ID uses default config."""
        acquirer = EurostatAcquirer(source="unknown_dataset")

        assert acquirer.dataset_id == "unknown_dataset"
        assert isinstance(acquirer.config_obj, EurostatDatasetConfig)

    def test_validate_source_valid(self) -> None:
        """Test source validation with valid dataset ID."""
        acquirer = EurostatAcquirer(source="demo_pjan")

        assert acquirer.validate_source() is True

    def test_validate_source_empty(self) -> None:
        """Test source validation with empty dataset ID."""
        acquirer = EurostatAcquirer(source="", dataset_id="")

        assert acquirer.validate_source() is False

    @patch.object(EurostatAcquirer, "validate_source", return_value=False)
    def test_acquire_invalid_source(self, mock_validate: MagicMock) -> None:
        """Test acquire with invalid source returns error."""
        acquirer = EurostatAcquirer(source="")

        result = acquirer.acquire()

        assert result.success is False
        assert result.error is not None
        assert "Invalid dataset id" in result.error

    @patch("backend.src.data_acquisition.eurostat.acquirer.EurostatClient")
    def test_acquire_success(
        self,
        mock_client_class: MagicMock,
        mock_eurostat_jsonstat_response: dict[str, Any],
    ) -> None:
        """Test successful data acquisition."""
        # Setup mock
        mock_client = MagicMock()
        mock_client.get_dataset.return_value = mock_eurostat_jsonstat_response
        mock_client_class.return_value = mock_client

        acquirer = EurostatAcquirer(
            source="demo_pjan",
            params={"geo": "DE", "time": "2023"},
        )
        result = acquirer.acquire()

        assert result.success is True
        assert result.data is not None
        assert len(result.data) > 0
        assert result.records_count is not None
        assert result.records_count == len(result.data)

    @patch("backend.src.data_acquisition.eurostat.acquirer.EurostatClient")
    def test_acquire_data_mapping(
        self,
        mock_client_class: MagicMock,
        mock_eurostat_jsonstat_response: dict[str, Any],
    ) -> None:
        """Test that acquired data is correctly mapped."""
        mock_client = MagicMock()
        mock_client.get_dataset.return_value = mock_eurostat_jsonstat_response
        mock_client_class.return_value = mock_client

        acquirer = EurostatAcquirer(source="demo_pjan")
        result = acquirer.acquire()

        assert result.success is True
        assert result.data is not None

        # Check first record has expected fields
        first_record = result.data[0]
        assert "region_code" in first_record
        assert "region_name" in first_record
        assert "year" in first_record
        assert "gender" in first_record
        assert "age_group" in first_record
        assert "population" in first_record
        assert "_eurostat" in first_record

    @patch("backend.src.data_acquisition.eurostat.acquirer.EurostatClient")
    def test_acquire_region_mapping(
        self,
        mock_client_class: MagicMock,
        mock_eurostat_jsonstat_response: dict[str, Any],
    ) -> None:
        """Test that region codes and names are mapped correctly."""
        mock_client = MagicMock()
        mock_client.get_dataset.return_value = mock_eurostat_jsonstat_response
        mock_client_class.return_value = mock_client

        acquirer = EurostatAcquirer(source="demo_pjan")
        result = acquirer.acquire()
        assert result.data is not None

        # Find a German record
        de_record = next(r for r in result.data if r["region_code"] == "DE")
        assert de_record["region_name"] == "Germany"

        # Find a French record
        fr_record = next(r for r in result.data if r["region_code"] == "FR")
        assert fr_record["region_name"] == "France"

    @patch("backend.src.data_acquisition.eurostat.acquirer.EurostatClient")
    def test_acquire_time_normalization(
        self,
        mock_client_class: MagicMock,
        mock_eurostat_jsonstat_response: dict[str, Any],
    ) -> None:
        """Test that time values are normalized to years."""
        mock_client = MagicMock()
        mock_client.get_dataset.return_value = mock_eurostat_jsonstat_response
        mock_client_class.return_value = mock_client

        acquirer = EurostatAcquirer(source="demo_pjan")
        result = acquirer.acquire()
        assert result.data is not None

        # All year values should be integers
        years = {r["year"] for r in result.data}
        assert years == {2022, 2023}

    @patch("backend.src.data_acquisition.eurostat.acquirer.EurostatClient")
    def test_acquire_gender_normalization(
        self,
        mock_client_class: MagicMock,
        mock_eurostat_jsonstat_response: dict[str, Any],
    ) -> None:
        """Test that gender values are normalized."""
        mock_client = MagicMock()
        mock_client.get_dataset.return_value = mock_eurostat_jsonstat_response
        mock_client_class.return_value = mock_client

        acquirer = EurostatAcquirer(source="demo_pjan")
        result = acquirer.acquire()
        assert result.data is not None

        genders = {r["gender"] for r in result.data}
        assert genders == {"M", "F"}

    @patch("backend.src.data_acquisition.eurostat.acquirer.EurostatClient")
    def test_acquire_age_normalization(
        self,
        mock_client_class: MagicMock,
        mock_eurostat_jsonstat_response: dict[str, Any],
    ) -> None:
        """Test that age values are normalized."""
        mock_client = MagicMock()
        mock_client.get_dataset.return_value = mock_eurostat_jsonstat_response
        mock_client_class.return_value = mock_client

        acquirer = EurostatAcquirer(source="demo_pjan")
        result = acquirer.acquire()
        assert result.data is not None

        age_groups = {r["age_group"] for r in result.data}
        # Y0-4 -> "0-4", Y5-9 -> "5-9", Y_GE85 -> "85+"
        assert "0-4" in age_groups
        assert "5-9" in age_groups
        assert "85+" in age_groups

    @patch("backend.src.data_acquisition.eurostat.acquirer.EurostatClient")
    def test_acquire_metadata(
        self,
        mock_client_class: MagicMock,
        mock_eurostat_jsonstat_response: dict[str, Any],
    ) -> None:
        """Test that metadata is included in result."""
        mock_client = MagicMock()
        mock_client.get_dataset.return_value = mock_eurostat_jsonstat_response
        mock_client_class.return_value = mock_client

        acquirer = EurostatAcquirer(
            source="demo_pjan",
            params={"geo": "DE"},
        )
        result = acquirer.acquire()

        assert result.metadata is not None
        assert result.metadata["dataset_id"] == "demo_pjan"
        assert "params" in result.metadata
        assert "records_flattened" in result.metadata
        assert "records_mapped" in result.metadata

    @patch("backend.src.data_acquisition.eurostat.acquirer.EurostatClient")
    def test_acquire_merges_default_params(
        self,
        mock_client_class: MagicMock,
        mock_eurostat_jsonstat_response: dict[str, Any],
    ) -> None:
        """Test that default params from config are merged with caller params."""
        mock_client = MagicMock()
        mock_client.get_dataset.return_value = mock_eurostat_jsonstat_response
        mock_client_class.return_value = mock_client

        # STS_INPR_M has default params
        acquirer = EurostatAcquirer(
            source="sts_inpr_m",
            params={"geo": "DE"},  # Caller param
        )
        acquirer.acquire()

        # Check that both default and caller params were used
        call_params = mock_client.get_dataset.call_args.kwargs["params"]
        assert call_params["geo"] == "DE"  # Caller param
        assert call_params.get("unit") == "I15"  # Default param from STS_INPR_M

    @patch("backend.src.data_acquisition.eurostat.acquirer.EurostatClient")
    def test_acquire_caller_params_override_defaults(
        self,
        mock_client_class: MagicMock,
        mock_eurostat_jsonstat_response: dict[str, Any],
    ) -> None:
        """Test that caller params override default params."""
        mock_client = MagicMock()
        mock_client.get_dataset.return_value = mock_eurostat_jsonstat_response
        mock_client_class.return_value = mock_client

        # Override the default unit
        acquirer = EurostatAcquirer(
            source="sts_inpr_m",
            params={"unit": "I21"},  # Override default I15
        )
        acquirer.acquire()

        call_params = mock_client.get_dataset.call_args.kwargs["params"]
        assert call_params["unit"] == "I21"

    @patch("backend.src.data_acquisition.eurostat.acquirer.EurostatClient")
    def test_acquire_skips_null_values(self, mock_client_class: MagicMock) -> None:
        """Test that records with null values are skipped."""
        mock_client = MagicMock()
        mock_client.get_dataset.return_value = {
            "id": ["geo", "time"],
            "size": [2, 1],
            "dimension": {
                "geo": {
                    "category": {
                        "index": {"DE": 0, "FR": 1},
                        "label": {"DE": "Germany", "FR": "France"},
                    }
                },
                "time": {
                    "category": {
                        "index": {"2023": 0},
                        "label": {"2023": "2023"},
                    }
                },
            },
            "value": [83000000, None],  # FR has null value
        }
        mock_client_class.return_value = mock_client

        acquirer = EurostatAcquirer(source="demo_pjan")
        result = acquirer.acquire()

        assert result.success is True
        assert result.data is not None
        assert len(result.data) == 1
        assert result.data[0]["region_code"] == "DE"

    @patch("backend.src.data_acquisition.eurostat.acquirer.EurostatClient")
    def test_acquire_error_handling(self, mock_client_class: MagicMock) -> None:
        """Test error handling during acquisition."""
        mock_client = MagicMock()
        mock_client.get_dataset.side_effect = Exception("Network error")
        mock_client_class.return_value = mock_client

        acquirer = EurostatAcquirer(source="demo_pjan")
        result = acquirer.acquire()

        assert result.success is False
        assert result.error is not None
        assert "Network error" in result.error

    @patch("backend.src.data_acquisition.eurostat.acquirer.EurostatClient")
    def test_acquire_eurostat_metadata_in_records(
        self,
        mock_client_class: MagicMock,
        mock_eurostat_jsonstat_response: dict[str, Any],
    ) -> None:
        """Test that _eurostat metadata is included in each record."""
        mock_client = MagicMock()
        mock_client.get_dataset.return_value = mock_eurostat_jsonstat_response
        mock_client_class.return_value = mock_client

        acquirer = EurostatAcquirer(
            source="demo_pjan",
            params={"geo": "DE"},
        )
        result = acquirer.acquire()
        assert result.data is not None

        for record in result.data:
            assert "_eurostat" in record
            assert record["_eurostat"]["dataset_id"] == "demo_pjan"
            assert "params" in record["_eurostat"]


class TestEurostatDatasetConfigs:
    """Tests for Eurostat dataset configurations."""

    def test_demo_pjan_config(self) -> None:
        """Test DEMO_PJAN configuration."""
        assert DEMO_PJAN.dataset_id == "demo_pjan"
        assert DEMO_PJAN.dim_geo == "geo"
        assert DEMO_PJAN.dim_time == "time"
        assert DEMO_PJAN.dim_sex == "sex"
        assert DEMO_PJAN.dim_age == "age"

    def test_sts_inpr_m_config(self) -> None:
        """Test STS_INPR_M (industrial production) configuration."""
        assert STS_INPR_M.dataset_id == "sts_inpr_m"
        assert STS_INPR_M.dim_sex == ""  # Not applicable
        assert STS_INPR_M.dim_age == ""  # Not applicable
        assert STS_INPR_M.default_params is not None
        assert STS_INPR_M.default_params.get("unit") == "I15"

    def test_datasets_registry(self) -> None:
        """Test that all configured datasets are in registry."""
        assert "demo_pjan" in DATASETS
        assert "demo_fasec" in DATASETS
        assert "demo_magec" in DATASETS
        assert "migr_imm1ctz" in DATASETS
        assert "migr_emi1ctz" in DATASETS
        assert "sts_inpr_m" in DATASETS
