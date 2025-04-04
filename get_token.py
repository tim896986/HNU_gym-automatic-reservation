import requests
import json
import urllib3

# 禁用SSL警告
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def get_login_info():
    # 登录URL
    login_url = 'https://eportal.hnu.edu.cn/v2/reserve/hallView'
    
    # 请求头
    headers = {
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36 Edg/134.0.0.0",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
        "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6",
        "Accept-Encoding": "gzip, deflate, br, zstd",
        "Connection": "keep-alive",
        "Host": "eportal.hnu.edu.cn",
        "Referer": "http://cas.hnu.edu.cn/",
        "Cookie": "UM_distinctid=1950e5aeee8d77-04271b8a2cbb4b-4c657b58-168000-1950e5aeee912d1; PHPSESSID=ST-792-0xKUC69A90jieD3kBXKi-zfsoftcom; vjuid=288482; vjvd=f6f4ee89f6daa4d90f335f5a2b502590; vt=259452869; cas_ticket=ST-792-0xKUC69A90jieD3kBXKi-zfsoft.com"
    }
    
    try:
        # 发送请求，禁用SSL验证和代理
        session = requests.Session()
        session.trust_env = False  # 禁用系统代理
        
        # 添加查询参数
        params = {
            "id": "10"
        }
        
        response = session.get(login_url, params=params, headers=headers, verify=False)
        
        # 打印响应状态码
        print(f"状态码: {response.status_code}")
        
        # 打印响应头
        print("\n响应头:")
        for key, value in response.headers.items():
            print(f"{key}: {value}")
        
        # 打印响应内容
        print("\n响应内容:")
        print(response.text[:500])  # 只打印前500个字符，避免输出太多
        
        # 保存响应到文件
        with open('response.html', 'w', encoding='utf-8') as f:
            f.write(response.text)
            
    except Exception as e:
        print(f"发生错误: {str(e)}")

if __name__ == "__main__":
    get_login_info() 