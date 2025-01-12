# PurpleAir Home Assistant Integration

This custom component leverages the PurpleAir API to pull in air quality
reports from sensors in your area. **You will need to register for a
free API key!**

This release has been tested on **2024.12.5**. There is no guarantee of
backwards compatibility. The next major version of this component will
require a newer version of Home Assistant. I generally require the
previous month's `.0` version when I work on this component.

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

{% set inst_ver = version_installed.replace("v", "").replace(".","") | int %}
{% set next_ver = version_available.replace("v", "").replace(".","") | int %}

## What's New

{% if inst_ver < 322 %}{# > #}
### 3.2.2

Quick fix to address deprecations in HA 2025.1.

{% endif %}

{% if inst_ver < 321 %}{# > #}
### 3.2.1

Quick fix to clear up problems during device creation/update in Home
Assistant 2023.8.

{% endif %}

{% if inst_ver < 320 %}{# > #}
### 3.2.0

Fix reported warning "using native unit of measurement 'AQI' which is
not a valid unit for the device class ('aqi')".

{% endif %}

{% if inst_ver < 320 and next_ver >= 320 %}{# > #}
#### IMPORTANT

You will receive a new (mostly silent) warning log indicating the
statistics for the sensors are no longer valid since it has switched
from 'AQI' to None. This is an easy fix, you can go to the [developer
tools/statistics][dev-stats] page and click the "Fix Me" link on the AQI
sensors at the top of the list and select the option describing "Update
the unit of the historic statistic values from 'AQI' to '', without
converting.". This only needs to be done once per AQI sensor provided by
this add-on. Alternatively you can select the "clear statistics" option
to wipe historical data and start over.

{% endif %}

{% if inst_ver < 311 %}{# > #}
### 3.1.1

Fixes an issue when adding sensors.

  - Contributed by Michael Borohovski (@borski1). Thanks Michael!

README updates contributed by Erick Hitter (@ethitter). Thanks Erick!

{% endif %}

{% if inst_ver < 310 %}{# > #}
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
