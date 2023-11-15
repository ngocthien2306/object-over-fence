import time
import threading

from pydantic import BaseModel
from pyModbusTCP.client import ModbusClient

class PLCControllerConfig(BaseModel):
    plc_ip_address: str
    plc_port: int
    plc_address: int
    modbus_address: int

class PLCControllerBase:
    def __init__(self, plc_info: PLCControllerConfig):
        pass

    def turn_on(self):
        pass

    def turn_off(self):
        pass

class PLCReader:
    def __init__(self, plc_info: PLCControllerConfig) -> None:
        self._plc_info = plc_info
        self._value = False

    def start(self):
        self._job = threading.Thread(target=self._run)
        self._job.daemon = True
        self._job.start()

    def get_value(self):
        return self._value

    def _run(self):
        while True:
            self._value = self._read_from_plc(self._plc_info.modbus_address)
            time.sleep(2)

    def _read_from_plc(self, modbus_address):
        client = ModbusClient(host=self._plc_info.plc_ip_address, port=self._plc_info.plc_port)
        try:
            # Kết nối với PLC
            if client.open():
                # Ghi giá trị boolean xuống PLC
                result = client.read_coils(modbus_address, 1)
                print(result)
                if result is not None and len(result) > 0:
                    return result[0]
                else:
                    return False
            else:
                print("Không thể kết nối với PLC")
                return False
        except Exception as e:
            print("Lỗi khi ghi giá trị xuống PLC:", str(e))
            return False
        finally:
            # Đóng kết nối với PLC sau khi hoàn thành
            client.close()

class PLCController(PLCControllerBase):
    def __init__(self, plc_info: PLCControllerConfig):
        self._plc_info = plc_info
        self._state = None
    
    def _read_from_plc(self, modbus_address):
        client = ModbusClient(host=self._plc_info.plc_ip_address, port=self._plc_info.plc_port)
        try:
            # Kết nối với PLC
            if client.open():
                # Ghi giá trị boolean xuống PLC
                result = client.read_coils(modbus_address, 1)
                if result is not None and len(result) > 0:
                    return result[0]
                else:
                    return False
            else:
                print("Không thể kết nối với PLC")
                return False
        except Exception as e:
            print("Lỗi khi đọc giá trị PLC:", str(e))
            return False
        finally:
            # Đóng kết nối với PLC sau khi hoàn thành
            client.close()

    def _write_to_plc(self, modbus_address, value_to_write):
        """
        Hàm này ghi giá trị xuống PLC thông qua Modbus TCP.

        Parameters:
            plc_ip (str): Địa chỉ IP của PLC.
            plc_port (int): Cổng Modbus TCP của PLC.
            plc_address (int): Địa chỉ thiết bị Modbus trong PLC. Note = 1
            modbus_address (int): Địa chỉ Modbus của coil hoặc thanh ghi cần ghi giá trị.
            value_to_write (bool): Giá trị boolean cần ghi (True hoặc False).

        Returns:
            bool: Trả về True nếu việc ghi thành công, False nếu việc ghi thất bại.
        """
        client = ModbusClient(host=self._plc_info.plc_ip_address, port=self._plc_info.plc_port)
        try:
            # Kết nối với PLC
            if client.open():
                # Ghi giá trị boolean xuống PLC
                result = client.write_single_coil(modbus_address, value_to_write)
                return result
            else:
                print("Không thể kết nối với PLC")
                return False
        except Exception as e:
            print("Lỗi khi ghi giá trị xuống PLC:", str(e))
            return False
        finally:
            # Đóng kết nối với PLC sau khi hoàn thành
            client.close()

    def update_state(self):
        state = self._read_from_plc(self._plc_info.modbus_address)
        print("PLC value", state)
        if state:
            self._state = "on"
        else:
            self._state = "off"

    def turn_on(self):
        # self.update_state()
        if self._state is None or self._state == "off":
            print(self._plc_info.modbus_address,"ON")
            res = self._write_to_plc(self._plc_info.modbus_address, True)
            self._state = "on"
            return res
        return True

    def turn_off(self):
        
        # self.update_state()
        if self._state is None or self._state == "on":
            print(self._plc_info.modbus_address,"OFF")
            res = self._write_to_plc(self._plc_info.modbus_address, False)
            self._state = "off"
            return res
        return True

if __name__ == "__main__":
    import time
    plc_controller_config = PLCControllerConfig(
            plc_ip_address="192.168.2.150",
            plc_port=502,
            plc_address=1,
            modbus_address=8197
    )
    plc = PLCReader(plc_controller_config)
    plc.start()
    time.sleep(2)
    print(plc.get_value())
    # plc.turn_on()
    # time.sleep(3)
    # plc = PLCController(plc_controller_config)
    # plc.turn_on()
    # plc.turn_off()
