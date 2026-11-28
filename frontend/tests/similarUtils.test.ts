import test from 'node:test';
import assert from 'node:assert/strict';
import {
  extractTopicOptions,
  filterSimilarProblems,
  getPlatformItems,
  normalizeDifficultyBucket,
  toggleSolvedUrl,
} from '../src/features/workspace/similarUtils.ts';
import type { SimilarProblemsResponse } from '../src/types/similar.ts';

const SAMPLE_DATA: SimilarProblemsResponse = {
  codeforces: [
    {
      title: 'Cheap Travel',
      platform: 'codeforces',
      url: 'https://codeforces.com/problemset/problem/466/A',
      similarity_score: 88,
      difficulty: '1200',
      tags: ['implementation', 'math'],
      reason: 'Budget optimization.',
    },
    {
      title: 'Cut Ribbon',
      platform: 'codeforces',
      url: 'https://codeforces.com/problemset/problem/189/A',
      similarity_score: 84,
      difficulty: '1300',
      tags: ['dp', 'brute force'],
      reason: 'Unbounded count maximization.',
    },
    {
      title: 'Cut Ribbon',
      platform: 'codeforces',
      url: 'https://codeforces.com/problemset/problem/189/A',
      similarity_score: 84,
      difficulty: '1300',
      tags: ['dp', 'brute force'],
      reason: 'Duplicate URL should be deduped.',
    },
  ],
  codechef: [
    {
      title: 'Chef and Coins',
      platform: 'codechef',
      url: 'https://www.codechef.com/problems/CHCOINS',
      similarity_score: 79,
      difficulty: '1500',
      tags: ['math', 'dp'],
      reason: 'Divisibility and coins.',
    },
  ],
  leetcode: [],
};

test('getPlatformItems switches platforms and deduplicates by URL', () => {
  const cf = getPlatformItems(SAMPLE_DATA, 'codeforces');
  assert.equal(cf.length, 2);
  assert.equal(cf[0].title, 'Cheap Travel');

  const cc = getPlatformItems(SAMPLE_DATA, 'codechef');
  assert.equal(cc.length, 1);
  assert.equal(cc[0].title, 'Chef and Coins');

  const lc = getPlatformItems(SAMPLE_DATA, 'leetcode');
  assert.equal(lc.length, 0);
});

test('filterSimilarProblems filters by difficulty, topic, and hideSolved', () => {
  const cf = getPlatformItems(SAMPLE_DATA, 'codeforces');
  assert.equal(normalizeDifficultyBucket('1200'), 'easy');
  assert.equal(normalizeDifficultyBucket('1300'), 'medium');
  assert.equal(normalizeDifficultyBucket('1900'), 'hard');

  const easyOnly = filterSimilarProblems(cf, {
    difficulty: 'easy',
    topic: '',
    hideSolved: false,
    solvedUrls: new Set(),
  });
  assert.equal(easyOnly.length, 1);
  assert.equal(easyOnly[0].title, 'Cheap Travel');

  const dpOnly = filterSimilarProblems(cf, {
    difficulty: 'all',
    topic: 'dp',
    hideSolved: false,
    solvedUrls: new Set(),
  });
  assert.equal(dpOnly.length, 1);
  assert.equal(dpOnly[0].title, 'Cut Ribbon');

  let solved = new Set<string>();
  solved = toggleSolvedUrl(solved, 'https://codeforces.com/problemset/problem/466/A');
  const withoutSolved = filterSimilarProblems(cf, {
    difficulty: 'all',
    topic: '',
    hideSolved: true,
    solvedUrls: solved,
  });
  assert.equal(withoutSolved.length, 1);
  assert.equal(withoutSolved[0].title, 'Cut Ribbon');
});

test('extractTopicOptions returns sorted unique tags', () => {
  const cf = getPlatformItems(SAMPLE_DATA, 'codeforces');
  assert.deepEqual(extractTopicOptions(cf), ['brute force', 'dp', 'implementation', 'math']);
});
