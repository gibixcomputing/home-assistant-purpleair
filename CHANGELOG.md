# Releases

## 2.1.0

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
