"""
Unit tests proving that FHIR search requests use proper URL parameter encoding
(via requests params=) rather than manual string concatenation.

Identifiers with reserved URL characters (&, ?, =, /, space) must be percent-encoded
in the query string so that Blaze receives the correct identifier value.
"""

import unittest
from unittest.mock import Mock, patch, call

from service.blaze_service import BlazeService


RESERVED_CHAR_IDENTIFIERS = [
    "&:2022:118485",
    "A&B",
    "abc?x=1",
    "a/b",
    "space value",
]


def _make_service(mock_session):
    with patch("service.blaze_service.requests.session") as mock_session_factory, \
         patch("service.blaze_service.setup_logger"), \
         patch("service.blaze_service.get_blaze_auth", return_value=("u", "p")), \
         patch("service.blaze_service.get_metrics_for_service"):
        mock_session_factory.return_value = mock_session
        return BlazeService(
            patient_service=Mock(),
            condition_service=Mock(),
            sample_service=Mock(),
            blaze_url="http://blaze:8080/fhir",
            sample_collection_repository=Mock(),
        )


class TestUrlEncodingIsResourcePresentInBlaze(unittest.TestCase):
    """is_resource_present_in_blaze must pass identifier via params=, not string concat."""

    def setUp(self):
        self.mock_session = Mock()
        self.service = _make_service(self.mock_session)

        mock_response = Mock()
        mock_response.json.return_value = {"total": 1}
        self.mock_session.get.return_value = mock_response

    def _assert_params_used(self, identifier: str, resource_type: str = "Specimen"):
        self.mock_session.get.reset_mock()
        result = self.service.is_resource_present_in_blaze(resource_type, identifier)

        self.assertTrue(result)
        self.mock_session.get.assert_called_once()
        _, kwargs = self.mock_session.get.call_args
        params = kwargs.get("params", {})
        self.assertEqual(params.get("identifier"), identifier,
                         f"identifier not passed via params= for {identifier!r}")
        self.assertEqual(params.get("_summary"), "count")
        url = kwargs.get("url", "")
        self.assertNotIn(identifier, url,
                         f"Raw identifier {identifier!r} found in URL — use params= instead")

    def test_ampersand_prefix(self):
        self._assert_params_used("&:2022:118485")

    def test_ampersand_mid_value(self):
        self._assert_params_used("A&B")

    def test_question_mark_and_equals(self):
        self._assert_params_used("abc?x=1")

    def test_slash_in_value(self):
        self._assert_params_used("a/b")

    def test_space_in_value(self):
        self._assert_params_used("space value")

    def test_plain_identifier_still_works(self):
        self._assert_params_used("plain-id-123")


class TestUrlEncodingGetResourceCountByIdentifier(unittest.TestCase):
    """get_resource_count_by_identifier must use params= and return the total."""

    def setUp(self):
        self.mock_session = Mock()
        self.service = _make_service(self.mock_session)

    def _setup_response(self, total: int):
        mock_response = Mock()
        mock_response.json.return_value = {"total": total}
        self.mock_session.get.return_value = mock_response

    def test_returns_correct_count(self):
        self._setup_response(9)
        count = self.service.get_resource_count_by_identifier("Specimen", "&:2022:118485")
        self.assertEqual(count, 9)

    def test_zero_total(self):
        self._setup_response(0)
        count = self.service.get_resource_count_by_identifier("Patient", "A&B")
        self.assertEqual(count, 0)

    def test_params_kwarg_used_for_all_reserved_identifiers(self):
        self._setup_response(1)
        for identifier in RESERVED_CHAR_IDENTIFIERS:
            self.mock_session.get.reset_mock()
            self.service.get_resource_count_by_identifier("Specimen", identifier)
            _, kwargs = self.mock_session.get.call_args
            params = kwargs.get("params", {})
            self.assertEqual(params.get("identifier"), identifier,
                             f"identifier not in params= for {identifier!r}")
            url = kwargs.get("url", "")
            self.assertNotIn(identifier, url,
                             f"Raw {identifier!r} in URL — use params=")


class TestUrlEncodingPatientHasCondition(unittest.TestCase):
    """patient_has_condition must use params= for both Patient lookup and Condition search."""

    def setUp(self):
        self.mock_session = Mock()
        self.service = _make_service(self.mock_session)

    def test_patient_lookup_uses_params(self):
        patient_response = Mock()
        patient_response.json.return_value = {
            "entry": [{"resource": {"id": "fhir-123"}}]
        }
        condition_response = Mock()
        condition_response.json.return_value = {"total": 0}
        self.mock_session.get.side_effect = [patient_response, condition_response]

        self.service.patient_has_condition("A&B", "C50.9")

        patient_call = self.mock_session.get.call_args_list[0]
        _, pkwargs = patient_call
        self.assertEqual(pkwargs.get("params", {}).get("identifier"), "A&B")
        patient_url = pkwargs.get("url", "")
        self.assertNotIn("A&B", patient_url)

    def test_condition_search_uses_params(self):
        patient_response = Mock()
        patient_response.json.return_value = {
            "entry": [{"resource": {"id": "fhir-456"}}]
        }
        condition_response = Mock()
        condition_response.json.return_value = {"total": 1}
        self.mock_session.get.side_effect = [patient_response, condition_response]

        result = self.service.patient_has_condition("plain-patient", "C50.9")

        self.assertTrue(result)
        condition_call = self.mock_session.get.call_args_list[1]
        _, ckwargs = condition_call
        params = ckwargs.get("params", {})
        self.assertIn("patient", params)
        self.assertIn("code", params)
        self.assertEqual(params["code"], "C50.9")


class TestUrlEncodingDeleteFhirResource(unittest.TestCase):
    """delete_fhir_resource must pass the search param value via params= not URL concat."""

    def setUp(self):
        self.mock_session = Mock()
        self.service = _make_service(self.mock_session)

    def test_identifier_with_ampersand_uses_params(self):
        get_response = Mock()
        get_response.status_code = 200
        get_response.json.return_value = {"entry": []}
        self.mock_session.get.return_value = get_response

        self.service.delete_fhir_resource("Specimen", "&:2022:118485")

        _, kwargs = self.mock_session.get.call_args
        params = kwargs.get("params", {})
        self.assertEqual(params.get("identifier"), "&:2022:118485")
        self.assertNotIn("&:2022:118485", kwargs.get("url", ""))


if __name__ == "__main__":
    unittest.main()