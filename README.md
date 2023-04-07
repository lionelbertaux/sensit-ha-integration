# sensit-ha-integration

Home Assistant integration for Sensit devices.

Sensors supported:
- Temperature sensor
- Battery sensor



## Installation

For now, only local mode is supported: raw data must be pushed to Home Assistant is a sensor called 'sensor.DEVICE_ID' with the ID of your Sensit.
To do, you can rely on callback (see below).

1. Add integration on your platform:
  1. With HACS (advised): follow the [initial configuration](https://hacs.xyz/docs/configuration/basic/) and add this GitHub repository as Custom repository (HACS, Integrations, dots top-right of page).
  2. Manually: copy files in custom_components/sensit folder on your Home assistant instance in the config folder, with the same path custom_components/sensit
2. Home assistant must be restarted after installation.
4. On the integration page of home assistent, click Add integration
5. Select Sensit integration.
6. Configure the new Sensit in the integration:
  1. Add device ID
  2. Choose a unique name for your sensit (can be the same as ID)
  3. Choose Version (1, 2 or 3)
  4. Optionnaly, choose mode (only local is supported for now).
6. Repeat from 4 of you want to do more sensits.



### Push data with HTTP/s callbacks

1. Create a Long-lived access token in home assistant
  1. Go to your profile.
  2. Click on 'Create token' at the bottom of page.
3. Connect to the Sigfox backend
3. Go to Callback page of the device type with sensits
4. Create new Custom Callback:
  1. Select Data uplink
  2. Channel URL
  3. URL pattern  https://HOST:PORT/api/states/sensor.{device}
  4. Mode POST
  5. Check send SNi
  6. Add a 'authorization' header with value 'Bearer YOUR_TOKEN'
  7. Set application/json as Content type.
  8. Set data.

Data can be customized, for the integration, we will only need the raw data pushed to sensor.deviceID
Data example:
```json
{
"state": "{data}", "attributes": {"friendly_name": "Sensit raw data", "version": "v2", "id": "{device}"}
}
```

More details on Home Assistant HTTP Sensors in the [documentation](https://www.home-assistant.io/integrations/http/#sensor).
