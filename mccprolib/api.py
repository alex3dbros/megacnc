import requests
import json


class MegacellCharger:
    def __init__(self, ip):
        self.ip = ip
        self.headers = {'content-type': 'application/json'}
        if self.ip != "0.0.0.0":
            self.device_type = self.get_device_type()
        else:
            self.device_type = "Unknown"

    def get_cells_data(self):
        # First request for cells 1 to 8
        data1 = {
            "start": 1, "end": 8
        }
        result1 = self.get_data(data1, "api/get_cells_info")

        # Second request for cells 9 to 16
        data2 = {
            "start": 9, "end": 16
        }
        result2 = self.get_data(data2, "api/get_cells_info")

        # Combine the results
        combined_result = {'cells': result1['cells'] + result2['cells']}
        return combined_result

    # set_cell used for setting cell commands
    # start charging: ach, start discharging: adc, stop charging: sc,
    # stop discharging: odc, Start Store Charging: asc
    # Stop Store charging: sc, Dispose Cell: dsp, Stop Dispose: odc
    # Start ESR Test: esr
    def set_cell(self, CiD, Cmd):
        data = {
            "cells": [{"CiD": CiD, "CmD": Cmd}]
        }

        result = self.set_data(data, "api/set_cell")
        return result

    def set_cells(self, data):
        result = self.set_data(data, "api/set_cell")
        return result

    def set_cell_macro(self, CiD, Cmd):
        data = {
            "cells": [{"CiD": CiD, "CmD": Cmd}]
        }

        result = self.set_data(data, "api/set_cell_macro")
        return result

    def set_cells_macro(self, data):
        result = self.set_data(data, "api/set_cell_macro")
        return result

    def set_pid(self, Kp, Ki, Kd):
        data = {
            "cells": [{"Kp": Kp, "Ki": Ki, "Kd": Kd, "CiD": 0, "CmD": "setPID"}]
        }

        result = self.set_data(data, "api/set_pid")
        return result

    def set_hardware_config(self, temp_source, cell_to_group, cell_per_group, data_feed_type):
        data = {"tempSource": temp_source, "cellsToGroup": cell_to_group, "maxCellPerGroup": cell_per_group, "dataFeedType": data_feed_type}

        result = self.set_data(data, "api/set_hw_conf")
        return result

    def get_config(self):
        data = {}
        result = self.get_data(data, "api/get_config_info")
        return result

    def set_config(self, config):
        result = self.set_data(config, "api/set_config_info")
        return result

    def set_cell_chemistry(self, config):
        result = self.set_data(config, "api/set_chemistry")
        return result

    def get_cell_chemistry(self, data):
        result = self.set_data(data, "api/get_chemistry")
        return result

    def reset(self):
        result = self.set_data({"secret" : 20200104}, "api/reset_charger")
        return result


    def get_data(self, data, api_addr):
        req_uri = "http://" + self.ip + "/" + api_addr
        req = requests.post(req_uri, data=json.dumps(data), headers=self.headers)
        return req.json()

    def set_data(self, data, api_addr):
        req_uri = "http://" + self.ip + "/" + api_addr
        req = requests.post(req_uri, data=json.dumps(data), headers=self.headers)
        return req.content

    def get_device_type(self):
        data = {}
        result = self.get_data(data, "api/who_am_i")

        return result

    @staticmethod
    def send_data_api(address, api_addr, data):
        req_uri = address + "/" + api_addr
        headers = {'content-type': 'application/json'}

        req = requests.post(req_uri, data=json.dumps(data), headers=headers)
        return req.text



