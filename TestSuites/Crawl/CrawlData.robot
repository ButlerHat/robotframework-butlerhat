*** Settings ***
Documentation     Crawl most used websites in EU
Library   ButlerRobot.AIBrowserLibrary  AS  Browser
Library      ButlerRobot.CrawlLibrary  AS  CrawlLibrary

*** Variables ***
${OUTPUT_DIR}   /workspaces/ia-butlerhat/data-butlerhat/robotframework-butlerhat/TestSuites/Crawl

*** Test Cases ***

Amazon
    [Documentation]    Crawl the data browser
    [Tags]    data_browser

    Open Browser  https://amazon.com  pause_on_failure=False
    CrawlLibrary.Crawl  https://www.amazon.com  6


Google
    [Documentation]    Crawl the data browser
    [Tags]    data_browser

    Open Browser  https://www.google.com/search?q=tesla  pause_on_failure=False
    CrawlLibrary.Crawl  https://www.google.com  2

Facebook
    [Documentation]    Crawl the data browser
    [Tags]    data_browser

    Open Browser  https://facebook.com  pause_on_failure=False
    CrawlLibrary.Crawl  https://www.facebook.com  2

Twitter
    [Documentation]    Crawl the data browser
    [Tags]    data_browser

    Open Browser  https://twitter.com  pause_on_failure=False
    CrawlLibrary.Crawl  https://www.twitter.com  2

LinkedIn2
    [Documentation]    Crawl the data browser
    [Tags]    data_browser

    Open Browser  https://linkedin.com  pause_on_failure=False
    CrawlLibrary.Crawl  https://www.linkedin.com  2

Reddit
    [Documentation]    Crawl the data browser
    [Tags]    data_browser

    Open Browser  https://reddit.com  pause_on_failure=False
    CrawlLibrary.Crawl  https://www.reddit.com  2

Wikipedia
    [Documentation]    Crawl the data browser
    [Tags]    data_browser

    Open Browser  https://en.wikipedia.org/wiki/Main_Page  pause_on_failure=False
    CrawlLibrary.Crawl  https://www.wikipedia.com  2

StackOverflow
    [Documentation]    Crawl the data browser
    [Tags]    data_browser

    Open Browser  https://stackoverflow.com  pause_on_failure=False
    CrawlLibrary.Crawl  https://www.stackoverflow.com  2

YouTube
    [Documentation]    Crawl the data browser
    [Tags]    data_browser

    Open Browser  https://youtube.com  pause_on_failure=False
    CrawlLibrary.Crawl  https://www.youtube.com  2

GitHub
    [Documentation]    Crawl the data browser
    [Tags]    data_browser

    Open Browser  https://github.com  pause_on_failure=False
    CrawlLibrary.Crawl  https://www.github.com  2

Instagram
    [Documentation]    Crawl the data browser
    [Tags]    data_browser

    Open Browser  https://instagram.com  pause_on_failure=False
    CrawlLibrary.Crawl  https://www.instagram.com  2

Pinterest
    [Documentation]    Crawl the data browser
    [Tags]    data_browser

    Open Browser  https://pinterest.com  pause_on_failure=False
    CrawlLibrary.Crawl  https://www.pinterest.com  2

Yahoo
    [Documentation]    Crawl the data browser
    [Tags]    data_browser

    Open Browser  https://yahoo.com  pause_on_failure=False
    CrawlLibrary.Crawl  https://www.yahoo.com  2

Bing
    [Documentation]    Crawl the data browser
    [Tags]    data_browser

    Open Browser  https://bing.com  pause_on_failure=False
    CrawlLibrary.Crawl  https://www.bing.com  2

Yelp
    [Documentation]    Crawl the data browser
    [Tags]    data_browser

    Open Browser  https://yelp.com  pause_on_failure=False
    CrawlLibrary.Crawl  https://www.yelp.com  2

Ebay
    [Documentation]    Crawl the data browser
    [Tags]    data_browser

    Open Browser  https://ebay.com  pause_on_failure=False
    CrawlLibrary.Crawl  https://www.ebay.com  2

Walmart
    [Documentation]    Crawl the data browser
    [Tags]    data_browser

    Open Browser  https://walmart.com  pause_on_failure=False
    CrawlLibrary.Crawl  https://www.walmart.com  2

Target
    [Documentation]    Crawl the data browser
    [Tags]    data_browser

    Open Browser  https://target.com  pause_on_failure=False
    CrawlLibrary.Crawl  https://www.target.com  2

BestBuy
    [Documentation]    Crawl the data browser
    [Tags]    data_browser

    Open Browser  https://bestbuy.com  pause_on_failure=False
    CrawlLibrary.Crawl  https://www.bestbuy.com  2

Apple
    [Documentation]    Crawl the data browser
    [Tags]    data_browser

    Open Browser  https://apple.com  pause_on_failure=False
    CrawlLibrary.Crawl  https://www.apple.com  2

Microsoft
    [Documentation]    Crawl the data browser
    [Tags]    data_browser

    Open Browser  https://microsoft.com  pause_on_failure=False
    CrawlLibrary.Crawl  https://www.microsoft.com  2

Adobe
    [Documentation]    Crawl the data browser
    [Tags]    data_browser

    Open Browser  https://adobe.com  pause_on_failure=False
    CrawlLibrary.Crawl  https://www.adobe.com  2

# Paginas para desarrolladores
W3Schools1
    [Documentation]    Crawl the data browser
    [Tags]    data_browser

    Open Browser  https://w3schools.com  pause_on_failure=False
    CrawlLibrary.Crawl  https://www.w3schools.com  2

W3Schools2
    [Documentation]    Crawl the data browser
    [Tags]    data_browser

    Open Browser  https://w3schools.com  pause_on_failure=False
    CrawlLibrary.Crawl  https://www.w3schools.com  2

Mozilla Developer Network
    [Documentation]    Crawl the data browser
    [Tags]    data_browser

    Open Browser  https://developer.mozilla.org/en-US/  pause_on_failure=False
    CrawlLibrary.Crawl  https://www.developer.mozilla.org  2

Microsoft Developer Network
    [Documentation]    Crawl the data browser
    [Tags]    data_browser

    Open Browser  https://msdn.microsoft.com/en-us/library/  pause_on_failure=False
    CrawlLibrary.Crawl  https://www.msdn.microsoft.com  2

Free Code Camp
    [Documentation]    Crawl the data browser
    [Tags]    data_browser

    Open Browser  https://freecodecamp.org  pause_on_failure=False
    CrawlLibrary.Crawl  https://www.freecodecamp.org  2

SitePoint 
    [Documentation]    Crawl the data browser
    [Tags]    data_browser

    Open Browser  https://sitepoint.com  pause_on_failure=False
    Browser.Click  //button[./span[text()='AGREE']]
    CrawlLibrary.Crawl  https://www.sitepoint.com  2




