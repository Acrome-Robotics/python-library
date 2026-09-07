# Overview

This library provides easy-to-use Python modules for interacting with Acrome Robotics products.

# Modules 

## **Controller Module**

This module provides a hardware abstraction layer between Acrome Controller board and application code and enables users to develop their own applications without hassle of implementing a communication protocol or struggling with any timing requirements. This module also provides safety limitations for Acrome Robotics products and users don't have to worry about any mechanical or electrical limit of the products while working on their application code.

The controller module provides 6 different classes  for interacting with 5 different products and the Acrome Controller board itself.

- ## Controller Class

    This class provides an interface with the Acrome Controller board. For basic communication checks and configuration via 4 different methods.

    * #### `__init__(self, portname="/dev/serial0", baudrate=115200)`
        
        **`Return:`** *None*
        
        This is the constructor of the Controller class.
        
        `portname` argument is the serial/COM port of the host computer which is connected to the Acrome Controller board. Since the board is designed with Raspberry Pi in mind, default portname is `/dev/serial0` to provide out of the box support for Raspberry Pi.

        `baudrate` argument must not be changed by the user since different baudrates are not supported by the hardware, yet.

    * #### `ping(self)` 

        **`Return:`** *boolean*

        This method provides a basic ping functionality between the board and the host computer as the name suggests. If the communication succeeded method returns true, otherwise false.
    * #### `reboot(self)`

        **`Return:`** *None*
        
        This method immediately reboots the Acrome Controller board when called.

    * #### `enter_bootloader(self)`

        **`Return:`** *None*
        
        When this method called, the Acrome Controller board boots into the embedded bootloader to provide a firmware update. When bootloader activated, the board does not respond to any other command rather than specific instruction for bootloader operation.
    * #### `get_latest_version(self)`

        **`Return:`** *string / None*

        This method returns the latest firmware version available as a string with a 'v' suffix. (Example: v0.1.0)

    * #### `fetch_fw_binary(self, version='')`

        **`Return:`** *boolean*

        This method fetches the given firmware version from related repository. When version argument is not given by the user, fetches the latest version available. User must provide version information as a string and with a suffix 'v'. Returns True on success.

    * #### `update_fw_binary(self, baudrate=115200)`

        **`Return:`** *None*

        This method initiates the firmware download procedure. This procedure must not be interrupted since it may brick the hardware. Baudrate argument can be selected between 1200 and 115200. Update procedure with low baudrates may take some time. Serial port in use on the host computer must support EVEN parity to work properly. When used with a Raspberry Pi, ttyAMA0 should be used as the serial port since ttyS0 does not support parity bits.

    * #### `get_board_info(self)`

        **`Return:`** *dict*

        This method returns a dictionary that contains information about the underlaying hardware configuration and status. Since gathering that information interrupts the any other operation at the hardware, calling it in any control loop might affect the system performance and should be avoided.


- ## OneDOF Class

    This class provides an interface with the OneDOF via Acrome Controller.

    * #### `__init__(self, portname="/dev/serial0", baudrate=115200)`
        
        **`Return:`** *None*
        
        This is the constructor of the OneDOF class. Please refer to the Controller class constructor for argument descriptions.

    * #### `set_speed(self, speed)`

        **`Return:`** *None*

        This method provides an interface to set speed of the OneDOF motor. Available range is from -1000 to 1000.

    * #### `enable(self)`
        **`Return:`** *None*

        This method enables the power stage of the OneDOF motor and should be called prior to setting speed.

    * #### `reset_encoder_mt(self)`
        **`Return:`** *None*

        This method resets the encoder of the DC motor on the OneDOF.

    * #### `reset_encoder_shaft(self)`
        **`Return:`** *None*

        This method resets the encoder on the shaft of OneDOF.

    * #### `update(self)`
        **`Return:`** *None*

        This method syncronizes the variables both on host computer and hardware side. Should be called prior to read of any attribute or called after any write/set operation to make latest values available immediately.

    * #### `motor_enc`

        This attribute returns the current value of encoder on the DC motor.
        
        > **Note:** This attribute might be always 0 according to your product configuration.

    * #### `shaft_enc`

        This attribute returns the current value of encoder on the OneDOF shaft.
        
    * #### `imu`
        
        This attribute returns the current roll, pitch and yaw values in degrees in a form of Python list.

        > **Note:** This attribute is only available on the products that shipped with an BNO055 Absolute Orientation Sensor. Products with MPU6050 IMU is not supported yet and will return 0.

- ## BallBeam Class

    This class provides an interface with Ball and Beam via Acrome Controller.

    * #### `__init__(self, portname="/dev/serial0", baudrate=115200)`
        
        **`Return:`** *None*
        
        This is the constructor of the BallBeam class. Please refer to the Controller class constructor for argument descriptions.
    * #### `set_servo(self, servo)`

        **`Return:`** *None*

        This method provides an interface to set angle of the servo motor on Ball and Beam. Available range is from -1000 to 1000.

    * #### `update(self)`
        **`Return:`** *None*

        This method syncronizes the variables both on host computer and hardware side. Should be called prior to read of any attribute or called after any write/set operation to make latest values available immediately.

    * #### `position`

        This attribute returns the current value of the ball position on the beam.

- ## BallBalancingTable Class

    This class provides an interface with Ball Balancing Table via Acrome Controller.

    * #### `__init__(self, portname="/dev/serial0", baudrate=115200)`
        
        **`Return:`** *None*
        
        This is the constructor of the BallBalancingTable class. Please refer to the Controller class constructor for argument descriptions.
    * #### `set_servo(self, x, y)`

        **`Return:`** *None*

        This method provides an interface to set angles of the servo motors on Ball Balancing Table. Available range is from -1000 to 1000 for each axis.

    * #### `update(self)`
        **`Return:`** *None*

        This method syncronizes the variables both on host computer and hardware side. Should be called prior to read of any attribute or called after any write/set operation to make latest values available immediately.

    * #### `position`

        This attribute returns a list that contains the current coordinates (x, y) of the ball position on the touch screen.

- ## Delta Class

    This class provides an interface with Delta Robot via Acrome Controller.

    * #### `__init__(self, portname="/dev/serial0", baudrate=115200)`
        
        **`Return:`** *None*
        
        This is the constructor of the Delta class. Please refer to the Controller class constructor for argument descriptions.
    * #### `set_motors(self, motors)`

        **`Return:`** *None*

        This method provides an interface to set angles of the motors on Delta Robot. Available range is from 310 to 810 for each motor. `motors` argument must be a list of 3 integers.
    
    * #### `pick(self, magnet)`
        **`Return:`** *None*

        This method controls the state of electromagnet which is attached to the Delta Robot. `magnet` argument is a boolean and when set to `True`, enables the magnet to pick the coin and when set to `False`, disables the magnet to release it.

    * #### `update(self)`
        **`Return:`** *None*

        This method syncronizes the variables both on host computer and hardware side. Should be called prior to read of any attribute or called after any write/set operation to make latest values available immediately.

    * #### `position`

        This attribute returns a list of 3 integers that contains the current values of the motor positions. List elements are Motor 1 Position, Motor 2 Position, and Motor 3 Position respectively.

- ## Stewart, StewartEncoder and StewartEncoderHR Classes

    These classes provides an interface with Stewart Platforms via Acrome Controller.
    While Stewart Platform uses analog position feedback, StewartEncoder and StewartEncoderHR uses incremental encoders for position feedback. StewartEncoder and StewartEncoderHR only differs in communication structure. StewartEncoderHR provides 32 bits wide encoder resolution while StewartEncoder provides only 16 bits. 16 bits encoder resolution is enough for 4" and 8" versions of Stewart Platforms and no need to bloat serial communication with extra 16 bits of data per encoder.

    * #### `__init__(self, portname="/dev/serial0", baudrate=115200)`
        
        **`Return:`** *None*
        
        This is the constructor of the Stewart class. Please refer to the Controller class constructor for argument descriptions.

    * #### `enable(self)`
        **`Return:`** *None*

        This method enables the power stages of the Stewart Platform motors and should be called prior to setting speed.
    
    * #### `reset_encoder(self, motor_num=[1,2,3,4,5,6])`
        **`Return:`** *None*

        This method resets the encoder of the motor at the given index to 0.

        > **Note:** This method is only available in StewartEncoder and StewartEncoderHR classes.

    * #### `set_motors(self, motors)`

        **`Return:`** *None*

        This method provides an interface to set speeds of the motors on Stewart Platform. Available range is from -1000 to 1000 for each motor. `motors` argument must be a list of 6 integers.

    * #### `set_digital_pins(self, pins)`

        **`Return:`** *None*

        This method sets the digital pin outputs of the Acrome Controller. `pins` argument is a single byte where each bit corresponds to one digital pin. Defaults to 0 when not set.

        > **Note:** This method is only available in the Stewart class and requires Acrome Controller firmware that expects the digital pin field in the Stewart packet.

    * #### `update(self)`
        **`Return:`** *None*

        This method syncronizes the variables both on host computer and hardware side. Should be called prior to read of any attribute or called after any write/set operation to make latest values available immediately.

    * #### `position`

        This attribute returns a list of 6 integers that contains the current values of the motor positions. List elements are ordered as starting from Motor 1 Position to Motor 6 Position.

    * #### `imu`
        
        This attribute returns the current roll, pitch and yaw values in degrees in a form of Python list.

        > **Note:** This attribute is only available on the products that shipped with an BNO055 Absolute Orientation Sensor. Products with MPU6050 IMU is not supported yet and will return 0.