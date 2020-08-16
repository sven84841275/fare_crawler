from selenium import webdriver
from selenium.common import exceptions
import pandas as pd
import datetime
import random
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.select import Select
import time
from selenium.webdriver.common.action_chains import ActionChains


# import os
# import traceback


# step 1
def set_driver(engine="chrome", is_headless=False):
    """
    设置web driver引擎

    :param engine: <str> web driver引擎，目前支持chrome和phantomjs
    :param is_headless: <bool> 是否开启无头模式
    :return: <object> driver对象
    """
    url = "https://www.ctrip.com/"
    if engine == "phantomjs":
        driver = webdriver.PhantomJS()
    else:
        if is_headless:
            options = webdriver.ChromeOptions()
            options.add_argument('headless')
            # 这个argument是设置浏览器窗口大小，与有视图模式时的设置是不一样的，有视图时可以直接最大化，但是headless是无法最大化的
            options.add_argument("--window-size=4000,1600")
            # 无头模式需要在此处传入options
            driver = webdriver.Chrome(options=options)
        else:
            driver = webdriver.Chrome()
            # 放大窗口是为了尽可能得使窗口显示更多的元素。如果元素不在窗口视野时，是无法点击或输入的。这点跟我们人工操作一样
            # 为了避免这些错误，所以要放大窗口
            driver.maximize_window()
    driver.get(url)
    return driver


# step 2
def get_fare(driver, dep_city, arr_city, dep_date, is_int=False, download_daily=False, has_child=False,
             has_infant=False):
    """
    获取当日票价数据

    :param driver: <object> driver对象
    :param dep_city: <str> 起飞城市三字码
    :param arr_city: <str> 到达城市三字码
    :param dep_date: <str> 起飞日期，格式为“YYYY-MM-DD”
    :param is_int: <bool> 是否为国际航班
    :param download_daily: <bool> 是否保存当天票价数据
    :param has_child: <bool> 有无儿童
    :param has_infant: <bool> 有无婴儿
    :return: fare_data: <dataframe> 当天票价数据
    """
    dep_city, arr_city = dep_city.lower(), arr_city.lower()
    # find_element_by_xxx是查找单个元素，返回的是一个元素; find_elements_by_xxx是查找多个元素，返回的是元素的list
    flight_tag = driver.find_element_by_id("searchBoxUl").find_elements_by_tag_name("li")[1]
    flight_tag.click()
    # step 8
    if is_int:
        driver.find_element_by_id("flightSwitch").find_elements_by_tag_name("a")[1].click()
        time.sleep(2 * random.random())
        driver.find_element_by_id("fl_search_type").find_element_by_id("fl_flight_way_s").click()
        dep_city_input = driver.find_element_by_id("fl_txtDCity")
        arr_city_input = driver.find_element_by_id("fl_dest_city_1")
        date_input = driver.find_element_by_id("fl_txtDDatePeriod1")
        if has_child:
            Select(driver.find_element_by_id("fl_ChildQuantity")).select_by_index(1)
        if has_infant:
            Select(driver.find_element_by_id("fl_InfantQuantity")).select_by_value("1")
    else:
        driver.find_element_by_id("FD_flightSubSwitch").find_elements_by_tag_name("input")[0].click()
        dep_city_input = driver.find_element_by_id("FD_StartCity")
        arr_city_input = driver.find_element_by_id("FD_DestCity")
        date_input = driver.find_element_by_id("FD_StartDate")
        # 解决search_button被日期选择框笼罩问题，是输入日期后直接按回车键，因此不需要用到search_button
        # search_button = driver.find_element_by_id("FD_StartSearch")
        if has_child:
            driver.find_element_by_id("FD_HasChild").click()
        if has_infant:
            driver.find_element_by_id("FD_HasChild").click()
    # step 3
    action = ActionChains(driver)

    # 给出发地的输入框（dep_city_input）输入我们要查询的出发地（dep_city）
    input_keys(driver, action, dep_city_input, dep_city)

    # 若不用input_keys函数，要输入出发地，是如下写法：
    # close_advertisement(driver)
    # driver.execute_script("arguments[0].focus();", dep_city_input)
    # dep_city_input.clear()
    # time.sleep(3 * random.random())
    # close_advertisement(driver)
    # dep_city_input.send_keys(dep_city)
    # time.sleep(3 * random.random())
    # action.key_down(Keys.ENTER).perform()
    # time.sleep(3 * random.random())

    # 同样地，下面还有输入目的地和输入日期两次输入，如果不用函数，要将上面的代码重复三次。因此使用函数会更加简洁。
    input_keys(driver, action, arr_city_input, arr_city)
    input_keys(driver, action, date_input, dep_date)

    # 隐式等待
    # driver.implicitly_wait(3)
    # 去除readonly
    # js = 'document.getElementById("datePicker").getElementsByTagName("input")[0].removeAttribute("readonly")'
    # driver.execute_script(js)
    # 修改value
    # arguments[0]可以帮我们把selenium的元素传入到JavaScript语句中，arguments指的是execute_script()方法中js代码后面的所有参数
    # arguments[0]表示第一个参数，argument[1]表示第二个参数
    # driver.execute_script("arguments[0].value = '%s'" % dep_date, date_input)

    # step 9
    if is_int:
        try:
            # 等待no-result-recommend-header加载完毕，最多等待3S，超时则会执行except
            # 这段语句return None，是因为如果加载出no-result-recommend-header，表示这个没有这条航线的数据。
            element = WebDriverWait(driver, 3).until(
                EC.presence_of_element_located((By.CLASS_NAME, "no-result-recommend-header"))
            )
            print("{} 没有搜索到航班".format(dep_date))
            driver.back()
            return None
        except:
            try:
                element = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.CLASS_NAME, "result-header"))
                )
            except:
                print("{} 加载数据超时，略过".format(dep_date))
                driver.back()
                return None
        close_alert_announce(driver)  # 关闭提示框函数
        # step 10
        fare_data = scroll_scan(driver)  # 滚动扫描函数
        columns = ["航班号", "起飞机场", "起飞时间", "到达机场", "到达时间", "到达日期", "最低票价"]
    # step 5
    else:
        try:
            element = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CLASS_NAME, "search_table_header"))
            )
        except:
            print("{} 加载数据超时，略过".format(dep_date))
            driver.back()
            return None
        # step 6
        close_alert_announce(driver)
        scroll_to_footer(driver)  # 滚动至页面底部函数
        flights = driver.find_elements_by_class_name("search_table_header")
        fare_data = []
        # step 7  提取数据的过程
        for flight in flights:
            flight_number = flight.find_element_by_class_name("logo-item.flight_logo").find_elements_by_tag_name("span")[2].text
            print("开始提取航班{}数据".format(flight_number))
            dep = flight.find_element_by_class_name("inb.right")
            dep_time = dep.find_element_by_class_name("time").text
            dep_airport = dep.find_element_by_class_name("airport").text
            arr = flight.find_element_by_class_name("inb.left")
            arr_time = arr.find_element_by_class_name("time").text
            time_delta = arr.find_elements_by_class_name("c-react-frame")
            if len(time_delta) != 0:
                time_delta = time_delta[0].text
            else:
                time_delta = ""
            arr_airport = arr.find_element_by_class_name("airport").text
            lowest_price = flight.find_element_by_class_name("inb.price.child_price").find_element_by_class_name(
                "base_price02").text[1:]
            fare_data.append((flight_number, dep_airport, dep_time, arr_airport, arr_time, time_delta, lowest_price))
        columns = ["航班号", "起飞机场", "起飞时间", "到达机场", "到达时间", "日期差", "最低票价"]

    # step 16
    fare_data = pd.DataFrame(fare_data, columns=columns)
    driver.back()  # 这里相当于点击了浏览器中的返回，为了方便下一次爬取
    if download_daily:
        try:
            fare_data.to_excel("{}_{}_{}.xlsx".format(dep_city, arr_city, dep_date))
        except PermissionError:
            print("{}_{}_{}.xlsx 文件正被使用，保存失败".format(dep_city, arr_city, dep_date))
        except Exception as e:
            print("{}_{}_{}.xlsx 文件保存时发生错误：{}，保存失败".format(dep_city, arr_city, dep_date, e))
    return fare_data


# step 4
def input_keys(driver, action, input_to, key):
    """
    用于键入查询值

    :param driver: <object> driver对象
    :param action: <object> action动作链对象
    :param input_to: <object> 键入目标输入框对象
    :param key: <str> 键入值
    :return: 无
    """
    close_advertisement(driver)  # 关闭广告
    driver.execute_script("arguments[0].focus();", input_to)
    input_to.clear()  # 清除原有值
    time.sleep(3 * random.random())
    close_advertisement(driver)
    input_to.send_keys(key)
    time.sleep(3 * random.random())
    action.key_down(Keys.ENTER).perform()  # 点击回车键，注意要用perform()方法，否则不会执行动作
    time.sleep(3 * random.random())


def close_alert_announce(driver):
    """
    用于关闭防疫公告

    :param driver: <object> driver对象
    :return: 无
    """
    try:
        notice_button = driver.find_element_by_class_name("btn-group").find_element_by_tag_name("a")
        notice_button.click()
        time.sleep(3 * random.random())
    except exceptions.NoSuchElementException as e:
        print(e.msg)
        pass


def close_advertisement(driver):
    """
    用于关闭弹出广告

    :param driver: <object> driver对象
    :return: 无
    """
    try:
        notice_button = driver.find_element_by_id("float_100_close")
        notice_button.click()
        time.sleep(3 * random.random())
    except:
        pass


def scroll_to_footer(driver):
    """
    针对国内航线页面动态加载特性，用于滚动页面至footer处，以完全加载数据

    :param driver: <object> driver对象
    :return: 无
    """
    body_height = driver.find_element_by_tag_name("body").size['height']  # 初始body的高度
    # js下拉方法
    # 下拉到底部
    # js = "arguments[0].scrollIntoView();"
    # driver.execute_script(js, footer)
    # 此方法不能解决问题，因为底部长度随着滚动下拉而增加，一次下拉无法到达
    init_height = 0
    count = 1
    while True:
        # 第一次从循环，init_height=0，从0-300。第二次循环300-600，第三次循环600-900，因此每次循环完毕都要增加init_height的值
        driver.execute_script("window.scrollTo(%d,%d);" % (init_height, init_height + 300))
        if count % 5 == 0:  # 求余运算
            current_body_height = driver.find_element_by_tag_name("body").size['height']  # 查看当前网页body的高度
            # 第一轮5次循环完后，如果当前body高度!=初始body高度，表示有数据被动态加载出来了，没有到达页面底部，还需要继续往下滚动
            # 往下滚动前，把当前body高度赋值给初始body高度，给下一的检查作为参考值
            if current_body_height != body_height:
                body_height = current_body_height
                init_height += 300
                count += 1
            else:
                time.sleep(2 * random.random())
                break
        else:
            init_height += 300
            count += 1


# step 11
def scroll_scan(driver):
    """
    针对国际航线页面动态加载特性，用于区间滚动票价页面

    :param driver: <object> driver对象
    :return: fare_data <list> 返回当日票价数据
    """
    body_height = driver.find_element_by_tag_name("body").size['height']  # 取出初始页面高度，跟国内页面同样的方法判断是否到底
    init_height = 0
    count = 1
    fare_data = {}
    while True:
        driver.execute_script("window.scrollTo(%d,%d);" % (init_height, init_height + 300))
        print("扫描中")
        # step 12 因国际航线动态加载并且还隐藏过期元素，因此需要每滚动一次，就执行get_flights函数提取一次视野范围内的数据
        get_flights(driver, fare_data)
        if count % 5 == 0:
            current_body_height = driver.find_element_by_tag_name("body").size['height']
            if current_body_height != body_height:
                body_height = current_body_height
                init_height += 300
                count += 1
            else:
                # step 15
                time.sleep(2 * random.random())
                print("整体页面扫描完毕")
                return list(fare_data.values())
        else:
            init_height += 300
            count += 1


# step 13
def get_flights(driver, fare_data):
    """
    针对国际航线网页动态加载特性，在页面滚动一定区间后，该函数用于提取国际航线的票价数据

    :param driver: <object> driver对象
    :param fare_data: <dict> 已取得的票价数据
    :return: 无
    """
    flights = driver.find_elements_by_class_name("flight-item")
    print("本次扫描提取出%d条航班信息" % len(flights))
    for flight in flights:
        try:
            flight_number = ""  # 先给flight number设置空值，方便拼接
            # 注意这里用find elements，因为国际客票有搜索出中转航线，会有多个航班号，因此我们判断flight_numbers（list）的长度
            # 如果大于1，则表示是联程，这里用拼接的方式将里面的航班号全部拼接在一起
            flight_numbers = flight.find_elements_by_class_name("plane-No")
            if len(flight_numbers) > 1:
                for single_flight_number in flight_numbers:
                    flight_number += single_flight_number.text + " "
            else:
                flight_number = flight_numbers[0].text
            if flight_number in fare_data.keys():
                print("航班{}数据已经存在，略过".format(flight_number))
                continue
            print("开始提取航班{}数据".format(flight_number))
            dep = flight.find_element_by_class_name("depart-box")
            dep_time = dep.find_element_by_class_name("time").text
            dep_airport = dep.find_element_by_class_name("airport").text
            arr = flight.find_element_by_class_name("arrive-box")
            arr_time = arr.find_element_by_class_name("time").text
            arr_airport = arr.find_element_by_class_name("airport").text
            flight_time = flight.find_element_by_class_name("flight-consume").text
            lowest_price = flight.find_element_by_class_name("flight-seats").find_element_by_class_name(
                "seat-row.seat-row-v3 ").find_element_by_class_name("price-box").text
            fare_data[flight_number] = (
            flight_number, dep_airport, dep_time, arr_airport, arr_time, flight_time, lowest_price)
            print("提取航班{}数据成功".format(flight_number))
        except exceptions.StaleElementReferenceException:
            print("提取信息所在元素已过时")
        # step 14
        except IndexError:
            print("未能提取到航班信息，需要重新定位")
            # driver.save_screenshot("I" + datetime.datetime.now().strftime("%Y%m%d%H%M%S") + ".png")


def make_date_list(start_date, end_date):
    """
    生成日期区间list

    :param start_date: <str> 起始日期，格式为：“YYYY-MM-DD”
    :param end_date: <str> 截止日期，格式为：“YYYY-MM-DD”
    :return: date_list: <list> 生成从起始日期开始，至截止日期为止的list（str元素，格式为“YYYY-MM-DD”）
    """
    date_list = []
    start_date = datetime.datetime.strptime(str(start_date), '%Y-%m-%d')
    end_date = datetime.datetime.strptime(str(end_date), '%Y-%m-%d')
    day_delta = (end_date - start_date).days + 1
    for days in range(day_delta):
        the_date = (start_date + datetime.timedelta(days=days)).strftime('%Y-%m-%d')
        date_list.append(the_date)
    return date_list


def get_fare_stack(driver, dep_city, arr_city, start_date, end_date, is_int=False, download_daily=False,
                   download_stack=False):
    """
    用于获取日期区间的价格数据

    :param driver: <object> driver对象
    :param dep_city: <str> 起飞城市三字码
    :param arr_city: <str> 到达城市三字码
    :param start_date: <str> 起始日期，格式为“YYYY-MM-DD”
    :param end_date: <str> 截止日期，格式为“YYYY-MM-DD”
    :param is_int: <bool> 是否为国际航线
    :param download_daily: <bool> 是否保存每日票价数据
    :param download_stack: <bool> 是否保存日期区间的整合票价数据
    :return: fare_stack <dataframe> 日期区间的整合票价数据
    """
    dep_city, arr_city = dep_city.lower(), arr_city.lower()
    date_list = make_date_list(start_date, end_date)
    fare_stack = pd.DataFrame(None)
    for dep_date in date_list:
        fare_data = get_fare(driver, dep_city, arr_city, dep_date, is_int, download_daily)
        if fare_data is None:
            continue
        if fare_data.shape[0] == 0:
            print("未搜索到{}该航线的票价！".format(dep_date))
            continue
        if fare_stack.shape[0] == 0:
            fare_stack = fare_data
        else:
            fare_stack = pd.concat([fare_stack, fare_data], axis=0, join='outer')
    if download_stack:
        try:
            fare_stack.to_excel("{}_{}_{}_{}.xlsx".format(dep_city, arr_city, start_date, end_date))
        except PermissionError:
            print("{}_{}_{}_{}.xlsx文件正被使用，保存失败".format(dep_city, arr_city, start_date, end_date))
        except Exception as e:
            print("{}_{}_{}_{}.xlsx文件保存时发生错误：{}，保存失败".format(dep_city, arr_city, start_date, end_date, e))
    return fare_stack


if __name__ == "__main__":
    driver = set_driver("chrome", True)
    get_fare(driver, "CAN", "SIN", "2021-03-23", is_int=True, download_daily=True)
    driver.quit()
    # get_fare_stack(driver, "CAN", "SIN", "2020-06-12", "2020-06-15", is_int=True, download_daily=False, download_stack=True)
    # driver.quit()
