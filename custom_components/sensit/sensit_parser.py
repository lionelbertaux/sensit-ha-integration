import logging
import json

_LOGGER = logging.getLogger(__name__)

class SensitParser:
    def __init__(self):
        pass

    def convert_battery(self, data):
        """ Battery converter for sensit v1
        """
        ret = 0
        if len(data) <= 2:
            ret = int(data, 16) * 0.02
        return ret

    def convert_temperature(self, data):
        """ Temperature converter for sensit v1
        """
        ret = 0
        if len(data) <= 2:
            ret = int(data, 16)
            if ret > 128:
                ret = ret - 256
            ret = (ret + 46) /2
        return ret

    def parse_v1(self, data, name="sensit"):
        """ Parser for sensit v1
        Arguments:
            - data: String to be parsed
            - name: Name of device, used to display a clear log
        b0-b2: Mode (0: off, 1: temperature, 2: movement, 3: full)
        b3-b5: Period (0: 24h, 1: 12h, 2: 6h, 3: 2h, 4: 1h, 5: 30m, 6: 15m, 7: 10m)
        b6: Forced message
        b7: Button message
        B1: Battery (voltage = 0.02 * value)
        B2: Sent battery (voltage during previous frame)
        B3: Temperature = (value + 46)/2
        0-6 bytes: DATA, depend on the mode
            - Temperature: 6 values, each on 1 byte
            - Movement: 1 byte for value, 3 bytes for config
            - Full: 1 byte min temp, 1 byte max temp, 1 byte movement value
        """
        out_data = {}
        try:
            logging.debug(f"Sensit {name} v1 data parsing {data}")
            # First byte must be split in bits
            b = "{:08b}".format(int(data[:2], base=16))
            # print("First byte: " + str(b))
            out_data.update({"mode":  int(b[2:])})
            out_data.update({"period": int(b[len(b)-5:len(b)-3], 2)})
            out_data.update({"forced": int(b[1])})
            out_data.update({"button": int(b[0])})
            # Following bytes are battery levels and temperature
            out_data.update({"battery": self.convert_battery(data[2:4])})
    
            # Push battery update to sensor
            out_data.update({"sent_battery": self.convert_battery(data[4:6])})
            out_data.update({"temperature": self.convert_temperature(data[6:8])})
            # Next bytes depends on mode
            mode = out_data.get("mode")
            out_data.update({"values": []})
            # Not all modes are implemented for now (to implement: Motion, Sound, All and Off)
            if mode == 1:
                logging.info(f"Sensit {name} mode temperature")
                for i in range(8, len(data), 2):
                    out_data["values"].append(self.convert_temperature(data[i:i+2]))
                logging.info(f"-- Data parsed: {str(out_data)}")
                return out_data
            elif mode == 2:
                logging.info(f"Sensit {name} mode Motion")
                # TODO Implement Motion mode message parsing for v1
                return {"body": {"message": "Motion message not implemented yet"}, "statusCode": 500}
            elif mode == 3:
                logging.info(f"Sensit {name}  mode All")
                # TODO Implement All mode message parsing for v1
                return {"body": {"message": "All message not implemented yet"}, "statusCode": 500}
            else:
                logging.info(f"Sensit {name} Off")
                # TODO Implement Off mode message parsing for v1
                return {"body": {"message": "Off notification not implemented yet"}, "statusCode": 500}
        except Exception as e:
            logging.error(f"Sensit {name} Error during data parsing {str(data)}. Error: {str(e.args)}")
            return {"body": {"message": "Error " + str(e.args)}, "statusCode": 500}
        return {"body": {"message": "Nothing was processed"}, "statusCode": 500}


    def parse_v2(data, name="sensit"):
        """ Parser for sensit v2
        Arguments:
            - data: String to be parsed
            - name: Name of device, used to display a clear log
        Bytes are read from left to right, the first byte being the most significant one
        Bits are numbered the other way, from the LSB to the MSB. Bit 0 being the LSB & bit 7 the
        MSB of the said byte
        Example : received frame is A9670d19 .
        First byte is 0xA9 or 0b10101001 .
        Or {bit 7}{bit 6}{bit 5}{bit 4}{bit 3}{bit 2}{bit 1}{bit 0}
    
        --B0
        b0-b2: Mode (0: Button, 1: Temperature, 2: Light, 3: Door, 4: Move, 5: Reed switch)
        b3-b4: Timeframe (0: 10m, 1: 1h, 2: 6h, 3: 24h)
        b5-b6: Type (0: regular no alert, 1: Button, 2: Alert, 3: New mode)
        b7: Battery MSB 
        -- B1
        This do not seem to match the computation done in code ....
        It appears that the value are reversed....
        b0-b3: Temperature MSB
        b4-b7: Battery LSB
        Data bytes
        -- B2
        Classic mode (excludes Light & Door regular frames)
        b0-b5: Temperature LSB
        b6: Reed Switch state
        b7: Unused
        Lightmode, value = {final multiplier} * {value} * 0.01              
        b0-b5: value
        b6-b7: Multiplier (for final multiplier, 0: 1, 1: 8, 2: 64, 3: 2014)
        Door mode: byte not used
        -- B3
        Button Frames
        b0-b3: Minor version
        b4-b7: Major version
        Temperaturemode:
        b0-b7: Humidity = value* 0.5
        Other mode, bytes contains the number of alerts
    
        Conversion details:
        For battery: MSB LSB and {value} * 0.05 * 2.7
        For Temperature MSB: ({value} * 6.4) - 20
        OR Temperature mSB LSB ({value} - 200) / 8 
        """
        out_data = {}
        try:
            logging.debug(f"Sensit {name} v2 data parsing {data}")
            # Byte 0 - Mode, period, ...
            b = "{:08b}".format(int(data[:2], base=16))
            logging.info(b)
            out_data.update({"mode":  int(b[8-1-2:8-0], 2)})
            out_data.update({"period": int(b[8-1-4:8-3], 2)})
            out_data.update({"type": int(b[8-1-6:8-5], 2)})
            out_data.update({"battery_msb": b[8-1-7:8-7]})
    
            # Byte 1 - Temperature MSB and Battery LSB
            b = "{:08b}".format(int(data[2:4], base=16))
            # Temperature and Battery seem to be mis-documented
            out_data.update({"temperature_msb": b[8-1-7:8-4]})
            out_data.update({"battery_lsb": b[8-1-3:8-0]})
    
            # Byte 2 - Data depends on mode
            b = "{:08b}".format(int(data[4:6], base=16))
            if out_data.get("mode") == 2:
                # Light mode
                logging.warning("Light mode, not implemented")
                # TODO implement Light mode data parsing
            elif out_data.get("mode") == 3:
                # Door mode, nothing in here
                pass
            else:
                # Parse byte
                out_data.update({"temperature_lsb": b[8-1-5:8-0]})
                out_data.update({"switch_state": b[8-1-6:8-6]})
                # b7 is not used
    
            # Byte 3 - Version or Data
            b = "{:08b}".format(int(data[6:8], base=16))
            if out_data.get("mode") == 0:
                # Mode button
                # TODO Add switch button sensor ? 
                logger.warning(f"Sensit {name} - Button mode not implemented")
                pass
                # TODO Implement parsing of software version ? 
            elif out_data.get("mode") == 1:
                out_data.update({"humidity": int(b[8-1-7:8-0], 2)*0.5})
            else:
                # Other modes, data is the number of alerts
                # TODO Implement Alert count ? 
                pass
    
            # Data has been parsed, we can compute Temperature and battery      
            battery = int(out_data.get("battery_msb") + out_data.get("battery_lsb"), 2) * 0.05 * 2.7
            out_data.update({"battery": battery})
            
            if out_data.get("temperature_lsb"):
                temperature = (int(out_data.get("temperature_msb") + out_data.get("temperature_lsb"), 2) - 200) / 8
                out_data.update({"temperature": temperature})
            else:
                temperature = (int(out_data.get("temperature_msb"), 2) * 6.4 )- 20 
                out_data.update({"temperature_from_msb": temperature})
                # Temperature computation with MSB only is not accurate
            return (out_data)
        except Exception as e:
            logging.error(f"Sensit {name} Error during data parsing {str(data)}. Error: {str(e.args)}")
            return {"body": {"message": "Error " + str(e.args)}, "statusCode": 500}



