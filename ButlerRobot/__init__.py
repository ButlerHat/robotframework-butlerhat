try:
    from .CrawlLibrary import CrawlLibrary
    from .DataBrowserLibrary import DataBrowserLibrary
    from .keywords.utils import vocabulary
except ImportError as e:
    # If this could not be imported, it means that library is not installed with <robotframework-butlerhat>[full]
    print(f"Error importing libraries: {e}")

try:
    from .DataSeleniumLibrary import DataSeleniumLibrary
except ImportError as e:
    # If this could not be imported, it means that library is not installed with <robotframework-butlerhat>[full]
    print(f"Error importing libraries: {e}")

try:
    from .AIBrowserLibrary import AIBrowserLibrary
except ImportError as e:
    # If this could not be imported, it means that library is not installed with <robotframework-butlerhat>[full]
    print(f"Error importing libraries: {e}")


__all__ = [
    "CrawlLibrary",
    "DataBrowserLibrary",
    "DataSeleniumLibrary",
    "AIBrowserLibrary",
    "vocabulary"
]
