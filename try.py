import requests
import time
import datetime
import socket
import json
import re
import argparse
import os
import sys

def test_connection():
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)
        sock.connect(('eportal.hnu.edu.cn', 443))
        sock.close()
        return True
    except:
        return False

def login(username, password):
    # 首先获取登录页面，获取execution参数
    session = requests.Session()
    login_url = "http://cas.hnu.edu.cn/cas/login?service=https%3A%2F%2Feportal.hnu.edu.cn%2Fsite%2Flogin%2Fcas-login%3Fredirect_url%3Dhttps%253A%252F%252Feportal.hnu.edu.cn%252Fv2%252Fsite%252Findex"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
        "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive"
    }
    
    try:
        print("获取登录页面...")
        response = session.get(login_url, headers=headers)
        print(f"登录页面响应状态码：{response.status_code}")
        
        # 从响应中提取execution参数
        execution_match = re.search(r'name="execution" value="([^"]+)"', response.text)
        if not execution_match:
            print("无法获取execution参数")
            return None
            
        execution = execution_match.group(1)
        print(f"获取到execution参数：{execution}")
        
        # 发送登录请求
        login_data = {
            "username": username,
            "password": password,
            "execution": execution,
            "_eventId": "submit",
            "geolocation": "",
            "service": "https://eportal.hnu.edu.cn/site/login/cas-login?redirect_url=https%3A%2F%2Feportal.hnu.edu.cn%2Fv2%2Fsite%2Findex"
        }
        
        print("发送登录请求...")
        response = session.post(login_url, headers=headers, data=login_data, allow_redirects=True)
        print(f"登录响应状态码：{response.status_code}")
        print(f"登录响应URL：{response.url}")
        
        if "eportal.hnu.edu.cn" in response.url:
            print("登录成功！")
            return session
        else:
            print("登录失败，请检查用户名和密码")
            print(f"响应内容：{response.text}")
            return None
            
    except Exception as e:
        print(f"登录请求失败：{str(e)}")
        return None

def make_reservation(session, reservations, resource_id):
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
        
        start_time = datetime.datetime.now()
        max_wait_time = 30
        attempt_count = 0
        
        while True:
            attempt_count += 1
            current_time = datetime.datetime.now()
            elapsed_time = (current_time - start_time).total_seconds()
            
            if elapsed_time > max_wait_time:
                print(f"\n超过最大等待时间（{max_wait_time}秒），停止尝试")
                return False
                
            response = session.post(reserve_url, headers=reserve_headers, data=data, timeout=10)
            
            try:
                result = response.json()
                
                if result.get('e') == 0:
                    print(f"\n预约成功！预约ID：{result['d']['appointment_id']}")
                    return True
                else:
                    error_msg = result.get('m', '未知错误')
                    if error_msg in ["参数错误", "预约日期未达到"]:
                        time.sleep(0.1)
                        continue
                    print(f"\n预约失败：{error_msg}")
                    return False
            except:
                time.sleep(0.1)
                continue
            
    except Exception as e:
        print(f"预约请求失败：{str(e)}")
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

def main():
    config = load_config()
    if not config:
        print("错误：无法读取配置文件，请确保config.json存在且格式正确")
        return
    
    # 如果没有命令行参数，直接使用配置文件中的参数
    if len(sys.argv) == 1:
        print("使用配置文件中的参数进行预约")
        username = config.get('username')
        password = config.get('password')
        resource_id = config.get('resource_id')
        slots = config.get('slots', 1)
        date = config.get('date')
        period1 = config.get('period1')
        sub_resource_id1 = config.get('sub_resource_id1')
        period2 = config.get('period2')
        sub_resource_id2 = config.get('sub_resource_id2')
        
        # 检查必填参数
        missing_params = []
        if not username:
            missing_params.append("学号")
        if not password:
            missing_params.append("密码")
        if not resource_id:
            missing_params.append("预约资源ID")
        if not period1:
            missing_params.append("第一个时间段ID")
        if not sub_resource_id1:
            missing_params.append("第一个台号ID")
        if slots == 2:
            if not period2:
                missing_params.append("第二个时间段ID")
            if not sub_resource_id2:
                missing_params.append("第二个台号ID")
            
        if missing_params:
            print("错误：以下参数为必填项：")
            for param in missing_params:
                print(f"- {param}")
            print("\n请在config.json中配置这些参数")
            return
            
        try:
            current_time = datetime.datetime.now()
            
            if not test_connection():
                print("网络连接测试失败，请检查网络")
                return
                
            print(f"使用学号：{username} 进行登录...")
            session = login(username, password)
            
            if not session:
                print("登录失败，程序退出")
                return
                
            target_date = date if date else current_time.strftime("%Y-%m-%d")
            target_datetime = datetime.datetime.strptime(target_date, "%Y-%m-%d")
            current_datetime = datetime.datetime.now()
            
            target_date_only = target_datetime.date()
            current_date_only = current_datetime.date()
            days_diff = (target_date_only - current_date_only).days
            
            if days_diff < 0:
                print("错误：预约日期不能是过去的日期")
                return
            elif days_diff > 7:
                print("错误：预约日期太早，系统只允许提前7天预约")
                return
                
            if slots == 1:
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
            
            success = make_reservation(session, reservations, resource_id)
            
            if success:
                print("预约成功！")
            else:
                print("预约失败")
                
        except Exception as e:
            print(f"程序发生错误：{str(e)}")
            print("程序结束")
        return
    
    # 如果有命令行参数，使用命令行参数
    parser = argparse.ArgumentParser(description='体育馆预约程序')
    parser.add_argument('--time', type=str, help='预约开始时间，格式：YYYY-MM-DD HH:MM:SS')
    parser.add_argument('--date', type=str, default=config.get('date'), help='预约日期，格式：YYYY-MM-DD')
    parser.add_argument('--username', type=str, default=config.get('username'), help='学号')
    parser.add_argument('--password', type=str, default=config.get('password'), help='密码')
    parser.add_argument('--resource_id', type=str, default=config.get('resource_id'), help='预约资源ID')
    parser.add_argument('--slots', type=int, choices=[1, 2], default=config.get('slots', 1), help='预约时间段数量：1或2（默认1）')
    parser.add_argument('--period1', type=str, default=config.get('period1'), help='第一个时间段ID')
    parser.add_argument('--sub_resource_id1', type=str, default=config.get('sub_resource_id1'), help='第一个台号ID')
    parser.add_argument('--period2', type=str, default=config.get('period2'), help='第二个时间段ID')
    parser.add_argument('--sub_resource_id2', type=str, default=config.get('sub_resource_id2'), help='第二个台号ID')
    args = parser.parse_args()

    missing_params = []
    if not args.username:
        missing_params.append("学号")
    if not args.password:
        missing_params.append("密码")
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
    
    try:
        current_time = datetime.datetime.now()
        
        if not test_connection():
            print("网络连接测试失败，请检查网络")
            return
            
        print(f"使用学号：{args.username} 进行登录...")
        session = login(args.username, args.password)
        
        if not session:
            print("登录失败，程序退出")
            return
            
        if args.time:
            target_time = parse_time(args.time)
            if not target_time:
                return
            print(f"等待到指定时间：{target_time}")
            wait_until(target_time)
            
        target_date = args.date if args.date else current_time.strftime("%Y-%m-%d")
        target_datetime = datetime.datetime.strptime(target_date, "%Y-%m-%d")
        current_datetime = datetime.datetime.now()
        
        target_date_only = target_datetime.date()
        current_date_only = current_datetime.date()
        days_diff = (target_date_only - current_date_only).days
        
        if days_diff < 0:
            print("错误：预约日期不能是过去的日期")
            return
        elif days_diff > 7:
            print("错误：预约日期太早，系统只允许提前7天预约")
            return
            
        if args.slots == 1:
            reservations = [
                {
                    "date": target_date,
                    "period": args.period1,
                    "sub_resource_id": args.sub_resource_id1
                }
            ]
        else:
            reservations = [
                {
                    "date": target_date,
                    "period": args.period1,
                    "sub_resource_id": args.sub_resource_id1
                },
                {
                    "date": target_date,
                    "period": args.period2,
                    "sub_resource_id": args.sub_resource_id2
                }
            ]
        
        success = make_reservation(session, reservations, args.resource_id)
        
        if success:
            print("预约成功！")
        else:
            print("预约失败")
            
    except Exception as e:
        print(f"程序发生错误：{str(e)}")
        print("程序结束")

if __name__ == "__main__":
    main()
