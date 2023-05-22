*** Settings ***
Library   ButlerRobot.AIBrowserLibrary  fix_bbox=${TRUE}  output_path=${OUTPUT_DIR}/crawl_amazon_data  WITH NAME  Browser


*** Variables ***
${OUTPUT_DIR}  /workspaces/ai-butlerhat/data-butlerhat/robotframework-butlerhat/TestSuites/CicloZero/robotframework/modeling

*** Test Cases ***
Iframe Scroll
    New Browser    chromium    headless=false  downloadsPath=${OUTPUT_DIR}${/}downloads
    New Context    acceptDownloads=${TRUE}
    New Page   file:///workspaces/ai-butlerhat/data-butlerhat/robotframework-butlerhat/TestSuites/CicloZero/robotframework/modeling/iframe_training/index.html
    
    ${bbox}  Element Bbox  //iframe >>> //*[text()='Eric']
    ${text}  Get Text From Bbox    ${bbox}