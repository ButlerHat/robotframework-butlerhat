from Browser import Browser
from robot.libraries.BuiltIn import RobotNotRunningError
from .DataBrowserLibrary import DataBrowserLibrary
from .RecordersLibraries import SingleClickRecorder, TypeTextRecorder
from robot.libraries.BuiltIn import BuiltIn


class CrawlLibrary:
    """
    This library uses DataBrowserLibrary to record all the actions 
    that are executed in the browser while crawling a website.
    It needs to import DataBrowserLibrary before using it.

    It implements the logic of the crawl process. The crawl consist en two steps:
    - Crawl: Navigate through the website pages.
    - Record: For each page, record all the actions with the recorders. This recorders 
        make actions on the page to capture the data.

    The recorders make an action an then restore the page to the original state. The recorders are:
    - SingleClickRecorder: Click on a single element and restore to the original page.
    - TypeTextRecorder: Type text with multiple words of the vocabulary and restore to the original page.
    """
    ROBOT_LIBRARY_SCOPE = 'GLOBAL'

    def __init__(self, ocr_url=None, lang_instructions: str = "en", supervise_crop: bool = False):
        try:
            lib: DataBrowserLibrary = BuiltIn().get_library_instance('Browser')
            lib.add_task_library('CrawlLibrary')
            # Add recorders to record tasks
            lib.add_task_library('SingleClickRecorder')
            lib.add_task_library('TypeTextRecorder')
        except RobotNotRunningError:
            return
        if lib is None:
            raise Exception('Could not import DataBrowserLibrary')
        if ocr_url is not None:
            BuiltIn().set_global_variable('${OCR_URL}', ocr_url)
        self._library: Browser = lib._library  # Need to access the private library to no record all.
        self._lang_instructions = lang_instructions
        self.recorders = ['click', 'type']
        self._max_elements = -1
        self.click_xpath = ['//a', '//button', '//input[@type="submit"]', '//input[@type="button"]', '//input[@type="image"]', '//input[@type="reset"]', '//input[@type="file"]', '//input[@type="checkbox"]', '//input[@type="radio"]', '//input[@type="hidden"]', '//select', '//option', '//optgroup', '//label']
        self.type_xpath = ['//input[@type="text"]', '//input[@type="password"]', '//input[@type="email"]', '//input[@type="number"]', '//input[@type="tel"]', '//input[@type="url"]', '//input[@type="search"]', '//textarea']
        self.supervise_crop = supervise_crop
        self.previous_keyword = None
        self.previous_keyword_args = None


    # ======= Task Keywords =======
    def crawl_clicks(
            self,
            url,
            max_number_of_page_to_crawl=1, 
            max_elements: int = -1, 
            elements_xpath: list | None = None
        ):
        """
        Crawl the site and capture clicks
        """
        self._max_elements = max_elements
        if elements_xpath:
            self.click_xpath = elements_xpath
        self._library.crawl_site(url, "CrawlLibrary.Crawl Page Clicks", int(max_number_of_page_to_crawl))

    def crawl_clicks_after_keyword(
            self,
            url,
            name_keyword,
            *args,
            max_number_of_page_to_crawl=2, 
            max_elements: int = -1, 
            elements_xpath: list | None = None
        ):
        """
        Crawl the site and capture clicks
        """
        self.previous_keyword = name_keyword
        self.previous_keyword_args = list(*args)
        self._max_elements = max_elements
        if elements_xpath:
            self.click_xpath = elements_xpath
        self._library.crawl_site(url, "CrawlLibrary.Crawl Page Clicks", int(max_number_of_page_to_crawl))

    def crawl_type(
            self, 
            url, 
            max_number_of_page_to_crawl=2, 
            max_elements: int = -1, 
            elements_xpath: list | None = None
        ):
        """
        Crawl the site and capture type
        """
        self._max_elements = max_elements
        if elements_xpath:
            self.type_xpath = elements_xpath
        self._library.crawl_site(url, "CrawlLibrary.Crawl Page Type", int(max_number_of_page_to_crawl))

    # ------- Private Keywords ------- 

    def crawl_page_clicks(self):
        data_recorder = SingleClickRecorder(
            self._library,
            elements_xpath=self.click_xpath,
            max_elements=self._max_elements, 
            lang_instructions=self._lang_instructions,
            supervise_crop=self.supervise_crop,
            previous_keyword=self.previous_keyword,
            previous_keyword_args=self.previous_keyword_args
        )
        data_recorder.record()

    def crawl_page_type(self):
        data_recorder = TypeTextRecorder(
            self._library, 
            elements_xpath=self.type_xpath,
            max_elements=self._max_elements, 
            lang_instructions=self._lang_instructions,
            supervise_crop=self.supervise_crop
        )
        data_recorder.record()

    # ======= Deprecated Keywords =======

    def crawl(self, url, max_number_of_page_to_crawl=2, recorders=None, max_elements: int = -1):
        """
        Crawl the site and capture clicks

        DEPRECATED: Use `Crawl Clicks` or `Crawl Type` instead.
        """
        if recorders:
            self.recorders = recorders
        self._max_elements = max_elements
        self._library.crawl_site(url, "CrawlLibrary.Crawl Page", int(max_number_of_page_to_crawl))

    def crawl_page(self):
        """
        Crawl the site and capture clicks

        DEPRECATED: Use `Crawl Clicks` or `Crawl Type` instead.
        """
        recorders_class = []
        if 'click' in self.recorders:
            recorders_class.append(SingleClickRecorder)
        if 'type' in self.recorders:
            recorders_class.append(TypeTextRecorder)

        for recorder in recorders_class:
            data_recorder = recorder(self._library, max_elements=self._max_elements)
            data_recorder.record()


if __name__ == '__main__':
    from robot.run import run
    run('./ButlerRobot/CrawlData.robot', outputdir='results')
