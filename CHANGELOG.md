# Changelog

## 1.0.0 -

- Subquery support
- CTE (Common Table Expressions) support
- PostgreSQL support
- Renamed constraint method `required_constraints` to `parameterized_constraints`
- Renamed Bifrost method `mocked` to `validation_only`
- All exceptions include a `ctx` property for debugging

## 0.3.0 - 7/15/23

- Autofix non-qualified column names
- Bugfix where aliases composed of multiple columns would not correctly resolve
- Allow customization of SQL dialect placeholder format
- Bugfix to allow forwards and backwards required conditions
- Add required whitespace to SQL grammars
- SQL pretty-printer should return everything on one line.
- Bugfix with Mysql prompt envelope mentioning sqlite

## 0.2.1 - 7/10/23

- Automated Github releases
- Add sdist and wheels to workflow artifacts

## 0.2.0 - 7/9/23

- Support for MySQL ~8.0
- Refactor sqlite helpers to be general
- Bugfix where disabling reconstruction resulted in an error
- Allow counting disallowed columns
- Bugfix api key not set when using openai completion method
- Generalize tests to handle multiple sql dialects

## 0.1.4 - 7/5/23

- Use an optional int instead of `math.inf` for an unrestricted SQL limit

## 0.1.3 - 7/4/23

- Docstring updates
- Improve test coverage

## 0.1.2 - 7/1/23

- Initial release
