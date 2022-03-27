# Releases

Current release: **3.0.0**


## 3.0.0

**MINIMUM HA VERSION**: 2021.11.5

This adds support for the new PurpleAir v1 API and the usage of API READ
keys. Existing sensors will be treated as "v0 legacy" sensors and will
be marked as needing an upgrade via the reauthentication flow. This
gives you time to request an API key from PurpleAir (see README) and
upgrade when you are able. **The next major version (4.0.0) will remove
support for legacy sensors!** The upgrade flow has been designed to be
as painless and helpful as possible.


### Major Changes

* Added PurpleAir API v1 support. New sensors can only be added with v1
  support. No legacy sensors can be added.

* Minimum required HA version bumped from 2021.08 to 2021.11.5.

* Updated config flow logic to allow for upgrading legacy sensors in
  place and validating and sharing API key configuration.


### Minor Changes

* Config entries now track which API version they use.

* Fixed a bug where incorrect data was stored in the config entry
  `hidden` field.

* Fixed a bug where all HA sensors were activated by default, rather
  than only enabling the AQI sensor and making the rest optional.

* Updated error messages to be more useful and descriptive.


### Code Changes

* Added namespaces to the API to help with future upgrades and made the
  HA related logic as API agnostic as possible.

* Utilized the `pytest-homeassistant-custom-component` python package to
  bring the code standards up to date. Linted using `pyupgrade
  --py38-plus`, `isort`, `black --fast`, `codespell`, `flake8`,
  `pylint`, and `mypy` with compatible settings. Added GitLab CI.


### Related issues

Fixes #6, #16, #17, #18, #19, #20, #21, #22.


## 2.1.0

**MINIMUM HA VERSION**: 2021.08

Fixes a couple annoyances:

* Fixes an error when removing a sensor.

* Removes latitude/longitude attributes from the primary sensor
  configuration. It added them to the map which wasn't necessary and
  doesn't really add any value at the moment. Once 2021.11 is released
  with the new `entity_category` attribute, a generic sensor for the
  state of the PA sensor could be added, which may make it easier to
  report sensor issues instead of the log and sensor attributes.

### Related issues

Fixes #11, #12, #14, #15.


## 2.0.2

Support Python 3.8 typings. `deque` and `dict` are not subscriptable
when creating a type alias.


## 2.0.1

Adds support for Home Assistant instances running on 2021.8 (or earlier,
prior versions are untested). This is due to new device classes and
`native_unit_of_measurement` being added in Home Assistant 2021.9.



## 2.0.0

This is a breaking change! The `air_quality` sensor in Home Assistant is
deprecated and therefore has been removed. The new logic of adding
additional disabled sensors replace the lost information and can be
enabled if desired.


### Major Changes

* The only sensor enabled by default is the Air Quality Index sensor.
  This sensor calculates the AQI using the EPA correction formula which
  better represents the air quality during wildfire smoke scenarios
  using a rolling 1 hour average.

* Exposes, and corrects, additional data points provided by the sensor,
  including temperature, humidity, and pressure.

* Uses the DataUpdateCoordinator to better integrate with Home
  Assistant, allowing for disabling of polling and handles adding and
  removing sensors without overloading the API.

* Adds a device entity to Home Assistant to contain all of the new
  sensors.


### Minor Changes

* Adds additional data on the primary sensor, such as the RSSI value for
  Wifi reception.

* Exposes the confidence of data provided, helping bring visibility to
  failing sensors.

* Adds the status of the corrected AQI value. Data is calculated
  immediately, but the attribute displays how long until a full hour of
  data is obtained and the AQI value is most accurate.

* Marks the AQI sensor unavailable if the data is over two hours old.

* Adds warning to the logs to indicate when a sensor is sending old data
  or if a dual laser sensor has faulty readings.



### Related Issues

Fixes #2, #5, and #7.


## 1.1.0

* Adds support for private hidden sensors and indoor sensors. Fixes #3
  and #4.


## 1.0.0

Initial release (after versioning)
