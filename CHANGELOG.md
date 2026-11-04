## 1.0.1

- Update Spring and Guava, and remove unused Jackson and SnakeYAML libraries.
- Check downloaded databases before replacing existing files.
- Preserve unrelated files and restore previous files if a replacement fails.
- Allow setup to read the API key from an environment variable.
- Fix country-only lookups, field selection and `ignore_missing`.
- Reload cloud-provider data after its file is replaced.

Existing language options remain unchanged. This build requires Elasticsearch 8.13.3 and Java 21.
