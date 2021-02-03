# Tetick ITU
Tetick ITU is a course scheduler based on tetick. See below for more information about tetick.

# Tetick ITU Status
- Currently must course addition, section constraints do not work.
- Capacity check constraint is working.
- Instructors are not shown properly.
- Some courses do not have valid hours/days, they are ignored.
- For development purposes, a cache mode is added to scraper. Cache mode might make it look like the database is updated when it is not.

# tetick

tetick is a course scheduler which takes course data and constructs possible schedules.

a version of it should be on [tetick.xyz](http://tetick.xyz).

## getting started

`make` should run the scrapers, minify and inline the file into www/index.html.

after getting the data, `make` is not needed during development. index.html in the directory will work.

the code is ~600 lines of annotated, vanilla JS. highly operational core is around 100 lines.
you can start reading from [compute()](https://github.com/duck2/tetick/blob/master/main.js#L385).

## features

- uses time intervals instead of table cells
- consistent collision checking for user-defined time blocks
- reasonably fast until ~1M combinations
- small- <100KB gzipped with all course data

## non-features

- won't rate schedules for "lunch" or "block courses together"

see [data_spec.md](https://github.com/duck2/tetick/blob/master/data_spec.md) for interpreting scrapers' output.
