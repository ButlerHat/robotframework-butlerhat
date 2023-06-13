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

    def __init__(self, ocr_url=None, max_elements: int = -1, lang_instructions: str = "en"):
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
        self._max_elements = max_elements
        self._lang_instructions = lang_instructions

    # ======= Task Keywords =======	 
    def crawl(self, url, max_number_of_page_to_crawl=2):
        """
        Crawl the site and capture clicks
        """
        self._library.crawl_site(url, "Crawl Page", int(max_number_of_page_to_crawl))

    def crawl_page(self):
        recorders = [SingleClickRecorder, TypeTextRecorder]
        # recorders = [TypeTextRecorder]

        for recorder in recorders:
            data_recorder = recorder(self._library, max_elements=self._max_elements, lang_instructions=self._lang_instructions)
            data_recorder.record()


if __name__ == '__main__':
    from robot.run import run
    run('./ButlerRobot/CrawlData.robot', outputdir='results')
