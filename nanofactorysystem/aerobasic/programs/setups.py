from nanofactorysystem.aerobasic import VelocityMode
from nanofactorysystem.aerobasic.constants.tasks import ProgrammingMode
from nanofactorysystem.aerobasic.programs import AeroBasicProgram


class DefaultSetup(AeroBasicProgram):
    def __init__(
            self,
            programming_mode: ProgrammingMode = ProgrammingMode.ABSOLUTE,
            velocity_mode: VelocityMode = VelocityMode.ON,
    ):
        super().__init__()
        self.send("PRIMARY")
        self.send("SECONDS")
        self.send(programming_mode.value)  # ABSOLUTE vs INCREMENTAL
        self.VELOCITY(velocity_mode)
        self.send("IFOV OFF")


class SetupIFOV(AeroBasicProgram):
    def __init__(
            self,
            size=0.5,
            time=10,
            tracking_speed=500,
            tracking_acceleration=500
    ):
        super().__init__()
        self.ifov_size = size
        self.ifov_time = time
        self.ifov_tracking_speed = tracking_speed
        self.ifov_tracking_acceleration = tracking_acceleration

        # Turn off IFOV until setup is completed
        self.comment("\nTurn off IFOV until setup is completed")
        self.send("IFOV OFF")

        # Set Galvo Delays and mode
        self.comment("\nSet Galvo Delays and mode")
        self.send("GALVO LASERONDELAY A 0")
        self.send("GALVO LASEROFFDELAY A 0")
        self.send("GALVO LASERMODE A 0")

        # Synchronize axes
        self.comment("\nSynchronize axes")
        self.send("IFOV AXISPAIR 0, A, X")
        self.send("IFOV AXISPAIR 1, B, Y")
        self.send("ENCODER OUT X ON 0,0")
        self.send("ENCODER OUT Y ON 0,0")
        self.send("IFOV SYNCAXES Z")

        # IFOV Settings
        self.comment("\nIFOV Settings")
        self.send(f"IFOV SIZE {size:f}")
        self.send(f"IFOV TIME {time:f}")
        self.send(f"IFOV TRACKINGSPEED {tracking_speed:f}")
        self.send(f"IFOV TRACKINGACCEL {tracking_acceleration:f}")

        # Turn on IFOV
        self.comment("\nTurn on IFOV")
        self.send("IFOV ON")
