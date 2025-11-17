PROGRAM TrafficControl
VAR
    (* Input variables - Reading from SUMO *)
    VehicleCount AT %IW100 : INT;
    AvgSpeed AT %IW101 : INT;
    SimTime AT %IW102 : INT;
    WaitingTime AT %IW103 : INT;
    JamLength AT %IW104 : INT;
    ArrivedVehicles AT %IW105 : INT;
    
    (* Output variables - Writing to SUMO *)
    EmergencyMode AT %QW100 : INT;
    SpeedLimit AT %QW103 : INT;
    
    (* Internal logic variables *)
    CongestionDetected : BOOL;
    HighTraffic : BOOL;
END_VAR

(* === TRAFFIC ANALYSIS === *)
(* Detect congestion - low speed with many vehicles *)
IF (AvgSpeed < 5) AND (VehicleCount > 40) THEN
    CongestionDetected := TRUE;
ELSE
    CongestionDetected := FALSE;
END_IF;

(* Detect high traffic *)
IF VehicleCount > 45 THEN
    HighTraffic := TRUE;
ELSE
    HighTraffic := FALSE;
END_IF;

(* === CONTROL LOGIC === *)

(* Rule 1: Emergency Mode Activation *)
(* Activate when congested with many vehicles *)
IF CongestionDetected THEN
    EmergencyMode := 1;
ELSE
    EmergencyMode := 0;
END_IF;

(* Rule 2: Speed Limit Control *)
(* Reduce speed limit when jam length is high *)
IF JamLength > 10 THEN
    SpeedLimit := 30;
ELSIF HighTraffic THEN
    SpeedLimit := 40;
ELSE
    SpeedLimit := 0;
END_IF;

END_PROGRAM
