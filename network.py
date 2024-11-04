import requests
from bs4 import BeautifulSoup
import json, os, re
from concurrent import futures
from tqdm import tqdm
import numpy as np
import time
import pickle

import socket
import requests.packages.urllib3.util.connection as urllib3_cn
import multiprocessing
# from multiprocessing_on_dill.dummy import Pool

def allowed_gai_family():
    family = socket.AF_INET
    return family
    # if urllib3_cn.HAS_IPV6:
    #     family = socket.AF_INET6 # force ipv6 only if it is available


urllib3_cn.allowed_gai_family = allowed_gai_family


class Model(object):
    def __init__(self, log=None, timeout=30):
        proxies = {'http': None, 'https': None}
        headers = {'User-Agent': "Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 6.0)",
                   'referer': None,
                   # 'Cookie':
                   }
        if log is not None:
            self.check_dirs(log)
        self.name = 'log'
        self.log = log
        self.proxies = proxies
        self.headers = headers
        self.timeout = timeout
        self.s = requests.session()

    def get(self, url, headers=None, allow_redirects=True, params=None):
        if headers:
            old_headers = self.headers.copy()
            old_headers.update(headers)
        else:
            old_headers = self.headers
        if not old_headers['referer']:
            old_headers['referer'] = '/'.join(url.split('/')[:3])
        try:
            return self.s.get(url=url, headers=old_headers, proxies=self.proxies,
                              allow_redirects=allow_redirects, params=params, timeout=self.timeout)  # ,timeout=1
        except Exception as e:
            # self.print(f"Network GET error: {url} {e}")
            raise Exception(f"Network GET Error {e}: {url} {params}")

    def post(self, url, data, headers=None):
        if headers:
            old_headers = self.headers.copy()
            old_headers.update(headers)
        else:
            old_headers = self.headers
        if not old_headers['referer']:
            old_headers['referer'] = '/'.join(url.split('/')[:3])
        try:
            return self.s.post(url=url, data=data, headers=old_headers, proxies=self.proxies, timeout=self.timeout)
        except Exception as e:
            # self.print(f"Network POST error: {url} {data} {e}")
            raise Exception(f"Network POST Error {e}: {url} {data}")

    def solver(self, r):
        r.encoding = "utf-8"
        return BeautifulSoup(r.text, 'lxml')

    def resolver(self, url):
        return self.solver(self.get(url))

    def download(self, url, path='download'):
        with open(path, 'wb') as f:
            f.write(self.get(url).content)

    def write(self, data, path, mode='w', encoding="utf-8"):
        with open(path, mode, encoding=encoding) as f:
            f.write(data)
        return 0

    def read(self, path, mode='r', encoding="utf-8"):
        with open(path, mode, encoding=encoding) as f:
            data = f.read()
        return data

    def write_plk(self, data, path, mode='wb'):
        with open(path, mode) as f:
            pickle.dump(data, f)
        return 0

    def read_plk(self, path, mode='rb'):
        with open(path, mode) as f:
            data = pickle.load(f)
        return data

    def write_json(self, data, path, encoding="utf-8"):
        with open(path, 'w', encoding=encoding) as f:
            json.dump(data, f, ensure_ascii=False)
        return 0

    def read_json(self, path, encoding='utf-8'):
        with open(path, 'r', encoding=encoding) as f:
            data = json.load(f)
        return data

    def check_dirs(self, dirs):
        self.dirs = dirs
        if not os.path.exists(self.dirs):
            os.makedirs(self.dirs)
        return dirs

    def time(self):
        return time.strftime("%Y-%m-%d_%H-%M-%S", time.localtime())

    def print(self, *str_, **kwargs):
        print(f'\033[34m{self.time()}\033[0m', *str_, **kwargs)
        # str_ = str(str_)
        # str_ = ", ".join(map(lambda x:x.strip().strip("'").strip('"'), str(str_)[1:-1].strip(",").split(",")))
        str_ = ", ".join(
            map(lambda x: x if isinstance(x, str) else x.__repr__() if isinstance(x, Exception) else str(x), str_))
        if self.log is not None:
            if 'end' in kwargs.keys() and '\n' not in kwargs['end']:
                # fstr = f'{str_}'[2:-3]
                fstr = str_
            else:
                # fstr =  f'{self.time()} ' + f'{str_}'[2:-3] + '\n'
                fstr = f'{self.time()} ' + str_ + '\n'
            self.write(fstr, path=f'{self.log}/{time.strftime("%Y-%m-%d", time.localtime())}_{self.name}.txt', mode='a')

    def pattern(self, string, pattern='(.*?)'):
        return re.findall(pattern, string)

    def muti_works(self, fn, datas, workers: int = 10, lam=None, show_tqdm=True):
        results = []
        # print(lam==None)
        with futures.ThreadPoolExecutor(max_workers=workers) as executor:
            to_do_map = {}
            for data in datas:
                if lam:
                    data = lam(data)
                    # future = executor.submit(fn, lam(data))
                if isinstance(data, tuple):
                    future = executor.submit(fn, *data)
                elif isinstance(data, dict):
                    future = executor.submit(fn, **data)
                else:
                    future = executor.submit(fn, data)
                to_do_map[future] = data
            done_iter = futures.as_completed(to_do_map)
            done_iter = tqdm(done_iter, total=len(datas)) if show_tqdm else done_iter
            for future in done_iter:
                if isinstance(future.result(), list):
                    results += future.result()
                else:
                    results += [future.result()]
        return results

    def muti_works_order(self, fn, datas, workers: int = 10, lam=None, show_tqdm=True):
        results = []
        with futures.ThreadPoolExecutor(max_workers=workers) as executor:
            fs = []
            print("提交任务...") if show_tqdm else None
            datas = tqdm(datas) if show_tqdm else datas
            for data in datas:
                if lam:
                    data = lam(data)
                    # future = executor.submit(fn, lam(data))
                if isinstance(data, tuple):
                    future = executor.submit(fn, *data)
                elif isinstance(data, dict):
                    future = executor.submit(fn, **data)
                else:
                    future = executor.submit(fn, data)
                fs.append(future)

            def result_iterator():
                try:
                    # reverse to keep finishing order
                    fs.reverse()
                    while fs:
                        # Careful not to keep a reference to the popped future
                        yield fs.pop().result()
                finally:
                    for future in fs:
                        future.cancel()
            print("获取结果...")
            done_iter = result_iterator()  # executor.map(fn,datas)
            done_iter = tqdm(done_iter, total=len(datas)) if show_tqdm else done_iter
            for future in done_iter:
                if isinstance(future, list):
                    results += future
                else:
                    results += [future]
        return results

    def muti_process_order(self, fn, datas, workers=None, lam=None):
        results = []
        with futures.ProcessPoolExecutor(max_workers=workers) as executor:
            fs = []
            print("提交任务...")
            for data in tqdm(datas):
                if lam:
                    data = lam(data)
                    # future = executor.submit(fn, lam(data))
                if isinstance(data, tuple):
                    future = executor.submit(fn, *data)
                elif isinstance(data, dict):
                    future = executor.submit(fn, **data)
                else:
                    future = executor.submit(fn, data)
                fs.append(future)

            def result_iterator():
                try:
                    # reverse to keep finishing order
                    fs.reverse()
                    while fs:
                        # Careful not to keep a reference to the popped future
                        yield fs.pop().result()
                finally:
                    for future in fs:
                        future.cancel()
            print("获取结果...")
            done_iter = result_iterator()  # executor.map(fn,datas)
            done_iter = tqdm(done_iter, total=len(datas))
            for future in done_iter:
                if isinstance(future, list):
                    results += future
                else:
                    results += [future]
        return results

    def simple_muti_process(self, fn, datas):
        with futures.ProcessPoolExecutor() as executor:
            # 将任务分成子任务
            print("提交任务...")
            tasks = []
            for data in tqdm(datas):
                if isinstance(data, tuple):
                    task = executor.submit(fn, *data)
                else:
                    task = executor.submit(fn, data)
                tasks.append(task)
            # 获取每个子任务的执行结果
            print("获取结果...")
            results = []
            for future in tqdm(futures.as_completed(tasks), total=len(datas)):
                result = future.result()
                results.append(result)
        return results

    def seconds_to_hours(self, seconds):
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        seconds = seconds % 60
        return f"{hours:0>2.0f}:{minutes:0>2.0f}:{seconds:0>2.0f}"

    def fast_muti_process(self, fn, datas):
        tic = time.time()
        with multiprocessing.Pool() as pool:
            results = pool.map(fn, datas)
        toc = time.time()
        print("时间已过：",self.seconds_to_hours(toc - tic), end=' ')
        return results

    def chunk_datas(self, datas, n):
        split_lst = []
        chunk_size = len(datas) // n
        remainder = len(datas) % n
        start = 0
        for i in range(n):
            if i < remainder:
                end = start + chunk_size + 1
            else:
                end = start + chunk_size
            split_lst.append(datas[start:end])
            start = end
        return split_lst

    def sample_datas(self, lst, n):
        sub_lsts = [lst[i:i+n] for i in range(0, len(lst), n)]
        return sub_lsts

    def new_fn(self, fn, datas):
        results = []
        for data in datas:
            if isinstance(data, tuple):
                result = fn(*data)
            else:
                result = fn(data)
            results.append(result)
        return results

    def simple_divide_process(self, fn, datas, chunk_size=None):
        with futures.ProcessPoolExecutor() as executor:
            # 将任务分成子任务
            print("提交任务...")
            tasks = []
            chunk_datas = self.chunk_datas(datas, executor._max_workers) if chunk_size is None else self.sample_datas(datas, chunk_size)
            for data in chunk_datas:
                task = executor.submit(self.new_fn, fn, data)
                tasks.append(task)
            # 获取每个子任务的执行结果
            print("获取结果...")
            results = []
            for future in tqdm(futures.as_completed(tasks), total=len(tasks)):
                result = future.result()
                results += result
        return results

    def all_data(self, fn, datas, workers: int = 10, lam=None):
        datas = np.array(datas)
        results = self.muti_works(fn, datas, workers, lam)
        results = np.array(results)
        left_data = datas[results == '0']
        if len(left_data) > 0:
            results[results == '0'] = self.all_data(fn, left_data, workers, lam)
        return results


if __name__ == '__main__':
    t = Model(log='.\log')
    # t.print('1', end='')
    # t.print('65','8')
    # try:
    #     raise Exception('error')
    # except Exception as e:
    #     t.print(e)
    #     t.print(e,9,"ui")
    # t.print('fdf1','i')
    # t.print("fdf2")
    # t.print('fdf2"o"')
    # t.print("fdf2'o'")
    # t.print(Exception('12'),8)
    # a=["dss","dss"]
    # t.print(f"fdfd{a}")
    # pass #(Exception('error'),)
    # lambda
    # t.get("http://127.0.0.0")

    url = "http://search.10jqka.com.cn/customized/chart/get-robot-data"
    data = {"question": "昨日阳线",
            "perpage": "100",
            "page": 1,
            # "secondary_intent": "stock",
            # "log_info": "{\"input_type\":\"typewrite\"}",
            "source": "Ths_iwencai_Xuangu",
            # "version": "2.0",
            # "query_area": "", "block_list": "",
            # "add_info": "{\"urp\":{\"scene\":1,\"company\":1,\"business\":1},\"contentType\":\"json\",\"searchInfo\":true}",
            # "rsh": "667299998"
            }
    headers = {
        "Content-Type": "application/json",
        "Cookie": "v=Ay-tDJenl7SbsJOOVdlGF9CGvkg81IokHQOH4UG-ybuljUE2SaQTRi34F2BS"
    }
    #https://apm.hexin.cn/skywalking-web/browser/errorELKLogs?hexin-v=A9VX_kEhHQZV3jl8pJv8JU4Y5NqK0oA2U61tM1d4k2mbs_sEHyKZtOPWfV_k&hexin-v=A8tJ4BszK4DfTHdSTkJq4xTKWmSwYNYwWV-jnT3KpS9hQeUaxTBvMmlEM75O&hexin-v=A7Q2HWjebPVcSfg_mhQNdjfvhXkjjdGlGppssE4XQprCpFqndp2oB2rBPBKd&hexin-v=Ay-tDJenl7SbsJOOVdlGF9CGvkg81IokHQOH4UG-ybuljUE2SaQTRi34F2BS&hexin-v=Aw2Ppkk5Vf6tJvHU2xREDcawHCKC6khuyzWlm0-QSwETWyNcFzpRjFtutTvc
    #https://apm.hexin.cn/skywalking-web/browser/errorELKLogs?hexin-v=A9VX_kEhHQZV3jl8pJv8JU4Y5NqK0oA2U61tM1d4k2mbs_sEHyKZtOPWfV_k&hexin-v=A8tJ4BszK4DfTHdSTkJq4xTKWmSwYNYwWV-jnT3KpS9hQeUaxTBvMmlEM75O&hexin-v=A7Q2HWjebPVcSfg_mhQNdjfvhXkjjdGlGppssE4XQprCpFqndp2oB2rBPBKd&hexin-v=Ay-tDJenl7SbsJOOVdlGF9CGvkg81IokHQOH4UG-ybuljUE2SaQTRi34F2BS&hexin-v=Aw2Ppkk5Vf6tJvHU2xREDcawHCKC6khuyzWlm0-QSwETWyNcFzpRjFtutTvc&hexin-v=A-Jgp8oA8i9eT-51OIvDHHUpM2NBM--fmBzaeix5DHAA4ozdFMM2XWjHKt3_
    #https://apm.hexin.cn/skywalking-web/browser/errorELKLogs?hexin-v=A9VX_kEhHQZV3jl8pJv8JU4Y5NqK0oA2U61tM1d4k2mbs_sEHyKZtOPWfV_k&hexin-v=A8tJ4BszK4DfTHdSTkJq4xTKWmSwYNYwWV-jnT3KpS9hQeUaxTBvMmlEM75O&hexin-v=A7Q2HWjebPVcSfg_mhQNdjfvhXkjjdGlGppssE4XQprCpFqndp2oB2rBPBKd&hexin-v=Ay-tDJenl7SbsJOOVdlGF9CGvkg81IokHQOH4UG-ybuljUE2SaQTRi34F2BS&hexin-v=Aw2Ppkk5Vf6tJvHU2xREDcawHCKC6khuyzWlm0-QSwETWyNcFzpRjFtutTvc&hexin-v=AwyOJVCWhE30MZA3c6k1_k-n3WE7Rbk9ssLEuGbPGhJa7KJfjlWAfwL5lBy1
    # t.get("http://search.10jqka.com.cn/unifiedwap/home/index")
    r = t.post(url,json.dumps(data),headers=headers).json()['data']["answer"][0]['txt'][0]['content']['components'][0]['data']['datas']

