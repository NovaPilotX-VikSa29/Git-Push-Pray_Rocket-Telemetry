import pandas as pd
import time
import os

from telemetry import Telemetry


# ============================================================
# CONFIGURATION
# ============================================================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

CSV_FILE = os.path.join(
    BASE_DIR,
    "real_values.csv"
)

# True  -> replay telemetry with delay
# False -> run immediately
REAL_TIME = True

# 1.0 = normal speed
# 0.1 = 10x faster
TIME_SCALE = 0.1


# ============================================================
# ROCKET SIMULATOR
# ============================================================

class RocketSimulator:

    def __init__(self, csv_file):

        self.csv_file = csv_file

        # ----------------------------------------------------
        # Load CSV
        # ----------------------------------------------------

        self.data = pd.read_csv(csv_file)

        # ----------------------------------------------------
        # Current telemetry
        # ----------------------------------------------------

        self.current_data = None
        self.current_telemetry = None

        # ----------------------------------------------------
        # Flight status
        # ----------------------------------------------------

        self.phase = "READY"

        self.apogee_detected = False
        self.parachute_deployed = False
        self.landed = False

        # ----------------------------------------------------
        # Flight information
        # ----------------------------------------------------

        self.max_altitude = 0.0
        self.previous_altitude = None

        print("Rocket simulator initialized.")
        print(f"Loaded {len(self.data)} telemetry records.")
        print()


    # ========================================================
    # DETERMINE FLIGHT PHASE
    # ========================================================

    def determine_phase(self, row):

        altitude = float(row["altitude"])
        velocity = float(row["velocity"])
        descent_rate = float(row["descent_rate"])

        parachute = row["parachute_deployed"]

        # Convert possible string values to boolean
        if isinstance(parachute, str):
            parachute = parachute.lower() in [
                "true",
                "1",
                "yes"
            ]

        # Don't call the initial zero-altitude row "LANDED"
        if self.previous_altitude is None:
            return "READY"

        # Landing
        if altitude <= 1 and abs(velocity) < 2:
            return "LANDED"

        # Parachute descent
        if parachute:
            return "PARACHUTE DESCENT"

        # Descent
        if descent_rate > 0 or velocity < 0:
            return "DESCENT"

        # Apogee
        if abs(velocity) < 2:
            return "APOGEE"

        # Ascent
        if velocity > 0:
            return "ASCENT"

        return "FLIGHT"


    # ========================================================
    # CREATE TELEMETRY OBJECT
    # ========================================================

    def create_telemetry(self, row):

        parachute = row["parachute_deployed"]

        # Convert string TRUE/FALSE if necessary
        if isinstance(parachute, str):

            parachute = parachute.lower() in [
                "true",
                "1",
                "yes"
            ]

        telemetry = Telemetry(

            time=float(row["time"]),

            altitude=float(row["altitude"]),

            latitude=float(row["latitude"]),

            longitude=float(row["longitude"]),

            velocity=float(row["velocity"]),

            temperature=float(row["temperature"]),

            pressure=float(row["pressure"]),

            wind_speed=float(row["wind_speed"]),

            wind_direction=float(row["wind_direction"]),

            acceleration=float(row["acceleration"]),

            descent_rate=float(row["descent_rate"]),

            parachute_deployed=parachute
        )

        return telemetry


    # ========================================================
    # PROCESS ONE TELEMETRY ROW
    # ========================================================

    def process_row(self, row):

        self.current_data = row

        altitude = float(row["altitude"])


        # ----------------------------------------------------
        # Track maximum altitude
        # ----------------------------------------------------

        if altitude > self.max_altitude:

            self.max_altitude = altitude


        # ----------------------------------------------------
        # Detect apogee
        # ----------------------------------------------------

        if not self.apogee_detected:

            if self.previous_altitude is not None:

                if altitude < self.previous_altitude:

                    self.apogee_detected = True

                    print()
                    print("🚀 APOGEE DETECTED!")

                    print(
                        f"   Maximum altitude: "
                        f"{self.max_altitude:.2f} m"
                    )

                    print()


        # ----------------------------------------------------
        # Detect parachute
        # ----------------------------------------------------

        parachute = row["parachute_deployed"]

        if isinstance(parachute, str):

            parachute = parachute.lower() in [
                "true",
                "1",
                "yes"
            ]

        if parachute and not self.parachute_deployed:

            self.parachute_deployed = True

            print()
            print("🪂 PARACHUTE DEPLOYED!")
            print()


        # ----------------------------------------------------
        # Determine phase
        # ----------------------------------------------------

        self.phase = self.determine_phase(row)


        # ----------------------------------------------------
        # Detect landing
        # ----------------------------------------------------

        if self.phase == "LANDED" and not self.landed:

            self.landed = True

            print()
            print("🛬 ROCKET LANDED!")
            print()


        # ----------------------------------------------------
        # Create telemetry object
        # ----------------------------------------------------

        self.current_telemetry = self.create_telemetry(row)

        # Store previous altitude
        self.previous_altitude = altitude


    # ========================================================
    # DISPLAY TELEMETRY
    # ========================================================

    def display_telemetry(self, row):

        print(
            f"TIME: {float(row['time']):6.1f} s | "
            f"ALT: {float(row['altitude']):8.2f} m | "
            f"VEL: {float(row['velocity']):8.2f} m/s | "
            f"ACC: {float(row['acceleration']):7.2f} m/s² | "
            f"WIND: {float(row['wind_speed']):5.2f} m/s | "
            f"PHASE: {self.phase}"
        )


    # ========================================================
    # RUN SIMULATION
    # ========================================================

    def run(self):

        print("==========================================")
        print("        ROCKET FLIGHT SIMULATOR")
        print("==========================================")
        print()

        print("🚀 Simulation starting...")
        print()

        previous_time = None


        # ----------------------------------------------------
        # Replay every CSV row
        # ----------------------------------------------------

        for _, row in self.data.iterrows():

            current_time = float(row["time"])


            # ------------------------------------------------
            # Wait according to telemetry time
            # ------------------------------------------------

            if previous_time is not None:

                time_difference = (
                    current_time - previous_time
                )

                if REAL_TIME:

                    time.sleep(
                        time_difference * TIME_SCALE
                    )


            previous_time = current_time


            # ------------------------------------------------
            # Process telemetry
            # ------------------------------------------------

            self.process_row(row)

            self.display_telemetry(row)


            # ------------------------------------------------
            # Current telemetry is now available here
            #
            # Other modules can access:
            #
            # simulator.current_telemetry
            # ------------------------------------------------


        # ====================================================
        # SIMULATION COMPLETE
        # ====================================================

        print()
        print("==========================================")
        print("        SIMULATION COMPLETE")
        print("==========================================")
        print()

        print(
            f"Total simulation time : "
            f"{self.data['time'].iloc[-1]} s"
        )

        print(
            f"Maximum altitude      : "
            f"{self.max_altitude:.2f} m"
        )

        print(
            f"Apogee detected       : "
            f"{self.apogee_detected}"
        )

        print(
            f"Parachute deployed    : "
            f"{self.parachute_deployed}"
        )

        print(
            f"Landing detected      : "
            f"{self.landed}"
        )

        print()


# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":

    simulator = RocketSimulator(CSV_FILE)

    simulator.run()