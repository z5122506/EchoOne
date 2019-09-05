from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException
import getpass
import os.path
import time
import re
import sys


def enable_download_in_headless_chrome(driver, download_dir):
	# add missing support for chrome "send_command"  to selenium webdriver
	driver.command_executor._commands["send_command"] = ("POST", '/session/$sessionId/chromium/send_command')

	params = {'cmd': 'Page.setDownloadBehavior', 'params': {'behavior': 'allow', 'downloadPath': download_dir}}
	command_result = driver.execute("send_command", params)

def print_download_progress(filename):
	# JavaScript magic to get us through shadowroots
	download = driver.execute_script('''
			var tag = document.querySelector('downloads-manager').shadowRoot;
			return tag.querySelector('downloads-item').shadowRoot;
			''')
	elm = download.find_element_by_id("description")
	reg = re.match(r'(.*) - (.*) of (.*), (.*) left', elm.text)
	length = 20
	suffix = "                "
	curr = 1
	total = 1
	if (reg):
		suffix = reg.group(4) + " at " + reg.group(1)
		curr = float(reg.group(2).split(" ")[0].replace(",",""))
		total = float(reg.group(3).split(" ")[0].replace(",",""))

	filledLength = int(length * curr // total)
	bar = '=' * filledLength
	if (filledLength != length):
		bar = bar + '>' + ' ' * (length - filledLength - 1)
	print('\r%s |%s| %4.1f%% %s     ' % (filename, bar, 100*curr/total, suffix), end = '\r')
	sys.stdout.flush()
	
	

options = Options() 
#options.add_argument("--headless")
options.add_argument('--no-sandbox')
driver = webdriver.Chrome(options=options)
#driver = webdriver.Firefox(firefox_options = options)
driver.get("http://www.echo360.org.au")

# login to echo360
elem = driver.find_element_by_name("email")
elem.clear()

# It doesn't matter whos email it is
# Might fail if carlin williamson graduates
elem.send_keys("carlin.williamson@unsw.edu.au")
elem.send_keys(Keys.RETURN)

time.sleep(2)

# login to microsoft
elem = driver.find_element_by_id("userNameInput")
elem.clear()
elem.send_keys(input("UNSW zID: ") + "@ad.unsw.edu.au")
elem = driver.find_element_by_name("Password")
elem.clear()
elem.send_keys(getpass.getpass())
elem.send_keys(Keys.RETURN)

time.sleep(2)

# choose course
elms = driver.find_elements_by_tag_name("a")
elms = list(filter(lambda x:x.get_attribute("aria-label"), elms))
elms = list(filter(lambda x:len(x.get_attribute("aria-label")) > 10, elms))
print("Your Courses:")
print("	Course   Term LectureStream")
for i, elm in enumerate(elms):
	text = elm.get_attribute("aria-label")
	if (text is None or len(text) < 10):
		continue
	courseName = text.split(" - ")[1].split("/")[0]
	reg = re.match(r'\d{2}(\d{2})TP(\d)', text.split(" - ")[2])
	term = "{}T{}".format(reg.group(1), reg.group(2))
	reg = re.match(r'.*(\d)', text.split(" - ")[2])
	stream = reg.group(1)
	#print(text)
	print("{:2d}: {} {} {}".format(i, courseName, term, stream))

courseInput = int(input("\nSelect a Courses Corresponding Number: "))

elm = elms[courseInput]
courseName = elm.get_attribute("aria-label").split(" - ")[1].split("/")[0]
elm.click()

time.sleep(2)

# choose lecture video
elms = driver.find_elements_by_class_name("menu-opener")
print("Your Lectures:")
counter = 0
for elm in elms:
	matchObj = re.match( r'.*_(\d{4})-(\d{2})-(\d{2})T.*', elm.get_attribute("aria-controls"))
	if matchObj:
		print(matchObj.group(3) + "/" + matchObj.group(2) + "/" + matchObj.group(1) + ": " + str(counter))
		counter += 1

lectureInputStart = int(input("\nSelect First Lecture To Download: "))
lectureInputEnd = int(input("\nSelect Last Lecture To Download: "))

downloadHD = input("\nDownload High Definition video? (y/n): ")
downloadFolder = courseName
downloadName = "sd1.mp4"

print("\n")

if not os.path.exists(downloadFolder):
	os.mkdir(downloadFolder)
os.chdir(downloadFolder)

if (downloadHD == "y"):
	downloadName = "hd1.mp4"

for lecture in range(lectureInputStart, lectureInputEnd + 1):
	elms = driver.find_elements_by_class_name("courseMediaIndicator")
	elms[lecture].click()
	time.sleep(0.5)

	# open download page
	# The next line can fail if the lecture video isn't avaliable yet
	# i.e. the lecture is either recording or hasn't been uploaded yet
	elm = driver.find_element_by_partial_link_text("Download original")
	elm.click()
	time.sleep(1)

	# make the video hd
	if (downloadHD == "y"):
		elm = driver.find_elements_by_tag_name("option")[1]
		elm.click()
		time.sleep(0.5)

	#download the video
	enable_download_in_headless_chrome(driver, os.getcwd())
	elm = driver.find_element_by_class_name("downloadBtn")
	elm.click()

	#print("Downloading Lecture " + str(lecture+1))
	driver.get('chrome://downloads/')
	time.sleep(3)
	filename = "{}_{:02d}.mp4".format(courseName, lecture)
	while not os.path.exists(downloadName):
		print_download_progress(filename)
		time.sleep(0.25)
	time.sleep(0.25)
	print_download_progress(filename) # make sure we print the 100% message
	sys.stdout.write('\n')

	os.rename(downloadName, filename)
	driver.back()

driver.close()

# vim: set softtabstop=8
