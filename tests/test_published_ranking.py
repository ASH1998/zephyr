import importlib.util
from pathlib import Path
import unittest


spec = importlib.util.spec_from_file_location('published_ranking',
    Path(__file__).resolve().parents[1]/'scripts/check-published-sedan-ranking.py')
benchmark = importlib.util.module_from_spec(spec)
spec.loader.exec_module(benchmark)


class PublishedRankingTests(unittest.TestCase):
    def test_selection_excludes_unavailable_and_normalizes_mixed_units(self):
        keys = list(benchmark.WIDTHS)
        lines = [','.join(['Run', *keys])]
        for run, key, value in ((1, 'Vehicle_Length', 0), (2, 'Vehicle_Length', 35),
                                (3, 'Vehicle_Pitch', .4), (4, 'Vehicle_Width', 60),
                                (5, 'Vehicle_Height', 80), (6, 'Hood_Angle', 50),
                                (7, 'Vehicle_Length', 1)):
            values = dict.fromkeys(keys, 0); values[key] = value
            lines.append(','.join(map(str, [run, *values.values()])))
        chosen = benchmark.select_cases('\n'.join(lines), [1, 2, 3, 4, 5, 6])
        self.assertEqual([r['run'] for r in chosen], [1, 2, 3, 4, 5])
        self.assertAlmostEqual(chosen[2]['normalizedDistance'], .2)

    def test_reversed_and_tied_predictions_cannot_claim_ranking_agreement(self):
        rows = [{'run': i, 'publishedForceN': float(i), 'dragN': float(i)} for i in range(1, 6)]
        correct = benchmark.ranking(rows)
        self.assertEqual(correct['spearmanForceRankCorrelation'], 1)
        self.assertEqual(correct['concordantPairs'], 10)
        self.assertTrue(correct['allPairsAgree'])
        for row in rows: row['dragN'] = -row['publishedForceN']
        reverse = benchmark.ranking(rows)
        self.assertEqual(reverse['spearmanForceRankCorrelation'], -1)
        self.assertEqual(reverse['concordantPairs'], 0)
        for row in rows: row['dragN'] = 600.
        tied = benchmark.ranking(rows)
        self.assertIsNone(tied['spearmanForceRankCorrelation'])
        self.assertFalse(tied['allPairsAgree'])


if __name__ == '__main__': unittest.main()
