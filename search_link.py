# 5/12/2020 Nick Gabriel

from time import sleep
import datetime
from os import sys, path
import os
from shutil import copy as cp
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
import traceback, logging, configparser


import numpy as np
from numpy.random import randint
import pandas as pd
from bs4 import BeautifulSoup

from ct_utils import fb_login, get_driver


def search_links(links_file, rootdir):
    rtic = lambda n: randint(1, n)  # lag to simulate manual data collection

    ### get FB/CrowdTangle username and password from INI file
    config_file = path.expanduser("~/config.ini")
    config = configparser.ConfigParser()
    config.read(config_file)
    username = "nickgabriel8"  # config['CrowdTangle']['username']
    password = config["CrowdTangle"]["password"]

    ### selenium driver setup
    browser = "chrome"
    driver = get_driver(browser)
    driver.implicitly_wait(4)  # doesn't work for me but may work for you

    fb_login(driver, username, password)
    driver.get("https://apps.crowdtangle.com/search/home")
    sleep(4 + rtic(4))

    ### build directory structure to write data
    outdir = rootdir + "out_search"
    if not (os.path.exists(outdir)):
        os.mkdir(outdir)
    dt_string = datetime.datetime.now().strftime("%d-%m-%Y_%H_%M_%S")
    write_dir = outdir + "/" + dt_string
    os.mkdir(write_dir)
    cp(links_file, write_dir)

    links_df = pd.read_csv(links_file, index_col=0)
    indices = list(links_df.index)
    links = list(links_df.links)

    for idx, link in zip(indices, links):

        try:
            clear_button = driver.find_element(
                By.XPATH, '//div[starts-with(@class,"searchBar__clearBtn")]'
            )
            clear_button.click()
        except:
            pass

        search_box = driver.find_element(
            By.XPATH, '//input[starts-with(@class,"searchBar")]'
        )
        search_box.click()
        search_box.send_keys(link)
        search_box.send_keys(Keys.ENTER)
        # return driver
        sleep(30 + rtic(10))

        platforms = driver.find_element(
            By.CLASS_NAME, "react-tab-container"
        ).find_elements(By.TAG_NAME, "div")
        write_path = write_dir + "/" + "link_" + str(idx)
        os.mkdir(write_path)
        df = {}
        for element in platforms:
            name = element.text
            element.click()
            sleep(10 + rtic(10))

            try:
                table = driver.find_element(
                    By.XPATH, '//div[starts-with(@class,"searchResultsTable")]'
                )
            except:
                print(f"Error finding table for platform {name} and link {link}")
                continue
            source = table.get_attribute("outerHTML")
            soup = BeautifulSoup(source, "html.parser")

            rows = soup.find_all("div", class_="searchResultsTable__row--3QpGF")
            print(f"Found {len(rows)} rows for {name}")
            data = []
            for row in rows:
                try:
                    page_name = (
                        row.find("span", class_="fb-react-post-name-span").text
                        if row.find("span", class_="fb-react-post-name-span")
                        else ""
                    )
                    message = (
                        row.find(
                            "div", class_="searchResultsTable__messageContainer--DuJz0"
                        ).text
                        if row.find(
                            "div", class_="searchResultsTable__messageContainer--DuJz0"
                        )
                        else ""
                    )
                    date = (
                        row.find("p", class_="searchResultsTable__date--Qzbax").text
                        if row.find("p", class_="searchResultsTable__date--Qzbax")
                        else ""
                    )
                    interactions = (
                        row.find(
                            "p", class_="searchResultsTable__interactionCount--1uvOf"
                        ).text
                        if row.find(
                            "p", class_="searchResultsTable__interactionCount--1uvOf"
                        )
                        else ""
                    )
                    external_link = (
                        row.find("a", href=True)["href"]
                        if row.find("a", href=True)
                        else ""
                    )
                    data.append([page_name, message, date, interactions, external_link])
                except Exception as e:
                    print(
                        f"Error processing row for platform {name} and link {link}: {e}"
                    )
                    continue

            df[name] = pd.DataFrame(
                data,
                columns=[
                    "page_name",
                    "message",
                    "date",
                    "interactions",
                    "external_link",
                ],
            )

            df[name].to_csv(write_path + "/" + name + ".csv")

    driver.close()


if __name__ == "__main__":

    rootdir = "./"
    links_file = "links.csv"
    search_links(links_file, rootdir)
