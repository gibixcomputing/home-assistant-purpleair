# PurpleAir Home Assistant Integration

This custom component leverages the PurpleAir API to pull in air quality
reports from sensors in your area. **You will need to register for a
free API key!**

The next version of this component will require at least Home Assistant
2022.3.

{% if not installed %}

## Registering for a PurpleAir API key

At the time of writing the process of registering and obtaining an API
read key is a manual process. Registration includes emailing
contact@purpleair.com and requesting a key and providing your first name
and last name. It's painless, but it does take a couple days, which is
why the component supports both legacy v0 and the new v1 API endpoints
to allow you to upgrade the component and migrate once you have your
key.

{% endif %}

{% set ver = version_installed.replace("v", "").replace(".","") | int %}

## What's New

{% if ver < 310 %}
### 3.1.0

Update EPA correction algorithm to 2021 data with a revised normal
formula and a new formula for PM2.5 concentrations > 343. See
[toolsresourceswebinar_purpleairsmoke_210519b.pdf][epa-smoke] for the
full details of the formula.

  - Contributed by Daniel Myers (@danielsmyers)

[epa-smoke]: https://www.epa.gov/sites/default/files/2021-05/documents/toolsresourceswebinar_purpleairsmoke_210519b.pdf


#### Bug Fixes

* Calculated AQI should never go "NaN" as it is now clamped to 0 and has
  a proper check for 0 vs None.
  Contribured by Daniel Myers (@danielsmyers)

Thanks for the contributions, Daniel!
{% endif %}
