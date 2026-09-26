class Telemetry:

    def __init__(
        self,
        time,
        altitude,
        latitude,
        longitude,
        velocity,
        temperature,
        pressure,
        wind_speed,
        wind_direction,
        acceleration,
        descent_rate,
        parachute_deployed
    ):

        self.time = float(time)
        self.altitude = float(altitude)

        self.latitude = float(latitude)
        self.longitude = float(longitude)

        self.velocity = float(velocity)

        self.temperature = float(temperature)
        self.pressure = float(pressure)

        self.wind_speed = float(wind_speed)
        self.wind_direction = float(wind_direction)

        self.acceleration = float(acceleration)
        self.descent_rate = float(descent_rate)

        self.parachute_deployed = bool(parachute_deployed)

    def to_dict(self):

        return {
            "time": self.time,
            "altitude": self.altitude,
            "latitude": self.latitude,
            "longitude": self.longitude,
            "velocity": self.velocity,
            "temperature": self.temperature,
            "pressure": self.pressure,
            "wind_speed": self.wind_speed,
            "wind_direction": self.wind_direction,
            "acceleration": self.acceleration,
            "descent_rate": self.descent_rate,
            "parachute_deployed": self.parachute_deployed
        }

    def display(self):

        print(
            f"Time: {self.time:.1f}s | "
            f"Altitude: {self.altitude:.2f}m | "
            f"Latitude: {self.latitude:.6f} | "
            f"Longitude: {self.longitude:.6f} | "
            f"Velocity: {self.velocity:.2f}m/s | "
            f"Wind: {self.wind_speed:.2f}m/s"
        )