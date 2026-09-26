import math


def predict_landing(telemetry: dict) -> dict:

    required = [
        "altitude",
        "latitude",
        "longitude",
        "descent_rate",
        "wind_speed",
        "wind_direction",
    ]

    # ========================================================
    # VALIDATE REQUIRED FIELDS
    # ========================================================

    for key in required:

        if key not in telemetry:

            raise ValueError(
                f"Missing telemetry field: {key}"
            )

    # ========================================================
    # READ TELEMETRY
    # ========================================================

    altitude = float(telemetry["altitude"])

    lat = float(telemetry["latitude"])

    lon = float(telemetry["longitude"])

    descent_rate = float(
        telemetry["descent_rate"]
    )

    wind_speed = float(
        telemetry["wind_speed"]
    )

    wind_direction = float(
        telemetry["wind_direction"]
    )

    # ========================================================
    # CHECK VALUES
    # ========================================================

    values = [
        altitude,
        lat,
        lon,
        descent_rate,
        wind_speed,
        wind_direction
    ]

    if not all(math.isfinite(v) for v in values):

        raise ValueError(
            "Telemetry values must be finite."
        )

    if altitude < 0:

        raise ValueError(
            "Altitude cannot be negative."
        )

    if not -90 <= lat <= 90:

        raise ValueError(
            "Latitude must be between -90 and 90."
        )

    if not -180 <= lon <= 180:

        raise ValueError(
            "Longitude must be between -180 and 180."
        )

    if descent_rate <= 0:

        raise ValueError(
            "Descent rate must be positive."
        )

    if wind_speed < 0:

        raise ValueError(
            "Wind speed cannot be negative."
        )

    # ========================================================
    # ESTIMATE TIME TO LANDING
    # ========================================================

    time_to_landing = (
        altitude / descent_rate
    )

    # ========================================================
    # WIND DIRECTION
    # ========================================================

    direction_rad = math.radians(
        wind_direction % 360
    )

    # ========================================================
    # CALCULATE WIND DRIFT
    # ========================================================

    north_drift = (
        wind_speed
        * math.cos(direction_rad)
        * time_to_landing
    )

    east_drift = (
        wind_speed
        * math.sin(direction_rad)
        * time_to_landing
    )

    # ========================================================
    # EARTH MODEL
    # ========================================================

    earth_radius = 6_371_000.0

    latitude_rad = math.radians(lat)

    # ========================================================
    # PREDICT LATITUDE
    # ========================================================

    predicted_lat = lat + math.degrees(
        north_drift / earth_radius
    )

    # ========================================================
    # PREDICT LONGITUDE
    # ========================================================

    cos_lat = math.cos(latitude_rad)

    if abs(cos_lat) < 1e-8:

        raise ValueError(
            "Longitude prediction is unreliable near the poles."
        )

    predicted_lon = lon + math.degrees(
        east_drift /
        (earth_radius * cos_lat)
    )

    # Keep longitude between -180 and +180

    predicted_lon = (
        (predicted_lon + 180) % 360
    ) - 180

    # ========================================================
    # UNCERTAINTY
    # ========================================================

    uncertainty_radius = (
        30.0
        + 0.15
        * time_to_landing
        * wind_speed
    )

    # ========================================================
    # RETURN RESULT
    # ========================================================

    return {

        "latitude": predicted_lat,

        "longitude": predicted_lon,

        "uncertainty_radius":
            uncertainty_radius,

        "time_to_landing":
            time_to_landing,

        "north_drift":
            north_drift,

        "east_drift":
            east_drift,

        "total_drift":
            math.hypot(
                north_drift,
                east_drift
            )
    }