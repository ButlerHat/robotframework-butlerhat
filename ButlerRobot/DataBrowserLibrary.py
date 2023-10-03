import base64
import datetime
import os
import random
import requests
from typing import Optional, Union, Any, List, Dict
from io import BytesIO
from enum import Enum, auto
from datetime import timedelta
import urllib.request
import zipfile
from pathlib import Path
import pkg_resources
from PIL import Image
from Browser import Browser, MouseButton
from Browser.utils.data_types import(
    MouseButtonAction,
    SupportedBrowsers,
    NewPageDetails,
    BoundingBox,
    KeyAction,
    ConditionInputs,
    ScreenshotReturnType,
    Proxy,
    ForcedColors,
    GeoLocation,
    HttpCredentials,
    Permission,
    RecordHar,
    RecordVideo,
    ReduceMotion,
    ViewportDimensions,
    ColorScheme
)
from robot.libraries.BuiltIn import BuiltIn
from robot.api.deco import keyword
from ButlerRobot.DataWrapperLibrary import DataWrapperLibrary
from ButlerRobot.src.data_types import BBox, Observation, PageAction, SaveStatus
from .src.utils.ocr import get_all_text


class TextType(Enum):
    """Enum that represents if the action is flexible, strict or critical"""
    array = auto()
    string = auto()
        

class DataBrowserLibrary(DataWrapperLibrary):

    # Capture args and kwargs for the DataBrowserLibrary
    def __init__(self, *args, **kwargs):
        """
        Implementation of the DataWrapperLibrary for the Browser library. 
        This library capture data from Browser tests to use later for training deep learning models.

        :param output_path: Path to save data. Default: RobotFramework output directory.
        :param all_json: Save all data in json format. This is use for debuggin purposes. Default: False.
        :param only_actions: Save only actions with tag PageAction. Default: True.
        :param record: Record data. Default: True.
        :param console: Show logs in console. Default: True.
        :param stealth_mode: Run browser in stealth mode. Default: False.
        """
        # Arguments of the library are only evaluated in execution time. There are two ways to handle this:
        # 1. Add "ButlerRobot.DataBrowser" in "robot.libraries.libdoc.needsArgs" setting to add the arguments in the documentation.
        # 2. Set default variables in the __init__ function.
        # In this case, we ignore arguments in linting time to avoid to start playwright process.

        # Check if robotframework is running
        is_running = False
        api_key_variables = None
        try:
            BuiltIn()._get_context()
            is_running = True
            api_key_variables = BuiltIn().get_variable_value('${CAPTCHA_API_KEY}', default=None)
        except:
            pass
        if is_running:
            keywords_file = pkg_resources.resource_filename('ButlerRobot', 'javascript/keywords.js')        
            # Add the jsextension to kwargs if file exists and not already in kwargs
            if os.path.isfile(keywords_file) and 'jsextension' not in kwargs:
                kwargs['jsextension'] = keywords_file  # This argument triggers the initialization of playwright

        # Get arguments to pass to the DataWrapperLibrary
        output_path = kwargs.pop('output_path', None)
        record = kwargs.pop('record', True)
        console = kwargs.pop('console', True)
        self.stealth_mode = kwargs.pop('stealth_mode', False)
        self.captcha_api_key = kwargs.pop('captcha_api_key', api_key_variables)

        super().__init__(Browser(*args, **kwargs), output_path=output_path, record=record, console=console)
        self._library: Browser = self._library

        # To filter recorded actions
        self.action_tags = ['PageContent', 'ActionWrapper', 'AI']
        self.exclude_tags = ['Wait', 'Getter']

        self.typing_kw_stringpos = {**self.typing_kw_stringpos, 'keyboardinput': 1, 'typetext': 1, 'typesecret': 1, 'keyboardkey': 0, 'presskeys': ':1'}
        
        # ==== Added Keywords ====
        # To add functions to the library
        self.added_keywords.extend(['click_at_bbox'])
        
        self._click_at_bbox_rf = {
            'args': ['selector_bbox', ('wait_after_click', 2.0)],
            'types': [Union[BBox, str], float],
            'tags': ['ActionWrapper'],
            'doc': self.click_at_bbox.__doc__.strip() if self.click_at_bbox.__doc__ else '',
            'source': f'{self.click_at_bbox.__code__.co_filename}:{self.click_at_bbox.__code__.co_firstlineno}'
        }

        self.observation_before_scroll = None
        self.update_scroll_observation = False

    # ======= Stealth Mode =======
    def _is_stealth_mode(self, package_name):
        """
        Check if stealth mode is installed.
        """
        try:
            pkg_resources.get_distribution(package_name)
            return True
        except pkg_resources.DistributionNotFound:
            return False
       
    def _download_plugin(self, dir_path):
        """
        Download the chrome plugin for stealth mode one time. Place into ./plugin folder in this file directory.
        :param download_path: Path to download the plugin.
        """
        download_dir = os.path.dirname(dir_path)
        if not os.path.exists(download_dir):
            os.makedirs(download_dir)
                
        url = 'https://antcpt.com/anticaptcha-plugin.zip'
        # Download plugin
        filehandle, _ = urllib.request.urlretrieve(url)
        # Unizp
        with zipfile.ZipFile(filehandle, "r") as f:
            f.extractall(dir_path)

    def _configure_plugin(self, api_key: str, download_path: str):
        """
        Configure the plugin with the api key.
        :param api_key: API_KEY_32_BYTES key to configure the plugin.
        """
        # establece la clave API en configuración
        file = Path(os.sep.join([download_path, 'js', 'config_ac_api_key.js']))
        file.write_text(
            file.read_text(encoding='utf8').replace(
                "antiCapthaPredefinedApiKey = ''", 
                f"antiCapthaPredefinedApiKey = '{api_key}'")
        , encoding='utf8')

    # ======= Overrides =======
    def _scroll_to_top(self):
        self._library.scroll_by(selector=None, vertical='-100%')

    def _get_viewport(self) -> dict:
        return self._library.get_viewport_size()

    def _run_scroll(self, selector: str) -> None:
        BuiltIn().run_keyword('Browser.Scroll Down', selector)
    
    def _get_screenshot(self, selector=None):
        if not selector:
            im_path = self._library.take_screenshot()
        else:
            im_path = self._library.take_screenshot(selector)
        # Read im_path as a PIL image
        im = Image.open(im_path)

        # Convert to string
        buff = BytesIO()
        im.save(buff, format="PNG")
        img_str = base64.b64encode(buff.getvalue()).decode('ascii')
        return img_str
    
    def _is_browser_open(self):
        catalog = self._library.get_browser_catalog()
        if not catalog or len(catalog) == 0:
            return False
        contexts = catalog[0]['contexts']
        if not contexts or len(contexts) == 0:
            return False
        pages = contexts[0]['pages']
        return pages and len(pages) > 0
    
    def _get_action_tags(self):
        return self.action_tags
    
    def _get_exclude_tags(self):
        return self.exclude_tags

    def _get_dom(self):
        return self._library.get_page_source()

    def _wait_for_browser(self):
        BuiltIn().sleep(0)  # For safe recording

    def _add_scroll_when_recording(self, step: PageAction) -> PageAction:
        """
        In this library, the scroll is added automatically in _retrieve_bbox_and_pointer_from_page.
        This is called from DataWrapperLibrary for libraries like SeleniumLibrary and others.
        Ignoring this function
        """
        return step
    
    def _element_is_in_viewport(self, bbox: BBox) -> bool:
        viewport = self._get_viewport()
        return bbox.x + bbox.width <= viewport['width'] \
                and bbox.y + bbox.height <= viewport['height'] \
                and bbox.x >= 0 \
                and bbox.y >= 0


    def _get_element_bbox_from_pointer(self, x, y) -> Optional[BBox]:
        x, y = str(x), str(y)
        bbox: dict = self._library.evaluate_javascript(None, r'''() => {
                element = document.elementFromPoint(''' + x + r''', ''' + y + r''');
                console.log(element);
                if (!element) {
                    return null;
                }
                if (element.tagName === "IFRAME") {
                    return 'iframe';
                } else {
                    return element.getBoundingClientRect();
                }
            }''')
        if not bbox:
            BuiltIn().log(f'Error getting selector pointer and bbox: {x, y}', console=self.console, level='WARN')
            return None
        if bbox == 'iframe':
            return None
        return BBox(bbox['x'], bbox['y'], bbox['width'], bbox['height'])

    def _retrieve_bbox_and_pointer_from_page(self, selector) -> tuple[None, None] | tuple[BBox, tuple]:
        # Here in browser libray, this function is going to make the element visible. If there is
        # a scroll, it will be added to the stack.
        try:
            web_element = self._library.get_element(selector)
            assert web_element is not None, f'Selector {selector} not found (Web element is None)'
            bbox_ = self._library.get_boundingbox(web_element)
            self.last_selector_error = ""
        except Exception as e:
            # We save the error instead of failing the test. In some cases is expected to do not hace valid selector.
            self.last_selector_error = str(e)
            BuiltIn().log(f'Error getting selector pointer and bbox: {e}', console=self.console)
            return None, None
        
        # Get observation before scroll and after getting element
        observation = self._get_observation()
        # Could be the first observation of the test. Updating first observation
        if self.last_observation == Observation(datetime.datetime.now(), "", "", (0, 0)):
            self._update_start_observation_to_all_stack(observation)
        self.last_observation = observation
        self.observation_before_scroll = self.last_observation
        
        scroll_dict = None
        additional_err = ""
        try:
            scroll_dict = self._library.scrollElementIfNeeded(selector)
        except Exception as e:
            if "Unknown engine" in str(e):
                # This error is raised when the locator is not native to playwright
                level = 'DEBUG'
            else:
                level = 'WARN'
                additional_err = "Element could be scrolled but the bbox is not updated."
            BuiltIn().log(f'Error in _retrieve_bbox_and_pointer_from_page when trying to scroll with scrollElementIfNeeded: {additional_err}. {e}', console=self.console, level=level)

        if not scroll_dict:
            if not self._element_is_in_viewport(BBox(**bbox_)):
                BuiltIn().log(f'The element is not in the viewport. Check the element is visible. Selector: {selector}', console=self.console)
            return (
                BBox(**bbox_),
                (bbox_['x'] + bbox_['width'] / 2,  bbox_['y'] + bbox_['height'] / 2)
            )
        
        if scroll_dict['is_element_scrolled']:
            bbox_ = scroll_dict['el_bbox_after_scroll']
            
            self.update_scroll_observation = True
            # Check if is a scroll in bounding box or scroll in page
            if scroll_dict['is_parent_scrolled']:
               # The start observation will be modified inside the keyword.
                if scroll_dict['is_scrolled_up']:
                    BuiltIn().run_keyword('Browser.Scroll Up')
                else:
                    BuiltIn().run_keyword('Browser.Scroll Down')

            else:
                # The scroll is done in a scrollable object.
                # The start observation will be modified inside the keyword.
                bbox_arg: BBox = BBox(**scroll_dict['parent_bbox_before_scroll'])
                fix_selector = self.fix_bbox
                self.fix_bbox = False
                try:
                    if scroll_dict['is_scrolled_up']:
                        BuiltIn().run_keyword('Browser.Scroll Up At BBox', bbox_arg)
                    else:
                        BuiltIn().run_keyword('Browser.Scroll Down At BBox', bbox_arg)
                finally:
                    self.fix_bbox = fix_selector  # In try to support keywords like "Run Keyword And Ignore Error"
        else:
            # For efficiency, don't update observation in complete_start_context
            self.no_record_next_observation = True 

        if not self._element_is_in_viewport(BBox(**bbox_)):
            BuiltIn().log(f'The element is not in the viewport. Check the element is visible. Selector: {selector}', console=self.console)

        return (
                BBox(**bbox_),
                (bbox_['x'] + bbox_['width'] / 2,  bbox_['y'] + bbox_['height'] / 2)
            )
        
    def _replace_keyboard_input(self, locator: str, text: str, clear: bool):
        """
        Override Input text in a text field. Convert this keyword to a Click at BBox and Keyboard Input.
        Param locator: Selector of the text field. In this function is not used. Rely on bbox retrieved from run_keyword.
        Param text: Text to input.
        Param clear: Clear the text field before inputing the text. Ignoring for now.
        """
        current_action = self.exec_stack.remove_action()

        # Replace with Click at BBox
        try:
            assert current_action.action_args.bbox, 'Trying to input text. The PageAction has no bbox'
            BuiltIn().run_keyword('Browser.Click At BBox', str(current_action.action_args.bbox))
            # Add Keyboard Input
            BuiltIn().run_keyword('Browser.Keyboard Input', text)
        finally:
            # Push keyword to ignore in end_keyword
            current_action.status = SaveStatus.no_record
            self.exec_stack.push(current_action)

    def _replace_keyword_click(self):
        """
        Override Click Element. Convert this keyword to a Click at BBox.
        Param locator: Selector of the element to click.
        """
        current_action = self.exec_stack.remove_action()

        # Replace with Click at BBox
        try:
            assert current_action.action_args.bbox, 'Trying to click element. The PageAction has no bbox. Last error was: \n' + str(self.last_selector_error)
            BuiltIn().run_keyword('Browser.Click At BBox', str(current_action.action_args.bbox))
        finally:
            # Push keyword to ignore in end_keyword
            current_action.status = SaveStatus.no_record
            self.exec_stack.push(current_action)

    # ======== Keywords =========
    @keyword(name="New Stealth Persistent Context", tags=("Setter", "BrowserControl"))
    def new_stealth_persistent_context(
        self,
        userDataDir: str = "",  # TODO: change to PurePath
        browser: SupportedBrowsers = SupportedBrowsers.chromium,
        headless: bool = True,
        *,
        acceptDownloads: bool = True,
        args: Optional[List[str]] = None,
        bypassCSP: bool = False,
        channel: Optional[str] = None,
        colorScheme: Optional[ColorScheme] = None,
        defaultBrowserType: Optional[SupportedBrowsers] = None,
        deviceScaleFactor: Optional[float] = None,
        devtools: bool = False,
        downloadsPath: Optional[str] = None,
        env: Optional[Dict] = None,
        executablePath: Optional[str] = None,
        extraHTTPHeaders: Optional[Dict[str, str]] = None,
        forcedColors: ForcedColors = ForcedColors.none,
        geolocation: Optional[GeoLocation] = None,
        handleSIGHUP: bool = True,
        handleSIGINT: bool = True,
        handleSIGTERM: bool = True,
        hasTouch: Optional[bool] = None,
        httpCredentials: Optional[HttpCredentials] = None,
        ignoreDefaultArgs: Union[List[str], bool, None] = None,
        ignoreHTTPSErrors: bool = False,
        isMobile: Optional[bool] = None,
        javaScriptEnabled: bool = True,
        locale: Optional[str] = None,
        offline: bool = False,
        permissions: Optional[List[Permission]] = None,
        proxy: Optional[Proxy] = None,
        recordHar: Optional[RecordHar] = None,
        recordVideo: Optional[RecordVideo] = None,
        reducedMotion: ReduceMotion = ReduceMotion.no_preference,
        screen: Optional[Dict[str, int]] = None,
        slowMo: timedelta = timedelta(seconds=0),
        timeout: timedelta = timedelta(seconds=30),
        timezoneId: Optional[str] = None,
        tracing: Optional[str] = None,
        url: Optional[str] = None,
        userAgent: Optional[str] = None,
        viewport: Optional[ViewportDimensions] = ViewportDimensions(
            width=1280, height=720
        )
    ):
        """Open a new
        [https://playwright.dev/docs/api/class-browsertype#browser-type-launch-persistent-context | persistent context].

        `New Persistent Context` does basically executes `New Browser`, `New Context` and `New Page` in one step with setting a profile at the same time.

        This keyword returns a tuple of browser id, context id and page details. (New in Browser 15.0.0)

        | =Argument=               | =Description= |
        | ``userDataDir``          | Path to a User Data Directory, which stores browser session data like cookies and local storage. More details for Chromium and Firefox. Note that Chromium's user data directory is the parent directory of the "Profile Path" seen at chrome://version. Pass an empty string to use a temporary directory instead. |
        | ``browser``              | Browser type to use. Default is Chromium. |
        | ``headless``             | Whether to run browser in headless mode. Defaults to ``True``. |
        | ``storageState`` & ``hideRfBrowser`` | These arguments have no function and will be removed soon. |
        | other arguments          | Please see `New Browser`, `New Context` and `New Page` for more information about the other arguments. |

        If you want to use extensions you need to download the extension as a .zip, enable loading the extension, and load the extensions using chromium arguments like below. Extensions only work with chromium and with a headful browser.

        | ${launch_args}=  Set Variable  ["--disable-extensions-except=./ublock/uBlock0.chromium", "--load-extension=./ublock/uBlock0.chromium"]
        | ${browserId}  ${contextId}  ${pageDetails}=  `New Persistent Context`  browser=chromium  headless=False  url=https://robocon,io  args=${launch_args}

        Check `New Browser`, `New Context` and `New Page` for the specific argument docs.

        [https://forum.robotframework.org/t//4309|Comment >>]
        """
        if not userDataDir:
            output_dir = BuiltIn().get_variable_value('${OUTPUT_DIR}')
            userDataDir = os.sep.join([output_dir, 'browser', 'user_data_dir'])

        if not self._is_stealth_mode("robotframework-browser-stealth"):
            BuiltIn().fail('Error at DataBrowserLibrary. Stealth mode is not installed. Please install robotframework-browser-stealth library.')

        plugins = []
        curr_dir = os.path.dirname(os.path.realpath(__file__))
        plugin_download_path = os.sep.join([curr_dir, '.cache', 'plugin'])
        plugin_path = os.sep.join([curr_dir, '.cache', 'plugin_configured.zip'])
        # Download plugin
        if self.captcha_api_key:
            if not os.path.exists(plugin_path):
                BuiltIn().log('Stealth mode is enabled. Downloading captcha plugin.', console=self.console, level='DEBUG')
                self._download_plugin(plugin_download_path)
                self._configure_plugin(self.captcha_api_key, plugin_download_path)
            plugins.append(plugin_download_path)
        else:
            BuiltIn().log('Stealth mode is enabled. CAPTCHA_API_KEY is not set. Plugin will not be configured.', console=self.console, level='DEBUG')

        if headless:
            BuiltIn().log('Stealth mode is enabled. Headless mode is disabled.', console=self.console, level='WARN')
        headless = False
    
        if ignoreDefaultArgs is not None:
            BuiltIn().log('Stealth mode is enabled. ignoreDefaultArgs is disabled.', console=self.console, level='WARN')
        ignoreDefaultArgs = [
            "--disable-extensions",
            "--enable-automation"
        ]

        assert os.path.exists(plugin_path), f'Error at New Stealth Browser. Plugin not found at {plugin_path}'
        if args is not None:
            BuiltIn().log('Stealth mode is enabled. args is disabled.', console=self.console, level='WARN')
        args = [
            f'--disable-extensions-except={",".join(plugins)}',
            f'--load-extension={",".join(plugins)}'
        ]
        self._library.new_persistent_context(
            userDataDir=userDataDir,
            browser=browser,
            headless=headless,
            acceptDownloads=acceptDownloads,
            args=args,
            bypassCSP=bypassCSP,
            channel=channel,
            colorScheme=colorScheme,
            defaultBrowserType=defaultBrowserType,
            deviceScaleFactor=deviceScaleFactor,
            devtools=devtools,
            downloadsPath=downloadsPath,
            env=env,
            executablePath=executablePath,
            extraHTTPHeaders=extraHTTPHeaders,
            forcedColors=forcedColors,
            geolocation=geolocation,
            handleSIGHUP=handleSIGHUP,
            handleSIGINT=handleSIGINT,
            handleSIGTERM=handleSIGTERM,
            hasTouch=hasTouch,
            httpCredentials=httpCredentials,
            ignoreDefaultArgs=ignoreDefaultArgs,
            ignoreHTTPSErrors=ignoreHTTPSErrors,
            isMobile=isMobile,
            javaScriptEnabled=javaScriptEnabled,
            locale=locale,
            offline=offline,
            permissions=permissions,
            proxy=proxy,
            recordHar=recordHar,
            recordVideo=recordVideo,
            reducedMotion=reducedMotion,
            screen=screen,
            slowMo=slowMo,
            timeout=timeout,
            timezoneId=timezoneId,
            tracing=tracing,
            url=url,
            userAgent=userAgent,
            viewport=viewport
        )

    @keyword(name="Open Browser", tags=("Setter", "BrowserControl"))
    def open_browser(
        self,
        url: Optional[str] = None,
        browser: SupportedBrowsers = SupportedBrowsers.chromium,
        headless: bool = False,
        pause_on_failure: bool = True,
        bypassCSP=True,
    ):
        """
        Open a browser. This keyword is a wrapper for Playwright Open Browser keyword.
        Param url: Url to open. If not provided, will open an empty page.
        Param browser: Browser to use. Supported browsers: chromium, firefox, webkit.
        Param headless: Run browser in headless mode.
        Param pause_on_failure: Pause test execution if keyword fails.
        Param bypassCSP: Bypass CSP.
        """
        self._library.open_browser(url, browser, headless, pause_on_failure, bypassCSP)
        self._library.wait_until_network_is_idle()
        BuiltIn().sleep(1)

    @keyword(name="Wait New Page", tags=("Setter", "BrowserControl"))
    def wait_new_page(self, url: Optional[str] = None, wait: int = 3) -> NewPageDetails:
        """
        Open a new page. This keyword is a wrapper for Playwright New Page keyword.
        Param url: Url to open. If not provided, will open an empty page.
        """
        return_val = self._library.new_page(url)
        self._library.wait_until_network_is_idle()
        BuiltIn().sleep(wait)
        return return_val
        
    @keyword(name='Click', tags=['action', 'PageContent'])
    def click(self, selector: str, button: MouseButton = MouseButton.left):
        """
        Override Click Button. Convert this keyword to a Click at BBox.
        Param locator: Selector of the button.
        """
        if self.exec_stack:
            self._replace_keyword_click()
        else:
            self._library.click(selector, button)


    def click_at_bbox(self, selector_bbox: Union[BBox, str], wait_after_click: float = 2.0):
        """
        Record a click event with no xpath selector. This keyword go throught WrapperLibrary middleware as PageAction.
        """
        if isinstance(selector_bbox, str):
            selector_bbox = BBox.from_rf_string(selector_bbox)
        if not self._element_is_in_viewport(selector_bbox):
            BuiltIn().fail(f'Failing clicking at a bounding box outside the viewport. Check previous messages in the logs. Selector: {selector_bbox}')
        # Get the middle of the bbox
        top_left = (selector_bbox.x, selector_bbox.y)
        w = selector_bbox.width
        h = selector_bbox.height
        middle_coordinates = (top_left[0] + w//2, top_left[1] + h//2)
        
        self._library.mouse_button(MouseButtonAction.click, middle_coordinates[0], middle_coordinates[1])

    @keyword(name="Scroll Down", tags=("action", "PageContent"))
    def scroll_down(self, pixels_selector: Union[int, str, None] = None, seed: int = -1):
        """
        Scroll down the page.
        Param pixels: Number of pixels to scroll down.
        """
        # Check the case of is scrolled by the library itself
        if self.update_scroll_observation:
            assert self.observation_before_scroll, 'Error at Scroll Down. Trying to scroll down without an observation before.'
            curr_step = self.exec_stack.get_last_step()
            self._update_observation_and_set_in_parents(self.observation_before_scroll)
            assert curr_step.context is not None, 'Error at Scroll Down. Trying to scroll down without an observation before.'
            curr_step.context.start_observation = self.observation_before_scroll
            self.update_scroll_observation = False
            return

        # Run Scroll with pixels. If is an int or starts with a number
        if isinstance(pixels_selector, int) or (isinstance(pixels_selector, str) and pixels_selector[0].isdigit()):
            self._library.scroll_by(vertical=pixels_selector)  # type: ignore
            return

        if seed == -1:
            seed = BuiltIn().get_variable_value('${SEED}', random.randint(0, 100))
        random.seed(seed)
        height = self._library.get_viewport_size()['height']

        # Try with locator
        if pixels_selector:
            bbox, _ = self._get_bbox_and_pointer(pixels_selector)
            viewport_height = self._library.get_viewport_size()['height']
            if bbox:
                pixels = (bbox.y + bbox.height) - viewport_height + random.randint(0, height//8)
                self.scroll_down(pixels)
                return
            else:
                BuiltIn().fail(f'Error at Scroll Down. Selector {pixels_selector} not found or does not have bbox.')

        # Scroll down a random number of pixels
        else:
            pixels = random.randint(0, height//2)
            self.scroll_down(pixels)

    @keyword(name="Scroll Up", tags=("action", "PageContent"))
    def scroll_up(self, pixels_selector: Union[int, str, None] = None, seed: int = -1):
        """
        Scroll up the page.
        Param pixels: Number of pixels to scroll up.
        """
        # Check the case of is scrolled by the library itself
        if self.update_scroll_observation:
            assert self.observation_before_scroll, 'Error at Scroll Up. Trying to scroll up without an observation before.'
            curr_step = self.exec_stack.get_last_step()
            self._update_observation_and_set_in_parents(self.observation_before_scroll)
            assert curr_step.context is not None, 'Error at Scroll Up. Trying to scroll up without an observation before.'
            curr_step.context.start_observation = self.observation_before_scroll
            self.update_scroll_observation = False
            return
        
        # Run Scroll with pixels. If is an int or starts with a number
        if isinstance(pixels_selector, int) or (isinstance(pixels_selector, str) and pixels_selector[0].isdigit()):
            self._library.scroll_by(vertical=f'-{pixels_selector}')
            return
        
        if seed == -1:
            seed = BuiltIn().get_variable_value('${SEED}', random.randint(0, 100))
        random.seed(seed)
        height = self._library.get_viewport_size()['height']

        # Try with locator
        if pixels_selector:
            bbox, _ = self._get_bbox_and_pointer(pixels_selector)
            if bbox:
                pixels = bbox.y + random.randint(0, height//8)
                self.scroll_up(pixels)
                return
            else:
                BuiltIn().fail(f'Error at Scroll Up. Selector {pixels_selector} not found or does not have bbox.')
        
        # Scroll up a random number of pixels
        else:
            pixels = random.randint(0, height//2)
            self.scroll_up(pixels)
        
        
    @keyword(name='Scroll Down At BBox', tags=['action', 'ActionWrapper'])
    def scroll_at_bbox(self, selector_bbox: BBox | str, offset: int = 100):
        """
        Record a click event with no xpath selector. This keyword go throught WrapperLibrary middleware as PageAction.
        """
        if self.update_scroll_observation:
            assert self.observation_before_scroll, 'Error at Scroll Down At BBox. Trying to scroll down without an observation before.'
            curr_step = self.exec_stack.get_last_step()
            self._update_observation_and_set_in_parents(self.observation_before_scroll)
            assert curr_step.context is not None, 'Error at Scroll Down At BBox. Trying to scroll down without an observation before.'
            curr_step.context.start_observation = self.observation_before_scroll
            self.update_scroll_observation = False
            return

        bbox: BBox | None = None
        # Check if is a locator and convert to BBox
        if isinstance(selector_bbox, str) and not selector_bbox.startswith('BBox'):
            curr_step = self.exec_stack.get_last_step()
            assert isinstance(curr_step, PageAction)
            assert curr_step.action_args.bbox, 'Error at Scroll in BBox. Trying to scroll element. The PageAction has no bbox'
            bbox = curr_step.action_args.bbox
            # Update the locator to build the dataset
            curr_step.action_args.selector_dom = str(bbox)

        elif isinstance(selector_bbox, str):
            bbox = BBox.from_rf_string(selector_bbox)
        else:
            bbox = selector_bbox
       
        assert bbox, 'Error at Scroll in BBox. Trying to scroll element. The PageAction has no bbox'
        # Get the middle of the bbox
        top_left = (bbox.x, bbox.y)
        viewport = self._library.get_viewport_size()
        w = min(bbox.width, viewport['width'])
        h = min(bbox.height, viewport['height'])
        middle_coordinates = (top_left[0] + w//2, top_left[1] + h//2)

        self._library.mouse_move(middle_coordinates[0], middle_coordinates[1])
        self._library.mouse_wheel(0, offset)

    @keyword(name='Scroll Up At BBox', tags=['action', 'ActionWrapper'])
    def scroll_up_at_bbox(self, selector_bbox: BBox | str, offset: int = 100):
        """
        Record a click event with no xpath selector. This keyword go throught WrapperLibrary middleware as PageAction.
        """
        bbox: BBox | None = None
        # Check if is a locator and convert to BBox
        if isinstance(selector_bbox, str) and not selector_bbox.startswith('BBox'):
            curr_step = self.exec_stack.get_last_step()
            assert isinstance(curr_step, PageAction)
            assert curr_step.action_args.bbox, 'Error at Scroll in BBox. Trying to scroll element. The PageAction has no bbox'
            bbox = curr_step.action_args.bbox
            # Update the locator to build the dataset
            curr_step.action_args.selector_dom = str(bbox)

        elif isinstance(selector_bbox, str):
            bbox = BBox.from_rf_string(selector_bbox)
        else:
            bbox = selector_bbox
       
        assert bbox, 'Error at Scroll in BBox. Trying to scroll element. The PageAction has no bbox'
        # Get the middle of the bbox
        top_left = (bbox.x, bbox.y)
        w = bbox.width
        h = bbox.height
        middle_coordinates = (top_left[0] + w//2, top_left[1] + h//2)

        self._library.mouse_move(middle_coordinates[0], middle_coordinates[1])
        self._library.mouse_wheel(0, -offset)

    @keyword(name='Keyboard Key', tags=['action', 'PageContent'])
    def keyboard_key(self, key: str):
        """
        Override Keyboard Key. Remove KeyAction from arguments.
        :param key: Key to press.
        """
        self._library.keyboard_key(KeyAction.press, key)

    @keyword(
            name='Wait For Condition',
            types={
                "condition": ConditionInputs,
                "args": Any,
                "timeout": Optional[timedelta],
                "message": Optional[str],
            },
            tags=["Wait", "PageContent", "task", "no_record"],
             )
    def wait_for_condition(
        self,
        condition,
        *args: Any,
        timeout: Optional[timedelta] = None,
        message: Optional[str] = None,
    ) -> Any:
        """
        Override Wait For Condition to add tags. Types specified to avoid errors with code ofuscation.
        """
        # TODO: Types on keywrod decorator is not working because the DataWrapperLibrary. Check later.
        # It works if we add condition: ConditionInputs in args, but the ofuscation remove that part.
        if isinstance(condition, str):
            condition_str = condition.lower().replace(' ', '_')
            for member in ConditionInputs:
                if condition_str in member.value:
                    condition_: ConditionInputs = member
                    break
            else:
                raise ValueError(f'Condition {condition} not found.')
        else:
            condition_: ConditionInputs = condition
        
        return self._library.wait_for_condition(condition_, *args, timeout=timeout, message=message)

    @keyword(name='Is Text Visible', tags=['task', 'no_record'])
    def is_text_visible(self, text: str, selector: str | BBox | None = None) -> bool:
        """
        Check if text is visible in the page.
        Param text: Text to search.
        Param selector: Selector to search in.
        """
        img = None
        if selector:
            bbox, _ = self._get_bbox_and_pointer(selector)
            if bbox:
                img = self._library.take_screenshot(crop=BoundingBox(**bbox.to_dict()), return_as=ScreenshotReturnType.base64)

        if not img:
            img = self._library.take_screenshot(return_as=ScreenshotReturnType.base64)

        element_txt = get_all_text(self.ocr_url, img)

        return text in element_txt if element_txt else False

    @keyword(name="Element BBox", tags=['action', 'PageContent'])
    def get_element_bbox(self, selector_bbox: BBox | str) -> BBox:
        """
        Get the bounding box of an element. Dummy instruction for the dataset.
        Param selector: Selector of the element.
        """
        bbox: BBox | None = None
        # Check if is a locator and convert to BBox
        if isinstance(selector_bbox, str) and not selector_bbox.startswith('BBox'):
            curr_step = self.exec_stack.get_last_step()
            assert isinstance(curr_step, PageAction)
            assert curr_step.action_args.bbox, 'Error Getting element. Trying to get element bbox from stack. The PageAction has no bbox. Last error was: \n' + str(self.last_selector_error)
            bbox = curr_step.action_args.bbox
            # Update the locator to build the dataset
            curr_step.action_args.selector_dom = str(bbox)

        elif isinstance(selector_bbox, str):
            bbox = BBox.from_rf_string(selector_bbox)
        else:
            bbox = selector_bbox

        return bbox
    
    @keyword(name="Get Text From BBox", tags=['task', 'no_record'])
    def get_text_from_bbox(self, selector_bbox: BBox | str, return_type: TextType = TextType.string, with_ocr: bool = True) -> str | list[str]:
        """
        Get the text from a BBox.
        Param selector: Selector of the element.
        """
        bbox: BBox | None = None
        # Check if is a locator and convert to BBox
        if isinstance(selector_bbox, str) and not selector_bbox.startswith('BBox'):
            curr_step = self.exec_stack.get_last_step()
            assert isinstance(curr_step, PageAction)
            assert curr_step.action_args.bbox, 'Error Getting Text From BBox. Trying to get element bbox from stack. The PageAction has no bbox'
            bbox = curr_step.action_args.bbox
            # Update the locator to build the dataset
            curr_step.action_args.selector_dom = str(bbox)

        elif isinstance(selector_bbox, str):
            bbox = BBox.from_rf_string(selector_bbox)
        else:
            bbox = selector_bbox
        
        # Get the middle of the bbox
        bottom_right = (bbox.x + bbox.width, bbox.y + bbox.height)
        view_port = self._library.get_viewport_size()
        if bottom_right[0] > view_port.width or bottom_right[1] > view_port.height:
            BuiltIn().log(f'Error at Get Text From BBox. The bbox is out of the viewport. BBox: {bbox.to_dict()}', 'WARN', console=True)
            return ''
        text = self._library.getTextFromBboxWithJs(bbox.x, bbox.y, bottom_right[0], bottom_right[1])
        if not text and with_ocr:
            BuiltIn().log(f'Getting text with JavaScript failed. Trying with OCR', console=True)
            img = self._library.take_screenshot(crop=BoundingBox(**bbox.to_dict()), return_as=ScreenshotReturnType.base64)
            text = get_all_text(self.ocr_url, img)
        if not text:
            BuiltIn().log(f'Error at Get Text From BBox. No text found for locator {selector_bbox}', 'WARN', console=True)
            text = ''
        if return_type == TextType.string:
            if isinstance(text, list) and len(text):
                text = '\n'.join(text)
            assert isinstance(text, str), f'Error at Get Text From BBox. The text is not a string. Text: {text}'
            text.strip()
        if return_type == TextType.array:
            if isinstance(text, str):
                text = [text]
        return text

    @keyword(name='Record Click', tags=['task', 'only_substeps'])
    def record_click(self):
        """
        Record a click in the screen. This action only make sense in the interpreter.
        """
        bounding_rect: dict = self._library.getElementBboxHighlighted()  # type: ignore
        bbox: BBox = BBox(bounding_rect['left'], bounding_rect['top'], bounding_rect['width'], bounding_rect['height'])
        
        curr_val_fix_bbox = self.fix_bbox if hasattr(self, 'fix_bbox') else False
        self.fix_bbox = False
        try:
            BuiltIn().run_keyword('Browser.Click At BBox', bbox)
        finally:
            self.fix_bbox = curr_val_fix_bbox
        
        BuiltIn().log_to_console(f'Browser.Click at BBox  {str(bbox)}')

    @keyword(name='Record Scroll', tags=['task', 'only_substeps'])
    def record_scroll(self):
        """
        Record a scroll in the screen. This action only make sense in the interpreter.
        """
        bounding_rect: dict = self._library.getElementBboxHighlighted()
        bbox: BBox = BBox(bounding_rect['left'], bounding_rect['top'], bounding_rect['width'], bounding_rect['height'])

        curr_val_fix_bbox = self.fix_bbox if hasattr(self, 'fix_bbox') else False
        self.fix_bbox = False
        try:
            BuiltIn().run_keyword('Browser.Scroll At BBox', bbox)
        finally:
            self.fix_bbox = curr_val_fix_bbox

        BuiltIn().log_to_console(f'Browser.Scroll at BBox  {str(bbox)}')

    @keyword(name='Record BBox', tags=['action', 'no_record'])
    def record_bbox(self) -> BBox:
        """
        Record a BBox in the screen. This action only make sense in the interpreter.
        """
        bounding_rect: dict = self._library.getElementBboxHighlighted()
        bbox: BBox = BBox(bounding_rect['left'], bounding_rect['top'], bounding_rect['width'], bounding_rect['height'])
        return bbox
