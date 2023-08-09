import unittest

from pyfakefs.fake_filesystem_unittest import patchfs

from model.sample import Sample
from persistence.sample_xml_repository import SampleXMLRepository


class TestSampleXMLRepository(unittest.TestCase):
    sample = '<STS>' \
             '<diagnosisMaterial number="136043" sampleId="&amp;:2032:136043" year="2032">' \
             '<diagnosis>C509</diagnosis>' \
             '</diagnosisMaterial>' \
             '</STS>'

    wrong_diagnosis = '<STS>' \
                      '<diagnosisMaterial number="136043" sampleId="&amp;:2032:136043" year="2032">' \
                      '<diagnosis>wrong</diagnosis>' \
                      '</diagnosisMaterial>' \
                      '</STS>'

    samples = '<STS>' \
              '<diagnosisMaterial number="136043" sampleId="&amp;:2032:136043" year="2032">' \
              '<diagnosis>C508</diagnosis>' \
              '</diagnosisMaterial>' \
              '<diagnosisMaterial number="136044" sampleId="&amp;:2032:136043" year="2032">' \
              '<diagnosis>C501</diagnosis>' \
              '</diagnosisMaterial>' \
              '</STS>'

    content = '<patient id="9999">{sample}</patient>'

    dir_path = "/mock_dir/"

    @patchfs
    def test_get_all_one_sample_ok(self, fake_fs):
        fake_fs.create_file(self.dir_path + "mock_file.xml", contents=self.content
                            .format(sample=self.content))
        for sample in SampleXMLRepository("/mock_dir/").get_all():
            self.assertIsInstance(sample, Sample)
            self.assertEqual("&amp;:2032:136043", sample.identifier)
            self.assertEqual(sample.donor_id, "9999")

    @patchfs
    def test_get_all_two_samples_ok(self, fake_fs):
        fake_fs.create_file(self.dir_path + "mock_file.xml", contents=self.content
                            .format(sample=self.samples))
        for sample in SampleXMLRepository("/mock_dir/").get_all():
            self.assertIsInstance(sample, Sample)
            self.assertEqual("&amp;:2032:136043", sample.identifier)
