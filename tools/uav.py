from langchain_core.tools import tool

@tool
def uav_telemetry(action: str, param: str = "") -> str:
    """
    UAV/İHA telemetri ve komut (STUB - gerçek bağlayıcıyı sen ekle).
    action: 'status' | 'arm' | 'disarm' | 'takeoff' | 'land' | 'goto' | 'rtl' | 'set_mode'
    param:  ekstra (örn: 'alt=10', 'lat=41.0,lon=29.0', 'mode=GUIDED')
    """
    # GERÇEK ENTREGRASYON BURAYA:
    # from pymavlink import mavutil
    # master = mavutil.mavlink_connection('udp:127.0.0.1:14550')
    # master.wait_heartbeat()
    # ...
    return f"[UAV STUB] action={action}, param={param} -> Bağlantı yok (simülasyon). pymavlink/DroneKit entegrasyonu bekliyor."