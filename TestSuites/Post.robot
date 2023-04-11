*** Settings ***
Library   ButlerRobot.AIBrowserLibrary  fix_bbox=${TRUE}  strict=${FALSE}  enable_presenter_mode=${TRUE}  show_keyword_call_banner=${TRUE}  AS  Browser
Library   ButlerRobot.CrawlLibrary


*** Variables ***
${user}  elon.musk@gmail.com
${password}  1234


*** Test Cases ***
Create a post
    Open Browser  http://hpc.etsii.urjc.es:4200  pause_on_failure=${FALSE}
	Start Task  Click on MyMessages logo
	Record Click
	End Task

Crawl
    Open Browser  http://hpc.etsii.urjc.es:4200  pause_on_failure=${FALSE}
	Crawl  http://hpc.etsii.urjc.es:4200  1000


*** Keywords ***
Go to sign up
    Click  xpath=/html/body/app-root/app-header/mat-toolbar/ul/li[2]/a

Click on Login
    Click  xpath=/html/body/app-root/app-header/mat-toolbar/ul/li[1]/a

Singup with user ${user} and password ${password}
	Click  //*[@type="email"]  position_x=125  position_y=9.54166
	Keyboard Input  type  ${user}
	Click  //*[@type="password"]  position_x=30  position_y=4.7083
	Keyboard Input  type  ${password}
	Click  //*[@type="submit"]/span  position_x=12  position_y=0


Login with user ${user} and pass ${password}
	Click  //*[@type="email"]  
	Keyboard Input  type  ${user}
	Click  //*[@type="password"]  
	Keyboard Input  type  ${password}
	Click  //*[@type="submit"]/span  position_x=12  position_y=0

Create a post
    Click  xpath=/html/body/app-root/app-header/mat-toolbar/ul/li[1]/a/span

Type title ${title}
	Click  //*[@type="text"]  position_x=149.8645782470703  position_y=3.5416641235351562
	Keyboard Input  type  ${title}
	
Upload image
    Upload File By Selector  //*[@type="file"]  ${CURDIR}/images/FullPage.png

# Debug
Type ${content} on content
	Click  //textaera  position_x=68.86457824707031  position_y=49.375
	Keyboard Input  type  Contenido del post

Submit
	Click  //*[@type="submit"]  position_x=42.86457824707031  position_y=2.916656494140625

Change Page Size To ${size}
	Click  //*[@class="mat-select-value ng-tns-c93-5"]  position_x=33.98956298828125  position_y=4.25
	Click  text=${size}  position_x=28.98956298828125  position_y=16.25

Expand Post
	Click  text=Post creado

Delete Post
	Click  text=DELETE  position_x=29.1041259765625  position_y=0.6666259765625

Edit Post
	Click  text=DELETE

Click on MyMessages logo
    Click  text=MyMessages