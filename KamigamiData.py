class KamigamiRobot:
    """
    Class that contains information specific to the Kamigami Robot
    """
    MAIN_SERVICE_UUID = '708a96f0f2004e2f96f09bc43c3a31c8'
    WRITE_UUID  = '708a96f1f2004e2f96f09bc43c3a31c8'
    NOTIFY_UUID = '708a96f2f2004e2f96f09bc43c3a31C8'

    class Identifiers:
        LIGHT_PACKET = 2
        MOTOR_PACKET = 3
        IR_PACKET = 5
        TEST_MODE = 16
        STICKY_PACKET_SET = 12
        UNIFIED_PACKET = 15
        SHUTDOWN = 1

    class Settings:
        IMU_NOTIFY_PER_SECOND = 20
        LUX_NOTIFY_PER_SECOND = 10
        MOTOR_SETTINGS_NOTIFY_PER_SECOND = 0


class KamigamiByteFormatter:
    """
    Formats packets for outgoing data to the Kamigami Robot.
    """

    # Get a motor packet to send to the robot.
    @staticmethod
    def get_sendable_motor_packet(left, right):
        if left >= 64 or left <= -64:
            raise ValueError("Please specify a left speed correctly.  Speeds must be between -63 and 63, inclusive.")
        if right >= 64 or right <= -64:
            raise ValueError("Please specify a right speed correctly.  Speeds must be between -63 and 63, inclusive.")
        return KamigamiByteFormatter.convert_params_to_message([KamigamiRobot.Identifiers.MOTOR_PACKET, left, right])

    # Get a light packet to send to the robot
    @staticmethod
    def get_sendable_light_packet(color=None, r=None, g=None, b=None):
        print(r,g,b)
        if color is not None and (r is not None or g is not None or b is not None):
            raise ValueError("Choose a color or specifying r, g, b values")
        if r is not None and g is not None and b is not None:
            if 0 > r or 255 < r:
                raise ValueError("Please specify a red color value correctly.  Color must be between 0 and 255, inclusive.")
            if 0 > g or 255 < g:
                raise ValueError("Please specify a green color value correctly.  Color must be between 0 and 255, inclusive.")
            if 0 > b or 255 < b:
                raise ValueError("Please specify a blue color value correctly.  Color must be between 0 and 255, inclusive.")
            data_ = KamigamiByteFormatter.convert_params_to_message([KamigamiRobot.Identifiers.LIGHT_PACKET, r, g, b])
            return data_
        if color.lower() == "red":
            # return "02ff0000".decode('hex')
            return KamigamiByteFormatter.get_sendable_light_packet(r=255, g=0, b=0)
        elif color.lower() == "blue":
            # return "020000ff".decode('hex')
            return KamigamiByteFormatter.get_sendable_light_packet(r=0, g=0, b=255)
        elif color.lower() == "green":
            # return "0200ff00".decode('hex')
            return KamigamiByteFormatter.get_sendable_light_packet(r=0, g=255, b=0)
        elif color.lower() == "yellow":
            return KamigamiByteFormatter.get_sendable_light_packet(r=255, g=255, b=0)
        elif color.lower() == "purple":
            return KamigamiByteFormatter.get_sendable_light_packet(r=127, g=0, b=127)
        elif color.lower() == "cyan":
            return KamigamiByteFormatter.get_sendable_light_packet(r=0, g=255, b=255)
        else:
            raise ValueError("Bad Arguments")

    @staticmethod
    def get_sendable_ir_packet():
        choice_values = ['\x08\x02', '\x07\x02', '\x06\x02']
        return KamigamiByteFormatter.convert_to_byte(KamigamiRobot.Identifiers.IR_PACKET) + choice(choice_values)

    @staticmethod
    def get_sendable_shutdown():
        return KamigamiByteFormatter.convert_to_byte(KamigamiRobot.Identifiers.SHUTDOWN)

    @staticmethod
    def get_sendable_testmode(speed):
        """
        Puts the robot in "Robot Test Mode,"
        which will test the lights and motors.
        Motor speed is the parameter.
        """
        return KamigamiByteFormatter.convert_params_to_message([KamigamiRobot.Identifiers.TEST_MODE, 1, speed, speed])

    @staticmethod
    def convert_to_byte(value):
        """
        Method used to format integers into
        bytes for the robot to interpret.
        """
        # Negative number
        if str(value)[0] == "-":
            return hex(256+int(value))[2:].decode('hex')
        # Single digit hex value (positive)
        if len(hex(value)) == 3:
            return ("0"+hex(value)[2:]).decode('hex')
        else:
            # Double digit hex value
            return hex(value)[2:].decode('hex')

    @staticmethod
    def convert_params_to_message(values):
        """
        For each index in the list parameter, convert it to 
        bytes that the robot can interpret.  Then, join
        the command together.
        """
        return "".join(map(KamigamiByteFormatter.convert_to_byte, values))

    @staticmethod
    def get_unified_packet(motor_power=None, lights=None):
        """
        Arguments as follows:
        motor_power: Two element list or tuple containing the left speed
                     in index 0 and right speed in index 1.
        lights: Three element list or tuple containing r,g,b in positions
                0, 1, and 2 respectively.
        """
        cmd = [KamigamiRobot.Identifiers.UNIFIED_PACKET] + [0x0 for i in range(19)] # Set all positions to 0x0
        if motor_power is not None:
            if not all(map(lambda speed: 0 <= speed <= 63, motor_power)):
                raise AttributeError("Motor parameters out of 0 to 63 (inclusive) range.")
            cmd[1] |= 0x01
            cmd[2] = motor_power[0]
            cmd[3] = motor_power[1]
        if lights is not None:
            if not all(map(lambda color: 0 <= color <= 255, lights)):
                raise AttributeError("Specified light values are out of range.")
            cmd[1] |= 0x04
            cmd[6] = lights[0]
            cmd[7] = lights[1]
            cmd[8] = lights[2]

        return KamigamiByteFormatter.convert_params_to_message(cmd)
