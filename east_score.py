from network import Model
import json, datetime
from urllib.parse import urlparse, parse_qs
import os

tool = Model()

day_format = "%Y/%m/%d"
time_format = "%H:%M:%S"

class Score():
    def __init__(self, ct, ut, print_key="", log_dir="logs"):
        self.ct = ct
        self.ut = ut
        self.log_dir = log_dir
        os.makedirs(log_dir, exist_ok=True)
        self.print_key = print_key
        self.task_headers = {
            "em-os": "android",
            "em-ver": "10.10.1",
            "em-md": "Z1fa9jdkODRjZGQ2MTVmY2YwZjFkNzA0ZTliNDQ1OTUwMmV8fDYyODA3NzI5OTQ2NTE1Mw=fce5=",
            "ctoken": self.ct,
            "utoken": self.ut,
            "appkey": "EIBnBlYuvK",
            "Content-Type": "application/json"
        }
        self.zixuan_headers = {
            "Referer": "http://www.eastmoney.com/",
            "ct": self.ct,
            "ut": self.ut,
            "appkey": "63219653eaf8343e4715a948e5ff0745",
        }

    def login(self):
        url = "https://empointcpf.eastmoney.com:9001/TaskServiceV2/UserSignIn"
        data = {
            "TaskId": "671cc3ec74ef40a2ad1e8adc3ca24478"
        }
        r_data = tool.post(url, data=json.dumps(data), headers=self.task_headers).json()
        return r_data

    def get_last_login(self):
        url = "https://empointcpf.eastmoney.com:9001/TaskServiceV2/GetUserSignInfo?TaskId=671cc3ec74ef40a2ad1e8adc3ca24478"
        r_data = tool.get(url, headers=self.task_headers).json()
        # print(r_data)
        last_time = r_data["data"]["FinishSignInTimeList"]
        if last_time:
            last_time = last_time[-1]
        else:
            last_time = ""
        return last_time

    def get_task_list(self):
        url = "https://empointcpf.eastmoney.com:9001/TaskServiceV2/GetUserTaskList"
        r_data = tool.get(url, headers=self.task_headers).json()
        return r_data

    def receive_task(self, task_id="8e772eb260a44e0b8220f74add76fa6b"):
        url = "https://empointcpf.eastmoney.com:9001/TaskServiceV2/ReceiveTask"
        data = {
            "TaskId": task_id,
        }
        r_data = tool.post(url, data=json.dumps(data), headers=self.task_headers).json()
        return r_data

    def add_zixuan(self, code="1$530050", g=6):
        url = "https://myfavor.eastmoney.com/v4/mobile/aslotmgrp"
        data = {
            "scs": code,
            "gis": str(g),
        }
        r_data = tool.post(url, data=json.dumps(data), headers=self.zixuan_headers).json()
        return r_data

    def remove_zixuan(self, code="1$530050", g=6):
        url = "https://myfavor.eastmoney.com/v4/mobile/dslotmg"
        data = {
            "scs": code,
            "gis": str(g),
        }
        r_data = tool.post(url, data=json.dumps(data), headers=self.zixuan_headers).json()
        return r_data

    def add_fund(self, code="1006$AXT0030", g=1): #150
        url = "https://myfavor.eastmoney.com/v4/mobile_fund/aslot"
        data = {
            "scs": code,
            "g": str(g),
        }
        r_data = tool.post(url, data=json.dumps(data), headers=self.zixuan_headers).json()
        if r_data["message"] == "分组信息不存在":
            return self.add_fund(code=code, g=g + 1)
        return r_data

    def remove_fund(self, code="1006$AXT0030", g=1):
        url = "https://myfavor.eastmoney.com/v4/mobile_fund/dslot"
        data = {
            "scs": code,
            "g": str(g),
        }
        r_data = tool.post(url, data=json.dumps(data), headers=self.zixuan_headers).json()
        if r_data["message"] == "分组信息不存在":
            return self.remove_fund(code=code, g=g + 1)
        return r_data

    def status(self, r_data, key=""):
        if "成功" not in r_data["message"] and r_data["message"] != "":
            self.print(f"{key} 失败", r_data)
            return 0
        else:
            self.print(f"{key} 成功!")
            # self.print(f"{key}成功", r_data)
            return 1


    def paser_url(self, url):
        # 解析URL
        parsed_url = urlparse(url)
        # 获取查询参数并转换为字典
        params = parse_qs(parsed_url.query)
        # 因为parse_qs会将每个值放在一个列表中，所以需要调整
        params = {k: v[0] for k, v in params.items()}
        return params

    def search_market(self, code):
        url = "https://search-api-security.eastmoney.com/search"
        data = {
            "client": "android",
            "clientType": "cfw",
            "clientVersion": "10.10.1",
            "keyword": code,
            "type": [
                "financeMixV2"
            ]
        }
        market = "150"
        r_data = tool.post(url, data=json.dumps(data), headers=self.task_headers).json()
        if len(r_data["result"]["financeMixV2"]):
            market = r_data["result"]["financeMixV2"][0]["data"]["market"]
        return market

    def print(self, *args, **kwargs):
        time = datetime.datetime.now().strftime(f"{day_format} {time_format}")
        print(time, self.print_key, *args, **kwargs)
        self.log(time, self.print_key, *args, **kwargs)

    def log(self, *args, **kwargs):
        time = datetime.datetime.now().strftime("%Y_%m_%d")
        log_file = f"{self.log_dir}/log_{time}.txt"
        log_content = " ".join(map(str, args)) + "\n"
        # 将日志写入文件
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(log_content)

    def main(self):
        self.print(f"开始刷新...")
        date = datetime.datetime.now().strftime(day_format)
        finished = 0
        last_login_str = self.get_last_login()
        if last_login_str:
            last_login = datetime.datetime.strptime(last_login_str, day_format).strftime(day_format)
        else:
            last_login = last_login_str
        if date != last_login:
            key = f"[0] 签到"
            self.print(f"{key}...")
            r_data = self.login()
            finished += self.status(r_data=r_data, key=key)

        tasks_ = self.get_task_list()["data"]
        tasks = []
        for task in tasks_:
            if "TaskList" in task.keys():
                task_ = task["TaskList"]
                tasks += task_

        task_nums = len(tasks)
        self.print(f"任务数量 {task_nums}")
        for i, task in enumerate(tasks):
            if task['TaskReceiveDate'] is None:
                task_id = task['TaskID']
                key = f"[{i+1}/{task_nums}] 接受任务"
                self.print(key, task_id)
                r_data = self.receive_task(task_id=task_id)
                self.status(r_data=r_data, key=key)

            task_url = json.loads(task["TaskExtUrl"])["android"]
            params = self.paser_url(task_url)
            code_keys = ["stockcode", "code"]
            for code_key in code_keys:
                if code_key in params.keys():
                    code = params[code_key]
                    if code[:2] in ["SH", "SZ"]:
                        code = ("1$" if code[:2] == "SH" else "0$") + code[2:]

                        key = f"[{i+1}/{task_nums}] 添加自选 {code}"
                        self.print(f"{key}...")
                        r_data = self.add_zixuan(code=code)
                        finished += self.status(r_data=r_data, key=key)

                        key = f"[{i+1}/{task_nums}] 删除自选 {code}"
                        self.print(f"{key}...")
                        r_data = self.remove_zixuan(code=code)
                        self.status(r_data=r_data, key=key)

                    # elif code[:3] == "AXT":
                    else:
                        code = str(self.search_market(code)) + "$" + code.split("|")[-1]

                        key = f"[{i+1}/{task_nums}] 添加基金自选  {code}"
                        self.print(f"{key}...")
                        r_data = self.add_fund(code=code)
                        finished += self.status(r_data=r_data, key=key)

                        key = f"[{i+1}/{task_nums}] 删除基金自选  {code}"
                        self.print(f"{key}...")
                        r_data = self.remove_fund(code=code)
                        self.status(r_data=r_data, key=key)

        self.print(f"完成任务数量: {finished}/{task_nums}")
        self.print("刷新完成!")


if __name__ == '__main__':
    ct = ""
    ut = ""

    score = Score(ct, ut)
    score.main()
    data = score.get_task_list()
    # data1 = score.add_zixuan()
    # data2 = score.remove_zixuan()
    # data3 = score.get_last_login()
    # data4 = score.login()
    # data5 = score.add_fund()



