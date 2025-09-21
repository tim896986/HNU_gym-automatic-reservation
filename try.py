import requests
import time
import datetime
import socket
import json
import re
import argparse
import os
import sys
import logging

# 配置日志
def setup_logging():
    """设置日志配置"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('reservation.log', encoding='utf-8'),
            logging.StreamHandler()
        ]
    )
    return logging.getLogger(__name__)

def test_connection():
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)
        sock.connect(('eportal.hnu.edu.cn', 443))
        sock.close()
        return True
    except:
        return False

# 新增：读取cookie.txt并返回cookie字典
def load_cookie_from_file(cookie_file='cookie.txt'):
    try:
        with open(cookie_file, 'r', encoding='utf-8') as f:
            cookie_str = f.read().strip()
        cookies = {}
        for item in cookie_str.split(';'):
            if '=' in item:
                k, v = item.strip().split('=', 1)
                cookies[k] = v
        return cookies
    except Exception as e:
        print(f"读取cookie失败: {e}")
        return None

# 新增：用cookie构造session
def get_session_with_cookie(cookie_file='cookie.txt'):
    session = requests.Session()
    cookies = load_cookie_from_file(cookie_file)
    if not cookies:
        print("未能加载cookie，无法继续")
        return None
    session.cookies.update(cookies)
    return session

def make_reservation(session, reservations, resource_id, max_attempts=1000, retry_delay=0.1, request_timeout=10):
    """
    进行预约，支持重试机制
    :param session: 会话对象
    :param reservations: 预约信息列表
    :param resource_id: 资源ID
    :param max_attempts: 最大尝试次数
    :param retry_delay: 重试间隔（秒）
    :return: 是否预约成功
    """
    if not session:
        print("未登录，无法进行预约")
        return False
        
    hall_url = "https://eportal.hnu.edu.cn/v2/reserve/hallView?id=10"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
        "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive"
    }
    
    try:
        session.get(hall_url, headers=headers)
        
        detail_url = f"https://eportal.hnu.edu.cn/v2/reserve/reserveDetail?id={resource_id}"
        session.get(detail_url, headers=headers)
        
        reserve_url = "https://eportal.hnu.edu.cn/site/reservation/launch"
        reserve_headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
            "Accept-Encoding": "gzip, deflate, br",
            "Content-Type": "application/x-www-form-urlencoded",
            "Origin": "https://eportal.hnu.edu.cn",
            "Referer": detail_url,
            "Connection": "keep-alive"
        }
        
        data = {
            "resource_id": resource_id,
            "code": "",
            "remarks": "",
            "deduct_num": "",
            "data": json.dumps(reservations)
        }
        
        attempt_count = 0
        start_time = datetime.datetime.now()
        
        while attempt_count < max_attempts:
            attempt_count += 1
            current_time = datetime.datetime.now()
            elapsed_time = (current_time - start_time).total_seconds()
            
            print(f"\r尝试第 {attempt_count} 次预约，已用时 {elapsed_time:.1f}秒", end="")
            
            try:
                response = session.post(reserve_url, headers=reserve_headers, data=data, timeout=request_timeout)
                result = response.json()
                
                if result.get('e') == 0:
                    print(f"\n预约成功！预约ID：{result['d']['appointment_id']}")
                    return True
                else:
                    error_msg = result.get('m', '未知错误')
                    # 对于可重试的错误，继续尝试
                    if error_msg in ["参数错误", "预约日期未达到", "点击太频繁了", "同一时间段不可重复预约", "系统繁忙", "网络错误"]:
                        time.sleep(retry_delay)
                        continue
                    # 对于不可重试的错误，记录但继续尝试
                    else:
                        print(f"\n[警告] 预约失败：{error_msg}，继续尝试...")
                        time.sleep(retry_delay)
                        continue
                        
            except requests.exceptions.Timeout:
                print(f"\n[警告] 请求超时，继续尝试...")
                time.sleep(retry_delay)
                continue
            except requests.exceptions.ConnectionError:
                print(f"\n[警告] 连接错误，继续尝试...")
                time.sleep(retry_delay)
                continue
            except json.JSONDecodeError:
                print(f"\n[警告] 响应解析错误，继续尝试...")
                time.sleep(retry_delay)
                continue
            except Exception as e:
                print(f"\n[警告] 请求异常：{str(e)}，继续尝试...")
                time.sleep(retry_delay)
                continue
        
        print(f"\n达到最大尝试次数（{max_attempts}次），预约失败")
        return False
            
    except Exception as e:
        print(f"\n预约请求初始化失败：{str(e)}")
        return False

def parse_time(time_str):
    try:
        target_time = datetime.datetime.strptime(time_str, "%Y-%m-%d %H:%M:%S")
        return target_time
    except ValueError:
        print("时间格式错误，请使用 'YYYY-MM-DD HH:MM:SS' 格式")
        return None

def wait_until(target_time):
    while True:
        current_time = datetime.datetime.now()
        if current_time >= target_time:
            return
        time_diff = (target_time - current_time).total_seconds()
        if time_diff > 0:
            print(f"\r距离预约开始还有: {time_diff:.1f}秒", end="")
            time.sleep(0.1)

def load_config():
    try:
        with open('config.json', 'r', encoding='utf-8') as f:
            config = json.load(f)
            return config
    except FileNotFoundError:
        print("错误：配置文件 config.json 不存在")
        return {}
    except json.JSONDecodeError:
        print("错误：配置文件格式不正确")
        return {}
    except Exception as e:
        print(f"读取配置文件时发生错误：{str(e)}")
        return {}

def fetch_time_and_table_options(session, resource_id, date):
    """
    拉取可预约时间段和台号，返回基础time_id、sub_id和展示列表
    只展示每种不同的时间段一次，台号遍历所有key下所有台号
    """
    url = f"https://eportal.hnu.edu.cn/site/reservation/resource-info-margin?resource_id={resource_id}&start_time={date}&end_time={date}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "Accept": "application/json, text/plain, */*",
        "Referer": f"https://eportal.hnu.edu.cn/v2/reserve/reserveDetail?id={resource_id}",
        "Connection": "keep-alive"
    }
    resp = session.get(url, headers=headers, verify=False)
    data = resp.json()
    d = data['d']
    # 只用第一个台号的时间段，且只显示每种时间段一次
    first_key = list(d.keys())[0]
    time_list = d[first_key]
    time_options = []
    last_yaxis = None
    for t in time_list:
        if t['yaxis'] != last_yaxis:
            time_options.append((len(time_options), t['yaxis']))
            last_yaxis = t['yaxis']
    base_time_id = time_list[0]['time_id']
    # 台号列表，遍历所有key下所有台号，去重
    table_options = []
    abscissa_set = set()
    base_sub_id = None
    for vlist in d.values():
        for v in vlist:
            abscissa = v['abscissa']
            if abscissa not in abscissa_set:
                table_options.append((len(table_options), abscissa))
                abscissa_set.add(abscissa)
                if base_sub_id is None:
                    base_sub_id = v['sub_id']
    return time_options, table_options, base_time_id, base_sub_id

def main():
    # 设置日志
    logger = setup_logging()
    logger.info("程序启动")
    
    config = load_config()
    if not config:
        logger.error("无法读取配置文件，请确保config.json存在且格式正确")
        print("错误：无法读取配置文件，请确保config.json存在且格式正确")
        return
    
    # 从配置文件读取重试参数
    max_retries = config.get('max_retries', 10)  # 最大重试次数
    retry_interval = config.get('retry_interval', 5)  # 重试间隔（秒）
    
    logger.info(f"配置参数：max_retries={max_retries}, retry_interval={retry_interval}")
    
    if len(sys.argv) == 1:
        print("使用cookie.txt中的cookie进行预约")
        resource_id = config.get('resource_id')
        slots = config.get('slots', 1)
        date = config.get('date')
        if not resource_id:
            print("错误：预约资源ID为必填项，请在config.json中配置resource_id")
            return
        
        # 外层重试循环
        retry_count = 0
        while retry_count < max_retries:
            try:
                retry_count += 1
                print(f"\n=== 第 {retry_count} 次尝试预约 ===")
                
                current_time = datetime.datetime.now()
                if not test_connection():
                    print("网络连接测试失败，请检查网络")
                    time.sleep(retry_interval)
                    continue
                    
                print("加载cookie...")
                session = get_session_with_cookie()
                if not session:
                    print("cookie无效，程序退出")
                    return
                    
                # 检查cookie是否有效（尝试访问个人主页）
                check_url = "https://eportal.hnu.edu.cn/v2/site/index"
                resp = session.get(check_url)
                if '登录' in resp.text or resp.url.startswith('http://cas.hnu.edu.cn'):
                    print("cookie已失效，请重新扫码登录并复制cookie")
                    return
                    
                target_date = date if date else current_time.strftime("%Y-%m-%d")
                # 拉取可选项
                time_options, table_options, base_time_id, base_sub_id = fetch_time_and_table_options(session, resource_id, target_date)
                print("可选时间段：")
                for idx, name in time_options:
                    print(f"{idx}. {name}")
                print("可选台号：")
                for idx, name in table_options:
                    print(f"{idx}. {name}")
                t_idx = int(input("请输入你想预约的时间段序号（如0）："))
                s_idx = int(input("请输入你想预约的台号序号（如0）："))
                time_count = len(time_options)
                print(f"[调试] 当前时间段总数 time_count = {time_count}")
                period1 = base_time_id + t_idx
                sub_resource_id1 = base_sub_id + time_count * s_idx - t_idx
                if slots == 2:
                    t_idx2 = t_idx + 1
                    s_idx2 = s_idx
                if slots == 1:
                    reservations = [
                        {
                            "date": target_date,
                            "period": period1,
                            "sub_resource_id": sub_resource_id1
                        }
                    ]
                else:
                    period2 = base_time_id + t_idx2
                    sub_resource_id2 = base_sub_id + time_count * s_idx2 - t_idx2
                    reservations = [
                        {
                            "date": target_date,
                            "period": period1,
                            "sub_resource_id": sub_resource_id1
                        },
                        {
                            "date": target_date,
                            "period": period2,
                            "sub_resource_id": sub_resource_id2
                        }
                    ]
                print(f"[调试] base_time_id = {base_time_id}, base_sub_id = {base_sub_id}")
                print(f"[调试] period1 = {period1}, sub_resource_id1 = {sub_resource_id1}")
                if slots == 2:
                    print(f"[调试] period2 = {period2}, sub_resource_id2 = {sub_resource_id2}")
                    
                # 从配置文件读取重试参数
                max_attempts = config.get('max_attempts', 1000)
                retry_delay = config.get('retry_delay', 0.1)
                request_timeout = config.get('request_timeout', 10)
                
                success = make_reservation(session, reservations, resource_id, max_attempts, retry_delay, request_timeout)
                if success:
                    logger.info("预约成功！程序结束")
                    print("预约成功！程序结束")
                    return
                else:
                    logger.warning(f"第 {retry_count} 次尝试失败，{retry_interval}秒后重试...")
                    print(f"第 {retry_count} 次尝试失败，{retry_interval}秒后重试...")
                    time.sleep(retry_interval)
                    
            except KeyboardInterrupt:
                logger.info("用户中断程序")
                print("\n用户中断程序")
                return
            except Exception as e:
                logger.error(f"程序发生错误：{str(e)}")
                print(f"程序发生错误：{str(e)}")
                print(f"第 {retry_count} 次尝试失败，{retry_interval}秒后重试...")
                time.sleep(retry_interval)
                
        logger.error(f"达到最大重试次数（{max_retries}次），程序结束")
        print(f"达到最大重试次数（{max_retries}次），程序结束")
        return
    # 命令行参数模式同样用cookie
    parser = argparse.ArgumentParser(description='体育馆预约程序')
    parser.add_argument('--time', type=str, help='预约开始时间，格式：YYYY-MM-DD HH:MM:SS')
    parser.add_argument('--date', type=str, default=config.get('date'), help='预约日期，格式：YYYY-MM-DD')
    parser.add_argument('--resource_id', type=str, default=config.get('resource_id'), help='预约资源ID')
    parser.add_argument('--slots', type=int, choices=[1, 2], default=config.get('slots', 1), help='预约时间段数量：1或2（默认1）')
    parser.add_argument('--period1', type=str, default=config.get('period1'), help='第一个时间段ID')
    parser.add_argument('--sub_resource_id1', type=str, default=config.get('sub_resource_id1'), help='第一个台号ID')
    parser.add_argument('--period2', type=str, default=config.get('period2'), help='第二个时间段ID')
    parser.add_argument('--sub_resource_id2', type=str, default=config.get('sub_resource_id2'), help='第二个台号ID')
    args = parser.parse_args()

    missing_params = []
    if not args.resource_id:
        missing_params.append("预约资源ID")
    if not args.period1:
        missing_params.append("第一个时间段ID")
    if not args.sub_resource_id1:
        missing_params.append("第一个台号ID")
    if args.slots == 2:
        if not args.period2:
            missing_params.append("第二个时间段ID")
        if not args.sub_resource_id2:
            missing_params.append("第二个台号ID")
    if missing_params:
        print("错误：以下参数为必填项：")
        for param in missing_params:
            print(f"- {param}")
        print("\n请通过以下方式提供这些参数：")
        print("1. 在config.json中配置")
        print("2. 通过命令行参数提供")
        return
    # 命令行模式的重试循环
    retry_count = 0
    while retry_count < max_retries:
        try:
            retry_count += 1
            print(f"\n=== 第 {retry_count} 次尝试预约（命令行模式）===")
            
            current_time = datetime.datetime.now()
            if not test_connection():
                print("网络连接测试失败，请检查网络")
                time.sleep(retry_interval)
                continue
                
            print("加载cookie...")
            session = get_session_with_cookie()
            if not session:
                print("cookie无效，程序退出")
                return
                
            check_url = "https://eportal.hnu.edu.cn/v2/site/index"
            resp = session.get(check_url)
            if '登录' in resp.text or resp.url.startswith('http://cas.hnu.edu.cn'):
                print("cookie已失效，请重新扫码登录并复制cookie")
                return
                
            target_date = args.date if args.date else current_time.strftime("%Y-%m-%d")
            time_options, table_options, base_time_id, base_sub_id = fetch_time_and_table_options(session, args.resource_id, target_date)
            print("可选时间段：")
            for idx, name in time_options:
                print(f"{idx}. {name}")
            print("可选台号：")
            for idx, name in table_options:
                print(f"{idx}. {name}")
            t_idx = int(input("请输入你想预约的时间段序号（如0）："))
            s_idx = int(input("请输入你想预约的台号序号（如0）："))
            if args.slots == 2:
                t_idx2 = t_idx + 1
                s_idx2 = s_idx
            if args.time:
                target_time = parse_time(args.time)
                if not target_time:
                    return
                print(f"等待到指定时间：{target_time}")
                wait_until(target_time)
            time_count = len(time_options)
            print(f"[调试] 当前时间段总数 time_count = {time_count}")
            period1 = base_time_id + t_idx
            sub_resource_id1 = base_sub_id + time_count * s_idx - t_idx
            if args.slots == 2:
                period2 = base_time_id + t_idx2
                sub_resource_id2 = base_sub_id + time_count * s_idx2 - t_idx2
            print(f"[调试] base_time_id = {base_time_id}, base_sub_id = {base_sub_id}")
            print(f"[调试] period1 = {period1}, sub_resource_id1 = {sub_resource_id1}")
            if args.slots == 2:
                print(f"[调试] period2 = {period2}, sub_resource_id2 = {sub_resource_id2}")
            if args.slots == 1:
                reservations = [
                    {
                        "date": target_date,
                        "period": period1,
                        "sub_resource_id": sub_resource_id1
                    }
                ]
            else:
                reservations = [
                    {
                        "date": target_date,
                        "period": period1,
                        "sub_resource_id": sub_resource_id1
                    },
                    {
                        "date": target_date,
                        "period": period2,
                        "sub_resource_id": sub_resource_id2
                    }
                ]
            # 从配置文件读取重试参数
            max_attempts = config.get('max_attempts', 1000)
            retry_delay = config.get('retry_delay', 0.1)
            request_timeout = config.get('request_timeout', 10)
            
            success = make_reservation(session, reservations, args.resource_id, max_attempts, retry_delay, request_timeout)
            if success:
                logger.info("预约成功！程序结束（命令行模式）")
                print("预约成功！程序结束")
                return
            else:
                logger.warning(f"第 {retry_count} 次尝试失败（命令行模式），{retry_interval}秒后重试...")
                print(f"第 {retry_count} 次尝试失败，{retry_interval}秒后重试...")
                time.sleep(retry_interval)
                
        except KeyboardInterrupt:
            logger.info("用户中断程序（命令行模式）")
            print("\n用户中断程序")
            return
        except Exception as e:
            logger.error(f"程序发生错误（命令行模式）：{str(e)}")
            print(f"程序发生错误：{str(e)}")
            print(f"第 {retry_count} 次尝试失败，{retry_interval}秒后重试...")
            time.sleep(retry_interval)
            
    logger.error(f"达到最大重试次数（{max_retries}次），程序结束（命令行模式）")
    print(f"达到最大重试次数（{max_retries}次），程序结束")

if __name__ == "__main__":
    main()
