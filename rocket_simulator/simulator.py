import pandas as pd
import time
import os
import sys

from telemetry import Telemetry


# ============================================================
# PROJECT PATH
# ============================================================

BASE_DIR = os.path.dirname(
    os.path.abspath(__file__)
)

PROJECT_DIR = os.path.dirname(BASE_DIR)

sys.path.append(PROJECT_DIR)


# Import landing predictor from the recovery folder
from recovery.landing_predictor import predict_landing


# ============================================================
# CSV FILE
# ============================================================

CSV_FILE = os.path.join(
    BASE_DIR,
    "real_values.csv"
)


# ============================================================
# SIMULATION SETTINGS
# ============================================================

REAL_TIME = True

# 0.1 means:
# 1 second of rocket flight = 0.1 seconds real time
TIME_SCALE = 0.1


# ============================================================
# ROCKET SIMULATOR
# ============================================================

class RocketSimulator:

    def __init__(self, csv_file):

        self.csv_file = csv_file

        self.data = pd.read_csv(
            csv_file
        )

        self.current_data = None
        self.current_telemetry = None
        self.current_prediction = None

        self.phase = "READY"

        self.apogee_detected = False
        self.parachute_deployed = False
        self.landed = False

        self.max_altitude = 0.0
        self.previous_altitude = None

        print("Rocket simulator initialized.")
        print(
            f"Loaded {len(self.data)} telemetry records."
        )
        print()


    # ========================================================
    # DETERMINE FLIGHT PHASE
    # ========================================================

    def determine_phase(self, row):

        altitude = float(
            row["altitude"]
        )

        velocity = float(
            row["velocity"]
        )

        descent_rate = float(
            row["descent_rate"]
        )

        parachute = row[
            "parachute_deployed"
        ]

        # Convert CSV string to boolean
        if isinstance(parachute, str):

            parachute = (
                parachute.lower()
                in ["true", "1", "yes"]
            )


        # First telemetry record
        if self.previous_altitude is None:

            return "READY"


        # Landing detection
        if (
            altitude <= 1
            and abs(velocity) < 2
        ):

            return "LANDED"


        # Parachute descent
        if parachute:

            return "PARACHUTE DESCENT"


        # Descent
        if (
            descent_rate > 0
            or velocity < 0
        ):

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

        parachute = row[
            "parachute_deployed"
        ]

        # Convert string boolean
        if isinstance(parachute, str):

            parachute = (
                parachute.lower()
                in ["true", "1", "yes"]
            )


        return Telemetry(

            time=row["time"],

            altitude=row["altitude"],

            latitude=row["latitude"],

            longitude=row["longitude"],

            velocity=row["velocity"],

            temperature=row["temperature"],

            pressure=row["pressure"],

            wind_speed=row["wind_speed"],

            wind_direction=row[
                "wind_direction"
            ],

            acceleration=row[
                "acceleration"
            ],

            descent_rate=row[
                "descent_rate"
            ],

            parachute_deployed=parachute
        )


    # ========================================================
    # PROCESS ONE TELEMETRY ROW
    # ========================================================

    def process_row(self, row):

        self.current_data = row

        altitude = float(
            row["altitude"]
        )


        # ----------------------------------------------------
        # Maximum altitude
        # ----------------------------------------------------

        if altitude > self.max_altitude:

            self.max_altitude = altitude


        # ----------------------------------------------------
        # APOGEE DETECTION
        # ----------------------------------------------------

        if not self.apogee_detected:

            if self.previous_altitude is not None:

                if altitude < self.previous_altitude:

                    self.apogee_detected = True

                    print()

                    print(
                        "🚀 APOGEE DETECTED!"
                    )

                    print(
                        f"   Maximum altitude: "
                        f"{self.max_altitude:.2f} m"
                    )

                    print()


        # ----------------------------------------------------
        # PARACHUTE DETECTION
        # ----------------------------------------------------

        parachute = row[
            "parachute_deployed"
        ]

        if isinstance(parachute, str):

            parachute = (
                parachute.lower()
                in ["true", "1", "yes"]
            )


        if (
            parachute
            and not self.parachute_deployed
        ):

            self.parachute_deployed = True

            print()

            print(
                "🪂 PARACHUTE DEPLOYED!"
            )

            print()


        # ----------------------------------------------------
        # DETERMINE FLIGHT PHASE
        # ----------------------------------------------------

        self.phase = (
            self.determine_phase(row)
        )


        # ----------------------------------------------------
        # LANDING DETECTION
        # ----------------------------------------------------

        if (
            self.phase == "LANDED"
            and not self.landed
        ):

            self.landed = True

            print()

            print(
                "🛬 ROCKET LANDED!"
            )

            print()


        # ----------------------------------------------------
        # CREATE TELEMETRY OBJECT
        # ----------------------------------------------------

        self.current_telemetry = (
            self.create_telemetry(row)
        )


        # ----------------------------------------------------
        # LANDING PREDICTION
        # ----------------------------------------------------

        self.current_prediction = None

        descent_rate = float(
            row["descent_rate"]
        )


        # Predictor requires:
        # altitude > 0
        # descent_rate > 0

        if (
            altitude > 0
            and descent_rate > 0
            and not self.landed
        ):

            try:

                telemetry_dict = (
                    self.current_telemetry
                    .to_dict()
                )


                self.current_prediction = (
                    predict_landing(
                        telemetry_dict
                    )
                )


            except ValueError as error:

                print(
                    f"⚠ Prediction error: "
                    f"{error}"
                )


        # Store altitude for next row
        self.previous_altitude = altitude


    # ========================================================
    # DISPLAY TELEMETRY
    # ========================================================

    def display_telemetry(self):

        telemetry = (
            self.current_telemetry
        )


        print(
            f"TIME: {telemetry.time:6.1f} s | "
            f"ALT: {telemetry.altitude:8.2f} m | "
            f"VEL: {telemetry.velocity:8.2f} m/s | "
            f"ACC: {telemetry.acceleration:7.2f} m/s² | "
            f"WIND: {telemetry.wind_speed:5.2f} m/s | "
            f"PHASE: {self.phase}"
        )


    # ========================================================
    # DISPLAY LANDING PREDICTION
    # ========================================================

    def display_prediction(self):

        if self.current_prediction is None:

            return


        prediction = (
            self.current_prediction
        )


        print(
            "   📍 PREDICTED LANDING:"
        )


        print(
            f"      Latitude  : "
            f"{prediction['latitude']:.6f}"
        )


        print(
            f"      Longitude : "
            f"{prediction['longitude']:.6f}"
        )


        print(
            f"      ETA       : "
            f"{prediction['time_to_landing']:.2f} s"
        )


        print(
            f"      Drift     : "
            f"{prediction['total_drift']:.2f} m"
        )


        print(
            f"      Uncertainty: "
            f"±{prediction['uncertainty_radius']:.2f} m"
        )


    # ========================================================
    # RUN SIMULATION
    # ========================================================

    def run(self):

        print(
            "=========================================="
        )

        print(
            "      INTELLIGENT ROCKET SYSTEM"
        )

        print(
            "=========================================="
        )

        print()

        print(
            "🚀 Simulation starting..."
        )

        print()


        previous_time = None


        # Process every telemetry record
        for _, row in self.data.iterrows():

            current_time = float(
                row["time"]
            )


            # ------------------------------------------------
            # REAL-TIME DELAY
            # ------------------------------------------------

            if previous_time is not None:

                time_difference = (
                    current_time
                    - previous_time
                )


                if REAL_TIME:

                    time.sleep(
                        time_difference
                        * TIME_SCALE
                    )


            previous_time = current_time


            # ------------------------------------------------
            # PROCESS TELEMETRY
            # ------------------------------------------------

            self.process_row(row)


            # ------------------------------------------------
            # DISPLAY CURRENT STATE
            # ------------------------------------------------

            self.display_telemetry()

            self.display_prediction()


        # ====================================================
        # SIMULATION COMPLETE
        # ====================================================

        print()

        print(
            "=========================================="
        )

        print(
            "        SIMULATION COMPLETE"
        )

        print(
            "=========================================="
        )

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


        # ----------------------------------------------------
        # FINAL LANDING PREDICTION
        # ----------------------------------------------------

        if self.current_prediction:

            prediction = (
                self.current_prediction
            )


            print()

            print(
                "FINAL LANDING PREDICTION"
            )


            print(
                f"Latitude  : "
                f"{prediction['latitude']:.6f}"
            )


            print(
                f"Longitude : "
                f"{prediction['longitude']:.6f}"
            )


            print(
                f"Uncertainty : "
                f"±{prediction['uncertainty_radius']:.2f} m"
            )


        print()


# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":

    simulator = RocketSimulator(
        CSV_FILE
    )

    simulator.run()