# sensit-ha-integration

Home Assistant integration for Sensit devices.
Version supported: 1.


## Installation

For now, only local mode is supported: raw data must be pushed to Home Assistant is a sensor called 'sensor.DEVICE_ID' with the ID of your Sensit.
To do, you can rely on callback (see below).

1. Add integration on your platform, either HACS or as a Custom component
2. Configure integration
3. Configure new Devices in the integration:
  1. Add device ID
  2. Choose Version (1, 2 or 3)
  3. Optionnaly, choose mode (only local is supported for now)



### Push data with HTTP/s callbacks

