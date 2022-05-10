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
