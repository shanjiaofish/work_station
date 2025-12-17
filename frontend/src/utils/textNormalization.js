/**
 * Text normalization utility for search functionality
 * Normalizes text by:
 * - Applying Unicode NFKC normalization (handles CJK full-width/half-width characters)
 * - Converting to lowercase
 * - Removing spaces and tabs
 * - Removing punctuation (., !, ?, etc.)
 * - Removing hyphens and underscores (-, _)
 * - Removing parentheses and brackets ((), [], {})
 */

/**
 * Normalizes text for search comparison
 * @param {string} text - The text to normalize
 * @returns {string} - The normalized text
 */
export function normalizeText(text) {
  if (!text || typeof text !== 'string') {
    return '';
  }

  // Step 1: Apply Unicode NFKC normalization
  // This handles CJK full-width/half-width characters and other Unicode equivalents
  let normalized = text.normalize('NFKC');

  // Step 2: Convert to lowercase for case-insensitive matching
  normalized = normalized.toLowerCase();

  // Step 3: Remove all special characters, spaces, and tabs
  // This regex removes:
  // - All whitespace characters (\s includes spaces, tabs, newlines, etc.)
  // - Punctuation: . , ! ? ; : ' "
  // - Hyphens and underscores: - _
  // - Parentheses and brackets: ( ) [ ] { }
  // - Other common special characters
  normalized = normalized.replace(/[\s\.\,\!\?\;\:\'\"\-\_\(\)\[\]\{\}]/g, '');

  return normalized;
}

/**
 * Checks if a search query matches a target text after normalization
 * @param {string} query - The search query
 * @param {string} target - The target text to search in
 * @returns {boolean} - True if the normalized query is found in the normalized target
 */
export function normalizedIncludes(query, target) {
  const normalizedQuery = normalizeText(query);
  const normalizedTarget = normalizeText(target);

  return normalizedTarget.includes(normalizedQuery);
}
