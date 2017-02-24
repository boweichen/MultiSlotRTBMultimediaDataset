# Multi-Slot RTB Multimedia Datasets 

## Data Description

This data description contains two parts:
* Overview of the dataset
* Design of data crawler

**Overview:**

This dataset aims to investigate the trade-off among stakeholders in Real-Time bidding. We have collected data from Yahoo and MSN over the period from 20 January to 30 January in 2017 to construct our multimedia datasets. All the multimedia datasets were collected in Singapore. For each platform, we designed two types of data crawlers：Crawler type (I) started from a given seed URL, and used breadth-first-search to collect as many different webpages as possible; Crawler type (II) repeatedly accessed to a set of particular webpages at a frequency of every 5 minutes. To ensure the diversity of our collected webpage and ad, we specified the webpage URLs as following:

Yahoo I: 
-	https://sg.yahoo.com

Yahoo II:
-	https://sg.yahoo.com/
-	https://sg.news.yahoo.com/
-	https://sg.finance.yahoo.com/
-	https://sg.sports.yahoo.com/
-	https://sg.style.yahoo.com/tagged/celebrity
-	https://sg.style.yahoo.com/tagged/movies
-	http://travelinspirations.yahoo.com
-	https://sg.answers.yahoo.com/

MSN I: 
-	http://www.msn.com/en-sg/

MSN II:
-	http://www.msn.com/en-sg/
-	http://www.msn.com/en-sg/news
-	http://www.msn.com/en-sg/entertainment
-	http://www.msn.com/en-sg/sport
-	http://www.msn.com/en-sg/money
-	http://www.msn.com/en-sg/lifestyle
-	http://www.msn.com/en-sg/foodanddrink
-	http://www.msn.com/en-sg/travel
-	http://www.msn.com/en-sg/health
-	http://www.msn.com/en-sg/cars

Since Yahoo and MSN adopt different ad-networks, we store the four collected data separately. Each of Yahoo I, Yahoo II, MSN I and MSN II dataset has two folders, two .json files and one _crawler.py file:
       ./webpage_image/: contains all the webpage-images under the corresponding platform
       ./ad_image/: contains all the ad-images in the displayed webpages. 
       ./webpage.json: contains textual information of collected webpages
       ./ad.json: contains textual information of collected ads within each displayed webpage.
	 ./_crawler.py: the data crawler to collect webpage and ad data.  

For ./webpage.json, the textual information of each webpage is:
     webpage_ID:
     webpage_url:
     webpage_title:
     webpage_keywords: which can be found from the source of the webpage
     webpage_description: which can be found from the source of the webpage
     webpage_text: we collect all the text within the webpage
     webpage_ad_id_list: which can be used to find the displayed ads from ./ad.json file
     webpage_ad_location_list: the location of displayed ads.

For ./ad.json, the textual information of each ad is:
     ad_ID:
     ad_URL:
     ad_title:
     ad_keywords: which can be found from the source of the ad landing webpage
     ad_description: which can be found from the source of the ad landing webpage
     ad_text: we collect all the text within the ad landing page
     ad_location: the location of this ad

For each sub-folder under ./ad_image/ :
We grouped the advertisers and ads according to their textual information and visual image. Each group can be viewed as a unique advertiser, and the name of the sub-folder can be viewed as the advertiser’s ID. The .jpg images under this folder are the unique images associated with this advertiser, and the .jpg images under the sub-sub-folder ./raw_ad_image/ are the original displayed ads in the webpage. 

Note that: 

1) We set the Chromedriver in the privacy model, which disables browsing history, web cache and data storage in the cookies so that the collected ads are not affected by the pervious page views.

2) In ./ad_image/ and ./ad.json , you may notice that some ads with different ad_IDs share the same content, this is because: those ads appeared from time to time.  We did not distinguish unique ads in our data crawler, and we did it in our data pre-processing instead. 
 
Data Crawler:
We implement the crawler with Python2.7, Selenium and Chromedriver, and the source code can be found in: 
./crawler_I/yahoo/yahoo_crawler.py
./crawler_II/yahoo/yahoo_crawler.py
./crawler_I/msn/msn_crawler.py
./crawler_II/msn/msn_crawler.py

To help you better understand our code, I will explain three important variables: collecting_webpage_urls: store the webpage URL candidates that is under collecting; to_be_colleccted_webpage_urls: store the new webpage URL candidates; collected_webapge_urls: store all the collect webpage URLs. 

**We design our crawler as follows:** 

Crawler type I:

Step1: initialize some variables, such as starting chromedriver, setting collecting_webpage_urls as seed_url setting to_be_colleccted_webpage_urls as empty,  setting collected_webapge_urls as empty.

Step2: for a webpage URL in colleccting_webpage_urls, in order to remove repetitive webpages , we first check whether it is in collected_webpage_urls. If yes, select the next webpage URL candidate. If not, go to step 3. Once we have traversed colleccting_webpage_urls, we will set it as to_be_collected_webpage_urls and set to_be_colleccted_webpage_urls as empty. 

Step3: for a new webpage URL, we first add it to collected_webapge_urls. And then we select all new URLs that belong to Yahoo/MSN within the webpage and add them to  to_be_colleccted_webpage_urls. If there exist an ad in the webpage, go to Step 4. If not, go to step 2.

Step4: For each detected ad, we collect the ad_image by cropping screen, and then we perform ‘clicking-ad’ action and transfer to the ad landing page. We collect textual information of the ads in the ad landing page, and save them in ./ad.json. Then, go to Step5.
Step5: we return to the original webpage, and collect the visual and textual information of the webpage, and save it to ./webpage_image/ and ./webpage.json.   

Crawler type II:

Compared with crawler type II, we did not have to add new webpages URLs in step 2 and step 3. We just repetitively access to the specified webpage sets. 

Note that: 
1)	When capture the webpage image, we snapshot the full webpage rather than partial of the webpage. 

## Data Download
[Link](https://137.132.145.252:5001/fbsharing/NuUWWDHX) (13.2GB)

## Contact 
- Chen Xiang: [chxiang@comp.nus.edu.sg](mailto:chxiang@comp.nus.edu.sg)
- Bowei Chen: [bchen@lincoln.ac.uk](mailto:bchen@lincoln.ac.uk) 



