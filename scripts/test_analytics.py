import unittest
import xml.etree.ElementTree as ET
from unittest.mock import patch

import analytics

class AnalyticsTests(unittest.TestCase):
    def test_forks_excluded_and_primary_languages_counted(self):
        rows = [
            {'fork': False, 'stargazers_count': 2, 'forks_count': 1, 'language': 'Python'},
            {'fork': False, 'stargazers_count': 3, 'forks_count': 2, 'language': None},
            {'fork': True, 'stargazers_count': 99, 'forks_count': 99, 'language': 'Java'},
        ]
        summary = analytics.summarize(rows)
        self.assertEqual((summary['repositories'], summary['stars'], summary['forks']), (2, 5, 3))
        self.assertEqual(summary['languages'], {'Python': 1})

    def test_svg_escapes_external_language_and_handles_empty_data(self):
        for languages in [{}, {'A&B <test>': 1}]:
            cards = analytics.render_cards({'repositories': 0, 'stars': 0, 'forks': 0, 'languages': analytics.Counter(languages)}, '2026-10-05')
            for svg in cards.values():
                ET.fromstring(svg)
            self.assertNotIn('<test>', cards['languages.svg'])

    def test_network_failure_keeps_existing_cards(self):
        with patch.object(analytics, 'fetch_repositories', side_effect=RuntimeError('API unavailable')), patch.object(analytics.Path, 'mkdir') as mkdir:
            with self.assertRaises(RuntimeError):
                analytics.main()
            mkdir.assert_not_called()

if __name__ == '__main__':
    unittest.main()
