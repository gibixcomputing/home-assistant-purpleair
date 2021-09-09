The `purpleair` custom component for Home Assistant integrates real-time
air quality sensor information from the public [PurpleAir][1] sensor
network. Available sensor information, such as Particulate Matter 2.5
(PM2.5) and the calculated NowCast Air Quality Index values are exposed
as sensors connected to the PurpleAir sensor.


# Important upgrade information for 2.0

If you are upgrading this sensor from a prior 1.x version, there is a
breaking change you need to be aware of. Home Assistant has depreciated
the built-in `air_quality` sensor type and recommends integrations
provide the information via separate basic sensors. The AQI sensor will
be upgraded, but the old particulate matter values in the old air
quality sensor will be removed during the upgrade.

If you had any automations, template sensors, or otherwise directly
relied on the data provided by the `air_quality` sensor you will need to
update those after upgrading. All of the information previously provided
is still available as _disabled_ sensors attached to the PurpleAir
Sensor device. Please go to the device configuration and enable any
additional sensors you may need.


# Air Quality Index (AQI) calculations

The Air Quality Index calcuation provided by this integration is based
off the EPA's recommended adjustments for PurpleAir sensor data, formed
during the 2020 wildfire season.

The new AQI calculation in 2.0 uses this new formula and requires a full
hour of historical data to provide the greatest accuracy. For the sake
of convenience, the AQI sensor will begin showing data immediately. The
AQI sensor exposes a new attribute, `status` that shows the status of
the calculations: "calculating (x mins left)" will show how long until
the reading is accurate, and "stable" when there is a full hour of
historical data to work with.

Additionally, the calculated AQI uses a rolling history, and may not be
exactly accurate compared to the EPA AirNow map or the PurpleAir map
with appropriate adjustments. This is due to the AQI calculation using a
bucket for calculating the value for a given hour, rather than a live,
updating value.


# Installation

Simply copy the `custom_components/purpleair` directory to your Home
Assistant configuration's `custom_components` directory (you may need to
create it), restart Home Assistant, and add the integration via the UI.

To find a sensor to integrate:

1. Look at the [PurpleAir Map][2].
2. Find and click an available station.
3. In the station pop up, right click on "Get This Widget" and copy the
   link. (Copy Link Location, et al.)
4. Go to Home Assistant and go to the Integrations Page.
5. Add the PurpleAir integration.
6. Paste the link and finish.

After adding the integration, you will have a new PurpleAir Sensor
device and one Air Quality Index sensor. It may take a couple minutes
for the device information to populate, but the sensor is set up and
ready to go!


# Upgrading

To upgrade, stop Home Assistant, and follow the directions above for
installing the integration. If you are upgrading from 1.x, please make
note of the sensor changes mentioned above.


# Using the PurpleAir integration

Sensor data on PurpleAir is only updated every two minutes, and to be
nice, this integration will batch its updates every five minutes. This
integration can work with indoor and outdoor air quality sensors, and
currently only work with the cloud API. Local API integration is in the
works and will be available in a future version.

By default, only the calculated air quality index sensor is available by
default. However, 7 other sensors are available for your use and can be
enabled by hand if desired. All data that was originally provided by the
`air_quality` aggregate sensor are now separate sensors.


## Available Sensors

| Sensor Name             | Description                                                                                    |
|-------------------------|------------------------------------------------------------------------------------------------|
| Air Quality Index       | The current air quality index, calculated using the EPA's NowCast PurpleAir corrected formula. |
| Air Quailty Index (Raw) | The original, uncorrected AQI calculation provided by older versions.                          |
| PM 1.0                  | Real-time Particulate Matter 1.0 data from the last report.                                    |
| PM 2.5                  | Real-time Particulate Matter 2.5 data from the last report.                                    |
| PM 10                   | Real-time Particulate Matter 10 data from the last report.                                     |
| Humidity                | Corrected relative humidity reported by the sensor.                                            |
| Temperature             | Corrected temperature reported by the sensor.                                                  |
| Pressure                | Current pressure reported by the sensor, in hPa.                                               |


### Extra Attributes

The primary air quality sensor also exposes some additional sensor data
as attributes on the sensor itself and can be viewed under the
"Attributes" drop down in the sensor view or in the developer dashboard.

| Attribute Name          | Description                                                          |
|-------------------------|----------------------------------------------------------------------|
| `device_location`       | Location of the sensor, "outside" or "inside".                       |
| `adc`                   | ADC voltage.                                                         |
| `rssi`                  | Wifi signal strength                                                 |
| `uptime`                | How long the sensor as been running, in seconds.                     |
| `latitude`, `longitude` | Physical location of the sensor in the world.                        |
| `confidence`*           | Confidence value given to the sensor data. Available on all sensors. |
| `status`                | EPA AQI calculation status.                                          |


#### Sensor Confidence

All sensors have a `confidence` attribute associated with the state.
This value is intended to give an indication on the health of the sensor
and the calculations provided.

Confidence States:

| Confidence               | Description                                                                             |
|--------------------------|-----------------------------------------------------------------------------------------|
| `good`                   | Data is reliable and falls in expected ranges.                                          |
| `questionable`           | Channel data from A and B are divergent (could be a sensor going bad)                   |
| `single`                 | Data is from the device itself, and not a laser sensor (ex: temperature, humidity, etc) |
| `single - a channel bad` | Particulate Matter sensor data is only coming from the B channel                        |
| `single - b channel bad` | Particulate Matter sensor data is only coming from the A channel                        |
| `invalid`                | The sensor data is invalid and falls outside expected ranges                            |


# License

This component is licensed under the MIT license, so feel free to copy,
enhance, and redistribute as you see fit.


# Notes

This started as a single-day project and has grown to much more. This
should work with both public and private (hidden) cloud devices. I just
recently purchased an ourdoor sensor, so local API support may come in
the near future.


# Releases


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

[1]: https://www.purpleair.com "PurpleAir: Real-time air quality
monitoring everyone can use"

[2]: http://www.purpleair.com/map?mylocation "PurpleAir Map"

