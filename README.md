The `purpleair` custom component for Home Assistant integrates real-time
air quality sensor information from the public [PurpleAir][1] sensor
network. Available sensor information, such as Particulate Matter 2.5
(PM2.5) and the calculated NowCast Air Quality Index values are exposed
as sensors connected to the PurpleAir sensor.


# Minimum Required Home Assistant Version: **2021.11.5**
This release has been tested on **2021.11.5**. There is no guarantee of
backwards compatibility. The next major version of this component will
require **2022.03**.


# Important upgrade information for 3.0

Version 3.0 changes the underlying API method to use the new API
endpoints provided by the new [PurpleAir v1 API][3]. These new endpoints
requires free registration and an API Read Key to work. To support this
transition, the component will support the legacy "v0" API while you
register for access to the new API. Please note that there will be
notifications that you need to address the PurpleAir sensors you have
registered, immediate action is not required and they will continue to
work until you complete the upgrade process.


## Registering for a PurpleAir API key

At the time of writing the process of registering and obtaining an API
read key is a manual process. Registration includes emailing
contact@purpleair.com and requesting a key and providing your first name
and last name. It's painless, but it does take a couple days, which is
why the component supports both legacy v0 and the new v1 API endpoints
to allow you to upgrade the component and migrate once you have your
key.

As pointed out in the [current v0 API documentation][4]:

> **NOTICE**: PurpleAir is migrating all users to our new API at
> https://api.purpleair.com.
> 
> Please email contact@purpleair.com to get a key to use it and you
> should know that we will be preventing access to the current url’s at
> www.purpleair.com/data.json and www.purpleair.com/json soon.


## Upgrading your legacy sensors to v1 sensors

Once you have your API keys from PurpleAir you will receive two keys, a
READ key and a WRITE key. For this component, you only need to
copy the **READ** key. The component will test the key you provide to
ensure the correct key is provided and will error out of the key is
invalid for any reason.

When upgrading your first sensor, the component will ask for the API
READ key and prefill the other values as it can. You should be able to
simply provide the READ key and can continue. It will reconfigure the
sensor to use the new API and will continue to work as if nothing
changed.

If you have multiple PurpleAir sensors registered with this component,
you will need to repeat the process for each one. However, it will check
to see if it can be upgraded without additional information and allow
you to continue without providing the key! If it cannot, it will prompt
you to provide the necessary information before continuing. I tried my
best to make this as painless a process as possible and have tested all
possible combinations I could think of.


# Air Quality Index (AQI) calculations

The Air Quality Index calculation provided by this integration is based
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


## Upgrading

If you've previously installed this component, please remove the
`custom_components/purpleair` directory completely and copy the latest
in cleanly. Some files have been removed and moved around and it hasn't
been tested with old files left around.


### Advanced Installation using Git

This is an advanced installation process to make the upgrade process a
lot easier to handle, but requires knowledge of Git. This is the process
I use to install the component and has worked flawlessly.

<details>
<summary>Click this text to view advanced installation using Git</summary>


#### If you use Git to track changes to `config`

If you are already tracking your changes `config` in Git you can add
this as a submodule:

```shell
$ cd /config
$ pwd
/config
$ git submodule init
$ git submodule add https://gitlab.com/gibwar/home-assistant-purpleair.git modules/purpleair
Cloning into '/config/modules/purpleair'...
... clone output ...
```


#### If you are not using Git to track your `config` changes

If you aren't using Git to track your config, you can check it out
normally and follow the directions below.

```shell
$ cd /config
$ pwd
/config
$ git checkout https://gitlab.com/gibwar/home-assistant-purpleair.git modules/purpleair
Cloning into '/config/modules/purpleair'...
... clone output ...
```


#### Link your Git repository to `custom_components`
Now to link the Git repository to `custom_components` you can follow
these steps:

```shell
$ cd /config

# if you don't have a custom_components directory already:
$ mkdir custom_components

# create the symlink from the git module repository to custom_components
$ ln -sv modules/purpleair/custom_components/purpleair custom_components/purpleair
'custom_components/purpleair' -> 'modules/purpleair/custom_components/purpleair'
$ ls -l custom_components/purpleair
lrwxrwxrwx 1 gibwar gibwar 45 Mar 26 12:48 custom_components/purpleair -> modules/purpleair/custom_components/purpleair
```


#### Check out the version you want using tags
From here, the default `main` branch is always a stable version but I
prefer to check out the tag to know what version I am using and can
choose how I upgrade. Regardless, `git status` should always output what
version you are on. All commits on `main` always have a tag starting
from `v2.0.0`. Regardless, the upgrade process should always follow this
process.

```shell
$ cd /config/modules/purpleair
$ git fetch
... git fetch output ...

# to see available versions run git tag -l
$ git tag -l
v2.0.0
v2.0.1
v2.0.2
v2.1.0

# specify the tag to check out
$ git checkout v2.1.0
Note: checking out 'v2.1.0'.
... extra output, depending on your Git configuration ...
  HEAD is now at a8fc51a Release 2.1.0
```


#### Alternative: track the `main` branch
If you just want to track the `main` branch and not worry about tags,
the following will work, but you should check your current version and
check the [CHANGELOG.md](./CHANGELOG.md) file for information on
upgrades and potential breaking changes.

```shell
$ cd /config/modules/purpleair
$ git log -1
commit 8a049c459918ebea0e586c323c544d3143ffe403 (HEAD -> main, tag: v2.0.2)
... other information ...
# note the "tag: v2.0.2" above, that is the version you are on
$ git pull
... git output ...
$ git log -1
commit a8fc51ae76cc610f9a027bfdc74236ff1ec9be03 (HEAD -> main, tag: v2.1.0, origin/main, origin/HEAD)
... git log output ...
# you are now on v2.1.0
```
</details>


# Adding a PurpleAir sensor

To find a sensor to integrate:

1. Look at the [PurpleAir Map][2].
2. Find and click on the station you want to use.
3. Click on *Get this Widget* and then click on *Download Data*.
4. In the new window, copy the URL of the Sensor Download Tool page.\
   It should look like https://www.purpleair.com/sensorlist?key=J213GUNST1PDPSTO&show=107440.
5. Paste the URL in an editor, eg. Notepad in Windows, TextEdit on MacOS.
6. Go to Home Assistant and go to the Integrations Page and add the
   PurpleAir integration.\
   [![Open your Home Assistant instance and start setting up a new
   integration.](https://my.home-assistant.io/badges/config_flow_start.svg)](https://my.home-assistant.io/redirect/config_flow_start/?domain=purpleair)
7. If required, paste your API READ key. This field will be hidden if
   you are adding another sensor.
8. Copy the value for `show` from the URL and paste it in the *PurpleAir
   station ID* field. In the example above, this is `107440`.
9. If this is a public sensor, click *Submit* as the station read key
   (which is different than your API READ key) is not necessary.
10. If this is a hidden sensor but you got it from the map, copy the
    value for `key` and paste it in the *Station Read Key* field. In the
    example above this would be `J213GUNST1PDPSTO`.\
    If you did not get this from the map, this value should be in the
    email when you registered your device.

**NOTE**: the integration will test the correct keys are given and will
error out if it cannot read the sensor data. If there is a problem,
double check your API READ key (if needed), the Station ID (`show`
value), and the station read key (`key` value) are correct. If the
sensor is public, you do not need to provide the sensor read key.

After adding the integration, you will have a new PurpleAir Sensor
device and one Air Quality Index sensor. It may take a couple minutes
for the device information to populate, but the sensor is set up and
ready to go!


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
| Air Quality Index (Raw) | The original, uncorrected AQI calculation provided by older versions.                          |
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

| Attribute Name           | Description                                                          |
|--------------------------|----------------------------------------------------------------------|
| `device_location`†       | Location of the sensor, "outside" or "inside".                       |
| `last_seen`              | Date and time the sensor last reported.                              |
| `adc`                    | ADC voltage.                                                         |
| `rssi`                   | WiFi signal strength                                                 |
| `uptime`                 | How long the sensor as been running, in seconds.                     |
| `latitude`, `longitude`‡ | Physical location of the sensor in the world.                        |
| `confidence`*†           | Confidence value given to the sensor data. Available on all sensors. |
| `status`                 | EPA AQI calculation status.                                          |

__*__ See [Sensor Confidence](#sensor-confidence).\
__†__ Available in legacy sensors (v0) only. These will be added back as
diagnostic sensors in the v4 release of this component.\
__‡__ Latitude and longitude were removed in v2.1.0 and will be added as
a diagnostic sensor in the v4 release of this component.


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

See [CHANGELOG.md](CHANGELOG.md) for up to date release information.

[1]: https://www.purpleair.com "PurpleAir: Real-time air quality
monitoring everyone can use"

[2]: http://www.purpleair.com/map?mylocation "PurpleAir Map"

[3]: https://api.purpleair.com/ "PurpleAir API"

[4]: https://docs.google.com/document/d/15ijz94dXJ-YAZLi9iZ_RaBwrZ4KtYeCy08goGBwnbCU/edit "Legacy v0 PurpleAir API documentation (Google Doc)"
